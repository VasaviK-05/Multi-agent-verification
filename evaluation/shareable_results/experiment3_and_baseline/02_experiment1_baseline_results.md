# Experiment 1 baseline results

Evidence label: **EMPIRICAL**. This is an offline replay of the frozen Experiment 3 verifier reports. Verifiers were not called again. Final Test files were not opened. The replay writes under `evaluation/experiments/experiment1/development/` and does not modify the Experiment 3 empirical files.

## Objective

Experiment 1 compares strategic verifier selection with simpler selection rules on the same Development population, loss, threshold, budget, coefficient, and seven attack columns.

| Method | Predeclared rule |
| --- | --- |
| Full minimax | Joint solver's modal strategy on the feasible matrix |
| Fixed team | Smallest worst-column augmented loss, then the smaller strategy id |
| Uniform | Equal weight on all 14 feasible strategies |
| Greedy | Coverage selector on the keyword heuristic, then reputation-weighted aggregation |

The fixed-team rule is the preexisting `deterministic_minimax` rule. The team was not named after seeing that evidence + rule won Experiment 3. Greedy aggregation is `reputation_weighted`, the value named in the pilot proposal. The Experiment 1 proposal file does not name an aggregation. A selector team outside the Experiment 3 budget is left infeasible. It is not replaced by another team.

Uniform losses and error counts are expectations under the 1/14 mixture. They are not one observed decision. Both game policies are fit on the Development matrix they are scored on.

## Shared recordings

Source: `evaluation/experiments/experiment3/empirical/verifier_reports.jsonl`, 744 candidates and 372 groups. The same seven attack columns are scored. Suppression remains unavailable. Seed `20261113`, 2,000 group-level paired resamples, 95% interval. The difference is method loss minus full-minimax loss.

## Selected policies

Full minimax and the fixed-team rule returned the same strategy, `7bebbe44c42c138b65816273a8807e0be825e5543903862c49970aa7f92813ac`: evidence + rule, reputation-weighted aggregation, game value `0.29096372230211043`. On this matrix the worst-column rule and the solver's tie-break land on the same strategy id. Their decisions therefore match on all 5,208 rows. That identity is a property of this matrix.

Uniform uses all 14 feasible strategies, including the confidence teams.

The coverage selector returned:

| Team | Candidates | Budget |
| --- | ---: | --- |
| rule + semantic | 370 | feasible |
| evidence + rule | 140 | feasible |
| confidence + evidence + rule | 234 | infeasible |

The 234 infeasible candidates are 117 complete groups. Both candidates in a group share a question, so they receive the same team. Their losses are not imputed. Greedy summaries and the greedy interval use the other 510 candidates, 255 groups, and 3,570 complete rows. Infeasible greedy rows are 1,638.

## Mean decision loss

| Method | Rows used | Mean decision loss | Mean resource penalty | Coverage | Selective risk |
| --- | ---: | ---: | ---: | ---: | ---: |
| Full minimax | 5208 | 0.2533026113671275 | 0.0014475932698523478 | 0.23751920122887865 | 0.4244139046079224 |
| Fixed team | 5208 | 0.2533026113671275 | 0.0014475932698523478 | 0.23751920122887865 | 0.4244139046079224 |
| Uniform | 5208 | 0.26770353302611366 | 0.08700956020966094 | 0.28428790871187276 | 0.4381512929370893 |
| Greedy, feasible subset | 3570 | 0.29949579831932777 | 0.0010834084422138668 | 0.3204481792717087 | 0.5104895104895105 |

The greedy mean is not a 744-candidate mean. Its resource penalty is lower because the infeasible confidence team is absent. That exclusion is not a resource improvement.

Full minimax and the fixed team, pooled over seven attacks: false acceptance 110/696 and false rejection 415/541. Uniform expected false-acceptance rate `0.4166825366596826`. Uniform expected false-rejection rate `0.4601994914922746`. Those uniform rates use fractional expected counts, including expected false acceptance `312.5714285714289` of expected denominator `750.1428571428603`. On the 3,570 feasible greedy rows, false acceptance is 418/602 and false rejection is 166/542.

## Paired intervals

| Contrast | Groups | Pairs | Mean difference | 95% interval | Exact zeros |
| --- | ---: | ---: | ---: | --- | ---: |
| Fixed team minus full minimax | 372 | 2604 | 0.0 | [0.0, 0.0] | 2604 |
| Uniform minus full minimax | 372 | 2604 | 0.014400921658986153 | [0.0036756638139126413, 0.02456756089532584] | 47 |
| Greedy minus full minimax | 255 | 1785 | 0.025602240896358545 | [0.004593837535014006, 0.045829131652661045] | 967 |

The uniform and feasible-greedy intervals lie above zero on this Development replay. The greedy interval does not include the 117 excluded groups. Neither interval is a Final Test result or a result under another budget.

## Figure

`figures/experiment1_baseline_decision_loss.svg` is the copied replay figure. It draws mean decision loss by attack. The full-minimax, uniform, and fixed-team series use 744 candidates per attack. The greedy series uses 510 candidates per attack. The figure file itself does not print that denominator. Read the greedy bars with the 510-candidate restriction above.

`figures/paired_differences_versus_full_minimax.svg` plots the paired differences and intervals from the two bootstrap files. That figure keeps the 255-group greedy contrast separate from the 372-group contrasts.
