"""Reconcile controlled negatives with verified-subset candidate identities.

Only the named History/Development v1 artifacts and protocol documents are
read. Final Test data paths are never opened. Output is written to a new
versioned directory; an existing non-empty output is never overwritten.
"""

from __future__ import annotations

import argparse
import collections
import hashlib
import json
import re
from decimal import Decimal, InvalidOperation
from fractions import Fraction
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
SUBSET = ROOT / "evaluation/datasets/verified_subset/v1_seed_20261104"
NEGATIVE = ROOT / "evaluation/datasets/verified_negative_candidates/v1"
DOCS = ROOT / "evaluation/docs"
DEFAULT_OUTPUT = ROOT / "evaluation/datasets/reconciled_candidates/v1"
BENCHMARKS = {
    "GSM8K": ("gsm8k_verified.jsonl", "gsm8k_negative_candidates.jsonl"),
    "HotpotQA": ("hotpotqa_verified.jsonl", "hotpotqa_negative_candidates.jsonl"),
}
PARTITIONS = {"history", "development"}
STATUSES = {"verified_correct", "verified_incorrect", "unresolved"}
PROTOCOLS = (
    "verified_subset_protocol.md",
    "verified_negative_candidate_protocol.md",
    "dataset_split_and_final_test_protocol.md",
)
VERSION = "reconciled-candidates-v1"
CONSTRUCTION_VERSION = {
    "GSM8K": "controlled_increment_one_in_same_implicit_discrete_answer_unit",
    "HotpotQA": "explicit_negation_of_context_supported_benchmark_answer",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def file_hashes(paths: list[Path]) -> dict[str, str]:
    return {
        path.relative_to(ROOT).as_posix(): sha256(path)
        for path in sorted(paths)
    }


def source_files() -> list[Path]:
    # Deliberately enumerate safe History/Development artifacts. Do not glob
    # unified datasets or any directory that could include Final Test rows.
    paths = [
        SUBSET / "gsm8k_verified.jsonl",
        SUBSET / "hotpotqa_verified.jsonl",
        SUBSET / "subset_manifest.json",
        SUBSET / "validation_summary.json",
        SUBSET / "quality_check.json",
        NEGATIVE / "gsm8k_negative_candidates.jsonl",
        NEGATIVE / "hotpotqa_negative_candidates.jsonl",
        NEGATIVE / "manifest.json",
        NEGATIVE / "validation_summary.json",
    ]
    paths.extend(DOCS / name for name in PROTOCOLS)
    missing = [path for path in paths if not path.is_file()]
    if missing:
        raise FileNotFoundError("Missing required input(s): " + ", ".join(map(str, missing)))
    return paths


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def write_jsonl(path: Path, rows: list[dict]) -> None:
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def numeric_value(value: Any) -> Fraction | None:
    text = str(value).strip().replace("−", "-").replace("$", "").replace(" ", "")
    if "," in text:
        if not re.fullmatch(r"-?\d{1,3}(?:,\d{3})+(?:\.\d+)?", text):
            return None
        text = text.replace(",", "")
    if text.startswith("+"):
        text = text[1:]
    try:
        if re.fullmatch(r"-?\d+/[1-9]\d*", text):
            numerator, denominator = text.split("/", 1)
            return Fraction(int(numerator), int(denominator))
        if re.fullmatch(r"-?(?:\d+(?:\.\d*)?|\.\d+)", text):
            return Fraction(Decimal(text))
    except (ValueError, InvalidOperation, ZeroDivisionError):
        return None
    return None


def group_roster(rows: list[dict], benchmark: str) -> dict[str, dict]:
    roster: dict[str, dict] = {}
    dataset_to_group: dict[str, str] = {}
    for row in rows:
        if row.get("benchmark") != benchmark:
            raise ValueError(f"Benchmark mismatch in source row {row.get('candidate_id')}")
        if row.get("partition") not in PARTITIONS:
            raise ValueError(f"Disallowed partition in source row {row.get('candidate_id')}")
        dataset_id = row.get("dataset_id")
        group_id = row.get("related_group_id")
        if not dataset_id or not group_id:
            raise ValueError(f"Missing dataset/group ID in {row.get('candidate_id')}")
        identity = {
            "dataset_id": dataset_id,
            "related_group_id": group_id,
            "partition": row["partition"],
            "question": row.get("question"),
            "gold_answer": row.get("gold_answer"),
        }
        if group_id in roster and roster[group_id] != identity:
            raise ValueError(f"Group ID maps to inconsistent question metadata: {group_id}")
        if dataset_id in dataset_to_group and dataset_to_group[dataset_id] != group_id:
            raise ValueError(f"Dataset ID maps to multiple group IDs: {dataset_id}")
        roster[group_id] = identity
        dataset_to_group[dataset_id] = group_id
    if len(dataset_to_group) != len(roster):
        raise ValueError(f"{benchmark}: more than one dataset ID maps to a question group")
    return roster


def canonical_row(source: dict, group: dict, *, origin: str, prior_status: str | None = None,
                  validation: dict | None = None) -> dict:
    status = source.get("correctness_status")
    if status not in STATUSES:
        raise ValueError(f"Invalid source status: {source.get('candidate_id')}")
    return {
        "candidate_id": source["candidate_id"],
        "dataset_id": source["dataset_id"],
        "benchmark": source["benchmark"],
        "dataset_version": source.get("dataset_version"),
        "partition": source["partition"],
        "related_group_id": group["related_group_id"],
        "question": source.get("question", group.get("question")),
        "candidate_answer": source.get("candidate_answer"),
        "gold_answer": source.get("gold_answer", group.get("gold_answer")),
        "correctness_status": status,
        "source_correctness_status": prior_status if prior_status is not None else status,
        "candidate_source": source.get("candidate_source"),
        "candidate_generation_method": source.get("candidate_generation_method"),
        "validation_method": (validation or {}).get("validation_method", source.get("validation_method")),
        "validation_basis": (validation or {}).get("validation_basis", {
            "validation_method": source.get("validation_method"),
            "validation_basis": source.get("validation_basis"),
            "validation_evidence": source.get("validation_evidence", []),
            "evidence_provenance": source.get("evidence_provenance", {}),
            "validation_rationale": source.get("validation_rationale"),
            "validation_confidence_category": source.get("validation_confidence_category"),
            "unresolved_reason": source.get("unresolved_reason"),
        }),
        "construction_version": CONSTRUCTION_VERSION[source["benchmark"]]
        if origin == "controlled_negative" else "verified_subset_v1",
        "origin": origin,
        "source_candidate_index": source.get("source_candidate_index"),
        "source_candidate_record": source,
        "reconciliation": validation or None,
    }


def reconcile_gsm8k(originals: list[dict], negatives: list[dict], roster: dict[str, dict]) -> tuple[list[dict], dict]:
    originals_by_id = {row["candidate_id"]: row for row in originals}
    if len(originals_by_id) != len(originals):
        raise ValueError("GSM8K source candidate IDs are duplicated")
    by_dataset: dict[str, list[dict]] = collections.defaultdict(list)
    for row in originals:
        by_dataset[row["dataset_id"]].append(row)
    controlled_by_dataset = {row["dataset_id"]: row for row in negatives}
    if len(controlled_by_dataset) != len(negatives):
        raise ValueError("GSM8K controlled negatives repeat source question IDs")

    matches: dict[str, dict] = {}
    used_targets: set[str] = set()
    for negative in negatives:
        if negative.get("correctness_status") != "verified_incorrect":
            raise ValueError(f"GSM8K controlled candidate is not verified incorrect: {negative.get('candidate_id')}")
        group = roster.get(next((row["related_group_id"] for row in originals if row["dataset_id"] == negative.get("dataset_id")), ""))
        if group is None:
            raise ValueError(f"GSM8K controlled candidate has no source question: {negative.get('candidate_id')}")
        if (negative.get("partition") != group["partition"] or negative.get("question") != group["question"]
                or numeric_value(negative.get("gold_answer")) != numeric_value(group["gold_answer"])):
            raise ValueError(f"GSM8K controlled candidate metadata differs from parent: {negative.get('candidate_id')}")
        candidates = [row for row in by_dataset[negative["dataset_id"]]
                      if row.get("source_candidate_index") == 1]
        if len(candidates) != 1:
            raise ValueError(f"Expected exactly one existing GSM8K candidate_1: {negative['dataset_id']}")
        original = candidates[0]
        if original.get("correctness_status") != "unresolved":
            raise ValueError(f"GSM8K target candidate must be unresolved before reconciliation: {original['candidate_id']}")
        if numeric_value(original.get("candidate_answer")) is None or numeric_value(original.get("candidate_answer")) != numeric_value(negative.get("candidate_answer")):
            raise ValueError(f"GSM8K controlled candidate does not numerically match original candidate: {negative['dataset_id']}")
        if original["candidate_id"] in used_targets:
            raise ValueError(f"GSM8K original candidate matched more than once: {original['candidate_id']}")
        used_targets.add(original["candidate_id"])
        matches[original["candidate_id"]] = negative

    result = []
    for original in originals:
        group = next(value for value in roster.values() if value["dataset_id"] == original["dataset_id"])
        negative = matches.get(original["candidate_id"])
        if negative is None:
            result.append(canonical_row(original, group, origin="verified_subset_v1"))
            continue
        validation = {
            "reconciliation_version": VERSION,
            "validation_method": negative["validation_method"],
            "validation_basis": {
                "construction_version": negative["candidate_generation_method"],
                "validation_method": negative["validation_method"],
                "validation_evidence": negative["validation_evidence"],
                "evidence_provenance": negative["evidence_provenance"],
                "validation_rationale": negative["validation_rationale"],
                "validation_confidence_category": negative["validation_confidence_category"],
                "numeric_comparison": negative.get("numeric_comparison"),
                "correctness_status": "verified_incorrect",
            },
            "corroborating_controlled_candidate_id": negative["candidate_id"],
            "controlled_candidate_answer": negative["candidate_answer"],
            "duplicate_observation_created": False,
        }
        result.append(canonical_row(original, group, origin="verified_subset_v1_reconciled", prior_status="unresolved", validation=validation) | {
            "correctness_status": "verified_incorrect",
        })
    if len(matches) != len(negatives):
        raise ValueError("Not every GSM8K controlled candidate was reconciled")
    return result, {"controlled_negative_records_matched": len(matches), "duplicate_observation_records_added": 0}


def reconcile_hotpotqa(originals: list[dict], negatives: list[dict], roster: dict[str, dict]) -> tuple[list[dict], dict]:
    result = []
    seen_ids = {row["candidate_id"] for row in originals}
    if len(seen_ids) != len(originals):
        raise ValueError("HotpotQA source candidate IDs are duplicated")
    for original in originals:
        group = next(value for value in roster.values() if value["dataset_id"] == original["dataset_id"])
        result.append(canonical_row(original, group, origin="verified_subset_v1"))
    for negative in negatives:
        if negative.get("correctness_status") != "verified_incorrect":
            raise ValueError(f"HotpotQA controlled candidate is not verified incorrect: {negative.get('candidate_id')}")
        group_matches = [value for value in roster.values() if value["dataset_id"] == negative.get("dataset_id")]
        if len(group_matches) != 1:
            raise ValueError(f"HotpotQA controlled candidate does not map to one question group: {negative.get('candidate_id')}")
        group = group_matches[0]
        if (negative.get("partition") != group["partition"] or negative.get("question") != group["question"]
                or negative.get("gold_answer") != group["gold_answer"]):
            raise ValueError(f"HotpotQA controlled candidate metadata differs from parent: {negative.get('candidate_id')}")
        if negative["candidate_id"] in seen_ids:
            raise ValueError(f"HotpotQA controlled candidate ID collides: {negative['candidate_id']}")
        seen_ids.add(negative["candidate_id"])
        result.append(canonical_row(negative, group, origin="controlled_negative_v1"))
    if len(negatives) != len(set(row["candidate_id"] for row in negatives)):
        raise ValueError("HotpotQA controlled candidate IDs are duplicated")
    return result, {"controlled_negative_records_appended": len(negatives)}


def summarize(rows_by_benchmark: dict[str, list[dict]], rosters: dict[str, dict]) -> dict:
    summary: dict[str, Any] = {"benchmarks": {}, "combined": {}}
    combined_candidates = 0
    combined_groups = 0
    combined_status = collections.Counter()
    for benchmark, rows in rows_by_benchmark.items():
        parts = {}
        status_counts = collections.Counter(row["correctness_status"] for row in rows)
        by_part = collections.defaultdict(list)
        for row in rows:
            by_part[row["partition"]].append(row)
        for partition in ("history", "development"):
            part_rows = by_part[partition]
            part_groups = {row["related_group_id"] for row in part_rows}
            parts[partition] = {
                "candidate_records": len(part_rows),
                "candidate_counts_by_status": dict(collections.Counter(r["correctness_status"] for r in part_rows)),
                "independent_question_groups": len(part_groups),
                "groups_with_at_least_one_candidate_by_status": {
                    status: len({r["related_group_id"] for r in part_rows if r["correctness_status"] == status})
                    for status in sorted(STATUSES)
                },
            }
        groups = set(rosters[benchmark])
        summary["benchmarks"][benchmark] = {
            "candidate_records": len(rows),
            "candidate_counts_by_status": dict(status_counts),
            "independent_question_groups": len(groups),
            "partition_counts": parts,
        }
        combined_candidates += len(rows)
        combined_groups += len(groups)
        combined_status.update(status_counts)
    summary["combined"] = {
        "candidate_records": combined_candidates,
        "candidate_counts_by_status": dict(combined_status),
        "independent_question_groups_across_benchmarks": combined_groups,
        "note": "Question groups are benchmark-specific; status-specific group counts overlap when a question has candidates with multiple statuses.",
    }
    return summary


def validate_payload(rows_by_benchmark: dict[str, list[dict]], rosters: dict[str, dict],
                     reconciliation: dict[str, dict]) -> dict:
    report: dict[str, Any] = {"passed": True, "checks": {}, "benchmarks": {}}
    all_candidate_ids = []
    group_partitions: dict[str, dict[str, str]] = {}
    for benchmark, rows in rows_by_benchmark.items():
        ids = [row["candidate_id"] for row in rows]
        if len(ids) != len(set(ids)):
            raise ValueError(f"{benchmark}: canonical candidate IDs are not unique")
        if any(row.get("partition") not in PARTITIONS for row in rows):
            raise ValueError(f"{benchmark}: non-History/Development row found")
        group_rows: dict[str, set[str]] = collections.defaultdict(set)
        for row in rows:
            if row["correctness_status"] not in STATUSES:
                raise ValueError(f"{benchmark}: invalid status in {row['candidate_id']}")
            if row["related_group_id"] not in rosters[benchmark]:
                raise ValueError(f"{benchmark}: unknown group in {row['candidate_id']}")
            source_record = row.get("source_candidate_record")
            if not isinstance(source_record, dict) or source_record.get("candidate_id") != row["candidate_id"]:
                raise ValueError(f"{benchmark}: original canonical candidate identity was not preserved")
            if (source_record.get("dataset_id") != row["dataset_id"]
                    or source_record.get("candidate_answer") != row["candidate_answer"]
                    or source_record.get("correctness_status") != row.get("source_correctness_status")):
                raise ValueError(f"{benchmark}: original candidate fields/status are not preserved")
            parent = rosters[benchmark][row["related_group_id"]]
            if (row["dataset_id"] != parent["dataset_id"] or row["partition"] != parent["partition"]
                    or row["question"] != parent["question"]):
                raise ValueError(f"{benchmark}: variant attached to wrong question/group")
            group_rows[row["related_group_id"]].add(row["partition"])
            if row["correctness_status"] == "unresolved" and row.get("validation_basis", {}).get("correctness_status") == "verified_incorrect":
                raise ValueError("An unresolved candidate carries an incorrect status as its active basis")
        if any(len(parts) != 1 for parts in group_rows.values()):
            raise ValueError(f"{benchmark}: History/Development group overlap")
        if set(group_rows) != set(rosters[benchmark]):
            raise ValueError(f"{benchmark}: reconciled output omitted or added a question group")
        if benchmark == "GSM8K":
            by_dataset_answer = set()
            for row in rows:
                value = numeric_value(row["candidate_answer"])
                if value is None:
                    raise ValueError(f"GSM8K candidate answer is not a valid normalized number: {row['candidate_id']}")
                key = (row["dataset_id"], value)
                if key in by_dataset_answer:
                    raise ValueError(f"GSM8K duplicate candidate observation: {key}")
                by_dataset_answer.add(key)
                if row.get("correctness_status") == "verified_incorrect" and row.get("origin") != "verified_subset_v1_reconciled":
                    raise ValueError("Unexpected new GSM8K negative observation was appended")
            if reconciliation[benchmark].get("duplicate_observation_records_added") != 0:
                raise ValueError("GSM8K duplicate negative observations were added")
        else:
            source_candidates = [r for r in rows if r["origin"] == "verified_subset_v1"]
            additional = [r for r in rows if r["origin"] == "controlled_negative_v1"]
            if len(source_candidates) != len(set(r["candidate_id"] for r in source_candidates)):
                raise ValueError("HotpotQA original candidate IDs were not preserved uniquely")
            for row in additional:
                if row["related_group_id"] != next(g for g, info in rosters[benchmark].items() if info["dataset_id"] == row["dataset_id"]):
                    raise ValueError("HotpotQA controlled variant is attached to the wrong parent group")
        report["benchmarks"][benchmark] = {
            "candidate_records": len(rows),
            "unique_candidate_ids": len(ids),
            "independent_question_groups": len(group_rows),
            "history_groups": sum(rosters[benchmark][g]["partition"] == "history" for g in group_rows),
            "development_groups": sum(rosters[benchmark][g]["partition"] == "development" for g in group_rows),
            "candidate_counts_by_status": dict(collections.Counter(r["correctness_status"] for r in rows)),
        }
        all_candidate_ids.extend(ids)
        for group_id, partitions in group_rows.items():
            key = f"{benchmark}:{group_id}"
            group_partitions[key] = next(iter(partitions))
    if len(all_candidate_ids) != len(set(all_candidate_ids)):
        raise ValueError("Canonical candidate IDs collide across benchmarks")
    report["checks"] = {
        "unique_canonical_candidate_ids": True,
        "unique_question_group_roster_per_benchmark": True,
        "no_history_development_group_overlap": True,
        "no_duplicate_gsm8k_candidate_observations": True,
        "all_hotpotqa_variants_attached_to_parent_groups": True,
        "all_rows_history_or_development": True,
        "unresolved_status_preserved": True,
        "no_final_test_records_or_identities_accessed": True,
        "source_hashes_match": True,
    }
    return report


def build(output_dir: Path) -> dict:
    if output_dir.exists() and any(output_dir.iterdir()):
        raise FileExistsError(f"Refusing to overwrite non-empty output directory: {output_dir}")
    inputs = source_files()
    input_hashes_before = file_hashes(inputs)
    rows_by_benchmark: dict[str, list[dict]] = {}
    rosters: dict[str, dict] = {}
    reconciliation: dict[str, dict] = {}
    for benchmark, (subset_name, negative_name) in BENCHMARKS.items():
        originals = read_jsonl(SUBSET / subset_name)
        negatives = read_jsonl(NEGATIVE / negative_name)
        rosters[benchmark] = group_roster(originals, benchmark)
        if benchmark == "GSM8K":
            rows_by_benchmark[benchmark], reconciliation[benchmark] = reconcile_gsm8k(originals, negatives, rosters[benchmark])
        else:
            rows_by_benchmark[benchmark], reconciliation[benchmark] = reconcile_hotpotqa(originals, negatives, rosters[benchmark])
    summary = summarize(rows_by_benchmark, rosters)
    quality = validate_payload(rows_by_benchmark, rosters, reconciliation)

    output_dir.mkdir(parents=True, exist_ok=True)
    output_paths = {
        "GSM8K": output_dir / "gsm8k_reconciled.jsonl",
        "HotpotQA": output_dir / "hotpotqa_reconciled.jsonl",
    }
    write_jsonl(output_paths["GSM8K"], rows_by_benchmark["GSM8K"])
    write_jsonl(output_paths["HotpotQA"], rows_by_benchmark["HotpotQA"])
    (output_dir / "validation_summary.json").write_text(json.dumps({**summary, **quality, "reconciliation": reconciliation}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    readme = """# Reconciled candidate identities v1

This version joins controlled-negative records to the original verified-subset question groups. GSM8K controlled negatives update the status basis of the existing `candidate_1` records while retaining their original candidate IDs; no duplicate candidate rows are added. HotpotQA explicit-negation candidates remain additional candidate variants, each attached to its source question's `related_group_id`. Original subset records are preserved in `source_candidate_record`.

Only History and Development records are included. Unresolved candidates remain unresolved. See `manifest.json` and `validation_summary.json` for source hashes, exact candidate/group counts, and validation checks. Final Test records and identities were not accessed.
"""
    (output_dir / "README.md").write_text(readme, encoding="utf-8")
    output_hashes = file_hashes([*output_paths.values(), output_dir / "validation_summary.json", output_dir / "README.md"])
    manifest = {
        "artifact_version": VERSION,
        "reconciliation_algorithm": "candidate_id_preserving_gsm_update_and_hotpot_variant_append_v1",
        "source_artifacts": input_hashes_before,
        "output_artifacts": output_hashes,
        "candidate_reconciliation": reconciliation,
        "counts": summary,
        "group_rosters": {
            benchmark: [
                {"dataset_id": group["dataset_id"], "related_group_id": group["related_group_id"], "partition": group["partition"]}
                for group in sorted(roster.values(), key=lambda item: (item["partition"], item["dataset_id"]))
            ] for benchmark, roster in rosters.items()
        },
        "final_test_records_read": False,
        "final_test_identities_accessed": False,
        "original_source_artifacts_modified": False,
        "policy_fitting_or_experiments_run": False,
    }
    (output_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if file_hashes(inputs) != input_hashes_before:
        raise RuntimeError("An input artifact changed during reconciliation")
    return validate(output_dir)


def validate(output_dir: Path) -> dict:
    manifest = read_json(output_dir / "manifest.json")
    for relative_path, expected_hash in manifest["source_artifacts"].items():
        path = ROOT / relative_path
        if not path.is_file() or sha256(path) != expected_hash:
            raise ValueError(f"Source artifact hash mismatch: {relative_path}")
    for relative_path, expected_hash in manifest["output_artifacts"].items():
        path = ROOT / relative_path
        if not path.is_file() or sha256(path) != expected_hash:
            raise ValueError(f"Output artifact hash mismatch: {relative_path}")
    rows_by_benchmark = {
        benchmark: read_jsonl(output_dir / f"{benchmark.lower()}_reconciled.jsonl")
        for benchmark in BENCHMARKS
    }
    rosters = {}
    source_rows = {}
    negative_rows = {}
    for benchmark, (subset_name, _) in BENCHMARKS.items():
        source_rows[benchmark] = read_jsonl(SUBSET / subset_name)
        rosters[benchmark] = group_roster(source_rows[benchmark], benchmark)
        negative_rows[benchmark] = read_jsonl(NEGATIVE / BENCHMARKS[benchmark][1])
    reconciliation = manifest["candidate_reconciliation"]
    report = validate_payload(rows_by_benchmark, rosters, reconciliation)
    gsm_source_by_id = {row["candidate_id"]: row for row in source_rows["GSM8K"]}
    gsm_control_by_dataset = {row["dataset_id"]: row for row in negative_rows["GSM8K"]}
    gsm_output_by_id = {row["candidate_id"]: row for row in rows_by_benchmark["GSM8K"]}
    if set(gsm_output_by_id) != set(gsm_source_by_id):
        raise ValueError("GSM8K reconciliation changed the original canonical candidate roster")
    updated_gsm = [row for row in rows_by_benchmark["GSM8K"] if row.get("reconciliation")]
    if len(updated_gsm) != len(negative_rows["GSM8K"]):
        raise ValueError("GSM8K controlled candidates are not one-to-one with reconciled originals")
    for row in updated_gsm:
        negative = gsm_control_by_dataset.get(row["dataset_id"])
        if (negative is None
                or row["reconciliation"].get("corroborating_controlled_candidate_id") != negative["candidate_id"]
                or numeric_value(row["candidate_answer"]) != numeric_value(negative["candidate_answer"])
                or row["source_candidate_record"] != gsm_source_by_id[row["candidate_id"]]):
            raise ValueError(f"GSM8K reconciliation does not preserve/map the source record: {row['candidate_id']}")
    hot_source_ids = {row["candidate_id"] for row in source_rows["HotpotQA"]}
    hot_control_ids = {row["candidate_id"] for row in negative_rows["HotpotQA"]}
    hot_output = {row["candidate_id"]: row for row in rows_by_benchmark["HotpotQA"]}
    if set(hot_output) != hot_source_ids | hot_control_ids:
        raise ValueError("HotpotQA output does not retain every source record plus each controlled variant")
    for source in source_rows["HotpotQA"]:
        if hot_output[source["candidate_id"]]["source_candidate_record"] != source:
            raise ValueError(f"HotpotQA original record changed: {source['candidate_id']}")
    for negative in negative_rows["HotpotQA"]:
        row = hot_output[negative["candidate_id"]]
        if row["source_candidate_record"] != negative or row["candidate_answer"] != negative["candidate_answer"]:
            raise ValueError(f"HotpotQA controlled variant changed: {negative['candidate_id']}")
    report["checks"].update({
        "all_original_candidate_ids_preserved": True,
        "gsm8k_controlled_candidates_one_to_one_with_original_ids": True,
        "hotpotqa_source_and_controlled_records_preserved": True,
    })
    if manifest.get("final_test_records_read") is not False or manifest.get("final_test_identities_accessed") is not False:
        raise ValueError("Manifest must certify no Final Test records/identities were accessed")
    if manifest.get("original_source_artifacts_modified") is not False:
        raise ValueError("Manifest does not affirm source preservation")
    expected = manifest["counts"]
    actual = summarize(rows_by_benchmark, rosters)
    if actual != expected:
        raise ValueError("Candidate/group summary differs from manifest")
    report["summary"] = actual
    report["source_hashes_match"] = True
    report["passed"] = True
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    build_parser = subparsers.add_parser("build")
    build_parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    validate_parser = subparsers.add_parser("validate")
    validate_parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    report = build(args.output_dir) if args.command == "build" else validate(args.output_dir)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
