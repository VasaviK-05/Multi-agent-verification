# Cost Measurement Protocol

## 1. Purpose and scope

This protocol defines how verifier timing and cost measurements are to be established and used for the final research experiment. It distinguishes three different objects:

- **Historical timing evidence:** measurements already recorded for earlier workloads and setups.
- **Planning cost estimates:** frozen offline estimates used by a planning context or policy build.
- **Actual evaluation durations:** durations observed while running the final evaluation, retained for reporting and later analysis.

These objects have different provenance and purposes. Later evaluation observations must not silently replace or mutate frozen planning estimates. This document specifies a procedure; it does not create new measurements or establish that historical measurements apply to the final benchmark.

## 2. Existing timing and cost evidence

The repository has both benchmark/offline timing infrastructure and historical measurements. The estimates below are quoted only where repository reports provide the values. Historical artifacts must be assessed against the final experiment's configuration and workload before reuse.

| Evidence source | Measurement type | Workload/configuration | Sample information | Evidence category | Usability |
|---|---|---|---|---|---|
| `artifacts/capability-probes-v1/timings-summary.json` and `artifacts/capability-probes-v1/collection/collection-report.json` | Per-verifier duration summaries; report says abstentions and failures are included | Smoke collection, intended use `smoke`; report records 96 calls, with 24 per verifier in the summary | 24 attempts per verifier; mean and nearest-rank p95 provided | Historical measurement/calibration artifact (empirical smoke collection) | **Historical/reference evidence only**; not calibrated for the final workload. The collection report records a smoke purpose and no study approval. |
| `docs/verifier_cost_results.md` and `docs/verifier_cost_artifacts.local.json` | `mean_attempt_wall_time_ms_v1` cost-only campaign and frozen local calibration metadata | Arithmetic-heavy local sample (80 arithmetic, six factual); observed local setup; first-call effects included | 344 attempts, 86 per verifier; report gives mean, median and nearest-rank p95 | Historical measurement/calibration artifact | **Historical/reference evidence only**. The report says the empirical bundle is local/ignored, and its measured source tree/setup do not match the reviewed revision. Do not bind it to a changed setup. |
| `docs/compound_reference_fitting_verification_20261105.md` | Costs used/reported in retained Reference and Compound fitting/evaluation | Study-specific policy, recorded workload, configuration, and reserved-call evidence described in that report | Reported fitting/reserved counts and means are specific to those studies | Recorded replay/frozen evaluation | **Historical/reference evidence only** for the final benchmark. A study's planning costs or reserved observations do not establish a new benchmark's cost distribution. |
| `artifacts/remaining-category-studies-v1/`, `artifacts/compound-study-36-v1/`, and `artifacts/compound-empirical-v2/` where timing/attempt records are present | Recorded attempt outcomes and, in some records, durations | Package/study-specific runs | Counts vary by artifact; consult the linked report/manifest for each run | Recorded replay/frozen evaluation | **Must be re-measured for final experiment** unless a specific record passes the compatibility decision in §9. Do not pool packages or runs based on shared verifier names alone. |
| `artifacts/flexible-heldout-v1/` collection reports/records | Held-out execution records, including recorded attempts | Explicitly marked held-out partitions | Collection reports identify 160 calls for each of arithmetic and factual | Recorded replay/frozen evaluation | **Must not be used to fit planning estimates**. Preserve held-out status; use only for its authorized evaluation/reporting purpose. |
| `app/game/offline/timing.py`, `app/game/offline/calibration.py`, `app/game/offline/collection.py`, `app/benchmark/collect_costs.py` | Timing, provenance, and offline calibration mechanisms | Supports labeled history/development preparation and held-out recording contracts | Mechanism only; it does not imply a current final-benchmark measurement set | Focused unit/contract test (implementation contract; tests are not run for this task) | **Usable now** as protocol infrastructure, subject to its explicit setup, authorization, and split checks. |
| `app/orchestration/validation_orchestrator.py` game execution journal and `app/database/verifier_cost_repository.py` | Runtime attempt journaling and cost persistence mechanisms | Runtime execution and persisted cost measurement/estimate identities | Mechanism/schema evidence, not new timing data | Persistence/schema evidence | **Usable now** for the supported runtime recording path where enabled; it does not establish that a final benchmark has been measured. |

The smoke timing summary reports these values (ms): Semantic mean 47.66354167562289, p95 75.76390006579459; Evidence mean 138.56010832629786, p95 351.09749995172024; Rule mean 0.6020124807643393, p95 3.1720998231321573; Confidence mean 15222.821108298376, p95 21616.66060006246. The report says 24 attempts per verifier and that abstentions/failures are included. These are historical smoke figures, not final-benchmark estimates.

The separate local cost campaign in `docs/verifier_cost_results.md` reports 86 attempts per verifier and mean/median/p95 in milliseconds: Semantic 30.955616/28.301850/39.269800; Evidence 42.124591/23.433650/147.836000; Rule 0.132202/0.082050/0.161200; Confidence 11831.109355/11469.350850/12696.482000. This collector did not retain verifier reports or abstention counts. Its returned-call status does not establish judgment correctness or rule out internally handled provider errors. These values describe only the reported arithmetic-heavy sample and local setup.

The cost campaign's calibration ID, input digest, setup fingerprint, file hashes, measured revision, and dirty-source digest are documented in `docs/verifier_cost_results.md`. The report explicitly says the measured tree differs from the reviewed commit and the empirical bundle is not pushed. Those identities are historical provenance, not values to copy into a new run.

## 3. Measurement identity and provenance

Every final-experiment measurement record must be traceable to a unique run and attempt, and must carry or link to the following identities. “Required by protocol” means it must be recorded for the final experiment; it does not mean every historical record contains the field.

| Identity/provenance | Repository support | Final-experiment requirement |
|---|---|---|
| Run/measurement ID and attempt ID | Offline recording uses `run_id` and deterministic attempt identities; persisted attempts use run and attempt identities | Required; unique within the recorded experiment and linked to the source run. |
| Verifier identity and implementation/configuration fingerprint | `ResourceManifest`, `MeasurementSetup`, and cost persistence support verifier identities/configuration | Required for each verifier, including implementation/configuration identity. |
| Model/service and prompt/configuration identity | Resource manifests support model/service/prompt hashes and service metadata where observed | Required when applicable. Record observed identities; do not substitute a guessed model alias for a verified model identity. |
| Runtime/policy mode and team/binding | Execution records/journals carry verifier/component/binding context where applicable; game contracts identify policy/runtime configuration | Required to identify baseline/game mode and the selected policy/team/bindings for evaluation attempts. |
| Resource/corpus/index identity | `ResourceManifest` and runtime compatibility checks bind resource identities | Required for applicable corpus/index/model/service resources and manifest identity. |
| Hardware/environment and dependencies | `MeasurementSetup.environment` and `dependency_versions`; persistence setup schema includes host/runtime/concurrency/cache fields | Required as observed provenance, with no credentials or secrets. Machine-local values should be clearly labeled as such. |
| Source revision and source digest | `MeasurementSetup` requires a code revision and application-source digest | Required, including dirty source changes if any; do not identify a dirty tree by commit alone. |
| Dataset, benchmark scope, group, and split | Offline measurement inputs identify dataset, role, split, question/content identity; final-test reservation is explicit | Required; final-test observations are evaluation records and never calibration inputs. |
| Timestamp | Database persistence has `recorded_at`; offline `AttemptMeasurement` does not define a timestamp field | Required by this protocol for final-run records, either directly or through an immutable run manifest. Do not imply it exists in every offline measurement artifact. |
| Outcome/status | Offline timing uses `returned`, `failure`, `timeout`, `interrupted`; runtime persistence distinguishes completed, unavailable, and failed attempts | Required, with the applicable schema's terminology preserved. |

## 4. What counts as verifier-attempt duration

### Verifier-attempt duration

For calibration, use elapsed monotonic wall time around one invocation of the configured verifier's `verify` call. `app/game/offline/timing.py` implements this boundary with `time.perf_counter()`. It records a duration in a `finally` block and preserves the returned value or raised exception. The measured interval includes work performed inside `verify`, including lazy initialization that occurs inside the call.

### Model/service construction or initialization

Factory construction and eager model/service initialization performed before `verify` are outside the `TimedVerifier` interval. Record startup/initialization duration separately when measuring it; do not add it to per-attempt duration. If a service initializes lazily during `verify`, that work is part of that attempt and should be identified as a cold/in-call condition in the run metadata where known.

### Resource/index preparation and hashing

Resource loading, index construction/loading, manifest checks, hashing, compatibility/preflight, and service metadata inspection are preparation measurements, not verifier-attempt duration, when they occur outside `verify`. Record them separately if relevant to the experiment. The adapter's setup inspection/preflight is not the verifier timer. Do not silently charge one-time preparation to every attempt or omit it from total setup reporting.

### Orchestration overhead

Selection, question routing, policy/team sampling, binding checks, coverage checks, aggregation/finalization, persistence, and audit work are not included in the offline `TimedVerifier` boundary. The game execution journal starts an attempt timer at the runtime attempt boundary and records duration on completion/unavailable/failure; report this as the runtime journal's attempt duration and keep its provenance/schema distinct from offline calibration measurements. Where the runtime attempt boundary includes dispatch/callback overhead, do not equate it automatically with the offline wrapper interval.

### Total request latency

End-to-end API/request latency is a separate metric, measured from a clearly declared request boundary through response completion. It can include routing, multiple verifier calls, concurrency, aggregation, database/audit work, and service initialization depending on deployment lifecycle. It is not equal to the sum of verifier costs in general, particularly under concurrent execution. Report it separately if the experiment studies it.

## 5. Warm-up procedure

For the final experiment, define and execute an explicit warm-up phase for each measured verifier/service configuration when warm-up is appropriate to the deployed runtime. Mark every such run with purpose `warmup`, preserve its attempts and statuses, and summarize warm-up observations separately from calibration and final evaluation observations.

Warm-up count and stopping rule must be set before collection and reported with the protocol/run manifest; this document does not prescribe a historical count because the repository's calibration interface takes an explicit `include_warmups` choice and existing reports document different procedures. Do not infer that warm-ups occurred unless the run records show them. By default, warm-up observations are excluded from planning estimates (`include_warmups: false` in the calibration template); if the experiment chooses otherwise, make that choice explicit before fitting and retain the included/excluded identities and rationale. Warm-up runs must not use final-test outcomes.

## 6. Successful attempts

Record each successful verifier invocation with its attempt/run identity, start/end or monotonic duration, verifier and configuration/resource identities, timestamp, status, and applicable validation/report/coverage linkage. In the offline schema, a returned result has timing status `returned`; returned rejection or abstention is still a returned execution, not an execution failure. Where a runtime journal stores a report validation ID, component ID, binding ID, or call ID, retain those links.

A successful attempt is eligible for a planning estimate only if it belongs to the pre-approved calibration population and matching setup, meets the split/reservation contract, and is not excluded by the frozen warm-up policy. The existing estimator can include durations for non-returned attempts too; see §7 and §10. Eligibility must follow the declared estimator and data policy, not a post hoc selection based on favorable timing or judgment outcome.

## 7. Failed attempts and timeouts

Record and report separately:

- **Execution failure:** an invocation raised an exception other than `TimeoutError`; offline status is `failure`.
- **Timeout:** an invocation raised `TimeoutError`; offline status is `timeout`.
- **Interrupted:** the wrapper began but did not observe a normal return or caught exception before its `finally` completed; offline status is `interrupted`. A process termination that bypasses recording may leave no row and must be disclosed as missing/incomplete data, not fabricated as a measured zero.
- **Unavailable/resource/service failure:** where no verifier invocation occurs because a prerequisite, resource, or service is unavailable, preserve the runtime/collection status (for example, `unavailable` or a non-executed attempt). Do not invent a verifier duration for work that did not execute. Record preflight/resource failures as operational outcomes with any separately measured preparation time.
- **Compatibility/preflight failure:** record the failed check, resource/configuration identity, and whether invocation began. It is not a successful verifier-attempt observation if `verify` was never called.
- **Uncertain/abstaining judgment:** if the verifier returned an uncertainty or abstention result, it is a returned execution and its duration remains a returned-attempt timing observation. Judgment outcome and execution status are separate fields.

Failures and timeouts must not be silently discarded. Report their counts and durations/statuses. For a successful-only descriptive estimate, non-returned attempts do not qualify as successful observations; however the repository's `mean_attempt_wall_time_ms_v1` explicitly computes over every included measurement, including failures, timeouts, and interruptions. A final experiment must declare which estimand it uses before calibration. If using the existing method, retain its inclusion behavior and report failure rates alongside the estimate. Operational rates remain reportable even when an event has no valid duration.

## 8. Sample counts and timing summaries

For each verifier/configuration/resource combination, report at minimum:

- number of attempted runs;
- number of successful returned attempts;
- number of failures, timeouts, interruptions, and unavailable/preflight outcomes, with categories not collapsed;
- number of warm-up attempts and number excluded from estimation;
- number of attempts with missing or invalid timing data;
- workload, split, and run identities and any exclusions.

Report the estimator and units. The repository calibration implementation supports arithmetic mean, median, nearest-rank p95, attempt count, and failure count. A report may additionally present minimum/maximum, dispersion, or other percentiles if the final analysis defines and computes them; this protocol does not claim current code computes those summaries. For small samples, state the sample size and avoid implying reliable tail-latency characterization. Separate successful-only summaries from all-attempt summaries if both are presented.

## 9. Compatibility of historical measurements

Reuse requires a documented match, not merely the same verifier name. Compare at least:

- verifier implementation, model/service, prompt, and configuration identity;
- resource manifest and corpus/index identity;
- hardware, runtime, dependencies, concurrency, and cache conditions;
- workload/question and answer distribution, dataset, groups, and split role;
- baseline/game mode, policy/team/binding where applicable;
- warm-up policy and cold/warm state;
- exact timing boundary and estimator/status inclusion rules;
- source revision/source digest and measurement provenance.

### Usable now

The collector, `TimedVerifier`, setup fingerprint checks, split guards, calibration artifact identity checks, and persistence schemas are reusable as mechanisms. A historical measurement is usable as a planning input only if its full setup, workload role, authorization, data split, warm-up handling, timer boundary, and required identities satisfy the final experiment's predeclared protocol. No inspected historical report establishes that complete match for the not-yet-final benchmark.

### Usable only as historical/reference evidence

The capability-probe smoke summary, the October local cost campaign, and the retained Reference/Compound study timing/cost reports establish that measurements and estimates were previously recorded for their stated workloads and configurations. They can inform planning discussion and protocol choices, but they do not establish final-benchmark costs. The October local bundle is not present as a portable tracked empirical bundle, and its measured source tree/setup differ from the reviewed checkout.

### Must be re-measured for the final experiment

Re-measure when verifier/model/service or prompt configuration changes; resources, corpus, or index change; hardware/runtime/concurrency/cache conditions materially differ; benchmark workload or split population differs; runtime mode/team bindings differ; warm-up/timer/status methodology differs; or the historical provenance is incomplete. Final-test observations must not be used to fit planning estimates. The existing held-out records remain held out.

## 10. Freezing planning cost estimates

Use a predeclared, authorized history/development measurement dataset and the final-test reservation contract. Select the eligible rows by run identity, dataset/split, setup fingerprint, verifier set, warm-up rule, and estimator before looking at final-test outcomes. Offline collection rejects final-test reservation overlap and verifies observed setup against expected setup; calibration rechecks measurement provenance against the training manifest and reservation.

The current offline vocabulary is `MeasurementSetup`, `MeasurementInput`, `AttemptMeasurement`, `CalibrationRequest`, `CalibrationArtifact`, `calibration_id`, and `input_digest`. Setup identity includes a resource manifest, environment/dependency records, source revision/digest, and evidence kind. The calibration artifact recomputes its result and content identity when loaded. `apply_calibration` requires the independently expected setup fingerprint, exact candidate set, compatible resource manifest/execution configuration, matching evidence kind, and a fresh unbound planning context. The build report records calibration identity/digest, estimator, units, and freeze record.

Freeze the selected measurement bundle, calibration request, estimator and status/warm-up inclusion rules, setup fingerprint, input digest, resulting calibration identity, and custody/freeze record as immutable versioned artifacts before final evaluation. A change in measurements or method creates a new calibration identity and planning context; it must not overwrite the prior frozen estimate. Database persistence uses separate identities: a persisted estimate row/UUID is associated with calibration ID and input digest, setup ID, estimator version, source attempt IDs, and estimate values. Do not assume that a persistence row ID, calibration ID, content digest, or setup fingerprint are interchangeable.

The existing `mean_attempt_wall_time_ms_v1` estimator is the arithmetic mean of every included attempt, including failures, timeouts, and interruptions; warm-ups are included or excluded only by the explicit request flag. Its mean is an engineering planning estimate, not money, CPU time, request latency, or a statistical guarantee. Do not change estimator behavior silently. If the research protocol requires a different inclusion rule or estimator, name and version it and freeze it explicitly.

## 11. Recording actual evaluation durations

During evaluation, record actual durations and outcomes using the runtime attempt journal and/or the approved evaluation recorder where those paths apply. Preserve each duration's run, verifier, configuration/resource, policy/team, dataset/split, and status provenance. Keep estimated planning cost and actual observed duration as separate fields/records; the orchestrator journal itself carries both `estimated_cost` and observed `duration_ms` for game attempts.

Actual evaluation observations may be summarized for the reported experiment and retained for later analysis. They must not silently update the frozen planning estimate or policy. Any recalibration requires an explicit new measurement population, versioned estimator/calibration artifact, setup and input identities, authorization, and a new freeze record. Final-test observations remain evaluation-only and cannot be retroactively moved into calibration.

## 12. Final experiment readiness checklist

### Already available

- Offline timing wrapper with monotonic duration and returned/failure/timeout/interrupted statuses (`app/game/offline/timing.py`).
- Collection/calibration schemas with setup, verifier/configuration, run, dataset/split, purpose, reservation, and content identity checks (`app/game/offline/collection.py`, `app/game/offline/calibration.py`, `app/benchmark/collect_costs.py`).
- Versioned calibration artifacts and setup compatibility checks; build reports can retain calibration/freeze provenance.
- Runtime game attempt journal stores observed duration separately from estimated cost; persistence schemas support attempt and estimate provenance.
- Historical smoke and cost campaign summaries and study-specific timing evidence described in §2.

### Can be prepared independently now

- Adopt the timer boundary, status vocabulary mapping, warm-up declaration, reporting table, and provenance checklist for the experiment.
- Prepare versioned run/calibration manifests and the reporting template without collecting new timing data.
- Review that runtime actual-duration fields and offline calibration artifacts remain separate in the final report.

### Blocked or pending

#### Person 1 dependencies

- Final benchmark scope, dataset identity, question groups/workload distribution, and development/final-test split and reservation identities are needed to select calibration-eligible examples and define the workload represented by estimates.
- Corpus/index decisions determine applicable resource identity and may require resource compatibility checks before calibration.

#### Person 3 dependencies

- Final experimental policies and matched baselines determine the verifier set, team/binding configuration, runtime mode, and whether each planning estimate covers the actual candidate set. Policy fitting/finalization must consume only eligible preparation measurements and preserve the frozen estimate identity.

## 13. Evidence inventory

| Evidence | Type | Source/path | What it establishes | Limitation | Final-experiment usability |
|---|---|---|---|---|---|
| Capability probe timings | Historical measurement/calibration artifact | `artifacts/capability-probes-v1/timings-summary.json`; `artifacts/capability-probes-v1/collection/collection-report.json` | Smoke timing summaries, 24 attempts per verifier, mean/p95 and inclusion of abstentions/failures; collection report says 96 calls and intended use smoke | Smoke purpose, no study approval; not final benchmark workload or setup | Historical/reference evidence only; remeasure for final estimates unless full compatibility is separately demonstrated. |
| October cost campaign summary | Historical measurement/calibration artifact | `docs/verifier_cost_results.md`; `docs/verifier_cost_artifacts.local.json`; local run cited there at `build/verifier-cost-calibration-proposal-20261028-v2/run-20261028-01/` | Reported 344 attempts and frozen calibration/setup/input/file identities for a local arithmetic-heavy campaign | Empirical bundle is local/ignored, no retained reports/abstention counts, and measured tree/setup differ from reviewed checkout | Historical/reference evidence only; do not bind to current/final setup. |
| Study-specific timing/cost records | Recorded replay/frozen evaluation | `docs/compound_reference_fitting_verification_20261105.md`; relevant files under `artifacts/compound-study-36-v1/` and `artifacts/remaining-category-studies-v1/` | Costs and timings used/reported for named retained studies and their reserved executions | Study-specific workload/policy/resources; not a general or future-benchmark estimate | Historical/reference evidence; remeasure if final experiment differs. |
| Held-out collections | Recorded replay/frozen evaluation | `artifacts/flexible-heldout-v1/` | Held-out records and collection counts for their declared partitions | Held-out data cannot be used to fit planning estimates; not evidence for a different final workload | Evaluation/reporting only under its reservation; never calibration input. |
| Timer and calibration contract | Focused unit/contract test | `app/game/offline/timing.py`; `app/game/offline/calibration.py`; `tests/test_cost_calibration.py` | Code/test contracts for timer status, calibration identity, setup and estimate behavior | Tests and code contracts do not constitute native measurements; tests were not run for this task | Reusable mechanism; final empirical measurements still required where compatibility is unproven. |
| Runtime attempt journal | Persistence/schema evidence | `app/orchestration/validation_orchestrator.py`; `app/database/verifier_cost_repository.py` | Runtime journal captures observed attempt duration and estimated cost separately; repository implements cost persistence identities | Mechanism is not proof of successful persistence for a future run or equivalence to offline timer | Usable for actual runtime reporting when enabled and validated for the final configuration. |
| Cost measurement schema | Persistence/schema evidence | `db/migrations/005_verifier_cost_measurements.sql`; relevant follow-up migration under `db/migrations/` | Declared persistence fields for setup, attempts, outcomes, warm-up/purpose, calibration and estimates | Schema does not establish that a database was accessed or data collected in this task | Usable schema contract; final persistence behavior must be established in its authorized environment. |
