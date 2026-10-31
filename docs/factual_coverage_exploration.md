# Exploratory clean-coverage variant (2026-10-30)

This is an explicitly authorized development exploration, not a primary paper
configuration or held-out result. The original policy, approval, calibration and
recordings remain unchanged. No inference, recalibration, final-test access,
production writes or API activation occurred.

## Diagnosis before modification

`build/factual-coverage-exploration42/all-strategies.md` compares all fourteen
strategies, including every team's estimated cost, clean/per-attack validation
loss, false acceptance/rejection, coverage, worst objective, contributor histogram
and finalization reason counts. Its JSON companion and `original-evaluation.json`
retain complete machine-readable outcomes. Diagnosis ran before changing engine
code, using the original public replay/finalization workflow. Actual effective
weights/confidence/group influence for correct and incorrect examples of every
strategy are retained in `effective-weight-examples.json`.

History is unchanged: Evidence and Confidence have 40 successes/0 failures,
posterior 41/42; log-odds weight log(41)=3.713572 and group reliability 20/21.
Semantic has 20/20, posterior 1/2 and zero weights; Rule has no directional
observations, prior 1/2 and zero weights. Rule abstains on these factual examples.
Semantic supports both answer classes; its similarity is not independent factual
evidence. No development labels update reputation.

All clean false acceptance/rejection counts are zero. Clean coverage / validation
loss / worst cost-inclusive objective for all fourteen strategies:

- Confidence + Evidence, reputation: 95% / 0.01 / 0.604600591.
- Confidence + Evidence, group: 95% / 0.01 / 0.604600591.
- Evidence + Rule, reputation: 0% / 0.2 / 0.201402410.
- Evidence + Rule, group: 0% / 0.2 / 0.201402410.
- Evidence + Semantic, reputation: 0% / 0.2 / 0.201799858.
- Evidence + Semantic, group: 100% / 0 / 0.501799858.
- Confidence + Evidence + Rule, reputation: 95% / 0.01 / 0.604601571.
- Confidence + Evidence + Rule, group: 95% / 0.01 / 0.604601571.
- Confidence + Evidence + Semantic, reputation: 95% / 0.01 / 0.604999019.
- Confidence + Evidence + Semantic, group: 97.5% / 0.005 / 0.599999019.
- Evidence + Rule + Semantic, reputation: 0% / 0.2 / 0.201800838.
- Evidence + Rule + Semantic, group: 100% / 0 / 0.501800838.
- All four, reputation: 95% / 0.01 / 0.605000000.
- All four, group: 97.5% / 0.005 / 0.600000000.

The original result is not a decision implementation defect. Evidence + Rule has
only one contributor on every clean example, so the minimum-two guard applies.
Its two aggregations have identical payoffs; solver allocation is not superiority.
Its 181.689941-ms estimated cost is lower than other feasible teams. Abstention
costs only 0.2, whereas coherent forced directional errors raise useful teams'
worst validation loss to approximately 0.5. Minimax therefore rationally selects
cheap abstention under the original approved objective and shared-group threat.

The existing group contributor contract differs from log-odds: it counts active
positive-confidence reports, including zero-reliability Semantic. Semantic carries
no weighted group mass when Evidence is active, but counts as a second active
report. This is documented existing behavior, not independent informative evidence
and not a guard change in this exploration. Coverage/availability/failure checks
remain in force; no new capability or contributor is invented. Mixed uncertainty
in other teams also reflects numerical score bands and one Confidence abstention.

## Additive constraint and certificate

The new obligation is `sum_s x_s Q_s >= q_min`, where Q is recomputed from actual
**finalized clean-development public decisions**, not preliminary numerical scores,
expected capabilities or verifier agreement. The producer accepts only the
training manifest with metadata-only final reservation. It checks source identities,
all payoff cells and the original evaluation binding, and replays clean source
records to reject stale/altered cached coverage. Neither reputation nor the source
reports change. The objective, original budget 12,955.553737 ms, resource weight
0.1/B, losses 1/1/0.2, threshold 0.55, dependencies and guards remain unchanged.

The existing `solve_minimax` adds one inequality to the same HiGHS LP. Its dual
witness has attacker distribution y and coverage multiplier eta>=0. The checked
lower bound is `min_s (M_s y - eta Q_s) + eta q_min`; it is compared with the
recomputed primal worst-case objective. Validation also checks coverage slack,
probabilities, axes, residuals and version semantics. Infeasible targets return
explicit infeasibility without relaxing the target or producing a policy.

`finalized_clean_development_coverage_v1` binds Q, target, parent matrix, source
evaluation and training identity. `clean_coverage_json` participates in context
compatibility; the matrix embeds the matching constraint. The parent matrix check
prevents changing costs/payoffs while claiming original lineage. Policies use
`game_policy_clean_coverage_v1`; artifacts use
`deployable_game_policy_clean_coverage_v1`; certificates use
`clean_coverage_dual_v1`. A legacy version cannot silently contain a constraint,
nor can a constrained policy match an unconstrained episode. Optional fields are
omitted when absent, preserving old serialized identities and semantics. No pooling
combination is implied; it explicitly requires a separately defined contract.

Only the replay planning-category comparison strips the fitting obligation: the
source example's analyzer/roster/prerequisite inputs have not changed. Runtime
episode compatibility retains the entire obligation. Feasibility enumeration,
budget validation, achieved coverage and participant/failure guards are unchanged.

## Original versus exploratory variants

Each variant has exactly two positive strategies: reputation-weighted Evidence +
Rule with probability `1-q_min`, and group-aggregated Evidence + Semantic with
probability `q_min`. The other twelve strategies retain zero probabilities. This
mixture is the constrained optimum, not a forced verifier/diversity choice.
Clean coverage is the exact policy-weighted expectation on these recordings;
finite realized sampling can vary.

- Original: coverage 0%; clean loss 0.2; estimated cost 181.689941 ms; worst
  objective 0.201402410.
- Target 25%: coverage 25%; clean loss 0.15; estimated cost 194.562842 ms;
  worst objective 0.276501772. Artifact
  `build/factual-coverage-exploration42/coverage-25/policy.json`.
- Target 50%: coverage 50%; clean loss 0.10; estimated cost 207.435743 ms;
  worst objective 0.351601134. Artifact
  `build/factual-coverage-exploration42/coverage-50/policy.json`.
- Target 75%: coverage 75%; clean loss 0.05; estimated cost 220.308644 ms;
  worst objective 0.426700496. Artifact
  `build/factual-coverage-exploration42/coverage-75/policy.json`.

For target q, clean and inflation have zero false accept/reject, uncertainty 1-q,
coverage q and validation loss 0.2(1-q). Forced support has expected false accepts
20q out of forty, zero false rejects, uncertainty 1-q and loss 0.2+0.3q; forced
rejection swaps the error type. Both forced attacks tie for the worst objective.
Suppression has no false accept/reject, uncertainty 1, zero coverage and loss 0.2.
Estimated cost is the same for each attack and is reported separately from loss.
Every variant's per-attack cost-inclusive objective is loss plus lambda times
estimated cost. `exploratory-results.md`, `variants-summary.json` and each
`coverage-*/report.json` contain full counts, objectives and every probability.

The dual multiplier is 0.3003974481120747 for each target, with zero coverage
residual. All artifacts were exported/reloaded, certificate validated at 1e-8,
and fitted twice with numerical equivalence at 1e-12. There are four successful
retained-report runtime/replay checks per variant: both positive strategies on a
correct and incorrect example, with live real resource observations. These are
conditional execution checks, not sampled performance evidence. The network guard
recorded 48 metadata calls and **zero generation calls**. A subsequent independent
clean-source replay check exactly matched all exported Q vectors and matrices.

## Recommendation and ownership

Use **q_min=0.50 as the next exploratory engineering candidate**, if a half-population
clean decision requirement is worth the explicit additional worst-case objective
0.150198724 and estimated attempt cost 25.745802 ms versus original. This is a
concrete tradeoff for review, not a universal best or an approved paper setting.
Keep the original as the unconstrained baseline. Do not activate either result
based on this development exercise alone or select a publication target by the
most attractive observed metric.

Applicability remains the reference-assisted, known-corpus constructed capital
pilot, single-token country analyzer context, with procedural custody. All
informative verifiers are in one connected compromise group under the actual
shared models plus conservative shared-unknown assumptions. Corrupting one group
can corrupt all informative selected checks. A clean coverage constraint creates
neither independent evidence nor attacked coverage: suppression still yields zero.
No verifier/retrieval/generation, DB/API/frontend or unrelated orchestration change
is required. Any future independent-dependency claim or operational tradeoff is
owned by the study owner and needs evidence/approval, not removal of protections.

## Reproduction and changed files

Completed commands (exclusive outputs; do not overwrite the original campaign):

```powershell
.venv/Scripts/python.exe -m scripts.factual_coverage_analysis diagnose
.venv/Scripts/python.exe -m scripts.factual_coverage_analysis variants
.venv/Scripts/python.exe -m scripts.factual_coverage_analysis verify
.venv/Scripts/python.exe -m pytest tests/test_game_clean_coverage.py tests/test_game_foundation.py tests/test_game_build.py tests/test_game_offline.py tests/test_game_runtime.py tests/test_game_completion.py tests/test_game_research.py -q
.venv/Scripts/python.exe -m pytest tests/test_game_clean_coverage.py -q
git diff --check
```

The combined suite passed 336 tests; after adding further target/parser/binding
regressions, all 26 focused coverage tests passed (overlapping counts). No new
affected-test failure remains. The earlier 232-test legacy subset also passed.
Infeasible targets, corrupt dual/coverage diagnostics, axes/parent payoff changes,
version downgrades, altered clean caches, held-out parser access and history
contamination are covered. Existing guard and runtime tests remain unchanged.

This task adds `app/game/coverage_contract.py`, `app/game/offline/coverage.py`,
`scripts/factual_coverage_analysis.py`, `tests/test_game_clean_coverage.py` and this
document. It extends owned `models.py`, `solver.py`, `policy.py`, `artifacts.py`,
`offline/evaluation.py` and `offline/replay.py`, plus the build-workflow doc link.
The prior task's uncommitted source/tests/docs and untracked empirical audit are
preserved. All recordings, source labels, final payloads and generated reports
remain ignored/local. No commits, pushes, merges or activation were performed.
