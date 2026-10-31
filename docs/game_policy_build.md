# Offline policy building

The [approved prototype bundle](multitask_prototype_bundle.md) packages the existing
arithmetic50% and experimental factual25% artifacts unchanged, with a validated
manifest, deployment episodes and explicit reference/scope/resource requirements.
It performs no fit or activation; Semantic equivalence has no deployed entry.

The [three-outcome prototype review](multitask_uncertainty_tradeoffs.md) treats
uncertainty as valuable and compares optional development coverage targets
0/25/50/75/90%. The historical 90% target remains exploratory, not a universal
acceptance condition. No prototype is automatically activated.

The [task-conditioned multi-cohort workflow](multitask_policy_workflow.md) documents
the opt-in task/history and semantic-measurement coverage contracts, bounded local
collection, safe resume, retained-report routing checks and budget sensitivities.
The [completed multi-cohort results](multitask_policy_results.md) record 960 study
attempts, infeasible 90%-coverage primary policies and separately validated
unconstrained diagnostics; no qualifying multi-task policy is claimed.

The [informative-contributor reliability-first exploration](factual_reliability_first.md)
adds opt-in execution semantics and validation-first/cost-second optimization with
90% expected clean coverage. Legacy artifacts and coverage variants remain unchanged.

The [2026-10-30 clean-coverage exploration](factual_coverage_exploration.md) adds
an explicitly versioned development coverage constraint. Its three exploratory
variants preserve the original unconstrained policy and primary settings.

The current factual engineering workflow is documented in
[the factual campaign handoff](factual_policy42_results.md). Historical results
below retain their original scope and approval status. The
[2026-10-29 main merge verification](offline_policy_main_merge.md) remains the
record of that merge, rather than the status of subsequent empirical work.


The builder now fits, validates, exports and reloads the existing PolicyArtifact
format. Synthetic tests exercise the complete command and existing provider/runtime
interfaces. The arithmetic engineering pilot has since been fitted and diagnosed. The separate
cost-only campaign and its local artifact availability are documented in
[verifier_cost_results.md](verifier_cost_results.md); its timings are not report
recordings or approval of policy settings.

## Commands and inputs

```powershell
.venv/Scripts/python.exe -m app.game.offline.build PATH_TO_COMPLETED_BUILD_SPEC.json --output-dir build/my-policy
.venv/Scripts/python.exe -m pytest tests/test_game_build.py -q -p no:cacheprovider
```

Start from `docs/game_policy_build.template.json`. It is intentionally incomplete and
fails validation. Obtain the detailed schema from
`app.game.research.specification.PolicyBuildSpecification.model_json_schema()`.
The existing research readiness CLI and its game_research_v1 schema are unchanged.

The build specification version is offline_policy_build_v1. It retains the explicit
study/dataset/recording declarations, scope, code revision, execution contract,
attacks, costs, losses, seeds and uncertainty design of ExperimentSpecification.
Its manifest instead has version game_training_manifest_v1, explicit evidence_kind,
exactly two full Partition records (history and development), and final_test_reservation.
Recordings are embedded in the configuration. No final outcome filename or URI is
part of the fitting schema, and no external recording path is followed automatically.

Supply a captured PlanningContext whose statistics agree with independent history
under the declared priors. Existing capture_context and history_reputation supply
the producer interfaces. The builder recomputes and verifies the history snapshot,
then binds unbound contexts to the training/reservation identity and execution
contract. Stale bindings or snapshots reject instead of silently changing recorded
planning categories. Recording categories must match category_id(context).
No analysis/verifier execution obtains new observations during a build.

Readiness retains complete candidate, independent label, configuration, resource,
adapter, supported achieved-coverage and known evidence-producer gates. The
comparison-only greedy-team feasibility gate does not apply to full-game fitting.
Pooled contexts still require the existing explicit multi-domain workflow.
Every feasible team and both aggregation methods remain represented, including
zero-probability rows. The builder replays every development example/attack and passes
the explicit optimizer tolerance through fit_policy/build_policy to the existing LP
solver. It checks the certificate, exports, reloads, refits and compares outputs.
A local InMemoryPolicyProvider and DeploymentEpisode check compatibility without
executing verifiers, touching a live manager or wiring an API.

## Final-test custody and identities

The verified original blocker was structural: DatasetManifest required three full
partitions, its digest included final outcomes, and binding/readiness inspected all
partitions. The legacy path remains supported without changing its identity.

FinalTestReservation contains only:

- Version final_test_reservation_v1, role final_test, dataset_id and a nonblank
  external custody_record reference.
- A nonempty roster of example_id, split_identity, question_id, SHA-256
  content_identity and validation_id. These are the same leakage keys as the existing
  full manifest. The custodian supplies content_id([question, answer, reference]);
  the fitter receives only that digest, never those texts.

Additional fields, including labels, reports, outcomes and paths, are forbidden.
Missing metadata, duplicate example/run IDs, malformed digests, cross-partition reuse
of any split key, and inconsistent grouping of repeated questions/content reject.
The custodian must audit semantic relationships such as paraphrases and alternative
answers into the same split_identity; hashes cannot discover semantic leakage.
Witnesses/digests establish consistency, not independent authentication or filesystem
access control. Keep final payloads outside fitting configuration/access.

The reservation ID hashes metadata only. TrainingManifest.manifest_id hashes full
history/development records plus that reservation, using a distinct versioned
offline_training_binding_v1 binding. It never depends on final labels, reports or
statistics. Changing a reservation changes compatibility and requires refitting.
The artifact format and runtime compatibility rules are unchanged.

After externally witnessing a complete policy/configuration freeze, the evaluation
owner explicitly releases the final full Partition to:

```python
from app.game.offline.evaluation import evaluate_reserved_final

result = evaluate_reserved_final(
    artifact, build_specification, released_final_partition,
    actual_code_revision=actual_revision,
    freeze_record="external witnessed freeze reference",
)
```

This separate evaluator checks the artifact/specification/revision binding and exact
reserved roster, group, content and execution identities. It applies full
Partition/Example/Attempt and ExperimentSpecification validation, including independent
label-source declarations, then replays through the existing final evaluator without
optimization. The result records reservation_id, final_payload_id and freeze_record
separately. Labels/reports can change the released payload digest without changing
the reservation; they are never retroactively added to the fitted binding.
Mismatched identities or undeclared labels reject.
The low-level evaluate_final_test also accepts TrainingManifest with an explicit
final_partition, checks reservation/full-record contracts and exposes both IDs.
Use evaluate_reserved_final for additional study/label-provenance and external-freeze
audit checks. No final payload is opened, parsed or required by fitting.

## Outputs and reproducibility

Use a new output directory per successful build. The command refuses to overwrite an
existing policy.json. Success writes policy.json, build-report.json and summary.txt.
Blocked builds write missing-inputs.json and summary.txt, then return status 2 without
creating a policy artifact. Schema errors and independent readiness gaps are collected
together where practical. Failed artifact publication also writes a blocked report.
No synthetic substitute fills missing inputs.

Reports separate scientific_outputs from incidental build_metadata. They include
artifact/policy/matrix/history-snapshot/training-manifest/reservation IDs, applicability,
budget/units, loss/dependency/attack settings, all probabilities, positive strategies
with team/aggregation/cost, totals by team size, and certificate diagnostics.
Each fixed attack has development decision-only validation loss, separately named
cost-inclusive game objective, uncertainty rate, decision coverage and expected
estimated attempt cost. Clean results, all exactly tied worst objective scenarios and
largest validation loss are retained. These are development results, not held-out
improvement claims. Concentration receives no invented causal explanation.
Metrics.mean_loss retains its legacy cost-inclusive meaning.

Metadata records the canonical input/configuration digest, exact Git revision,
working-tree cleanliness, application Python source digest, Python/platform, NumPy,
SciPy, Pydantic, bundled HiGHS version, method and default LP-options policy. The
certificate tolerance is explicit. Seeds, repetitions and uncertainty settings are
recorded; fitting/policy integration have no Monte Carlo sampling. An isolated seeded
RNG checks provider compatibility without changing scientific outputs. This builder
does not run bootstrap inference.

Each success fits twice in the same installed environment and compares matrix
axes/definitions, values and policy probabilities with absolute tolerance 1e-12 and
relative tolerance zero. Reputation records are compared exactly, stronger than
1e-12. Different execution/context bindings reject. Solver prose, paths and build
metadata are excluded. IDs remain exact hashes and may differ for numerically
equivalent floats; equivalence does not promise identical bytes across environments.

## Initial empirical input audit and ownership handoff (historical)

Available data/test_benchmark.jsonl provides questions, answers and correctness flags,
not complete verifier attempts, audited splits/groups, independent label provenance
or resource fingerprints. Corpus/index files do not fill those gaps. At this
initial audit no completed recording manifest/build specification existed.
Subsequent arithmetic and factual engineering campaigns are documented separately.

- Collection/integration owners: actual outputs or explicit failures/unavailability
  for every candidate, execution IDs, actual model/corpus/index/prompt/adapter and
  implementation/configuration fingerprints, and matching attempt observations.
- Independent adjudicators and dataset custodian: independent labels/provenance,
  history/development recordings, audited grouping/disjoint splits, metadata-only
  reservation and external custody/freeze records. Release final payloads later.
- Study owner: approved population/category, dependency pathways/unknown treatment,
  calibrated cost units/estimates, budget, error/uncertainty/resource penalties,
  thresholds/failure semantics, priors, seeds, uncertainty and sensitivity plans.
- Historical evidence handoff: the producer defects listed here were later repaired
  upstream. The factual campaign verifies current controlled/installed-NLI probes
  and uses a resource-bound readiness receipt; see the current handoff linked above.
  No verifier algorithms were changed in this workflow.

Integration owners load PolicyArtifact.model_validate_json(path.read_text()), register
it with InMemoryPolicyProvider((artifact,)), and use existing DeploymentEpisode and
GameRuntime interfaces. Synthetic artifacts retain synthetic_test_fixture evidence
and require the existing test-only runtime permission. Tests keep synthetic artifacts
in pytest temporary directories. No database/persistence, API, baseline, feedback or
early-stopping behavior is changed.

## Validation record

The final builder suite passed 26 tests. The affected game suite passed 314 tests
with one existing failure: test_cli_unresolved_template_is_read_only_and_reports_digests
hard-codes revision 9d21eba9d3ac823b0ebb6c90195cff524db55253, while actual HEAD is
224a2e59792b7ee0183bfa64aed0481dcad57d78. The same failure was reproduced using an
isolated git archive of unmodified HEAD. No test assertion or reported revision was
changed to hide it. A solver-adapter regression found during implementation was fixed
by preserving the original no-keyword default solve call; new builds pass their
explicit tolerance. The final CLI regressions exercise nondefault tolerance 2e-7.

```powershell
.venv/Scripts/python.exe -m pytest tests/test_game_build.py tests/test_game_offline.py tests/test_game_foundation.py tests/test_game_runtime.py tests/test_game_research.py tests/test_game_completion.py -q -p no:cacheprovider
.venv/Scripts/python.exe -m pytest tests/test_game_build.py -q -p no:cacheprovider
.venv/Scripts/python.exe build/reproduce_policy_build_baseline.py
.venv/Scripts/python.exe -m app.game.offline.build docs/game_policy_build.template.json --output-dir build/policy
```

The baseline evidence is build/policy-build-baseline.json. The deliberately incomplete
project template produces build/policy/missing-inputs.json and build/policy/summary.txt,
with nonzero status and no policy.json. Synthetic successful artifacts stay in pytest
temporary directories. Windows atomic artifact publication and subprocess tests were
run outside the sandbox after its access denial; no sandbox failure is counted as a
scientific or implementation result. Git diff whitespace checks pass. The full
repository suite and real providers/databases were not run. Existing concurrent
cost-calibration changes were preserved and are outside this validation claim.

## Offline labelled recording collector

The missing full-report producer is now implemented in
`app.game.offline.collect`; see [the recording workflow](verifier_recording_collection.md).
It captures independent labels separately, planning/prerequisite evidence, every
eligible candidate report, explicit failures/unavailability, actual attempt timings
and pre/post observed resource identities. It does not require fitting losses,
budgets, thresholds or priors. Raw bundles are first exported to TrainingManifest
only after their explicit compatible PlanningContext is supplied; no existing
category/binding is rewritten. Complete calibration measurements can come from
the same verified bundle. This implementation does not supply the still-missing
approved study dataset/settings or repair the evidence producer. A real rule-only
smoke output is explicitly unlabelled and unsuitable for fitting.

## Arithmetic pilot42 abstention investigation (2026-10-26)

The approved arithmetic fit and subsequent investigation are documented in
[the fit report](arithmetic_pilot42_fit.md) and
[the abstention diagnosis](arithmetic_pilot42_abstention.md). The latter includes
exact commands, worked correct/incorrect examples and before/after development
metrics; all 80 clean strategy/example traces are in
`build/arithmetic-pilot42/investigation/traces.json`.

The zero-coverage fitted policy is compatible with its unchanged execution
contract. Frozen Semantic reputation is 0.5, so its log-odds contribution is zero;
Rule alone cannot satisfy the minimum-two contributor guard. Group aggregation
uses the documented active-report contributor count and is decisive on clean
recordings, but its worst-case validation loss is 0.5 versus the fitted policy's
0.2 uncertainty loss. No scientific settings or decision semantics were changed,
and no corrected artifact was produced. Original artifacts, recordings,
calibration and approval remain preserved. Diagnosis uses only retained
history/development records and metadata reservation, with final payload opens
blocked; it does not collect, recalibrate or evaluate final test.

Ownership handoff: the study owner must approve a genuinely informative second
verifier/roster and the required recordings/resource calibration before attempting
to demonstrate multiple informative contributors or team selection. A change to
minimum-contributor semantics is a separate versioned scientific/runtime decision,
not an abstention bug fix. The current two-candidate/minimum-two pilot has one
feasible team and cannot demonstrate adaptive team selection or cost optimization.
Its reference-assisted Semantic supports incorrect answers as well as correct
ones; conclusions remain restricted to constructed arithmetic.

## Next factual team-selection pilot (2026-10-28)

The [review package](studies/factual-team-selection-v1/README.md) reuses the existing
factual draft/index receipt, complete diagnostics, 344-attempt historical cost
calibration and detached collector/builder. It proposes four independently
source-grounded candidate answers: paired correct/constructed-incorrect alternatives
for Germany/history and India/development, preserving related-question groups, plus
the existing four outcome-free final metadata entries. Four other preparation rows
remain in an explicit unknown-requirement exclusion audit. No analyzer requirement,
threshold, contributor guard or verifier/retrieval algorithm was changed.

Public prior-only planning enumerates seven teams and fourteen strategies. Historical
cost sums differ, but Rule cannot provide useful capital-fact contributions, and new
history must establish sufficient informative weights. The historical calibration's
code/source setup and preparation identities differ from this new proposal: its
numbers are for review, not silently rebound fitting inputs. The new 16-call/20-local-
generation/68-metadata-GET run, source labels, custody/freeze and proposed 30,000-ms
budget / 0.00001-loss-per-ms settings require explicit approval. Existing evidence
contract failures and the readiness gate remain owned handoff blockers.

No new collection/calibration/policy fit occurred. The package contains exact guarded
preparation and later collector/calibration/builder commands, a digest-bound pending
configuration, source-label review, exclusions, complete team/cost enumeration and
validation results. The latter explicitly records a legacy test fixture's mixed-source
benchmark read; it makes no claim of perfect process-wide final-input isolation or
unseen holdout evidence. Subsequent affected tests use separated preparation/synthetic
fixtures only and pass 214/214. Arithmetic artifacts and conclusions are preserved.
The legacy draft test fixture has now been corrected to use separated preparation
rows and synthetic reserved-position rows, with an explicit mixed-source read guard;
its 11 tests pass. Combined with the 214 affected tests, 225 final tests pass. The
initial mixed-source fixture read remains transparently recorded in the handoff.
