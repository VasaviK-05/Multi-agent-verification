# Experiment 3 aggregation ablation

## Objective

Determine whether allowing the game to select both the verifier team and the aggregation method improves validation, compared with restricting aggregation to one method.

This document is only the aggregation comparison. Dependency-robustness numbers are in `experiment3_dependency_robustness.md`.

## Hypothesis

Under the preserved Development reports, budget, loss, and Beta(1, 1) reputation, the joint team-and-aggregation game has lower validation loss or higher decision coverage than either restricted game.

## Design

Three games use the same candidates, saved reports, seven historical attack columns, reputation snapshot, resource budget, minimum team size, coverage rules, loss, threshold, and objective weights:

1. Joint game (`full_minimax`): the solver may choose a team and either `reputation_weighted` or `dependency_group`.
2. Reputation-only game (`fixed_reputation_weighted`): team selection with aggregation fixed to `reputation_weighted`.
3. Dependency-only game (`fixed_dependency_group`): team selection with aggregation fixed to `dependency_group`.

The historical artifacts in `evaluation/experiments/experiment3/empirical/` are inputs. Ablation v1 writes only under `evaluation/experiments/experiment3/ablation_v1/outputs/`.

## Population and provenance

- 744 Development candidates in 372 question groups.
- Eligibility manifest: `evaluation/artifacts/person1/research_v1_exploratory_eligibility_approved_v1/`.
- Verifier inputs: `evaluation/datasets/research_v1_exploratory/research_v1_exploratory_v1/development_verifier_inputs.jsonl`.
- Saved reports: `evaluation/experiments/experiment3/empirical/verifier_reports.jsonl`.
- Report SHA-256 before and after this run: `877d0218dd498e8ca525e651f52f8aa1e337cd6f5123583fb277a2a28e01eca5`.
- Reports unchanged: `True`.
- Final Test labels and Final Test data were not opened.

## Settings

- Reputation: Beta(1, 1), zero approved observations. Log-odds weight at mean 0.5 is 0, and dependency reliability `max(0, 2 * reputation - 1)` is 0. Both aggregators therefore use an unweighted fallback.
- Budget: `14996.39091498102` ms.
- Resource coefficient: `1.3399597937725295e-05`.
- Minimum team size: 2.
- Decision threshold: 0.55. A score above 0.55 passes, below -0.55 fails, and the remainder is uncertain.
- Loss version `experiment3-selected-loss-v1`: correct 0, false acceptance `1.0`, false rejection `1.0`, uncertain `0.2`.
- Validation loss excludes the resource penalty. The penalty is included in the augmented loss used to select a strategy.
- Calibration id `cc7e7ca8882f602b9854bf21b80b8a7bf70f6c70d05ccd12787322a84a12477d`.

## Reproduction of the neutral comparison

Status: `reproduced`. Historical match: `True`.

- `fixed_dependency_group`: decision loss `0.2533026113671275`, coverage `0.23751920122887865`, rows `5208`, modal strategy `ad0b8ffb719c57171af3713fed9ef5ee56abfeb911bb36d093c9e29406ae23f0`, matches stored modal `True`, game value `0.29096372230211043`, matches stored game value `True`, matches stored probabilities `True`.
- `fixed_reputation_weighted`: decision loss `0.2533026113671275`, coverage `0.23751920122887865`, rows `5208`, modal strategy `7bebbe44c42c138b65816273a8807e0be825e5543903862c49970aa7f92813ac`, matches stored modal `True`, game value `0.29096372230211043`, matches stored game value `True`, matches stored probabilities `True`.
- `full_minimax`: decision loss `0.2533026113671275`, coverage `0.23751920122887865`, rows `5208`, modal strategy `7bebbe44c42c138b65816273a8807e0be825e5543903862c49970aa7f92813ac`, matches stored modal `True`, game value `0.29096372230211043`, matches stored game value `True`, matches stored probabilities `True`.

Decision disagreements between `reputation_weighted` and `dependency_group`, over every feasible team and every historical attack: `0` of `36456`.

full_minimax has two optimal evidence-plus-rule rows. The solver probability does not make one aggregation better.

The stored diagnosis records two optimal rows for the joint game, both evidence plus rule. A solver probability of 1 on one of those rows is a vertex of a tie. It is not evidence that reputation aggregation is better.

## Paired differences

Resamples are question groups. Candidates from the same `related_group_id` stay together. Seed `20261113`, `2000` resamples, percentile interval from `app/game/research/uncertainty.py` `_quantile`. Each group's contrast is the mean of its per-attack mean losses, then the restricted method minus the joint method. `exact_ties` counts groups whose mean difference is exactly zero. That count is 372 groups here. It is not the historical attack-level sample size of 2604.

- `fixed_reputation_weighted minus joint`: mean `0.0`, 95% interval `[0.0, 0.0]`, groups `372`, exact zero groups `372`.
- `fixed_dependency_group minus joint`: mean `0.0`, 95% interval `[0.0, 0.0]`, groups `372`, exact zero groups `372`.

Every paired difference is exactly zero, so every resampled mean is zero. The interval `[0.0, 0.0]` was calculated. It was not entered as a placeholder.

## Non-neutral reputation

Status: `not_estimable`. Ran: `False`.

No approved non-neutral reputation snapshot exists. Development outcomes are excluded as a reputation source, observations_count is 0, and the update rule is not approved. No substitute reputations were invented.

Approved flag in the reputation policy file: `False`. Observations: `0`. Update rule: `PENDING_APPROVAL`.

No substitute reputations were assigned. No non-neutral bars or intervals are drawn. This is a limitation of the available reputation data, recorded separately from the primary neutral result.

## Result

On the preserved neutral snapshot, allowing the game to choose the aggregation method does not change any decision, the validation loss, or the coverage. Reputation aggregation and dependency aggregation are exactly tied. The hypothesis is not supported.

## Figure

`evaluation/experiments/experiment3/ablation_v1/outputs/figures/aggregation_ablation_grouped_bars.svg`

The loss panel states the calculated paired interval. The coverage panel states the exact tie and does not draw a coverage interval, because no coverage bootstrap was calculated.

## Sources

- `evaluation/experiments/experiment3/empirical_executor.py`: `score`, `_matrix`, `_policies`.
- `app/game/research/comparison.py`: `restricted_matrix`.
- `evaluation/experiments/experiment3/ablation_v1/runner.py`: `reproduce_neutral`.
- `evaluation/experiments/experiment3/ablation_v1/failures.py`: `paired_group_difference`.

## Command

`python evaluation/experiments/experiment3/ablation_v1/runner.py`

## Test results

Command:

`python -m pytest tests/test_experiment3_ablation_v1.py tests/test_experiment3_visualizations.py tests/test_dependency_aggregation.py tests/test_experiment3_synthetic.py tests/test_experiment3_empirical_integration.py evaluation/tests/test_experiment3_dependency_heatmap.py --tb=line -q --continue-on-collection-errors`

Result: 102 passed, 1 error. Pytest exit code 1.

The error is collection of `tests/test_experiment3_synthetic.py`:

`ImportError: cannot import name 'CONTROLLED_SYNTHETIC_ASSUMPTION' from 'app.game.dependencies'`.

`app/game/dependencies.py` was not modified for ablation v1. The other five files collected and passed. That includes `tests/test_experiment3_ablation_v1.py`, which checks the registries, failure scope, unchanged reports, matched inputs, group bootstrap, missing cells, and the completed result file.

