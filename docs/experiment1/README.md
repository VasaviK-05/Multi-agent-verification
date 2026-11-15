# Retrospective Experiment 1: clean and attacked frozen-policy comparisons

This implementation prepares and reports **retrospective/exploratory** comparisons
on previously exposed tests. It does not turn those tests into a new confirmatory
study. It does not fit a full policy, collect verifier outputs, alter scientific
settings, activate deployment, or pool different cohorts. No empirical final-test
scoring was performed during implementation.

Baseline commit: `10a168773ff45328e4a3cbd65cb2533d29baf7dd`.
Branch: `codex/experiment1-retrospective-phase-a`. Existing uncommitted Phase 1
changes are carried forward on this branch. Source commit **and source-byte
fingerprint** are required because a commit alone cannot identify those changes.

## Frozen specification format

`app.game.research.experiment1.manifest.ExperimentManifest` is the authoritative
strict schema. Export a machine-readable schema with:

```sh
python3 -B -m app.game.research.experiment1 schema
```

`manifest.template.json` records the actual intended policy identities and the
original Semantic infeasibility, but explicitly blocks cohorts whose complete
canonical inputs/reviewed specifications are not assembled. It is not permission
to score. Never fill a missing training input from final-test outcomes.

The manifest binds source commit/bytes, retrospective status, per-cohort frozen
artifacts and comparison distributions, history/development datasets, outcome-free
test reservations, related-example groups, exact feasible strategy definitions,
resource/execution contracts, reputation, attack actions, method-selection rules,
and statistical settings. Reporting Python/NumPy/SciPy/Pydantic versions are
recorded separately from the original collection environment and checked at
readiness; mismatches block reproducibility. Binding snapshots are verified against typed embedded
objects, not accepted as caller assertions. Original policy bytes/IDs are retained.
JSON duplicate keys and nonfinite numbers are rejected by the readiness CLI.

Construct atomic entries from **already prepared** Phase 1 comparisons:

```python
from app.game.research.experiment1.manifest import AtomicEntry, atomic_bindings
entry = AtomicEntry(
    cohort="arithmetic",                 # or factual/reference
    specification=training_only_spec,     # PolicyBuildSpecification
    comparison=frozen_comparison,         # FrozenComparison
    bindings=atomic_bindings(training_only_spec, frozen_comparison),
)
```

A `PolicyBuildSpecification` contains only history/development records and an
outcome-free final reservation. Its inherited name does not authorize fitting.
Use the existing `prepare_comparison` only for separately approved development
baseline preparation. It authenticates development replay and preserves coverage
and reliability-first overlays. It does not refit the full policy. No real-cohort
baseline distributions were prepared in this implementation phase.

Component entries embed validated `Training`, `FrozenComponentComparison`, exact
original freeze ID and `component_bindings(training, comparison)`. For scoped E/R
final recordings, also supply the existing `resource_transfer`: its content ID,
policy/freeze/study IDs, full-resource ID and exact required-resource projection
are checked. Readiness checks its source-file hashes under the repository root.
A scoped observer or arbitrary saved manifest is not a provenance substitute.
Original full-setup records need no scope transfer. Actual recording setup and
component/binding/report identity are revalidated on explicit release.

After review, build `ExperimentManifest` with all five cohort dispositions. Its
`manifest_id` is the canonical content hash; persist the exact JSON separately
without overwriting any historical artifact. A manifest cannot claim confirmatory
status or pooled estimates. Freeze a single statistical design before scoring;
never search seeds after outcomes.

## Methods and cohort boundaries

| Method | Semantics |
|---|---|
| Full minimax | Exact existing policy probabilities, including zeros and tiny nonzero entries |
| Greedy | Captured `initial_selected` and declared aggregation; same complete-team finalization, no selector redesign |
| Development fixed | Rows individually meeting the development coverage floor; validation objective first, declared tolerance/epsilon, cost and ID tie-break |
| Clean-development fixed | Separately labelled clean-loss selection, development only |
| Uniform | Exactly 1/N across feasible rows, without reweighting to meet a distribution coverage floor |
| Aggregation-restricted minimax | Restrict rows while preserving floor, validation-first objective, cost tie-break, source bindings and numerical certificate |

Every distribution reports its expected development coverage and floor compliance.
Noncompliance is reported, never repaired. An unavailable/infeasible method has no
invented probabilities or metric rows. Restricted solver failure is distinct from
mathematical infeasibility. Greedy's heuristic resource ranking remains the
original selector's ranking; replay uses the common frozen attempt-cost budget.

Arithmetic/Factual use their original minimum-one contracts. Reference retains its
actual 1/6 Semantic / 5/6 Semantic+Confidence mixture, not simulated team counts;
its 50% floor chosen after development is recorded in bindings. Compound retains
base-fact and derived-sum obligations and component aggregation/joining, including
submitted-base arithmetic. Its 85% floor amendment remains in the frozen contract.
The existing equal-cost component architecture supports fixed/uniform/restricted
comparisons; a genuinely comparable component greedy executor does not exist, so
it is excluded with a reason. Original Semantic's 90% infeasibility is represented
with its original matrix/result and no fitted distribution.

## Metrics and attacker semantics

`runner.atomic_cube` and `runner.component_cube` adapt existing pure replay into a
complete outcome cube. Original resource and provenance checks stay active. Each
method has the same declared examples and full attack axis, including unused
strategies needed for completeness checks. Labels and frozen costs must agree
across rows/actions. Missing records block reporting; failed/unavailable attempts
are retained. No record is edited. Component execution counts every component call,
including repeated verifier identities; it does not count just distinct names.

For each method and action the report retains attack kind, attack ID and dependency
group ID, correct/false accepts/rejects (expected counts and rates over **all
examples**), decision coverage, uncertainty, selective risk, validation loss,
estimated attempt cost, total cost-inclusive loss, execution failures and reasons,
and unresolved coverage/requirements/reasons. Unresolved coverage can coexist with
a qualified whole-answer rejection and is counted independently of uncertainty.

Selective risk is `(FA+FR)/decisions`; it is null with no decisions. Decision loss
uses the exact frozen FA/FR/uncertainty penalties. Cost is the frozen estimated
attempt cost, including failed/abstaining/suppressed attempts; it is not observed
latency, money, or end-to-end deployment cost. Total loss adds the original resource
coefficient times that estimate. Both validation and total loss are named explicitly.

Failure counts describe post-attack execution states, with separately reported
original-record failure counts so simulated suppression is not labelled an observed
upstream failure. The detached atomic replay manifest lacks collector exception strings:
reasons are honestly labelled `recorded_state_only:<state>` or the retained attack
suppression reason; per-call provenance is retained in detached outcomes. Full collector journals may contain additional exception detail, but those
strings are not inferred from state or substituted by an unbound lookup. No
exception cause is guessed. Component decisions, binding/dependency IDs and
per-component states remain in `components_json`.

Worst-case expected loss is **max over complete configured attack actions after
integrating policy probabilities and averaging the cohort**. It is not the average
of per-example worst attacks. Both validation-loss and total-loss maxima and their
attack identities are retained. Every declared dependency group receives all four
corruption actions plus the common clean action. Same-kind attacks on different
groups never overwrite each other.

## Paired statistical design

Defaults frozen before scoring: **95% percentile intervals, 5,000 resamples,
seed 20261112**, NumPy PCG64 via `default_rng`, linear quantiles. A manifest stores
these values; changing them creates a different manifest ID. Shorter repetition
counts in tests are synthetic software checks, not study settings.

Draw whole related-example groups with replacement. Keep all variants/components
within each group. Use the same draw matrix for every method and attack. Unequal
group sizes use the number of examples in the drawn groups as denominator; this
estimates the example-weighted cohort metric. Probabilities are integrated exactly;
no random team sampling or favorable policy seed enters a metric.

Intervals cover all scalar counts/rates, decision coverage, uncertainty, selective
risk, unresolved coverage, validation loss, cost, total loss and failure counts.
Worst-case losses are recomputed across all attacks within each resample. Paired
full-minus-baseline point differences and intervals use the same draws. If any
resample has undefined selective risk, its unconditional interval is omitted and
its undefined fraction is reported; undefined values are never replaced by zero.
One group yields no population interval and an explicit reason. Small source-known
cohorts and degenerate zero-error intervals do not establish population safety.

## Readiness and future scoring

Run readiness only, with the intended frozen manifest:

```sh
python3 -B -m app.game.research.experiment1 readiness /absolute/path/to/experiment1-manifest.json
```

Exit 0 means the supplied manifest passes declared source/contract/readiness
checks; exit 2 lists blockers. The command performs no replay, optimization,
collection, model/service requests, final-payload reads or file writes. It has no
scoring subcommand. Archive its manifest ID and exact source bytes before seeking
final-scoring approval.

Future approved scoring uses the explicit Python API:

```python
from app.game.research.experiment1.runner import report_cohort
# NOT executed during Phase A:
# result = report_cohort(manifest, "arithmetic", actual_commit=commit,
#     actual_source_fingerprint=fingerprint, source_root=repo,
#     role="final_test", released_final=separately_released_partition)
```

Readiness is rechecked before replay. Atomic release must match the outcome-free
reservation and original cross-partition grouping checks. Compound release must
match the original freeze, component requests and exact approved resource setup.
No optimizer or baseline selection runs during scoring. `role="development"` is
an explicitly separate diagnostic, not a final-test result. Emit separate reports
per cohort; there is no pooled-report API. Outputs bind manifest/policy/comparison,
released-payload and complete outcome-cube hashes, metrics, intervals, exclusions
and detached outcomes. Readiness is a reproducibility gate, not user approval.

## Current blockers

- Arithmetic/Factual: original complete training manifests/development evaluations
  and reviewed scientific specification/evidence-validation metadata must be
  restored/assembled from their canonical sources. Selected-report examples cannot
  replace full candidate recordings.
- Compound: canonical study/training/freeze custody inputs remain necessary. The
  public finalized outcome export alone cannot establish source/resource binding.
  Existing E/R transfer must accompany scoped final recordings.
- Reference: published training/evaluation records exist, but a reviewed complete
  experiment specification and baseline comparison freeze must be assembled and
  provenance checked without consulting final outcomes.
- Original Semantic: 90% fit remains infeasible; exclude it from fitted-policy
  performance comparisons with the preserved infeasibility record.
- New method/statistical comparisons on exposed tests are retrospective. No new
  confirmatory claim follows from implementation or internal numerical checks.

## Tests

All implementation checks use synthetic examples/reports only. They cover exact
mixing (including tiny probabilities), singleton/pair calls, all attack conditions,
multiple dependency-group IDs, failed/unavailable attempts, undefined risk, whole
and unequal-size groups, paired differences, max-after-expectation, frozen identity
checks, development-only selection, source drift, compound obligations, and record
immutability. Existing comparison/coverage/reliability tests remain applicable.
No empirical performance assertions or final records are test inputs.

The local temporary test environment uses the same optional-model construction
and connection guards documented in the Phase 1 handoff. These are test-only guards,
not production code or substitutes for scientific model/resource observations.

### Verified implementation results

The broad synthetic suite passed **128 tests**, including the formerly excluded
runtime-parity check. Subsequent reporting-environment and bootstrap edge-case
checks passed **30 targeted tests** (overlapping the broad run); the final synthetic
component/end-to-end development-report check passed separately (**1 test**).
There were no failed or blocked tests in these final runs. Test fixture fitting
and fake report production are synthetic software checks only, not empirical
refits or new verifier reports.

```sh
PYTHONPATH=/private/tmp/experiment1-test-guard:/private/tmp/experiment1-test-deps python3 -B -m pytest tests/test_experiment1_reporting.py tests/test_experiment1_comparison.py tests/test_game_research.py tests/test_game_clean_coverage.py tests/test_game_reliability_first.py tests/test_flexible_teams.py -q -p no:cacheprovider -p no_external_connections
PYTHONPATH=/private/tmp/experiment1-test-guard:/private/tmp/experiment1-test-deps python3 -B -m pytest tests/test_experiment1_reporting.py tests/test_experiment1_comparison.py -k 'not component_comparison and not component_adapter' -q -p no:cacheprovider -p no_external_connections
PYTHONPATH=/private/tmp/experiment1-test-guard:/private/tmp/experiment1-test-deps python3 -B -m pytest tests/test_experiment1_comparison.py -k experiment1_component_adapter -q -p no:cacheprovider -p no_external_connections
```

The schema and explicitly blocked template were regenerated after source changes.
Template readiness exits **2**, with exactly the four documented input/specification
blockers, Original Semantic's preserved infeasible disposition, and zero replay,
optimization, native calls or final-payload reads. This is the expected honest
result, not an assertion that the empirical experiment is ready to score.

New Phase A files:

- `app/game/research/experiment1/__init__.py`
- `app/game/research/experiment1/__main__.py`
- `app/game/research/experiment1/manifest.py`
- `app/game/research/experiment1/metrics.py`
- `app/game/research/experiment1/runner.py`
- `docs/experiment1/README.md`
- `docs/experiment1/manifest.schema.json`
- `docs/experiment1/manifest.template.json`
- `tests/test_experiment1_reporting.py`

Extended existing Phase 1 file: `tests/test_experiment1_comparison.py`.
Carried forward unchanged from Phase 1: `app/game/research/comparison.py`,
`app/game/research/component_comparison.py`, `app/game/research/uncertainty.py`,
`docs/experiment1_comparison_compatibility.md`. All remain uncommitted on the
feature branch. No main merge, existing research-artifact update, dependency-file
change, API/runtime/verifier/database/frontend change, or empirical final scoring
was performed.
