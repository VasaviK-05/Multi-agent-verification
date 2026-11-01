# Empirical policy attempt: 26 October 2026

**Empirical policy remains blocked.** No empirical policy, cost table or new real
recordings were created. The ten benchmark rows have boolean labels but no source
provenance, partition/group membership or verifier reports. No completed approved
specification, final reservation, resource-observing collection factory, measured
cost bundle or compatible cost artifact was found in project data/build outputs.
No final-test payloads were opened and no collection/model/provider call was launched.

The exact missing-input table is the `missing_input_table` array in
`docs/game_empirical_build_audit.json`. It lists fields/formats, existing producer
interfaces, responsible owners and blocking reasons, separated into missing
recordings, missing scientific decisions, software/interface blockers and defects.
The same table can be opened beside the chat in
[the readiness canvas](C:/Users/jhaan/.cursor/projects/c-Users-jhaan-Multi-agent-verification/canvases/empirical-policy-inputs.canvas.tsx).

## Verified implementation and attempted build

Current branch: codex/game-pooling-resource-provenance. HEAD:
224a2e59792b7ee0183bfa64aed0481dcad57d78. The existing builder accepts
TrainingManifest history/development records and an outcome-free final reservation.
It verifies history reputation, enumerates both aggregations/all feasible teams,
replays development attacks, solves and certifies the minimax policy, exports/reloads,
checks the provider/deployment contract and refits for numerical equivalence.
The current synthetic builder and calibration tests pass. The reservation schema
forbids extra outcome fields and uses a distinct training binding; the later evaluator
checks released payloads against it. That structural blocker has been fixed.

Actual attempted commands, using the only available configuration templates:

```powershell
.venv/Scripts/python.exe -m app.game.offline.build docs/game_policy_build.template.json --output-dir build/empirical-policy-attempt
.venv/Scripts/python.exe -m app.game.offline.calibration docs/verifier_cost_calibration.template.json --output build/empirical-policy-attempt/verifier-costs.json
```

Both entry points return 2. The policy attempt writes missing-inputs.json and
summary.txt in build/empirical-policy-attempt; calibration rejects missing measurements,
reservation and freeze record. No policy.json or verifier-costs.json exists there.
The collection template also fails schema validation before factory initialization.
Templates remain intentionally invalid. These attempts are readiness failures, not
empirical estimates. No payoff matrix, policy probabilities or performance metrics
can be reported honestly for an empirical policy.

## Collection limits and upstream defects

The benchmark runner emits aggregate MethodReport counts, not per-example Attempt
records. The cost collector emits duration/status measurements, not verifier reports.
It requires an owner-supplied `module:function` returning verifier instances and the
actually observed MeasurementSetup; no concrete project factory was found. Its
failure handler preserves measured attempts then propagates the exception. Later
unattempted candidates must remain incomplete, not be invented as failed attempts.

AutomaticGroundTruthEvaluator supports external Wikidata lookup for supported
questions, but is not a complete provenance/split/custody producer. The HaluEval
evaluation scripts download data/models and use their own fixed scope/settings;
they do not export this game's complete compatible recordings. None establishes
permission to collect the benchmark rows as history or development. Existing default
selector penalties, test fixtures and cost-template rosters are not approved study
configuration and were not adopted as scientific settings.

The evidence/public-coverage defects were reproduced in the current tree and in a
full isolated archive of unmodified HEAD: directional entailment/contradiction returns
public uncertainty instead of expected passed/failed, and conflicting evidence reports
no_relevant_evidence instead of conflict. The evidence readiness gate remains enforced.
These cases use controlled model/retriever doubles and establish a contract defect,
not empirical behavior of an installed model. A reviewed upstream repair is needed
for evidence-bearing studies. An arithmetic-only study requires separate approval
and a genuinely different dataset; it is not an excuse to remove failed examples.

## Next executable steps and ownership

1. Dataset/study owners provide approved independent labels/provenance,
   history/development membership, related-example groups, final reservation/custody,
   population/category and complete settings. Supply existing approved paths if these
   inputs live outside the repository. Do not select examples from reserved final test.
2. Integration owners supply a real resource-observing factory and replay-ready report
   exporter using the existing Example/Attempt contracts. There is no complete turnkey
   recording-export command in this checkout. Resource identities must come from actual
   loaded resources; calibration cannot fill this gap.
3. Once the approved collection request and factory exist, execute the supported
   duration collector and calibration commands below. Separately persist complete
   verifier reports/states and observations; the cost bundle alone cannot fit a policy.
4. Complete the build spec with the real training recordings, approved settings and
   compatible measured costs. Build into a fresh directory and inspect its scientific
   outputs, certificate and reload checks before registering an artifact.

```powershell
.venv/Scripts/python.exe -m app.benchmark.collect_costs build/collection.json --output build/verifier-attempts.json
.venv/Scripts/python.exe -m app.game.offline.calibration build/calibration-settings.json --measurements build/verifier-attempts.json --output build/verifier-costs.json
$costSettings = Get-Content build/calibrated-build-settings.json -Raw | ConvertFrom-Json
.venv/Scripts/python.exe -m app.game.offline.build build/policy-input.json --calibration build/verifier-costs.json --budget-ms $costSettings.budget_ms --resource-weight-per-ms $costSettings.resource_weight_per_ms --measurement-setup-fingerprint $costSettings.expected_setup_fingerprint --output-dir build/empirical-policy
```

The named completed inputs in this block do not yet exist; the commands become
usable after their owner prerequisites are supplied. If approved costs use other
explicit units, the normal non-calibration builder path remains available; no unit,
budget, loss weight or measurement rule was selected by this audit.

## Validation and changed files

Working-tree checks: 49 passed, 3 existing evidence failures, 88 deselected. Isolated
HEAD reproduction: 1 passed, the same 3 failures, 88 deselected. There are no new
implementation failures in these checks. Exact test command and baseline output are
recorded in the JSON audit and build/empirical-policy-attempt/evidence-baseline.json.
The isolated archive initially lacked root import modules; the final reproduction
uses all tracked HEAD files and does not count those harness setup errors as defects.

This turn adds only docs/game_empirical_build_audit.json,
docs/game_empirical_build_audit.md, the managed canvas, and generated ignored files
under build/empirical-policy-attempt. Existing builder, tests and concurrent
cost-calibration changes were preserved. No app, verifier, retrieval, generation,
DB/API, schema, migration or persistence code was edited this turn. No production
reputation writes, commits or pushes occurred. API/DB modules imported by the existing
regression tests use their established isolated boundaries; no live DB was used.

## Concrete settings for review only

The user confirmed that no external approved settings or labelled bundles were
supplied. The following are proposed engineering choices, not scientifically
calibrated settings, approvals or empirical findings. They were not used to collect
or fit anything. The existing incomplete templates remain unchanged and invalid.

Two scope options are available for review:

- **Arithmetic pilot:** an independently adjudicated corpus of addition, subtraction,
  multiplication and division answers. This uses an existing supported achieved
  contract, but needs a new real labelled/grouped dataset; the factual benchmark is
  not silently repurposed.
- **Evidence study:** independently labelled direct-fact QA, closer to existing
  benchmark topics. Collection/fitting needs the separately reviewed evidence repair
  as well as complete provenance/recordings. Keeping this scope does not permit
  bypassing the readiness gate.

Review either scope with one of these loss profiles:

- **Balanced:** false-accept=1, false-reject=1, uncertainty=0.2; threshold=0.55.
- **False-accept emphasis:** false-accept=5, false-reject=1, uncertainty=0.2;
  threshold=0.75. This expresses a higher cost of accepting a wrong answer and a
  stronger directional threshold, without assuming better performance.

Common candidate settings: minimum two participants; Beta(1,1) history prior;
all_selected_returned failure contract; existing report_corruption_v1 attacks with
unavailable suppression; shared_unknown for explicitly unresolved dependencies.
Actual dependency pathways still come from resource owners. All feasible teams and
both aggregations remain in the game; these choices do not select a winning team.

For a compatible measured calibration, propose B_ms equal to the sum of all eligible
candidate mean attempt costs, allowing the full eligible team to remain budget-feasible.
Require B_ms>0; resource_weight_per_ms=0.1/B_ms gives a full-budget team a 0.1 loss
penalty. Actual milliseconds are still unknown. Exclude only explicitly marked
warmups, and retain all measured calibration failures. These budget/weight formulas
need approval; they are not cost estimates or automatically adopted defaults.

A concrete preparation proposal is 20% history, 40% development and 40% final,
assigned at the audited related-example group level before collection. Real group
counts, allocation feasibility and adequate independent sample size remain unresolved.
Use seed 20261026, one declared policy-sampling repetition (exact LP fitting itself
has no sampling), certificate tolerance 1e-8 and repeat-build absolute tolerance 1e-12.
For later preregistered uncertainty analysis, propose 2,000 grouped percentile resamples,
95% confidence and seed 20261027. These choices do not establish statistical power.

Development-only sensitivity candidates: resource weights 0, 0.05/B_ms, 0.1/B_ms,
0.2/B_ms and thresholds 0.55/0.75. Approve the primary outcome/selection/coverage plan
before using those settings; freeze the chosen policy and protocol before releasing
final records. No setting, population or data membership is approved by elapsed time
or by this report. Numeric candidates are also recorded under
proposed_settings_for_review in the JSON audit.
