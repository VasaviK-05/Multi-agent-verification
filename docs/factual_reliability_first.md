# Informative contributors and reliability-first exploration

This 2026-10-30 development experiment is opt-in. It preserves the original
unconstrained and 25/50/75% coverage policies, execution semantics, reports,
calibration and findings. No fresh inference, recalibration, final evaluation,
production writes, API activation or Git publication occurred.

## Reproduction and contributor contract

Before changing engine code, every original development strategy/attack outcome
was replayed from retained records and matched the previous evaluation exactly.
The reproduced evaluation and preserved-input hashes are under
`build/factual-reliability-first42/`. Source custody-open guards remain active;
only history/development and metadata reservation enter fitting.

`offline_public_decision_v3` explicitly selects
`informative_history_influence_v1` and requires the same resource-bound execution
identity as v2. A contributor must have a directional positive-confidence report,
frozen history posterior strictly above 0.5, positive actual scoring coefficient,
and pass existing structural-rule/prerequisite exclusions. Reliable rejections
count: positive influence means positive coefficient, not positive signed vote.

For reputation weighting this requires an included positive log-odds weight.
For group aggregation it requires positive member reliability within an active
group with positive outer influence. Zero-reliability members cannot meet the
minimum merely by being active. The minimum participant count, achieved factual
coverage, unresolved requirements and execution-failure checks remain unchanged.
Two informative members can belong to one compromise group: independence is not
a contributor condition or claim. Legacy v1/v2 retain their original behavior.

History remains Evidence/Confidence 40 successes, no failures, Beta(41,1), mean
41/42; Semantic 20/20, mean 0.5; Rule no directional observations, prior 0.5.
The new replay changes no raw report or reputation. All fourteen feasible
team/aggregation strategies remain in the matrices.

Under the new contract, all eight strategies containing both Evidence and
Confidence have 95% clean coverage and zero clean errors. Each has two informative
contributors on 39/40 examples and one on the Confidence-abstention example; a
second example remains in the numerical uncertainty band. The other six strategies
have one informative contributor and zero clean coverage. In particular,
group-aggregated Evidence+Semantic falls from 100% legacy coverage to zero.
Adding zero-weight Semantic or abstaining Rule cannot supply missing contributors.
Maximum achievable clean coverage is therefore **95%**, so the approved 90% floor
is feasible. Every per-attack contributor/reason histogram is retained in
`informative-all-strategies.json` and the readable `comparison.md`.

The intermediate **new contributor contract with the old objective** still chooses
Evidence+Rule, reputation weighted, probability one: zero coverage, loss 0.2,
181.689941 ms and cost-inclusive objective 0.201402410. This isolates the semantic
change from optimization; it does not cure cheap abstention by itself.

## Versioned two-stage optimization

The only new approved primary requirements are clean expected coverage 0.90,
informative contributors, and validation-first/cost-second optimization. All old
loss weights (1/1/0.2), threshold 0.55, hard team budget 12,955.553737 ms, measured
costs, attacks and shared-unknown dependency model remain unchanged.

Stage A minimizes worst-case empirical validation loss V, **excluding cost**,
subject to the simplex, all original strategy feasibility checks and Q.x>=0.90.
Q comes from finalized clean source-record replay via the existing coverage
producer. Its primal/dual certificate uses the existing minimax solver. Stage B
minimizes c.x with every validation attack loss at most v_A+1e-8, plus the same
coverage/simplex constraints. No probability, verifier diversity or aggregation
method is manually selected.

For Stage B, nonnegative attack multipliers mu need not sum to one. With coverage
multiplier eta, its cost lower bound is
`min_s(c_s + sum_a mu_a V_sa - eta Q_s) - cap*sum_a mu_a + 0.90*eta`.
Validation recomputes both stages, their dual bounds, coverage, primary cap,
normalization, axes and all stored diagnostics. The synthetic test where both
plans have full coverage but the reliable plan costs 100 versus 1 proves that
Stage A prioritizes lower loss; Stage B may buy cost only within epsilon.
Infeasible coverage is rejected without relaxation or a valid artifact. The
producer reports maximum achievable coverage separately and does not lower 90%.

Versions and bindings:

- Execution: `offline_public_decision_v3` / `informative_history_influence_v1`.
- Intermediate policy/artifact: `game_policy_informative_v1` /
  `deployable_game_policy_informative_v1`.
- Reliability objective: `validation_then_attempt_cost_v1`.
- Policy/artifact: `game_policy_reliability_first_v1` /
  `deployable_game_policy_reliability_first_v1`.
- Certificate: `validation_then_cost_certificate_v1`.

The context and matrix bind the full reliability specification, the exact parent
coverage matrix, finalized Q, source evaluation and new execution contract.
Cost-inclusive `matrix.values` remain diagnostics/parent lineage; the explicitly
versioned primary matrix is `matrix.reliability_first.validation_values`. The
solver selects it only for the reliability-first version. Validation requires
diagnostic values to equal validation loss plus the original resource penalty.
Legacy optional fields are omitted when absent, preserving old identities. A
legacy artifact/version or episode cannot silently adopt the new semantics.

## Actual result and remaining abstention

The solver assigns:

- **18/19 = 94.7368421%** to reputation-weighted Evidence+Confidence.
- **1/19 = 5.2631579%** to reputation-weighted Evidence+Rule.
- **Zero** to the other twelve represented feasible strategies.

Finalized expected clean coverage is **90%** and the floor binds. The first plan
is the least costly team with two informative history contributors. The second
is the cheapest zero-clean-coverage plan; using its 1/19 probability meets the
floor at minimum worst-case validation loss, then cost. Coverage prevents any
further cost purchase in this dataset. Intrinsic uncertainty within Evidence+
Confidence plus the intentionally uncertain plan yields 10% clean uncertainty.
This is sampling before outcomes, not request-specific adaptation.

Both aggregations on Evidence+Confidence have equivalent finalized losses and
coverage here. The probability allocation does not establish reputation weighting
as superior. The dataset does not identify a genuinely better aggregation method.

Expected attempt cost is **12,234.222880 ms**, summed verifier wall time, not a
guaranteed request latency. Per attack, expected false counts are out of forty:

- Clean: coverage 90%, false accept/reject 0/0, uncertainty 10%, validation loss
  **0.020000000**, old cost-inclusive diagnostic **0.114432265**.
- Forced support: coverage 92.3684211%, false accept/reject 18.9473684/0,
  uncertainty 7.6315789%, validation loss **0.488947368**, old diagnostic
  **0.583379634**. This is worst case.
- Forced rejection: coverage 92.3684211%, false accept/reject 0/18,
  uncertainty 7.6315789%, validation loss **0.465263158**, old diagnostic
  **0.559695423**.
- Confidence inflation: same finalized metrics as clean.
- Unavailable suppression: coverage 0%, false accept/reject 0/0, uncertainty 100%,
  validation loss **0.2**, old diagnostic **0.294432265**.

Stage A optimum: **0.4889473684210527**; primal/dual gap 5.55e-17; tolerance
1e-8 loss units. Stage B cap: **0.4889473784210527**; actual worst loss remains
the Stage-A optimum. Cost and cost dual bound both **12,234.222880445304 ms**,
gap zero; cost certificate tolerance 1e-8 ms. Cap feasibility is checked at
1e-12 loss units; probability/coverage tolerances are 1e-12. Stage B uses HiGHS
primal/dual feasibility options 1e-10; Stage A uses existing SciPy defaults with
independent certificate validation. `solver-environment.json` records stage-specific
options and supersedes the generic defaults-only metadata entry in the preserved
initial fit report. The producer now records stage-specific options directly.
No numerical or scientific settings changed in making that reporting correction.

## Comparison with preserved policies

The six-policy `comparison.md` / `comparison.json` report every probability and
clean/per-attack loss, errors, uncertainty, coverage, cost and old objective.
Their concise clean coverage / worst validation loss / expected cost / worst old
cost-inclusive diagnostic / zero-clean-plan probability are:

- Original: 0% / 0.2 / 181.689941 ms / 0.201402410 / 100%.
- Legacy coverage 25%: 25% / 0.275 / 194.562842 ms / 0.276501772 / 75%.
- Legacy coverage 50%: 50% / 0.350 / 207.435743 ms / 0.351601134 / 50%.
- Legacy coverage 75%: 75% / 0.425 / 220.308644 ms / 0.426700496 / 25%.
- Informative contributors, old objective: same aggregate result as original.
- Informative contributors, reliability first: 90% / 0.488947368 /
  12,234.222880 ms / 0.583379634 / 5.2631579%.

Legacy coverage variants use their old contributor semantics, including active
zero-reliability Semantic. They are not reevaluated as if they had the new contract.
The new result has a different contributor requirement and coverage target; the
comparison is not evidence of superiority or measured efficiency improvement.

An additional objective-isolation diagnostic holds **both** informative
contributors and the 90% floor fixed while restoring the cost-inclusive optimizer.
`informative-coverage90-old-objective/policy.json` and
`optimization-isolation.json` show the same finalized losses, coverage and expected
cost as the lexicographic fit. Thus this pilot does **not** demonstrate an empirical
selection advantage from reordering the objectives. The synthetic conflicting-
cost/loss case demonstrates the implemented distinction; the real dataset's
coverage/roster constraints dominate this particular choice.

## Artifacts, checks and recommendation

New policy: `build/factual-reliability-first42/reliability-first/policy.json`.
Intermediate: `build/factual-reliability-first42/informative-old-objective/policy.json`.

- Artifact ID: `7163d5c448504374081be9133b9b9977a8d873cd36e30ea8e25985c86ab98550`.
- Policy ID: `5ceececda0584b0769f50427c3d3a00754c4f1c349019f87b567963a7733dd2e`.
- Matrix ID: `46d08e01ad61a347119b5b403cb3af35de83fe0e1a07844bf483ae1e6ea93d03`.

The fit was repeated, exported, reloaded and certificate validated, with numerical
equivalence at absolute 1e-12. Existing provider/episode/runtime interfaces work
with the opt-in contract. Four retained-report runtime checks cover both positive
strategies on correct/incorrect examples and agree with replay contributor counts,
scores and public status. Live resource checks used 16 loopback metadata requests
and **zero generation calls**. No verifier inference was repeated. Original input
and artifact hashes were checked unchanged. Exact initial fit-driver bytes are
archived locally; later readable-report code has separate provenance.
The new `approval-binding.json` separately binds the current user request's exact
digest, exploratory status, approved 90%/epsilon settings, complete new contracts
and artifact/context configuration digest. It does not overwrite the original
arithmetic, factual or coverage-variant approvals.

Recommend this as the next engineering-review candidate **if two informative
contributors and 90% expected clean coverage are the intended requirements**.
It is not universally best or ready for automatic activation. It still selects
an always-abstaining plan 5.263% of the time and cannot meet a product requirement
that every sampled plan be potentially decisive. A separately versioned,
prospectively approved planning-admissibility contract could require enough
positive-history potentially influential members before optimization. That rule
is only a proposal: no strategy is removed in the implemented experiment.

All informative verifiers remain in one modeled compromise component through
shared resources and conservative unknown dependencies. One compromised group
can corrupt all informative selected checks; suppression still destroys coverage.
Scope remains the constructed reference-assisted known-corpus capital-fact pilot
with procedural custody. These are exploratory development results, not held-out
robustness, publication readiness or proof of independent evidence.

## Commands, tests and ownership

The baseline function was initially invoked directly with an active custody guard;
the corresponding CLI is `python -m scripts.factual_reliability_analysis baseline`.
Do not rerun exclusive producers over existing output directories. Actual subsequent
commands were:

```powershell
.venv/Scripts/python.exe -m scripts.factual_reliability_analysis replay
.venv/Scripts/python.exe -m scripts.factual_reliability_analysis fit
.venv/Scripts/python.exe -m scripts.factual_reliability_analysis report
.venv/Scripts/python.exe -m scripts.factual_reliability_analysis isolate
.venv/Scripts/python.exe -m pytest tests/test_game_reliability_first.py tests/test_game_clean_coverage.py tests/test_game_foundation.py tests/test_game_build.py tests/test_game_offline.py tests/test_game_runtime.py tests/test_game_completion.py tests/test_game_research.py tests/test_game_collection.py tests/test_cost_calibration.py tests/test_dependency_aggregation.py tests/test_early_termination.py tests/test_vote_normalization.py -q
.venv/Scripts/python.exe -m pytest tests/test_game_reliability_first.py -q
.venv/Scripts/python.exe -m pytest tests/test_game_reliability_first.py tests/test_game_offline.py tests/test_game_runtime.py tests/test_game_build.py -q
git diff --check
```

The affected suite passed **601 tests**. Final focused coverage is **21 tests**
(overlapping counts), including reliable rejection influence, both aggregations,
zero/negative-history exclusion, structural/prerequisite/coverage/failure guards,
synthetic expensive-but-reliable preference, both-stage certificate tampering,
infeasible 90%, serialization/version mismatch, history-only reputation, held-out
parser isolation and public runtime parity. An initial new synthetic fixture
omitted explicit prior arguments; that fixture was corrected without relaxing
assertions. No new affected failure remains. The earlier 210-test legacy subset
also passed; this is not a claim that every repository/model/DB test was run.
An overly broad late finalizer-binding check initially broke two legacy
direct-replay failure-policy diagnostics. It was narrowed to mismatched contributor
semantics only; legacy diagnostic behavior and assertions are preserved.
The final affected rerun passed **154 tests**, including all 21 new regressions
and those legacy failure-policy cases. Counts overlap the 601-test suite. The
binding correction changes rejection of incompatible contributor versions, not
valid evaluated scores or outcomes. `post-validation.json` records current-code
artifact validation, original factual/coverage hashes and all ten preserved
arithmetic files. No test was removed or weakened.

This task adds `app/game/reliability_contract.py`,
`app/game/offline/reliability.py`, `scripts/factual_reliability_analysis.py`,
`tests/test_game_reliability_first.py` and this document. It extends owned
`app/game/execution_contract.py`, `finalization.py`, `models.py`, `policy.py`,
`artifacts.py`, `solver.py`, `offline/evaluation.py`, `offline/replay.py` and the
build-doc link. Prior uncommitted work and the empirical audit remain preserved.
No verifier/retriever/generator, database, API, frontend or unrelated orchestration
source/test was modified. Private/generated data remain ignored under `build/`.
No commits, pushes, merges or activation were performed.
