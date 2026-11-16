# Experiment 3 protocol specification

Status: `PENDING_APPROVAL`. This is not a frozen `ExperimentSpecification`. `specification_id` is null. Collection and the empirical run are not authorized. The synthetic fixture is not this specification's result. Specification SHA-256: `f64b47cfe206548c57f60d48ebf2404dacce65b46ed05e4210fe68fb8250f529`. The protocol approval template cites that hash and remains `NOT_AN_APPROVAL`.

Machine-readable copy: `evaluation/config/experiments/experiment3_specification.json`.

## Research questions

1. What is the effect of the aggregation strategy when verifier reports, questions, reputation inputs, costs, loss, coverage rules, and attack budgets stay fixed?
2. What is the effect of the declared dependency structure on which verifiers an attack can target together, and on the resulting decisions?

## Comparison methods

`full_minimax`, `fixed_reputation_weighted`, and `fixed_dependency_group`. A probability placed on one of two tied actions is not evidence that the aggregation is better.

## Controlled variables

Question groups, verifier reports, reputation inputs, verifier cost measurements, loss function, coverage and decision threshold, attack scenarios, and budget. The approved Development roster is `research_v1_exploratory_eligibility_approved_v1`, body SHA-256 `f2cc0fd108b961bf4795767df4f90e92d7fa0f418ef9865d0206f32d7b45282d`. Final Test is prohibited.

## Experimental variables

Aggregation policy and dependency configuration. The provisional dependency configuration is `structural_shared_resource_v1`: shared model resources, not a measured correlation, and not one group of every verifier. The two-group registry remains a synthetic assumption.

## Outcomes

Correct acceptance and rejection, false acceptance and rejection, coverage, uncertainty, selective risk, validation loss, estimated attempt cost, unresolved cases, execution failures, aggregation frequencies, and verifier inclusion frequencies.

## Analysis

Comparisons are paired on `related_group_id` and the attack condition, and reported by benchmark and attack. The plotted contrast is ablation validation loss minus `full_minimax` loss. Positive values are worse than the full game, negative values are an improvement, and zero is identical loss. The interval resamples `related_group_id` and keeps every paired attack difference inside the drawn groups. Independent method means are not compared. Unresolved labels stay out of binary outcomes. A missing side of a pair is counted and is not imputed. Execution failures are reported and are not filled in as decisions. The operational eligible group count is 372. That count is not a power calculation.

Aggregation frequencies describe the solved mixture. They are not evidence that one aggregation is superior. Identical decisions and identical losses are reported when the matched rows have them.

## Research visualizations

The machine-readable figure contract is in `experiment3_specification.json`. Figures are drawn from result rows by `evaluation/analysis/visualization/experiment3.py`. A synthetic figure is labeled `SYNTHETIC` and is not written into an empirical result directory.

### Aggregation ablation grouped bars

The bars compare `full_minimax`, `fixed_reputation_weighted`, and `fixed_dependency_group` on validation loss and decision coverage. Question groups, verifier reports, reputation, costs, loss, budget, coverage rules, and attacks stay matched. Bars are grouped by clean and attacked conditions and by benchmark. Uncertainty intervals appear only after the bootstrap settings are approved. Sample size is printed with each bar.

### Dependency robustness heatmap

Columns are independent failures and correlated failures. Rows are the declared dependency model and any alternative assumption. The cell is validation loss, with the aggregation policy held fixed. A missing combination is marked unavailable. The empirical heatmap is not estimable: the only declared empirical model is provisional `shared_unknown`, and that model places every verifier in one group, so it cannot separate independent from correlated failures. The synthetic two-group registry can be plotted only as `SYNTHETIC`. It is not an empirical alternative.

### Paired ablation-effect difference plot

Each ablation is compared with `full_minimax` inside the same `related_group_id` and attack condition. The point is the mean paired loss difference. The interval, when the bootstrap settings are approved, is drawn around that mean. A horizontal line marks zero. The mean is the practical effect and is reported separately from the interval. Subgroup splits by benchmark or attack are produced only when the paired sample supports them. Missing pairs are counted.

## Result rows

Each analyzed row keeps `related_group_id`, benchmark, attack condition, dependency model, dependency scenario, aggregation method, decision, gold label, validation loss, coverage, uncertainty, verifier reports, verifier costs, execution status, provenance, and configuration id. The evidence label is `SYNTHETIC` or `EMPIRICAL`. Final Test rows are refused. `UNRESOLVED` gold labels are not binary correctness outcomes.

`PENDING_APPROVAL`: loss weights, resource coefficient, decision threshold, budget, suppression mode, bootstrap resamples, confidence level, bootstrap seed, and the sample-size justification. Those fields stay null in the specification's analysis block. The same file records the proposal under `proposed_settings_not_approved`: false-acceptance loss 1.0, false-rejection loss 1.0, uncertainty loss 0.2, decision threshold 0.55, suppression unavailable, 2,000 bootstrap resamples, confidence 0.95, seed 20261113, and all 372 approved Development groups. Resource coefficient and verifier budget stay null. `these_values_are_not_approved_settings` is true. The approval templates under `evaluation/config/experiments/approvals/` are not approvals.

The heatmap name `provisional_shared_unknown_v1` puts every verifier in one failure group, so it cannot separate independent and correlated failures. The dependency configuration file records a different unapproved model, `structural_shared_resource_v1`. Hypothetical alternatives are stored in `evaluation/experiments/experiment3/hypothetical/configurations.json` with no loss values.

## Synthetic separation

`evaluation/experiments/experiment3/synthetic/` is `SYNTHETIC`. It does not satisfy the empirical recording requirement.
