"""Prepare reconciled candidate labels for later offline recording collection.

This preparation stage deliberately does not construct offline Example objects:
the source artifact has no verifier Attempts or execution identifiers.
Unresolved candidates are retained in a separate exclusion ledger.
"""

from __future__ import annotations

import argparse
import collections
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Literal, get_args

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.game.offline.records import Example


SOURCE = ROOT / "evaluation/datasets/reconciled_candidates/v1"
DEFAULT_OUTPUT = ROOT / "evaluation/datasets/offline_examples/v1_reconciled_candidates"
BENCHMARKS = ("GSM8K", "HotpotQA")
PARTITIONS = ("history", "development")
STATUS_TO_BOOL = {"verified_correct": True, "verified_incorrect": False}
CONTRACT_LABEL_METHODS = set(get_args(Example.model_fields["label_method"].annotation))
PREPARATION_LABEL_METHOD = "independent_ground_truth"
SUPPORTED_METHODS = {
    ("GSM8K", "verified_correct"): {"benchmark_source_match_plus_independent_arithmetic_replay"},
    ("GSM8K", "verified_incorrect"): {
        "raw_worked_solution_source_match_plus_exact_rational_arithmetic_replay_and_distinct_integer_check"
    },
    ("HotpotQA", "verified_correct"): {"benchmark_source_answer_match_with_supporting_context_provenance"},
    ("HotpotQA", "verified_incorrect"): {
        "source_answer_match_plus_supporting_fact_context_and_literal_negation_check"
    },
}
VERSION = "offline-candidate-preparation-v1"
REQUIRED_RECORDING_FIELDS = (
    "domain",
    "planning_category",
    "validation_id",
    "execution_configuration_id",
    "cache_contract",
    "attempts",
)


def json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")


def jsonl_bytes(rows: list[dict]) -> bytes:
    return b"".join(
        (json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
        for row in rows
    )


def digest_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def validate_label_method(method: str) -> str:
    """Validate against Example's literal contract; no verifier-based methods."""
    if method not in CONTRACT_LABEL_METHODS:
        raise ValueError(f"Unsupported offline label method: {method}")
    return method


def map_status(status: str) -> bool:
    if status not in STATUS_TO_BOOL:
        raise ValueError(f"Status is not eligible for binary label mapping: {status}")
    return STATUS_TO_BOOL[status]


def validate_source_rows(rows_by_benchmark: dict[str, list[dict]]) -> None:
    global_ids: set[str] = set()
    for benchmark, rows in rows_by_benchmark.items():
        groups: dict[str, tuple[str, str]] = {}
        for row in rows:
            for key in ("candidate_id", "dataset_id", "related_group_id", "partition", "correctness_status", "question", "candidate_answer"):
                if row.get(key) in (None, ""):
                    raise ValueError(f"{benchmark}: missing {key} in reconciled row")
            if row.get("benchmark") != benchmark:
                raise ValueError(f"Benchmark mismatch for candidate {row['candidate_id']}")
            if row["partition"] not in PARTITIONS:
                raise ValueError(f"Disallowed partition for candidate {row['candidate_id']}")
            if row["correctness_status"] not in {"verified_correct", "verified_incorrect", "unresolved"}:
                raise ValueError(f"Invalid correctness status for candidate {row['candidate_id']}")
            if row["candidate_id"] in global_ids:
                raise ValueError(f"Duplicate canonical candidate ID: {row['candidate_id']}")
            global_ids.add(row["candidate_id"])
            group_value = (row["dataset_id"], row["partition"])
            if row["related_group_id"] in groups and groups[row["related_group_id"]] != group_value:
                raise ValueError(f"Group maps to multiple questions/partitions: {row['related_group_id']}")
            groups[row["related_group_id"]] = group_value
            method = row.get("validation_method")
            if row["correctness_status"] in STATUS_TO_BOOL:
                allowed = SUPPORTED_METHODS.get((benchmark, row["correctness_status"]), set())
                if method not in allowed:
                    raise ValueError(f"Unsupported validation provenance for {row['candidate_id']}: {method}")
                if not row.get("validation_basis") or not row.get("source_candidate_record"):
                    raise ValueError(f"Verified label lacks provenance: {row['candidate_id']}")
                validate_label_method(PREPARATION_LABEL_METHOD)
    if not rows_by_benchmark:
        raise ValueError("No benchmark input rows")


def prepare_rows(rows_by_benchmark: dict[str, list[dict]]) -> tuple[dict[str, list[dict]], list[dict]]:
    validate_source_rows(rows_by_benchmark)
    prepared: dict[str, list[dict]] = {part: [] for part in PARTITIONS}
    excluded: list[dict] = []
    for benchmark in BENCHMARKS:
        for source in rows_by_benchmark.get(benchmark, []):
            status = source["correctness_status"]
            provenance = {
                "validation_method": source.get("validation_method"),
                "validation_basis": source.get("validation_basis"),
                "source_correctness_status": source.get("source_correctness_status"),
                "source_candidate_record": source.get("source_candidate_record"),
                "reconciliation": source.get("reconciliation"),
                "human_adjudication": False,
            }
            if status == "unresolved":
                excluded.append({
                    "candidate_id": source["candidate_id"],
                    "dataset_id": source["dataset_id"],
                    "benchmark": benchmark,
                    "related_group_id": source["related_group_id"],
                    "partition": source["partition"],
                    "candidate_answer": source["candidate_answer"],
                    "gold_answer": source.get("gold_answer"),
                    "correctness_status": "unresolved",
                    "exclusion_reason": source.get("validation_basis", {}).get("unresolved_reason")
                    or source.get("source_candidate_record", {}).get("unresolved_reason")
                    or "Source status remains unresolved; no binary label assigned.",
                    "label_provenance": provenance,
                    "source_record": source,
                })
                continue
            method = validate_label_method(PREPARATION_LABEL_METHOD)
            is_correct = map_status(status)
            context_condition = (
                "arithmetic_worked_solution_used_for_label_validation_only; not verifier input"
                if benchmark == "GSM8K"
                else "benchmark_context_assisted; reconciled supporting-context evidence retained; not shared-corpus retrieval"
            )
            evidence_context = source.get("validation_basis", {}).get("validation_evidence", [])
            verifier_input = {
                "benchmark": benchmark,
                "question": source["question"],
                "candidate_answer": source["candidate_answer"],
                "evidence_context": evidence_context if benchmark == "HotpotQA" else [],
            }
            prepared[source["partition"]].append({
                "preparation_version": VERSION,
                "preparation_status": "label_prepared_only_not_offline_Example",
                "example_id": source["candidate_id"],
                "candidate_id": source["candidate_id"],
                "dataset_id": source["dataset_id"],
                "question_id": f"{benchmark}:{source['dataset_id']}",
                "related_group_id": source["related_group_id"],
                "split_identity": source["related_group_id"],
                "benchmark": benchmark,
                "dataset_version": source.get("dataset_version"),
                "partition": source["partition"],
                "question": source["question"],
                "candidate_answer": source["candidate_answer"],
                "gold_answer": source.get("gold_answer"),
                "correctness_status": status,
                "answer_is_correct": is_correct,
                "label_method": method,
                "label_source": f"reconciled_candidates_v1:{source['validation_method']}",
                "label_provenance": provenance,
                "candidate_source": source.get("candidate_source"),
                "candidate_generation_method": source.get("candidate_generation_method"),
                "construction_version": source.get("construction_version"),
                "evidence_condition": context_condition,
                "evidence_context": evidence_context,
                "verifier_input": verifier_input,
                "offline_example_ready": False,
                "complete_verifier_attempt_records": False,
                "missing_required_recording_fields": list(REQUIRED_RECORDING_FIELDS),
            })
    for part in prepared:
        prepared[part].sort(key=lambda row: (row["benchmark"], row["dataset_id"], row["candidate_id"]))
    excluded.sort(key=lambda row: (row["benchmark"], row["partition"], row["dataset_id"], row["candidate_id"]))
    validate_group_partition_assignments(prepared, excluded)
    return prepared, excluded


def validate_group_partition_assignments(prepared: dict[str, list[dict]], excluded: list[dict]) -> None:
    assignments: dict[tuple[str, str], str] = {}
    ids: set[str] = set()
    for row in [*prepared["history"], *prepared["development"], *excluded]:
        key = (row["benchmark"], row["related_group_id"])
        old = assignments.setdefault(key, row["partition"])
        if old != row["partition"]:
            raise ValueError(f"History/Development group leakage: {key}")
        candidate_id = row["candidate_id"]
        if candidate_id in ids:
            raise ValueError(f"Candidate appears more than once in preparation/exclusion outputs: {candidate_id}")
        ids.add(candidate_id)


def make_summary(prepared: dict[str, list[dict]], excluded: list[dict]) -> dict:
    summary: dict[str, Any] = {"version": VERSION, "benchmarks": {}, "combined": {}}
    for benchmark in BENCHMARKS:
        details = {}
        source_labelled = [row for part in PARTITIONS for row in prepared[part] if row["benchmark"] == benchmark]
        source_excluded = [row for row in excluded if row["benchmark"] == benchmark]
        for partition in PARTITIONS:
            good = [row for row in prepared[partition] if row["benchmark"] == benchmark]
            unresolved = [row for row in source_excluded if row["partition"] == partition]
            details[partition] = {
                "prepared_labelled_candidates": len(good),
                "verified_correct": sum(row["correctness_status"] == "verified_correct" for row in good),
                "verified_incorrect": sum(row["correctness_status"] == "verified_incorrect" for row in good),
                "excluded_unresolved_candidates": len(unresolved),
                "labelled_question_groups": len({row["related_group_id"] for row in good}),
                "unresolved_question_groups": len({row["related_group_id"] for row in unresolved}),
                "complete_verifier_attempt_records": 0,
            }
        summary["benchmarks"][benchmark] = {
            "prepared_labelled_candidates": len(source_labelled),
            "verified_correct": sum(row["correctness_status"] == "verified_correct" for row in source_labelled),
            "verified_incorrect": sum(row["correctness_status"] == "verified_incorrect" for row in source_labelled),
            "excluded_unresolved_candidates": len(source_excluded),
            "independent_question_groups": len({row["related_group_id"] for row in source_labelled + source_excluded}),
            "partition_counts": details,
            "complete_verifier_attempt_records": 0,
        }
    summary["combined"] = {
        "prepared_labelled_candidates": sum(v["prepared_labelled_candidates"] for v in summary["benchmarks"].values()),
        "excluded_unresolved_candidates": sum(v["excluded_unresolved_candidates"] for v in summary["benchmarks"].values()),
        "complete_verifier_attempt_records": 0,
        "offline_Example_objects_constructed": 0,
        "note": "Candidate labels are prepared; every record still lacks required offline recording fields and verifier Attempts.",
    }
    return summary


def render_artifacts(rows_by_benchmark: dict[str, list[dict]], source_hashes: dict[str, str]) -> dict[str, bytes]:
    prepared, excluded = prepare_rows(rows_by_benchmark)
    summary = make_summary(prepared, excluded)
    summary["validation"] = {
        "passed": True,
        "no_final_test_records_or_identities_accessed": True,
        "unresolved_excluded_with_reason": True,
        "label_methods_within_offline_contract": True,
        "offline_examples_constructed": False,
    }
    readme = (
        "# Offline candidate label preparation v1\n\n"
        "These are label-preparation rows, not validated `app.game.offline.records.Example` objects. "
        "The source contains no verifier Attempts, validation IDs, or execution-configuration IDs; none were fabricated. "
        "Unresolved candidates are preserved in `excluded_unresolved.jsonl`. See the protocol and manifest for provenance.\n"
    )
    files = {
        "history_prepared.jsonl": jsonl_bytes(prepared["history"]),
        "development_prepared.jsonl": jsonl_bytes(prepared["development"]),
        "excluded_unresolved.jsonl": jsonl_bytes(excluded),
        "validation_summary.json": json_bytes(summary),
        "README.md": readme.encode("utf-8"),
    }
    output_hashes = {name: digest_bytes(data) for name, data in sorted(files.items())}
    manifest_core = {
        "artifact_version": VERSION,
        "source_paths": {
            "reconciled_gsm8k": "evaluation/datasets/reconciled_candidates/v1/gsm8k_reconciled.jsonl",
            "reconciled_hotpotqa": "evaluation/datasets/reconciled_candidates/v1/hotpotqa_reconciled.jsonl",
            "reconciled_manifest": "evaluation/datasets/reconciled_candidates/v1/manifest.json",
            "reconciled_validation_summary": "evaluation/datasets/reconciled_candidates/v1/validation_summary.json",
        },
        "source_sha256": source_hashes,
        "output_sha256": output_hashes,
        "label_method_contract": {
            "accepted_values": sorted(CONTRACT_LABEL_METHODS),
            "prepared_value": PREPARATION_LABEL_METHOD,
            "method_basis_allowlist": {f"{benchmark}:{status}": sorted(methods)
                                       for (benchmark, status), methods in SUPPORTED_METHODS.items()},
            "human_adjudication_claimed": False,
            "team_approval_of_methodology_required": True,
        },
        "recording_requirements_missing": list(REQUIRED_RECORDING_FIELDS),
        "counts": summary,
        "no_final_test_records_or_identities_accessed": True,
        "no_splits_or_holdout_created": True,
        "policy_fitting_or_research_experiments_run": False,
        "offline_Example_objects_constructed": False,
    }
    manifest = {**manifest_core, "manifest_sha256": digest_bytes(json_bytes(manifest_core))}
    files["manifest.json"] = json_bytes(manifest)
    return files


def load_sources(source_dir: Path) -> tuple[dict[str, list[dict]], dict[str, str]]:
    filenames = {"GSM8K": "gsm8k_reconciled.jsonl", "HotpotQA": "hotpotqa_reconciled.jsonl"}
    rows = {benchmark: read_jsonl(source_dir / filename) for benchmark, filename in filenames.items()}
    paths = [source_dir / filenames[b] for b in BENCHMARKS]
    paths.extend(source_dir / name for name in ("manifest.json", "validation_summary.json", "README.md"))
    hashes = {path.name: sha256_file(path) for path in paths}
    return rows, hashes


def write_artifacts(output_dir: Path, artifacts: dict[str, bytes]) -> None:
    if output_dir.exists() and any(output_dir.iterdir()):
        raise FileExistsError(f"Refusing to overwrite non-empty output directory: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)
    for name, data in sorted(artifacts.items()):
        with (output_dir / name).open("xb") as handle:
            handle.write(data)


def validate_artifacts(output_dir: Path) -> dict:
    manifest = read_json(output_dir / "manifest.json")
    core = {key: value for key, value in manifest.items() if key != "manifest_sha256"}
    if digest_bytes(json_bytes(core)) != manifest.get("manifest_sha256"):
        raise ValueError("Manifest digest mismatch")
    for name, expected in manifest.get("output_sha256", {}).items():
        if sha256_file(output_dir / name) != expected:
            raise ValueError(f"Output hash mismatch: {name}")
    source_dir = ROOT / "evaluation/datasets/reconciled_candidates/v1"
    for name, expected in manifest.get("source_sha256", {}).items():
        if sha256_file(source_dir / name) != expected:
            raise ValueError(f"Reconciled source hash mismatch: {name}")
    prepared = {
        "history": read_jsonl(output_dir / "history_prepared.jsonl"),
        "development": read_jsonl(output_dir / "development_prepared.jsonl"),
    }
    excluded = read_jsonl(output_dir / "excluded_unresolved.jsonl")
    validate_group_partition_assignments(prepared, excluded)
    if any("attempts" in row or "validation_id" in row or "execution_configuration_id" in row for part in prepared.values() for row in part):
        raise ValueError("Preparation output contains fabricated recording fields")
    if any(row.get("correctness_status") != "unresolved" or "answer_is_correct" in row for row in excluded):
        raise ValueError("Unresolved exclusion was mapped to a binary label")
    summary = make_summary(prepared, excluded)
    for benchmark in BENCHMARKS:
        source = read_jsonl(source_dir / f"{benchmark.lower()}_reconciled.jsonl")
        expected_ids = {r["candidate_id"] for r in source if r["correctness_status"] in STATUS_TO_BOOL}
        actual_ids = {r["candidate_id"] for part in prepared.values() for r in part if r["benchmark"] == benchmark}
        if expected_ids != actual_ids:
            raise ValueError(f"Eligible label roster mismatch for {benchmark}")
        unresolved_ids = {r["candidate_id"] for r in source if r["correctness_status"] == "unresolved"}
        excluded_ids = {r["candidate_id"] for r in excluded if r["benchmark"] == benchmark}
        if unresolved_ids != excluded_ids:
            raise ValueError(f"Unresolved exclusion ledger mismatch for {benchmark}")
    summary_path = output_dir / "validation_summary.json"
    persisted = read_json(summary_path)
    if any(persisted.get(key) != summary.get(key) for key in ("version", "benchmarks", "combined")):
        raise ValueError("Persisted validation summary differs from prepared rows")
    return {"passed": True, "summary": summary, "checks": {
        "source_hashes_match": True,
        "output_hashes_match": True,
        "manifest_hash_matches": True,
        "binary_label_mapping_valid": True,
        "unresolved_candidates_preserved_without_binary_labels": True,
        "candidate_group_identity_preserved": True,
        "history_development_groups_disjoint": True,
        "no_recording_fields_fabricated": True,
        "no_final_test_records_or_identities_accessed": True,
    }}


def build(output_dir: Path, source_dir: Path) -> dict:
    rows, source_hashes = load_sources(source_dir)
    artifacts = render_artifacts(rows, source_hashes)
    write_artifacts(output_dir, artifacts)
    return validate_artifacts(output_dir)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    build_parser = subparsers.add_parser("build")
    build_parser.add_argument("--source-dir", type=Path, default=SOURCE)
    build_parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    validate_parser = subparsers.add_parser("validate")
    validate_parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    report = build(args.output_dir, args.source_dir) if args.command == "build" else validate_artifacts(args.output_dir)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
