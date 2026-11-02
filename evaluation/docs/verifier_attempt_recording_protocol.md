# Research dataset verifier execution and Attempt recording

## Purpose and current status

`evaluation/data_preparation/run_verifier_attempts.py` is the resumable execution/recording entry point for `evaluation/datasets/offline_examples/research_v1/`. It invokes the project's four actual verifier implementations through the existing local-only `app.benchmark.project_adapter:create_verifiers` factory. It never constructs an offline `Example`, `Partition`, or `TrainingManifest`, and does not fit reputation, payoffs, or policies.

The current checkout is **not execution-ready**. `VERIFIER_COLLECTION_ADAPTER_CONFIG` is unset, and no `evaluation/datasets/verifier_attempts/research_v1/` output exists. The supported factory requires locally pinned embedding and NLI snapshots, an identified corpus and matching index with a recorded build receipt, and a live loopback Ollama service/model observation. The factory intentionally refuses network downloads. No verifier calls or empirical Attempts were produced in this implementation pass.

## Repository contracts inspected

- `app/game/offline/records.py::Attempt` validates the verifier name, one of `directional`, `abstention`, `unavailable`, `failed`, or `missing`, the actual `VerificationResult` JSON when returned, execution/configuration IDs, report provenance, adapter version, and optional observed resources.
- `app/game/offline/records.py::Example` additionally requires an independently sourced binary label, complete attempt set, planning metadata, and cache contract. These prepared rows are not Examples until those requirements can be fulfilled and reviewed.
- `TrainingManifest` requires History and Development `Partition`s plus an outcome-free `FinalTestReservation`. This task creates neither a reservation nor a training manifest because the existing final partition is exposed and no protected holdout exists.
- `app/game/offline/timing.py::TimedVerifier` measures real call duration and preserves exceptions. The runner records elapsed milliseconds as an execution sidecar, not as an invented verifier score or monetary cost.
- `app/benchmark/project_adapter.py::inspect_setup` performs local preflight; `create_verifiers()` validates the live service/resource identity before and after loading the actual verifier pool.
- The ValidationOrchestrator is not used: it performs selection/aggregation and may evaluate automatic ground truth rather than making the four required direct verifier calls.

## Input boundary

The runner reads the History and Development prepared JSONL rosters and only extracts candidate/question/group/partition identifiers plus the explicit `verifier_input` fields: benchmark, question, candidate answer, and permitted context. It does not use or copy `gold_answer`, correctness labels, worked solutions, replay traces, or label provenance into verifier calls or attempt records. GSM8K worked solutions are not supplied. HotpotQA context is passed only where already present in `verifier_input`; this is benchmark-context-assisted, not retrieval from the shared corpus. The Evidence Verifier itself uses the pinned shared corpus configured for the run.

The prepared unresolved ledger has candidate answers and identities but no `verifier_input`. Those records are preserved in `unresolved_not_attempted.jsonl` with their `unresolved` status and `not_attempted_no_prepared_verifier_input`; the runner does not reconstruct missing inputs from source records or send those records to verifiers. Thus they are not counted as attempted candidates.

## Output and resume behavior

After successful preflight, output is created at `evaluation/datasets/verifier_attempts/research_v1/` and contains:

- `execution_manifest.json`: source hashes, resource/setup fingerprint, adapter-config hash, code revision, runtime/dependency metadata, roster digest, and boundary declarations.
- `attempts.jsonl`: one wrapper per actual candidate/verifier call; includes the schema-validated `Attempt`, candidate/question/group IDs, partition, input digest, real wall time, and return/failure timing status. It does not duplicate question text, labels, answers, or evidence.
- `unresolved_not_attempted.jsonl`: unresolved identities preserved without inferred labels or fabricated inputs.
- `validation_summary.json`: generated after a complete run.

Each candidate receives a deterministic execution ID; each Attempt is keyed by candidate ID and verifier name. The runner flushes each completed Attempt, and `--resume` verifies source hashes, resource/config/code manifest identity and skips already recorded candidate/verifier pairs. A changed input/resource/configuration requires a new versioned output path; failed calls are retained and are not silently retried. A deliberate retry should use a separately versioned run so original failures remain auditable.

Run from the repository root after the adapter configuration and local resources have been reviewed:

```powershell
$env:VERIFIER_COLLECTION_ADAPTER_CONFIG = "path\to\reviewed_project_adapter.json"
.\.venv\Scripts\python.exe evaluation\data_preparation\run_verifier_attempts.py run
.\.venv\Scripts\python.exe evaluation\data_preparation\run_verifier_attempts.py validate
```

If execution is interrupted after output creation, resume with:

```powershell
.\.venv\Scripts\python.exe evaluation\data_preparation\run_verifier_attempts.py run --resume
```

The JSON configuration must satisfy `app.benchmark.project_adapter.AdapterConfiguration`, and its referenced local resources must pass `inspect_setup`. No download or provider pull is performed by this runner.

## Validation and interpretation

`validate` reopens every stored Attempt through the actual Pydantic schema, checks candidate/verifier uniqueness, candidate/group/partition identity, adapter/configuration linkage, source hashes, unresolved-ledger preservation, and reports pending calls and actual failures. Returned abstentions are valid Attempts with the actual report; unavailable and failed calls have no report. Neither abstentions nor failures are relabeled as correctness outcomes.

An output with Attempts is still **not policy-fitting-ready**. Genuine verifier calls do not create a protected Final Test, establish approval of label provenance, or replace the Example/Attempt and TrainingManifest contracts. A separate approved conversion/recording stage must bind these attempts to prepared labels, determine any missing domain/planning metadata, validate complete-team/cache semantics, and use a custodian-approved split/custody design before fitting.

## Tests

`tests/test_verifier_attempt_runner.py` uses synthetic fake verifier objects only to test serialization, label-input isolation, identity preservation, resume idempotence, source-change refusal, and Pydantic Attempt validation. These tests are not empirical verifier runs and do not create research Attempts.
