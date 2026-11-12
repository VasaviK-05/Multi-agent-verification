# Experiment 1 Phase 1: offline comparison compatibility

Baseline checkout: `10a168773ff45328e4a3cbd65cb2533d29baf7dd`.
Feature branch: `codex/experiment1-comparison-compatibility`.

This change prepares comparison distributions from **development only**. It does
not authorize new empirical baseline fitting, policy fitting, test scoring, or
scientific claims. Original policy IDs, probabilities, records and resources are
unchanged. New comparison definitions on previously exposed tests remain subject
to the separate confirmatory/retrospective provenance decision.

## Atomic preparation

`prepare_comparison(spec, development, artifact, freeze_record=...,
actual_code_revision=...)` accepts the existing research specification or a
`PolicyBuildSpecification` with a `TrainingManifest` and outcome-free reservation.
Use the training-only form for current frozen cohorts. Provide their ORIGINAL
unconstrained development `Evaluation`, not a fabricated transformed evaluation.
The function reconstructs development replay and existing coverage/reliability
transforms, verifies exact context/matrix equality, and validates the existing full
artifact. These transforms do not solve or refit the full game. Resource,
history, adapter, evidence-validation and execution-contract gates remain active.

Restricted aggregation games project strategy definitions, payoffs, validation
values and clean coverage in the same row order. Coverage floor, epsilon,
secondary cost tolerance, source evaluation/training IDs and parent identities
are retained. Parent IDs describe the original full fit, not a newly deployed
restricted policy. The frozen comparison validates each projection against that
full matrix and checks both-stage solver certificates. Restricted games are
research distributions, never replacement deployable policies.

Fixed baselines first require each row to meet the development coverage floor.
For reliability-first policies, ranking uses validation losses, then cost among
rows within the frozen epsilon of the optimum, then strategy ID. The
coverage-only fixed ranking uses its declared numerical tolerance and cost tie
break. Clean-development is a separate explicitly labelled selection objective.
Legacy unconstrained ranking is retained. No final labels select a strategy.

Captured greedy keeps `initial_selected` and the declared aggregation. No selector
algorithm, cost heuristic or stopping rule changes. All methods use the exact
same decision threshold, resource-bound recordings, contributor/coverage guards,
and complete-team replay. Greedy may miss the statistical development coverage
floor; that is reported rather than repaired.

Uniform means exactly `1/N` over all feasible team/aggregation rows. It is not
coverage-conditioned or reweighted. Every research distribution exposes
`coverage_compliance` (minimum, expected achieved development coverage,
satisfies); scoring outputs include this as `development_coverage`. Uniform
noncompliance does not become an infeasible probability distribution. Full-game
probabilities are copied exactly, including tiny nonzero entries and zeros.

An infeasible fixed baseline or failed/infeasible restricted solve has no
probability distribution. `unavailable_methods` records status, reason and, for
restricted solves, exact projected matrix and failed solver result. Solver
failure is distinguished from mathematical infeasibility. Missing captured
greedy is explicitly unavailable; no fallback team is invented.

## Compound preparation

`prepare_component_comparison(policy, training, freeze_record=...)` uses a
separate `FrozenComponentComparison`, accepts validated `Training` only, and
reconstructs joint development cells with the existing component replay.
Base-fact and derived-sum obligations, submitted-answer binding, component
aggregations, required resources, joining semantics and joint strategy IDs stay
intact. It does not convert a component policy into an atomic policy.

Full, uniform, development-fixed and aggregation-restricted component
probabilities are supported for the existing equal-cost joint-plan architecture.
An aggregation restriction applies to every obligation. Unequal-cost joint plans
are rejected because this architecture has no declared two-stage joint objective.
Compound greedy is unavailable: there is no independently specified comparable
component greedy executor. A fixed E/R plan must not be renamed greedy.

Canonical Compound training/study inputs are required. Published finalized
outcomes do not substitute for source/resource validation. Missing unpublished
canonical inputs therefore remain a real preparation blocker in a public clone.
No new component final-scoring or statistics executor is introduced in Phase 1.

## Cohort support and remaining boundaries

| Cohort | Phase 1 support |
|---|---|
| Arithmetic/Factual minimum-one | Atomic full, fixed, captured greedy, uniform, restricted games; frozen objective reconstruction |
| Reference | Same atomic path; exact frozen mixed probabilities preserved |
| Compound | Separate full/fixed/uniform/restricted preparation; greedy unavailable; canonical training required |
| Original Semantic 90% | Infeasible fit remains infeasible; no policy or comparison distribution invented |

Training-only final evaluation requires an explicitly supplied released partition;
reservation identity and cross-partition related-example exclusions are validated
before replay. The same explicit-release path is shared by atomic uncertainty.
Synthetic fixtures exercise these gates; no empirical final partition was opened
or scored for this work. Existing legacy synthetic research entry points remain
supported.

The next phase can build metric extraction/statistical reporting on these
interfaces. It must distinguish validation loss from cost-inclusive `mean_loss`,
add the agreed endpoint/failure reporting and component statistics, and decide
how new retrospective comparisons will be labelled. This change does not claim
that all those reports already exist or that live resource compatibility holds.

## Focused verification

`tests/test_experiment1_comparison.py` uses generated synthetic fixtures only:
minimum-one v4 contracts, development-only reconstruction, lexicographic
restrictions, uniform compliance, tiny probabilities, common synthetic test
examples/attacks, failure/abstention costs, drift rejection, and joint component
semantics with fake verifier report producers. Existing empirical artifacts are
not test inputs in this file. Synthetic fitting creates fixtures only; the
comparison entry points never refit the full policy.

The local Python 3.12 environment lacks the optional `sentence_transformers`
package imported eagerly by verifier modules. A temporary `sitecustomize.py`
provides its import symbol and raises on any model construction; this applies to
subprocesses too. It is an import guard, not a verifier/model substitute, and is
not part of repository or production code. Pytest/httpx/dotenv/faiss dependencies
were installed only under `/private/tmp/experiment1-test-deps`. No model/index was
loaded. Normal environments with repository dependencies can run the tests
without this guard.

Real-cohort preparation still requires complete original training manifests,
development evaluations and evidence-validation metadata. Arithmetic/Factual's
original ignored build paths are not recreated here; selected-report examples
cannot replace the full candidate recordings. Reference's published training
bundle/evaluation exists, but a reviewed research specification and its exact
source/resource bindings must be supplied. No Phase 1 real-cohort comparison
artifact was generated. The optional canonical Compound inputs remain separate.

### Local results

Final scoped runs passed 111 distinct checks: 56 atomic/research checks, two
component checks, and 53 coverage/reliability/flexible-team regression checks.
`git diff --check` and AST syntax checks passed. Earlier collection attempts
failed on absent optional imports before the temporary test environment/guard was
prepared; no scientific execution occurred.

The broader regression attempt additionally encountered one existing runtime test
(`test_full_export_reload_versions_and_runtime_parity_no_heldout_parser`) blocked
by absent `psycopg2` while importing runtime/persistence. That test was excluded
from the final scoped regression run because production runtime/persistence is
outside Phase 1; it was not repaired or counted as passed. No DB connection or
mutation was performed.

Commands used (temporary guard described above):

```sh
PYTHONPATH=/private/tmp/experiment1-test-guard:/private/tmp/experiment1-test-deps python3 -B -m pytest tests/test_experiment1_comparison.py tests/test_game_research.py -k 'not component_comparison' -q -p no:cacheprovider
PYTHONPATH=/private/tmp/experiment1-test-guard:/private/tmp/experiment1-test-deps python3 -B -m pytest tests/test_experiment1_comparison.py -k component_comparison -q -p no:cacheprovider
PYTHONPATH=/private/tmp/experiment1-test-guard:/private/tmp/experiment1-test-deps python3 -B -m pytest tests/test_game_clean_coverage.py tests/test_game_reliability_first.py tests/test_flexible_teams.py -k 'not test_full_export_reload_versions_and_runtime_parity_no_heldout_parser' -q -p no:cacheprovider
```

Only `app/game/research/comparison.py`, `component_comparison.py`, `uncertainty.py`,
`tests/test_experiment1_comparison.py`, and this document changed. `git diff` for
`artifacts/` and `reconciliation/` is empty. No empirical comparison distribution,
verifier report or final-test result was generated. No commit, merge, deployment
or production configuration change was performed.
