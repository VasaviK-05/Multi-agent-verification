"""Provisional exploratory eligibility audit. Not an approval or a collection authorization."""

import json
from pathlib import Path

import pytest

from evaluation.data_preparation.exploratory_eligibility import (
    ARTIFACT, OUTPUT, VERSION, audit, protocol_inventory, validate,
)

ROOT = Path(__file__).resolve().parents[1]
FINAL_TEST_LABELS = ROOT / "evaluation/datasets/_custodian/final_test_research_v1_v2/labels.jsonl"


def test_provisional_audit_matches_the_snapshot_and_stays_unapproved():
    report = validate(OUTPUT)
    assert report["status"] == "PROVISIONAL_NOT_APPROVED"
    assert report["approved"] is False and report["frozen"] is False
    assert report["collection_authorized"] is False
    assert report["manifest_hash_matches_body"] is True
    assert report["stored_hash_mismatches"] == []
    assert report["provisionally_eligible_candidates"] == 774
    assert report["provisionally_eligible_groups"] == 387
    assert report["eligibility_manifest_sha256"] == "9f220e4d9affa2e10d088cd6afcd2587b318912a4b4f0568d5617e3976693ac4"
    mirrored = json.loads((ARTIFACT / "eligibility_manifest.json").read_text(encoding="utf-8"))
    assert mirrored["eligibility_manifest_sha256"] == report["eligibility_manifest_sha256"]
    assert mirrored["eligibility_version"] == VERSION


def test_eligible_rows_exclude_unresolved_and_do_not_carry_answers():
    rows = [json.loads(line) for line in (OUTPUT / "development_provisionally_eligible.jsonl").read_text(encoding="utf-8").splitlines()]
    assert len(rows) == 774
    assert {row["label_class"] for row in rows} == {"VERIFIED_CORRECT", "SYNTHETIC_INCORRECT"}
    assert all(row["human_verified"] is False and row["eligible"] is True for row in rows)
    assert all("candidate_answer" not in row and "question" not in row and "gold_answer" not in row for row in rows)
    excluded = [json.loads(line) for line in (OUTPUT / "development_excluded.jsonl").read_text(encoding="utf-8").splitlines()]
    reasons = {row["exclusion_reason"] for row in excluded}
    assert "unresolved_not_a_binary_label" in reasons
    assert sum(row["exclusion_reason"] == "unresolved_not_a_binary_label" for row in excluded) == 332
    assert not any(row["label_class"] == "HUMAN_VERIFIED_INCORRECT" for row in rows + excluded)


def test_audit_does_not_use_the_research_v1_roster_or_final_test_labels(monkeypatch):
    opened = []
    real_open = Path.open

    def guard(self, *args, **kwargs):
        opened.append(self)
        if self.resolve() == FINAL_TEST_LABELS.resolve():
            raise AssertionError("Final Test v2 labels were opened")
        text = str(self).replace("\\", "/")
        if text.endswith("research_v1_person1_v1/development_eligible_candidates.jsonl"):
            raise AssertionError("research_v1 eligibility roster was reused")
        return real_open(self, *args, **kwargs)

    monkeypatch.setattr(Path, "open", guard)
    result = audit()
    assert result["development_labelled"] == 774
    assert result["overlap"]["related_group_id"] == 0
    assert result["overlap"]["paragraph_hash"] == 50
    assert result["human_verified_incorrect"] == 0


def test_settings_and_experiment_proposals_are_not_approved():
    settings = json.loads((ROOT / "evaluation/config/research_settings_proposal_v1.json").read_text(encoding="utf-8"))
    assert settings["approved"] is False and settings["approver"] is None
    assert all(row["approver"] is None and row["approval_date"] is None for row in settings["settings"])
    assert all(row["status"] in {"PROPOSED", "PENDING"} for row in settings["settings"])
    budgets = next(row for row in settings["settings"] if row["parameter"] == "budget_levels")
    assert budgets["proposed_value"] is None
    for name in ("experiment1_proposal.json", "experiment2_proposal.json", "experiment3_proposal.json", "experiment4_proposal.json"):
        proposal = json.loads((ROOT / "evaluation/config/experiments" / name).read_text(encoding="utf-8"))
        assert proposal["approved"] is False and proposal["frozen"] is False
        assert proposal["specification_id"] is None and proposal["collection_authorized"] is False
        assert "final_test" in proposal["prohibited_partitions"]


def test_protocol_inventory_hashes_the_proposal_files():
    inventory = protocol_inventory()
    assert inventory["approved"] is False
    for relative, digest in inventory["file_sha256"].items():
        assert len(digest) == 64
        assert (ROOT / relative).is_file()
