# Figure captions

Every file in this folder is an empirical Development figure. None is a synthetic sensitivity plot. Copied files are byte-for-byte copies of the source figures. The paired-difference figure was drawn from the two recorded bootstrap files and did not change those files.

## `experiment3_attack_loss_by_method.svg`

Source: `evaluation/experiments/experiment3/empirical/figures/attack_decision_loss_by_method.svg`.

Mean decision loss by attack for the three Experiment 3 methods. Each bar uses 744 candidates. The three bars in a group have the same height because the methods match on every cell. Decision loss excludes the resource penalty. The tallest group is forced support of the model component, mean `0.2895161290322581`.

## `experiment3_attack_loss_by_benchmark.svg`

Source: `evaluation/experiments/experiment3/empirical/figures/attack_validation_loss.svg`.

The preserved benchmark chart. GSM8K bars use 374 candidates. HotpotQA bars use 370 candidates. Labels on the bars are three-decimal displays. GSM8K clean is `0.2074866310160428`, shown as 0.207. HotpotQA clean is `0.2794594594594595`, shown as 0.279. The pooled clean mean, `0.24327956989247312`, is not printed on this figure. Use `01_experiment3_results.md` for full-precision pooled values.

## `experiment3_coverage_uncertainty.svg`

Source: `evaluation/experiments/experiment3/empirical/figures/benchmark_coverage_uncertainty.svg`.

Coverage and uncertainty for clean reports versus forced support of the model component. Denominators are 374 GSM8K candidates and 370 HotpotQA candidates.

## `experiment3_false_acceptance_rejection.svg`

Source: `evaluation/experiments/experiment3/empirical/figures/attack_false_rates.svg`.

False-acceptance and false-rejection rates by attack. The figure's denominators are the classified negatives and classified positives for that attack, not the 744-candidate population. Pooled rates are 110/696 and 415/541.

## `experiment3_verifier_decisions.svg`

Source: `evaluation/experiments/experiment3/empirical/figures/verifier_uncertainty.svg`.

Clean SUPPORT, REJECT, and UNSURE counts for the four verifiers. This is not an attacked-report chart. Rule is UNSURE on 742 of 744 candidates. GSM8K semantic is UNSURE on all 374 candidates.

## `experiment3_team_selection.svg`

Source: `evaluation/experiments/experiment3/empirical/figures/team_selection.svg`.

Worst-case augmented loss of each feasible team, scored on the stored reports. Evidence + rule is the lowest, at `0.29096372230211043`.

## `experiment1_baseline_decision_loss.svg`

Source: `evaluation/experiments/experiment1/development/figures/method_decision_loss.svg`.

Mean decision loss by attack for full minimax, coverage-greedy, uniform, and the fixed team. Full minimax, uniform, and the fixed team use 744 candidates per attack. The greedy series uses 510 candidates per attack. The image does not print that difference. Do not read the greedy bars as a 744-candidate mean.

## `paired_differences_versus_full_minimax.svg`

Source data: `evaluation/experiments/experiment3/empirical/bootstrap_results.json` and `evaluation/experiments/experiment1/development/bootstrap_results.json`.

Paired mean decision-loss difference versus full minimax, with the recorded 95% intervals. Aggregation contrasts and the fixed-team contrast are zero on 372 groups. Uniform is the 372-group contrast. Greedy is the 255-group contrast. The horizontal positions are the recorded means and interval endpoints. This file was created for the package. The bootstrap files were not edited.
