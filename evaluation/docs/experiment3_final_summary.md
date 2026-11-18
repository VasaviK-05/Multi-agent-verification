# Experiment 3 final summary

Primary results are the neutral aggregation reproduction and the dependency matrices in `ablation_v1/outputs/results.json`. The non-neutral reputation check was not run. No synthetic fixture is reported here as a Development result. The one-example synthetic heatmap under `evaluation/experiments/experiment3/synthetic/` is a separate fixture and is not this result.

## Answers

1. Did allowing aggregation choice improve validation? No. Joint, reputation-only, and dependency-only games reproduce the stored modal strategies and game value `0.29096372230211043`. Mean decision loss is `0.2533026113671275` and coverage is `0.23751920122887865` for all three. Decision disagreements: `0` of `36456`. Paired loss differences are 0 with interval [0.0, 0.0] on 372 groups.
2. Did reputation aggregation outperform dependency aggregation? No. They are exactly tied under Beta(1, 1). A non-neutral comparison is not estimable: approved observations are 0, Development outcomes are excluded as a reputation source, and no reputations were invented.
3. Did the declared dependency model outperform the independent alternative? No. On matched attacks the worst-column decision loss is `0.2895161290322581` for both, in both failure scenarios. Paired differences are 0 with interval [0.0, 0.0].
4. Did the declared dependency model outperform the fully correlated alternative? No. The matched losses are the same, and the paired differences are 0 with interval [0.0, 0.0].
5. Were results different under independent and correlated failures? Worst-column decision loss and coverage were not different: every native and matched cell is loss `0.2895161290322581` and coverage `0.2513440860215054`. False acceptance and false rejection did differ for the native fully correlated column, which targets all four verifiers: false acceptance `1.0`, false rejection `0.0`. The other native cells have false acceptance 0.9903846153846154 and false rejection 0.012048192771084338. Decision loss is unchanged because both error types cost 1.
6. Supported conclusions: on these 744 Development reports, with Beta(1, 1) reputation and the forced-support operator, aggregation choice does not change validation, and the declared structural grouping does not reduce worst-column decision loss relative to independent or fully correlated grouping. The equality is exact on the paired group differences, not a claim from a solver probability.
7. Unproven: any gain once reputation leaves 0.5; any gain on Final Test; any claim that the structural groups are measured dependencies; any claim about attack operators other than `forced_support`; any claim that native correlated columns of different widths are the same attack.

## Loss matrix used by the heatmap

| Assumption | Independent failures | Correlated failures |
| --- | ---: | ---: |
| declared_structural | 0.2895161290322581 | 0.2895161290322581 |
| independent | 0.2895161290322581 | 0.2895161290322581 |
| fully_correlated | 0.2895161290322581 | 0.2895161290322581 |

## Figures

- `evaluation/experiments/experiment3/ablation_v1/outputs/figures/aggregation_ablation_grouped_bars.svg`
- `evaluation/experiments/experiment3/ablation_v1/outputs/figures/dependency_robustness_heatmap.svg`
- `evaluation/experiments/experiment3/ablation_v1/outputs/figures/dependency_coverage_heatmap.svg`
- `evaluation/experiments/experiment3/ablation_v1/outputs/figures/ablation_effect_differences.svg`

## Reproduce

`python evaluation/experiments/experiment3/ablation_v1/runner.py`

Seed `20261113`. Bootstrap resamples `2000`. The command reads the historical empirical files and writes `ablation_v1/outputs/` plus these three documents.

## Test results

Command:

`python -m pytest tests/test_experiment3_ablation_v1.py tests/test_experiment3_visualizations.py tests/test_dependency_aggregation.py tests/test_experiment3_synthetic.py tests/test_experiment3_empirical_integration.py evaluation/tests/test_experiment3_dependency_heatmap.py --tb=line -q --continue-on-collection-errors`

Result: 102 passed, 1 error. Pytest exit code 1.

The error is collection of `tests/test_experiment3_synthetic.py`:

`ImportError: cannot import name 'CONTROLLED_SYNTHETIC_ASSUMPTION' from 'app.game.dependencies'`.

`app/game/dependencies.py` was not modified for ablation v1. The other five files collected and passed. That includes `tests/test_experiment3_ablation_v1.py`, which checks the registries, failure scope, unchanged reports, matched inputs, group bootstrap, missing cells, and the completed result file.

