# Labelled arithmetic pilot: preparation record and approved fit

The user subsequently approved the complete configuration and the pilot policy was
fitted without changing its digest or recalibrating. See
[approved fit results](arithmetic_pilot42_fit.md). The selected policy has zero
development decision coverage; no final-test payload was opened or evaluated.
The original proposal file remains unchanged. The remainder of this document records
the earlier preparation/proposal stage and its then-pending approval.

The authorized engineering pilot completed **160 real verifier calls**: 80 rule and
80 semantic. All 160 returned valid directional reports, with zero execution failures,
timeouts, unavailable outcomes, unknown resource observations or incomplete records.
The existing completeness check passed and a reload-validated calibration artifact
was produced. **At that preparation stage, no policy had yet been fitted and no
optimizer, final-test collection or evaluation had run.** This pilot supplies no
research-improvement claim.

## Origin, independent labels and holdout

No locally available benchmark had suitable arithmetic examples with documented label
provenance, so the user-authorized constructed fallback was used. Version
`constructed_arithmetic_fraction_v1` creates 60 distinct one-operation groups: 15 each
of addition, subtraction, multiplication and division. Every group has one correct
candidate and one substantive incorrect answer exactly 1 greater than the correct
value. The negative is not a formatting variation.

Correctness is calculated with stdlib fractions.Fraction and an independent exact
long-division formatter. The framework's RuleVerifier uses its own Decimal checks;
neither verifier reports nor framework final decisions establish these labels.
Per-example provenance stores operands, operator, expected/candidate rational values,
the equality check, method/version and stable identities.

Seed 42 shuffles whole question groups: 20 history groups/40 candidates, 20 development
groups/40 candidates, and 20 reserved final groups/40 candidates. Both variants stay
in the same group, question identity and partition. The existing heuristic analyzer
classifies these as easy arithmetic in the general/unknown domain; that metadata was
not relabelled to permit smaller teams.

Fitting/collection inputs contain only the 80 history/development examples and the
existing metadata-only FinalTestReservation. Final labels and answer variants are in
`build/arithmetic-pilot42/custody/final-examples.jsonl`, outside those inputs. The
workflow constructed that file, so this is **procedural holdout, not independent
third-party custody**. The generator is deterministic and can reconstruct examples;
file separation is not access control or a claim of third-party blinding.

Reservation ID: `a4b582931905305695d3b64a435e978fa8e7b28b766e682786d144b9e720915c`.
No final verifier outputs were collected. Proposal preparation ran with an executable
guard that rejects opening the final-label file and a second guard that rejects LP
optimizer calls; both passed. Their evidence is `proposal-isolation-check.json`.

## Genuine resources and applicability

The full existing project-adapter preflight still rejects the index because it lacks
a genuine observed build receipt linking the actual embedding bytes to vector bytes.
No receipt was invented and no corpus/index was rebuilt or overwritten. The detailed
blocker is saved in `build/arithmetic-pilot42/full-project-preflight.json`.

A narrower compatible adapter uses unchanged RuleVerifier and SemanticVerifier
constructors, the installed 91,578,415-byte local embedding snapshot and CPU execution
with two explicitly configured intra-op threads. Actual source/config/model fingerprints
are observed before and after calls. The embedding directory digest is
`23c61c55d84d9ab0045288ba589018e80ff90cf894514f5676e351c14624d255`.
No NLI model, retrieval index, corpus-dependent evidence adapter or confidence-generation
service was used for collection. No large model was downloaded and no paid/external
inference API was called. Offline flags and local_files_only prevent remote fallback.

Semantic receives a correct-result arithmetic reference, identical for both answer
variants. This is an explicitly **reference-assisted constructed task**, not blind
arithmetic discovery or factual QA. Semantic similarity does not certify arithmetic
correctness. The observed raw reports were rule: 40 SUPPORT/40 REJECT; semantic:
80 SUPPORT. These are raw adapter outputs, not fitted-policy development or test
performance. Evidence-verifier robustness is not evaluated.

The two candidates meet their existing prerequisites. The proposed minimum of two
also preserves the production easy/medium contributor floor. No duplicated verifier
identities or forced four-verifier eligibility were introduced.

## Actual collection and calibration results

The existing recording collector was used; no new collector was implemented here.
The bundle ID is `96a88bd532dfee725d18dd48bda2aa1ebb342fdf0fc56f74c3e9649ec9a1e591`.
Request digest: `46c0375d35a5801f059a8824b6170697ac4c7a6776f584182125dcbbde5acb7b`.

Calibration method is the existing mean_attempt_wall_time_ms_v1. All 80 calls per
candidate are included; include_warmups=true, exclusions empty, and measured failures
would be included under the estimator contract. Legitimate REJECT reports are returned
outcomes, not execution failures.

- Rule: mean **0.13031749986112118 ms**, median 0.053099996875971556 ms,
  nearest-rank p95 0.08290004916489124 ms; 80 calls, zero failures.
- Semantic: mean **12.817771245318 ms**, median 10.86074998602271 ms,
  nearest-rank p95 16.188699984923005 ms; 80 calls, zero failures.

The first measured calls are retained: rule 0.3505999920889735 ms and semantic
98.36209996137768 ms. Each has 79 subsequent calls. The linked
`attempt-temperature-annotations.json` distinguishes first measured calls after eager
initialization from subsequent calls; cache temperature itself was not measured.
Nothing was excluded as a warmup. Model initialization and resource-observation
overhead are outside the verify-call timer. The estimate is summed attempt wall time,
not parallel request latency, monetary cost or a hard runtime guarantee.

Calibration ID: `c32267151f0fdf265ca502652f11f6828d967b985ab1efbd7a33fdd69d117398`.
The recorded setup includes dependency versions, actual environment/hardware, exact
Git revision and dirty application-source digest. Git HEAD was
`224a2e59792b7ee0183bfa64aed0481dcad57d78`; concurrent work was preserved.

## One complete fitting proposal: UNAPPROVED

The full proposal is
`build/arithmetic-pilot42/proposed/fitting-proposal.UNAPPROVED.json`.
It contains a complete schema-valid PolicyBuildSpecification, context, contract,
history/development manifest, source links, explicit versions/seeds and assumptions.
The outer wrapper is intentionally not accepted by the builder: approving/extracting
the nested specification is a separate deliberate step. No PolicyArtifact exists.

Proposed values and their effects:

- False accept **1**, false reject **1**, uncertain **0.2**: equal error penalties;
  uncertainty costs one fifth of an error. These are normative pilot proposals,
  not empirically calibrated losses.
- Threshold **0.55**: reuse the existing production signed-margin default. Raw score
  strictly greater than +0.55 passes, strictly less than -0.55 fails; the interval and
  boundaries are uncertain. It is not a probability threshold. Production values
  were unchanged. Semantic's existing 0.5 SUPPORT / below-0.3 REJECT thresholds and
  all vote-normalization semantics were unchanged.
- Beta prior **alpha=1, beta=1**: propose the existing manager defaults. Only 40
  labelled history candidates update the proposed frozen reputation, never development
  or final labels. bind_evaluation independently verifies the resulting snapshot.
- Minimum **2** participants: preserve the easy/medium floor; both real candidates
  are the one feasible team, represented with both aggregation methods. This is a
  consequence of the narrower roster and constraints, not a fitted team preference.
- Estimated budget **12.94808874517912 ms**: the sum of the two measured means.
  Resource weight **0.007723147560077727 loss/ms** gives a full-budget team an
  additional 0.1 loss. Budget is estimated attempt cost, not a deadline. The choice
  of 0.1 and the budget formula need approval.
- Failure contract **all_selected_returned**; existing report_corruption_v1 actions,
  unavailable suppression, and **shared_unknown** with both candidates unresolved
  as one conservative connected group. No independence is asserted and simulated
  transformations remain offline. These attack/dependency assumptions need approval.
- Seed **42**, one declared policy-sampling repetition, optimizer certificate tolerance
  **1e-8**, repeat-build absolute tolerance **1e-12**. Proposed future grouped uncertainty
  settings are 2,000 resamples, confidence 0.95 and seed 42; no uncertainty analysis or
  final evaluation ran. The 20 groups per split are authorized engineering sizes,
  not evidence of statistical power or publication readiness.
- Primary outcomes: worst_case_expected_loss (the configured cost-inclusive objective)
  and decision_coverage. Decision-only validation loss must be reported separately.
  No tuning, matched-coverage target or superiority claim is proposed for this pilot.

The exported manifest and bound context are builder-compatible **under this unapproved
proposal**. Readiness passes, including history/resource validation. Producing these
proposal inputs did not solve a game or score final outcomes. Only the fitting step
awaits the user's decision; data preparation, collection and calibration are complete
for this narrow scope.

## Exact commands and output paths

Executed preparation and collection:

```powershell
.venv/Scripts/python.exe -m app.game.offline.arithmetic_pilot --project-adapter-config build/verifier-collection/adapter.local.json --output-dir build/arithmetic-pilot42
.venv/Scripts/python.exe -m app.game.offline.collect validate build/arithmetic-pilot42/inputs/recording-request.json
$env:VERIFIER_ARITHMETIC_ADAPTER_CONFIG = (Resolve-Path build/arithmetic-pilot42/inputs/adapter.json).Path
$env:HF_HUB_OFFLINE = '1'
$env:TRANSFORMERS_OFFLINE = '1'
$env:HF_HUB_DISABLE_TELEMETRY = '1'
.venv/Scripts/python.exe -m app.game.offline.collect collect build/arithmetic-pilot42/inputs/recording-request.json --output-dir build/arithmetic-pilot42/collection
.venv/Scripts/python.exe -m app.game.offline.collect check build/arithmetic-pilot42/collection
.venv/Scripts/python.exe -m app.game.offline.calibration build/arithmetic-pilot42/inputs/calibration-settings.json --measurements build/arithmetic-pilot42/collection/measurements.json --output build/arithmetic-pilot42/calibration.json
.venv/Scripts/python.exe build/arithmetic-pilot42/propose_guarded.py
```

The public proposal helper is also
`.venv/Scripts/python.exe -m app.game.offline.pilot_proposal build/arithmetic-pilot42`.
It refuses to overwrite an existing proposed directory. Reruns require new collection
output paths/run IDs; existing actual reports, timings and custody files are retained.

Important outputs under build/arithmetic-pilot42:

- `dataset-summary.json`, `pilot-report.json`: origin, counts, provenance, actual
  costs, limitations, proposal status and identifiers.
- `inputs/recording-request.json`, `inputs/reservation.json`: history/development
  inputs and metadata-only holdout. No final label payload is included.
- `collection/recordings.json`, `collection/attempts.jsonl`: complete real reports,
  prerequisites, resource observations and stable attempt links.
- `collection/measurements.json`, `calibration.json`: all measured attempts and
  the validated cost artifact.
- `attempt-temperature-annotations.json`: first/subsequent invocation facts; no exclusions.
- `proposed/training-manifest.json`, `proposed/context.json`: initial training export
  and compatible context under proposed settings, not an approved deployable policy.
- `proposed/fitting-proposal.UNAPPROVED.json`, `proposal-isolation-check.json`:
  reviewable complete proposal and executable no-final-read/no-optimizer evidence.

**Only after explicit approval**, extract the nested policy_build_specification,
preserve configuration_version and every approved value exactly, record approval in a separate sidecar, then run the existing builder without
reapplying calibration to the already bound context. It already contains the actual
measured costs and verified lineage. Keep the original proposal/calibration alongside
the resulting build report. Do not modify or reopen the held-out final payload.

```powershell
# NOT EXECUTED: requires explicit fitting approval first.
$proposal = Get-Content build/arithmetic-pilot42/proposed/fitting-proposal.UNAPPROVED.json -Raw | ConvertFrom-Json
$spec = $proposal.policy_build_specification
$spec | ConvertTo-Json -Depth 100 | Set-Content build/arithmetic-pilot42/approved-policy-input.json -Encoding utf8
.venv/Scripts/python.exe -m app.game.offline.build build/arithmetic-pilot42/approved-policy-input.json --output-dir build/arithmetic-pilot42/fitted-policy
```

## Validation and scope

Initial preparation/collector tests: 26 passed. Final affected preparation, collector,
project-adapter, calibration and builder run: **106 passed**, no failures. These overlap.
Actual collection/check/calibration commands succeeded, and guarded proposal preparation
passed. No baseline failure was encountered/classified in this test run. Whitespace
checks passed. The full repository suite and final-test scoring were not run.

```powershell
.venv/Scripts/python.exe -m pytest tests/test_arithmetic_pilot.py tests/test_game_collection.py tests/test_project_collection_adapter.py tests/test_cost_calibration.py tests/test_game_build.py -q -p no:cacheprovider
```

This turn adds arithmetic_pilot.py, pilot_proposal.py, test_arithmetic_pilot.py and
this document, and extends only the offline recording_adapters.py with the narrow
real-resource factory. It preserves existing collector/calibration and concurrent
factual-study work. No DB/API, schema, migration, persistence, frontend, verifier,
retrieval or generation code was changed. No production reputation writes, commits
or pushes occurred.

## Publication and reuse

This document records a historical run. All referenced build artifacts, approvals,
recordings and final payloads remain local and are not included in Git. Historical
authorization cannot authorize another run. The reusable preparation CLI now requires
explicit `--preparation-authorization`, `--custody-record` and `--freeze-record`
references in addition to the local adapter/output paths. Start from
`docs/arithmetic_adapter.template.json`; an installed model path must be supplied.
Changing preparation/adapter source bytes changes resource provenance; do not
rewrite the existing artifact or its historical bindings to match new code.
