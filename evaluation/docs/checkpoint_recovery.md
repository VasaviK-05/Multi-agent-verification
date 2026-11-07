# Checkpointing and Recovery

## 1. Purpose

This document describes the current checkpointing and recovery mechanisms in the multi-agent verification system.

The objective is to preserve execution progress, retain completed verifier outcomes, prevent accidental repetition of completed calls, and make interrupted experiments auditable and recoverable.

Two execution contexts must be distinguished:

- Offline evidence collection, which has an implemented file-based checkpoint and resume mechanism.
- Live game execution through `GameRuntime`, for which equivalent incremental checkpointing and restart recovery have not yet been demonstrated.

These mechanisms must not be treated as interchangeable.

## 2. Offline Collector Architecture

The offline collection workflow is implemented across:

- `app/game/offline/collect.py`
- `app/game/offline/collection.py`

The command-line collector supports resuming a previous collection through `--resume-from`.

A collection bundle can contain:

- `recordings.json`
- `attempts.jsonl`
- `started.jsonl`
- `resume-provenance.json`
- A completeness report

The collector loads the previous bundle, validates that the resumed request matches the original request, and checks the prior execution journal before continuing.

## 3. Attempt Recording and Checkpoint Behavior

The collector maintains separate records for attempt starts and completed outcomes.

### 3.1 Start journal

Before a verifier call is executed, the collector invokes its start callback.

The start callback:

1. Appends the attempt identity to `started.jsonl`.
2. Flushes the file.
3. Calls `fsync` to request durable persistence of the start record.

This makes the start of an execution attempt visible in the recovery journal before the verifier call proceeds.

### 3.2 Completion journal

After an attempt produces an outcome, the collector writes its record to `attempts.jsonl` and flushes the file.

Recorded outcomes include successful directional reports, abstentions, unavailable verifiers, failures and other retained execution states.

The completion writer flushes the file, but the inspected implementation does not call `fsync` for every completion record. This distinction should be preserved when describing durability guarantees.

### 3.3 Resume behavior

When resuming a collection, the collector:

- Loads previously completed attempts.
- Reuses retained completed outcomes rather than calling those verifiers again.
- Carries prior executed identities into the new start journal.
- Records resume provenance.
- Continues only with attempts that have not already been completed or started.

If an attempt appears in the start journal but has no corresponding completion record, the collector refuses to retry it.

This is intentional: the system cannot safely determine whether the verifier call completed before the process stopped.

## 4. Interruption and Failure Handling

The collection workflow preserves failures rather than silently discarding them.

The inspected implementation handles:

- Verifier unavailability.
- Verifier execution failures.
- Timeouts and exceptions.
- Invalid or unusable returned reports.
- Interruptions.
- Attempts that were not started before interruption.

An interrupted collection can retain a completeness report describing missing outcomes and execution gaps.

A collection must not be evaluated as complete merely because some favorable verifier outcomes were recorded.

The recovery workflow requires all started attempts to have retained completion records. Ambiguous in-flight attempts block resumption.

Failures must not be retried by silently changing the request, resource setup or execution configuration.

## 5. Resource Consistency During Recovery

The offline collector checks that the resumed collection uses the same request and compatible observed measurement setup.

The resource setup is important because a result produced by one model, corpus, index or configuration cannot automatically be treated as equivalent to a result produced by another.

The transfer-evaluation protocol also requires:

- The same frozen current source and environment for paired conditions.
- Separate clean and altered resource observations.
- Resource-bound Evidence validation for each condition.
- Preservation of the original request and execution scope.
- No modification of historical recordings.

An incomplete or resource-inconsistent collection must not be promoted into a completed evaluation.

## 6. PostgreSQL Persistence: Current Capabilities

The application has PostgreSQL persistence for validation-level audit records through:

- `app/database/audit_repository.py`
- `db/migrations/003_validation_audit.sql`
- `db/migrations/004_audit_execution_metadata.sql`

The audit repository supports:

- Creating an audit with status `started`.
- Updating an audit to `completed`, `failed` or `partial`.
- Retrieving an audit by validation ID.
- Persisting execution contracts, selection plans, summaries, coverage, costs and failure details.

The API routes create the initial audit and persist validation and verifier outputs after the validation service returns.

This provides validation-level audit persistence. It does not establish incremental persistence of every live verifier attempt.

The separate verifier cost repository and migration 005 provide measurement setup, individual cost-attempt and cost-estimate persistence. These are measurement records, not a demonstrated live execution recovery journal.

No application-level calls to the cost repository functions were found in the inspected Python application code. Their PostgreSQL persistence is covered by a dedicated integration script and repository tests.

## 7. Live GameRuntime: PostgreSQL Execution Journal and Recovery

The live game execution path now has a PostgreSQL-backed execution journal.

The implementation spans:

- `app/orchestration/validation_orchestrator.py`
- `app/game/execution.py`
- `app/game/component_execution.py`
- `app/database/execution_journal_repository.py`
- `app/database/execution_recovery.py`
- `app/main.py`

### 7.1 Attempt-level persistence

The orchestrator creates a `_GameExecutionJournal` and passes it to the game execution runtime.

For each verifier attempt, the journal:

1. Creates a PostgreSQL attempt record.
2. Marks the attempt as started before verifier execution.
3. Records a completed report and outcome, including directional or abstention outcomes.
4. Records verifier unavailability with its reason.
5. Records execution failures with error type, message, duration and estimated cost.

Both standard game execution and component execution use these journal callbacks.

The repository provides `get_verifier_attempts()` to retrieve attempts in execution order, including their lifecycle status, report, digest, errors, timestamps, duration, cost and identity bindings.

### 7.2 Lease-based recovery

The orchestrator uses execution leases and heartbeat checks to protect active executions.

At application startup, `inspect_and_recover_incomplete_executions()` checks for:

- Stale initializing or ready executions.
- Running executions with missing or expired leases.
- Executions already marked blocked.

For stale executions, attempts still marked `started` are changed to `ambiguous`, with their outcome cleared. The execution is then blocked for manual inspection.

Completed attempts are preserved. Already-blocked executions are reported without being automatically resumed.

The recovery query uses row locking with `SKIP LOCKED` to avoid competing recovery workers processing the same execution.

### 7.3 Recovery limitations

This mechanism provides durable attempt journaling and conservative recovery, but it does not automatically resume interrupted live executions.

An ambiguous attempt is not retried because the system cannot establish whether the external verifier call completed before the process stopped.

There is also a separate persistence boundary:

- The orchestrator marks the execution journal completed.
- The API route subsequently persists validation-level records, verifier outputs and the completed audit.

A process crash between these stages can leave a completed execution journal with missing or incomplete API-level records.

The repositories provide individual retrieval functions for audits and verifier outputs, but a complete reconciliation mechanism for this condition has not been demonstrated.

### 7.4 Integration evidence

The repository contains integration tests covering:

- Successful validation persistence and application restart.
- Game-mode journal persistence and selected-output attempt links.
- Compound component attempt identity and finalization.
- Abstention and execution-failure lifecycle persistence.

The successful game-mode test checks the selected strategy, attempt identities, report-validation IDs, verifier-output links and actual verifier call counts.

The recovery and journal lifecycle suites were executed against a dedicated PostgreSQL test database:

- `tests/test_execution_recovery.py`: 5 passed in a fresh rerun (19.21 seconds; Python 3.14.7; controlled PostgreSQL test database).
- `tests/test_execution_journal_lifecycle.py`: 15 passed in a fresh rerun (20.96 seconds; Python 3.14.7; controlled PostgreSQL test database).

These results establish the tested journal and recovery behavior. The orchestrator persistence integration suite was freshly rerun: 5 tests passed in 30.98 seconds against the controlled PostgreSQL test database.

Application restart survival is covered by an integration test. A PostgreSQL server restart test and crash injection between journal completion and API-level persistence have not been demonstrated.
## 8. Validation Evidence

### 8.1 Offline collection and recovery

Previously executed checks included:

- `tests/test_game_task_conditioning.py`
- `tests/test_game_collection.py`
- The upstream transfer, evaluation, evidence, coverage, reliability, runtime, prototype-bundle and offline test suites.

Recorded results from the inspected development session:

- 39 tests passed for the task-conditioning and collection test group.
- 245 tests passed for the broader game and offline test group.

These historical results establish the behavior covered by those test groups at the time they were executed.

### 8.2 PostgreSQL execution journal and recovery

The following database integration suites were executed against the dedicated PostgreSQL test database:

- `tests/test_execution_recovery.py`: 5 passed in a fresh rerun (19.21 seconds; Python 3.14.7; controlled PostgreSQL test database).
- `tests/test_execution_journal_lifecycle.py`: 15 passed in a fresh rerun (20.96 seconds; Python 3.14.7; controlled PostgreSQL test database).

The repository also contains orchestrator integration tests covering:

- Validation persistence and survival across a second application startup.
- Game-mode execution journal and selected-output attempt links.
- Compound component attempt identity and finalization.
- Abstention and execution-failure persistence.

The orchestrator persistence integration suite was freshly executed: 5 tests passed in 30.98 seconds, including application restart survival, verifier-attempt links, game-mode journaling, and compound component finalization.

### 8.3 Evidence boundaries

The available evidence establishes PostgreSQL execution journaling, tested stale-execution recovery, successful API-level persistence and application-restart survival.

It does not establish:

- PostgreSQL server restart survival through a dedicated test.
- Automatic resumption of interrupted live verifier calls.
- Crash recovery between journal completion and API-level audit/output persistence.
- Complete reconciliation of missing or incomplete API-level records after such a crash.

The verifier cost repository has separate unit and PostgreSQL integration coverage. This establishes cost-measurement persistence, not live execution recovery.## 9. Remaining Work

The core PostgreSQL execution journal and conservative stale-execution recovery are implemented. The remaining work is focused on validating persistence boundaries and documenting the limits of recovery.

1. **Orchestrator integration tests:** Completed; 5 tests passed against the controlled PostgreSQL test database.
2. **Test the journal/API persistence boundary:** Add a controlled crash test between journal completion and API-level validation, verifier-output and audit persistence.
3. **Define reconciliation:** Specify and test how completed journal executions with missing or incomplete API-level records are detected and reconciled.
4. **Test database restart durability:** If required by the project acceptance criteria, verify that persisted execution and attempt records survive a PostgreSQL server restart.
5. **Preserve conservative recovery:** Keep ambiguous in-flight attempts blocked for inspection unless a safe retry or reconciliation rule is established. Do not describe the current implementation as automatically resuming interrupted verifier calls.

These tasks should remain within the Person 3 persistence, recovery and evaluation scope. Changes to teammate-owned verifier logic or runtime behavior outside the approved integration boundary are not required for this documentation update.## 10. Research Protocol Constraints

The governing protocol is `docs/upstream_transfer_evaluation.md`.

For transfer evaluation:

- Preserve every started attempt and its completion or failure.
- Do not retry an ambiguous in-flight attempt.
- Resume only unattempted identities.
- Preserve identical requests, source and resource setup during resumption.
- Count rehearsal calls against approved execution limits.
- Do not discard failures or evaluate a favorable subset.
- Do not refit policies, update reputation or recalibrate costs during transfer evaluation.

The transfer protocol is an evaluation contract, not evidence that a real experiment has been executed.

## 11. Current Status

| Capability | Status |
|---|---|
| Offline collector start journal | Implemented |
| Offline collector completion journal | Implemented |
| Offline resume and completed-attempt reuse | Implemented |
| Ambiguous in-flight attempt protection | Implemented |
| Offline completeness reporting | Implemented |
| Validation-level PostgreSQL audit | Implemented |
| PostgreSQL verifier cost measurement storage | Implemented |
| Live GameRuntime PostgreSQL attempt journaling | Implemented |
| Live attempt lifecycle and report retrieval | Implemented |
| Lease-based stale-execution detection and quarantine | Implemented and covered by recovery tests |
| Journal and recovery lifecycle test suites | 20 tests freshly passed (5 recovery + 15 journal lifecycle) |
| Orchestrator persistence integration tests | 5 freshly passed in 30.98 seconds |
| Application restart survival | Covered by a freshly passed orchestrator integration test |
| PostgreSQL server restart durability test | Not demonstrated |
| Automatic resumption of interrupted live executions | Not implemented |
| Reconciliation after journal completion but before API-level persistence | Not demonstrated |
| Controlled live crash-and-restart test across the persistence boundary | Pending |

The current evidence supports offline collector recovery, PostgreSQL-backed live attempt journaling, conservative stale-execution quarantine and validation-level persistence.

It does not support a claim that interrupted live executions automatically resume or that every journal/API persistence boundary is fully recoverable.
