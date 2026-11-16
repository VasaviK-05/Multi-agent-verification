# Experiment 3 results

Evidence label: **EMPIRICAL**. Development evaluation only. These numbers are one-method totals. `metrics.json` stores the same slices three times, once per aggregation method, and its top-level `correctness_counts` add those copies together. The counts below are the single-method counts.

## Objective

Experiment 3 asks whether the aggregation rule changes the selected verifier team or the Development decisions when the reports, budget, loss, threshold, and attacks are held fixed.

- `full_minimax` may choose both the team and the aggregation.
- `fixed_reputation_weighted` may choose the team and must use reputation-weighted aggregation.
- `fixed_dependency_group` may choose the team and must aggregate by the declared dependency components.

This is an aggregation comparison. The comparison against greedy, uniform, and a separately declared fixed team is Experiment 1.

## Population and conditions

The population is the approved Development eligibility manifest: 372 groups (GSM8K 187, HotpotQA 185) and 744 candidates, two per group. One candidate in each pair is `VERIFIED_CORRECT`. The other is `SYNTHETIC_INCORRECT`. Final Test labels were not opened. `final_test_accessed` is false.

Decision loss is 1.0 for false acceptance, 1.0 for false rejection, and 0.2 for uncertainty. The decision threshold is 0.55. Reported `validation_loss` is decision loss only. The game objective adds `1.3399597937725295e-05` loss per millisecond times the frozen team cost. The budget is `14996.39091498102` ms, from calibration `cc7e7ca8882f602b9854bf21b80b8a7bf70f6c70d05ccd12787322a84a12477d`. That coefficient and budget are a selected configuration. They were not fit to these outcomes.

Reputation is a `Beta(1, 1)` cold start: mean 0.5, no decay, and zero approved historical observations. Dependency groups are the structural configuration `structural_shared_resource_v1`. They were not independently measured.

The attack columns are report transformations of the stored verifier calls. Suppression was unavailable and was not collected. The structural dependency has two failure components, `[confidence, evidence, semantic]` and `[rule]`, so each non-clean attack is one column per component:

| Column | Candidates |
| --- | ---: |
| clean | 744 |
| confidence inflation, model component | 744 |
| confidence inflation, rule | 744 |
| forced rejection, model component | 744 |
| forced rejection, rule | 744 |
| forced support, model component | 744 |
| forced support, rule | 744 |

The completed grid is 744 candidates × 7 columns × 3 methods = 15,624 cells. Execution failures are 0. A four-column grid would have been 8,928 cells. That is not the grid that ran.

Policies were fit and scored on the same 744 rows. The paired bootstrap resamples `related_group_id`, with 2,000 resamples, a 95% interval, and seed `20261113`.

## Pooled result, one method

Denominator 5,208 = 744 × 7. Each candidate is counted once per attack. These are not the clean-condition rates. The other two methods match every count.

| Quantity | Value | Count |
| --- | ---: | --- |
| Mean decision loss | 0.2533026113671275 | 5208 rows |
| Correct acceptance | 126 | 126 / 5208 |
| Correct rejection | 586 | 586 / 5208 |
| False acceptance | 110 | 110 / 5208 |
| False rejection | 415 | 415 / 5208 |
| Uncertain | 3971 | 3971 / 5208 |
| Coverage | 0.23751920122887865 | 1237 / 5208 |
| Uncertainty | 0.7624807987711214 | 3971 / 5208 |
| Selective risk | 0.4244139046079224 | 525 / 1237 classified |
| False-acceptance rate | 0.15804597701149425 | 110 / 696 |
| False-rejection rate | 0.767097966728281 | 415 / 541 |
| Execution failures | 0 | 0 / 5208 |

Clean only, 744 candidates: decision loss `0.24327956989247312`, coverage 169/744, uncertainty 575/744, selective risk 66/169, false acceptance 1/96, false rejection 65/73.

GSM8K contributes 2,618 pooled rows in `results.json`. Their mean decision loss is `0.21061879297173414`. Coverage 101/2618. Uncertainty 2517/2618. HotpotQA contributes 2,590 pooled rows. Their mean decision loss is `0.29644787644787646`. Coverage 1136/2590. Uncertainty 1454/2590. Reweighting the stored `metrics.json` slice means gives the same HotpotQA value and gives GSM8K `0.2106187929717342`, one floating-point step from the row mean, because each slice mean is a stored float. The row mean is the value used here.

## Attack columns, one method

Team cost is 108.03258997621015 ms on every row. The resource penalty on that team is 0.0014475932698523478. The game value, the worst column of decision loss plus that penalty, is 0.29096372230211043. That is a different number from the pooled mean 0.2533026113671275.

| Attack | Decision loss | CA | CR | FA | FR | Uncertain | Coverage | Selective risk | FAR | FRR |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| clean | 0.24327956989247312 | 8 | 95 | 1 | 65 | 575 | 169/744 | 66/169 | 1/96 | 65/73 |
| confidence inflation, model component | 0.24919354838709679 | 11 | 102 | 2 | 72 | 557 | 187/744 | 74/187 | 2/104 | 72/83 |
| confidence inflation, rule | 0.24327956989247312 | 8 | 95 | 1 | 65 | 575 | 169/744 | 66/169 | 1/96 | 65/73 |
| forced rejection, model component | 0.26129032258064516 | 0 | 104 | 0 | 83 | 557 | 187/744 | 83/187 | 0/104 | 83/83 |
| forced rejection, rule | 0.24327956989247312 | 8 | 95 | 1 | 65 | 575 | 169/744 | 66/169 | 1/96 | 65/73 |
| forced support, model component | 0.2895161290322581 | 82 | 1 | 103 | 1 | 557 | 187/744 | 104/187 | 103/104 | 1/83 |
| forced support, rule | 0.24327956989247312 | 9 | 94 | 2 | 64 | 575 | 169/744 | 66/169 | 2/96 | 64/73 |

Forced support of the model component is the worst column. On HotpotQA that column classifies 168 of 370 candidates and accepts every one of them: 74 correct acceptances and 94 false acceptances. GSM8K clean classifies 11 of 374 candidates. Rates on those small GSM8K classified sets are unstable.

## Why the three methods match

All three methods selected evidence + rule and made the same decision on every candidate-attack cell. The paired difference versus `full_minimax` is 0.0 for both restricted methods, on 372 groups and 2,604 group-attack pairs. Both 95% intervals are [0.0, 0.0], with 2,604 of 2,604 differences equal to zero.

`log_odds_weight(0.5)` is 0, and dependency reliability at reputation 0.5 is 0. Both aggregations therefore fall back to unweighted averages. On these stored reports the two averages never landed on opposite sides of 0.55: 0 decision disagreements in 5,208 cells per team. A synthetic control can make the two rules disagree. That control was not observed in the empirical reports.

## Why evidence + rule was selected

Fourteen strategies are feasible: 7 teams × 2 aggregations. Singletons fail the participant floor of 2. Teams that contain both confidence and evidence, including the full roster, fail the frozen-cost budget. Evidence + rule has worst augmented loss 0.29096372230211043. The next team, rule + semantic, has worst augmented loss 0.2979886195303902. The selected team is unique. `full_minimax` has two optimal strategy rows, one per aggregation, and the solver returned probability 1 on the reputation-weighted row. Each restricted method has one optimum, and each selects the same verifiers.

The selected team usually has only the evidence vote. Rule is UNSURE on 742 of 744 clean reports. GSM8K semantic is UNSURE on all 374 clean reports because those inputs have an empty evidence context. Confidence is UNSURE on 558 of 744 clean reports and was not selected.

## What this establishes

On this Development configuration, changing the aggregation restriction does not change the team or any recorded decision. The game still separates teams: evidence + rule is the unique minimax team, and six other feasible teams have higher worst-case loss. Uncertainty is the dominant outcome, especially on GSM8K. Forced support of the model component is the worst attack column.

The [0.0, 0.0] interval describes a paired sample that contains only zeros. It does not show that the three methods are equivalent under another prior, budget, or report distribution. The run does not measure dependency, does not use a held-out split, and does not score Final Test.

Figures: `figures/experiment3_attack_loss_by_method.svg`, `figures/experiment3_attack_loss_by_benchmark.svg`, `figures/experiment3_coverage_uncertainty.svg`, `figures/experiment3_false_acceptance_rejection.svg`, `figures/experiment3_verifier_decisions.svg`, `figures/experiment3_team_selection.svg`.
