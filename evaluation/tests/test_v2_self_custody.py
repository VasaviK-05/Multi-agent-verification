import json
from pathlib import Path

from evaluation.research_readiness.guards import assert_collection_authorized
from evaluation.research_readiness.v2_authorization import (
    LABEL_SHA256,
    MANIFEST_SHA256,
    ROSTER_SHA256,
    SEALED_LABEL,
    SELF_CUSTODY,
    CustodyAuthorizationError,
    assess_self_custody,
    refuse_sealed_label_without_release,
    release_blockers,
    scoring_decision,
    self_expected_binding,
    self_release_blockers,
    self_scoring_decision,
    validate_independent_appointment,
)


def _signed(**overrides):
    record = {
        "record_type": "self_custody_authorization_v1",
        "custody_mode": "SELF_CUSTODY",
        "independent_custody": False,
        "independent_custodian": False,
        "roles": ["dataset_creator", "researcher"],
        "approved": True,
        "status": "APPROVED",
        "signature": "research-lead-signature",
        "approver": "research-lead",
        "approval_date": "2026-11-13",
        "expires_on": "2099-01-01",
        "revoked": False,
        "dataset_version": "research_v1_final_test_v2_exploratory_v1",
        "manifest_sha256": MANIFEST_SHA256,
        "roster_sha256": ROSTER_SHA256,
        "label_sha256": LABEL_SHA256,
        "protocol_sha256": "a" * 64,
    }
    record.update(overrides)
    return record


def _protocol(**overrides):
    return _signed(record_type="self_custody_protocol_freeze_v1", **overrides)


def _release(**overrides):
    return _signed(record_type="self_custody_release_authorization_v1", label_release="AUTHORIZED", scoring_authorized=False, **overrides)


def _scoring(**overrides):
    return _signed(
        record_type="self_custody_scoring_authorization_v1",
        label_release="NOT_AUTHORIZED",
        scoring_authorized=True,
        scope="final_test_v2_self_custody_scoring",
        **overrides,
    )


def test_self_custody_never_reports_independent_custody():
    live = json.loads(SELF_CUSTODY.read_text(encoding="utf-8"))
    status = assess_self_custody(live)
    assert status["self_custody"] == "ACKNOWLEDGED"
    assert status["independent_custody"] == "NOT_ESTABLISHED"
    assert status["satisfies_independent_custody"] is False
    assert status["protocol_freeze"] == "PENDING"
    assert status["release"] == "AUTHORIZED"
    assert status["scoring"] == "AUTHORIZED"
    withheld = dict(live)
    withheld.pop("scoring_authorization")
    withheld_status = assess_self_custody(withheld)
    assert withheld_status["release"] == "AUTHORIZED"
    assert withheld_status["scoring"] == "NOT_AUTHORIZED"
    assert status["signed_evidence"] is False
    assert status["labels"] == "SEALED"
    assert status["final_test_execution"] == "NOT_RUN"
    decision = self_scoring_decision(_protocol(), _release(), _scoring(), self_expected_binding("a" * 64))
    assert decision["permitted"] is True
    assert decision["independent_custody"] == "NOT_ESTABLISHED"


def test_self_custody_cannot_satisfy_independent_authorization():
    live = json.loads(SELF_CUSTODY.read_text(encoding="utf-8"))
    assert "self_custody_cannot_satisfy_independent_authorization" in validate_independent_appointment(live)
    assert "self_custody_cannot_satisfy_independent_authorization" in release_blockers(_release(), self_expected_binding("a" * 64))
    decision = scoring_decision(_release(), _scoring(), self_expected_binding("a" * 64))
    assert decision["permitted"] is False
    assert "self_custody_cannot_satisfy_independent_authorization" in decision["reasons"]


def test_missing_protocol_freeze_blocks_release_and_freeze_does_not_score():
    expected = self_expected_binding("a" * 64)
    assert "protocol_not_frozen" in self_release_blockers(None, _release(), expected)
    frozen_only = self_scoring_decision(_protocol(), None, None, expected)
    assert frozen_only["permitted"] is False
    assert "missing_scoring_authorization" in frozen_only["reasons"]
    assert "release_not_authorized" in frozen_only["reasons"]


def test_release_does_not_imply_scoring():
    decision = self_scoring_decision(_protocol(), _release(), None, self_expected_binding("a" * 64))
    assert decision["permitted"] is False
    assert "missing_scoring_authorization" in decision["reasons"]


def test_hash_mismatches_block_self_custody_authorization():
    expected = self_expected_binding("a" * 64)
    assert "dataset_hash_mismatch" in self_release_blockers(_protocol(), _release(manifest_sha256="b" * 64), expected)
    assert "protocol_hash_mismatch" in self_release_blockers(_protocol(protocol_sha256="c" * 64), _release(), expected)


def test_development_evaluation_and_sealed_labels_stay_closed():
    assert_collection_authorized({"partition": "synthetic", "evidence_label": "SYNTHETIC"}, synthetic_fixture=True)
    refuse_sealed_label_without_release(Path("evaluation/datasets/unified/development.json"))
    try:
        refuse_sealed_label_without_release(SEALED_LABEL)
    except CustodyAuthorizationError:
        return
    raise AssertionError("sealed Final Test v2 labels were not refused")
