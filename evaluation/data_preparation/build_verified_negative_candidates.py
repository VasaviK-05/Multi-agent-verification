"""Build controlled, evidence-backed negative candidates from the verified H/D subset.

This builder reads the existing verified subset v1, GSM8K raw train only, and
never opens Final Test or HotpotQA's mixed raw validation split. It writes a
new versioned directory and refuses to overwrite non-empty output.
"""

from __future__ import annotations

import argparse
import collections
import hashlib
import json
import random
import re
import sys
from datetime import date
from pathlib import Path
from typing import Any

from datasets import load_from_disk

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from evaluation.data_preparation.build_verified_subset import (  # noqa: E402
    normalize_numeric,
    replay_gsm_solution,
)


SOURCE_DIR = ROOT / "evaluation/datasets/verified_subset/v1_seed_20261104"
RAW_GSM_TRAIN = ROOT / "evaluation/datasets/raw/gsm8k/train"
DEFAULT_SEED = 20261105
DEFAULT_OUTPUT = ROOT / "evaluation/datasets/verified_negative_candidates/v1"
PARTITIONS = ("history", "development")
QUOTAS = {"history": 40, "development": 10}
MAX_PER_BENCHMARK = 50
VALID_STATUSES = {"verified_correct", "verified_incorrect", "unresolved"}
ROUNDING_OR_APPROX = re.compile(r"round(?:ed|ing)?|nearest|approximately|approx\.?|about|roughly|estimate", re.I)
GSM_RATIO_CUE = re.compile(r"percentage|percent|%|ratio|probability|fraction|how many times", re.I)
HOT_PUNCT = re.compile(r"[^a-z0-9]+")
HOT_ARTICLES = {"a", "an", "the"}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def hash_tree_files(directory: Path) -> dict[str, str]:
    return {
        str(path.relative_to(ROOT)).replace("\\", "/"): sha256_file(path)
        for path in sorted(directory.glob("*")) if path.is_file()
    }


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_jsonl(path: Path, rows: list[dict]) -> None:
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        for row in rows:
            stream.write(json.dumps(row, ensure_ascii=False) + "\n")


def hot_tokens(text: object) -> list[str]:
    return [token for token in HOT_PUNCT.sub(" ", str(text).lower()).split() if token and token not in HOT_ARTICLES]


def phrase_in(text: object, phrase: object) -> bool:
    haystack = hot_tokens(text)
    needle = hot_tokens(phrase)
    return bool(needle) and any(haystack[index:index + len(needle)] == needle for index in range(len(haystack) - len(needle) + 1))


def stratified_sample(pool_by_partition: dict[str, list[dict]], seed: int, benchmark_offset: int) -> list[dict]:
    selected: list[dict] = []
    for offset, partition in enumerate(PARTITIONS):
        pool = sorted(pool_by_partition[partition], key=lambda row: row["dataset_id"])
        take = min(QUOTAS[partition], len(pool))
        selected.extend(random.Random(seed + benchmark_offset * 100 + offset).sample(pool, take))
    return sorted(selected, key=lambda row: (row["partition"], row["dataset_id"]))


def gsm_replay_pool(gsm_rows: list[dict], raw_train: Any) -> tuple[dict[str, list[dict]], list[dict]]:
    by_partition = {partition: [] for partition in PARTITIONS}
    skipped: list[dict] = []
    source_gold = {
        row.get("candidate_id"): row
        for row in read_jsonl(SOURCE_DIR / "gsm8k_verified.jsonl")
    }
    for row in gsm_rows:
        if row.get("source_candidate_index") != 0 or row.get("correctness_status") != "verified_correct":
            continue
        candidate_gold = source_gold.get(f"{row['dataset_id']}::candidate_0")
        # The verified subset is immutable; its gold candidate record must match
        # the candidate selected above before any controlled mutation is made.
        if candidate_gold is None or candidate_gold.get("correctness_status") != "verified_correct":
            raise ValueError(f"Missing source-matched verified GSM8K gold record: {row['dataset_id']}")
        checked, reason = validate_gsm_discrete_count_negative(row, raw_train)
        if checked is None:
            skipped.append({"dataset_id": row.get("dataset_id"), "reason": reason})
            continue
        by_partition[row["partition"]].append(checked)
    return by_partition, skipped


def validate_gsm_discrete_count_negative(row: dict, raw_train: Any) -> tuple[dict | None, str | None]:
    """Apply the pilot's narrow +1 validation rule to any train question.

    This reusable predicate intentionally accepts only exact discrete-count
    questions with a fully replayable source derivation. It does not use the
    candidate-generation operation as its validation evidence.
    """
    question = str(row.get("question", ""))
    gold = str(row.get("gold_answer", ""))
    value = normalize_numeric(gold)
    if value is None or value.denominator != 1:
        return None, "answer is not an exact integer"
    if "how many" not in question.lower() or GSM_RATIO_CUE.search(question):
        return None, "not an unambiguous discrete-count candidate under the controlled rule"
    if ROUNDING_OR_APPROX.search(question):
        return None, "question indicates rounding or approximation"
    match = re.fullmatch(r"gsm8k_train_(\d+)", str(row.get("dataset_id", "")))
    if not match or row.get("partition") not in PARTITIONS:
        return None, "source ID/partition is outside allowed History/Development raw train"
    source_index = int(match.group(1))
    source = raw_train[source_index]
    if source.get("question") != question:
        raise ValueError(f"GSM8K source question mismatch: {row['dataset_id']}")
    answer = str(source["answer"])
    replay = replay_gsm_solution(answer, gold)
    if replay.get("status") != "passed":
        return None, "worked-solution arithmetic replay was incomplete"
    if ROUNDING_OR_APPROX.search(answer):
        return None, "worked solution indicates rounding or approximation"
    return {
        "dataset_id": row["dataset_id"],
        "partition": row["partition"],
        "question": question,
        "gold_answer": gold,
        "source_index": source_index,
        "source_solution": answer,
        "solution_sha256": hashlib.sha256(answer.encode("utf-8")).hexdigest(),
        "replay": replay,
    }, None


def hotpot_pool(hotpot_rows: list[dict]) -> tuple[dict[str, list[dict]], list[dict]]:
    by_partition = {partition: [] for partition in PARTITIONS}
    skipped: list[dict] = []
    for row in hotpot_rows:
        if row.get("source_candidate_index") != 0 or row.get("correctness_status") != "verified_correct":
            continue
        if row.get("partition") not in PARTITIONS:
            continue
        gold = str(row.get("gold_answer", "")).strip()
        tokens = hot_tokens(gold)
        if not 2 <= len(tokens) <= 5 or gold.lower() in {"yes", "no"}:
            skipped.append({"dataset_id": row.get("dataset_id"), "reason": "answer is not a concise factual phrase suitable for explicit-negation control"})
            continue
        if re.search(r"\b(or|either|possibly|perhaps|uncertain|approximately)\b", str(row.get("question", "")), re.I):
            skipped.append({"dataset_id": row.get("dataset_id"), "reason": "question wording signals potential ambiguity"})
            continue
        evidence = [item for item in row.get("validation_evidence", []) if item.get("kind") == "benchmark_context_paragraph_for_supporting_fact"]
        matching = [item for item in evidence if phrase_in(item.get("text", ""), gold)]
        if not matching:
            skipped.append({"dataset_id": row.get("dataset_id"), "reason": "canonical answer phrase not found in supplied supporting-fact paragraphs"})
            continue
        support_refs = row.get("evidence_provenance", {}).get("supporting_facts", [])
        matched_refs = {(item.get("title"), item.get("sentence_id")) for item in matching}
        if not any((fact.get("title"), fact.get("sentence_id")) in matched_refs for fact in support_refs):
            skipped.append({"dataset_id": row.get("dataset_id"), "reason": "matching context paragraph lacks a supporting-fact reference"})
            continue
        by_partition[row["partition"]].append({
            "dataset_id": row["dataset_id"],
            "partition": row["partition"],
            "question": row["question"],
            "gold_answer": gold,
            "supporting_facts": support_refs,
            "supporting_evidence": matching,
            "source_record": row,
        })
    return by_partition, skipped


def build(seed: int, output_dir: Path) -> dict:
    if output_dir.exists() and any(output_dir.iterdir()):
        raise FileExistsError(f"Refusing to overwrite non-empty output directory: {output_dir}")
    gsm_verified_path = SOURCE_DIR / "gsm8k_verified.jsonl"
    hotpot_verified_path = SOURCE_DIR / "hotpotqa_verified.jsonl"
    gsm_rows = read_jsonl(gsm_verified_path)
    hotpot_rows = read_jsonl(hotpot_verified_path)
    raw_train = load_from_disk(str(RAW_GSM_TRAIN))
    gsm_pool, gsm_skipped = gsm_replay_pool(gsm_rows, raw_train)
    hotpot_candidates, hotpot_skipped = hotpot_pool(hotpot_rows)
    gsm_selected = stratified_sample(gsm_pool, seed, 0)
    hotpot_selected = stratified_sample(hotpot_candidates, seed, 1)

    gsm_output: list[dict] = []
    for item in gsm_selected[:MAX_PER_BENCHMARK]:
        gold_value = normalize_numeric(item["gold_answer"])
        alternative = gold_value + 1
        alternative_text = str(alternative.numerator) if alternative.denominator == 1 else f"{alternative.numerator}/{alternative.denominator}"
        if alternative == gold_value:
            raise ValueError(f"GSM8K transformation did not change value: {item['dataset_id']}")
        candidate_id = f"{item['dataset_id']}::controlled_increment_seed_{seed}"
        gsm_output.append({
            "candidate_id": candidate_id,
            "dataset_id": item["dataset_id"],
            "benchmark": "GSM8K",
            "dataset_version": "openai/gsm8k main@740312add88f781978c0658806c59bc2815b9866",
            "partition": item["partition"],
            "question": item["question"],
            "gold_answer": item["gold_answer"],
            "candidate_answer": alternative_text,
            "correctness_status": "verified_incorrect",
            "candidate_generation_method": "controlled_increment_one_in_same_implicit_discrete_answer_unit",
            "validation_method": "raw_worked_solution_source_match_plus_exact_rational_arithmetic_replay_and_distinct_integer_check",
            "validation_evidence": [{
                "kind": "original_benchmark_worked_solution",
                "source_path": "evaluation/datasets/raw/gsm8k/train",
                "source_split": "train",
                "source_row_index": item["source_index"],
                "solution_sha256": item["solution_sha256"],
                "final_answer": item["gold_answer"],
                "arithmetic_replay": item["replay"],
            }],
            "evidence_provenance": {
                "source_question_id": item["dataset_id"],
                "unified_source_subset": "evaluation/datasets/verified_subset/v1_seed_20261104/gsm8k_verified.jsonl",
                "raw_source_path": "evaluation/datasets/raw/gsm8k/train",
                "source_row_index": item["source_index"],
                "answer_unit": "same implicit discrete unit requested by the question; numeric benchmark-answer format retained",
                "rounding_or_fraction_ambiguity_filter": "exact integer answer, full equation replay, no rounding/approximation cue, quantity question begins with 'how many', and percentage/ratio/fraction questions excluded",
            },
            "validation_rationale": "The raw benchmark question and final answer match the source record. Every tagged worked-solution equation was independently recomputed with exact rational arithmetic, and the terminal checked result matches the source answer. The controlled candidate is exactly one whole unit above that integer result, in the same implicit requested unit; numeric normalization confirms it is not an equivalent representation. Under the benchmark's unique exact-count answer, the alternative is inconsistent.",
            "validation_confidence_category": "high_under_exact_GSM8K_answer_semantics",
            "unresolved_reason": None,
            "numeric_comparison": {
                "gold_fraction": str(gold_value),
                "candidate_fraction": str(alternative),
                "difference_in_requested_units": "1",
                "equivalent_after_normalization": False,
            },
            "independent_framework_judgment": False,
        })

    hotpot_output: list[dict] = []
    for item in hotpot_selected[:MAX_PER_BENCHMARK]:
        source = item["source_record"]
        candidate_id = f"{item['dataset_id']}::explicit_negation_seed_{seed}"
        evidence = item["supporting_evidence"]
        hotpot_output.append({
            "candidate_id": candidate_id,
            "dataset_id": item["dataset_id"],
            "benchmark": "HotpotQA",
            "dataset_version": "hotpotqa/hotpot_qa distractor@1908d6afbbead072334abe2965f91bd2709910ab",
            "partition": item["partition"],
            "question": item["question"],
            "gold_answer": item["gold_answer"],
            "candidate_answer": f"The answer is not {item['gold_answer']}.",
            "correctness_status": "verified_incorrect",
            "candidate_generation_method": "explicit_negation_of_context_supported_benchmark_answer",
            "validation_method": "source_answer_match_plus_supporting_fact_context_and_literal_negation_check",
            "validation_evidence": evidence,
            "evidence_provenance": {
                "source_question_id": item["dataset_id"],
                "unified_source_subset": "evaluation/datasets/verified_subset/v1_seed_20261104/hotpotqa_verified.jsonl",
                "source_context_condition": "benchmark-context-assisted; no shared-corpus retrieval claim",
                "supporting_facts": item["supporting_facts"],
                "gold_phrase_present_in_supporting_fact_paragraph": True,
                "support_fact_sentence_boundaries_available": all(e.get("sentence_text_extracted") is True for e in evidence),
                "paragraph_hashes": [hashlib.sha256(str(e.get("text", "")).encode("utf-8")).hexdigest() for e in evidence],
            },
            "validation_rationale": "The generated response explicitly denies the canonical answer. The benchmark source record identifies that answer, and the cited supporting-fact paragraph(s) contain the answer phrase, providing context provenance for the supported proposition. The candidate is therefore a deliberately constructed contradiction under the benchmark's single-answer interpretation; this is not a claim about natural error prevalence.",
            "validation_confidence_category": "high_for_explicit_negation_under_benchmark_answer_semantics",
            "unresolved_reason": None,
            "diagnostics": {
                "candidate_explicitly_negates_gold": True,
                "gold_phrase_found_in_cited_supporting_context": True,
                "answer_string_mismatch_used_as_sole_evidence": False,
            },
            "independent_framework_judgment": False,
        })

    output_dir.mkdir(parents=True, exist_ok=True)
    write_jsonl(output_dir / "gsm8k_negative_candidates.jsonl", gsm_output)
    write_jsonl(output_dir / "hotpotqa_negative_candidates.jsonl", hotpot_output)
    selected_counts = {
        "GSM8K": dict(collections.Counter(row["partition"] for row in gsm_output)),
        "HotpotQA": dict(collections.Counter(row["partition"] for row in hotpot_output)),
    }
    source_paths = [gsm_verified_path, hotpot_verified_path, SOURCE_DIR / "subset_manifest.json", *sorted(RAW_GSM_TRAIN.glob("*"))]
    manifest = {
        "dataset_version": "verified-negative-candidates-v1",
        "created_date": date.today().isoformat(),
        "random_seed": seed,
        "target_candidates_per_benchmark": MAX_PER_BENCHMARK,
        "generated_candidates": {"GSM8K": len(gsm_output), "HotpotQA": len(hotpot_output)},
        "selection_method": "stratified random sample without replacement from exact validated candidate pools, sorted by source dataset ID; target 40 History and 10 Development per benchmark",
        "partition_candidate_counts": selected_counts,
        "selected_dataset_ids": {
            "GSM8K": [row["dataset_id"] for row in gsm_output],
            "HotpotQA": [row["dataset_id"] for row in hotpot_output],
        },
        "selected_candidate_ids": {
            "GSM8K": [row["candidate_id"] for row in gsm_output],
            "HotpotQA": [row["candidate_id"] for row in hotpot_output],
        },
        "source_paths": {
            "verified_subset_v1_gsm8k": "evaluation/datasets/verified_subset/v1_seed_20261104/gsm8k_verified.jsonl",
            "verified_subset_v1_hotpotqa": "evaluation/datasets/verified_subset/v1_seed_20261104/hotpotqa_verified.jsonl",
            "verified_subset_manifest": "evaluation/datasets/verified_subset/v1_seed_20261104/subset_manifest.json",
            "gsm8k_raw_source": "evaluation/datasets/raw/gsm8k/train (train only)",
            "hotpotqa_context_source": "the selected History/Development rows in verified subset v1; raw mixed validation split not opened",
        },
        "source_sha256": {
            str(path.relative_to(ROOT)).replace("\\", "/"): sha256_file(path)
            for path in source_paths if path.is_file()
        },
        "candidate_construction": {
            "GSM8K": "gold + 1 exact integer in the same implicit discrete unit, restricted to fully replayed unique integer-count solutions without rounding/ratio cues",
            "HotpotQA": "explicit natural-language negation of a short gold phrase that occurs in a cited supporting-fact context paragraph",
        },
        "final_test_included": False,
        "final_test_records_read": False,
        "shared_corpus_retrieval_claimed": False,
        "framework_used_as_correctness_judge": False,
        "original_verified_subset_modified": False,
        "original_benchmark_or_adjudication_files_modified": False,
        "skipped_candidate_counts": {"GSM8K": len(gsm_skipped), "HotpotQA": len(hotpot_skipped)},
        "skipped_reason_counts": {
            "GSM8K": dict(collections.Counter(row["reason"] for row in gsm_skipped)),
            "HotpotQA": dict(collections.Counter(row["reason"] for row in hotpot_skipped)),
        },
    }
    (output_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    summary = summarize(gsm_output, hotpot_output, selected_counts, gsm_skipped, hotpot_skipped, seed)
    (output_dir / "validation_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (output_dir / "README.md").write_text(README, encoding="utf-8")
    return validate(output_dir)


def summarize(gsm: list[dict], hotpot: list[dict], partitions: dict, gsm_skipped: list[dict], hotpot_skipped: list[dict], seed: int) -> dict:
    benchmarks = {}
    for name, rows, skipped in (("GSM8K", gsm, gsm_skipped), ("HotpotQA", hotpot, hotpot_skipped)):
        statuses = collections.Counter(row["correctness_status"] for row in rows)
        benchmarks[name] = {
            "generated_candidates": len(rows),
            "verified_correct": statuses.get("verified_correct", 0),
            "verified_incorrect": statuses.get("verified_incorrect", 0),
            "unresolved": statuses.get("unresolved", 0),
            "partition_counts": partitions[name],
            "validation_methods": dict(collections.Counter(row["validation_method"] for row in rows)),
            "pool_candidates_skipped": len(skipped),
            "skip_reasons": dict(collections.Counter(row["reason"] for row in skipped)),
        }
    return {
        "seed": seed,
        "benchmarks": benchmarks,
        "combined": {
            "generated_candidates": len(gsm) + len(hotpot),
            "verified_correct": sum(row["correctness_status"] == "verified_correct" for row in gsm + hotpot),
            "verified_incorrect": sum(row["correctness_status"] == "verified_incorrect" for row in gsm + hotpot),
            "unresolved": sum(row["correctness_status"] == "unresolved" for row in gsm + hotpot),
        },
        "interpretation": "Unresolved is not counted as verified incorrect; generated negative status is conditional on the documented exact benchmark-answer semantics.",
    }


def validate(output_dir: Path) -> dict:
    manifest = json.loads((output_dir / "manifest.json").read_text(encoding="utf-8"))
    for relative_path, expected_hash in manifest.get("source_sha256", {}).items():
        source_path = ROOT / relative_path
        if not source_path.is_file() or sha256_file(source_path) != expected_hash:
            raise ValueError(f"Source hash mismatch or missing source: {relative_path}")
    files = {
        "GSM8K": read_jsonl(output_dir / "gsm8k_negative_candidates.jsonl"),
        "HotpotQA": read_jsonl(output_dir / "hotpotqa_negative_candidates.jsonl"),
    }
    candidate_ids: list[str] = []
    dataset_ids: dict[str, list[str]] = {}
    report = {"passed": True, "benchmarks": {}, "checks": {}}
    for benchmark, rows in files.items():
        ids = [row.get("candidate_id") for row in rows]
        source_ids = [row.get("dataset_id") for row in rows]
        if len(ids) != len(set(ids)) or len(source_ids) != len(set(source_ids)):
            raise ValueError(f"{benchmark}: duplicate candidate/dataset IDs")
        if any(row.get("partition") not in PARTITIONS for row in rows):
            raise ValueError(f"{benchmark}: Final Test/unknown partition found")
        if any(row.get("correctness_status") not in VALID_STATUSES for row in rows):
            raise ValueError(f"{benchmark}: invalid correctness status")
        source_records = read_jsonl(SOURCE_DIR / f"{benchmark.lower()}_verified.jsonl")
        group_by_id = {record["dataset_id"]: record.get("related_group_id") for record in source_records}
        selected_groups = [group_by_id.get(source_id) for source_id in source_ids]
        if any(group_id is None for group_id in selected_groups):
            raise ValueError(f"{benchmark}: selected source record lacks a related-group ID")
        if len(selected_groups) != len(set(selected_groups)):
            raise ValueError(f"{benchmark}: related-example group leakage within selected set")
        for row in rows:
            if not row.get("evidence_provenance") or not row.get("validation_evidence") or not row.get("validation_rationale"):
                raise ValueError(f"{row.get('candidate_id')}: missing evidence/provenance/rationale")
            if row["correctness_status"] == "verified_incorrect" and not row.get("validation_method"):
                raise ValueError(f"{row.get('candidate_id')}: verified incorrect lacks validation method")
            if row["correctness_status"] == "unresolved" and not row.get("unresolved_reason"):
                raise ValueError(f"{row.get('candidate_id')}: unresolved reason missing")
            if benchmark == "GSM8K" and row["correctness_status"] == "verified_incorrect":
                if row["validation_evidence"][0].get("arithmetic_replay", {}).get("status") != "passed":
                    raise ValueError(f"{row.get('candidate_id')}: GSM8K negative lacks full independent arithmetic replay")
                if normalize_numeric(row["gold_answer"]) == normalize_numeric(row["candidate_answer"]):
                    raise ValueError(f"{row.get('candidate_id')}: GSM8K candidate is numerically equivalent to gold")
                if row.get("numeric_comparison", {}).get("difference_in_requested_units") != "1":
                    raise ValueError(f"{row.get('candidate_id')}: GSM8K transformation is not the declared +1")
            if benchmark == "HotpotQA" and row["correctness_status"] == "verified_incorrect":
                if row.get("diagnostics", {}).get("candidate_explicitly_negates_gold") is not True:
                    raise ValueError(f"{row.get('candidate_id')}: HotpotQA candidate is not an explicit negation")
                if not row.get("evidence_provenance", {}).get("gold_phrase_present_in_supporting_fact_paragraph"):
                    raise ValueError(f"{row.get('candidate_id')}: HotpotQA negative lacks gold phrase in supporting context")
        candidate_ids.extend(ids)
        dataset_ids[benchmark] = source_ids
        statuses = collections.Counter(row["correctness_status"] for row in rows)
        report["benchmarks"][benchmark] = {
            "generated_candidates": len(rows),
            "verified_correct": statuses.get("verified_correct", 0),
            "verified_incorrect": statuses.get("verified_incorrect", 0),
            "unresolved": statuses.get("unresolved", 0),
            "history": sum(row["partition"] == "history" for row in rows),
            "development": sum(row["partition"] == "development" for row in rows),
            "validation_methods": dict(collections.Counter(row["validation_method"] for row in rows)),
        }
    if len(candidate_ids) != len(set(candidate_ids)):
        raise ValueError("Duplicate candidate IDs across benchmarks")
    for benchmark, rows in files.items():
        if [row["candidate_id"] for row in rows] != manifest["selected_candidate_ids"][benchmark]:
            raise ValueError(f"{benchmark}: candidate IDs do not match manifest")
        if dataset_ids[benchmark] != manifest["selected_dataset_ids"][benchmark]:
            raise ValueError(f"{benchmark}: source question IDs do not match manifest")
    if manifest.get("final_test_records_read") is not False or manifest.get("final_test_included") is not False:
        raise ValueError("Manifest does not confirm Final Test non-access/exclusion")
    if manifest.get("original_verified_subset_modified") is not False:
        raise ValueError("Manifest must affirm the verified subset was not modified")
    report["checks"] = {
        "history_development_only": True,
        "final_test_records_read": False,
        "candidate_ids_unique": True,
        "dataset_ids_unique_per_benchmark": True,
        "related_group_ids_unique_per_benchmark": True,
        "source_provenance_and_evidence_present": True,
        "all_gsm_negatives_have_full_arithmetic_replay": True,
        "hotpot_negatives_are_explicitly_contradicted_by_supported_gold_construction": True,
        "unresolved_not_counted_as_incorrect": True,
        "verified_subset_v1_unchanged": True,
        "recorded_source_hashes_match": True,
    }
    report["combined"] = {
        "generated_candidates": sum(item["generated_candidates"] for item in report["benchmarks"].values()),
        "verified_correct": sum(item["verified_correct"] for item in report["benchmarks"].values()),
        "verified_incorrect": sum(item["verified_incorrect"] for item in report["benchmarks"].values()),
        "unresolved": sum(item["unresolved"] for item in report["benchmarks"].values()),
    }
    report["selection_seed"] = manifest.get("random_seed")
    report["interpretation"] = "Unresolved is not counted as verified incorrect; all labels are conditional on the documented benchmark semantics and evidence."
    return report


README = """# Controlled negative candidates v1\n\nThese files contain controlled answer corruptions from History and Development only. GSM8K negatives use an exact +1 transformation on verified integer-count answers whose original worked-solution equations replay completely. HotpotQA negatives explicitly negate a short benchmark answer that occurs in a cited supporting-fact paragraph.\n\nGSM8K alternatives preserve the implicit requested count unit and are numerically non-equivalent under exact integer/fraction normalization. HotpotQA alternatives are deliberately explicit negations, a controlled stress case rather than a sample of natural model errors. Each HotpotQA record includes the supporting-fact paragraph and title/sentence provenance. This remains benchmark-context-assisted; it is not shared-corpus retrieval.\n\nStatuses use `verified_correct`, `verified_incorrect`, or `unresolved`. Unresolved cases are never treated as incorrect. See `evaluation/docs/verified_negative_candidate_protocol.md` and `manifest.json` for selection, source hashes, and limitations. Final Test was not read or used.\n"""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    build_parser = sub.add_parser("build")
    build_parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    build_parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    validate_parser = sub.add_parser("validate")
    validate_parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    if args.command == "build":
        report = build(args.seed, args.output_dir)
    else:
        report = validate(args.output_dir)
        (args.output_dir / "validation_summary.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
