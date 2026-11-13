# Experiment 3 results

There are no empirical Experiment 3 results. Development recordings are 0. Unresolved labels were not relabeled. Nothing was imputed. No empirical figure was written. The synthetic dependency heatmap stays under `synthetic/figures/` and is not a Development result.

The questions are unanswered on Development data:

1. Whether letting the game choose its aggregation improves validation performance is inconclusive.
2. Whether explicit dependency modeling improves robustness under correlated failures is unestablished. No paired failure recording exists.

## Synthetic fixture, not a finding

`evaluation/experiments/experiment3/synthetic/results.json` is a hand-built fixture. The sample is one fixture, not 372 groups. These cells are expected loss on that fixture.

| Configuration | Method | Clean loss | Clean coverage | Worst-case expected loss |
|---|---|---:|---:|---:|
| shared_unknown | full_minimax | 0.4 | 0.0 | 0.4 |
| shared_unknown | fixed_reputation_weighted | 0.4 | 0.0 | 0.4 |
| shared_unknown | fixed_dependency_group | 0.2 | 1.0 | 1.2 |
| controlled_synthetic_two_group | full_minimax | 0.2 | 1.0 | 0.4 |
| controlled_synthetic_two_group | fixed_reputation_weighted | 0.4 | 0.0 | 0.4 |
| controlled_synthetic_two_group | fixed_dependency_group | 0.2 | 1.0 | 0.4 |

On this fixture, `full_minimax` places frequency 1 on `reputation_weighted` under `shared_unknown`, so its clean loss matches fixed reputation. That frequency is not evidence that one aggregation is better. Selective risk is null where coverage is 0.

## Hypothetical dependency stress

`evaluation/experiments/experiment3/hypothetical/configurations.json` names the one-group model, an independent-verifier assumption, and a shared-text assumption. `empirical_loss` is null. `measured_dependence` is false. No hypothetical loss was filled in.
