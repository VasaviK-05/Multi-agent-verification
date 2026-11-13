"""Provisional eligibility audit for research_v1_exploratory_v1.

Reads the exploratory History/Development snapshot only. It does not read Final
Test labels, does not rewrite the snapshot, and does not authorize collection.
The result is provisional: scientific approval of the eligibility rule is pending.
"""
from __future__ import annotations

import argparse
import collections
import json
import subprocess
from pathlib import Path

from evaluation.data_preparation.final_test_workflow import (
    ROOT, canonical_bytes, context_hashes, jsonl_bytes, norm_question, read_jsonl, sha256_bytes, sha256_file,
)
from evaluation.data_preparation.label_classes import (
    HUMAN_VERIFIED_INCORRECT, PROTOCOL, SYNTHETIC_INCORRECT, UNRESOLVED, VERIFIED_CORRECT,
)

VERSION = "research_v1_exploratory_eligibility_provisional_v1"
DATASET_VERSION = "research_v1_exploratory_v1"
SOURCE = ROOT / "evaluation/datasets/research_v1_exploratory" / DATASET_VERSION
OUTPUT = ROOT / "evaluation/datasets/person1" / VERSION
ARTIFACT = ROOT / "evaluation/artifacts/person1" / VERSION
BINARY = {VERIFIED_CORRECT, SYNTHETIC_INCORRECT}
CRITERIA = (
    "PROVISIONAL, NOT APPROVED. A Development candidate is provisionally eligible only when "
    "its dataset_version is research_v1_exploratory_v1, its label_class is VERIFIED_CORRECT or "
    "SYNTHETIC_INCORRECT, human_verified is false, and its related_group_id has exactly one "
    "VERIFIED_CORRECT and one SYNTHETIC_INCORRECT Development candidate. UNRESOLVED is excluded "
    "and is never incorrect. SYNTHETIC_INCORRECT is not HUMAN_VERIFIED_INCORRECT. History is not "
    "an eligibility population. This audit does not authorize verifier collection or recording."
)


def _git_revision() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        return "UNAVAILABLE"


def _identity(row: dict, *, eligible: bool, reason: str) -> dict:
    source = row.get("source") if isinstance(row.get("source"), dict) else {}
    return {
        "candidate_id": row.get("candidate_id"),
        "related_group_id": row.get("related_group_id"),
        "split_identity": row.get("split_identity"),
        "partition": row.get("partition"),
        "benchmark": row.get("benchmark"),
        "question_id": row.get("question_id"),
        "source_dataset_id": source.get("research_v1_dataset_id") or row.get("dataset_id"),
        "dataset_version": row.get("dataset_version", DATASET_VERSION),
        "label_class": row.get("label_class"),
        "label_method": row.get("label_method"),
        "label_source": row.get("label_source"),
        "label_protocol": row.get("label_protocol"),
        "human_verified": row.get("human_verified"),
        "eligible": eligible,
        "exclusion_reason": None if eligible else reason,
    }


def _load(name: str) -> list[dict]:
    path = SOURCE / name
    if not path.is_file():
        raise FileNotFoundError(f"exploratory snapshot file missing: {path}")
    return read_jsonl(path)


def audit(source: Path = SOURCE) -> dict:
    """Return eligibility rows and audits. Does not write and does not open Final Test files."""
    if source.resolve() != SOURCE.resolve():
        raise ValueError("eligibility audit is bound to research_v1_exploratory_v1")
    manifest = json.loads((source / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("dataset_version") != DATASET_VERSION:
        raise ValueError("source manifest version differs from research_v1_exploratory_v1")
    labelled = {role: _load(f"{role}_candidates.jsonl") for role in ("history", "development")}
    unresolved = _load("unresolved_candidates.jsonl")
    skipped = _load("skipped_groups.jsonl")
    for role, rows in labelled.items():
        for row in rows:
            if row.get("partition", role) != role:
                raise ValueError("candidate partition differs from its file")
            if row.get("dataset_version") != DATASET_VERSION:
                raise ValueError("candidate dataset_version differs from the snapshot")
            if row.get("label_class") == HUMAN_VERIFIED_INCORRECT or row.get("human_verified") is True:
                raise ValueError("refusing to treat a synthetic snapshot row as human-verified incorrect")
            if row.get("label_class") == SYNTHETIC_INCORRECT and row.get("answer_is_correct") is not False:
                raise ValueError("SYNTHETIC_INCORRECT must stay incorrect")
            if row.get("label_class") == VERIFIED_CORRECT and row.get("answer_is_correct") is not True:
                raise ValueError("VERIFIED_CORRECT must stay correct")
    groups: dict[str, list[dict]] = collections.defaultdict(list)
    for row in labelled["development"]:
        groups[row["related_group_id"]].append(row)
    eligible, excluded = [], []
    group_rows = []
    for gid, rows in sorted(groups.items()):
        classes = collections.Counter(row["label_class"] for row in rows)
        paired = classes[VERIFIED_CORRECT] == 1 and classes[SYNTHETIC_INCORRECT] == 1 and len(rows) == 2
        benchmarks = {row["benchmark"] for row in rows}
        reason = None if paired and len(benchmarks) == 1 else (
            "mixed_benchmark_group" if len(benchmarks) != 1 else "group_not_exactly_one_correct_and_one_synthetic_incorrect")
        group_rows.append({"related_group_id": gid, "benchmark": next(iter(benchmarks)),
                           "label_classes": dict(sorted(classes.items())), "paired": paired and reason is None,
                           "provisionally_eligible": reason is None})
        for row in sorted(rows, key=lambda item: item["candidate_id"]):
            if reason is None and row["label_class"] in BINARY and row.get("human_verified") is False:
                eligible.append(_identity(row, eligible=True, reason=""))
            else:
                excluded.append(_identity(row, eligible=False, reason=reason or "label_not_binary"))
    for row in unresolved:
        if row.get("partition") == "development":
            excluded.append(_identity(row, eligible=False, reason="unresolved_not_a_binary_label"))
    for row in skipped:
        if row.get("partition") == "development":
            excluded.append({"candidate_id": None, "related_group_id": row.get("related_group_id"),
                             "partition": "development", "benchmark": row.get("benchmark"),
                             "dataset_version": DATASET_VERSION, "label_class": None, "eligible": False,
                             "exclusion_reason": row.get("reason", "skipped_group"), "human_verified": False})

    def ids(rows, key):
        return {row.get(key) for row in rows if row.get(key)}

    history, development = labelled["history"], labelled["development"]
    overlap = {}
    for key in ("related_group_id", "candidate_id", "question_id", "content_identity"):
        overlap[key] = len(ids(history, key) & ids(development, key))
    overlap["normalized_question"] = len({norm_question(row["question"]) for row in history}
                                         & {norm_question(row["question"]) for row in development})
    overlap["paragraph_hash"] = len(set().union(*(context_hashes(row.get("evidence_context")) for row in history))
                                    & set().union(*(context_hashes(row.get("evidence_context")) for row in development)))
    facts = lambda rows: {f"{title}\0{sent}" for row in rows for title, sent in (row.get("supporting_facts") or [])}
    overlap["supporting_fact"] = len(facts(history) & facts(development))
    duplicate_candidates = len(development) - len(ids(development, "candidate_id"))
    duplicate_groups_across_roles = overlap["related_group_id"]
    by_benchmark = collections.defaultdict(collections.Counter)
    for row in eligible:
        by_benchmark[row["benchmark"]][row["label_class"]] += 1
    return {"manifest_source": manifest, "eligible": eligible, "excluded": excluded, "groups": group_rows,
            "overlap": overlap, "duplicate_development_candidate_ids": duplicate_candidates,
            "duplicate_groups_across_history_and_development": duplicate_groups_across_roles,
            "eligible_by_benchmark": {name: dict(counts) for name, counts in sorted(by_benchmark.items())},
            "development_labelled": len(development), "history_labelled": len(history),
            "development_unresolved": sum(row.get("partition") == "development" for row in unresolved),
            "human_verified_incorrect": 0}


def _manifest(result: dict, files: dict[str, bytes], source: Path) -> dict:
    source_manifest = source / "manifest.json"
    body = {
        "eligibility_version": VERSION,
        "status": "PROVISIONAL_NOT_APPROVED",
        "frozen": False,
        "approved": False,
        "approver": None,
        "approval_date": None,
        "collection_authorized": False,
        "recording_authorized": False,
        "dataset_version": DATASET_VERSION,
        "specification_id": None,
        "specification_status": "NOT_FROZEN",
        "source_manifest": str(source_manifest.relative_to(ROOT)).replace("\\", "/"),
        "source_manifest_sha256": sha256_file(source_manifest),
        "source_file_sha256": {name: sha256_file(source / name) for name in (
            "development_candidates.jsonl", "history_candidates.jsonl", "unresolved_candidates.jsonl",
            "skipped_groups.jsonl")},
        "eligibility_criteria": CRITERIA,
        "label_classes": {
            "VERIFIED_CORRECT": "benchmark gold under the recorded deterministic check; not a new human adjudication",
            "SYNTHETIC_INCORRECT": "deterministic transformation; not HUMAN_VERIFIED_INCORRECT",
            "HUMAN_VERIFIED_INCORRECT": "none in this snapshot",
            "UNRESOLVED": "excluded; never counted as incorrect",
        },
        "counts": {
            "development_labelled_candidates": result["development_labelled"],
            "provisionally_eligible_candidates": len(result["eligible"]),
            "excluded_rows": len(result["excluded"]),
            "provisionally_eligible_groups": sum(row["provisionally_eligible"] for row in result["groups"]),
            "development_groups": len(result["groups"]),
            "eligible_by_benchmark": result["eligible_by_benchmark"],
            "development_unresolved_excluded": result["development_unresolved"],
            "history_labelled_candidates_not_in_eligibility_roster": result["history_labelled"],
            "human_verified_incorrect": 0,
        },
        "duplicate_development_candidate_ids": result["duplicate_development_candidate_ids"],
        "history_development_overlap": result["overlap"],
        "semantic_or_paraphrase_leakage": "NOT AUDITED; exact identity checks are not semantic leakage clearance",
        "not_the_research_v1_roster": "evaluation/datasets/person1/research_v1_person1_v1/development_eligible_candidates.jsonl",
        "generator": "evaluation/data_preparation/exploratory_eligibility.py",
        "generator_code_revision": _git_revision(),
        "output_sha256": {name: sha256_bytes(data) for name, data in sorted(files.items())},
    }
    encoded = canonical_bytes(body)
    body["eligibility_manifest_sha256"] = sha256_bytes(encoded)
    return body


def generate(output: Path = OUTPUT, artifact: Path = ARTIFACT) -> dict:
    if output.exists() and any(output.iterdir()):
        raise FileExistsError("Refusing to overwrite an existing eligibility version")
    result = audit()
    files = {
        "development_provisionally_eligible.jsonl": jsonl_bytes(result["eligible"]),
        "development_excluded.jsonl": jsonl_bytes(result["excluded"]),
        "development_group_assignments.jsonl": jsonl_bytes(result["groups"]),
        "label_and_leakage_validation.json": canonical_bytes({
            "label_protocol": PROTOCOL,
            "human_verified_incorrect": 0,
            "synthetic_not_converted_to_human": True,
            "unresolved_excluded": True,
            "duplicate_development_candidate_ids": result["duplicate_development_candidate_ids"],
            "history_development_overlap": result["overlap"],
            "semantic_or_paraphrase_leakage": "NOT AUDITED",
            "eligible_by_benchmark": result["eligible_by_benchmark"],
        }),
    }
    manifest = _manifest(result, files, SOURCE)
    output.mkdir(parents=True, exist_ok=True)
    artifact.mkdir(parents=True, exist_ok=True)
    written = {**files, "eligibility_manifest.json": canonical_bytes(manifest)}
    for name, data in written.items():
        for directory in (output, artifact):
            with (directory / name).open("xb") as handle:
                handle.write(data)
    return manifest


def validate(output: Path = OUTPUT) -> dict:
    manifest = json.loads((output / "eligibility_manifest.json").read_text(encoding="utf-8"))
    if manifest.get("approved") is not False or manifest.get("frozen") is not False or manifest.get("collection_authorized") is not False:
        raise ValueError("provisional eligibility audit must stay unapproved, unfrozen, and unauthorized for collection")
    stored = manifest["output_sha256"]
    mismatches = sorted(name for name, digest in stored.items() if sha256_file(output / name) != digest)
    body = {key: value for key, value in manifest.items() if key != "eligibility_manifest_sha256"}
    recomputed = sha256_bytes(canonical_bytes(body))
    return {"status": manifest["status"], "approved": manifest["approved"], "frozen": manifest["frozen"],
            "collection_authorized": manifest["collection_authorized"],
            "eligibility_manifest_sha256": manifest["eligibility_manifest_sha256"],
            "manifest_hash_matches_body": recomputed == manifest["eligibility_manifest_sha256"],
            "stored_hash_mismatches": mismatches,
            "provisionally_eligible_candidates": manifest["counts"]["provisionally_eligible_candidates"],
            "provisionally_eligible_groups": manifest["counts"]["provisionally_eligible_groups"]}


def protocol_inventory() -> dict:
    """Hash proposal records. This does not approve them."""
    config = ROOT / "evaluation/config"
    proposals = sorted((config / "experiments").glob("experiment*_proposal.json"))
    files = [config / "research_settings_proposal_v1.json", *proposals]
    entries = {str(path.relative_to(ROOT)).replace("\\", "/"): sha256_file(path) for path in files}
    return {"record_type": "research_protocol_inventory_v1", "approved": False, "frozen": False,
            "collection_authorized": False, "file_sha256": entries}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("generate", "validate"))
    args = parser.parse_args(argv)
    result = generate() if args.command == "generate" else validate()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
