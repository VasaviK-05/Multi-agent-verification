# Experiment 1 offline replay

Evidence label: EMPIRICAL. This comparison rescores the frozen Experiment 3 Development verifier reports. It does not call verifiers, and it does not write into `evaluation/experiments/experiment3/empirical/`. Final Test files were not opened.

## Protocol

The population, loss, threshold, resource coefficient, budget, dependency configuration, and attack columns are the Experiment 3 configuration: 744 Development candidates in 372 groups, false acceptance 1.0, false rejection 1.0, uncertainty 0.2, threshold 0.55, coefficient `1.3399597937725295e-05` loss per millisecond, budget `14996.39091498102` ms, and the seven structural attack columns. Suppression stays unavailable.

The four methods were declared before this replay was scored:

- `full_minimax`: the joint solver's modal strategy on the same feasible matrix.
- `deterministic_minimax`: the preexisting fixed rule in `app/game/research/comparison.py`. It selects the feasible strategy with the smallest worst-column augmented loss and breaks ties by the smaller strategy id. The team was not chosen because evidence + rule won Experiment 3.
- `uniform`: equal weight on all 14 feasible strategies. Reported losses and error counts are expectations under that mixture, not one decision.
- `coverage_aware_greedy`: the coverage selector in `VerifierSelector`, using the keyword heuristic and `BUILTIN_CAPABILITIES`, with reputation-weighted aggregation. The aggregation name comes from `app/game/offline/pilot_proposal.py`. `experiment1_proposal.json` does not name it. A selector team that is outside the matched budget and participant floor is recorded as infeasible and is not replaced.

Both game policies are fit on the Development matrix they are scored on. That is the same in-sample limitation as Experiment 3. The bootstrap uses 2000 group-level paired resamples, seed `20261113`, and a 95% interval. The difference is method loss minus full-minimax loss.

## Policies on this matrix

Full minimax and the deterministic rule returned the same strategy, `7bebbe44c42c138b65816273a8807e0be825e5543903862c49970aa7f92813ac`: evidence + rule, reputation-weighted aggregation, game value `0.29096372230211043`. Their decision losses therefore match on all 5,208 candidate-attack rows. This is a property of this matrix. It does not show that the two rules are the same rule.

Uniform places weight `1/14` on every feasible strategy, including the confidence teams.

The selector's teams, from the question text and the heuristic, were:

| Team | Candidates | Under the Experiment 3 budget |
| --- | ---: | --- |
| rule + semantic | 370 | feasible |
| evidence + rule | 140 | feasible |
| confidence + evidence + rule | 234 | infeasible |

The 234 infeasible candidates are 117 complete groups. Both candidates in a group share a question, so they receive the same team. Their losses are not imputed. The greedy summary and its paired interval use the other 510 candidates (255 groups, 3,570 rows).

## Decision loss

Pooled mean decision loss, seven attacks:

| Method | Rows | Mean decision loss | Mean resource penalty | Coverage | Selective risk |
| --- | ---: | ---: | ---: | ---: | ---: |
| full minimax | 5208 | 0.2533026113671275 | 0.0014475932698523478 | 0.23751920122887865 | 0.4244139046079224 |
| deterministic minimax | 5208 | 0.2533026113671275 | 0.0014475932698523478 | 0.23751920122887865 | 0.4244139046079224 |
| uniform | 5208 | 0.26770353302611366 | 0.08700956020966094 | 0.28428790871187276 | 0.4381512929370893 |
| greedy, feasible subset | 3570 | 0.29949579831932777 | 0.0010834084422138668 | 0.3204481792717087 | 0.5104895104895105 |

The greedy row is not a 744-candidate mean. Its resource penalty is lower because the infeasible confidence team is absent. That is an exclusion, not a resource improvement.

Paired difference against full minimax, seed `20261113`, 2000 resamples:

| Method | Groups | Mean difference | 95% interval | Exact-zero pairs |
| --- | ---: | ---: | --- | ---: |
| deterministic minimax | 372 | 0.0 | [0.0, 0.0] | 2604 of 2604 |
| uniform | 372 | 0.014400921658986153 | [0.0036756638139126413, 0.02456756089532584] | 47 of 2604 |
| greedy, feasible groups | 255 | 0.025602240896358545 | [0.004593837535014006, 0.045829131652661045] | 967 of 1785 |

On this Development replay, the uniform and feasible-greedy intervals lie above zero. That describes this paired sample. It does not establish a result on a new population or on Final Test, and the greedy interval does not include the 117 groups the budget excluded.

## Errors

Full minimax and the deterministic rule match the Experiment 3 one-method counts: 126 correct acceptances, 586 correct rejections, 110 false acceptances, 415 false rejections, and 3971 uncertain outcomes. False-acceptance rate `110/696`. False-rejection rate `415/541`. Clean loss is `0.24327956989247312`. The model-component forced-support column remains the high false-acceptance column: 103 of 104, loss `0.2895161290322581`.

Uniform expected pooled rates are false acceptance `0.4166825366596826` and false rejection `0.4601994914922746`. Its clean loss is `0.24612135176651304`. The higher resource penalty is the average penalty of the 14 teams.

On the 510 feasible greedy candidates, clean loss is `0.27098039215686276`, with 55 false acceptances out of 59 and 3 false rejections out of 50. The model-component forced-support column on that subset has false-acceptance rate 1.0 and loss `0.3466666666666667`. These rates describe the selector's feasible questions, which are mostly the rule + semantic team.

## What this comparison establishes

Under the matched budget, the joint solver and the predeclared worst-column rule select the same evidence + rule strategy, so they have the same Development loss. Uniform feasible selection has higher expected decision loss and a much larger expected resource penalty. The coverage selector often requests confidence + evidence + rule, and that team is infeasible at the frozen budget. On the questions where its team is feasible, its paired decision loss is higher than full minimax.

The comparison does not show that joint selection is better on Final Test, under a different budget, or after reputation leaves the cold start. It does not repair the Experiment 3 limitations: Development-only evaluation, synthetic incorrect candidates, cold-start reputation, and assumed dependencies.
