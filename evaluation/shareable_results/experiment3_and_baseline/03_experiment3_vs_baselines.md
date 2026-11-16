# Experiment 3 and the Experiment 1 baselines

Experiment 3 and Experiment 1 answer different questions on the same Development recordings. Their results stay in separate rows below. There is no single score that mixes the 15,624-cell aggregation grid with the greedy subset.

## Comparison

| | Experiment 3 | Experiment 1 |
| --- | --- | --- |
| Research question | Does the aggregation restriction change the team or the decisions? | Does strategic team selection differ from a fixed worst-column rule, a uniform mixture, and coverage-greedy selection? |
| Methods | Full minimax, fixed reputation-weighted, fixed dependency-group | Full minimax, fixed team (`deterministic_minimax`), uniform, coverage-greedy |
| Population | 744 candidates, 372 groups, 7 attack columns, 15,624 cells | Same recordings and attacks. Full minimax, fixed team, and uniform use 5,208 rows. Greedy uses 3,570 rows from 255 groups. |
| Primary metric | Decision loss, plus the worst-column game value used to select the team | Paired difference in decision loss versus full minimax |
| Results | All three methods select evidence + rule and match on every cell. Pooled mean decision loss 0.2533026113671275. | Fixed team matches full minimax exactly. Uniform mean decision loss 0.26770353302611366 on 5,208 rows. Feasible-greedy mean 0.29949579831932777 on 3,570 rows. |
| Statistical evidence | Both aggregation contrasts: mean difference 0.0, interval [0.0, 0.0], 372 groups, 2,604 pairs, seed 20261113 | Fixed team: 0.0, [0.0, 0.0], 372 groups. Uniform: 0.014400921658986153, [0.0036756638139126413, 0.02456756089532584], 372 groups. Greedy: 0.025602240896358545, [0.004593837535014006, 0.045829131652661045], 255 groups. |
| Interpretation | With cold-start weights, these reports do not separate the two aggregations. The game does separate teams. | On this matrix the declared fixed rule selects the same strategy as the joint solver. Uniform and feasible greedy have higher paired decision loss. |
| Limitations | Development-only, in-sample policy fit, synthetic incorrect candidates, cold-start reputation, assumed dependencies, no Final Test | Same limitations, plus greedy's 117 excluded groups and uniform's mixture expectations |

## Four contrasts

**Minimax versus uniform.** Both sides use all 372 groups and all 5,208 candidate-attack rows. Uniform's expected decision loss is higher by 0.014400921658986153. The paired interval is above zero. Its mean resource penalty, 0.08700956020966094, is a separate quantity: the mixture includes confidence teams whose frozen penalty is about 0.200. The decision-loss difference does not include that penalty.

**Minimax versus greedy, feasible groups only.** The comparison uses 255 groups and 1,785 group-attack pairs. The mean paired difference is 0.025602240896358545, and the interval is above zero. The other 117 groups requested confidence + evidence + rule, which the frozen budget rejects. Those groups have no greedy loss. The 0.29949579831932777 mean is the mean on 3,570 rows. It is not a mean on the same 5,208 rows as minimax.

**Minimax versus the fixed team.** The worst-column rule returned strategy `7bebbe44c42c138b65816273a8807e0be825e5543903862c49970aa7f92813ac`, the same id as full minimax: evidence + rule, reputation-weighted. The paired difference is 0.0 on 2,604 of 2,604 pairs. The rules can diverge on another matrix. They do not diverge here.

**Experiment 3's identical aggregation results.** Full minimax, reputation-weighted, and dependency-group selected evidence + rule. Decision disagreements are zero. Both paired intervals are [0.0, 0.0] because every difference is zero. Cold-start reputation gives both aggregations zero weight, so both fall back to an unweighted average, and these reports never separated those averages.

## Why Experiment 1 does not establish aggregation superiority

Experiment 1's full minimax and fixed team use the same reputation-weighted evidence + rule strategy. Their match shows that two selection rules agreed. It does not compare reputation-weighted aggregation with dependency-group aggregation. That comparison is Experiment 3, and on these reports the two aggregations produced the same decisions. Uniform mixes all 14 strategies, so its higher loss mixes team choice with both aggregations. Greedy is locked to reputation-weighted aggregation and, for 234 candidates, has no score. An aggregation advantage is not identified by any of those three contrasts.
