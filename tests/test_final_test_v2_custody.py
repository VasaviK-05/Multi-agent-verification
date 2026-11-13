"""Custody appointment is not evaluation authorization. No Final Test label payload is opened."""

import hashlib
import json

import pytest

from evaluation.data_preparation import final_test_custody as custody
from evaluation.data_preparation import final_test_workflow as ft

FROZEN_LABEL = "35b126ba350a942f42f11d1845e16e01fd755516d20b53faf3aaf616143858a6"
FROZEN_ROSTER = "3f8fcbf1e698174a9a7cf6c586ec51048bcc07ca11154b36fdef0dadc7796208"
FROZEN_EXAMPLES = "a33be6afcd2233479a05ee9c9444d1457d5b98d07c0c10e5bbef5191fab4d496"
V2 = ft.ROOT / "evaluation/datasets/final_test_research_v1_eval_v2"
LABELS = ft.ROOT / "evaluation/datasets/_custodian/final_test_research_v1_v2/labels.jsonl"


def test_appointment_names_the_dataset_creator_without_independent_custody():
    record = custody.load_appointment()
    assert record["appointee"] == "Raunak"
    assert record["roles"] == ["dataset_creator", "designated_final_test_custodian"]
    assert record["custody_status"] == custody.CUSTODY_STATUS
    assert record["previous_custody_status"] == "PENDING_NO_INDEPENDENT_CUSTODIAN"
    assert record["independent_custodian"] is False
    assert record["custody_independence"] == "NOT_INDEPENDENT"
    assert record["operating_system_protection"] is False
    assert record["responsibilities"] == list(custody.RESPONSIBILITIES)
    assert record["evaluation_authorized"] is False
    assert record["evaluation_authorization"] == "PENDING"
    assert record["label_release"] == "NOT_AUTHORIZED"
    assert record["protocol_freeze"] == "PENDING"


def test_appointment_cannot_claim_independent_custody_or_authorization(tmp_path):
    record = custody.load_appointment()
    path = tmp_path / "appointment.json"
    path.write_text(json.dumps({**record, "independent_custodian": True}), encoding="utf-8")
    with pytest.raises(ValueError, match="independent custody"):
        custody.load_appointment(path)
    path.write_text(json.dumps({**record, "evaluation_authorization": "AUTHORIZED", "evaluation_authorized": True}),
                    encoding="utf-8")
    with pytest.raises(ValueError, match="authorization pending"):
        custody.load_appointment(path)


def test_denied_roles_and_activities_never_receive_labels_even_after_approval():
    approved = {"approved": True, "protocol_frozen": True, "person": "Raunak", "purpose": "confirmatory evaluation"}
    for role in ("verifier_developer", "development_experiment_runner"):
        decision = custody.label_access_decision(role=role, purpose="confirmatory evaluation",
                                                 authorization=approved, protocol_frozen=True)
        assert decision == {"permitted": False, "reason": "role_denied", "role": role}
    for purpose in ("development experiment", "verifier development", "reputation fitting", "policy selection",
                    "training", "threshold tuning"):
        decision = custody.label_access_decision(role="designated_final_test_custodian", purpose=purpose,
                                                 authorization=approved, protocol_frozen=True)
        assert decision["permitted"] is False and decision["reason"] == "activity_denied"
    held = custody.label_access_decision(role="designated_final_test_custodian", purpose="confirmatory evaluation",
                                         authorization=approved, protocol_frozen=False)
    assert held == {"permitted": False, "reason": "protocol_not_frozen"}
    pending = custody.label_access_decision(role="designated_final_test_custodian", purpose="confirmatory evaluation",
                                            authorization=custody.load_appointment(), protocol_frozen=True)
    assert pending["reason"] == "custodian_appointment_is_not_evaluation_authorization"


def test_label_reader_refuses_denied_roles_without_opening_a_label_file(tmp_path):
    missing = tmp_path / "labels.jsonl"
    auth = tmp_path / "auth.json"
    for role, purpose in (("verifier_developer", "confirmatory evaluation"),
                          ("development_experiment_runner", "confirmatory evaluation"),
                          ("designated_final_test_custodian", "development experiment")):
        with pytest.raises(PermissionError, match="withheld"):
            ft.read_custodian_labels(missing, auth, tmp_path / "log.jsonl", person="Raunak", purpose=purpose,
                                     expected_manifest_sha256="a" * 64, role=role)
    assert not missing.exists() and not auth.exists()


def test_appointment_does_not_authorize_evaluation():
    manifest = {"partition": "final_test", "status": "NOT_AUTHORIZED", "enabled": False,
                "custody_status": custody.CUSTODY_STATUS, "evaluation_authorization": "PENDING",
                "label_counts": {"GSM8K": {"VERIFIED_CORRECT": 1, "SYNTHETIC_INCORRECT": 1}},
                "exposure_audit": {"method": ft.EXPOSURE_METHOD, "passed": True}}
    manifest["manifest_sha256"] = ft.sha256_bytes(ft.canonical_bytes(manifest))
    appointment = custody.load_appointment()
    status, reasons = ft.final_test_gate(manifest, appointment, {})
    assert status == "NOT APPROVED"
    assert "evaluation_authorization_pending" in reasons
    assert "custodian_appointment_is_not_evaluation_authorization" in reasons
    auth = {"approved": True, "protocol_frozen": True, "manifest_sha256": manifest["manifest_sha256"],
            "approver": "Protocol owner", "custodian": "Raunak"}
    assert ft.final_test_gate(manifest, auth, {})[0] == "NOT APPROVED"
    released = {k: v for k, v in manifest.items() if k not in {"evaluation_authorization", "manifest_sha256"}}
    released["manifest_sha256"] = ft.sha256_bytes(ft.canonical_bytes(released))
    auth["manifest_sha256"] = released["manifest_sha256"]
    assert ft.final_test_gate(released, auth, {}) == ("APPROVED", [])
    assert ft.final_test_gate(released, {**auth, "protocol_frozen": False}, {}) == ("NOT APPROVED", ["protocol_not_frozen"])


@pytest.mark.skipif(not (V2 / "manifest.json").exists(), reason="Final Test v2 absent")
def test_v2_custody_update_preserves_dataset_hashes_and_withholds_evaluation():
    manifest = json.loads((V2 / "manifest.json").read_text(encoding="utf-8"))
    reservation = json.loads((V2 / "final_test_reservation.json").read_text(encoding="utf-8"))
    examples = hashlib.sha256(json.dumps(reservation["examples"], ensure_ascii=False, sort_keys=True,
                                         separators=(",", ":")).encode()).hexdigest()
    assert examples == FROZEN_EXAMPLES
    assert ft.sha256_file(LABELS) == FROZEN_LABEL == manifest["label_file_sha256"]
    assert ft.sha256_file(V2 / "evaluation_roster.jsonl") == FROZEN_ROSTER == manifest["evaluation_roster_sha256"]
    assert reservation["custody_record"] == "DESIGNATED_CUSTODIAN_IS_DATASET_CREATOR:Raunak"
    assert manifest["status"] == "NOT_AUTHORIZED" and manifest["enabled"] is False
    assert manifest["custody_status"] == custody.CUSTODY_STATUS
    assert manifest["evaluation_authorization"] == "PENDING"
    assert manifest["custodian_appointment_sha256"] == ft.sha256_file(custody.APPOINTMENT_PATH)
    readiness = ft.validate_readiness(ft.ROOT / "evaluation/config/protocol_readiness.yaml", V2 / "manifest.json")
    assert readiness["checks"]["final_test_partition_and_custody"] == "NOT APPROVED"
    assert readiness["confirmatory_readiness"] == "BLOCKED"
    assert readiness["final_test_custody_status"] == custody.CUSTODY_STATUS
    assert readiness["final_test_evaluation_authorization"] == "PENDING"
    assert "evaluation_authorization_pending" in readiness["final_test_gate_reasons"]
