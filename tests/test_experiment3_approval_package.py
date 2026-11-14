"""Approval package and gate checks. Unsigned records stay unsigned."""

import json

import pytest

from evaluation.data_preparation.final_test_workflow import ROOT
from evaluation.experiments.experiment3.approval_inventory import validate_manifest
from evaluation.experiments.experiment3.collection_gate import collection_allowed
from evaluation.experiments.experiment3.prerequisite_validator import (
    BLOCKED, READY_FOR_APPROVAL, REPUTATION, SETTINGS_APPROVAL, assess,
)
from tests.test_experiment3_prerequisites import _copy_package, _write


def test_bound_manifest_matches_files_and_signs_nothing():
    current = validate_manifest(ROOT)
    assert current["approved"] is False
    assert current["collection_authorized"] is False
    assert current["approver"] is None
    statuses = {row["role"]: row["preparation_status"] for row in current["artifacts"]}
    assert statuses["protocol"] == "proposed"
    assert statuses["loss_settings"] == "proposed"
    assert statuses["reputation_configuration"] == "proposed"
    assert statuses["resource_configuration"] == "proposed"
    assert statuses["collection_authorization_template"] == "proposed"
    assert statuses["development_eligibility"] == "approved"
    assert statuses["cost_calibration_freeze"] == "approved"


def test_stale_manifest_hash_is_rejected(tmp_path):
    source = ROOT / "evaluation/experiments/experiment3/approval_package/manifest.json"
    payload = json.loads(source.read_text(encoding="utf-8"))
    payload["artifacts"][0]["sha256"] = "0" * 64
    copied = tmp_path / "manifest.json"
    copied.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="hash or status mismatch"):
        validate_manifest(ROOT, copied)


def test_manifest_cannot_authorize_itself(tmp_path):
    source = ROOT / "evaluation/experiments/experiment3/approval_package/manifest.json"
    payload = json.loads(source.read_text(encoding="utf-8"))
    payload["approved"] = True
    payload["approver"] = "Research Lead"
    copied = tmp_path / "manifest.json"
    copied.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="cannot sign"):
        validate_manifest(ROOT, copied)


def test_resource_and_reputation_proposals_are_incomplete():
    resource = json.loads((ROOT / "evaluation/experiments/experiment3/approval_package/resource_configuration_proposal.json").read_text(encoding="utf-8"))
    reputation = json.loads((ROOT / "evaluation/experiments/experiment3/approval_package/reputation_initialization_proposal.json").read_text(encoding="utf-8"))
    assert resource["approved"] is False
    assert resource["cost_unit"] == "ms"
    assert resource["resource_coefficient"] is None
    assert resource["verifier_budget_ms"] is None
    assert resource["approved_budget_candidates"] == []
    assert resource["coefficient_derived_from_approved_protocol"] is False
    assert reputation["approved"] is False
    assert reputation["observations_count"] == 0
    assert reputation["decay"] is None
    assert reputation["development_labels_permitted"] is False
    assert reputation["history_snapshots_permitted"] is False
    assert reputation["verifier_roster"] == ["semantic", "evidence", "rule", "confidence"]
    assert reputation["proposed_initialization"]["prior_alpha"] == 1.0
    assert reputation["proposed_initialization"]["prior_beta"] == 1.0


def test_live_gate_is_ready_for_approval_and_withholds_collection():
    report = assess(ROOT)
    assert report["status"] == READY_FOR_APPROVAL
    assert report["blockers"] == []
    assert "protocol settings are unsigned or incomplete" in report["withheld"]
    assert "resource coefficient and verifier budget are not signed" in report["withheld"]
    assert "collection is not authorized" in report["withheld"]
    assert "verifier model or rule hashes are incomplete" in report["withheld"]
    assert "collection seed is missing" in report["withheld"]
    assert "reputation initialization is not approved" in report["withheld"]
    assert "collection configuration does not bind a cost measurement" in report["withheld"]
    gate = collection_allowed(ROOT)
    assert gate["authorized_by_research_lead"] is True
    assert gate["independent_human_approval"] is False
    assert gate["contributor_signatures_obtained"] is False
    assert gate["collection_started"] is False
    assert gate["status"] in {"AUTHORIZED_BY_RESEARCH_LEAD", "TECHNICALLY_READY", "EMPIRICALLY_EXECUTED", "EMPIRICALLY_COMPLETED"}


def test_unsigned_or_stale_settings_are_rejected(tmp_path):
    _copy_package(tmp_path)
    record = json.loads((tmp_path / SETTINGS_APPROVAL).read_text(encoding="utf-8"))
    record["artifact_sha256"] = "0" * 64
    _write(tmp_path, SETTINGS_APPROVAL, record)
    assert assess(tmp_path)["status"] == BLOCKED
    _copy_package(tmp_path)
    record = json.loads((tmp_path / SETTINGS_APPROVAL).read_text(encoding="utf-8"))
    record["approved"] = True
    record["status"] = "APPROVED"
    record["decision"] = "APPROVED"
    _write(tmp_path, SETTINGS_APPROVAL, record)
    report = assess(tmp_path)
    assert report["status"] == BLOCKED
    assert "unsigned settings record was marked approved" in report["blockers"]


def test_reputation_inputs_cannot_approve_themselves(tmp_path):
    _copy_package(tmp_path)
    reputation = json.loads((tmp_path / REPUTATION).read_text(encoding="utf-8"))
    reputation["approved"] = True
    _write(tmp_path, REPUTATION, reputation)
    report = assess(tmp_path)
    assert report["status"] == BLOCKED
    assert "reputation inputs cannot approve themselves" in report["blockers"]
