"""Create and validate a blinded, history/development-only adjudication pilot.

This script deliberately reads no Final Test dataset or adjudication rows. It
uses only the first 5,000 source-order records in each v1 adjudication JSONL:
4,000 History candidate rows followed by 1,000 Development candidate rows.
It refuses to proceed if those partition boundaries do not match.
"""

from __future__ import annotations

import argparse
import collections
import hashlib
import json
import random
import shutil
from datetime import date
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "evaluation/datasets/adjudication/pilot_v3"
SOURCE_ADJUDICATION = ROOT / "evaluation/datasets/adjudication/v1"
PARTITIONS = ("history", "development")
PER_DATASET = 30
SEED = 20261102
CONSISTENCY_SEED = 20261103
SOURCE_TAG = {
    "gsm8k": "synthetic_numeric_perturbation",
    "hotpotqa": "synthetic_cross_example_answer",
}
VALID_DECISIONS = {"verified_correct", "verified_incorrect", "unresolved"}
EXPECTED_PREFIX_ROWS = {"gsm8k": 5000, "hotpotqa": 5000}
EXPECTED_PARTITION_ROWS = {"history": 4000, "development": 1000}


def has_second_reviewer_fields(row: dict) -> bool:
    return any(
        key == "reviewer_decisions" or key == "second_reviewer"
        or key.startswith("reviewer_2") or key.startswith("reviewer2")
        for key in row
    )


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_history_development_prefix(path: Path, dataset: str) -> tuple[list[dict], str]:
    """Read exactly the known History+Development prefix; do not read beyond it."""
    target = EXPECTED_PREFIX_ROWS[dataset]
    rows: list[dict] = []
    raw = bytearray()
    with path.open("rb") as handle:
        for line_number in range(1, target + 1):
            line = handle.readline()
            if not line:
                raise ValueError(f"{path} ended before expected safe prefix row {line_number}")
            raw.extend(line)
            row = json.loads(line)
            if row.get("partition") not in PARTITIONS:
                raise ValueError(f"Safe prefix contains disallowed partition at row {line_number}")
            rows.append(row)
    counts = collections.Counter(row["partition"] for row in rows)
    if counts != EXPECTED_PARTITION_ROWS:
        raise ValueError(f"Unexpected source-order partition boundaries for {dataset}: {dict(counts)}")
    return rows, sha256_bytes(bytes(raw))


def blank_review() -> dict[str, Any]:
    return {
        "reviewer_id": None,
        "adjudication_status": None,
        "adjudication_evidence": [],
        "adjudication_provenance": [],
        "adjudication_rationale": None,
    }


def read_json(path: Path) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_unified(partition: str) -> dict[str, dict]:
    path = ROOT / f"evaluation/datasets/unified/{partition}.json"
    return {str(row["id"]): row for row in read_json(path)}


def validate_records(gsm: list[dict], hotpot: list[dict], *, require_count: bool = True) -> dict:
    errors: list[str] = []
    if require_count and (len(gsm) != 30 or len(hotpot) != 30):
        errors.append(f"expected 30 records per benchmark; got GSM8K={len(gsm)}, HotpotQA={len(hotpot)}")
    all_rows = [("GSM8K", row) for row in gsm] + [("HotpotQA", row) for row in hotpot]
    ids = [row.get("candidate_id") for _, row in all_rows]
    if len(ids) != len(set(ids)):
        errors.append("duplicate candidate IDs found")
    if any(row.get("partition") not in PARTITIONS for _, row in all_rows):
        errors.append("Final Test or an unknown partition found")
    for benchmark, rows in (("GSM8K", gsm), ("HotpotQA", hotpot)):
        if any(row.get("adjudication_status_before_pilot") != "unresolved" for row in rows):
            errors.append(f"{benchmark}: a selected candidate was not unresolved before review")
        for row in rows:
            if has_second_reviewer_fields(row):
                errors.append(f"{row.get('candidate_id')}: legacy/multiple-reviewer field is not allowed")
            status = row.get("adjudication_status")
            if status is not None and status not in VALID_DECISIONS:
                errors.append(f"{row.get('candidate_id')}: invalid adjudication_status {status!r}")
            if status is None:
                if row.get("reviewer_id") is not None or row.get("adjudication_evidence") or row.get("adjudication_provenance") or row.get("adjudication_rationale"):
                    errors.append(f"{row.get('candidate_id')}: pending review has populated decision fields")
            elif not all((row.get("reviewer_id"), row.get("adjudication_evidence"), row.get("adjudication_provenance"), row.get("adjudication_rationale"))):
                errors.append(f"{row.get('candidate_id')}: completed review lacks reviewer/evidence/provenance/rationale")
            if "adjudicator" not in row:
                errors.append(f"{row.get('candidate_id')}: exceptional adjudicator field missing")
    if errors:
        raise ValueError("Pilot validation failed:\n- " + "\n- ".join(errors))
    return {
        "gsm8k_count": len(gsm),
        "hotpotqa_count": len(hotpot),
        "total_count": len(gsm) + len(hotpot),
        "unique_candidate_ids": len(set(ids)),
        "partitions": {
            name: {
                "gsm8k": sum(row["partition"] == name for row in gsm),
                "hotpotqa": sum(row["partition"] == name for row in hotpot),
            }
            for name in PARTITIONS
        },
        "final_test_count": sum(row.get("partition") == "final_test" for _, row in all_rows),
        "unresolved_before_review": sum(row.get("adjudication_status_before_pilot") == "unresolved" for _, row in all_rows),
        "pending_reviews": sum(row.get("adjudication_status") is None for _, row in all_rows),
        "second_reviewer_decisions": sum(has_second_reviewer_fields(row) for _, row in all_rows),
        "errors": [],
    }


def create(seed: int, output: Path) -> dict:
    if output.exists():
        if any(output.iterdir()):
            raise FileExistsError(f"Refusing to overwrite non-empty pilot directory: {output}")
    # Validate the source prefix before creating any output files.
    unified = {part: read_unified(part) for part in PARTITIONS}
    source_rows: dict[str, list[dict]] = {}
    prefix_hashes: dict[str, str] = {}
    for dataset in SOURCE_TAG:
        source_path = SOURCE_ADJUDICATION / f"{dataset}_adjudications.jsonl"
        source_rows[dataset], prefix_hashes[dataset] = read_history_development_prefix(source_path, dataset)

    chosen: dict[str, list[dict]] = {}
    queues: dict[str, list[dict]] = {}
    for dataset, source_tag in SOURCE_TAG.items():
        eligible = [
            row for row in source_rows[dataset]
            if row.get("adjudication_status") == "unresolved"
            and row.get("candidate_source") == source_tag
            and row.get("partition") in PARTITIONS
        ]
        eligible.sort(key=lambda row: row["candidate_id"])
        if len(eligible) < PER_DATASET:
            raise ValueError(f"Only {len(eligible)} eligible {dataset} candidates; need {PER_DATASET}")
        selected = random.Random(seed + (0 if dataset == "gsm8k" else 1)).sample(eligible, PER_DATASET)
        selected.sort(key=lambda row: row["candidate_id"])
        queue: list[dict] = []
        for source in selected:
            partition = source["partition"]
            example = unified[partition].get(source["example_id"])
            if example is None:
                raise ValueError(f"Missing {partition} source example {source['example_id']}")
            candidate_index = int(source["candidate_id"].rsplit("candidate_", 1)[1])
            candidate = (example.get("candidate_answers") or [])[candidate_index]
            if candidate.get("source") != source_tag or str(candidate.get("answer")) != source["candidate_answer"]:
                raise ValueError(f"Candidate/source mismatch for {source['candidate_id']}")
            row = {
                "candidate_id": source["candidate_id"],
                "example_id": source["example_id"],
                "dataset": source["dataset"],
                "dataset_version": source["dataset_version"],
                "partition": partition,
                "question": example.get("question"),
                "benchmark_gold_answer": source.get("source_gold_answer"),
                "candidate_answer": source["candidate_answer"],
                "candidate_generation_method": source_tag,
                "adjudication_status_before_pilot": source["adjudication_status"],
                **blank_review(),
                "adjudicator": None,
                "adjudicator_evidence": [],
                "adjudicator_provenance": [],
                "adjudicator_rationale": None,
            }
            if dataset == "gsm8k":
                row["original_worked_solution"] = example.get("solution")
                row["review_instruction"] = "Solve independently before consulting the worked solution; record answer, units, derivation, and ambiguity."
            else:
                row["supplied_context"] = example.get("context") or []
                row["supporting_facts"] = example.get("supporting_facts") or []
                row["donor_id"] = None
                row["donor_id_status"] = "not_recorded_by_source_builder; not inferred"
                row["review_instruction"] = "Judge whether the answer addresses the target question using supplied context and supporting facts; substring matches are not proof."
            queue.append(row)
        chosen[dataset] = selected
        queues[dataset] = queue

    # Do not create an output directory until all source and selection checks pass.
    output.mkdir(parents=True, exist_ok=True)
    all_selected_ids = {dataset: [row["candidate_id"] for row in rows] for dataset, rows in chosen.items()}
    partition_counts = {
        dataset: dict(collections.Counter(row["partition"] for row in rows))
        for dataset, rows in chosen.items()
    }
    decisions = []
    for dataset in SOURCE_TAG:
        for row in queues[dataset]:
            decisions.append({
                "candidate_id": row["candidate_id"],
                "dataset": dataset,
                "partition": row["partition"],
                "adjudication_status_before_pilot": "unresolved",
                **blank_review(),
                "adjudicator": None,
                "adjudicator_evidence": [],
                "adjudicator_provenance": [],
                "adjudicator_rationale": None,
            })
    for dataset in SOURCE_TAG:
        write_jsonl(output / f"{dataset}_review_queue.jsonl", queues[dataset])
    write_jsonl(output / "decisions_template.jsonl", decisions)
    create_reviewer_views(output)
    manifest = {
        "pilot_version": "candidate-adjudication-pilot-v3",
        "selection_date": date.today().isoformat(),
        "seed": seed,
        "sampling": "sort unresolved generated candidate records by candidate_id, sample without replacement using Python random.Random(seed) for GSM8K and random.Random(seed+1) for HotpotQA, then sort selected IDs for output",
        "per_dataset": PER_DATASET,
        "partitions_included": list(PARTITIONS),
        "final_test_excluded": True,
        "final_test_data_read": False,
        "source_paths": {
            "unified_history": "evaluation/datasets/unified/history.json",
            "unified_development": "evaluation/datasets/unified/development.json",
            "adjudication_source": "evaluation/datasets/adjudication/v1/{gsm8k,hotpotqa}_adjudications.jsonl (History+Development prefix only; Final Test lines were not read)",
        },
        "source_sha256": {
            "evaluation/datasets/unified/history.json": sha256_file(ROOT / "evaluation/datasets/unified/history.json"),
            "evaluation/datasets/unified/development.json": sha256_file(ROOT / "evaluation/datasets/unified/development.json"),
            "gsm8k_adjudication_history_development_prefix": prefix_hashes["gsm8k"],
            "hotpotqa_adjudication_history_development_prefix": prefix_hashes["hotpotqa"],
        },
        "candidate_generation_methods": SOURCE_TAG,
        "dataset_versions": {
            "GSM8K": "main@740312add88f781978c0658806c59bc2815b9866",
            "HotpotQA": "distractor@1908d6afbbead072334abe2965f91bd2709910ab",
        },
        "selected_candidate_ids": all_selected_ids,
        "partition_counts": partition_counts,
        "unresolved_before_review": True,
        "reviewer_count": 1,
        "initial_reviews_populated": False,
        "second_review_decisions_entered": False,
        "consistency_check": {
            "status": "pending_until_all_60_initial_reviews_are_complete",
            "seed": CONSISTENCY_SEED,
            "sample_size": 15,
            "strata": {"gsm8k": 8, "hotpotqa": 7},
            "measure": "intra-reviewer consistency, not inter-reviewer agreement",
        },
        "framework_predictions_included": False,
        "hotpotqa_donor_id": "null when not reliably recorded; never inferred",
        "source_datasets_modified": False,
        "existing_adjudication_files_modified": False,
        "notice": "Review queues only. No correctness decisions have been assigned.",
    }
    (output / "pilot_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    readme = README
    (output / "README.md").write_text(readme, encoding="utf-8")
    result = validate_directory(output)
    (output / "validation_report.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


def write_jsonl(path: Path, rows: list[dict]) -> None:
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def create_reviewer_views(directory: Path) -> None:
    """Write one reviewer queue per benchmark; no second reviewer is implied."""
    reviewer_dir = directory / "reviewer"
    if reviewer_dir.exists() and any(reviewer_dir.iterdir()):
        raise FileExistsError(f"Refusing to overwrite reviewer queue directory: {reviewer_dir}")
    reviewer_dir.mkdir(parents=True, exist_ok=True)
    for dataset in SOURCE_TAG:
        rows = read_jsonl(directory / f"{dataset}_review_queue.jsonl")
        write_jsonl(reviewer_dir / f"{dataset}_review_queue.jsonl", rows)


def validate_directory(directory: Path, decisions_file: Path | None = None) -> dict:
    gsm = read_jsonl(directory / "gsm8k_review_queue.jsonl")
    hotpot = read_jsonl(directory / "hotpotqa_review_queue.jsonl")
    report = validate_records(gsm, hotpot)
    manifest = json.loads((directory / "pilot_manifest.json").read_text(encoding="utf-8"))
    if manifest.get("final_test_excluded") is not True or manifest.get("final_test_data_read") is not False:
        raise ValueError("Manifest must affirm Final Test exclusion and non-access")
    if manifest.get("reviewer_count") != 1:
        raise ValueError("Pilot manifest must declare exactly one initial reviewer")
    if manifest.get("partitions_included") != list(PARTITIONS):
        raise ValueError("Manifest partition declaration is invalid")
    decision_path = decisions_file or (directory / "decisions_template.jsonl")
    template = read_jsonl(decision_path)
    if len(template) != 60 or len({row.get("candidate_id") for row in template}) != 60:
        raise ValueError("Decision template must have 60 unique candidate IDs")
    queue_ids = {row["candidate_id"] for row in gsm + hotpot}
    if {row.get("candidate_id") for row in template} != queue_ids:
        raise ValueError("Decision file IDs must match the review queue IDs")
    manifest_ids = manifest.get("selected_candidate_ids", {})
    if {row["candidate_id"] for row in gsm} != set(manifest_ids.get("gsm8k", [])):
        raise ValueError("GSM8K queue IDs differ from the original pilot manifest")
    if {row["candidate_id"] for row in hotpot} != set(manifest_ids.get("hotpotqa", [])):
        raise ValueError("HotpotQA queue IDs differ from the original pilot manifest")
    expected_partitions = {"gsm8k": {"history": 26, "development": 4}, "hotpotqa": {"history": 22, "development": 8}}
    for dataset, rows in (("gsm8k", gsm), ("hotpotqa", hotpot)):
        actual = dict(collections.Counter(row["partition"] for row in rows))
        if actual != expected_partitions[dataset]:
            raise ValueError(f"{dataset} partition counts changed: {actual}")
    for row in template:
        if has_second_reviewer_fields(row):
            raise ValueError(f"{row.get('candidate_id')}: multiple-reviewer structure is not allowed")
        status = row.get("adjudication_status")
        if status is not None and status not in VALID_DECISIONS:
            raise ValueError(f"{row.get('candidate_id')}: invalid adjudication status {status!r}")
        if status is None:
            if row.get("reviewer_id") is not None or row.get("adjudication_evidence") or row.get("adjudication_provenance") or row.get("adjudication_rationale"):
                raise ValueError(f"{row.get('candidate_id')}: pending record contains a decision")
        elif not all((row.get("reviewer_id"), row.get("adjudication_evidence"), row.get("adjudication_provenance"), row.get("adjudication_rationale"))):
            raise ValueError(f"{row.get('candidate_id')}: completed review requires reviewer, evidence, provenance, and rationale")
        if "adjudicator" not in row:
            raise ValueError(f"{row.get('candidate_id')}: exceptional adjudicator field missing")
    completed_reviewer_ids = {row.get("reviewer_id") for row in template if row.get("adjudication_status") is not None}
    if len(completed_reviewer_ids) > 1:
        raise ValueError("Initial reviews must use one consistent human reviewer ID")
    report["decision_template_records"] = len(template)
    report["pending_decision_records"] = sum(row.get("adjudication_status") is None for row in template)
    report["second_reviewer_decisions"] = sum(has_second_reviewer_fields(row) for row in template)
    report["decision_values_valid"] = True
    report["required_evidence_fields_enforced_for_completed_decisions"] = True
    report["exceptional_adjudicator_field_present"] = True
    report["initial_reviewer_count"] = 1
    report["final_test_excluded"] = True
    report["validated_decisions_file"] = str(decision_path)
    for retired_name in ("reviewer_1", "reviewer_2"):
        if (directory / retired_name).exists():
            raise ValueError(f"Retired multi-reviewer directory still present: {retired_name}")
    for dataset in SOURCE_TAG:
        isolated = read_jsonl(directory / "reviewer" / f"{dataset}_review_queue.jsonl")
        expected = gsm if dataset == "gsm8k" else hotpot
        if [row.get("candidate_id") for row in isolated] != [row.get("candidate_id") for row in expected]:
            raise ValueError(f"Single-reviewer {dataset} queue IDs do not match the main queue")
        if any(has_second_reviewer_fields(row) for row in isolated):
            raise ValueError(f"Single-reviewer {dataset} queue contains a second reviewer field")
    report["single_reviewer_queues"] = True
    return report


def validate_completed_reviews(records: list[dict], expected_ids: set[str], expected_count: int) -> None:
    if len(records) != expected_count or {row.get("candidate_id") for row in records} != expected_ids:
        raise ValueError(f"Expected exactly {expected_count} completed review records with matching candidate IDs")
    if len({row.get("candidate_id") for row in records}) != len(records):
        raise ValueError("Duplicate candidate IDs in completed review file")
    for row in records:
        if row.get("partition") not in PARTITIONS:
            raise ValueError(f"{row.get('candidate_id')}: Final Test/unknown partition is not allowed")
        if row.get("adjudication_status") not in VALID_DECISIONS:
            raise ValueError(f"{row.get('candidate_id')}: completed review must use a permitted adjudication_status")
        if has_second_reviewer_fields(row):
            raise ValueError(f"{row.get('candidate_id')}: second reviewer fields are prohibited")
        if not all((row.get("reviewer_id"), row.get("adjudication_evidence"), row.get("adjudication_provenance"), row.get("adjudication_rationale"))):
            raise ValueError(f"{row.get('candidate_id')}: reviewer ID, evidence, provenance, and rationale are required")
    if len({row.get("reviewer_id") for row in records}) != 1:
        raise ValueError("All completed records must use the same single human reviewer ID")


def convert_legacy_record(row: dict) -> dict:
    """Convert one still-pending two-slot row, preserving all candidate fields."""
    old_slots = row.pop("reviewer_decisions", None)
    if not isinstance(old_slots, list) or len(old_slots) != 2:
        raise ValueError(f"{row.get('candidate_id')}: expected old two-slot structure for migration")
    if any(slot.get("reviewer_id") or slot.get("decision") or slot.get("evidence") or slot.get("rationale") for slot in old_slots):
        raise ValueError(f"{row.get('candidate_id')}: cannot migrate populated reviewer decisions")
    row.pop("disagreement", None)
    row.pop("adjudicator_decision", None)
    row.pop("adjudicator_evidence_provenance", None)
    row.pop("adjudication_method", None)
    row["reviewer_id"] = None
    row["adjudication_status"] = None
    row["adjudication_evidence"] = []
    row["adjudication_provenance"] = []
    row["adjudication_rationale"] = None
    row.setdefault("adjudicator", None)
    row.setdefault("adjudicator_evidence", [])
    row.setdefault("adjudicator_provenance", [])
    row.setdefault("adjudicator_rationale", None)
    return row


def migrate_existing_schema(directory: Path, backup: Path) -> dict:
    if not backup.is_dir():
        raise FileNotFoundError(f"Required pre-change backup not found: {backup}")
    manifest_path = directory / "pilot_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("final_test_excluded") is not True:
        raise ValueError("Pilot manifest does not establish Final Test exclusion")
    expected_ids = manifest.get("selected_candidate_ids", {})
    all_ids: set[str] = set()
    migrated_queues: dict[str, list[dict]] = {}
    for dataset in SOURCE_TAG:
        name = f"{dataset}_review_queue.jsonl"
        current = directory / name
        saved = backup / name
        if not saved.is_file() or current.read_bytes() != saved.read_bytes():
            raise ValueError(f"Current queue does not match its preserved backup: {current}")
        rows = [convert_legacy_record(row) for row in read_jsonl(current)]
        ids = [row["candidate_id"] for row in rows]
        if len(ids) != 30 or ids != expected_ids.get(dataset):
            raise ValueError(f"{dataset}: migration must preserve all original 30 IDs and their order")
        if any(row.get("partition") not in PARTITIONS for row in rows):
            raise ValueError("Final Test/unknown partition encountered during migration")
        all_ids.update(ids)
        migrated_queues[dataset] = rows

    template_path = directory / "decisions_template.jsonl"
    backup_template = backup / "decisions_template.jsonl"
    if not backup_template.is_file() or template_path.read_bytes() != backup_template.read_bytes():
        raise ValueError("Decision template does not match its preserved backup")
    template = [convert_legacy_record(row) for row in read_jsonl(template_path)]
    if len(template) != 60 or {row["candidate_id"] for row in template} != all_ids:
        raise ValueError("Template migration changed candidate identities or count")

    # Confirm the two prior private queue directories also match their backups
    # before retiring those folders; initial slots must all be blank.
    for reviewer in ("reviewer_1", "reviewer_2"):
        source_dir = directory / reviewer
        backup_dir = backup / reviewer
        for dataset in SOURCE_TAG:
            filename = f"{dataset}_review_queue.jsonl"
            original = source_dir / filename
            saved = backup_dir / filename
            if not saved.is_file() or original.read_bytes() != saved.read_bytes():
                raise ValueError(f"Reviewer queue does not match its backup: {original}")

    reviewer_dir = directory / "reviewer"
    if reviewer_dir.exists():
        raise FileExistsError(f"Single-reviewer directory already exists: {reviewer_dir}")
    reviewer_dir.mkdir()
    for dataset, rows in migrated_queues.items():
        write_jsonl(reviewer_dir / f"{dataset}_review_queue.jsonl", rows)
    for dataset, rows in migrated_queues.items():
        path = directory / f"{dataset}_review_queue.jsonl"
        path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")
    template_path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in template), encoding="utf-8")

    for reviewer in ("reviewer_1", "reviewer_2"):
        target = (directory / reviewer).resolve()
        root = directory.resolve()
        if root not in target.parents:
            raise ValueError("Refusing to retire a reviewer folder outside the pilot directory")
        shutil.rmtree(target)
    manifest["pilot_version"] = "candidate-adjudication-pilot-v3-single-reviewer"
    manifest["reviewer_count"] = 1
    manifest["initial_review_count"] = 60
    manifest["consistency_check"] = {
        "status": "pending_until_all_60_initial_reviews_are_complete",
        "seed": CONSISTENCY_SEED,
        "sample_size": 15,
        "strata": {"gsm8k": 8, "hotpotqa": 7},
        "measure": "intra-reviewer consistency, not inter-reviewer agreement",
    }
    manifest.pop("reviewer_decisions_populated", None)
    manifest["initial_reviews_populated"] = False
    manifest["second_review_decisions_entered"] = False
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"migrated_candidates": len(all_ids), "unique_candidate_ids": len(all_ids), "backup_verified": True, "final_test_count": 0}


def prepare_consistency(pilot_dir: Path, directory: Path, initial_decisions: Path, seed: int) -> dict:
    if directory.exists():
        if any(directory.iterdir()):
            raise FileExistsError(f"Refusing to overwrite consistency output: {directory}")
    queue_records = read_jsonl(pilot_dir / "gsm8k_review_queue.jsonl") + read_jsonl(pilot_dir / "hotpotqa_review_queue.jsonl")
    queue_ids = {row["candidate_id"] for row in queue_records}
    initial = read_jsonl(initial_decisions)
    validate_completed_reviews(initial, queue_ids, 60)
    by_id = {row["candidate_id"]: row for row in queue_records}
    strata = {
        "gsm8k": (8, [row for row in initial if row.get("dataset", "").lower() == "gsm8k"]),
        "hotpotqa": (7, [row for row in initial if row.get("dataset", "").lower() == "hotpotqa"]),
    }
    second_queue: list[dict] = []
    selected_ids: dict[str, list[str]] = {}
    for offset, (dataset, (count, pool)) in enumerate(strata.items()):
        if len(pool) != 30:
            raise ValueError(f"Expected 30 initial {dataset} reviews; found {len(pool)}")
        pool.sort(key=lambda row: row["candidate_id"])
        selected = random.Random(seed + offset).sample(pool, count)
        selected.sort(key=lambda row: row["candidate_id"])
        selected_ids[dataset] = []
        for reviewed in selected:
            candidate_id = reviewed["candidate_id"]
            source = by_id[candidate_id]
            view = {key: source[key] for key in (
                "candidate_id", "example_id", "dataset", "dataset_version", "partition", "question",
                "benchmark_gold_answer", "candidate_answer", "candidate_generation_method",
                "original_worked_solution", "supplied_context", "supporting_facts", "donor_id",
                "donor_id_status", "review_instruction",
            ) if key in source}
            view.update(blank_review())
            view["review_stage"] = "blinded_intra_reviewer_consistency_second_pass"
            view["reviewer_id"] = None
            second_queue.append(view)
            selected_ids[dataset].append(candidate_id)
    directory.mkdir(parents=True, exist_ok=True)
    write_jsonl(directory / "second_review_queue.jsonl", second_queue)
    manifest = {
        "consistency_check_version": "intra-reviewer-consistency-v1",
        "seed": seed,
        "sampling": "stratified sample without replacement: 8 GSM8K and 7 HotpotQA; candidates sorted by ID before random.Random(seed + dataset_offset).sample",
        "stratum_counts": {"gsm8k": 8, "hotpotqa": 7},
        "selected_candidate_ids": selected_ids,
        "initial_decisions_file": str(initial_decisions),
        "initial_decisions_exposed_in_second_review_queue": False,
        "final_test_included": False,
        "purpose": "intra-reviewer consistency only; not inter-reviewer agreement",
        "second_review_decisions_entered": False,
    }
    (directory / "consistency_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"selected": len(second_queue), "gsm8k": 8, "hotpotqa": 7, "initial_decisions_hidden": True, "final_test_count": 0}


def analyze_consistency(initial_decisions: Path, second_decisions: Path, consistency_manifest: Path, output: Path) -> dict:
    if initial_decisions.resolve() == second_decisions.resolve():
        raise ValueError("Initial and second-review decision files must be separate")
    initial = read_jsonl(initial_decisions)
    second = read_jsonl(second_decisions)
    second_ids = {row.get("candidate_id") for row in second}
    validate_completed_reviews(second, second_ids, 15)
    second_counts = collections.Counter(str(row.get("dataset", "")).lower() for row in second)
    if second_counts != {"gsm8k": 8, "hotpotqa": 7}:
        raise ValueError(f"Consistency sample must contain 8 GSM8K and 7 HotpotQA cases; found {dict(second_counts)}")
    manifest = json.loads(consistency_manifest.read_text(encoding="utf-8"))
    manifest_ids = {candidate_id for ids in manifest.get("selected_candidate_ids", {}).values() for candidate_id in ids}
    if second_ids != manifest_ids:
        raise ValueError("Second review IDs do not match the reproducible sample manifest")
    initial_by_id = {row.get("candidate_id"): row for row in initial}
    if len(initial_by_id) != 60:
        raise ValueError("Initial decision file must contain 60 unique candidates")
    if not second_ids.issubset(initial_by_id):
        raise ValueError("Second-review candidates must come from initial 60")
    if any(row.get("partition") not in PARTITIONS for row in initial + second):
        raise ValueError("Final Test records are not allowed")
    pairs = []
    matrix: dict[str, dict[str, int]] = {}
    for row in second:
        original = initial_by_id[row["candidate_id"]]
        first_decision = original.get("adjudication_status")
        second_decision = row.get("adjudication_status")
        if row.get("reviewer_id") != original.get("reviewer_id"):
            raise ValueError(f"{row['candidate_id']}: second review must be by the original reviewer")
        if first_decision not in VALID_DECISIONS:
            raise ValueError(f"{row['candidate_id']}: initial decision is incomplete")
        matrix.setdefault(first_decision, {}).setdefault(second_decision, 0)
        matrix[first_decision][second_decision] += 1
        pairs.append({
            "candidate_id": row["candidate_id"],
            "dataset": row.get("dataset", original.get("dataset")),
            "initial_status": first_decision,
            "second_review_status": second_decision,
            "exact_match": first_decision == second_decision,
        })
    agree = sum(pair["exact_match"] for pair in pairs)
    report = {
        "measure": "intra-reviewer exact categorical consistency",
        "not_inter_reviewer_agreement": True,
        "initial_decisions_file": str(initial_decisions),
        "second_decisions_file": str(second_decisions),
        "consistency_manifest": str(consistency_manifest),
        "sample_size": len(pairs),
        "agreement_count": agree,
        "disagreement_count": len(pairs) - agree,
        "exact_agreement_rate": agree / len(pairs) if pairs else None,
        "exact_disagreement_rate": (len(pairs) - agree) / len(pairs) if pairs else None,
        "transition_counts": matrix,
        "paired_decisions": pairs,
        "initial_decisions_modified": False,
    }
    if output.exists():
        raise FileExistsError(f"Refusing to overwrite consistency report: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


README = """# Candidate adjudication pilot v3\n\nThis pilot contains 30 unresolved GSM8K synthetic numeric perturbations and 30 unresolved HotpotQA borrowed answers, all from History and Development. The seed and hashes are in `pilot_manifest.json`; no Final Test data were accessed or selected. No framework predictions or human decisions are included.\n\n## Single-reviewer process\n\nOne human reviewer records one `reviewer_id`, `adjudication_status` (`verified_correct`, `verified_incorrect`, or `unresolved`), `adjudication_evidence`, `adjudication_provenance`, and `adjudication_rationale` per candidate. Pending statuses and empty evidence fields mean no review has been entered. Do not create a second reviewer or fill a second slot. For GSM8K, solve independently before consulting the supplied solution. For HotpotQA, use the supplied context/supporting facts; substring matching alone is not proof. Keep ambiguous or under-evidenced cases unresolved. The borrower donor ID was not retained by the source builder and is not inferred.\n\nA separate `adjudicator` field is reserved for an exceptional third-party review, such as a later audit; it does not imply that a second reviewer participated in the initial adjudication. Preserve the first decision if this field is ever used.\n\n## Intra-reviewer consistency check\n\nOnly after all 60 initial reviews are complete, select 15 cases reproducibly using seed 20261103: 8 GSM8K and 7 HotpotQA, sampled without replacement from sorted candidate IDs. The second-review queue omits the initial decision, evidence, provenance, and rationale. The same reviewer completes it independently; save those decisions separately from the initial file. Compare exact categorical status labels and report agreement/disagreement counts and rates. This is intra-reviewer consistency, not inter-reviewer agreement. Initial decisions must never be overwritten. See the evaluation protocol document for commands and details.\n"""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    prepare = subparsers.add_parser("prepare")
    prepare.add_argument("--seed", type=int, default=SEED)
    prepare.add_argument("--output-dir", type=Path, default=OUTPUT)
    validate = subparsers.add_parser("validate")
    validate.add_argument("--pilot-dir", type=Path, default=OUTPUT)
    validate.add_argument("--decisions-file", type=Path, default=None)
    consistency = subparsers.add_parser("prepare-consistency")
    consistency.add_argument("--pilot-dir", type=Path, default=OUTPUT)
    consistency.add_argument("--initial-decisions", type=Path, required=True)
    consistency.add_argument("--seed", type=int, default=CONSISTENCY_SEED)
    consistency.add_argument("--output-dir", type=Path, default=OUTPUT / f"consistency_check_seed_{CONSISTENCY_SEED}")
    analyze = subparsers.add_parser("analyze-consistency")
    analyze.add_argument("--initial-decisions", type=Path, required=True)
    analyze.add_argument("--second-decisions", type=Path, required=True)
    analyze.add_argument("--consistency-manifest", type=Path, required=True)
    analyze.add_argument("--output", type=Path, required=True)
    migrate = subparsers.add_parser("migrate-existing-schema")
    migrate.add_argument("--pilot-dir", type=Path, default=OUTPUT)
    migrate.add_argument("--backup-dir", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "prepare":
        result = create(args.seed, args.output_dir)
    elif args.command == "migrate-existing-schema":
        result = migrate_existing_schema(args.pilot_dir, args.backup_dir)
    elif args.command == "validate":
        result = validate_directory(args.pilot_dir, args.decisions_file)
        (args.pilot_dir / "validation_report.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    elif args.command == "prepare-consistency":
        result = prepare_consistency(args.pilot_dir, args.output_dir, args.initial_decisions, args.seed)
    else:
        result = analyze_consistency(args.initial_decisions, args.second_decisions, args.consistency_manifest, args.output)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
