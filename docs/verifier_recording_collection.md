# Offline verifier report collection

The replay-ready collector is `python -m app.game.offline.collect`. It collects
detached reports and measured call timings without selecting a policy team, running
the decision engine, updating reputation, or calling DB/API/persistence interfaces.
Collection does not require a budget, loss weights, decision threshold, minimum team
size or reputation prior. No proposed scientific settings were adopted.

The separately authorized cost-only campaign is documented in
[verifier_cost_results.md](verifier_cost_results.md); its empirical files remain
local. It used `app.benchmark.collect_costs`, not this labelled report collector.

`DiagnosticRecordingRequest` is a separately versioned label-free smoke path.
It accepts an unwitnessed metadata-only exclusion roster, requires absent labels
and study approval, and cannot export calibration measurements or training data.
Execution permission never promotes a diagnostic bundle. Standard RecordingRequest
can retain reports and calibration inputs from the same calls when genuine label,
reservation and preparation contracts are satisfied. The existing label-free
cost-only path retains timings/statuses, but not reports or abstention counts.

## Input and adapter contracts

Start with `docs/verifier_recording_collection.template.json`. Null required fields
and the empty permitted-dataset list deliberately fail validation. The schema is
`app.game.offline.collection.RecordingRequest.model_json_schema()`.

Supply explicit history/development examples, related-question/group identities,
unique run IDs, dataset permissions, the existing metadata-only final reservation,
and independent labels. Each label includes strict boolean `answer_is_correct`,
supported `label_method`, nonblank `label_source`, and nonblank provenance. Labels
remain in a separate request branch and are never passed to verify(). No framework
decision is used as truth. `analysis` is the existing QuestionAnalysis dataclass,
supplied by the producer; the collector does not infer a population or run an analyzer.

Each candidate declares registration, an existing adapter label, CapabilityDescriptor,
and its explicit/builtin source. Builtin descriptors must equal BUILTIN_CAPABILITIES.
The collector captures requirement_inputs and prerequisite_status directly, including
missing-reference and unavailable results. Unknown readiness has the same semantics
as the existing selector. Every registered eligible candidate executes exactly once
per example; no sampled team, early stop, fallback or retry is used. Ineligible or
missing factory candidates get explicit unavailable outcomes without fake reports or
zero-duration measurements. Expected capabilities are not counted as achieved;
factual_capabilities recognizes only certificates actually present in returned reports.

`cache_contract=complete_team_independent_v1` is a producer attestation required for
counterfactual replay. The collector cannot authenticate statelessness or source claims.
`randomness_control` must state the actual adapter seed/control or its absence; it does
not pretend to seed opaque models. Stable request and attempt IDs bind the configuration,
example and candidate; output bundle IDs also include actual reports/timings and will
usually differ across repeated runs.

Factory protocol: a trusted local `module:function` returns
`(verifier_instances, observed_MeasurementSetup, observer)`. The observer's `snapshot()`
returns an actually observed ResourceManifest. Before and after each executed call,
the collector checks the manifest against the factory-observed setup. Observation
overhead and initialization are excluded from the verify-call timer. The exact
existing benchmark timer was moved to `app.game.offline.timing.TimedVerifier`; the
benchmark retains its `_TimedVerifier` alias and behavior.

The execution configuration ID must equal the observed resource-manifest ID. Each
canonical Attempt preserves the full VerificationResult, metadata, score/confidence,
execution ID, adapter and observed verifier resources. A sidecar retains raw returned
payload JSON, achieved factual capabilities, planning/prerequisite audit, post-call
observations, duration and the linked AttemptMeasurement. Resource fingerprints are
supplied by actual observations, never hashes of a guessed model alias.

Old two-value factories can collect reports but have no per-attempt observer: outputs
are explicitly incomplete and cannot be exported for replay or verified calibration.
Similarly, `expected_setup=null` means resources have not been predeclared, not that
unknown identities are invented; an actual factory setup and matching observations
are still needed for usable exports. With no actual setup, raw reports/durations can
be retained but completeness fails. A declared expected setup must match the factory
before any verifier call. No observed resources are substituted for missing ones.

## Existing project adapter bridge

The concurrent local project adapter/preparation work is preserved. To use its
existing local-only constructors and resource observers, set the reviewed adapter
configuration and use the recording bridge as the request's factory:

```powershell
$env:VERIFIER_COLLECTION_ADAPTER_CONFIG = (Resolve-Path build/adapter.local.json).Path
# request.factory = "app.game.offline.recording_adapters:project_factory"
```

This bridge calls the existing project factory, inspect_setup and observe_service.
Resource snapshots hash actual local files and verify live loopback service metadata;
hashing large snapshots can be expensive and is outside the attempt timer. See
`docs/verifier_collection_adapter.md` for prerequisite preflight, local snapshot/index
receipts, service metadata, provider request counts and model/RAM considerations.
No downloads, index rebuilding, upstream algorithm repair or configuration guessing
is added by this collector. The rule-only `rule_factory` is also available, with the
same three-value protocol and actual source/configuration observations.

## Validate, collect, check and recover

After supplying approved preparation data and the reviewed factory/setup:

```powershell
.venv/Scripts/python.exe -m app.game.offline.collect validate build/recording-request.json
.venv/Scripts/python.exe -m app.game.offline.collect collect build/recording-request.json --output-dir build/recordings
.venv/Scripts/python.exe -m app.game.offline.collect check build/recordings
```

Validation checks split separation and reservation overlap before importing the
factory. It reads no final payload and follows no final outcome paths. The factory
is trusted executable local code and must not independently access held-out storage.
Use a new output directory: existing files are not overwritten. Outputs are:

- `request.json`: separately labelled input/configuration and reservation metadata.
- `observed-setup.json`: actual factory-observed setup (or explicit null).
- `attempts.jsonl`: flushed append-only per-candidate audit journal.
- `recordings.json`: validated RecordingBundle, retaining every input example.
- `measurements.json`: existing MeasurementInput format, only when every executed
  timing has verified pre/post resource observations and a real setup.
- `collection-report.json`: completeness/gap reasons and stable request/bundle IDs.

`check build/recordings` reconstructs from request/setup/journal even after an interrupted
run. No factory or verifier executes during checking. A missing row remains a gap;
partial journal writes reject rather than silently disappearing. Callers may also
check an explicitly named recordings.json. Canonical links and achieved capabilities
are revalidated on load. Hashes check consistency, not authentic provenance.

VerifierUnavailable, explicit VerifierExecutionFailure and raised TimeoutError are
recorded as genuine unavailable/failed outcomes and collection continues to later
candidates. Type/message and measured status remain in the audit; failed calls are
included in calibration data. Generic exceptions are retained as failed outcomes
but block training export pending adapter review, preserving production's distinction
between expected execution failure and programming/configuration errors. Invalid
returned reports become explicit missing recordings with their returned payload and
validation issue. KeyboardInterrupt preserves its measured interrupted attempt and
marks later candidates unattempted/missing. The collector does not kill background
threads or impose a new timeout: timeout enforcement belongs to existing adapters.
Factory/initialization failures save the request and a blocked report before exit.

Completeness is a recording-consistency gate, not scientific approval. Study requests
require a nonblank study_approval reference; pilot and smoke results stay labelled.
Smoke bundles cannot be promoted to training. Warmups remain in raw/calibration
provenance and are not silently converted into history/development training examples.
Use a separate approved non-warmup request for training data.

## Calibration and first training export

The collector's measurements share run/example/candidate identities with its reports.
The shared measurement schema validates setup/resource fingerprints and disjoint
preparation identities. There are no durations for candidates skipped by prerequisites.
If a required candidate was never actually measured, calibrate rejects it; obtain
approved preparation examples on which that candidate can execute instead of inventing
a zero cost. No difficult or failed example is silently dropped to achieve completeness.

```powershell
.venv/Scripts/python.exe -m app.game.offline.calibration build/calibration-settings.json --measurements build/recordings/measurements.json --output build/verifier-costs.json
```

`calibration-settings.json` follows the existing CalibrationRequest template: explicitly
approve required_verifiers, include_warmups, the identical final reservation and a
freeze_record; leave measurements null when supplying --measurements. The calibration
artifact retains measured failures and source observations. No cost weight/budget is
required merely to estimate durations.

Once the study owner supplies a frozen history-derived snapshot and explicit fitting
settings, export raw reports for the first time against a fresh unbound PlanningContext:

```powershell
.venv/Scripts/python.exe -m app.game.offline.collect export build/recordings --context build/approved-context.json --output build/training-manifest.json
```

This creates existing Partition/Example/Attempt and TrainingManifest objects. It checks
domain, analysis/difficulty/version, requirement signature, candidate capabilities,
prerequisites, eligibility, references, resources and any execution-contract binding
against collection. It assigns category_id(context) only during this initial export.
No old Example category or evaluated binding is rewritten. Mixed categories reject
instead of silently dropping rows; collect/export separate category cohorts. Both
history and development must be present in one complete non-warmup bundle. The full
label-provenance audit stays in the raw bundle; exported labels retain their source
and method, and Attempt provenance links back to the original request digest.

The existing concurrent calibrated-context helper can populate actual costs without
placeholders before that first export and additionally validate history/resources:

```powershell
.venv/Scripts/python.exe -m app.game.offline.prepare_calibrated_context build/collected-context-input.json --collection-bundle build/recordings/recordings.json --calibration build/verifier-costs.json --settings build/calibrated-build-settings.json --output build/calibrated-training-inputs.json
$prepared = Get-Content build/calibrated-training-inputs.json -Raw | ConvertFrom-Json
$spec = Get-Content build/approved-policy-settings.json -Raw | ConvertFrom-Json
$spec.context = $prepared.context
$spec.manifest = $prepared.manifest
$spec | ConvertTo-Json -Depth 100 | Set-Content build/policy-input.json -Encoding utf8
$s = Get-Content build/calibrated-build-settings.json -Raw | ConvertFrom-Json
.venv/Scripts/python.exe -m app.game.offline.build build/policy-input.json --calibration build/verifier-costs.json --budget-ms $s.budget_ms --resource-weight-per-ms $s.resource_weight_per_ms --measurement-setup-fingerprint $s.expected_setup_fingerprint --output-dir build/empirical-policy
```

The named completed inputs do not yet exist. Start with the corresponding incomplete
templates and obtain actual values from their owners. The builder still validates
history-only reputation, all-candidate resources, scientific readiness and the existing
evidence defects. This collector does not approve a study or bypass those gates.

## Required choices and unapproved pilot suggestions

- `intended_use`: no approved value exists. Suggested `pilot` for initial labelled
  preparation runs; it accurately limits the claim. Affects collection/export marking.
- `purpose`: existing measurement schema allows `warmup`/`calibration`. Suggested
  `calibration` for measured training-eligible examples, with any warmups in a separate
  request. No warmup count/inclusion rule is assumed. Affects collection/calibration.
- `randomness_control`: no study seed exists. Suggested explicit statement of actual
  deterministic behavior or uncontrolled adapter randomness. A seed must only be
  claimed if the underlying adapter supports/applies it. Affects collection provenance.
- Adapter provider timeout/sample controls: current project AdapterConfiguration has
  timeout=60 seconds, n_samples=5 and temperature=0.8. If that adapter is chosen,
  proposed pilot values are those existing values to avoid an unrelated behavior
  change; resource/request counts still need review. They are not adopted by the
  report collector or changed in vote normalization. Affects collection cost/outputs.
- Independent labels, partition/group membership, preparation permission, reservation
  and observed resource setup have **no safe guessed values**; their owners must
  supply actual data before labelled collection can run.
- Losses, thresholds, budget/units/resource weight, minimum team size, reputation
  priors and confirmatory evaluation/uncertainty settings are fitting/evaluation
  decisions. No proposed value is required or silently used for report collection.

## Real local smoke and limitations

The real, model-free RuleVerifier was invoked on an ad hoc question with no independent
label or study partition claims:

```powershell
.venv/Scripts/python.exe -m app.game.offline.recording_adapters --question "What is 2 + 2?" --answer "4" --output build/recording-rule-smoke.json
```

It returned its actual arithmetic SUPPORT report and measured duration with observed
source/configuration fingerprints and unchanged resources. This smoke command cannot
create a TrainingManifest. The output explicitly says independently_labelled=false
and suitable_for_fitting=false. It is not an empirical study corpus, calibrated cost
table or policy. No reserved data, model download, provider call or DB/API was used.
No labelled empirical history/development collection or empirical policy was produced.

The known evidence/public-coverage defects and absent approved study inputs remain
separate blockers. They were not exercised by the rule-only smoke or repaired here.

## Validation record

The affected collector/benchmark/calibration/builder/offline run passed 124 tests.
The collector plus existing project-adapter run passed 50 tests. The final focused
collector run passed 22 tests, including additional timing/observation integrity,
final isolation and project-bridge checks. These runs overlap; their totals must
not be added. No failures were encountered or classified as baseline failures in
these runs. The invalid recording template rejects as intended before factory work.
Exact commands and changed paths are recorded in build/verifier-recording-validation.json.
Git diff whitespace checks passed. The full repository suite and live project-model
collection were not run. No DB/API, schema, persistence, verifier, retrieval or generation
files were changed; existing concurrent adapter/calibration/builder work was preserved.
