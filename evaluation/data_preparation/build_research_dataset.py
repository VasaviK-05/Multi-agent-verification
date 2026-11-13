"""Build immutable, incremental History/Development research candidate data.

Only unified History/Development, raw GSM8K train, raw HotpotQA train, and a
declared prior reconciled dataset are read. No Final Test source is opened.
This pipeline prepares labels only; it never creates verifier Attempts or
offline Example objects.
"""

from __future__ import annotations

import argparse
import collections
import copy
import hashlib
import json
import random
import re
import sys
from datetime import date
from pathlib import Path
from typing import Any

import yaml
from datasets import load_from_disk

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from evaluation.data_preparation.build_verified_subset import (  # noqa: E402
    make_supporting_evidence,
    norm_question,
    normalize_numeric,
    replay_gsm_solution,
    token_f1,
)
from evaluation.data_preparation.build_verified_negative_candidates import (  # noqa: E402
    validate_gsm_discrete_count_negative,
)
from evaluation.data_preparation.reconcile_verified_candidates import (  # noqa: E402
    canonical_row,
    group_roster,
)
from evaluation.data_preparation import build_offline_examples as offline_adapter  # noqa: E402

DEFAULT_CONFIG = ROOT / "evaluation/config/research_dataset.yaml"
PARTITIONS = ("history", "development")
BENCHMARKS = ("GSM8K", "HotpotQA")
SOURCE_VERSION = {
    "GSM8K": "openai/gsm8k main@740312add88f781978c0658806c59bc2815b9866",
    "HotpotQA": "hotpotqa/hotpot_qa distractor@1908d6afbbead072334abe2965f91bd2709910ab",
}
GSM_ID = re.compile(r"gsm8k_train_(\d+)$")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")


def jsonl_bytes(rows: list[dict]) -> bytes:
    return b"".join((json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8") for row in rows)


def digest_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def resolve_path(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def group_id(benchmark: str, question: str) -> str:
    prefix = "gsm8k" if benchmark == "GSM8K" else "hotpotqa"
    normalized = norm_question(question)
    if not normalized:
        raise ValueError("Question normalizes to an empty string")
    return f"{prefix}-q-{hashlib.sha256(normalized.encode('utf-8')).hexdigest()[:16]}"


def sample_incremental_groups(
    rows_by_partition: dict[str, list[dict]],
    benchmark: str,
    prior_groups: dict[str, dict],
    quotas: dict[str, int],
    seed: int,
) -> list[dict]:
    """Preserve prior source IDs/partitions and deterministically add groups."""
    by_id = {str(row.get("id")): row for partition in PARTITIONS for row in rows_by_partition[partition]}
    if len(by_id) != sum(len(rows_by_partition[p]) for p in PARTITIONS):
        raise ValueError(f"{benchmark}: duplicate source dataset IDs in H/D pool")
    assigned_by_normalized: dict[str, tuple[str, str]] = {}
    selected: dict[str, dict] = {}
    for old_group, identity in prior_groups.items():
        dataset_id = str(identity["dataset_id"])
        partition = str(identity["partition"])
        if partition not in PARTITIONS or dataset_id not in by_id:
            raise ValueError(f"Prior group is absent from allowed H/D source pool: {dataset_id}")
        row = by_id[dataset_id]
        if row.get("benchmark") != benchmark or row.get("question") != identity.get("question"):
            raise ValueError(f"Prior group/source mismatch: {dataset_id}")
        expected = group_id(benchmark, str(row["question"]))
        if old_group != expected:
            raise ValueError(f"Prior group ID is not stable under current grouping: {dataset_id}")
        if row.get("candidate_answers") is None or len(row["candidate_answers"]) != 2:
            raise ValueError(f"Prior source row has invalid candidate shape: {dataset_id}")
        normalized = norm_question(row["question"])
        if normalized in assigned_by_normalized and assigned_by_normalized[normalized][1] != dataset_id:
            raise ValueError(f"Duplicate normalized questions in prior groups: {dataset_id}")
        assigned_by_normalized[normalized] = (partition, dataset_id)
        selected[dataset_id] = {"row": row, "partition": partition, "group_id": old_group, "reused": True}

    if len(selected) != len(prior_groups):
        raise ValueError(f"{benchmark}: repeated prior source IDs")
    for partition in PARTITIONS:
        existing = sum(item["partition"] == partition for item in selected.values())
        if existing > quotas[partition]:
            raise ValueError(f"Configured {benchmark}/{partition} target is below preserved prior count {existing}")

    pools: dict[str, list[dict]] = {partition: [] for partition in PARTITIONS}
    seen_norm: dict[str, str] = {}
    for partition in PARTITIONS:
        for row in rows_by_partition[partition]:
            if row.get("benchmark") != benchmark:
                continue
            dataset_id = str(row.get("id"))
            normalized = norm_question(row.get("question", ""))
            if not normalized:
                continue
            previous = seen_norm.get(normalized)
            if previous is not None and previous != dataset_id:
                # Keep an existing/prior identity where possible; otherwise the
                # fixed History-before-Development order is the tie breaker.
                prior = assigned_by_normalized.get(normalized)
                if prior and prior[1] != dataset_id:
                    continue
                continue
            seen_norm[normalized] = dataset_id
            if normalized in assigned_by_normalized or dataset_id in selected:
                continue
            variants = row.get("candidate_answers") or []
            if len(variants) != 2 or variants[0].get("source") != "benchmark_gold":
                continue
            if len({str(candidate.get("answer", "")) for candidate in variants}) != 2:
                continue
            pools[partition].append({"row": row, "partition": partition, "group_id": group_id(benchmark, row["question"]), "reused": False})

    b_offset = 0 if benchmark == "GSM8K" else 1
    for p_offset, partition in enumerate(PARTITIONS):
        existing = sum(item["partition"] == partition for item in selected.values())
        needed = quotas[partition] - existing
        pool = sorted(pools[partition], key=lambda item: str(item["row"]["id"]))
        if needed > len(pool):
            raise ValueError(f"Insufficient eligible source groups for {benchmark}/{partition}: need {needed}, have {len(pool)}")
        additions = random.Random(seed + 1009 * b_offset + p_offset).sample(pool, needed)
        for item in additions:
            selected[str(item["row"]["id"])] = item

    result = sorted(selected.values(), key=lambda item: (PARTITIONS.index(item["partition"]), str(item["row"]["id"])))
    if len({item["group_id"] for item in result}) != len(result):
        raise ValueError(f"{benchmark}: normalized duplicate group selected")
    return result


def audit_selection_pool(rows_by_partition: dict[str, list[dict]], benchmark: str, selected: list[dict]) -> dict:
    seen_questions: dict[str, str] = {}
    excluded = collections.Counter()
    eligible_ids: set[str] = set()
    row_count = 0
    for partition in PARTITIONS:
        for row in rows_by_partition[partition]:
            if row.get("benchmark") != benchmark:
                continue
            row_count += 1
            dataset_id = str(row.get("id"))
            normalized = norm_question(row.get("question", ""))
            if not normalized:
                excluded["empty_normalized_question"] += 1
                continue
            if normalized in seen_questions and seen_questions[normalized] != dataset_id:
                excluded["duplicate_normalized_question_identity"] += 1
                continue
            seen_questions[normalized] = dataset_id
            candidates = row.get("candidate_answers") or []
            if len(candidates) != 2:
                excluded["candidate_variant_count_not_two"] += 1
                continue
            if candidates[0].get("source") != "benchmark_gold":
                excluded["first_candidate_not_benchmark_gold"] += 1
                continue
            if len({str(candidate.get("answer", "")) for candidate in candidates}) != 2:
                excluded["duplicate_candidate_answer_text"] += 1
                continue
            eligible_ids.add(dataset_id)
    selected_ids = {str(item["row"]["id"]) for item in selected}
    return {
        "source_question_rows": row_count,
        "eligible_unique_groups": len(eligible_ids),
        "selected_groups": len(selected_ids),
        "eligible_groups_not_selected_by_configured_target": len(eligible_ids - selected_ids),
        "selected_ids_not_in_eligible_pool": sorted(selected_ids - eligible_ids),
        "excluded_source_rows_by_reason": dict(sorted(excluded.items())),
    }


def source_candidate_record(base: dict, candidate: dict, *, status: str, method: str, basis: str,
                            evidence: list[dict], provenance: dict, rationale: str,
                            unresolved_reason: str | None, candidate_index: int) -> dict:
    original = {key: value for key, value in base.items() if not key.startswith("_")}
    return {
        "candidate_id": f"{base['id']}::candidate_{candidate_index}",
        "dataset_id": str(base["id"]),
        "benchmark": base["benchmark"],
        "dataset_version": SOURCE_VERSION[base["benchmark"]],
        "partition": base["_partition"],
        "question": base["question"],
        "candidate_answer": str(candidate.get("answer", "")),
        "candidate_source": candidate.get("source"),
        "candidate_generation_method": candidate.get("source"),
        "candidate_generation_provenance": {
            "source_file": f"evaluation/datasets/unified/{base['_partition']}.json",
            "source_candidate_index": candidate_index,
            "sampling_seed": base.get("_sampling_seed"),
            "candidate_values_inherited_from_existing_preprocessor": True,
            "generation_random_seed": "not_applicable_existing_preprocessing_output",
        },
        "original_unified_source_record": original,
        "gold_answer": str(base.get("gold_answer", "")),
        "correctness_status": status,
        "validation_method": method,
        "validation_basis": basis,
        "validation_evidence": evidence,
        "evidence_provenance": provenance,
        "validation_rationale": rationale,
        "validation_confidence_category": "high_under_declared_method" if status != "unresolved" else "not_established",
        "unresolved_reason": unresolved_reason,
        "independent_human_review": False,
        "source_candidate_index": candidate_index,
    }


def recover_hotpot_donor(base: dict, ordered_partition_rows: list[dict], answer: str) -> str | None:
    target = str(base["gold_answer"])
    try:
        from evaluation.data_preparation.build_verified_subset import hotpot_normalize
    except ImportError:
        hotpot_normalize = lambda value: re.sub(r"[^a-z0-9]+", "", str(value).lower())
    rows = [row for row in ordered_partition_rows if row.get("benchmark") == "HotpotQA"]
    try:
        position = next(i for i, row in enumerate(rows) if str(row.get("id")) == str(base["id"]))
    except StopIteration:
        return None
    for offset in range(1, len(rows)):
        donor = rows[(position + offset) % len(rows)]
        donor_answer = str(donor.get("gold_answer", ""))
        if hotpot_normalize(donor_answer) != hotpot_normalize(target) and donor_answer == answer:
            return str(donor["id"])
    return None


def make_new_rows(
    selected: list[dict], benchmark: str, raw_gsm: Any, raw_hotpot_train: Any,
    ordered_partition_rows: dict[str, list[dict]], include_negatives: bool, sampling_seed: int,
) -> list[dict]:
    output: list[dict] = []
    hotpot_raw_by_id = {str(row.get("id")): row for row in raw_hotpot_train} if benchmark == "HotpotQA" else {}
    for item in selected:
        if item["reused"]:
            continue
        row = dict(item["row"])
        row["_partition"] = item["partition"]
        row["_sampling_seed"] = sampling_seed
        candidates = row.get("candidate_answers") or []
        if len(candidates) != 2:
            raise ValueError(f"Expected two candidate variants: {row.get('id')}")
        if benchmark == "GSM8K":
            match = GSM_ID.fullmatch(str(row["id"]))
            if not match:
                raise ValueError(f"GSM8K candidate is not from raw train: {row['id']}")
            index = int(match.group(1))
            raw = raw_gsm[index]
            if raw.get("question") != row.get("question"):
                raise ValueError(f"GSM8K raw question mismatch: {row['id']}")
            solution = str(raw.get("answer", ""))
            gold = str(row.get("gold_answer", ""))
            replay = replay_gsm_solution(solution, gold)
            gold_value = normalize_numeric(gold)
            gold_candidate = candidates[0]
            if normalize_numeric(gold_candidate.get("answer")) != gold_value:
                raise ValueError(f"GSM8K source candidate/gold mismatch: {row['id']}")
            ev = [{"kind": "original_GSM8K_worked_solution", "source_path": "evaluation/datasets/raw/gsm8k/train",
                   "source_split": "train", "source_row_index": index,
                   "solution_sha256": hashlib.sha256(solution.encode("utf-8")).hexdigest(),
                   "arithmetic_replay": replay}]
            provenance = {"source_file": f"evaluation/datasets/unified/{item['partition']}.json",
                          "raw_source_path": "evaluation/datasets/raw/gsm8k/train", "source_split": "train",
                          "source_row_index": index, "solution_sha256": ev[0]["solution_sha256"]}
            gold_ok = replay.get("status") == "passed" and gold_value is not None
            gold_status = "verified_correct" if gold_ok else "unresolved"
            source0 = source_candidate_record(row, gold_candidate, status=gold_status,
                method="benchmark_source_match_plus_independent_arithmetic_replay" if gold_ok else "numeric_normalization_and_worked_solution_arithmetic_diagnostic",
                basis="source final answer matches and tagged arithmetic equations replay exactly" if gold_ok else "source-linked answer lacks complete arithmetic replay",
                evidence=ev, provenance=provenance,
                rationale="Source answer matches and all tagged equations were replayed exactly; this is not a human semantic re-solve." if gold_ok else "The source derivation could not be fully replayed; no correctness claim is made.",
                unresolved_reason=None if gold_ok else "worked-solution replay did not establish the result", candidate_index=0)
            source0["numeric_candidate_equals_gold"] = True
            source0["numeric_normalization"] = {"candidate_fraction": str(gold_value), "gold_fraction": str(gold_value)}
            output.append(new_canonical(source0, item, "research_dataset_v1"))

            alt = candidates[1]
            alternative = str(alt.get("answer", ""))
            neg_status = "unresolved"
            neg_method = "numeric_normalization_and_worked_solution_arithmetic_diagnostic"
            neg_basis = "candidate-generation metadata is not a correctness label"
            neg_evidence = ev
            neg_provenance = provenance
            neg_reason = "candidate requires question-semantic review unless the narrow controlled rule independently validates it"
            neg_rationale = "A difference from the benchmark answer and the gold+1 construction alone do not establish incorrectness."
            if include_negatives and gold_ok:
                predicate_row = {"dataset_id": str(row["id"]), "partition": item["partition"],
                                 "question": row["question"], "gold_answer": gold}
                control, _ = validate_gsm_discrete_count_negative(predicate_row, raw_gsm)
                alt_value = normalize_numeric(alternative)
                if control and gold_value is not None and alt_value == gold_value + 1:
                    neg_status = "verified_incorrect"
                    neg_method = "raw_worked_solution_source_match_plus_exact_rational_arithmetic_replay_and_distinct_integer_check"
                    neg_basis = "source worked-solution replay passed; exact discrete-count rule applies; candidate is gold + 1 and is a distinct integer count"
                    neg_evidence = ev + [{"kind": "controlled_discrete_count_validation", "transformation": "gold + 1",
                                          "replay": control["replay"], "source_solution_sha256": control["solution_sha256"]}]
                    neg_provenance = provenance | {"controlled_negative_method": "exact discrete-count increment",
                                                   "transformation": "gold + 1", "construction_version": "controlled_negative_candidates_v1"}
                    neg_reason = None
                    neg_rationale = "The independently replayed source derivation establishes the integer count; under the narrow discrete-count rule, the distinct count gold+1 is inconsistent with that result."
            source1 = source_candidate_record(row, alt, status=neg_status, method=neg_method, basis=neg_basis,
                evidence=neg_evidence, provenance=neg_provenance, rationale=neg_rationale,
                unresolved_reason=neg_reason, candidate_index=1)
            source1["numeric_candidate_equals_gold"] = normalize_numeric(alternative) == gold_value
            source1["candidate_generation_provenance"]["transformation"] = "gold + 1 as supplied by existing benchmark preprocessor"
            source1["numeric_normalization"] = {"candidate_fraction": str(normalize_numeric(alternative)) if normalize_numeric(alternative) is not None else None,
                                                "gold_fraction": str(gold_value) if gold_value is not None else None}
            output.append(new_canonical(source1, item, "research_dataset_v1"))
        else:
            dataset_id = str(row["id"])
            source = hotpot_raw_by_id.get(dataset_id.removeprefix("hotpot_")) if item["partition"] == "history" else None
            if item["partition"] == "history" and source is None:
                raise ValueError(f"HotpotQA History source missing from raw train: {dataset_id}")
            if source is not None and (source.get("question") != row.get("question") or str(source.get("answer")) != str(row.get("gold_answer"))):
                raise ValueError(f"HotpotQA History question/answer differs from raw source: {dataset_id}")
            if source is not None:
                raw_context = [{"title": title, "text": " ".join(sentences)} for title, sentences in
                               zip(source.get("context", {}).get("title", []), source.get("context", {}).get("sentences", []))]
                raw_support = [{"title": title, "sentence_id": sentence_id} for title, sentence_id in
                               zip(source.get("supporting_facts", {}).get("title", []), source.get("supporting_facts", {}).get("sent_id", []))]
                if raw_context != (row.get("context") or []) or raw_support != (row.get("supporting_facts") or []):
                    raise ValueError(f"HotpotQA History context/support differs from raw train source: {dataset_id}")
            context = row.get("context") or []
            supporting = row.get("supporting_facts") or []
            evidence, supports = make_supporting_evidence({"context": context, "supporting_facts": supporting},
                f"evaluation/datasets/unified/{item['partition']}.json")
            gold = str(row.get("gold_answer", ""))
            gold_match = str(candidates[0].get("answer", "")) == gold
            gold_ok = supports and gold_match
            provenance = {"source_file": f"evaluation/datasets/unified/{item['partition']}.json",
                          "raw_source_path": "evaluation/datasets/raw/hotpotqa/train" if item["partition"] == "history" else "unified development context",
                          "source_id": dataset_id, "source_split": "train" if item["partition"] == "history" else "validation (from prior preprocessing provenance; raw validation not opened)",
                          "supporting_facts": supporting,
                          "supporting_context_status": "supporting_fact_context_present" if supports else "supporting_fact_context_incomplete",
                          "context_hashes": [hashlib.sha256(str(entry.get("text", "")).encode("utf-8")).hexdigest() for entry in context]}
            source0 = source_candidate_record(row, candidates[0], status="verified_correct" if gold_ok else "unresolved",
                method="benchmark_source_answer_match_with_supporting_context_provenance" if gold_ok else "normalized_exact_match_and_token_f1_diagnostics",
                basis="benchmark source answer match; supporting-fact context paragraphs are present" if gold_ok else "answer/context provenance did not establish a supported benchmark answer",
                evidence=evidence, provenance=provenance,
                rationale="Candidate matches the benchmark answer and all supporting-fact references map to non-empty supplied context paragraphs; not a human semantic adjudication." if gold_ok else "The available context/reference did not establish the answer sufficiently.",
                unresolved_reason=None if gold_ok else "supporting context or source answer match is incomplete", candidate_index=0)
            source0["diagnostics"] = {"normalized_exact_match_to_gold": gold_match,
                                      "token_f1_to_gold": round(token_f1(str(candidates[0].get("answer", "")), gold), 8),
                                      "metrics_are_diagnostic_not_label_rules": True}
            output.append(new_canonical(source0, item, "research_dataset_v1"))

            alt = candidates[1]
            donor = recover_hotpot_donor(row, ordered_partition_rows[item["partition"]], str(alt.get("answer", "")))
            method = str(alt.get("source") or "synthetic_cross_example_answer")
            source1 = source_candidate_record(row, alt, status="unresolved",
                method="normalized_exact_match_and_token_f1_diagnostics",
                basis="borrowed answer is not treated as incorrect without target-question adjudication",
                evidence=evidence, provenance=provenance | {"donor_dataset_id": donor},
                rationale="A donor answer differing from the target gold may still answer the target question; no automatic incorrectness inference is made.",
                unresolved_reason="requires question-conditioned factual adjudication", candidate_index=1)
            source1["candidate_generation_method"] = method
            source1["candidate_generation_provenance"]["donor_dataset_id"] = donor
            source1["candidate_generation_provenance"]["donor_provenance_status"] = "recovered_by_replaying_partition_ordered_borrowing_rule" if donor else "not_recovered"
            source1["donor_dataset_id"] = donor
            source1["diagnostics"] = {"normalized_exact_match_to_gold": str(alt.get("answer", "")).casefold() == gold.casefold(),
                                      "token_f1_to_gold": round(token_f1(str(alt.get("answer", "")), gold), 8),
                                      "metrics_are_diagnostic_not_label_rules": True}
            if donor is None:
                source1["donor_provenance_status"] = "not_recovered"
            else:
                source1["donor_provenance_status"] = "recovered_by_replaying_partition_ordered_borrowing_rule"
            output.append(new_canonical(source1, item, "research_dataset_v1"))
    return output


def new_canonical(source: dict, item: dict, origin: str) -> dict:
    group = {"related_group_id": item["group_id"], "dataset_id": str(item["row"]["id"]),
             "partition": item["partition"], "question": item["row"]["question"],
             "gold_answer": item["row"].get("gold_answer")}
    canonical = canonical_row(source, group, origin=origin)
    canonical["construction_version"] = "research_dataset_pipeline_v1"
    canonical["source_candidate_record"] = source
    canonical["candidate_generation_provenance"] = source.get("candidate_generation_provenance")
    if source["correctness_status"] == "verified_incorrect" and source["benchmark"] == "GSM8K":
        # Preserve the original generated row's unresolved annotation while
        # recording the stronger, independent construction-specific basis.
        canonical["source_correctness_status"] = "unresolved"
        canonical["reconciliation"] = {"reconciliation_version": "research_dataset_pipeline_v1",
            "validation_method": source["validation_method"], "validation_basis": source["validation_basis"],
            "validation_evidence": source["validation_evidence"], "evidence_provenance": source["evidence_provenance"],
            "validation_rationale": source["validation_rationale"], "correctness_status": "verified_incorrect",
            "duplicate_observation_created": False}
    if source.get("donor_dataset_id") is not None:
        canonical["donor_dataset_id"] = source["donor_dataset_id"]
        canonical["donor_provenance_status"] = source["donor_provenance_status"]
    return canonical


def load_prior_groups(base_dir: Path) -> tuple[dict[str, dict], dict[str, list[dict]]]:
    rows_by_benchmark: dict[str, list[dict]] = {}
    groups_by_benchmark: dict[str, dict] = {}
    for benchmark in BENCHMARKS:
        rows = read_jsonl(base_dir / f"{benchmark.lower()}_reconciled.jsonl")
        roster = group_roster(rows, benchmark)
        rows_by_benchmark[benchmark] = rows
        groups_by_benchmark[benchmark] = roster
    return groups_by_benchmark, rows_by_benchmark


def apply_conservative_hotpot_label_policy(rows: list[dict]) -> list[dict]:
    """Keep explicit-negation source decisions visible but unresolved here."""
    result = []
    for original in rows:
        row = copy.deepcopy(original)
        method = row.get("validation_method")
        if (row.get("benchmark") == "HotpotQA"
                and row.get("correctness_status") == "verified_incorrect"
                and method == "source_answer_match_plus_supporting_fact_context_and_literal_negation_check"):
            row["source_correctness_status"] = row.get("source_correctness_status") or "verified_incorrect"
            row["prior_active_correctness_status"] = "verified_incorrect"
            row["correctness_status"] = "unresolved"
            row["unresolved_reason"] = "explicit negation and answer-string context match do not independently establish target-question incorrectness"
            basis = dict(row.get("validation_basis") or {})
            basis["prior_active_status"] = "verified_incorrect"
            basis["unresolved_reason"] = row["unresolved_reason"]
            basis["protocol_adjustment"] = "retained as unresolved pending question-conditioned factual verification"
            row["validation_basis"] = basis
            row["protocol_status_adjustment"] = "verified_incorrect_to_unresolved"
        result.append(row)
    return result


def read_unified(config: dict) -> tuple[dict[str, dict[str, list[dict]]], dict[str, list[dict]]]:
    by_part: dict[str, dict[str, list[dict]]] = {b: {p: [] for p in PARTITIONS} for b in BENCHMARKS}
    all_rows: dict[str, list[dict]] = {p: [] for p in PARTITIONS}
    for partition in PARTITIONS:
        path = resolve_path(config["sources"][f"unified_{partition}"])
        for row in json.loads(path.read_text(encoding="utf-8")):
            if row.get("benchmark") in BENCHMARKS:
                by_part[row["benchmark"]][partition].append(row)
                all_rows[partition].append(row)
    return by_part, all_rows


def build(config_path: Path) -> dict:
    config_path = config_path.resolve()
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    if config.get("final_test", {}).get("enabled") is not False or config.get("final_test", {}).get("source") is not None:
        raise ValueError("Final Test must remain disabled with a null source")
    if (config.get("candidate_generation", {}).get("correct_candidates_per_question") != 1
            or config.get("candidate_generation", {}).get("incorrect_candidates_per_question") != 1
            or config.get("candidate_generation", {}).get("hotpotqa_negative_method") != "synthetic_cross_example_answer"):
        raise ValueError("This version supports one inherited gold and one existing candidate per question; HotpotQA alternatives remain unresolved")
    if (config.get("quality_control", {}).get("deduplicate_questions") is not True
            or config.get("incremental", {}).get("enabled") is not True
            or config.get("incremental", {}).get("preserve_existing_ids") is not True):
        raise ValueError("Deduplication and ID-preserving incremental expansion must remain enabled")
    if config["quality_control"].get("retain_unresolved") is not True or config["quality_control"].get("exclude_unresolved_from_binary_examples") is not True:
        raise ValueError("Unresolved candidates must be retained and excluded from binary preparation")
    out_dir = resolve_path(config["output"]["reconciled_dir"])
    offline_dir = resolve_path(config["output"]["offline_preparation_dir"])
    for path in (out_dir, offline_dir):
        if path.exists() and any(path.iterdir()):
            raise FileExistsError(f"Refusing to overwrite non-empty versioned output: {path}")

    base_dir = resolve_path(config["incremental"]["base_dataset_dir"])
    prior_groups, prior_rows = load_prior_groups(base_dir)
    unified_by_part, all_unified_rows = read_unified(config)
    targets = {
        "GSM8K": {"history": int(config["benchmarks"]["gsm8k"]["history_groups"]), "development": int(config["benchmarks"]["gsm8k"]["development_groups"])},
        "HotpotQA": {"history": int(config["benchmarks"]["hotpotqa"]["history_groups"]), "development": int(config["benchmarks"]["hotpotqa"]["development_groups"])},
    }
    selected = {b: sample_incremental_groups(unified_by_part[b], b, prior_groups[b], targets[b], int(config["seed"])) for b in BENCHMARKS}
    selection_audit = {b: audit_selection_pool(unified_by_part[b], b, selected[b]) for b in BENCHMARKS}

    raw_gsm = load_from_disk(str(resolve_path(config["sources"]["gsm8k_train"])))
    raw_hotpot = load_from_disk(str(resolve_path(config["sources"]["hotpotqa_train"])))
    new_rows = {
        "GSM8K": make_new_rows(selected["GSM8K"], "GSM8K", raw_gsm, raw_hotpot, all_unified_rows, bool(config["candidate_generation"].get("include_controlled_negatives", True)), int(config["seed"])),
        "HotpotQA": make_new_rows(selected["HotpotQA"], "HotpotQA", raw_gsm, raw_hotpot, all_unified_rows, bool(config["candidate_generation"].get("include_controlled_negatives", True)), int(config["seed"])),
    }
    rows = {b: [*prior_rows[b], *new_rows[b]] for b in BENCHMARKS}
    rows["HotpotQA"] = apply_conservative_hotpot_label_policy(rows["HotpotQA"])
    rows = {b: sorted(values, key=lambda r: (PARTITIONS.index(r["partition"]), r["dataset_id"], r["candidate_id"])) for b, values in rows.items()}
    quality = validate_candidate_rows(rows, selected, targets)

    source_paths = [resolve_path(config["sources"][f"unified_{p}"]) for p in PARTITIONS]
    for key in ("gsm8k_train", "hotpotqa_train"):
        source_paths.extend(path for path in sorted(resolve_path(config["sources"][key]).glob("*")) if path.is_file())
    source_paths.extend(base_dir / name for name in ("gsm8k_reconciled.jsonl", "hotpotqa_reconciled.jsonl", "manifest.json", "validation_summary.json", "README.md"))
    source_paths.append(config_path)
    input_hashes = {str(path.relative_to(ROOT)).replace("\\", "/"): sha256_file(path) for path in source_paths}

    prepared, excluded = offline_adapter.prepare_rows(rows)
    offline_summary = offline_adapter.make_summary(prepared, excluded)
    candidate_files = {
        "gsm8k_reconciled.jsonl": jsonl_bytes(rows["GSM8K"]),
        "hotpotqa_reconciled.jsonl": jsonl_bytes(rows["HotpotQA"]),
        "history_candidates.jsonl": jsonl_bytes([r for b in BENCHMARKS for r in rows[b] if r["partition"] == "history"]),
        "development_candidates.jsonl": jsonl_bytes([r for b in BENCHMARKS for r in rows[b] if r["partition"] == "development"]),
        "unresolved_candidates.jsonl": jsonl_bytes([r for b in BENCHMARKS for r in rows[b] if r["correctness_status"] == "unresolved"]),
        "validation_summary.json": json_bytes({"dataset_version": config["dataset_version"], "quality": quality, "offline_label_preparation": offline_summary,
            "attempt_records": 0, "complete_offline_examples": 0, "policy_fitting_ready": False}),
        "README.md": ("# Research candidate dataset\n\n" +
            "History/Development candidate data only. Unresolved candidates remain explicit and are excluded from binary label preparation. "
            "The offline files are preparation rows, not verifier Attempts or offline Example objects. Final Test is disabled and was not read.\n").encode("utf-8"),
    }
    offline_files = {
        "history_prepared.jsonl": jsonl_bytes(prepared["history"]),
        "development_prepared.jsonl": jsonl_bytes(prepared["development"]),
        "excluded_unresolved.jsonl": jsonl_bytes(excluded),
        "validation_summary.json": json_bytes(offline_summary),
        "README.md": ("# Offline label preparation\n\nPrepared labels only: no genuine verifier Attempts or complete Example records were supplied or fabricated.\n").encode("utf-8"),
    }
    output_hashes = {name: digest_bytes(data) for name, data in sorted(candidate_files.items())}
    offline_hashes = {name: digest_bytes(data) for name, data in sorted(offline_files.items())}
    manifest_core = {
        "dataset_version": config["dataset_version"], "created_date": date.today().isoformat(),
        "seed": int(config["seed"]), "configuration": config,
        "source_versions": SOURCE_VERSION, "source_paths_read": [str(p.relative_to(ROOT)).replace("\\", "/") for p in source_paths if p != config_path],
        "source_sha256": input_hashes, "output_sha256": output_hashes,
        "offline_preparation_path": str(offline_dir.relative_to(ROOT)).replace("\\", "/"),
        "offline_output_sha256": offline_hashes, "counts": quality,
        "candidate_generation_methods": {"GSM8K": ["benchmark_gold", "synthetic_numeric_perturbation"],
            "HotpotQA": ["benchmark_gold", "synthetic_cross_example_answer"]},
        "label_quality": {"human_adjudication_claimed": False, "unresolved_preserved": True,
            "hotpotqa_borrowed_candidates_automatically_incorrect": False,
            "prior_explicit_negation_statuses_demoted_to_unresolved": sum(r.get("protocol_status_adjustment") == "verified_incorrect_to_unresolved" for r in rows["HotpotQA"]),
            "gsm8k_incorrectness_rule": "narrow discrete-count +1 rule with independently replayed source equations"},
        "incremental": {"prior_groups_preserved": True, "new_groups_selected_only": True,
            "reused_group_counts": {b: len(prior_groups[b]) for b in BENCHMARKS},
            "added_group_counts": {b: sum(not item["reused"] for item in selected[b]) for b in BENCHMARKS}},
        "selected_question_roster": {b: [{"dataset_id": str(item["row"]["id"]), "related_group_id": item["group_id"],
            "partition": item["partition"], "reused_from_prior": item["reused"]} for item in selected[b]] for b in BENCHMARKS},
        "selected_candidate_ids": {b: [row["candidate_id"] for row in rows[b]] for b in BENCHMARKS},
        "selection_audit": selection_audit,
        "partition_overlap_report": {b: {"history_development_group_overlap": 0} for b in BENCHMARKS},
        "final_test_enabled": False, "final_test_records_or_identities_accessed": False,
        "attempt_records": 0, "complete_offline_examples": 0, "policy_fitting_ready": False,
    }
    candidate_files["manifest.json"] = json_bytes({**manifest_core, "manifest_sha256": digest_bytes(json_bytes(manifest_core))})
    write_new_files(out_dir, candidate_files)
    write_new_files(offline_dir, offline_files)
    return validate(out_dir)


def write_new_files(directory: Path, files: dict[str, bytes]) -> None:
    if directory.exists() and any(directory.iterdir()):
        raise FileExistsError(f"Refusing to overwrite non-empty directory: {directory}")
    directory.mkdir(parents=True, exist_ok=True)
    for name, data in sorted(files.items()):
        with (directory / name).open("xb") as stream:
            stream.write(data)


def validate_candidate_rows(rows: dict[str, list[dict]], selected: dict[str, list[dict]], targets: dict[str, dict[str, int]]) -> dict:
    all_ids: list[str] = []
    result: dict[str, Any] = {}
    for benchmark in BENCHMARKS:
        candidates = rows[benchmark]
        ids = [row.get("candidate_id") for row in candidates]
        if len(ids) != len(set(ids)):
            raise ValueError(f"{benchmark}: duplicate canonical candidate IDs")
        all_ids.extend(ids)
        roster = {item["group_id"]: item for item in selected[benchmark]}
        if len(roster) != len(selected[benchmark]):
            raise ValueError(f"{benchmark}: duplicate question groups")
        if {row.get("related_group_id") for row in candidates} != set(roster):
            raise ValueError(f"{benchmark}: candidate group roster differs from sampled group roster")
        by_part: dict[str, list[dict]] = {p: [r for r in candidates if r["partition"] == p] for p in PARTITIONS}
        assignments: dict[str, set[str]] = collections.defaultdict(set)
        per_part = {}
        for partition, part_rows in by_part.items():
            groups = {row["related_group_id"] for row in part_rows}
            if len(groups) != targets[benchmark][partition]:
                raise ValueError(f"{benchmark}/{partition}: group count mismatch")
            for row in part_rows:
                if row.get("benchmark") != benchmark or row.get("partition") != partition:
                    raise ValueError("Candidate benchmark/partition mismatch")
                if row["dataset_id"] != roster[row["related_group_id"]]["row"]["id"]:
                    raise ValueError("Candidate dataset ID does not match parent group")
                assignments[row["related_group_id"]].add(partition)
                if row["correctness_status"] not in {"verified_correct", "verified_incorrect", "unresolved"}:
                    raise ValueError("Invalid correctness status")
                if row["benchmark"] == "HotpotQA" and row.get("candidate_source") == "synthetic_cross_example_answer" and row["correctness_status"] == "verified_incorrect":
                    raise ValueError("Borrowed HotpotQA answer cannot be auto-labelled incorrect")
                if row["correctness_status"] == "verified_incorrect" and not row.get("validation_method"):
                    raise ValueError("Verified incorrect candidate lacks validation basis")
                unresolved_reason = row.get("unresolved_reason") or (row.get("validation_basis") or {}).get("unresolved_reason")
                if row["correctness_status"] == "unresolved" and not unresolved_reason:
                    raise ValueError("Unresolved candidate lacks unresolved reason")
            counts = collections.Counter(row["correctness_status"] for row in part_rows)
            per_part[partition] = {"candidate_records": len(part_rows), "groups": len(groups),
                                   "verified_correct": counts["verified_correct"], "verified_incorrect": counts["verified_incorrect"],
                                   "unresolved": counts["unresolved"]}
        if any(len(parts) != 1 for parts in assignments.values()):
            raise ValueError(f"{benchmark}: History/Development group leakage")
        duplicate_answer_groups = sum(
            1 for group in roster
            if len([r["candidate_answer"] for r in candidates if r["related_group_id"] == group])
            != len({r["candidate_answer"] for r in candidates if r["related_group_id"] == group})
        )
        result[benchmark] = {"partitions": per_part, "candidate_records": len(candidates), "question_groups": len(roster),
                             "verified_correct": sum(r["correctness_status"] == "verified_correct" for r in candidates),
                             "verified_incorrect": sum(r["correctness_status"] == "verified_incorrect" for r in candidates),
                             "unresolved": sum(r["correctness_status"] == "unresolved" for r in candidates),
                             "reused_groups": sum(item["reused"] for item in selected[benchmark]),
                             "added_groups": sum(not item["reused"] for item in selected[benchmark]),
                             "candidate_generation_method_counts": dict(sorted(collections.Counter(str(r.get("candidate_generation_method")) for r in candidates).items())),
                             "duplicate_report": {"canonical_candidate_ids_unique": True, "group_ids_unique": True,
                                 "duplicate_candidate_answer_text_groups": duplicate_answer_groups}}
    if len(all_ids) != len(set(all_ids)):
        raise ValueError("Canonical candidate ID collision across benchmarks")
    return {"benchmarks": result, "combined": {"question_groups": sum(x["question_groups"] for x in result.values()),
            "candidate_records": len(all_ids), "verified_correct": sum(x["verified_correct"] for x in result.values()),
            "verified_incorrect": sum(x["verified_incorrect"] for x in result.values()), "unresolved": sum(x["unresolved"] for x in result.values()),
            "complete_verifier_attempt_records": 0, "complete_offline_Examples": 0}}


def validate(output_dir: Path) -> dict:
    manifest = json.loads((output_dir / "manifest.json").read_text(encoding="utf-8"))
    core = {key: value for key, value in manifest.items() if key != "manifest_sha256"}
    if digest_bytes(json_bytes(core)) != manifest.get("manifest_sha256"):
        raise ValueError("Dataset manifest digest mismatch")
    for name, digest in manifest["output_sha256"].items():
        if sha256_file(output_dir / name) != digest:
            raise ValueError(f"Dataset output hash mismatch: {name}")
    offline_dir = resolve_path(manifest["offline_preparation_path"])
    for name, digest in manifest["offline_output_sha256"].items():
        if sha256_file(offline_dir / name) != digest:
            raise ValueError(f"Offline preparation output hash mismatch: {name}")
    all_rows = {b: read_jsonl(output_dir / f"{b.lower()}_reconciled.jsonl") for b in BENCHMARKS}
    groupmaps = {}
    selected = {}
    for b in BENCHMARKS:
        groupmaps[b] = group_roster(all_rows[b], b)
        selected[b] = [{"group_id": group, "partition": identity["partition"], "row": {"id": identity["dataset_id"]}, "reused": False} for group, identity in groupmaps[b].items()]
    targets = {b: {p: sum(1 for row in all_rows[b] if row["partition"] == p and row["source_candidate_index"] == 0) for p in PARTITIONS} for b in BENCHMARKS}
    # Count groups rather than candidates; roster has one entry per source question.
    for b in BENCHMARKS:
        for p in PARTITIONS:
            targets[b][p] = sum(identity["partition"] == p for identity in groupmaps[b].values())
    summary = validate_candidate_rows(all_rows, selected, targets)
    for b in BENCHMARKS:
        summary["benchmarks"][b]["reused_groups"] = manifest["incremental"]["reused_group_counts"][b]
        summary["benchmarks"][b]["added_groups"] = manifest["incremental"]["added_group_counts"][b]
    persisted = json.loads((output_dir / "validation_summary.json").read_text(encoding="utf-8"))
    if persisted.get("quality") != summary:
        raise ValueError("Persisted quality summary differs from candidate rows")
    if manifest.get("final_test_enabled") is not False or manifest.get("final_test_records_or_identities_accessed") is not False:
        raise ValueError("Final Test must remain disabled and unopened")
    for relative, digest in manifest["source_sha256"].items():
        source = ROOT / relative
        if not source.is_file() or sha256_file(source) != digest:
            raise ValueError(f"Source hash mismatch: {relative}")
    if manifest.get("attempt_records") != 0 or manifest.get("complete_offline_examples") != 0:
        raise ValueError("Pipeline must not fabricate Attempts/Examples")
    return {"passed": True, "summary": summary, "checks": {"manifest_and_output_hashes_match": True,
        "candidate_ids_unique": True, "group_ids_unique_per_benchmark": True, "history_development_disjoint": True,
        "unresolved_retained": True, "borrowed_hotpot_negatives_not_auto_labelled": True,
        "final_test_not_accessed": True, "no_attempt_or_example_fabrication": True}}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    build_p = sub.add_parser("build")
    build_p.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    valid_p = sub.add_parser("validate")
    valid_p.add_argument("--dataset-dir", type=Path, required=True)
    args = parser.parse_args()
    report = build(args.config) if args.command == "build" else validate(args.dataset_dir)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
