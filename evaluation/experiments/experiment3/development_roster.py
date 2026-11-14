"""Approved Development roster for Experiment 3.

Reads the eligibility manifest and its Development JSONL. It does not open
Final Test labels, rewrite the roster, or authorize collection.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ELIGIBILITY_RELATIVE = "evaluation/artifacts/person1/research_v1_exploratory_eligibility_approved_v1/eligibility_manifest.json"
EXPECTED_BODY_SHA256 = "f2cc0fd108b961bf4795767df4f90e92d7fa0f418ef9865d0206f32d7b45282d"
EXPECTED_GROUPS = {"GSM8K": 187, "HotpotQA": 185}
EXPECTED_CANDIDATES = 744
EXPECTED_GROUP_TOTAL = 372
BINARY_LABELS = frozenset({"VERIFIED_CORRECT", "SYNTHETIC_INCORRECT"})


def _reject_final_test(path: Path) -> None:
    text = path.as_posix().lower()
    if "final_test" in text or "final-test" in text:
        raise RuntimeError(f"refusing a Final Test path: {path.as_posix()}")


def _lf_sha256(path: Path) -> str:
    normalized = path.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return hashlib.sha256(normalized).hexdigest()


def _canonical(payload: dict) -> bytes:
    return (json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")


def load_roster(root: Path) -> dict:
    """Return paired Development groups from the approved eligibility outputs."""
    root = Path(root)
    manifest_path = root / ELIGIBILITY_RELATIVE
    _reject_final_test(manifest_path)
    if not manifest_path.is_file():
        raise FileNotFoundError(ELIGIBILITY_RELATIVE)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("final_test_authorized") is True or manifest.get("collection_authorized") is True:
        raise RuntimeError("eligibility manifest unexpectedly authorizes collection or Final Test")
    if manifest.get("dataset_version") != "research_v1_exploratory_v1":
        raise ValueError("eligibility manifest dataset version changed")
    body = {key: value for key, value in manifest.items() if key != "eligibility_manifest_sha256"}
    body_sha256 = hashlib.sha256(_canonical(body)).hexdigest()
    if body_sha256 != EXPECTED_BODY_SHA256 or manifest.get("eligibility_manifest_sha256") != EXPECTED_BODY_SHA256:
        raise ValueError("eligibility manifest body hash does not match the approved digest")
    folder = manifest_path.parent
    eligible_path = folder / "development_eligible.jsonl"
    _reject_final_test(eligible_path)
    expected_outputs = manifest.get("output_sha256") or {}
    output_hashes = {}
    for name, expected in expected_outputs.items():
        path = folder / name
        _reject_final_test(path)
        output_hashes[name] = _lf_sha256(path) if path.is_file() else None
        if output_hashes[name] != expected:
            raise ValueError(f"LF-normalized hash mismatch for {name}")
    groups: dict[str, dict] = {}
    candidate_ids: list[str] = []
    for line in eligible_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("partition") != "development":
            raise RuntimeError("eligible roster row is not a Development partition row")
        if row.get("eligible") is not True:
            raise ValueError("development_eligible.jsonl contains an ineligible row")
        label = row.get("label_class")
        if label not in BINARY_LABELS:
            raise ValueError("eligible row does not have a binary Development label")
        group_id = str(row.get("related_group_id") or "")
        candidate_id = str(row.get("candidate_id") or "")
        benchmark = str(row.get("benchmark") or "")
        if not group_id or not candidate_id or benchmark not in EXPECTED_GROUPS:
            raise ValueError("eligible row is missing group, candidate, or benchmark identity")
        candidate_ids.append(candidate_id)
        group = groups.setdefault(group_id, {
            "related_group_id": group_id,
            "benchmark": benchmark,
            "question_id": row.get("question_id"),
            "dataset_version": row.get("dataset_version"),
            "candidates": [],
        })
        if group["benchmark"] != benchmark or group["question_id"] != row.get("question_id"):
            raise ValueError(f"group {group_id} pairs candidates from different questions")
        group["candidates"].append({
            "candidate_id": candidate_id,
            "label_class": label,
            "label_source": row.get("label_source"),
            "label_protocol": row.get("label_protocol"),
            "label_method": row.get("label_method"),
            "human_verified": row.get("human_verified"),
            "question_id": row.get("question_id"),
            "partition": "development",
        })
    if len(candidate_ids) != len(set(candidate_ids)):
        raise ValueError("duplicate candidate id in the Development roster")
    by_benchmark: dict[str, int] = {name: 0 for name in EXPECTED_GROUPS}
    for group in groups.values():
        labels = [item["label_class"] for item in group["candidates"]]
        if len(group["candidates"]) != 2 or set(labels) != set(BINARY_LABELS):
            raise ValueError(f"group {group['related_group_id']} is not one correct and one incorrect candidate")
        by_benchmark[group["benchmark"]] += 1
    if by_benchmark != EXPECTED_GROUPS or len(groups) != EXPECTED_GROUP_TOTAL or len(candidate_ids) != EXPECTED_CANDIDATES:
        raise ValueError("Development roster counts differ from the approved manifest")
    counts = manifest.get("counts") or {}
    if counts.get("eligible_groups") != EXPECTED_GROUP_TOTAL or counts.get("eligible_candidates") != EXPECTED_CANDIDATES:
        raise ValueError("eligibility manifest counts differ from the approved roster")
    ordered = tuple(sorted(groups.values(), key=lambda item: item["related_group_id"]))
    return {
        "eligibility_manifest": ELIGIBILITY_RELATIVE,
        "eligibility_body_sha256": body_sha256,
        "dataset_version": manifest.get("dataset_version"),
        "label_protocol": manifest.get("label_protocol"),
        "collection_authorized": manifest.get("collection_authorized"),
        "recording_authorized": manifest.get("recording_authorized"),
        "final_test_authorized": manifest.get("final_test_authorized"),
        "does_not_authorize": list(manifest.get("does_not_authorize") or []),
        "output_lf_sha256": output_hashes,
        "groups": len(ordered),
        "candidates": len(candidate_ids),
        "groups_by_benchmark": by_benchmark,
        "paired_groups": ordered,
    }
