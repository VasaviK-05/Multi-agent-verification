# Experiment 3 resource-configuration sensitivity

SYNTHETIC / CONFIGURATION-SENSITIVITY ANALYSIS

This is a synthetic configuration analysis for the research lead. It is not an empirical Development result, not a Final Test result, and not a protocol approval. No coefficient and no budget is selected. Empirical collection was not run. Approval records were not modified.

## Calibration

Frozen method `mean_attempt_wall_time_ms_v1`, calibration `cc7e7ca8882f602b9854bf21b80b8a7bf70f6c70d05ccd12787322a84a12477d`, unit milliseconds. The calibration file hash matches the resource proposal: `7fbfe418c0c65c3782628ab5117b773f2fc4c8312c33d769934f76d2ff61a7f3`. The freeze does not authorize budget selection.

| Verifier | Mean attempt cost (ms) |
|---|---:|
| semantic | 70.472863335938499 |
| evidence | 107.93551665459138 |
| rule | 0.09707332161876063 |
| confidence | 14925.820978323463 |

The four means sum to 15104.326431635613 ms. That sum is the cost of using every verifier once. It is not used here as a protocol budget. The permissive grid point is the enumerated four-verifier team cost, which is this same sum, and it is marked `not_a_protocol_budget`.

Proposed decision-loss scale, still unapproved: false acceptance 1.0, false rejection 1.0, uncertainty 0.2. Those numbers convert milliseconds into loss. They are not themselves a resource coefficient.

## Coefficients

Each value is loss per millisecond. A scientifically justified coefficient cannot be derived from the calibration or from the synthetic fixture: the calibration has no utility scale, and the fixture does not score this roster. The rows are translations for the lead to choose among.

| Id | Loss per ms | How it is obtained |
|---|---:|---|
| no_resource_penalty | 0 | LossConfiguration.resource_weight allows zero. The penalty term is then identically zero. This is a decision-only reference, not a recommendation to drop cost from the protocol. |
| low | 1.3399597937725295e-05 | Proposed uncertainty loss 0.2 divided by the frozen confidence mean. One confidence attempt then costs the same as one uncertain decision. |
| moderate | 6.6997989688626471e-05 | Proposed false-acceptance loss 1.0 divided by the frozen confidence mean. One confidence attempt then costs the same as one false acceptance. |
| high | 0.0028379718168483666 | Proposed uncertainty loss 0.2 divided by the frozen semantic mean. One semantic attempt then costs the same as one uncertain decision, so a confidence attempt costs many false-acceptance losses. Rule is not the denominator: its mean is under a tenth of a millisecond and would only inflate the same ratio. |

The zero weight is included because `LossConfiguration.resource_weight` allows it (`ge=0`). `0.1/budget` is not included. The settings proposal rejects it because the penalty would change whenever the budget changes.

## Budgets

Budgets are milliseconds. They are the estimated costs `enumerate_strategies` assigns to particular teams, so a team at the cap is feasible and a team above the cap is not. None is a protocol budget.

| Id | Budget (ms) | Defining team | Role |
|---|---:|---|---|
| restrictive | 70.569936657557264 | rule, semantic | Estimated cost of the cheapest two-verifier team under enumerate_strategies. At the easy/medium floor this admits only that pair. At the hard floor it admits nothing, because every size-3 team costs more. |
| moderate | 178.50545331214863 | evidence, rule, semantic | Estimated cost of the only three-verifier team that excludes confidence. Every confidence team costs more, so confidence is infeasible at both participant floors. Equality is feasible: enumerate_strategies rejects only a strict cost excess. |
| confidence_entry | 14996.390914981021 | confidence, rule, semantic | Estimated cost of the cheapest three-verifier team that includes confidence. This is the smallest cap at which the hard floor can field confidence. It is a boundary used to explain the confidence cost, not a fourth protocol level. |
| permissive | 15104.326431635613 | confidence, evidence, rule, semantic | Estimated cost of the four-verifier team. It equals the sum of the frozen means and is the smallest cap that admits every team. The sum is not a selected protocol budget. |

Participant floors come from the implementation, not from an Experiment 3 approval. Floor 2 is the non-hard minimum (`max(2, plan.minimum_count)` with the easy/medium default). Floor 3 is the hard-band minimum. The same budget is offered to `full_minimax`, `fixed_reputation_weighted`, and `fixed_dependency_group`.

The synthetic plan gives every verifier the same expected capability. Expected coverage therefore does not eliminate teams. Real capability descriptors are not applied. Dependency structure does not enter the budget test.

## Feasibility

A configuration is infeasible when `enumerate_strategies` returns no strategy. Infeasible cells are every coefficient at the restrictive budget and the hard floor of 3. There are 4 such cells. The coefficient does not change feasibility. Confidence is absent from every moderate-budget team and present in every confidence-entry and permissive team.

Once any team is feasible, the cheapest team remains feasible at every higher budget. Raising the budget adds expensive teams. It does not replace the cheapest team.

## Decision loss and resource penalty

The checked-in synthetic fixture (`evaluation/experiments/experiment3/synthetic/results.json`) is read and not rewritten. Its verifiers are a, b, and c. Its recorded loss splits exactly into

```
decision loss = 1*false_acceptance + 1*false_rejection + 0.2*uncertainty
fixture resource penalty = 0.1 * fixture cost
```

on every row. The fixture cost is 2.0 in the fixture's own units. That 0.1 is not applied to milliseconds.

`Metrics.validation_loss` is the decision term. `summarize` adds `resource_weight * estimated_cost` to produce `mean_loss`. This analysis reports those terms separately. The overlay game is

```
cell loss = fixture decision loss for that aggregation and attack + coefficient * team cost in ms
```

The same fixture decision loss is assigned to every calibrated team that uses that aggregation. That is a sensitivity assumption, not a measurement of semantic, evidence, rule, or confidence.

No sampling uncertainty is available. The fixture is one deterministic synthetic case. Coverage and uncertainty below are the fixture's recorded rates, not rates for the calibrated roster.

| Configuration | Method | Worst decision loss | Coverage on that worst attack | Uncertainty on that worst attack |
|---|---|---:|---:|---:|
| controlled_synthetic_two_group | full_minimax | 0.2 | 0 | 1 |
| controlled_synthetic_two_group | fixed_reputation_weighted | 0.2 | 0 | 1 |
| controlled_synthetic_two_group | fixed_dependency_group | 0.2 | 0 | 1 |
| shared_unknown | full_minimax | 0.2 | 0 | 1 |
| shared_unknown | fixed_reputation_weighted | 0.2 | 0 | 1 |
| shared_unknown | fixed_dependency_group | 1 | 1 | 0 |

Declared-attack decision loss. Duplicate member lists with the same three losses are one row. Coverage and uncertainty for every row are in `sensitivity/results.json`.

| Configuration | Attack | Members | full_minimax | fixed reputation | fixed dependency |
|---|---|---|---:|---:|---:|
| controlled_synthetic_two_group | clean | none | 0 | 0.2 | 0 |
| controlled_synthetic_two_group | forced_support | a | 0 | 0.2 | 0 |
| controlled_synthetic_two_group | forced_rejection | a | 0.2 | 0.2 | 0.2 |
| controlled_synthetic_two_group | confidence_inflation | a | 0 | 0.2 | 0 |
| controlled_synthetic_two_group | forced_support | b, c | 0 | 0.2 | 0 |
| controlled_synthetic_two_group | forced_rejection | b, c | 0.2 | 0.2 | 0.2 |
| controlled_synthetic_two_group | confidence_inflation | b, c | 0 | 0.2 | 0 |
| shared_unknown | clean | none | 0.2 | 0.2 | 0 |
| shared_unknown | forced_support | a, b, c | 0.2 | 0.2 | 0 |
| shared_unknown | forced_rejection | a, b, c | 0.2 | 0.2 | 1 |
| shared_unknown | confidence_inflation | a, b, c | 0.2 | 0.2 | 0 |

Suppression rows are in the machine-readable extract and out of the overlay. The settings proposal sets suppression to unavailable.

Where the selected policy changes:

- The coefficient does not change which teams are feasible. The budget and the participant floor do.
- At zero weight, decision loss does not depend on the team, so every feasible team is optimal. Shared-unknown still keeps only reputation-weighted aggregation, because its worst decision loss is 1.0 against 0.2 for the other methods. The controlled two-group fixture ties all three methods at a worst decision loss of 0.2, so both aggregations stay optimal.
- Any positive coefficient, low or high, drops every team except the cheapest. Low, moderate, and high select that same team. They change the penalty level, not the argmin.
- Inside one floor the cheapest team does not change as the budget grows. Floor 2 selects rule and semantic. Floor 3 cannot field a pair, so it selects semantic, evidence, and rule. The restrictive cap at floor 3 has no feasible policy.
- Attack-level method order is not stable. In the controlled fixture, fixed reputation has decision loss 0.2 on clean, forced support, and confidence inflation, while the other two methods have 0, and all three tie at 0.2 on forced rejection. In shared-unknown, fixed dependency is best on clean, forced support, and confidence inflation (0 versus 0.2) and worst on forced rejection (1 versus 0.2). Worst-case minimax follows the forced-rejection column there and keeps reputation-weighted aggregation. Adding the same millisecond cost to every method does not reverse those orders.

Neither fixture configuration is empirical dependence.

## Confidence cost

Confidence is 14925.820978323463 ms, 0.98818183292581163 of the four-mean sum. Any cap below the confidence mean excludes confidence even before the participant floor. At floor 2 the cheapest confidence team is confidence plus rule. At floor 3 it is confidence plus semantic plus rule, because a pair is too small.

The loss gap that confidence must beat, relative to the cheapest team at the permissive cap, is `coefficient * (confidence team cost - cheapest team cost)`:

| Coefficient | Floor 2 gap (loss) | Floor 3 gap (loss) | Larger than 0.2 | Larger than 1.0 |
|---|---:|---:|---|---|
| no_resource_penalty | 0 | 0 | False | False |
| low | 0.19905569196577819 | 0.19855370747362783 | False | False |
| moderate | 0.99527845982889085 | 0.99276853736813919 | True | False |
| high | 42.159059279806101 | 42.052741325503405 | True | True |

Low prices one confidence attempt at 0.2. The gap versus the cheap pair is just under 0.2, so a team that removed one uncertain decision could still prefer confidence. Moderate prices that attempt at 1.0. The gap is just under one false acceptance, so only a near-complete error reduction would pay for confidence. High prices one semantic attempt at 0.2 and therefore prices confidence far above 1.0. On the proposed loss scale, no decision improvement can justify confidence, and a permissive budget would not change the cost-augmented optimum.

The high coefficient is the case in which resource cost dominates decision loss for any team that includes confidence. The low and moderate coefficients do not, except as the near-ties above. On the cheapest floor-2 team the penalties stay small, because that team excludes confidence.

## Recommendation

Do not freeze a coefficient or a budget from this file.

A scientifically justified coefficient cannot be derived from the existing evidence. The frozen calibration is a millisecond measurement. The synthetic fixture is a decision-loss example for a different verifier set. `research_settings_proposal_v1` and `experiment3_settings_proposal.json` both leave the coefficient unset and reject `0.1/budget`.

Alternatives for the research lead:

| Alternative | Consequence in this grid | Why it is not selected here |
|---|---|---|
| Leave both null | The approval gate cannot reach collection. Decision-only loss stays definable. | This is the current unsigned state. |
| Zero weight, budget still chosen | Decision loss is unmixed with cost. Feasibility still depends on the cap. At zero, every feasible team is optimal when decision losses do not differ by team. | Zero is a reference the implementation allows. It does not answer how expensive confidence should be. |
| Low, 0.2 / confidence mean | Confidence costs one uncertain decision. It can be worth that much, and not much more. | The 0.2 is the unapproved uncertainty weight, not a measured utility. |
| Moderate, 1.0 / confidence mean | Confidence costs one false acceptance. It is rarely worth fielding unless it removes almost a whole error. | The 1.0 is the unapproved error weight. |
| High, 0.2 / semantic mean | Confidence's penalty exceeds every loss on the proposed scale. The optimum ignores it even when the budget allows it. | This makes the resource term dominate. That may be what the lead wants, but it is not identified by the data. |
| Permissive cap at the four-mean sum | Every team is feasible. The cost-minimizing team is still the cheapest team. | The sum is a scale fact. The freeze says it does not authorize budget selection. |
| Restrictive cap at the cheapest pair | Floor 2 can field only rule and semantic. Floor 3 has no policy. | An infeasible hard question would confound aggregation with roster availability. |

What the grid does support is a choice rule, not a number. Pick the coefficient whose confidence gap is the smallest decision-loss improvement that should justify paying for confidence. Pick one shared budget at or above the participant floor the lead actually adopts, and do not give the three methods different caps. If the hard floor of 3 is in force, the restrictive cap in this grid is not a usable matched budget.

## Reproducibility

```
python evaluation/experiments/experiment3/resource_sensitivity.py
```

Outputs, all labeled SYNTHETIC / CONFIGURATION-SENSITIVITY ANALYSIS:

- `evaluation/experiments/experiment3/sensitivity/scenarios.json`
- `evaluation/experiments/experiment3/sensitivity/results.json`
- `evaluation/experiments/experiment3/sensitivity/reproducibility_manifest.json`

The manifest hashes those files, this document, the synthetic fixture, and the calibration file. Existing synthetic figures, `synthetic/results.json`, empirical outputs, and the approval package are not rewritten.
