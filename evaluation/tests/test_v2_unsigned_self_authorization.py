import json
from pathlib import Path

import pytest

from evaluation.research_readiness.v2_authorization import (
    MANIFEST_SHA256,
    ROSTER_SHA256,
    SEALED_LABEL,
    SELF_CUSTODY,
    CustodyAuthorizationError,
    assess_self_custody,
    refuse_sealed_label_without_release,
    release_blockers,
    self_expected_binding,
    unsigned_release_decision,
    unsigned_scoring_decision,
)
from evaluation.scripts import score_final_test_v2


def _declaration():
    return json.loads(SELF_CUSTODY.read_text(encoding="utf-8"))


def _metadata(**overrides):
    metadata = {
        "dataset_version": "research_v1_final_test_v2_exploratory_v1",
        "partition": "final_test",
        "manifest_sha256": MANIFEST_SHA256,
        "group_count": 600,
        "candidate_count": 1200,
        "status": "NOT_AUTHORIZED",
        "enabled": False,
    }
    metadata.update(overrides)
    return metadata


def _ack(**overrides):
    record = {
        "record_type": "researcher_self_authorization_v1",
        "custody_mode": "SELF_CUSTODY",
        "independent_custody": False,
        "independent_custodian": False,
        "independent_verification": False,
        "evidence_form": "UNSIGNED_VERBAL_ACKNOWLEDGMENT",
        "signed_evidence": False,
        "signature": None,
        "self_custody_limitations_acknowledged": True,
        "action": "PROTOCOL_APPROVAL",
        "release_confirmed": False,
        "scoring_confirmed": False,
        "dataset_version": "research_v1_final_test_v2_exploratory_v1",
        "manifest_sha256": MANIFEST_SHA256,
        "roster_sha256": ROSTER_SHA256,
        "revoked": False,
    }
    record.update(overrides)
    return record


def _release(**overrides):
    return _ack(action="RELEASE", release_confirmed=True, scoring_confirmed=False, **overrides)


def _scoring(**overrides):
    return _ack(action="SCORING", scoring_confirmed=True, release_confirmed=False, **overrides)


def test_unsigned_self_authorization_does_not_claim_a_signature_or_independence():
    decision = unsigned_release_decision(_declaration(), _release(), _metadata())
    assert decision["permitted"] is True
    assert decision["signed_evidence"] is False
    assert decision["independent_custody"] == "NOT_ESTABLISHED"
    assert decision["independent_verification"] is False
    assert decision["labels_opened"] is False
    assert decision["experiment_executed"] is False
    claimed = unsigned_release_decision(_declaration(), _release(signature="not-a-real-signature", signed_evidence=True), _metadata())
    assert claimed["permitted"] is False
    assert claimed["signed_evidence"] is False
    assert "signed_evidence_not_accepted_on_unsigned_path" in claimed["reasons"]


def test_protocol_approval_does_not_release_and_release_does_not_score():
    protocol_only = unsigned_release_decision(_declaration(), _ack(), _metadata())
    assert protocol_only["permitted"] is False
    assert "protocol_approval_does_not_authorize_release" in protocol_only["reasons"]
    released = unsigned_scoring_decision(_declaration(), _release(), _release(), _metadata())
    assert released["permitted"] is False
    assert "release_does_not_authorize_scoring" in released["reasons"]
    scored = unsigned_scoring_decision(_declaration(), _release(), _scoring(), _metadata())
    assert scored["permitted"] is True
    assert scored["signed_evidence"] is False
    assert scored["experiment_executed"] is False


def test_limitations_dataset_integrity_and_live_state_block_unconfirmed_actions():
    missing_ack = unsigned_release_decision(_declaration(), _release(self_custody_limitations_acknowledged=False), _metadata())
    assert "self_custody_limitations_not_acknowledged" in missing_ack["reasons"]
    substituted = unsigned_release_decision(_declaration(), _release(), _metadata(partition="development", dataset_version="research_v1_development"))
    assert "development_or_history_substituted" in substituted["reasons"]
    mismatched = unsigned_release_decision(_declaration(), _release(manifest_sha256="b" * 64), _metadata())
    assert "dataset_hash_mismatch" in mismatched["reasons"]
    status = assess_self_custody(_declaration(), metadata=_metadata())
    assert status["self_custody"] == "ACKNOWLEDGED"
    assert status["protocol_approval"] == "VERBAL_TEAM_APPROVAL_STATED"
    assert status["signed_evidence"] is False
    assert status["protocol_freeze"] == "PENDING"
    assert status["release"] == "AUTHORIZED"
    assert status["scoring"] == "AUTHORIZED"
    assert status["labels"] == "SEALED"
    assert status["independent_custody"] == "NOT_ESTABLISHED"
    assert status["final_test_execution"] == "NOT_RUN"
    mismatched = assess_self_custody(_declaration(), metadata=_metadata(manifest_sha256="b" * 64))
    assert mismatched["release"] == "NOT_AUTHORIZED"
    assert mismatched["scoring"] == "NOT_AUTHORIZED"
    live = _declaration()
    assert live["roster_sha256"] == ROSTER_SHA256
    assert live["scoring_confirmed"] is False
    assert live["scoring_authorization"]["action"] == "SCORING"
    assert live["scoring_authorization"]["release_confirmed"] is False
    assert live["scoring_authorization"]["signed_evidence"] is False
    assert live["scoring_authorization"]["signature"] is None
    assert live["labels_opened"] is False
    assert live["final_test_executed"] is False
    claimed = unsigned_scoring_decision(live, _release(), _scoring(signature="not-a-real-signature", signed_evidence=True), _metadata())
    assert claimed["permitted"] is False
    assert claimed["signed_evidence"] is False


def test_existing_label_protection_and_independent_gate_remain():
    with pytest.raises(CustodyAuthorizationError):
        refuse_sealed_label_without_release(SEALED_LABEL)
    refuse_sealed_label_without_release(Path("evaluation/datasets/unified/development.json"))
    assert "self_custody_cannot_satisfy_independent_authorization" in release_blockers(_release(), self_expected_binding("a" * 64))
    assert score_final_test_v2.main() == 2
    refused = unsigned_scoring_decision(_declaration(), None, None, _metadata())
    assert refused["permitted"] is False
    assert "scoring_not_confirmed" in refused["reasons"]
