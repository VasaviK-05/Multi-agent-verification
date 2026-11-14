# Experiment 3 policy diagnosis

Evidence label: `EMPIRICAL` for every number taken from the stored Development reports. The controlled three-vote example later in this note is a synthetic illustration of the aggregation arithmetic. It is not an empirical finding. Coefficient variants other than the selected coefficient are counterfactuals on the stored reports. They are not new collections.

The diagnosis file is `evaluation/experiments/experiment3/empirical/diagnosis/policy_diagnosis.json`. Building it calls `score` on `verifier_reports.jsonl`. It does not call verifiers and it does not write `results.json`, `metrics.json`, `bootstrap_results.json`, or `verifier_reports.jsonl`.

A fresh solve with the current scoring code reproduced the stored modal strategy ids and the stored game value `0.29096372230211043`. No scoring defect was found. The completed collection was not rerun, and it already matches this code.

## What the three methods did

`full_minimax`, `fixed_reputation_weighted`, and `fixed_dependency_group` each returned a pure policy on evidence and rule. Across 5,208 candidate-attack cells, decision mismatches are 0 and loss mismatches are 0.

That establishes an observed identity on this Development collection: same team, same decisions, same decision losses, paired differences of 0, and a degenerate 95% group-bootstrap interval `[0, 0]`.

It does not establish that the methods are equivalent in general. A different prior, a different budget, or reports that put the two aggregation rules on opposite sides of the 0.55 threshold can separate them. The controlled example below is one such case.

## Feasible set

`enumerate_strategies` uses the frozen means, a participant floor of 2, uniform capabilities, and budget `14996.39091498102` ms. Equality with the budget is feasible. A larger cost is not.

Seven teams are feasible, and each is crossed with both aggregations, giving 14 strategies:

| Team | Frozen cost (ms) | Selected penalty | Worst augmented loss | Clean coverage (744) |
| --- | ---: | ---: | ---: | ---: |
| evidence + rule | 108.03258997621015 | 0.0014475932698523478 | 0.29096372230211043 | 0.2271505376344086 |
| rule + semantic | 70.56993665755726 | 0.000945608777702009 | 0.2979886195303902 | 0.13978494623655913 |
| evidence + semantic | 178.40837999052988 | 0.002390600560594015 | 0.33894974034554026 | 0.2110215053763441 |
| evidence + rule + semantic | 178.50545331214863 | 0.0023919013040741856 | 0.3397574927019236 | 0.21370967741935484 |
| confidence + rule | 14925.918051645082 | 0.2000013007434802 | 0.4905926985929425 | 0.25268817204301075 |
| confidence + semantic | 14996.293841659402 | 0.20094430803422186 | 0.5452991467438992 | 0.28897849462365593 |
| confidence + rule + semantic | 14996.39091498102 | 0.20094560877770204 | 0.5461068991002827 | 0.2916666666666667 |

The worst augmented loss is the maximum, over the seven attack columns, of mean decision loss plus `coefficient × frozen team cost`. Both aggregations produce the same loss vector on every one of these teams, so each row stands for both aggregations.

Rejected teams are the four singletons, because the floor is 2, and every team that contains both confidence and evidence, because the frozen sum exceeds the budget. The full roster is in that rejected set.

Uniform capabilities mean expected coverage removes no team. The only binding constraints are the floor and the frozen budget.

## Why the team is evidence + rule

Inside each aggregation, evidence + rule is the unique minimax optimum at the selected coefficient. The next team, rule + semantic, has worst augmented loss 0.2979886195303902. The gap is 0.00702489722827977. This is not a tie across teams.

The two aggregations of evidence + rule have the same worst-case value, `0.29096372230211043`. `full_minimax` therefore has two optimal strategies and one optimal verifier team. `solve_minimax` returned probability 1 on the reputation-weighted strategy id. The recorded tie-break, if a returned distribution put mass on more than one strategy, is the maximum of `(probability, strategy_id)`. Here the solver's returned distribution is already pure. The equal optimum under dependency-group aggregation is visible in the worst-case comparison, not as a second positive probability.

Each fixed method searches only its own aggregation. Each of those restricted matrices has one optimal strategy. The fixed methods are not forced by the code to copy the minimax team. They select evidence + rule because it is the unique optimum inside each aggregation.

The worst column for that team is forced support of `[confidence, evidence, semantic]`. Its mean decision loss is `0.2895161290322581`. Adding the penalty `0.0014475932698523478` recovers the game value.

## Why the aggregations did not change decisions

The planning snapshot is `Beta(1, 1)`. Every reputation mean is 0.5.

- `log_odds_weight(0.5)` is 0. Reputation-weighted scoring then uses the equal-weight average of informative votes.
- Dependency reliability is `max(0, 2 × 0.5 − 1) = 0`. Dependency scoring then averages informative votes inside a component and averages those components without reliability weights.

When a team has at most one informative verifier in each component, the two averages are the same function. Evidence + rule is that case: evidence sits in the merged model component and rule sits alone.

When one component contains two informative verifiers, the averages differ. The controlled example uses semantic SUPPORT at score 1, evidence SUPPORT at score 1, and rule REJECT at score 0.2, with the same cold-start snapshot and threshold 0.55. Reputation-weighted status is `passed` (score 0.6). Dependency-group status is `uncertain` (score 0.4). That example is synthetic. It shows the rules can separate. It is not a Development outcome.

On the stored reports, the two aggregations disagree on 0 of 5,208 cells for every feasible team, including teams with more than one verifier in the model component. The attack-wise mean decision losses also match across aggregations. The identity is a property of these reports under zero weights. It is not an assignment that forces the fixed methods onto the minimax strategy object.

## Resource coefficient

The selected coefficient is `1.3399597937725295e-05` loss per millisecond. On the stored decision losses:

| Coefficient | Value | Optimal team |
| --- | ---: | --- |
| no penalty | 0 | evidence + rule |
| selected low | `1.3399597937725295e-05` | evidence + rule |
| moderate | `6.699798968862647e-05` | evidence + rule |
| high | `0.0028379718168483666` | rule + semantic |

The high row is `0.2 / frozen semantic mean`. It is the sensitivity grid's high coefficient applied to these empirical cell losses. It is a counterfactual, marked `COUNTERFACTUAL_ON_STORED_EMPIRICAL_REPORTS`. It was not collected as a separate experiment, and the synthetic fixture sensitivity remains a different record.

At the selected coefficient, the penalty does not choose the winner. Evidence + rule also wins with a zero penalty, where its worst decision loss is 0.2895161290322581. The penalty does make confidence-bearing teams unattractive: confidence + rule carries penalty 0.2000013007434802 because the frozen confidence mean is 14925.820978323463 ms. Subtracting that penalty from its worst augmented loss leaves 0.2905913978494623, still above evidence + rule's zero-penalty worst loss of 0.2895161290322581.

Confidence was excluded from the selected team for that loss comparison. The budget, separately, excludes confidence + evidence and the full roster under the frozen means. Some confidence teams remain feasible: confidence + rule, confidence + semantic, and confidence + rule + semantic. They are feasible and suboptimal.

## Recorded time is not the feasibility cost

Mean recorded milliseconds on the 744 calls, against the frozen means:

| Verifier | Recorded ms | Frozen ms | Recorded minus frozen |
| --- | ---: | ---: | ---: |
| confidence | 13247.462 | 14925.821 | -1678.359 |
| evidence | 209.858 | 107.936 | 101.922 |
| rule | 0.042 | 0.097 | -0.055 |
| semantic | 29.967 | 70.473 | -40.506 |

The sum of the recorded means is about 13487 ms, which is under the budget. The sum of the frozen means is about 15104 ms, which is over the budget. A budget applied to this run's wall times would have admitted confidence + evidence and the full roster. The protocol uses the frozen means for feasibility and for the penalty. Those recorded times were not substituted, and the collection was not rerun.

## Classification

- Unique team at the selected coefficient, inside each aggregation and in the joint matrix.
- Tied aggregations of that same team, with identical decisions on these reports.
- Cold-start arithmetic explains why the aggregations can collapse to unweighted averages.
- The report set explains why they in fact made the same decision on every feasible team.
- The frozen budget and the confidence penalty constrain the strategy set. They do not create the evidence + rule optimum by themselves, because that team also wins at penalty zero.
- No implementation defect was found. No corrected experiment version was run.

## Implication for the game

On this collection, minimax separates verifier teams and does not separate aggregation rules. A claim that dependency-group aggregation is more or less robust than reputation-weighted aggregation is not supported here. A claim that every feasible team is equivalent is also not supported: six other teams have higher worst-case loss.
