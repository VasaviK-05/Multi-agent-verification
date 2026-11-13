"""Approved exploratory eligibility manifest. Eligibility approval is not protocol freeze."""

import json
from pathlib import Path

import pytest

from evaluation.data_preparation.exploratory_eligibility import OUTPUT as PROVISIONAL_OUTPUT
from evaluation.data_preparation.exploratory_eligibility import validate as validate_provisional
from evaluation.data_preparation.exploratory_eligibility_approved import (
    OUTPUT, VERSION, _forbid, build, generate, validate, _manifest, _package,
)
from evaluation.data_preparation.final_test_workflow import sha256_bytes, sha256_file

ROOT = Path(__file__).resolve().parents[1]
FINAL_TEST_LABELS = ROOT / "evaluation/datasets/_custodian/final_test_research_v1_v2/labels.jsonl"
BODY_SHA256 = "f2cc0fd108b961bf4795767df4f90e92d7fa0f418ef9865d0206f32d7b45282d"


def _rows(name: str) -> list[dict]:
    return [json.loads(line) for line in (OUTPUT / name).read_text(encoding="utf-8").splitlines()]


def test_approved_manifest_schema_hashes_and_does_not_authorize_collection():
    report = validate(OUTPUT)
    assert report["manifest_id"] == VERSION
    assert report["approval"]["status"] == "APPROVED_BY_RESEARCH_LEAD"
    assert report["approval"]["approver"] == "Research Lead"
    assert report["approval"]["approval_date"] == "2026-11-13"
    assert report["eligibility_manifest_sha256"] == BODY_SHA256
    assert report["manifest_hash_matches_body"] is True
    assert report["manifest_file_hash_matches"] is True
    assert report["stored_hash_mismatches"] == []
    assert report["semantic_clearance"] == "NOT_CLAIMED"
    assert report["semantic_findings"] == 0
    manifest = json.loads((OUTPUT / "eligibility_manifest.json").read_text(encoding="utf-8"))
    assert manifest["collection_authorized"] is False
    assert manifest["frozen_protocol"] is False
    assert manifest["final_test_authorized"] is False
    assert manifest["recording_authorized"] is False
    assert "final_test" not in manifest["dataset_version"]
    assert set(manifest["output_sha256"]) == {
        "development_eligible.jsonl", "development_excluded.jsonl", "group_assignments.jsonl",
        "label_validation.jsonl", "leakage_audit.json",
    }


def test_roster_groups_exclusions_and_label_provenance_are_consistent():
    eligible = _rows("development_eligible.jsonl")
    excluded = _rows("development_excluded.jsonl")
    groups = _rows("group_assignments.jsonl")
    labels = _rows("label_validation.jsonl")
    assert len(eligible) == 744
    assert len({row["question_id"] for row in eligible}) == 372
    assert len({row["related_group_id"] for row in eligible}) == 372
    by_group: dict[str, list[dict]] = {}
    for row in eligible:
        by_group.setdefault(row["related_group_id"], []).append(row)
    for members in by_group.values():
        assert {row["label_class"] for row in members} == {"VERIFIED_CORRECT", "SYNTHETIC_INCORRECT"}
        assert len({row["question_id"] for row in members}) == 1
        assert all(row["human_verified"] is False and row["eligible"] is True for row in members)
        assert all("candidate_answer" not in row for row in members)
    assert not any(row["label_class"] == "HUMAN_VERIFIED_INCORRECT" for row in eligible + excluded)
    eligible_ids = {row["candidate_id"] for row in eligible}
    excluded_ids = {row["candidate_id"] for row in excluded if row.get("candidate_id")}
    assert eligible_ids.isdisjoint(excluded_ids)
    reasons = {row["exclusion_reason"] for row in excluded}
    assert reasons == {"shared_history_reference_context", "unresolved_not_a_binary_label", "no_verified_gold"}
    assert all(row.get("exclusion_reasons") for row in excluded)
    unresolved = [row for row in excluded if row["exclusion_reason"] == "unresolved_not_a_binary_label"]
    assert len(unresolved) == 332
    assert all(row["label_class"] == "UNRESOLVED" for row in unresolved)
    assignments = {row["related_group_id"]: row for row in groups}
    assert len(assignments) == len(groups) == 387
    assert sum(row["eligible"] for row in groups) == 372
    for row in eligible:
        assert assignments[row["related_group_id"]]["eligible"] is True
    quarantined = {row["related_group_id"] for row in groups if row["exclusion_reasons"] == ["shared_history_reference_context"]}
    assert len(quarantined) == 15
    assert quarantined.isdisjoint({row["related_group_id"] for row in eligible})
    passed = [row for row in labels if row["validation_status"] == "passed"]
    unresolved_labels = [row for row in labels if row["validation_status"] == "unresolved"]
    assert len(passed) == 774 and len(unresolved_labels) == 332
    assert {row["label_class"] for row in unresolved_labels} == {"UNRESOLVED"}
    assert all(row["eligible"] is False for row in unresolved_labels)
    synthetic = [row for row in passed if row["label_class"] == "SYNTHETIC_INCORRECT"]
    assert len(synthetic) == 387
    assert all(row["validation_method"] == "synthetic_negative_role_v1" and row["human_verified"] is False for row in synthetic)


def test_leakage_audit_records_overlap_without_claiming_semantic_clearance():
    audit = json.loads((OUTPUT / "leakage_audit.json").read_text(encoding="utf-8"))
    assert audit["exact_overlap"] == {
        "candidate_id": 0, "content_identity": 0, "normalized_question": 0,
        "question_id": 0, "related_group_id": 0, "source_dataset_id": 0,
    }
    assert audit["paragraph_hash_overlap_count"] == 50
    assert len(audit["paragraph_records"]) == 50
    assert all(record["same_question_id"] is False for record in audit["paragraph_records"])
    assert all(record["eligibility_decision"] == "quarantine_development_groups" for record in audit["paragraph_records"])
    assert audit["supporting_fact_overlap_count"] == 2
    assert len(audit["supporting_fact_records"]) == 2
    assert {record["supporting_fact"]["title"] for record in audit["supporting_fact_records"]} == {"Magic Dirt", "Tom Clancy"}
    assert audit["semantic_findings_at_or_above_threshold"] == []
    assert audit["semantic_clearance"] == "NOT_CLAIMED"
    assert audit["semantic_thresholds"] == {"token_jaccard": 0.80, "sequence_ratio": 0.85}
    assert audit["maximum_sequence_ratio"] < 0.85
    assert audit["manually_reviewed_pairs_at_or_above_0_65"]
    assert all(row["adjudication"] == "not_a_paraphrase_different_named_entities" for row in audit["manually_reviewed_pairs_at_or_above_0_65"])
    quarantined = set(audit["quarantined_development_groups"])
    eligible_groups = {row["related_group_id"] for row in _rows("development_eligible.jsonl")}
    assert quarantined.isdisjoint(eligible_groups)
    assert len(quarantined) == 15


def test_experiment_proposals_cite_the_approved_manifest_and_stay_unrunnable():
    for name in ("experiment1_proposal.json", "experiment2_proposal.json", "experiment3_proposal.json", "experiment4_proposal.json"):
        proposal = json.loads((ROOT / "evaluation/config/experiments" / name).read_text(encoding="utf-8"))
        assert proposal["eligibility_manifest"] == VERSION
        assert proposal["eligibility_manifest_sha256"] == BODY_SHA256
        assert proposal["dataset_version_for_development"] == "research_v1_exploratory_v1"
        assert proposal["approved"] is False and proposal["frozen"] is False
        assert proposal["specification_id"] is None and proposal["collection_authorized"] is False
        assert proposal["runnable"] is False
        assert "final_test" in proposal["prohibited_partitions"]
        assert "research_v1_final_test_v2_exploratory_v1" in proposal["final_test_dataset"]
    experiment2 = json.loads((ROOT / "evaluation/config/experiments/experiment2_proposal.json").read_text(encoding="utf-8"))
    assert experiment2["budget_values"] is None and experiment2["resource_coefficient"] is None


def test_provisional_manifest_is_preserved_and_generate_refuses_overwrite():
    report = validate_provisional(PROVISIONAL_OUTPUT)
    assert report["approved"] is False
    assert report["eligibility_manifest_sha256"] == "9f220e4d9affa2e10d088cd6afcd2587b318912a4b4f0568d5617e3976693ac4"
    with pytest.raises(FileExistsError):
        generate(OUTPUT)


def test_final_test_paths_are_refused():
    with pytest.raises(RuntimeError):
        _forbid(FINAL_TEST_LABELS)


def test_rebuild_matches_the_written_files_and_does_not_open_sealed_labels(monkeypatch):
    opened = []
    real_open = Path.open

    def guard(self, *args, **kwargs):
        opened.append(self)
        if "labels.jsonl" in self.name and "_custodian" in str(self).replace("\\", "/"):
            raise AssertionError("Final Test v2 labels were opened")
        text = str(self).replace("\\", "/")
        if text.endswith("research_v1_person1_v1/development_eligible_candidates.jsonl"):
            raise AssertionError("research_v1 eligibility roster was reused")
        return real_open(self, *args, **kwargs)

    monkeypatch.setattr(Path, "open", guard)
    result = build()
    files = _package(result)
    manifest = _manifest(result, files)
    assert manifest["eligibility_manifest_sha256"] == BODY_SHA256
    for name, data in files.items():
        assert sha256_bytes(data) == sha256_file(OUTPUT / name)
    assert opened
