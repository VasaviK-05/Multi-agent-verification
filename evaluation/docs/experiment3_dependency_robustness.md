# Experiment 3 dependency robustness

## Objective

Test whether the declared structural dependency model gives lower validation loss than an independent-failure model and a fully correlated model, under separate individual-failure and correlated-failure scenarios.

This comparison does not use the historical seven attack columns. Those columns remain the aggregation reproduction.

## Hypotheses

1. The declared grouping has lower worst-column decision loss than independent grouping when both are scored on the same failure columns.
2. The declared grouping has lower worst-column decision loss than fully correlated grouping on those same columns.
3. Independent failures and correlated failures produce different selected-team validation loss.

## What the registries are

The declared registry is a manual structural assumption. `evaluation/config/experiments/experiment3_dependency_configuration.json` records that empirical dependence evidence is unavailable. These groups are not learned correlations.

Resolved groups in this run:

- `declared_structural`: `[['confidence', 'evidence', 'semantic'], ['rule']]`
- `fully_correlated`: `[['confidence', 'evidence', 'rule', 'semantic']]`
- `independent`: `[['confidence'], ['evidence'], ['rule'], ['semantic']]`

- Declared version `structural_shared_resource_v1`, from the four configured edges: rule alone, semantic with evidence, evidence with confidence, and confidence alone. Union-find merges them to `{confidence, evidence, semantic}` and `{rule}`.
- Independent version `independent_verifier_failures_v1`: one group per verifier.
- Fully correlated version `fully_correlated_verifiers_v1`: all four verifiers share one unresolved component.

The alternative registries change `DependencyRegistry.groups` and the correlated attack membership. They are not renamed copies of the declared registry.

## Failure generation

Operator: `forced_support`. Abstention policy: `preserve_abstentions`.

`forced_support` sets a directional targeted report to decision SUPPORT, passed true, and score 1. An abstention, including UNSURE, stays an abstention. A verifier outside the targeted members is not transformed. The saved JSONL is not written. SHA-256 after the run equals the hash above in the aggregation document: `877d0218dd498e8ca525e651f52f8aa1e337cd6f5123583fb277a2a28e01eca5`.

Independent columns: one forced-support attack per verifier, identical for every assumption. Target count is 1.

Native correlated columns: one forced-support attack per group of that assumption. Declared correlated columns target 3 and 1 verifiers. Independent correlated columns target 1. The fully correlated column targets 4. Those native correlated columns are not severity-matched across rows. The loss heatmap uses this native matrix and must be read with that difference.

Matched columns: every assumption is scored on the independent singletons and on the declared groups `{confidence, evidence, semantic}` and `{rule}`. A difference across matched rows would be an aggregation difference. There is no such difference in this run.

`actually_corrupted` sums, over candidates, the targeted reports whose signed mass or decision changed. `preserved_abstentions` sums targeted reports left unchanged because they abstained. Neither number is a count of candidates.

## Settings held fixed

Reputation remains Beta(1, 1). Budget `14996.39091498102` ms. Loss `experiment3-selected-loss-v1` with weights 1.0 / 1.0 / 0.2. Threshold 0.55. Minimum team size 2. The reported matrix cell is the `dependency_group` strategy with the lowest worst-column augmented loss. On the matched attacks, the joint game and the reputation-only game are also scored and stored. They select evidence plus rule and the same worst-column decision loss. The joint game has two tied optimal rows (`full_minimax_tie_count` 2). The dependency-group selection has tie count 1.

## Measured matrix

Every required cell has status `available`. No cell was filled with zero in place of a missing run.

The selected dependency-group team in every cell is evidence plus rule. Frozen team cost is 108.03258997621015 ms. Resource penalty is 0.0014475932698523478. Worst-column decision loss is 0.2895161290322581. Coverage is 0.2513440860215054. Uncertainty is 0.7486559139784946. Selective risk is 0.5561497326203209.

Those four rates match 187 classified decisions, 557 uncertain decisions, and 104 errors among the 744 candidates: 104 errors at loss 1 and 557 uncertain decisions at loss 0.2 give total loss 215.4, and 215.4 / 744 = 0.2895161290322581.

False acceptance and false rejection are not identical in every native cell. In five of the six native cells the rates are 0.9903846153846154 and 0.012048192771084338, which match 103 false accepts among 104 classified negatives and 1 false reject among 83 classified positives. The native fully correlated column, which targets all four verifiers, has false acceptance 1.0 and false rejection 0.0. That is 104 false accepts among 104 classified negatives and 0 false rejects among 83 classified positives. The error count, coverage, and decision loss stay the same because a false accept and a false reject both cost 1. The matched matrix, where targets do not change with the assumption, has the 103-and-1 split in every cell.

Aggregation disagreements on the selected evidence-plus-rule team are 0 in every matched cell.

| Assumption | Scenario | Matrix | Loss | Coverage | False acceptance | False rejection | Uncertainty | Selective risk |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| declared_structural | independent_failures | native | 0.2895161290322581 | 0.2513440860215054 | 0.9903846153846154 | 0.012048192771084338 | 0.7486559139784946 | 0.5561497326203209 |
| declared_structural | independent_failures | matched | 0.2895161290322581 | 0.2513440860215054 | 0.9903846153846154 | 0.012048192771084338 | 0.7486559139784946 | 0.5561497326203209 |
| declared_structural | correlated_failures | native | 0.2895161290322581 | 0.2513440860215054 | 0.9903846153846154 | 0.012048192771084338 | 0.7486559139784946 | 0.5561497326203209 |
| declared_structural | correlated_failures | matched | 0.2895161290322581 | 0.2513440860215054 | 0.9903846153846154 | 0.012048192771084338 | 0.7486559139784946 | 0.5561497326203209 |
| independent | independent_failures | native | 0.2895161290322581 | 0.2513440860215054 | 0.9903846153846154 | 0.012048192771084338 | 0.7486559139784946 | 0.5561497326203209 |
| independent | independent_failures | matched | 0.2895161290322581 | 0.2513440860215054 | 0.9903846153846154 | 0.012048192771084338 | 0.7486559139784946 | 0.5561497326203209 |
| independent | correlated_failures | native | 0.2895161290322581 | 0.2513440860215054 | 0.9903846153846154 | 0.012048192771084338 | 0.7486559139784946 | 0.5561497326203209 |
| independent | correlated_failures | matched | 0.2895161290322581 | 0.2513440860215054 | 0.9903846153846154 | 0.012048192771084338 | 0.7486559139784946 | 0.5561497326203209 |
| fully_correlated | independent_failures | native | 0.2895161290322581 | 0.2513440860215054 | 0.9903846153846154 | 0.012048192771084338 | 0.7486559139784946 | 0.5561497326203209 |
| fully_correlated | independent_failures | matched | 0.2895161290322581 | 0.2513440860215054 | 0.9903846153846154 | 0.012048192771084338 | 0.7486559139784946 | 0.5561497326203209 |
| fully_correlated | correlated_failures | native | 0.2895161290322581 | 0.2513440860215054 | 1.0 | 0.0 | 0.7486559139784946 | 0.5561497326203209 |
| fully_correlated | correlated_failures | matched | 0.2895161290322581 | 0.2513440860215054 | 0.9903846153846154 | 0.012048192771084338 | 0.7486559139784946 | 0.5561497326203209 |

Heatmap source cells:

| Assumption | Independent failures | Correlated failures |
| --- | ---: | ---: |
| declared_structural | 0.2895161290322581 | 0.2895161290322581 |
| independent | 0.2895161290322581 | 0.2895161290322581 |
| fully_correlated | 0.2895161290322581 | 0.2895161290322581 |

## Corruption counts

### Native `declared_structural` / `independent_failures`

loss `0.2895161290322581`, coverage `0.2513440860215054`, false acceptance `0.9903846153846154`, false rejection `0.012048192771084338`, uncertainty `0.7486559139784946`, selective risk `0.5561497326203209`, team `['evidence', 'rule']`, worst column `['evidence']`, tie count `1`, status `available`

- targets `['confidence']` (1 verifiers); effective corruptions `162`; preserved abstentions `558` across `744` candidates
- targets `['evidence']` (1 verifiers); effective corruptions `185`; preserved abstentions `559` across `744` candidates
- targets `['rule']` (1 verifiers); effective corruptions `2`; preserved abstentions `742` across `744` candidates
- targets `['semantic']` (1 verifiers); effective corruptions `227`; preserved abstentions `517` across `744` candidates
### Native `declared_structural` / `correlated_failures`

loss `0.2895161290322581`, coverage `0.2513440860215054`, false acceptance `0.9903846153846154`, false rejection `0.012048192771084338`, uncertainty `0.7486559139784946`, selective risk `0.5561497326203209`, team `['evidence', 'rule']`, worst column `['confidence', 'evidence', 'semantic']`, tie count `1`, status `available`

- targets `['confidence', 'evidence', 'semantic']` (3 verifiers); effective corruptions `574`; preserved abstentions `1634` across `744` candidates
- targets `['rule']` (1 verifiers); effective corruptions `2`; preserved abstentions `742` across `744` candidates
### Native `independent` / `independent_failures`

loss `0.2895161290322581`, coverage `0.2513440860215054`, false acceptance `0.9903846153846154`, false rejection `0.012048192771084338`, uncertainty `0.7486559139784946`, selective risk `0.5561497326203209`, team `['evidence', 'rule']`, worst column `['evidence']`, tie count `1`, status `available`

- targets `['confidence']` (1 verifiers); effective corruptions `162`; preserved abstentions `558` across `744` candidates
- targets `['evidence']` (1 verifiers); effective corruptions `185`; preserved abstentions `559` across `744` candidates
- targets `['rule']` (1 verifiers); effective corruptions `2`; preserved abstentions `742` across `744` candidates
- targets `['semantic']` (1 verifiers); effective corruptions `227`; preserved abstentions `517` across `744` candidates
### Native `independent` / `correlated_failures`

loss `0.2895161290322581`, coverage `0.2513440860215054`, false acceptance `0.9903846153846154`, false rejection `0.012048192771084338`, uncertainty `0.7486559139784946`, selective risk `0.5561497326203209`, team `['evidence', 'rule']`, worst column `['evidence']`, tie count `1`, status `available`

- targets `['confidence']` (1 verifiers); effective corruptions `162`; preserved abstentions `558` across `744` candidates
- targets `['evidence']` (1 verifiers); effective corruptions `185`; preserved abstentions `559` across `744` candidates
- targets `['rule']` (1 verifiers); effective corruptions `2`; preserved abstentions `742` across `744` candidates
- targets `['semantic']` (1 verifiers); effective corruptions `227`; preserved abstentions `517` across `744` candidates
### Native `fully_correlated` / `independent_failures`

loss `0.2895161290322581`, coverage `0.2513440860215054`, false acceptance `0.9903846153846154`, false rejection `0.012048192771084338`, uncertainty `0.7486559139784946`, selective risk `0.5561497326203209`, team `['evidence', 'rule']`, worst column `['evidence']`, tie count `1`, status `available`

- targets `['confidence']` (1 verifiers); effective corruptions `162`; preserved abstentions `558` across `744` candidates
- targets `['evidence']` (1 verifiers); effective corruptions `185`; preserved abstentions `559` across `744` candidates
- targets `['rule']` (1 verifiers); effective corruptions `2`; preserved abstentions `742` across `744` candidates
- targets `['semantic']` (1 verifiers); effective corruptions `227`; preserved abstentions `517` across `744` candidates
### Native `fully_correlated` / `correlated_failures`

loss `0.2895161290322581`, coverage `0.2513440860215054`, false acceptance `1.0`, false rejection `0.0`, uncertainty `0.7486559139784946`, selective risk `0.5561497326203209`, team `['evidence', 'rule']`, worst column `['confidence', 'evidence', 'rule', 'semantic']`, tie count `1`, status `available`

- targets `['confidence', 'evidence', 'rule', 'semantic']` (4 verifiers); effective corruptions `576`; preserved abstentions `2376` across `744` candidates

The matched columns repeat the declared independent columns and the declared correlated columns for every assumption. They are stored in `results.json` under `dependency.matched`.

## Paired differences against the declared model

Each contrast is the other assumption minus the declared model, on the declared model's worst matched column, with the same targeted members. Seed `20261113`, `2000` group resamples.

- `independent independent_failures minus declared`: mean `0.0`, interval `[0.0, 0.0]`, groups `372`, exact zero groups `372`, severity matched `True`.
- `fully_correlated independent_failures minus declared`: mean `0.0`, interval `[0.0, 0.0]`, groups `372`, exact zero groups `372`, severity matched `True`.
- `independent correlated_failures minus declared`: mean `0.0`, interval `[0.0, 0.0]`, groups `372`, exact zero groups `372`, severity matched `True`.
- `fully_correlated correlated_failures minus declared`: mean `0.0`, interval `[0.0, 0.0]`, groups `372`, exact zero groups `372`, severity matched `True`.

Native correlated columns are not used for these contrasts, because their targets differ by assumption.

## Interpretation

The declared model does not reduce validation loss relative to either alternative. The three assumptions select the same team and the same worst-column loss on both the native and the matched attacks. Cold-start weights are zero, and the selected team is evidence plus rule. Rule abstains on 742 of the 744 candidates in the rule column (`preserved_abstentions` 742, effective corruptions 2), so a multi-verifier group average and a member average usually have only one active vote.

Independent and correlated scenarios do not change that worst-column loss or coverage. They do change the false-acceptance and false-rejection split in the one native column that also forces the two directional rule reports.

## Figures

- `evaluation/experiments/experiment3/ablation_v1/outputs/figures/dependency_robustness_heatmap.svg`
- `evaluation/experiments/experiment3/ablation_v1/outputs/figures/dependency_coverage_heatmap.svg`
- `evaluation/experiments/experiment3/ablation_v1/outputs/figures/ablation_effect_differences.svg`

Displayed heatmap values use six decimals of the stored loss. The paired-difference figure draws the calculated intervals and a zero line.

## Sources

- `evaluation/experiments/experiment3/ablation_v1/failures.py`: `declared_registry`, `independent_registry`, `fully_correlated_registry`, `independent_attacks`, `correlated_attacks`, `matched_attacks`, `apply_attack`, `severity`.
- `app/game/dependencies.py`: `DependencyRegistry.groups`.
- `app/game/offline/attacks.py`: `transform`.
- `app/decision/dependency_aggregation.py`: `aggregate_dependency_groups`.
- `evaluation/experiments/experiment3/ablation_v1/runner.py`: `run_dependency`.

## Command

`python evaluation/experiments/experiment3/ablation_v1/runner.py`

## Test results

Command:

`python -m pytest tests/test_experiment3_ablation_v1.py tests/test_experiment3_visualizations.py tests/test_dependency_aggregation.py tests/test_experiment3_synthetic.py tests/test_experiment3_empirical_integration.py evaluation/tests/test_experiment3_dependency_heatmap.py --tb=line -q --continue-on-collection-errors`

Result: 102 passed, 1 error. Pytest exit code 1.

The error is collection of `tests/test_experiment3_synthetic.py`:

`ImportError: cannot import name 'CONTROLLED_SYNTHETIC_ASSUMPTION' from 'app.game.dependencies'`.

`app/game/dependencies.py` was not modified for ablation v1. The other five files collected and passed. That includes `tests/test_experiment3_ablation_v1.py`, which checks the registries, failure scope, unchanged reports, matched inputs, group bootstrap, missing cells, and the completed result file.

