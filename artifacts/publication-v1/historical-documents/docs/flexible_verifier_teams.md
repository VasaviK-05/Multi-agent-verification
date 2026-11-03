# Flexible verifier teams: implementation and integration handoff

Work lives on `codex/flexible-verifier-teams`, in the isolated worktree
`<LOCAL_USER_HOME>/Multi-agent-verification/build/flexible-verifier-teams`.
Base: fetched `origin/main` at `0b3595e` (2026-11-02).
Original checkout: branch `codex/offline-policy-recording-pilots`, commit
`2c9f697439d1d1c2ed7c0a92645848c0f07f7e3f`. Its merge base with latest main
is `be61859`. Main contains the merged recording work plus deployment/audit
integration (`d9c19ad`, `3dc6824`) and capability fixes. Comparing the owned
code showed the current engine contracts on main, so main is the combined base.
No applicable AGENTS.md was found in the repository or checked ancestor paths.

Original uncommitted files were preserved in place: `app/game/execution.py`,
`app/game/offline/recording_adapters.py`, `tests/test_game_upstream_evidence.py`,
`tests/test_project_collection_adapter.py`, and untracked
`app/benchmark/resource_diagnostics.py`. None are copied over the integrated main
implementation. The separate index/provenance incident remains out of scope.

## Contract

Set `ExecutionContract.team_requirements` to
`TeamRequirements(version="flexible_team_requirements_v1", minimum_selected=1,
minimum_informative=1)` and bind it into the planning context before enumeration
or fitting. Use `(2, 2)` for the explicit paired minimum-two configuration.
Use `(1, 2)` to permit singletons in planning but require two informative
contributors: those singletons necessarily finalize uncertain. This deliberately
shows why the two minima must be separate.

The option requires `informative_history_influence_v1` (execution v3 or v4).
Omitting it retains the historical difficulty-dependent execution/contributor
floor. Omitted options are not serialized: old identifiers and policy bytes are
not silently migrated. New contracts change evaluation, context, matrix and
policy identities. Bound finalization rejects old/new team contract mismatches.
No default API configuration, policy registry or deployment is changed.

Existing exhaustive enumeration already visits every eligible nonempty subset;
its minimum now reads the explicit selected-team setting. Both reputation-weighted
and dependency-group aggregation remain available. Capability, budget and candidate
prerequisite exclusions remain enforced. Larger teams remain even at zero fitted
probability. Game runtime executes the complete selected team and explicitly
reports early stopping disabled. The adaptive non-game stopping heuristic retains
its old floor; this feature introduces no sequential team expansion.

## Decision examples and limits

A factual arithmetic rule report from a verifier with positive informative
history can decide `307 + 503 = 810` by itself if it actually covers arithmetic
and crosses the configured threshold. A strong rejecting report can also reject;
one report does not imply acceptance. Missing reports, abstentions, structural-only
rule outputs, missing required coverage, or unresolved requirements produce
uncertainty. Selected failures still obey the failure contract.

A singleton with positive reputation influence has a normalized score equal to
its signed report confidence, for both supported aggregations. The normalization
does not establish calibrated correctness or a special reliability guarantee.
Neutral reputation (posterior mean 0.5) has zero informative influence and cannot
satisfy the contributor minimum, even if the numerical aggregation's fallback
produces a directional score. Negative reputation also does not count. Conflicting
reports retain the existing weighted/group score: equal opposing evidence can be
uncertain; unequal influence can decide only after all coverage and contributor
guards pass. The threshold remains strict (`score > threshold` or
`score < -threshold`). New opt-in contracts record `decision_threshold` alongside
contributor, coverage and execution reasons for uncertainty.

Semantic still needs a real reference (judgment-label lists are rejected) and
must not be configured unavailable. A reference is only a prerequisite, not
proof of factual usefulness. Semantic supplies expected semantic-comparison
coverage; it cannot alone satisfy arithmetic or direct-fact requirements. Actual
semantic-comparison coverage still needs the existing output metadata contract.
If Semantic is ineligible, enumeration considers the eligible remaining subsets.

Analyzer requirements feed capability eligibility and coverage; subject domain
and task identity bind isolated history and routing. Difficulty remains in the
analyzer/selector configuration and task routing signature. Explicit team minima
do not invent an easy/medium/hard-to-team-size mapping. Historical evidence here
is restricted to constructed additions, pinned population/area/currency facts,
and constructed paraphrase frames, all classified `general` with unknown subject
domain. It does not support broad scientific/legal/medical/domain or difficulty
claims. Unknown tasks, unsupported requirements and missing compatible policies
remain explicit failures rather than receiving an improvised policy.

## Offline comparison

Run from this worktree with the original environment:

```powershell
<LOCAL_USER_HOME>/Multi-agent-verification/.venv/Scripts/python.exe -m scripts.evaluate_flexible_teams --source <LOCAL_USER_HOME>/Multi-agent-verification/build/multitask-policy42 --output artifacts/flexible-teams-v1
```

The output directory must be new. The runner validates original resource-bound
history/task contracts, then replays the same independently recorded full-roster
examples with only the team minima changed. Recorded inputs attest
`complete_team_independent_v1`; report identities, candidate rosters, missing
recordings and resource observations are checked by the existing replay path.
No verifier is instantiated and no inference, download or index rebuild occurs.
This supports counterfactual team aggregation, not newly measured runtime costs
or upstream attack robustness. Historical attempt costs remain estimates for
selected teams; shared setup/cache effects are not remeasured.

Primary settings are fixed: original calibrated full-roster budget, history,
threshold 0.55, attack specification/dependency groups, losses (1,1,0.2),
90% clean decision coverage and reliability-first objective with epsilon and
cost tolerance 1e-8. No coverage relaxation, manual probabilities or attack tuning. In this study the observed shared dependencies and shared-unknown treatment connect the roster into one failure group; a group corruption can affect every selected verifier. Larger teams therefore do not establish independent fault tolerance.
Development labels alone form payoffs. Source-known study reservations are not
blinded held-out evidence. Reserved final-test candidates have no recorded
verifier outputs; held-out metrics are unavailable and no final payload is opened.
Additional evaluation needs resource-compatible independent complete-roster
recordings for the reserved final partition after policy freeze. Other domains
and difficulty strata need separately labeled compatible history/development/test
records and policies; neutral sparse history is not a substitute.

Artifacts: `artifacts/flexible-teams-v1/comparison.json` summarizes feasibility,
size probabilities and policy-weighted development attack metrics. Each cohort
and minimum has `enumeration.json` (all feasible strategies and exclusions),
`strategy-diagnostics.json` (every strategy/attack, including singleton vulnerability,
coverage, uncertainty, errors, selective risk and reasons), `context.json`,
`contract.json`, `matrix.json`, `solution.json`, and, only when optimal,
`policy.json`. Selective risk is null when coverage is zero. Error counts are
expected counts; divide by `examples` for rates. Estimated costs are in ms.
`input-hashes.json` authenticates the original study inputs and is checked after
replay. `baseline-reproduction.json` compares every minimum-two payoff and axis
against its historical development matrix. `file-manifest.json` lists every changed
source file and generated artifact with hashes. Historical policies/bundles and minimum-two artifacts remain untouched.

Integration later should consume each new context/contract/policy together,
validate exact compatibility and resource provenance, and complete held-out
validation before any separate activation. Infeasible results have no policy to
register. No commit, push, merge or activation was performed.

## Changed files

- `app/game/execution_contract.py`: versioned, strictly validated independent minima;
  omit absent option for historical serialization.
- `app/game/models.py`: separate planning and informative minimum accessors.
- `app/game/finalization.py`: enforce the informative minimum and bound team contract;
  explain threshold uncertainty only for new contracts.
- `app/game/execution.py`: runtime audit reports both selected-team and informative minima.
- `scripts/evaluate_flexible_teams.py`: reproducible offline paired replay and refit.
- `tests/test_flexible_teams.py`: singleton decisions, exclusions, neutral history,
  abstention, missing coverage, conflicting reports, old/new identity checks,
  independent minima and larger-team enumeration.
- `docs/flexible_verifier_teams.md`: behavior, evidence limits and handoff.
- `artifacts/flexible-teams-v1/**`: new comparison artifacts only.


## Completed results (development only)

Each cohort has 40 development examples (20 correct, 20 incorrect).
The minimum-two configuration has 14 strategies over seven teams; minimum-one
has 16 strategies over eight teams, retaining both aggregation methods and all
team sizes 1â€“4 where coverage permits them. Non-covering teams remain listed
with exclusion reasons. No probability was edited by hand.

- Arithmetic, minimum two: infeasible, maximum achievable clean decision coverage
  82.5%. Arithmetic, minimum one: an optimal policy was actually fitted; rule
  singleton with reputation-weighted aggregation has probability 1.0. Team-size
  probabilities are (1, 0, 0, 0). Clean coverage 100%, uncertainty 0%, false accepts
  0, false rejects 0, decision loss 0, selective risk 0. Estimated cost 9.6782 ms.
- Factual, minimum two: infeasible, maximum clean coverage 37.5%.
  Factual, minimum one: an optimal policy was actually fitted; evidence singleton
  with reputation-weighted aggregation has probability 1.0. Size probabilities
  are (1, 0, 0, 0). Clean coverage 97.5%, uncertainty 2.5%, false accepts 0,
  false rejects 1/40 (2.5% of all examples), decision loss 0.03, selective risk
  1/39 (2.5641%). Estimated cost 188.7989 ms. The uncertain case has threshold
  and achieved-coverage deficits; individual reasons are in the diagnostics.
- Semantic comparison, minimum two: infeasible, maximum clean coverage 0%.
  Minimum one: still infeasible, maximum clean coverage 57.5%. Semantic's
  history posterior mean is 0.5; a semantic singleton is not informative.
  No semantic policy was fitted. Its 57.5% maximum is a strategy diagnostic,
  not an optimized deployed or held-out policy metric.

Infeasible configurations have no selected probabilities or policy-level error,
coverage or cost estimates. Their per-strategy diagnostics remain available;
maximum coverage above is an infeasibility bound, not a selected policy result.
All three minimum-two payoff matrices exactly reproduce the original historical
strategy/attack axes and values (maximum absolute difference 0).

For both fitted singleton policies, forced-support corruption yields 20/40 false
accepts, forced rejection yields 20/40 false rejects, selective risk 50%, and
decision loss 0.5. Suppression yields 100% uncertainty, zero coverage and undefined
selective risk; decision loss is 0.2. Confidence inflation leaves these clean
metrics unchanged under the declared report corruption adapter. This is a
report-level stress test, not measured upstream compromise performance.
Larger teams remain available with zero selected probability for the two fitted
policies. Neither fitting success nor clean coverage is evidence of broad
robustness, domain adaptation, or held-out improvement.

Relevant regression runs passed: 397 tests covering replay/planning/selector/
stopping, 257 covering aggregation/reliability/coverage/runtime/historical bundles,
73 after runtime audit changes, and the final 7 flexible-contract tests. These
runs overlap. `git diff --check` passed. `verification.json` records policy IDs,
compatibility rejection, input hashes, exact historical payoff reproduction and
unchanged bundle bytes. No held-out evaluation, commit, push, merge, inference,
index rebuild, download or API activation occurred.

Later integration can use the arithmetic and factual `minimum-1` directories'
`context.json`, `contract.json`, and `policy.json` together. The opt-in setting is
`flexible_team_requirements_v1` with selected/informative minima `(1, 1)`.
The semantic and all minimum-two directories carry infeasibility results only.
The exported policies remain offline candidates pending resource-compatible
held-out recordings, validation, and a separate integration/activation task.
