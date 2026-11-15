"""Historical references remain separate from fitting/evaluation records."""

import pytest
from pydantic import ValidationError

from app.game.offline.historical_attempts import (
    HistoricalAttemptReferenceLedgerV1,
    HistoricalAttemptReferenceV1,
)


HASH_A = "a" * 64
HASH_B = "b" * 64
HASH_C = "c" * 64


def row(**updates):
    data = dict(
        source_archive_sha256=HASH_A,
        source_member="recordings/record-001.json",
        source_record_sha256=HASH_B,
        source_run_id="research-v1-rehearsal",
        source_candidate_id="candidate-001",
        verifier_name="semantic",
        mapping_status="exact_input_match",
        input_equivalence_sha256=HASH_C,
        mapping_method="repository_permitted_input_canonical_json_v1",
        mapped_example_id="approved-example-001",
        admission_status="conditional",
        admission_reason="conditional_pending_review",
    )
    data.update(updates)
    return HistoricalAttemptReferenceV1(**data)


def test_exact_match_is_still_non_fitting_and_content_addressed():
    reference = row()
    assert reference.fitting_eligible is False
    assert len(reference.reference_id) == 64
    assert reference.source_attempt_id is None


def test_exact_match_requires_mapping_evidence():
    with pytest.raises(ValidationError):
        row(mapping_method=None)


def test_nonmatch_cannot_claim_a_mapped_example():
    with pytest.raises(ValidationError):
        row(mapping_status="nonmatch")


def test_unknown_attempt_id_is_not_fabricated():
    reference = row(source_attempt_id=None)
    assert reference.source_attempt_id is None


def test_ledger_append_is_immutable_and_rejects_duplicate_source_record():
    first = row()
    ledger = HistoricalAttemptReferenceLedgerV1().append(first)
    assert len(ledger.references) == 1
    assert len(HistoricalAttemptReferenceLedgerV1().references) == 0
    with pytest.raises(ValidationError, match="duplicate historical source"):
        ledger.append(first)


def test_rejected_record_requires_real_rejection_reason():
    with pytest.raises(ValidationError):
        row(admission_status="rejected", admission_reason="conditional_pending_review")
    assert row(admission_status="rejected", admission_reason="source_record_hash_mismatch")



def test_reference_has_no_implicit_conversion_helpers():
    reference = row()
    ledger = HistoricalAttemptReferenceLedgerV1().append(reference)
    assert not hasattr(reference, "to_attempt")
    assert not hasattr(reference, "to_example")
    assert not hasattr(ledger, "to_training_manifest")


def test_fitting_eligibility_cannot_be_enabled():
    with pytest.raises(ValidationError):
        row(fitting_eligible=True)


def test_historical_contract_is_not_wired_into_application_modules():
    from pathlib import Path

    repository_root = Path(__file__).resolve().parents[1]
    protected_modules = (
        "app/game/offline/__init__.py",
        "app/game/offline/records.py",
        "app/game/offline/collection.py",
        "app/game/offline/evaluation.py",
    )
    for relative_path in protected_modules:
        source = (repository_root / relative_path).read_text(encoding="utf-8")
        assert "historical_attempts" not in source, relative_path
        assert "HistoricalAttemptReference" not in source, relative_path
