# Offline verifier cost calibration

The concrete project adapter, resource preflight and approved-data preparation
commands are documented in [verifier_collection_adapter.md](verifier_collection_adapter.md).
`app.benchmark.project_adapter:create_verifiers` now supplies the real factory;
the completed local campaign and artifact inventory are documented in
[verifier_cost_results.md](verifier_cost_results.md). Empirical files remain local,
outside this commit; the implementation and synthetic tests are tracked.

`mean_attempt_wall_time_ms_v1` is an initial engineering estimator. It uses the
arithmetic mean of every included measured attempt, including exceptions,
timeouts and interruptions. A returned rejection or abstention is a returned call,
not an execution failure. Only a raised `TimeoutError` is classified as a timeout;
opaque provider errors remain failures. No provider price is inferred.

Costs are **milliseconds**, representing an **estimated sum of verifier-attempt
wall times**. They are neither money nor CPU time. Summed attempt times differ
from elapsed request latency during parallel execution. Durations use the existing
benchmark wrapper's monotonic `perf_counter` timer around `verify`, excluding
factory/model construction and recording overhead. In-call lazy initialization
is included. The approved warm-up policy is explicit; excluded warm-ups remain in
the artifact with reasons. The upper summary is nearest-rank p95, the sorted
observation at one-based index `ceil(0.95*n)`. Small samples offer no tail guarantee.
No statistical optimality or representativeness is claimed. Failure rates, sample
mix, host contention and model/cache state can affect these estimates.

## Inputs and producer responsibilities

Copy `docs/verifier_cost_collection.template.json` to `build/collection.json` and
`docs/verifier_cost_calibration.template.json` to `build/calibration-settings.json`.
Both templates intentionally fail validation. Supply approved preparation roles
and dataset IDs, authorization, and the existing outcome-free final-test reservation.
Never include final-test labels, reports, timings, outcomes or outcome file paths.
Collection examples contain `example_id`, `split_identity`, `question_id`, unique
`run_id`, `dataset_id`, `role` (`history` or `development`), `purpose` (`warmup` or
`calibration`), `question`, `answer`, and nullable `context`. They contain no labels.
The content digest uses the existing `[question, answer, reference/context]` convention.
History and development identities must remain separate, even for warm-ups.

The setup contains the existing `ResourceManifest`: implementation/configuration
hashes per verifier, and required model/corpus/index/prompt/service hashes. Include
all other relevant resources too. Include host/hardware, OS, execution/concurrency,
runtime, provider and cache settings in `environment`, dependency versions, exact
Git revision, and a digest of application sources (including dirty files).
These are producer-observed provenance, not authenticated attestations. Secrets
must not appear in metadata. Never hash a guessed model alias as though it were an
observed model version. Setup fingerprint = `content_id(setup.model_dump(mode='json'))`.

`factory` is an explicit `module:function` adapter supplied by the collection
owner. It returns `(verifier_instances, observed_MeasurementSetup)` and must inspect
the actual initialized resources/environment; exact equality with the approved
setup is required before attempts run. No default factory launches the project
models. The CLI executes the supplied factory as trusted local Python code.
Collecting all four project verifiers may initialize embedding/NLI models,
load the corpus/index and call the confidence service. The owner must report
model downloads, RAM/GPU, corpus availability, provider requests/prices and intended
attempt count before authorizing a costly run. The separately authorized completed
campaign is described in the results document; these commands do not authorize a run.

## Commands

Run from the repository root after supplying approved inputs and creating `build/`:

```powershell
.venv/Scripts/python.exe -m app.benchmark.collect_costs build/collection.json --output build/verifier-attempts.json
.venv/Scripts/python.exe -m app.game.offline.calibration build/calibration-settings.json --measurements build/verifier-attempts.json --output build/verifier-costs.json
```

The settings file supplies `required_verifiers`, explicit `include_warmups`, the
same final-test reservation and a nonblank `freeze_record` referencing the custody
freeze witness before final evaluation. `measurements` stays null when passed
separately. Calibration writes only a new file, refuses overwrites, and returns 2
on missing/invalid inputs. Its stdout reports the validation blocker. The artifact
embeds the recorded input, provenance, input digest, costs, counts, duration
summaries and exclusions. Reload recomputes the estimates and content identity.
No fallback costs exist. Incompatible setups must be collected/calibrated separately.

Collection preserves the original verifier exception after writing attempts so
far. Later verifiers have no observations, not invented failure rows. Missing
required measurements block calibration. Use a new output path for a new run;
the collector never retries automatically. A factory failure before attempts
leaves an empty reserved output, not a valid measurement artifact.

The study owner copies `docs/verifier_cost_build_settings.template.json` to
`build/calibrated-build-settings.json` and supplies its values:

```json
{
  "budget_ms": null,
  "resource_weight_per_ms": null,
  "expected_setup_fingerprint": null
}
```

Null values deliberately fail the builder's explicit-setting checks. Budget is in
ms; resource weight is loss per ms. Do not reuse a normalized-unit weight. The
expected fingerprint is the independently approved evaluated environment/setup,
not an instruction to blindly copy an arbitrary artifact's fingerprint.

```powershell
$costSettings = Get-Content build/calibrated-build-settings.json -Raw | ConvertFrom-Json
.venv/Scripts/python.exe -m app.game.offline.build build/policy-input.json --calibration build/verifier-costs.json --budget-ms $costSettings.budget_ms --resource-weight-per-ms $costSettings.resource_weight_per_ms --measurement-setup-fingerprint $costSettings.expected_setup_fingerprint --output-dir build/calibrated-policy
```

The existing complete policy-build specification is still required, with a fresh
unbound context and custody-safe TrainingManifest. With calibration supplied,
`context.attempt_costs`, budget, cost units, and loss resource weight are populated
before context validation; guessed placeholder costs are unnecessary. All other
loss settings and provenance must be supplied. Python callers use
`build(..., calibration=artifact, budget_ms=..., resource_weight_per_ms=...,
expected_setup_fingerprint=...)` with the same checks.

The resource-bound v2 execution contract, recording configuration, required
candidate set, evidence kind, reservation and preparation identities must match.
Calibration observations must match history/development example content/group
keys in the training manifest. The producer must supply recording categories
matching the calibrated context's existing `category_id`; changing costs changes
that identity. Use public `apply_calibration` to prepare the new context/category.
The builder never relabels recordings, clears stale bindings or changes custody
validation. No existing policy is rewritten. All feasible teams and both
aggregation methods still pass through existing enumeration, payoffs and minimax.

Successful output: `build/calibrated-policy/policy.json`, `build-report.json` and
`summary.txt`. The build report references calibration ID, digest, method, units
and freeze record. Costs flow into `PlanningContext.attempt_costs`, so changed
costs change context, matrix and policy identities under existing contracts.
An invalid build writes `missing-inputs.json` and `summary.txt`, with no policy.

## Calibration status and policy limits

One approved local campaign produced a reload-validated four-verifier artifact.
See the results document for the sample-specific estimates, original paths and
digests. Earlier six-example diagnostic observations remain diagnostic and were
not promoted or pooled. Tests use explicitly synthetic measurements.

Calibration does not approve a policy. Budget/resource weight, independent labels,
compatible report recordings and all other scientific settings remain explicit
policy-builder inputs. The cost-only campaign retained no verifier reports or
abstention counts. Existing evidence and analyzer limitations are not repaired.
TrainingManifest support and the offline builder are reviewed dependencies for
loading calibration, not new API/database integration or an empirical policy fit.
