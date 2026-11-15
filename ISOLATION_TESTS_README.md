# Historical-reference isolation tests

This is a test-only follow-up for the standalone historical-reference experiment.

## Scope

- Does not change application source code.
- Does not connect the sidecar ledger to collection, verifier execution, records, fitting, evaluation, reputation, APIs, or Final Test.
- Adds checks that `fitting_eligible` cannot be enabled, no implicit conversion helpers exist, and the contract remains unreferenced by the offline package initializer, canonical records, collection, and evaluation modules.
- Keeps all existing six provenance/immutability tests.

## Apply

Copy `tests/test_historical_attempt_references.py` into the repository, replacing the prior test file. No other file should be changed.

Run:

```powershell
python -m pytest -q tests/test_historical_attempt_references.py
```

Expected result in the isolated source-review environment: `9 passed`.

This is focused test coverage only, not a full-suite or production-integration validation.
