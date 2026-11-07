# Persistence Validation

## 1. Purpose and scope

This document records the PostgreSQL persistence mechanisms inspected for the capstone backend.

It distinguishes:
- Persistence implemented in repositories and database migrations.
- Persistence connected to the API application flow.
- Persistence and restart behaviour covered by tests.
- Remaining integration gaps.

The objective is to establish which application records survive process restarts and whether database operations handle retries, conflicts and failures safely.

This document complements `checkpoint_recovery.md`. Database persistence of completed records is not equivalent to incremental execution checkpointing.

## 2. Persistence architecture

The inspected PostgreSQL implementation is distributed across several modules:

| Data | Implementation |
|---|---|
| Validation records | `app/database/validation_repository.py` |
| Verifier outputs | `app/database/verifier_repository.py` |
| Feedback | `app/database/feedback_repository.py` |
| Reputation | `app/database/reputation_repository.py` |
| Ground-truth labels | `app/ground_truth/storage.py` |
| Audit records | `app/database/audit_repository.py` |
| Verifier cost measurements | `app/database/verifier_cost_repository.py` |

The API routes coordinate several of these repositories. The service and orchestrator are not themselves the complete persistence layer.

An older scaffold also exists at `app/database/repository.py`. Its methods are explicitly placeholders: writes are no-ops and retrieval returns `None`. Its current usage should be checked before any cleanup or claims that it is unused.

## 3. Validation record persistence

Implementation: `app/database/validation_repository.py`

### Write operation

`save_validation()` stores:
- Validation ID and question ID.
- Question and generated answer.
- Context.
- Final status and final score.
- Session ID, domain and difficulty.
- Selected verifiers.
- Early-stop reason and signed score.
- Creation timestamp.

The function commits on success, rolls back on exceptions, and closes its cursor and connection.

### Retrieval operation

`get_validation(validation_id)` retrieves a persisted validation record by ID and returns its fields as a dictionary. It returns `None` if no matching record exists.

### Assessment

Validation-level storage and retrieval are implemented. This repository persists the final validation record; it does not provide a per-verifier execution checkpoint.

## 4. Verifier output persistence

Implementation: `app/database/verifier_repository.py`

### Write operation

`save_verifier_outputs()` inserts verifier results associated with a validation. Each inserted result receives a generated UUID and an execution-order value.

Stored fields include:
- Validation ID and question ID.
- Verifier name.
- Score and pass/fail value.
- Reasoning.
- JSON metadata.
- Execution order.
- Creation timestamp.

The function commits the collection of outputs in one transaction and rolls back on failure.

### Retrieval operation

`get_verifier_outputs(validation_id)` retrieves the results for a validation, ordered by execution order and creation time.

### Known limitations

- `latency_ms` is currently inserted as `None`, even though the database field exists.
- The API-level repository saves the result collection after execution rather than writing each verifier result incrementally as it finishes.
- This API-level output persistence is separate from the PostgreSQL-backed live GameRuntime execution journal documented in `checkpoint_recovery.md`.

## 5. Feedback persistence

Implementation: `app/database/feedback_repository.py`

`save_feedback()` checks for existing feedback associated with a validation before inserting a new record.

Its retry behaviour is:

1. If no feedback exists, insert a new record with a UUID and timestamp.
2. If feedback already exists with the same `is_correct` value, return the existing record.
3. If the existing `is_correct` value differs, raise a `ValueError`.
4. Commit successful operations and roll back on exceptions.

This makes repeated submissions with the same correctness value safe from duplicate insertion.

### Known limitation

The existing-record comparison checks `is_correct`, not `comment`. A retry with the same correctness value but a different comment returns the existing feedback rather than updating it.

## 6. Reputation persistence and reconstruction

Implementation: `app/database/reputation_repository.py`

The repository supports both individual reputation rows and complete reputation-manager state.

### Individual reputation rows

- `load_reputation()` retrieves verifier/domain alpha and beta values.
- `save_reputation()` inserts or updates a verifier/domain pair using an atomic PostgreSQL upsert.

### Feedback-event reconstruction

`load_feedback_events()` joins:
- `feedback`
- `validation_records`
- `verifier_outputs`

It reconstructs feedback events containing the external correctness label, domain and verifier results.

`build_reputation_state()` converts these events into the reputation manager's expected event objects, records the feedback batch and exports the resulting state.

### Complete snapshot persistence

- `save_reputation_manager_state()` stores the complete exported manager state as JSONB with a schema version.
- `load_reputation_manager_state()` retrieves the snapshot and checks that the stored schema version matches the version inside the JSON state.
- `save_reputation_state_and_rows()` stores the complete manager snapshot and verifier/domain aggregate rows in one database transaction.

### Restoration assessment

Two restoration mechanisms are available:

1. Load a persisted manager snapshot.
2. Reconstruct manager state from persisted feedback events and verifier outputs.

The repository supports reconstruction when a snapshot is missing. This capability should not be confused with proof that every application startup automatically invokes the recovery path. Startup integration must be verified separately.

## 7. Ground-truth persistence

Implementation: `app/ground_truth/storage.py`

`save_ground_truth()` persists a ground-truth label in the `ground_truth_labels` table.

Stored fields include:
- Ground-truth UUID.
- Validation ID.
- Question ID.
- Label.
- Source.
- Label timestamp.

### Idempotency behaviour

The insert uses `ON CONFLICT (validation_id) DO NOTHING`.

If a record already exists, the function retrieves it and compares its question ID, label and source:

- Identical data: return the existing record.
- Different data: raise a `ValueError`.
- Conflict without a retrievable existing row: raise a `RuntimeError`.

Successful operations are committed; exceptions trigger rollback.

### Database constraint

Migration `006_ground_truth_idempotency.sql`:

1. Checks for existing duplicate validation IDs.
2. Refuses migration if duplicates exist.
3. Adds a unique constraint on `ground_truth_labels.validation_id`.

The application-level retry handling is therefore backed by a database-level uniqueness constraint.

## 8. Audit persistence

Implementation: `app/database/audit_repository.py`

The audit repository provides:

- `create_audit()`: creates a validation audit with initial status `started`.
- `update_audit()`: updates the audit lifecycle and execution metadata.
- `get_audit()`: retrieves the persisted audit by validation ID.

The audit lifecycle supports `started`, `completed`, `failed` and `partial`.

The audit record includes execution contract, reputation snapshot and identifier, selection plan, run summary and other execution metadata.

Migrations `003_validation_audit.sql` and `004_audit_execution_metadata.sql` establish the audit table and add selection-plan and run-summary JSONB fields.

### API integration

The inspected API routes import and call the validation, verifier-output and audit repositories.

In the `/validate` flow, the route:

1. Calls the validation service.
2. Saves the completed validation record.
3. Creates the audit record.
4. Saves verifier outputs and any applicable ground-truth record.
5. Updates the audit with completion status and execution metadata.

The `/generate-and-validate` route follows a corresponding persistence sequence after answer generation.

If persistence fails, the route makes a best-effort attempt to mark the audit as failed.

### Important lifecycle limitation

The route invokes validation before creating the audit record. Consequently, the audit record does not serve as a pre-execution checkpoint for the live GameRuntime.

Individual live verifier attempts are now recorded through the PostgreSQL-backed execution journal described in `checkpoint_recovery.md`. The audit remains a separate validation-level record created after orchestration.

A crash after the execution journal is marked completed but before API-level validation, verifier-output and audit persistence can leave incomplete API-level records. A complete reconciliation mechanism for this boundary has not been demonstrated.

## 9. Verifier cost measurement persistence

Implementation: `app/database/verifier_cost_repository.py`

Migration: `db/migrations/005_verifier_cost_measurements.sql`

Three PostgreSQL tables support cost measurement.

### `verifier_measurement_setups`

Stores measurement-environment information, including:
- Verifier identity and implementation fingerprint.
- Configuration and model fingerprints.
- Corpus and index fingerprints.
- Machine and runtime configuration.
- Concurrency and cache configuration.
- Code revision and dependency versions.

A unique setup fingerprint identifies an equivalent measurement setup.

### `verifier_cost_attempts`

Stores individual measurement outcomes, including:
- Attempt ID and run ID.
- Verifier and setup IDs.
- Dataset ID.
- Duration.
- Outcome and error information.
- Warmup flag.
- Measurement purpose and data role.
- Optional source verifier-result ID.
- Metadata and recorded timestamp.

Allowed outcomes are `returned`, `failure`, `timeout` and `interrupted`.

The table enforces valid measurement purposes, data roles and nonnegative durations.

### `verifier_cost_estimates`

Stores calculated statistics:
- Mean attempt cost.
- Median duration.
- P95 duration.
- Attempt and failure counts.
- Warmup inclusion setting.
- Estimator version.
- Input digest.
- Source attempt IDs.

The repository calculates and saves estimates from persisted attempts. It also uses an input digest and calibration ID to identify repeated estimate inputs.

### Cost-estimate idempotency

Migration `007_verifier_cost_estimate_idempotency.sql`:

1. Checks for duplicate `(calibration_id, input_digest)` pairs.
2. Refuses migration if duplicates exist.
3. Adds a unique constraint on those two columns.

This database constraint backs the repository's estimate-retry behaviour.

### Known integration limitation

The cost repository and its database schema are implemented, but the inspected application-wide search found no production application call sites for `save_verifier_attempt()`, `save_measurement_setup()` or `calculate_and_save_cost_estimate()`.

The functions were found in the repository and persistence test script.

Therefore, calibrated cost-measurement persistence is implemented at the repository level, but application integration with these cost-repository functions has not been established by the inspected code.

This is separate from the live GameRuntime execution journal, which records attempt duration and estimated cost through `execution_journal_repository.py`. The journal does not establish that the calibrated cost-measurement setup, attempt and estimate workflow is automatically invoked for every live execution.

The cost-attempt table stores final measurement outcomes; it does not implement a started to completed checkpoint lifecycle.

## 10. Database migration history

| Migration | Purpose |
|---|---|
| `001_review_updates.sql` | Review-related schema updates |
| `002_reputation_state.sql` | Reputation persistence |
| `003_validation_audit.sql` | Validation audit records |
| `004_audit_execution_metadata.sql` | Audit selection plan and run summary |
| `005_verifier_cost_measurements.sql` | Measurement setups, attempts and estimates |
| `006_ground_truth_idempotency.sql` | Unique ground-truth record per validation |
| `007_verifier_cost_estimate_idempotency.sql` | Unique cost estimate per calibration and input digest |

Previously recorded database verification established that migrations 001–007 were applied and verified on the project databases. Integration checks used an isolated `capstone_test_db` where appropriate. The actual `capstone_db` must not be subjected to destructive test operations.

## 11. Test and verification evidence

Previously recorded focused persistence tests completed with:

**103 passed, 1 warning**

The test command covered:
- Feedback API.
- Validation retrieval.
- Reputation repository and migration upgrade.
- Audit API and repository.
- Ground-truth storage and persistence.
- Verifier cost repository.
- Migration runner.

The warning concerned the Starlette/httpx TestClient deprecation and was non-blocking.

### Database integration checks

Previously executed integration scripts verified:
- Feedback persistence and restart behaviour.
- Reputation reconstruction when a snapshot is missing.
- Ground-truth persistence.
- Verifier-cost persistence.

The verifier-cost persistence script saved a measurement setup, three attempts and a calculated estimate, then read back the stored values. The sample attempts included successful returns and a failure.

### Live execution journal and recovery tests

The following PostgreSQL integration suites were executed against the dedicated test database:

- `tests/test_execution_recovery.py`: 5 passed in 19.21 seconds (fresh rerun during this review).
- `tests/test_execution_journal_lifecycle.py`: 15 passed in 20.96 seconds (fresh rerun during this review).

These tests cover journal lifecycle persistence, attempt retrieval, stale-execution recovery, ambiguous attempts and preservation of completed attempts.

`tests/test_orchestrator_persistence_integration.py` was freshly rerun during this review: 5 passed in 30.98 seconds. It covers validation persistence, application restart survival, generated-and-validated attempt links, game-mode journal/output links and compound component execution.

### Evidence boundaries

- Repository tests do not by themselves prove every production application path invokes the repository.
- Application restart survival was freshly verified by the orchestrator persistence integration test run (5 passed).
- PostgreSQL server restart durability has not been demonstrated by a dedicated test.
- The execution journal does not automatically resume ambiguous interrupted verifier calls.
- A crash between journal completion and API-level audit/output persistence still lacks a demonstrated reconciliation mechanism.
- Cost-measurement repository persistence does not prove automatic integration with every live GameRuntime execution.
## 12. Outstanding work and limitations

| Item | Current assessment |
|---|---|
| Validation record save/retrieval | Implemented |
| Verifier output save/retrieval | Implemented at API level |
| Feedback duplicate handling | Implemented |
| Reputation snapshot save/load | Implemented |
| Reputation reconstruction from feedback | Implemented at repository level |
| Ground-truth idempotency | Implemented and database-constrained |
| Audit lifecycle and metadata | Implemented |
| Cost measurement repository and schema | Implemented |
| Cost estimate idempotency | Implemented and database-constrained |
| Live GameRuntime PostgreSQL attempt journaling | Implemented |
| Live attempt lifecycle and report retrieval | Implemented |
| Lease-based stale-execution quarantine | Implemented and covered by recovery tests |
| Verifier output latency population | Not established; current insert passes `None` |
| Production GameRuntime integration with calibrated cost-attempt repository | Not established |
| Automatic resumption of interrupted live executions | Not implemented |
| Reconciliation between journal completion and API-level persistence | Not demonstrated |
| PostgreSQL server restart durability test | Not demonstrated |
| Automatic startup restoration of reputation | Requires startup-path verification |
| Usage of the older no-op scaffold | Requires call-site verification |

### Recommended follow-up

1. Run the existing orchestrator persistence integration tests against the dedicated PostgreSQL test database.
2. Test the crash boundary between journal completion and API-level validation, verifier-output and audit persistence; define a reconciliation mechanism.
3. Verify PostgreSQL server restart durability if required by the project acceptance criteria.
4. Verify the application's reputation initialization path and confirm which restoration mechanism it invokes.
5. Verify whether the older `app/database/repository.py` scaffold has active callers.
6. Confirm the intended integration point for calibrated cost measurement and actual latency recording.

## 13. Relationship to the research evaluation protocol

Database persistence validation is separate from policy fitting, baseline comparison and transfer-evaluation readiness.

The transfer evaluation must continue to follow `docs/upstream_transfer_evaluation.md`.

In particular:

- Do not refit or update frozen policies.
- Do not change reputation, probabilities, thresholds, dependencies or estimated costs during transfer evaluation.
- Keep historical, current-clean and current-altered records separate.
- Preserve failures, abstentions and every started attempt.
- Do not use final-test payloads or labels.
- Do not treat database persistence tests as evidence of empirical policy performance.

The offline collector's journal and resume safeguards are documented separately in `checkpoint_recovery.md`. They must not be presented as guarantees of the live GameRuntime.









