# Historical attempt reference sidecar

## Files

- `app/game/offline/historical_attempts.py`
- `tests/test_historical_attempt_references.py`

## Contract boundary

`HistoricalAttemptReferenceV1` is a provenance pointer, not an `Attempt`. It stores source archive/member/record hashes, source run and candidate identifiers, an optional source attempt identifier (left `None` when the source did not assign one), verifier identity, and a separately recorded mapping/admission state.

An exact input match requires the input-equivalence hash, mapping method, and mapped example ID. A nonmatch or unresolved row cannot claim a mapped example. Every record has `fitting_eligible=False`; no conversion, collection, fitting, evaluation, reputation update, or Final Test pathway is provided.

`HistoricalAttemptReferenceLedgerV1.append()` returns a new immutable ledger and rejects duplicate source-record references. Existing entries are not rewritten.

## Integration

The module is intentionally not imported by `app/game/offline/__init__.py` and is not wired into `records.py`, `TrainingManifest`, collection, or evaluation. This keeps historical rehearsal evidence isolated until a separately reviewed and approved admission/conversion contract exists.

## Validation

Focused command:

```powershell
pytest -q tests/test_historical_attempt_references.py
```

Result in the review environment: `6 passed`. The first run initially failed during import because the environment lacked `faiss`; the new module was adjusted to avoid importing `app.game.models` solely for content hashing. No full-suite run was performed.
