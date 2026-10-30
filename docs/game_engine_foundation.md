# Game engine foundation (Stage 1)

The defender is the validation framework. Its action is `(verifier subset,
aggregation method)`. The experimental attacker commits to a configured failure
group and report transformation before seeing the sampled team. This package
minimizes the worst-case entry of a supplied finite empirical payoff matrix.
Its optimality claim is limited to that matrix, its attacks and feasible actions.
Reputation-weighted voting alone is not an equilibrium calculation.

Production still uses the existing baseline orchestrator. No game execution,
dependency aggregation, attack transformations, payoff fitting, policy persistence,
or learned default policy is enabled by this change.

## Actual interfaces

`capture_context(selector, analysis, context=reference, **configuration)` calls
the existing `selector.plan()` exactly once and never calls `resolve()`. The
selector plan now includes `reputation_statistics`, taken from the same atomic
`statistics_batch()` call already used for ranking. Counts, priors, unrounded
posterior means/variances and cold-start flags are retained. This is a
process-local atomic read, not a database transaction. Feedback behavior is
unchanged; source tags still do not authenticate labels.

Configuration must supply:

- `attempt_costs`: one nonnegative estimate for every captured candidate;
- `budget` and `cost_units`: the same explicit units as attempt costs;
- `loss_configuration`: application-chosen false-accept, false-reject,
  uncertainty penalties and resource weight, with matching units and version;
- `dependencies`: a versioned `DependencyRegistry`;
- `aggregation_versions`: versions for `reputation_weighted` and `dependency_group`;
- `provenance`: `PayoffProvenance` identifying the attack specification, distinct
  history/development/final-test partitions, matrix version, loss configuration,
  domain or explicitly pooled category, and empirical versus synthetic-fixture data.

No scientific calibration is implied by these caller-provided penalties, versions
or dataset identifiers. Identifiers alone cannot prove partition disjointness or
data provenance; the future offline pipeline must establish both.

`PlanningContext` is frozen and serializable. Nested configuration uses frozen
models and tuples. The selector snapshot is validated canonical JSON, not a
mutable nested object. Its `plan` accessor returns a fresh detached view.
The adapter preserves analyzer method and context/scoring versions, including
versions on invalid research contexts. Invalid field types are explicit markers.
It consumes the current requirement validator without redefining its rules.
Missing legacy obligations, unknown contexts, invalid contexts and unsupported
labels remain explicit and cannot create feasible teams. Legacy known requirements
remain supported, as the existing validator permits.

`requirement_signature` sorts set-like validator fields while preserving source,
weights and uncertainty diagnostics. SHA-256 identifiers use sorted-key UTF-8 JSON
with compact separators and no NaN/Infinity. `reputation_snapshot_id` hashes all
captured statistics. `compatibility_id` binds domain/status, analyzer provenance,
requirements, candidate availability/configuration, prerequisites, minimum size,
reputation, attempt costs/budget/units, dependency assumptions, aggregation versions,
loss settings and payoff provenance. Candidate registration order, greedy ranking
terms and ordering of capability/limitation sets do not affect game compatibility.
Dependency and cost/aggregation configuration order is canonicalized too.
Pooled categories are explicit provenance, not an automatic cross-domain fallback;
the remaining captured domain and reputation bindings must still be compatible.

`DependencyRegistry` requires named resources with explicit compromise pathways
and affected verifier names. Every candidate must be configured or explicitly
unresolved. Sharing a generated answer is not itself a dependency declaration.
Overlapping resources form connected components; unresolved verifiers share an
unknown pathway, including transitive connections to known resources. Components
are formed over the whole registry before projection onto a team, so omitting a
bridge verifier cannot split a configured failure group. Group IDs hash sorted
full component membership. Observed provenance must be stored in a separate audit;
it cannot alter a captured registry. Alternative unknown treatments and sensitivity
experiments remain future work; unsupported treatments are rejected.

`enumerate_strategies(context)` enumerates every nonempty subset of eligible,
registered candidates and both aggregation identifiers. It enforces the selector
minimum, all validated requirements including zero-weight requirements, and the
estimated attempt budget. It returns `feasible` or `no_feasible_strategy`, rejected
teams with reasons, and candidate exclusions. It never relaxes constraints and
does not use the greedy soft target. Four eligible candidates yield at most 30
team/aggregation pairs. Expected capability coverage is not achieved coverage.
The captured minimum also includes the existing orchestrator's floor of two for
non-hard questions, even when a custom selector is configured below that floor.

`PayoffMatrix` has unique stable strategy/attack labels, finite rectangular numeric
values, and a context compatibility ID. Policy matrices must also carry ordered
`strategy_definitions`: the exact teams, aggregation labels and estimated costs
against which the rows were evaluated. Strategy IDs bind team membership and
aggregation; policy construction checks definitions and costs against enumeration.
Generic numerical solver fixtures may omit definitions but cannot become policies.
`solve_minimax(matrix, tolerance=1e-8)`
uses SciPy HiGHS with nonnegative strategy probabilities and a **free** game-value
variable. Pure optima and negative values are allowed. It checks solver status,
normalization, feasibility and tightness after clipping tiny negative roundoff and
normalizing. It also reads the negated HiGHS inequality marginals as an attacker
distribution, validates/cleans it, and recomputes the defender upper bound
`max_a sum_i(x_i*M_i,a)` and attacker lower bound `min_i sum_a(M_i,a*y_a)`.
Both final distributions must normalize within `1e-12`, independently of the
payoff tolerance. Their absolute gap must fit the configured payoff tolerance.
This is a floating-point primal-dual certificate check using a solver-supplied
witness, not an independent optimizer run or exact-arithmetic proof. Primal
feasibility and a tight primal constraint alone do not certify optimality.
`SolverResult` contains labelled probabilities, value, tolerance,
constraint slacks (`value - attack loss`), attack losses, worst-case labels,
normalization residual, minimum probability, attacker probabilities, dual lower
bound, gap and an explicit `optimality_basis`. The reported game value is the
recomputed worst-case loss of the final returned defender distribution; the
original solver objective must agree within tolerance. Solver failure returns
`solver_failure` with no policy probabilities. Invalid matrix inputs raise validation
errors. The tolerance is absolute; badly scaled matrices may fail validation and
require rescaling by the caller.

`build_policy(context, matrix)` requires exactly the complete feasible strategy set,
solves it, and rejects failure. `validate_policy(policy, context)` rejects changed
bindings, omitted strategies, invalid distributions and mismatched diagnostics,
then recomputes the stored primal-dual certificate without another LP call. It
returns the detached validated policy used by sampling. Nested model instances
are revalidated so unchecked Pydantic copies cannot preserve mutable leaves or
bypass numeric validation. `sample_policy(policy, context, rng=...)` validates
before drawing from injected `rng.random()` in `[0,1)`. It never drops unavailable
strategies or renormalizes around them. Cumulative boundaries use `math.fsum`;
zero-probability actions are never sampled. Only machine-scale upper-tail roundoff
may select the last positive action. Compatible-policy retrieval/caching belongs
in a later integration stage.

The returned `PolicyDecision` includes policy/version and strategy IDs, verifier
names, aggregation, cost/budget/units, dependency assumptions, reputation snapshot
ID and selection explanation. Policy IDs address the complete stored payload,
including its matrix, explicit provenance and solver diagnostics. Synthetic-fixture
labelling survives policy serialization. Integrity hashes are not signatures
or authentication. Synthetic fixtures are explicitly labelled; no learned policy
or empirical result is provided by this implementation.

## Subsequent-stage contracts

Dependency aggregation belongs in decision code and must reuse `signed_mass`,
`is_abstention` and `vote_confidence`. Exclude abstention and zero confidence.
With frozen domain reputation, set `a_i=max(0,2*r_i-1)`. Within each active group,
`z_g=fsum(a_i*m_i)/fsum(a_i)`, falling back to the active unweighted mean when
the denominator is zero. Let `b_g=max(a_i)` and combine group scores as
`fsum(b_g*z_g)/fsum(b_g)`, falling back to the unweighted active-group mean.
Canonicalize exact duplicate report identities and reject conflicting duplicates.
Use `math.fsum`, retain no-result/all-abstention distinctions, classify the unrounded
score, and expose verifier/group explanations. Preserve the current log-odds
aggregator, including below-chance inversion. Both paths must accept the policy's
frozen reputation snapshot rather than reading unrelated live updates.

Offline evaluation must use isolated reputation state (the existing manager's
export/restore APIs support independent experiment instances), copied reports,
independent labels and separate history, development and held-out test roles.
Attacks are clean, forced support/rejection, confidence inflation and suppression,
initially compromising at most one failure group. Transformations must be
verifier-aware because normalization reads decisions, rule metadata and judgments.
Payoffs must evaluate the public decision **after achieved-coverage enforcement**,
including uncertainty penalties and `resource_weight * estimated_attempt_cost`.
Report coverage, risk at matched coverage, penalty/threshold sensitivity and the
limitations of report-level corruption experiments.

Runtime integration must execute the complete sampled team, disable early stopping,
avoid automatic fallback, enforce budget before dispatch, record failed attempts
and resources, and return uncertain for missing execution conditions or achieved
coverage. Preserve validation identities, detached snapshots, feedback binding and
baseline behavior. Do not enable game mode until aggregation and this execution
contract are implemented and tested together.

Current out-of-scope observations: `app/verifiers/__init__.py` eagerly imports
verifier modules even though selector construction remains lazy; baseline
orchestration's final uncertainty guard does not explicitly veto unknown
requirements (it records `coverage_unknown` and vetoes early stopping). Neither
behavior was changed here.

Project input is required for actual compromise pathways and unknown-dependency
sensitivity assumptions, resource units/cost calibration, application loss penalties,
aggregation/attack versions, dataset partitions and any pooled-domain mapping.
There are no scientifically justified defaults supplied for those decisions.

## Initial implementation validation

Validated on branch `vasavi/game-engine-foundation`, created from the clean
`vasavi/reputation-feedback-fix` HEAD. Nothing was staged, committed or pushed.
The complete tracked diff and all added source, test and documentation files were
reviewed for scope. Existing-file changes are only the selector's captured
statistics field/assignment and the SciPy dependency. Orchestration, verifiers,
retrieval, generation, frontend, database and teammate-owned tests are unchanged.

Commands use `.\.venv\Scripts\python.exe -m pytest`:

- `tests/test_game_foundation.py -q`: **59 passed** after the final test changes.
- `tests/test_game_foundation.py tests/test_verifier_selector.py
  tests/test_reputation_manager.py tests/test_reputation_imports.py
  tests/test_decision_engine.py tests/test_vote_normalization.py
  tests/test_early_termination.py tests/test_question_analyzer.py
  tests/test_question_research_context.py -q`: **439 passed**. The final subsequent
  test-only change strengthened nested-input mutation checks; the 59-test
  foundation suite was rerun successfully afterward.
- `tests/test_adaptive_pipeline.py tests/test_reputation_integration_upgrade.py -q`:
  **112 passed, 3 failed**, outside the sandbox. Sandboxed runs were interrupted
  after diagnosing TestClient blocking in Windows asyncio's local `socketpair()`.
- `tests/test_feedback_api.py -q`: collection fails because local PostgreSQL on
  port 5432 refuses connections outside the sandbox (network denied inside it).
- `git diff --check`: passed.

All three pipeline failures were reproduced with the original HEAD versions of
both modified selector modules, loaded through a read-only import hook using
`git show HEAD:<path>`; no working files were replaced. The baseline reproduction
selected `actual_evidence_output_contract_is_consumed_without_models` and
`actual_conflicting_evidence_cannot_cover_factual_request`: **3 failed, 1 passed,
88 deselected**. Two directional evidence cases return public uncertainty instead
of the expected pass/fail; the conflict case reports `no_relevant_evidence`
instead of `conflict`. These are demonstrated baseline failures and were left
untouched under the ownership boundaries. The feedback API's PostgreSQL
collection error was also reproduced using those original HEAD modules.

The full repository suite was not run. No empirical payoff fitting or production
game run was performed. Remaining implementation stages are dependency aggregation
with frozen reputation, verifier-aware offline attacks/payoff evaluation, then
compatible-policy retrieval and complete-team orchestration with execution audits.

## Stage 1 code review, 2026-10-22

Reviewed against `03-new-changes-with-game-engine.txt` in full and the original
Stage 1 implementation prompt. The review found the following P2 defects/gaps;
all were fixed in the existing reported game package, test and documentation files:

- **P2, fixed — mutable or unchecked nested inputs** (`app/game/dependencies.py:6`,
  `app/game/policy.py:76`). Pydantic's default nested-instance handling could retain
  mutable leaves from unchecked copies and skip numeric validation. Sampling also
  used the original object after validating a different copy. Nested instances and
  public planning/policy boundaries now revalidate, and sampling uses the detached
  validated policy. Tests mutate nested dependency lists and the caller's strategy
  list during the RNG call.
- **P2, fixed — row labels alone did not carry strategy definitions**
  (`app/game/policy.py:39`, `app/game/models.py:281`). Numerical matrices could
  become policies based only on compatible row IDs. Policy matrices now require
  explicit ordered row definitions, equality to enumerated teams/aggregations/costs,
  and content-derived strategy IDs. Generic solver-only matrices remain supported.
- **P2, fixed — imported policy diagnostics were not verified**
  (`app/game/solver.py:27`, `app/game/solver.py:51`). An otherwise valid distribution
  could retain false residuals, worst attacks or normalization diagnostics. All are
  recomputed and checked. The solver also now checks a feasible attacker witness
  and primal-dual gap, explicitly separating numerical optimality from primal
  feasibility. A mocked successful but suboptimal solver output is rejected.
- **P2, fixed — incomplete numeric snapshot validation**
  (`app/game/models.py:140`). Negative candidate counts, out-of-range candidate
  reputations/costs, inconsistent candidate/full-snapshot counts or cold-start flags,
  and impossible variances were accepted. These now reject. The existing extreme
  finite prior contract and exact integer observation totals above float precision
  remain supported; values are validated, never reconstructed from rounded means.
- **P2, fixed — equivalent configuration order changed compatibility IDs**
  (`app/game/models.py:237`). Registration order and capability/limitation ordering
  leaked baseline-only ordering into game compatibility. They no longer do;
  relevant semantic fields remain bound. Negative zero is canonicalized too.
- **P2, fixed — serialized policies lost explicit fixture labelling**
  (`app/game/policy.py:11`). Evidence kind previously survived only inside the
  context's opaque compatibility digest. Policies now serialize explicit provenance
  and reject mismatched provenance during compatibility validation.

No P0/P1 finding or remaining in-scope commit blocker was identified. This is a
Stage 1-only commit-readiness assessment, not approval to enable game execution.
The selector diff is still exactly its statistics type import, defaulted plan field
and assignment of the existing `stats` tuple. The same single locked batch read
supplies ranking and full statistics. No selection formulas, ordering, eligibility,
prerequisite checks, `resolve()` behavior, reputation updates or feedback rules
changed. Only the audit payload gains the additional statistics field. Production
modules contain no import or call into `app.game`. No Stage 2 work was started.

Review checks: **99 foundation tests passed**, including rectangular orientation,
pure/mixed/negative games, malformed matrices, cleanup changing the objective,
primal-dual certificates, stale diagnostics, missing or changed row definitions,
sampling at 0, exact cumulative boundaries and just below 1, leading/trailing zero
probabilities, nested mutation, numeric snapshot validation and explicit fixture
provenance. The affected component suite was rerun after the review changes:
**479 passed**. The isolated pipeline
and reputation integration run is **112 passed, 3 demonstrated baseline failures**.
The standalone feedback API/PostgreSQL limitation described above was not rerun
during this review. `git diff --check` passed; the full repository suite was not run.

The exact baseline failures are:

- `tests/test_adaptive_pipeline.py::test_actual_evidence_output_contract_is_consumed_without_models[probabilities0-passed]`
- `tests/test_adaptive_pipeline.py::test_actual_evidence_output_contract_is_consumed_without_models[probabilities1-failed]`
- `tests/test_adaptive_pipeline.py::test_actual_conflicting_evidence_cannot_cover_factual_request`

They were rerun in a fresh Python process with a `MetaPathFinder`/loader intercepting
only `app.selection.models` and `app.selection.verifier_selector`. For each, the
loader executed `git show HEAD:<module path>` in that module's namespace before
pytest imports; every other source/test remained the actual repository version.
Baseline HEAD was `7dbe8daa3101ffbbed0242bd10b1d0daf3472142`.
Pytest selected the two function names with `-k
'actual_evidence_output_contract_is_consumed_without_models or
actual_conflicting_evidence_cannot_cover_factual_request'`: **3 failed, 1 passed,
88 deselected**, matching the changed-tree symptoms. Neither this method nor the
checks used checkout/reset, replaced working files, staged changes or changed HEAD.

Unresolved design choices remain explicit: pooled provenance is supported but does
not define cross-domain reputation sharing or relax domain bindings; independent
policies still need compatible captured inputs. Unknown dependencies use only the
declared conservative shared-unknown treatment. Observed provenance remains an
audit contract for later integration, not an inferred resource registry. Actual
dependencies, costs/units, loss penalties, partition membership and pooling choices
must come from the project. Hashes and numeric certificates do not authenticate
that supplied payoffs are empirical or that dataset partitions are disjoint.
Certificate arithmetic is floating point with an absolute payoff tolerance; badly
scaled matrices can be rejected. Imported diagnostic values must reproduce the
documented reductions exactly. Dependency-group aggregation is an enumerated label,
not an implemented aggregator, and there is no production policy retrieval path.
