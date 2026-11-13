"""Custody recovery inventories. They do not open Final Test labels."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RECOVERY = ROOT / "evaluation/artifacts/person1/historical_evidence_recovery_v1"
AUTH = ROOT / "evaluation/artifacts/person1/final_test_authorization_v1"


def test_twelve_files_are_verified_in_place_and_match_disk():
    inventory = json.loads((RECOVERY / "twelve_original_files_inventory.json").read_text(encoding="utf-8"))
    files = inventory["files"]
    assert len(files) == 12
    assert [row["ordinal"] for row in files] == list(range(1, 13))
    for row in files:
        path = ROOT / row["original_path"]
        assert row["status"] == "ORIGINAL_VERIFIED_IN_PLACE"
        assert path.is_file()
        import hashlib
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        assert digest == row["sha256"]


def test_authorization_package_is_not_an_approval_and_labels_stay_closed():
    readiness = json.loads((AUTH / "authorization_readiness.json").read_text(encoding="utf-8"))
    pending = json.loads((AUTH / "pending_authorization_record.json").read_text(encoding="utf-8"))
    inventory = json.loads((RECOVERY / "recovery_inventory.json").read_text(encoding="utf-8"))
    assert readiness["decision"] == "NOT_READY_FOR_AUTHORIZATION"
    assert readiness["approval_recorded"] is False
    assert readiness["labels_opened"] is False
    assert pending["approved"] is False and pending["approver"] is None
    assert pending["status"] == "NOT_AN_APPROVAL"
    assert inventory["final_test_labels_opened"] is False
    assert inventory["development_evidence_corpus_status"] == "PROPOSAL_NOT_APPROVED"
    blob = json.dumps(inventory) + json.dumps(readiness) + json.dumps(pending)
    assert "Raunak" not in blob


def test_execution_source_zip_is_not_claimed_recovered():
    inventory = json.loads((RECOVERY / "recovery_inventory.json").read_text(encoding="utf-8"))
    execution = next(row for row in inventory["artifacts"] if row["artifact"] == "execution_source_custody_zip")
    assert execution["status"] == "NOT_RECOVERABLE_FROM_AVAILABLE_EVIDENCE"
    matrix = json.loads((RECOVERY / "verifier_configuration_recovery.json").read_text(encoding="utf-8"))
    research = next(row for row in matrix["cohorts"] if row["cohort"] == "research_v1")
    assert research["fields"]["model_weight_snapshot_hash"]["status"] == "UNKNOWN"
