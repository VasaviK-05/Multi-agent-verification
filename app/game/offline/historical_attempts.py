"""Non-fitting references to historical verifier evidence.

These records preserve provenance and mapping decisions without pretending that
historical rows satisfy the canonical Attempt/Example fitting contract.
"""

from typing import Literal
import hashlib
import json

from pydantic import Field, model_validator

from app.game.dependencies import FrozenModel, identifier


def _content_id(value) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"),
                         ensure_ascii=False, allow_nan=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


_SHA256 = r"^[0-9a-f]{64}$"


class HistoricalAttemptReferenceV1(FrozenModel):
    """A provenance pointer to one source record; never a fitting Attempt."""

    version: Literal["historical_attempt_reference_v1"] = "historical_attempt_reference_v1"
    source_archive_sha256: str = Field(pattern=_SHA256)
    source_member: str
    source_record_sha256: str = Field(pattern=_SHA256)
    source_run_id: str
    source_candidate_id: str
    # Optional because some historical sources never assigned canonical attempt IDs.
    source_attempt_id: str | None = None
    source_dataset_id: str | None = None
    verifier_name: str
    mapping_status: Literal["exact_input_match", "nonmatch", "unresolved"]
    input_equivalence_sha256: str | None = Field(default=None, pattern=_SHA256)
    mapping_method: str | None = None
    mapped_example_id: str | None = None
    admission_status: Literal["conditional", "rejected"] = "conditional"
    admission_reason: str
    fitting_eligible: Literal[False] = False

    @model_validator(mode="after")
    def validate_provenance(self):
        for field in ("source_member", "source_run_id", "source_candidate_id",
                      "verifier_name", "admission_reason"):
            identifier(getattr(self, field))
        for field in ("source_attempt_id", "source_dataset_id", "mapping_method", "mapped_example_id"):
            value = getattr(self, field)
            if value is not None:
                identifier(value)
        if self.mapping_status == "exact_input_match":
            if self.input_equivalence_sha256 is None or self.mapping_method is None or self.mapped_example_id is None:
                raise ValueError("exact input matches require hash, mapping method, and mapped example ID")
        elif self.mapped_example_id is not None:
            raise ValueError("nonmatch/unresolved records cannot claim a mapped example")
        if self.admission_status == "rejected" and self.admission_reason == "conditional_pending_review":
            raise ValueError("rejected records require a rejection reason")
        return self

    @property
    def reference_id(self) -> str:
        """Content-addressed identity; does not fabricate a source attempt ID."""
        return _content_id(self.model_dump(mode="json"))


class HistoricalAttemptReferenceLedgerV1(FrozenModel):
    """Append-only sidecar ledger, intentionally not accepted by fitting APIs."""

    version: Literal["historical_attempt_reference_ledger_v1"] = "historical_attempt_reference_ledger_v1"
    references: tuple[HistoricalAttemptReferenceV1, ...] = ()

    @model_validator(mode="after")
    def validate_unique_sources(self):
        identities = [(row.source_archive_sha256, row.source_member, row.source_record_sha256)
                      for row in self.references]
        if len(identities) != len(set(identities)):
            raise ValueError("duplicate historical source record reference")
        ids = [row.reference_id for row in self.references]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate historical reference identity")
        return self

    def append(self, reference: HistoricalAttemptReferenceV1):
        """Return a new ledger; existing records are never mutated or replaced."""
        row = HistoricalAttemptReferenceV1.model_validate(reference)
        return HistoricalAttemptReferenceLedgerV1(references=(*self.references, row))

    @property
    def ledger_id(self) -> str:
        return _content_id(self.model_dump(mode="json"))
