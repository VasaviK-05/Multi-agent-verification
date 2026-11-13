import json
from pathlib import Path

import pytest

from evaluation.data_preparation.final_test_custody import load_appointment
from evaluation.research_readiness.guards import assert_collection_authorized
from evaluation.research_readiness.v2_authorization import (
    LABEL_SHA256,
    MANIFEST_SHA256,
    ROSTER_SHA256,
    SEALED_LABEL,
    CustodyAuthorizationError,
    custody_state,
    dataset_creator_identity,
    expected_binding,
    refuse_sealed_label_without_release,
    refuse_v2_scoring,
    release_blockers,
    scoring_decision,
    validate_independent_appointment,
)
from evaluation.scripts import score_final_test_v2


def _binding(protocol="a" * 64, custodian="custodian-independent-1"):
    return expected_binding(custodian, protocol)


def _release(**overrides):
    record = {
        "approved": True, "status": "APPROVED", "signature": "external-signature",
        "approver": "research-lead", "approval_date": "2026-11-13", "expires_on": "2099-01-01",
        "revoked": False, "label_release": "AUTHORIZED", "scoring_authorized": False,
        "dataset_version": "research_v1_final_test_v2_exploratory_v1",
        "manifest_sha256": MANIFEST_SHA256, "label_sha256": LABEL_SHA256, "roster_sha256": ROSTER_SHA256,
        "protocol_sha256": "a" * 64, "custodian_id": "custodian-independent-1",
    }
    record.update(overrides)
    return record


def _scoring(**overrides):
    record = _release(label_release="NOT_AUTHORIZED", scoring_authorized=True, scope="final_test_v2_scoring", authorized_scorer="scorer-1")
    record.update(overrides)
    return record


def _appointment(**overrides):
    record = {
        "record_type": "independent_final_test_custodian_appointment_v1",
        "established": False,
        "independent_custodian_id": "custodian-independent-1",
        "roles": ["independent_custodian"],
        "identity_verification": "VERIFIED_EXTERNAL",
        "signature": "external-signature",
        "approval_date": "2026-11-13",
    }
    record.update(overrides)
    return record


def test_missing_custodian_appointment():
    assert custody_state(None, None, None, None, None) == "CUSTODY_NOT_ESTABLISHED"
    assert "missing_custodian_appointment" in validate_independent_appointment(None)


def test_creator_cannot_be_the_independent_custodian():
    reasons = validate_independent_appointment(_appointment(independent_custodian_id=dataset_creator_identity()))
    assert "creator_appointed_as_independent_custodian" in reasons


def test_conflicting_roles_are_rejected():
    reasons = validate_independent_appointment(_appointment(roles=["independent_custodian", "developer", "verifier_tuner"]))
    assert "conflicting_custodian_roles" in reasons
    preserved = load_appointment()
    assert preserved["independent_custodian"] is False


def test_missing_independent_verification_stays_pending():
    state = custody_state(_appointment(), {"independent_verification": "PENDING", "labels_parsed": False}, None, None, None)
    assert state == "CUSTODY_VERIFICATION_PENDING"


def test_hash_and_protocol_mismatches_fail_closed():
    expected = _binding()
    assert "manifest_hash_mismatch" in release_blockers(_release(manifest_sha256="b" * 64), expected)
    assert "label_hash_mismatch" in release_blockers(_release(label_sha256="c" * 64), expected)
    assert "roster_hash_mismatch" in release_blockers(_release(roster_sha256="d" * 64), expected)
    assert "protocol_hash_mismatch" in release_blockers(_release(protocol_sha256="e" * 64), expected)
    assert "protocol_not_frozen" in release_blockers(_release(), expected_binding("custodian-independent-1", None))


def test_unsigned_freeze_release_and_scoring_fail():
    unsigned = {"approved": False, "status": "NOT_AN_APPROVAL", "signature": None}
    assert "unsigned_or_template" in release_blockers(unsigned, _binding())
    assert scoring_decision(unsigned, unsigned, _binding())["permitted"] is False


def test_release_and_scoring_are_separate():
    expected = _binding()
    released_only = scoring_decision(_release(), None, expected)
    assert released_only["permitted"] is False and "unsigned_scoring_authorization" in released_only["reasons"]
    scored_only = scoring_decision(None, _scoring(), expected)
    assert scored_only["permitted"] is False and "unsigned_release_authorization" in scored_only["reasons"]


def test_authorization_bound_to_another_dataset_fails():
    assert "different_dataset" in release_blockers(_release(dataset_version="other"), _binding())


def test_sealed_label_access_and_scoring_entry_points_refuse():
    with pytest.raises(CustodyAuthorizationError):
        refuse_sealed_label_without_release(SEALED_LABEL)
    with pytest.raises(CustodyAuthorizationError):
        refuse_v2_scoring(None, None)
    assert score_final_test_v2.main() == 2


def test_valid_synthetic_authorization_path_does_not_open_labels():
    decision = scoring_decision(_release(), _scoring(), _binding())
    assert decision["permitted"] is True
    verification = {"independent_verification": "RECORDED", "labels_parsed": False}
    protocol = {"approved": True, "signature": "external-signature", "protocol_sha256": "a" * 64}
    assert custody_state(_appointment(), verification, protocol, _release(), _scoring()) == "SCORING_AUTHORIZED"


def test_development_collection_fixture_is_not_sent_to_the_v2_gate():
    assert_collection_authorized({"partition": "synthetic", "evidence_label": "SYNTHETIC"}, synthetic_fixture=True)
    refuse_sealed_label_without_release(Path("evaluation/datasets/unified/development.json"))


def test_errors_do_not_include_label_contents_and_expired_or_revoked_fail():
    with pytest.raises(CustodyAuthorizationError) as caught:
        refuse_v2_scoring(None, None)
    assert "candidate" not in str(caught.value).lower()
    assert "label_sha256" not in str(caught.value)
    assert "expired" in release_blockers(_release(expires_on="2000-01-01"), _binding())
    assert "revoked" in release_blockers(_release(revoked=True), _binding())


def test_live_records_do_not_establish_custody_or_authorize_scoring():
    root = Path(__file__).resolve().parents[1]
    appointment = json.loads((root / "config/research_v1/independent_custodian_appointment.json").read_text(encoding="utf-8"))
    verification = json.loads((root / "config/research_v1/independent_custody_verification.json").read_text(encoding="utf-8"))
    assert appointment["established"] is False
    assert verification["independent_verification"] == "PENDING"
    assert verification["labels_parsed"] is False
    assert custody_state(appointment, verification, None, None, None) == "CUSTODY_VERIFICATION_PENDING"


def test_self_declared_establishment_is_rejected():
    reasons = validate_independent_appointment(_appointment(established=True))
    assert "self_declared_establishment_is_not_evidence" in reasons


def test_scoring_entry_point_calls_the_central_guard():
    from evaluation.data_preparation import final_test_workflow
    source = Path(score_final_test_v2.__file__).read_text(encoding="utf-8")
    reader = Path(final_test_workflow.__file__).read_text(encoding="utf-8")
    assert "refuse_v2_scoring" in source
    assert "refuse_sealed_label_without_release" in reader
