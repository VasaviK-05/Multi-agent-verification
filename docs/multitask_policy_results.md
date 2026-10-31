# Task-conditioned pilot results and ownership handoff

The 2026-10-31 engineering campaign completed **240 history/development candidates
and 960 verifier attempts**, without study retries. All three primary 90%-coverage
problems are infeasible. No qualifying reliability-first policy was created.
This is a contributor/informativeness and decision-margin limitation under the
fixed settings, not evidence that task conditioning produces better policies.

The implementation and exact commands are in
[the workflow](multitask_policy_workflow.md). All measurements below are exploratory
development diagnostics, not held-out research evidence. Historical arithmetic,
capital, clean-coverage and reliability-first artifacts remain preserved.

## Data, resources and integrity

Each cohort has 60 related-example groups, split seed42 into 20 history, 20
development and 20 outcome-free reserved groups. Each has paired independently
labelled correct/incorrect answers. Only the 80 history/development candidates per
cohort were collected. Every candidate received the same four eligible verifiers
once; failures and abstentions were retained. No final outcome was collected or
opened after preparation. Reservations remain procedural/source-known, not blinded.

Arithmetic uses constructed integer additions and off-by-one negatives. Semantic
equivalence uses independent predicate frames, active/passive positives and
different-action negatives; it does not measure factual truth. Factual questions
cover population, currency and area from retained GeoNames countryInfo and pinned
mledoze countries snapshots. Usage terms and exact file hashes are preserved under
`build/multitask-policy42/sources/` and `study-audit.json`.

The factual source audit considers 250 rows, selects 60 and excludes 190 before
outcomes. Reasons may overlap: 92 outside single-token-country scope, 60 prior
capital groups, 25 currency disagreement/multiple values, 24 predeclared
transition/dispute exclusions, 16 outside the seed42 sample and one missing area.
No question-ID overlap with prior arithmetic/capital preparation or reserved
metadata was found. Source files were previously inspected; India also appeared
in older public preparation, so no unseen-country/source claim is made.

The isolated index-v2 has 57 source-fact documents, genuinely built through the
existing public index utility with installed embedding weights. One factual group
per split is absent from the corpus; these examples remain in the study. Installed
CPU embedding/NLI models and local llama3.2:3b were used; there were no downloads or
paid services. All three collections share exact resource bindings. The workers
overlapped on one machine; costs include shared-machine contention.

`collection-integrity.json` verifies frozen preparation hashes, unique start
ledgers, exact journal/export equality, resource observations and linked timing
exports. All 960 attempts are accounted for. One arithmetic-development Confidence
call returned `provider_unavailable` after a 60-second timeout; its report and
duration remain included. There are no such error reports in the other cohorts.
This differs from ordinary returned uncertainty and from collection-integrity gaps.

Seven fixed software fixtures separately validated the evidence output contract
against actual resources: four controlled cases and three installed-NLI cases,
using a controlled retriever. These are software checks, not additional study
candidates, retrieval-quality measurements, reputation observations or calibration
samples. The resource validation issued zero generation and eight metadata calls.
All 21 cohort/budget contexts passed the unchanged applicable readiness gates.

## History-only influence and measured costs

All means below use fresh isolated Beta(1,1) histories. The subject domain remains
`general/unknown`; the enclosing versioned task/history binding prevents reuse of
capital or other-task expertise. Variances, successes/failures and effective
log-odds/group strengths are in every budget report.

- Arithmetic: Rule 40 directional observations, mean 41/42; Confidence 37,
  mean 34/39; Semantic 23, mean 16/25; Evidence zero, prior mean 1/2.
- Semantic equivalence: Confidence 25, mean 26/27; Semantic 40, mean 21/42;
  Evidence and Rule zero, prior mean 1/2. Semantic supported all 40 history
  candidates, including all incorrect ones, so its influence is zero.
- Factual: Evidence 38, mean 38/40; Confidence 13, mean 11/15; Semantic 40,
  mean 21/42; Rule zero, prior mean 1/2.

Each measured cost is the mean of all 80 first/subsequent verifier attempts per
cohort. No failures or warmups are removed. Units are verifier-attempt wall
milliseconds, not money or request latency:

- Arithmetic: Confidence 21127.605639, Evidence 81.452711, Rule 9.678210,
  Semantic 39.598705. Full-roster primary budget **21258.335265 ms**.
- Semantic: Confidence 15778.139944, Evidence 31.851542, Rule 0.109292,
  Semantic 42.323445. Primary budget **15852.424224 ms**.
- Factual: Confidence 15732.456319, Evidence 188.798949, Rule 0.104605,
  Semantic 43.686593. Primary budget **15965.046465 ms**.

Initialization/resource hashing/checkpoint overhead lies outside `verify` timers.
Timing differences do not demonstrate an efficiency improvement.

## All-strategy conclusions

Every cohort has seven feasible teams, each with both aggregation methods: 14
strategies. Required coverage means arithmetic teams contain Rule, semantic teams
contain Semantic, and factual teams contain Evidence. All other genuine roster
members remain eligible subject to the existing prerequisite/minimum-two guards.
Team sizes two, three and four are retained; no diversity or randomization is forced.

All seven distinct team-cost breakpoints per cohort were evaluated. Primary and
all sensitivity budgets are infeasible at q=0.90. The complete team/aggregation,
cost, contributor/reason-count, clean/per-attack loss/error/uncertainty/coverage
reports are in `build/multitask-policy42/cross-context-results.json` and `.md`.
Each cohort's `budget-results.json` and `budget-XX/report.json` retain the original
details. Infeasible policies have **undefined probabilities and marginals**, not a
zero distribution. No constrained artifact, certificate or positive-probability
claim is fabricated.

- **Arithmetic maximum clean coverage: 82.5%.** Rule+Confidence, with either
  aggregation, makes 33/40 correct decisions (14 accepts, 19 rejects), zero false
  acceptances/rejections and seven uncertainties. Clean validation loss is 0.035;
  estimated cost 21137.283849 ms. Forced-support/rejection attacks yield 95%
  coverage, respectively 19 false accepts or 19 false rejects, loss 0.485; suppression
  yields zero coverage/loss 0.2. Confidence inflation retains the clean metrics.
  The separate old cost-inclusive worst-case diagnostic is 0.584430570.
  Adding more roster members does not raise maximum clean coverage.
- **Semantic maximum clean coverage: 0%.** Confidence is the sole informative
  contributor; every strategy fails minimum two, even when its preliminary score
  is decisive and Semantic supplies a genuine comparison measurement. All scenario
  validation losses are 0.2 with 100% uncertainty. A similarity measurement cannot
  create a second informative contributor or an independent source.
- **Factual maximum clean coverage: 37.5%.** Evidence+Confidence, with either
  aggregation, makes 15/40 correct decisions (eight accepts, seven rejects), zero
  false accepts/rejects and 25 uncertainties. Clean loss is 0.125; estimated cost
  15921.255267 ms. Forced support yields 47.5% coverage/eight false accepts/loss
  0.305; forced rejection yields 47.5%/11 false rejects/loss 0.38. Suppression yields
  zero coverage/loss 0.2; confidence inflation retains the clean metrics. The old
  cost-inclusive worst-case diagnostic is 0.479725706. Extra members do not improve
  maximum coverage.

These are individual-strategy diagnostics, **not fitted q=0.90 mixtures** or a
post-outcome selection of primary settings. Any mixture's clean coverage is bounded
above by the maximum individual finalized coverage; that establishes infeasibility
without relaxing targets or pruning strategies.

## Preserved unconstrained comparison artifacts

The old cost-inclusive objective was independently fitted for each new cohort,
separately from historical artifacts and the infeasible primary formulation:

- Arithmetic chooses reputation-weighted Evidence+Rule with probability one,
  estimated cost 91.130921 ms; cost-inclusive objective 0.200428683.
- Semantic chooses reputation-weighted Rule+Semantic with probability one,
  estimated cost 42.432737 ms; objective 0.200267673.
- Factual chooses reputation-weighted Evidence+Rule with probability one,
  estimated cost 188.903554 ms; objective 0.201183232.

For each comparison, all other 13 strategy probabilities are zero; all 14 are
serialized. Each has zero coverage, zero false acceptance/rejection, 100%
uncertainty and validation loss 0.2 in clean and all four attack scenarios.
Verifier marginals are one for each selected member and zero for the others;
reputation-weighted aggregation marginal is one, dependency-group zero. All mass
is on zero-clean-coverage strategies. This is cheap abstention under that objective,
not useful verification, robustness or evidence of aggregation superiority.

The two aggregations have identical finalized scenario metrics for all semantic
and factual teams. Arithmetic metrics also agree except for confidence inflation
on Rule+Semantic and Evidence+Rule+Semantic: weighted coverage/loss 47.5%/0.105
versus grouped 30%/0.14. Both have the same larger worst-case loss. The chosen
always-abstaining comparison teams have equivalent payoffs across aggregations;
the solver's weighted allocation is not evidence of superiority.

The only new PolicyArtifacts are clearly labelled diagnostics:

```text
build/multitask-policy42/arithmetic/unconstrained-comparison/policy.json
build/multitask-policy42/semantic/unconstrained-comparison/policy.json
build/multitask-policy42/factual/unconstrained-comparison/policy.json
```

All were exported/reloaded, certificate-validated and compared against an
independent payoff reconstruction/refit with matrix/probability absolute tolerance
1e-12 (relative zero); reputation records agree exactly. Source revision, working
source digests, seeds, configuration/request/manifest/calibration IDs and versions
are retained in `fit-provenance.json`. The solver environment is CPython 3.11.5,
NumPy 2.4.6, SciPy 1.17.1/HiGHS 1.12.0, Pydantic 2.13.5. No numerical certificate
for a qualifying primary policy exists because that problem is infeasible.

## Decision diagnostics and owner handoff

`decision-diagnostics.json` contains all clean strategy status/guard counts and
representative correct/incorrect/boundary cases, complete raw reports and decision
details. It uses retained development records only. `aggregation-equivalence.json`
records the same-team comparisons; full per-attack outcomes remain in each
`development-evaluation.json`.

- Arithmetic Rule+Confidence: two contributor failures and five threshold-only
  uncertainties. For `addition-377-613-correct` (990), Rule contributes
  +3.713572067 while Confidence contributes -1.916922612. The denominator is
  5.630494679, giving score 0.319092648, inside ±0.55 despite two contributors.
  This is intended disagreement handling, not faulty arithmetic. Confidence's
  retained samples/judgments are the precise verifier-owner reproducer; do not
  change its algorithm or threshold in this workflow.
- Semantic `frame-Alex-correct`: preliminary score 1.0, but only Confidence
  contributes; Semantic's reputation is 0.5/zero log odds. The semantic owner or
  future study owner should review its existing public `comparison_mode` contract.
  Current `question_answer` mode embeds a question containing the reference as well
  as the answer. A preregistered answer-only comparison may be worth studying on
  fresh groups; it is a hypothesis/new configuration, not an applied repair or a
  guarantee of useful equivalence detection. Never rewrite references to rescue it.
- Factual Evidence+Confidence: 21 minimum-contributor failures, one missing achieved
  coverage case and three threshold-only uncertainties (guard reasons can overlap
  preliminary uncertainty). For `EC-correct`, Evidence contribution 2.916297020
  and Confidence contribution -1.011600912 over denominator 3.956039891 give
  score 0.481465344, correctly uncertain. The verifier/NLI owner can inspect
  retained numeric/source-snapshot judgments; software probes passing does not
  establish adequate performance on population, area or currency questions.

No teammate-owned implementation defect was inferred from these limitations.
Rule remains arithmetic-only; generic logical consistency remains unsupported by
achieved-coverage evidence. Actual shared embedding/NLI pathways and conservative
shared-unknown dependencies connect the roster into one compromise group. A single
group compromise can therefore affect all informative verifiers in this declared
report-corruption model. Contributor count is not evidence independence.

The next defensible experiment is a **new preregistered semantic-reference study**
using a reviewed public comparison configuration and genuinely informative second
checker, plus a separate numeric-factual/NLI owner review. It requires fresh grouped
recordings and cost calibration if configuration/resources change. Do not lower q,
thresholds or contributor protections after viewing this data. Do not claim useful
cross-task selection until more than one task has a qualifying policy and routing
plus measurements support that conclusion. No new experiment is authorized or run
by this handoff.

## Runtime, validation and ownership

Actual analyzer → explicit prepared-question/task/budget route → captured plan →
provider → selected-team finalizer matched retained replay for both correct and
incorrect development examples for each diagnostic policy. The provider also held
the old capital artifact to check absence of cross-task fallback. Primary routes
fail explicitly as infeasible. Unknown requirements, outside-study requests,
missing references and incompatible budgets fail safely. Existing resource-change
guards remain mandatory. Runtime used **zero generation / 24 metadata requests**.
This is retained-report execution, not fresh live inference or final evaluation.

Pre-change focused/affected selections passed 666 tests after two Windows sandbox
atomic-rename permission failures passed outside the sandbox. Four new validation
gaps were reproduced and fixed after collection, plus explicit task-isolated
pooling validation; 144 relevant post-change tests passed. An overbroad initial
finalizer check broke two legacy diagnostic replay cases; limiting complete-contract
strictness to v4 restored their original semantics without weakening v4 protection.
The final focused suite passed **219 tests** outside the filesystem sandbox;
with 438 broader affected tests and 14 evidence tests, the selected commands
account for **671 passing tests**, with no remaining failures. `git diff --check`
and conflict-marker checks passed. Details are recorded in the local validation handoff.
Historical evidence probes remain passing, not reproduced baseline failures.

Current-task source changes are confined to `app/analysis/task_analyzer.py`,
`app/decision/coverage.py`, `app/game/task_conditioning.py`, game context/execution/
artifact/finalization bindings, offline collect/collection/evaluation/replay and
budget sensitivity, research readiness, the thin `scripts/multitask_policy42.py`
producer, directly supporting tests and these docs. Existing uncommitted
coverage/reliability/previous-pilot work and `docs/game_empirical_build_audit.md`
were preserved. No verifier/retrieval/generation, DB, API or frontend paths changed.
No production reputation writes, final evaluation, commits, pushes or merges ran.

Exact current-task changed/new files (earlier dirty workflow files remain separate):

```text
app/analysis/task_analyzer.py
app/decision/coverage.py
app/game/artifacts.py
app/game/execution_contract.py
app/game/finalization.py
app/game/models.py
app/game/task_conditioning.py
app/game/offline/budget_sensitivity.py
app/game/offline/collect.py
app/game/offline/collection.py
app/game/offline/evaluation.py
app/game/offline/replay.py
app/game/research/readiness.py
scripts/multitask_policy42.py
tests/test_game_task_conditioning.py
docs/game_policy_build.md
docs/multitask_policy_workflow.md
docs/multitask_policy_results.md
```
