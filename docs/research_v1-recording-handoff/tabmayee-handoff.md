# Tabmayee Handoff A — technical review, no collection authorization

## Status and files

Game-side code is proposed for review on `codex/research-v1-precollection-consolidated`. It is uncommitted. Read final-review.md, recording-config.proposed.json, recording-contract.md, input-contract.md, filesystem-support.md, source-resource-summary.json, source-resource-checklist.md and blocker-register.csv. Public file scope is public-commit-files.json; full raw datasets, provenance, archive originals and logs remain local under publication-boundary.md. No study configuration is frozen, and no teammate is being authorized to collect or fit.

Consume these game interfaces, without rewriting them in the orchestrator:

| Interface | Location / meaning |
|---|---|
| Planning input | QuestionAnalysis + QuestionResearchContext, approved q/a/reference, Candidate descriptors, known verification requirements; collection_plan(request, example) captures prerequisites and exclusions without reading reputation |
| Planning output | Detached plan diagnostics (requirements/status/candidates/eligibility/exclusions); later PlanningContext and enumerate_strategies produce feasible team/aggregation/cost definitions only after approved History, budget, dependencies and versions exist |
| Recording request | app/game/offline/collection.py: RecordingRequest / PreparationExample / IndependentLabel / Candidate; offline_recording_request_v1, intended_use=study requires explicit approval and custodian metadata |
| Recording outcome | CollectedAttempt wraps Attempt, original payload, timing, input/planning/resource provenance; RecordingBundle validates identity links and complete candidate outcomes |
| CLI/file boundary | app/game/offline/collect.py: validate, check, load_bundle; real collect is prohibited in this preparation. Its production path integrates the single durable file layer |
| Durability | app/game/offline/file_journal.py: create_run_directory, atomic_write_text, AttemptJournal.start / terminal, recovery_state |
| Verbatim content | app/game/offline/input_contract.py: QuestionText / verbatim_question_text_v1; also used by offline replay Example |

The JSON proposal is a worksheet, not a runnable RecordingRequest. Actual factory, expected_setup, study authorization, reservation and operational limits intentionally remain unresolved. Purpose currently accepts warmup/calibration; approve an honest study-purpose mapping or a separately reviewed extension before materializing a real request.

## Configuration and scientific boundaries

Proposed dataset is research_v1_exploratory_v1: Development **774 candidates /387 groups** (374 GSM8K, 400 HotpotQA); History **1,153 /577 groups**. Zero example approvals or human-verified labels are documented. Exact raw IDs and source digests are preserved locally; source-resource-summary.json exposes counts and immutable hashes without republishing payloads.

Capture four candidate names: confidence, evidence, rule, semantic. Use explicit registration/capabilities/prerequisites. Semantic requires nonblank non-judgment reference; Evidence does not require caller reference. Expected capabilities do not prove achieved coverage or independence. With unchanged proposed scope, null GSM8K references and valid HotpotQA context, there would be **3,096 outcome slots**, potentially **2,722 dispatched calls plus 374 Semantic exclusions**, conditional on approval and no other exclusions. No policy budget or sampled team may prune complete-candidate recording.

Preserve exact question and candidate-answer strings; no strip, Unicode normalization, sentinel encoding or surrogate input hashing. A nonblank question may contain outer whitespace; identifiers remain strict. Reference serialization is unresolved: proposed null GSM8K and deterministic permitted HotpotQA context. Never send correctness labels, gold answers, synthetic-generation metadata or label-oracle annotations to verifiers. Preserve label source/method/provenance privately. Provisional automated/synthetic labels must not be cast to independent_ground_truth. The independent-label enum is unchanged.

Costs remain recorded mean attempt wall times in **ms**, not prices or hard runtime limits: confidence 14925.820978323463; evidence 107.93551665459138; rule 0.09707332161876063; semantic 70.4728633359385. There are 120 included samples per verifier after eight total warmups. Hard strategy budget, cost coefficient, team minima, threshold, losses, coverage floor, priors, aggregation/execution/attack versions and suppression are unapproved. Raw report collection does not need a fitted policy.

Recorded resource manifest `754bfa8ec4b43881a183c64478d791496e6a21d2e68b3c862d85a8e89beda10c` and setup `83c114806aa6eb3ba06664b8d3d6bd1892699f0c588990e0fb88f35bcc37f1ee` are historical expectations. Confidence freeze records llama3.2:3b /5 samples. They are not actual live observations or certificates for edited source. Match implementation/config/model/prompt/service/corpus/index/receipt and before/after observations using existing guards. Unknown/changed resources must stay incomplete; no test fixture or old policy may replace real bindings. The exact historical whole-app source digest and actual call inputs for 24 timing rows remain unresolved.

## Required orchestration call order

1. **Before services or factory construction:** obtain an approved, immutable request/profile and approved outcome-free reservation; non-executingly validate schemas, exact source/scope/reference/input/label/eligibility/authorization identity. Use a prerequisite-aware factory; do not eagerly instantiate Semantic for a reference-less example. Verify actual source/setup/resources with Raunak; no live verification occurs in this handoff step.
2. Create a new exclusive run directory. Atomically publish and synchronize request/setup metadata. The actual future factory returns `(verifiers, MeasurementSetup, resource_observer)` and must truthfully describe the full captured roster. expected_setup/resource IDs must bind the real reviewed source and environment.
3. For each eligible slot, derive the existing stable `attempt_identity = content_id(['offline_attempt_v1', request_id, run_id, verifier_name])`. Await `AttemptJournal.start(attempt_id)` success **before dispatch**. If this raises, do not execute or advance.
4. Dispatch exactly the approved question/answer/reference tuple once. Preserve the original returned payload separately from canonical VerificationResult. Capture state, duration/timing status, source/model/prompt/index/config fingerprints and before/after resource observations. Ineligible/unavailable-before-dispatch slots receive explicit executed=false outcomes, no synthetic duration and no invented report.
5. Pass unchanged one-line `CollectedAttempt` JSON to `AttemptJournal.terminal`. Await durable acknowledgment **before treating it complete or scheduling the next call**. Failure stops the workflow; surface stable attempt ID and preserved location. The existing CLI already wires this ordering; prefer using it rather than duplicating journaling.
6. Publish final bundle/measurements/report via atomic_write_text. Completion statistics do not substitute for completeness/provenance checks. A terminal failure may complete a slot but does not establish achieved coverage or usefulness for fitting.
7. Restart only into a fresh output directory. Validate original request/setup and strict start/terminal journal links before factory initialization. Preserve old evidence and resume provenance. Retain completed/failed outcomes without repeating calls. Started-without-terminal ambiguity blocks automatic retry. Executed missing/interrupted/malformed outcomes remain incomplete and must not be re-executed silently; never-started missing slots may resume only under the approved request.

Support and rejection are directional returned reports; abstention is also returned and has a body. Unavailable, failed and missing have no report. Timeout maps to failed+timing_status timeout. Typed VerifierUnavailable/VerifierExecutionFailure differ from unexpected runtime programming errors; preserve unexpected-error issue flags and obtain explicit adapter disposition. Do not turn errors/missing data into abstention or successful runtime trials. No exactly-once external effect guarantee is claimed.

Local synchronization is tested on macOS/APFS with fsync/F_FULLFSYNC, directory fsync and same-filesystem atomic publication. Windows and the actual collection platform are not certified. If her external rehearsal runner is retained instead of the game CLI, its owner must implement and independently validate the same acknowledgment/recovery interface. No external runner or API route was edited.

## Owner-specific remaining work

| Owner | Required action |
|---|---|
| Vasavi / game owner | Review the code/proposal; approve scientific scope/label/reference/analyzer/roster/randomness/purpose/operational decisions separately; bind approved future planning and recording contracts; do not approve through this handoff |
| Tabmayee | Supply prerequisite-aware factory/observer and orchestration integration, typed exception/timeout boundary, supported filesystem/route, operational caps and immutable request/checkpoint flow; verify no team/order/prefix-conditioned report behavior |
| Raunak / relevant producers | Verify actual verifier/model/prompt/evidence/semantic/rule configuration and resource custody; supply historical source/cost request/tuple ledger where owned; missing custody remains missing |
| Samika | No database migration or API persistence work is required for file-only preparation. If separately scoped later, consume durably acknowledged immutable rows idempotently by attempt_id, reject conflicting duplicates and never trigger retries from database recovery |
| Independent custodian + Vasavi | Supply outcome-free reservation and split/exposure/shared-context disposition without sharing Final Test payloads |

## Non-verifier integration smoke: commands and observable criteria

Export `TEST_PYTHON` and `HF_HOME` using environment.md, then run from the repository root. These commands need no raw research dataset, model, provider, database or network:

```sh
"$TEST_PYTHON" docs/research_v1-recording-handoff/validation/probe_imports.py .
"$TEST_PYTHON" docs/research_v1-recording-handoff/validation/run_checks.py boundaries
```

**PASS:** import command exits 0 and prints SCHEMA_IMPORT_PASS; boundaries exits 0 with **18 passed, zero failures/skips**. Its deterministic synthetic tests verify acknowledged starts before calls, terminal acknowledgment before progress, stop-on-ack-failure, duplicate rejection, raw-input/provenance identity, corrupt recovery rejection before factory initialization, executed-missing versus never-started distinctions, and no repeated completed calls after final snapshot failure. Ownership tests reject unauthorized paths. Temporary synthetic files are not study recordings.

**FAIL / stop:** any nonzero exit, real verifier/model/network guard firing, duplicate or ambiguity accepted, lost raw tuple/state/provenance, changed resources accepted as compatible, repeated completed calls, or a skipped boundary case. Report the failing test and stable artifact location; do not enable a live fallback or remove guards.

Optional private evidence revalidation is separate:

```sh
RESEARCH_V1_REQUIRE_PRIVATE_INPUTS=1 "$TEST_PYTHON" docs/research_v1-recording-handoff/validation/run_checks.py input
"$TEST_PYTHON" docs/research_v1-recording-handoff/validation/run_checks.py handoff
```

Export `RESEARCH_V1_ARTIFACT_DIR` to the authorized external ZIP directory first. These require the full local authorized evidence bundle; expected results are 26 input cases and 13 consistency checks with no failure/skip. Public-checkout skips of private-input cases are not proof of source validation. None of these commands authorizes History/Development collection or fitting.

## Manual review message — not sent

> Tabmayee, please review Handoff A at docs/research_v1-recording-handoff/tabmayee-handoff.md and final-review.md on the proposed feature branch. The public allowlist excludes raw/unapproved research payloads and local host logs. Please run the two non-verifier smoke commands and review the factory/observer, typed failure boundary and durable start/terminal/resume flow. Scientific, custody, live-resource, deployment-platform and concrete request authorization gates remain open. This is a technical review handoff, not permission to collect, fit or access Final Test.
