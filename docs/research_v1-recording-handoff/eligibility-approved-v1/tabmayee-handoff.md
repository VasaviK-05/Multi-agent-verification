# Tabmayee Handoff A — approved eligibility compatibility v1

This version supersedes the Development selection and approval assumptions of the original Handoff A. Base: main `9c38f4de402d510bb13111da592a4f29abe03a24` (merged PR #35). The eligibility approval is recognized; recording, collection, fitting and protocol freeze remain blocked. No live verifier, database, service or policy is activated by this update.

## Configuration and identities

Consume `recording-config.proposed.json`, `scope.ids.json`, `verification-receipt.json` and `remaining-decisions.md` in this directory. These are an offline compatibility worksheet and ID/hash inventory, not a runnable RecordingRequest. The original root proposals remain historical, with their original identities in `historical-identities.json`. Do not run the original source extractor or old validator as an approved-roster selector.

Approved manifest: `evaluation/artifacts/person1/research_v1_exploratory_eligibility_approved_v1/eligibility_manifest.json`; ID `research_v1_exploratory_eligibility_approved_v1`. Body SHA-256: `f2cc0fd108b961bf4795767df4f90e92d7fa0f418ef9865d0206f32d7b45282d`. Complete-file SHA-256: `75087c28f01e566be0572c149a182f5b02872f2973bcb32156bb607ecdac1eaa`. These are different hash definitions. The receipt pins both, the sidecar and all five supporting outputs.

Development is **744 candidates / 372 groups**: GSM8K 374 candidates /187 groups; HotpotQA 370 candidates /185 groups. Every group has one VERIFIED_CORRECT and one SYNTHETIC_INCORRECT candidate. Stable IDs are enumerated in `scope.ids.json`. Fifteen HotpotQA groups (30 candidates) were quarantined from the former 774/387 source inventory. The 375 exclusion rows comprise 332 unresolved candidates, 30 quarantined candidates and 13 group summaries with no candidate ID. Do not interpret 375 as excluded candidate identities. History scope/approval has not been enlarged by this manifest.

Approval is Development eligibility only. `provisional_automated_labeling_v1` and `human_verified=false` remain true for all approved rows. VERIFIED_CORRECT is a producer class, not independently reviewed ground truth. No label-enum conversion or independent-label certification is supplied. Semantic clearance is **NOT_CLAIMED**: zero threshold findings do not prove every lower-scoring pair is unrelated. Keep the shared-context quarantine and unresolved leakage disposition.

## Input completeness and provenance

The eligibility bundle alone lacks full question/reference tuples and runtime configuration. The separately supplied original source package is bound by source manifest SHA `5e55dbd17bf968eaa7768819945ab3adfc3b30d850817b859c63015e9db03764`. A read-only join verified all 744 original candidate and verifier-input tuples, with zero missing/mismatched payloads and exactly 30 quarantined IDs removed. Sixteen retained questions have outer whitespace. Preserve question and answer strings verbatim through QuestionText; never strip, normalize, use sentinels or substitute surrogate hashes as inputs.

This payload availability is not reference or runtime approval. GSM8K has no supplied evidence context; HotpotQA has context requiring approved deterministic non-judgment serialization. Never send labels, gold answers, synthetic-generation metadata or label-validation annotations to verifiers. The public index contains IDs and integrity digests only, not raw answers or per-candidate labels.

Producer custody remains incomplete: the named generator `evaluation/data_preparation/exploratory_eligibility_approved.py` is absent at declared revision `d9fd453afe9bfe601ace8e1d30b80a9e593c8484`. Obtain actual generator bytes/revision, dirty-file inventory and run/transfer custody from the producer. A matching user-approved hash establishes the designated eligibility bytes, not the missing producer chain or runtime resource observations.

Historical resource/setup hashes and timing rows remain historical expectations. Retain all existing source/config/model/prompt/service/corpus/index/receipt and before/after observation checks. Unknown or changed resources remain incompatible/incomplete. No bypass, fixture resource or old policy may stand in for actual bindings.

## Four-verifier compatibility and planning

Captured roster remains confidence/evidence/rule/semantic with unchanged confidence_v1/evidence_v1/rule_v1/semantic_v1 adapters. Semantic requires a nonblank non-judgment reference; Evidence does not require a caller reference. A prerequisite-aware factory must avoid constructing Semantic for an ineligible reference-less slot. Capabilities describe eligibility, not achieved coverage or independent information.

Complete-candidate recording has **2,976 outcome slots**. Conditional on null GSM8K references, valid HotpotQA references and no other exclusions, this means **2,602 dispatched calls plus 374 explicit Semantic exclusions**. These are planning counts, not execution authorization or guaranteed completed reports. No sampled policy/team budget may prune recording. Preserve explicit outcomes for every candidate/verifier slot.

Planning input remains QuestionAnalysis + QuestionResearchContext, Candidate descriptors, declared requirements and approved input/reference identities. `collection_plan(request, example)` returns detached prerequisite/eligibility/exclusion diagnostics without reading reputation. Later PlanningContext/enumerate_strategies require separately approved History, budget, dependencies and versions. No new team minima, coverage floor, decision threshold, fallback, aggregation, execution, replay, attack or suppression version is approved here. Raw complete-candidate recording has no decision-based early termination; recorded failures/abstentions remain distinct and cannot be used as fabricated informative coverage.

Calibration estimates remain mean wall time in **ms**: confidence 14925.820978323463; evidence 107.93551665459138; rule 0.09707332161876063; semantic 70.4728633359385 (120 included samples each, eight total warmups). They are neither prices nor hard deadlines. Hard budget, cost coefficient and operational caps remain unset; no existing policy values change.

## Interfaces and required call order

Use existing game interfaces unchanged:

- `app/game/offline/eligibility.py`: `verify_archive(path)` validates pinned approved bytes and linked records; `verify_source_payloads(evidence, source_archive)` validates original Development payload identity only. Neither dispatches anything nor creates a RecordingRequest.
- `app/game/offline/collection.py`: RecordingRequest, PreparationExample, IndependentLabel, Candidate, CollectedAttempt and RecordingBundle; schema `offline_recording_request_v1`. Actual study requests require explicit authorization/custodian metadata, reference/label disposition and outcome-free reservation. Existing purpose constraints need an honest approved mapping or separately reviewed extension.
- `app/game/offline/input_contract.py`: QuestionText / `verbatim_question_text_v1`; no coercion of input bytes.
- `app/game/offline/collect.py` and `file_journal.py`: validate/check/load_bundle, exclusive run directory, atomic_write_text, AttemptJournal.start/terminal and recovery_state. No orchestration/API changes are supplied.

1. Before factory/service construction, verify eligibility and source hashes, exact selected IDs, approved references/labels, request/reservation and actual resource bindings. Missing prerequisite stops preparation; do not substitute historical resources.
2. Create an exclusive run directory and atomically synchronize request/setup metadata. Future factory supplies `(verifiers, MeasurementSetup, resource_observer)` for the captured roster.
3. Derive existing `content_id(['offline_attempt_v1', request_id, run_id, verifier_name])`. Await durable `AttemptJournal.start(attempt_id)` before dispatch. A failed acknowledgment prohibits the call.
4. Future authorized dispatch uses the unchanged q/a/reference tuple once; preserve original report, canonical result, timings/status and before/after resource observations. Ineligible/unavailable-before-dispatch slots are executed=false with no invented duration/report.
5. Await durable `AttemptJournal.terminal` on the unchanged one-line CollectedAttempt JSON before progress or the next call. On failure stop and retain attempt ID/location.
6. Publish bundle/measurements/report with atomic_write_text. Failed outcomes may fill a slot but do not prove informative coverage or fitting readiness.
7. Resume only into a fresh output directory after strict request/setup/journal-link validation before factory initialization. Preserve completed outcomes and failed outcomes without repeating calls. Started-without-terminal ambiguity blocks automatic retry. Executed missing/interrupted/malformed slots remain incomplete; only never-started missing slots may resume under an approved request. No exactly-once external effect guarantee is claimed.

Typed VerifierUnavailable and VerifierExecutionFailure remain distinct from programming errors. Timeout is failed with timing_status=timeout. Abstention is a returned report; failure/missing/unavailable are not abstentions. Preserve unexpected-error flags and require explicit adapter disposition. External orchestration must demonstrate the same start/completion acknowledgment boundary; database recovery must not initiate verifier retries.

## Owners and remaining gates

| Owner | Remaining work |
|---|---|
| Vasavi / scientific owner | Eligibility decision is resolved. Approve label estimand/mapping, reference serializer, semantic/shared-context risk disposition, analyzer/requirements/capabilities, planning versions/minima/coverage/thresholds/fallback, budgets/losses, attack/suppression, purpose and operational protocol separately. |
| Tabmayee | Implement/validate prerequisite-aware factory/observer, request and reservation binding, exception/timeout/acknowledgment/resume boundary and deployment-platform smoke. No production orchestration change is included here. |
| Raunak / source producers | Supply actual verifier/resource custody and fingerprints; confirm four adapters and reference semantics; supply missing generator/run custody and source transfer evidence. |
| History custodian + Vasavi | Authentic complete History reports/reputation inputs, split/exposure disposition and outcome-free reservation; do not expose Final Test. |
| Samika | No database action for this file-only preparation. Any later separately scoped persistence must be idempotent on acknowledged attempt IDs and reject conflicting duplicates. |

Collection requires resolved input/label/reference, custody/resource, reservation, operational/integration and explicit recording-authorization gates. Fitting additionally requires authentic History and approved planning/budget/loss/dependency/attack settings; fitting-only parameters need not delay raw complete-candidate recording once its own gates are approved. Neither action is authorized here. Deployment validation remains pending; earlier durability evidence is macOS/APFS only, not Windows or end-to-end service validation.

## Non-verifier acceptance commands

Use the isolated environment described in `../environment.md`; set TEST_PYTHON and HF_HOME. Set RESEARCH_V1_ELIGIBILITY_ARCHIVE to the authorized eligibility ZIP and RESEARCH_V1_SOURCE_ARCHIVE to the original source ZIP, outside version control. From repository root:

```sh
"$TEST_PYTHON" docs/research_v1-recording-handoff/validation/probe_imports.py .
RESEARCH_V1_REQUIRE_ELIGIBILITY=1 "$TEST_PYTHON" docs/research_v1-recording-handoff/validation/run_checks.py eligibility
"$TEST_PYTHON" docs/research_v1-recording-handoff/validation/run_checks.py boundaries
"$TEST_PYTHON" docs/research_v1-recording-handoff/validation/run_checks.py filesystem
"$TEST_PYTHON" docs/research_v1-recording-handoff/validation/run_checks.py regression
```

PASS: SCHEMA_IMPORT_PASS; eligibility 32 pass with no skip, boundaries 18 pass, filesystem 27 pass, regression 11 pass. Eligibility checks reject tampered body/sidecar/support/source bytes and duplicates, verify exact scope/source join/verbatim input and preserve approval limits. Without private evidence the archive-dependent tests explicitly skip: that is not sufficient collection acceptance. FAIL: any nonzero exit, mandatory skip, guard violation, accepted corruption, lost tuple/provenance, repeated completed attempt or resource mismatch accepted. Stop; never remove guards or enable fallback. These commands use synthetic adapters only and authorize no live execution.
