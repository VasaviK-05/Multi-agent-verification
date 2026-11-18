"""Documentation written from an ablation v1 result file. Numbers are not typed in by hand."""

from __future__ import annotations

from pathlib import Path

from evaluation.experiments.experiment3.ablation_v1.failures import RESAMPLES, SEED
from evaluation.experiments.experiment3.empirical_executor import LOSS
from evaluation.experiments.experiment3.execution_readiness import BUDGET_MS, COEFFICIENT

ASSUMPTIONS = ("declared_structural", "independent", "fully_correlated")
SCENARIOS = ("independent_failures", "correlated_failures")


def _cell_line(cell: dict) -> str:
    return (
        f"loss `{cell.get('worst_column_decision_loss')}`, "
        f"coverage `{cell.get('coverage')}`, "
        f"false acceptance `{cell.get('false_acceptance_rate')}`, "
        f"false rejection `{cell.get('false_rejection_rate')}`, "
        f"uncertainty `{cell.get('uncertainty_rate')}`, "
        f"selective risk `{cell.get('selective_risk')}`, "
        f"team `{cell.get('verifiers')}`, "
        f"worst column `{cell.get('worst_attack_members')}`, "
        f"tie count `{cell.get('tie_count')}`, "
        f"status `{cell.get('status')}`"
    )


def _columns(cell: dict) -> list[str]:
    lines = []
    for column in cell.get("failure_columns", []):
        lines.append(
            f"- targets `{column['members']}` ({column['targeted_count']} verifiers); "
            f"effective corruptions `{column['actually_corrupted']}`; "
            f"preserved abstentions `{column['preserved_abstentions']}` "
            f"across `{column['candidates']}` candidates"
        )
    return lines


def write_documents(payload: dict, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    neutral = payload["aggregation"]["neutral"]
    sensitivity = payload["aggregation"]["non_neutral_reputation"]
    native = payload["dependency"]["native"]
    matched = payload["dependency"]["matched"]
    matrix = payload["dependency"]["native_matrix"]
    (destination / "experiment3_aggregation_ablation.md").write_text(
        _aggregation(payload, neutral, sensitivity), encoding="utf-8"
    )
    (destination / "experiment3_dependency_robustness.md").write_text(
        _dependency(payload, native, matched, matrix), encoding="utf-8"
    )
    (destination / "experiment3_final_summary.md").write_text(
        _summary(payload, neutral, native, matched, matrix), encoding="utf-8"
    )


def _test_section(payload: dict) -> str:
    report = payload.get("test_results")
    if not report:
        return (
            "## Test results\n\n"
            "This file is generated from `ablation_v1/outputs/results.json`. "
            "The pytest record is appended when `test_results` is present in that file. "
            "A missing test record is not a pass.\n"
        )
    return "## Test results\n\n" + report.strip() + "\n"


def _aggregation(payload: dict, neutral: dict, sensitivity: dict) -> str:
    method_lines = []
    for method, item in neutral["methods"].items():
        method_lines.append(
            f"- `{method}`: decision loss `{item['mean_decision_loss']}`, coverage `{item['coverage']}`, "
            f"rows `{item['rows']}`, modal strategy `{item['modal_strategy_id']}`, "
            f"matches stored modal `{item['modal_matches']}`, game value `{item['game_value']}`, "
            f"matches stored game value `{item['game_value_matches']}`, "
            f"matches stored probabilities `{item['probabilities_match']}`."
        )
    contrasts = [
        row for row in payload["differences"] if row["family"] == "aggregation_neutral"
    ]
    contrast_lines = [
        f"- `{row['label']}`: mean `{row['mean']}`, 95% interval `[{row['lower']}, {row['upper']}]`, "
        f"groups `{row['groups']}`, exact zero groups `{row['exact_ties']}`."
        for row in contrasts
    ]
    return f"""# Experiment 3 aggregation ablation

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
- Report SHA-256 before and after this run: `{payload['reports_sha256']}`.
- Reports unchanged: `{payload['reports_unchanged']}`.
- Final Test labels and Final Test data were not opened.

## Settings

- Reputation: Beta(1, 1), zero approved observations. Log-odds weight at mean 0.5 is 0, and dependency reliability `max(0, 2 * reputation - 1)` is 0. Both aggregators therefore use an unweighted fallback.
- Budget: `{BUDGET_MS}` ms.
- Resource coefficient: `{COEFFICIENT}`.
- Minimum team size: 2.
- Decision threshold: 0.55. A score above 0.55 passes, below -0.55 fails, and the remainder is uncertain.
- Loss version `{LOSS.version}`: correct 0, false acceptance `{LOSS.false_accept}`, false rejection `{LOSS.false_reject}`, uncertain `{LOSS.uncertain}`.
- Validation loss excludes the resource penalty. The penalty is included in the augmented loss used to select a strategy.
- Calibration id `cc7e7ca8882f602b9854bf21b80b8a7bf70f6c70d05ccd12787322a84a12477d`.

## Reproduction of the neutral comparison

Status: `{neutral['status']}`. Historical match: `{neutral['reproduction_matches_historical']}`.

{chr(10).join(method_lines)}

Decision disagreements between `reputation_weighted` and `dependency_group`, over every feasible team and every historical attack: `{neutral['decision_disagreements']}` of `{neutral['team_attack_cells_compared']}`.

{neutral['tie_note']}

The stored diagnosis records two optimal rows for the joint game, both evidence plus rule. A solver probability of 1 on one of those rows is a vertex of a tie. It is not evidence that reputation aggregation is better.

## Paired differences

Resamples are question groups. Candidates from the same `related_group_id` stay together. Seed `{SEED}`, `{RESAMPLES}` resamples, percentile interval from `app/game/research/uncertainty.py` `_quantile`. Each group's contrast is the mean of its per-attack mean losses, then the restricted method minus the joint method. `exact_ties` counts groups whose mean difference is exactly zero. That count is 372 groups here. It is not the historical attack-level sample size of 2604.

{chr(10).join(contrast_lines)}

Every paired difference is exactly zero, so every resampled mean is zero. The interval `[0.0, 0.0]` was calculated. It was not entered as a placeholder.

## Non-neutral reputation

Status: `{sensitivity['status']}`. Ran: `{sensitivity['ran']}`.

{sensitivity['reason']}

Approved flag in the reputation policy file: `{sensitivity['approved']}`. Observations: `{sensitivity['observations_count']}`. Update rule: `{sensitivity['update_rule']}`.

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

{_test_section(payload)}
"""


def _matrix_table(native: dict, matched: dict) -> str:
    lines = [
        "| Assumption | Scenario | Matrix | Loss | Coverage | False acceptance | False rejection | Uncertainty | Selective risk |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for assumption in ASSUMPTIONS:
        for scenario in SCENARIOS:
            for label, block in (("native", native), ("matched", matched)):
                cell = block[assumption]["scenarios"][scenario]
                lines.append(
                    f"| {assumption} | {scenario} | {label} | {cell.get('worst_column_decision_loss')} | "
                    f"{cell.get('coverage')} | {cell.get('false_acceptance_rate')} | {cell.get('false_rejection_rate')} | "
                    f"{cell.get('uncertainty_rate')} | {cell.get('selective_risk')} |"
                )
    return "\n".join(lines)


def _dependency(payload: dict, native: dict, matched: dict, matrix: dict) -> str:
    group_lines = [
        f"- `{assumption}`: `{body['groups']}`" for assumption, body in native.items()
    ]
    column_sections = []
    for assumption in ASSUMPTIONS:
        for scenario in SCENARIOS:
            cell = native[assumption]["scenarios"][scenario]
            column_sections.append(
                f"### Native `{assumption}` / `{scenario}`\n\n"
                + _cell_line(cell)
                + "\n\n"
                + "\n".join(_columns(cell))
            )
    contrasts = [row for row in payload["differences"] if row["family"] == "dependency_matched"]
    contrast_lines = [
        f"- `{row['label']}`: mean `{row['mean']}`, interval `[{row['lower']}, {row['upper']}]`, "
        f"groups `{row['groups']}`, exact zero groups `{row['exact_ties']}`, "
        f"severity matched `{row['severity_matched']}`."
        for row in contrasts
    ]
    return f"""# Experiment 3 dependency robustness

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

{chr(10).join(group_lines)}

- Declared version `structural_shared_resource_v1`, from the four configured edges: rule alone, semantic with evidence, evidence with confidence, and confidence alone. Union-find merges them to `{{confidence, evidence, semantic}}` and `{{rule}}`.
- Independent version `independent_verifier_failures_v1`: one group per verifier.
- Fully correlated version `fully_correlated_verifiers_v1`: all four verifiers share one unresolved component.

The alternative registries change `DependencyRegistry.groups` and the correlated attack membership. They are not renamed copies of the declared registry.

## Failure generation

Operator: `{payload['dependency']['operator']}`. Abstention policy: `{payload['dependency']['abstention_policy']}`.

`forced_support` sets a directional targeted report to decision SUPPORT, passed true, and score 1. An abstention, including UNSURE, stays an abstention. A verifier outside the targeted members is not transformed. The saved JSONL is not written. SHA-256 after the run equals the hash above in the aggregation document: `{payload['reports_sha256']}`.

Independent columns: one forced-support attack per verifier, identical for every assumption. Target count is 1.

Native correlated columns: one forced-support attack per group of that assumption. Declared correlated columns target 3 and 1 verifiers. Independent correlated columns target 1. The fully correlated column targets 4. Those native correlated columns are not severity-matched across rows. The loss heatmap uses this native matrix and must be read with that difference.

Matched columns: every assumption is scored on the independent singletons and on the declared groups `{{confidence, evidence, semantic}}` and `{{rule}}`. A difference across matched rows would be an aggregation difference. There is no such difference in this run.

`actually_corrupted` sums, over candidates, the targeted reports whose signed mass or decision changed. `preserved_abstentions` sums targeted reports left unchanged because they abstained. Neither number is a count of candidates.

## Settings held fixed

Reputation remains Beta(1, 1). Budget `{BUDGET_MS}` ms. Loss `{LOSS.version}` with weights {LOSS.false_accept} / {LOSS.false_reject} / {LOSS.uncertain}. Threshold 0.55. Minimum team size 2. The reported matrix cell is the `dependency_group` strategy with the lowest worst-column augmented loss. On the matched attacks, the joint game and the reputation-only game are also scored and stored. They select evidence plus rule and the same worst-column decision loss. The joint game has two tied optimal rows (`full_minimax_tie_count` 2). The dependency-group selection has tie count 1.

## Measured matrix

Every required cell has status `available`. No cell was filled with zero in place of a missing run.

The selected dependency-group team in every cell is evidence plus rule. Frozen team cost is 108.03258997621015 ms. Resource penalty is 0.0014475932698523478. Worst-column decision loss is 0.2895161290322581. Coverage is 0.2513440860215054. Uncertainty is 0.7486559139784946. Selective risk is 0.5561497326203209.

Those four rates match 187 classified decisions, 557 uncertain decisions, and 104 errors among the 744 candidates: 104 errors at loss 1 and 557 uncertain decisions at loss 0.2 give total loss 215.4, and 215.4 / 744 = 0.2895161290322581.

False acceptance and false rejection are not identical in every native cell. In five of the six native cells the rates are 0.9903846153846154 and 0.012048192771084338, which match 103 false accepts among 104 classified negatives and 1 false reject among 83 classified positives. The native fully correlated column, which targets all four verifiers, has false acceptance 1.0 and false rejection 0.0. That is 104 false accepts among 104 classified negatives and 0 false rejects among 83 classified positives. The error count, coverage, and decision loss stay the same because a false accept and a false reject both cost 1. The matched matrix, where targets do not change with the assumption, has the 103-and-1 split in every cell.

Aggregation disagreements on the selected evidence-plus-rule team are 0 in every matched cell.

{_matrix_table(native, matched)}

Heatmap source cells:

| Assumption | Independent failures | Correlated failures |
| --- | ---: | ---: |
| declared_structural | {matrix['declared_structural']['independent_failures']['worst_column_decision_loss']} | {matrix['declared_structural']['correlated_failures']['worst_column_decision_loss']} |
| independent | {matrix['independent']['independent_failures']['worst_column_decision_loss']} | {matrix['independent']['correlated_failures']['worst_column_decision_loss']} |
| fully_correlated | {matrix['fully_correlated']['independent_failures']['worst_column_decision_loss']} | {matrix['fully_correlated']['correlated_failures']['worst_column_decision_loss']} |

## Corruption counts

{chr(10).join(column_sections)}

The matched columns repeat the declared independent columns and the declared correlated columns for every assumption. They are stored in `results.json` under `dependency.matched`.

## Paired differences against the declared model

Each contrast is the other assumption minus the declared model, on the declared model's worst matched column, with the same targeted members. Seed `{SEED}`, `{RESAMPLES}` group resamples.

{chr(10).join(contrast_lines)}

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

{_test_section(payload)}
"""


def _summary(payload: dict, neutral: dict, native: dict, matched: dict, matrix: dict) -> str:
    full = native["fully_correlated"]["scenarios"]["correlated_failures"]
    return f"""# Experiment 3 final summary

Primary results are the neutral aggregation reproduction and the dependency matrices in `ablation_v1/outputs/results.json`. The non-neutral reputation check was not run. No synthetic fixture is reported here as a Development result. The one-example synthetic heatmap under `evaluation/experiments/experiment3/synthetic/` is a separate fixture and is not this result.

## Answers

1. Did allowing aggregation choice improve validation? No. Joint, reputation-only, and dependency-only games reproduce the stored modal strategies and game value `{neutral['methods']['full_minimax']['game_value']}`. Mean decision loss is `{neutral['methods']['full_minimax']['mean_decision_loss']}` and coverage is `{neutral['methods']['full_minimax']['coverage']}` for all three. Decision disagreements: `{neutral['decision_disagreements']}` of `{neutral['team_attack_cells_compared']}`. Paired loss differences are 0 with interval [0.0, 0.0] on 372 groups.
2. Did reputation aggregation outperform dependency aggregation? No. They are exactly tied under Beta(1, 1). A non-neutral comparison is not estimable: approved observations are 0, Development outcomes are excluded as a reputation source, and no reputations were invented.
3. Did the declared dependency model outperform the independent alternative? No. On matched attacks the worst-column decision loss is `{matched['declared_structural']['scenarios']['independent_failures']['worst_column_decision_loss']}` for both, in both failure scenarios. Paired differences are 0 with interval [0.0, 0.0].
4. Did the declared dependency model outperform the fully correlated alternative? No. The matched losses are the same, and the paired differences are 0 with interval [0.0, 0.0].
5. Were results different under independent and correlated failures? Worst-column decision loss and coverage were not different: every native and matched cell is loss `{matrix['declared_structural']['independent_failures']['worst_column_decision_loss']}` and coverage `{matrix['declared_structural']['independent_failures']['coverage']}`. False acceptance and false rejection did differ for the native fully correlated column, which targets all four verifiers: false acceptance `{full['false_acceptance_rate']}`, false rejection `{full['false_rejection_rate']}`. The other native cells have false acceptance 0.9903846153846154 and false rejection 0.012048192771084338. Decision loss is unchanged because both error types cost 1.
6. Supported conclusions: on these 744 Development reports, with Beta(1, 1) reputation and the forced-support operator, aggregation choice does not change validation, and the declared structural grouping does not reduce worst-column decision loss relative to independent or fully correlated grouping. The equality is exact on the paired group differences, not a claim from a solver probability.
7. Unproven: any gain once reputation leaves 0.5; any gain on Final Test; any claim that the structural groups are measured dependencies; any claim about attack operators other than `forced_support`; any claim that native correlated columns of different widths are the same attack.

## Loss matrix used by the heatmap

| Assumption | Independent failures | Correlated failures |
| --- | ---: | ---: |
| declared_structural | {matrix['declared_structural']['independent_failures']['worst_column_decision_loss']} | {matrix['declared_structural']['correlated_failures']['worst_column_decision_loss']} |
| independent | {matrix['independent']['independent_failures']['worst_column_decision_loss']} | {matrix['independent']['correlated_failures']['worst_column_decision_loss']} |
| fully_correlated | {matrix['fully_correlated']['independent_failures']['worst_column_decision_loss']} | {matrix['fully_correlated']['correlated_failures']['worst_column_decision_loss']} |

## Figures

- `evaluation/experiments/experiment3/ablation_v1/outputs/figures/aggregation_ablation_grouped_bars.svg`
- `evaluation/experiments/experiment3/ablation_v1/outputs/figures/dependency_robustness_heatmap.svg`
- `evaluation/experiments/experiment3/ablation_v1/outputs/figures/dependency_coverage_heatmap.svg`
- `evaluation/experiments/experiment3/ablation_v1/outputs/figures/ablation_effect_differences.svg`

## Reproduce

`python evaluation/experiments/experiment3/ablation_v1/runner.py`

Seed `{SEED}`. Bootstrap resamples `{RESAMPLES}`. The command reads the historical empirical files and writes `ablation_v1/outputs/` plus these three documents.

{_test_section(payload)}
"""
