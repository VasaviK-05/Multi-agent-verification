# Experiment 3 paper integration

Text below is written so it can be adapted into a paper. It cites only this repository's Development run. It does not add related work, citations, or a hypothesis that the joint policy is superior. Numbers are the verified one-method totals. The other two methods match them. Synthetic sensitivity is named where it appears and is not part of the empirical result.

## Abstract-ready result

On 372 Development groups and 744 candidates, a joint minimax policy and the same game restricted to reputation-weighted or dependency-group aggregation selected the same verifier team, evidence and rule, and made the same decision in all 15,624 cells. The group-level paired difference was 0, and the 95% bootstrap interval was [0, 0]. Pooled over seven attack columns, mean decision loss was 0.2533, coverage 1,237/5,208 (23.75%), and selective risk 525/1,237 (42.44%). The identity is a negative finding about aggregation separation under a cold-start prior. It is not evidence that the methods are equivalent in general, and it is not a Final Test result.

## Methods subsection

Experiment 3 compares three solutions of one Development payoff matrix. `full_minimax` chooses both the verifier team and the aggregation. `fixed_reputation_weighted` and `fixed_dependency_group` choose the team inside one aggregation. Reports, questions, the reputation prior, the loss, the threshold, the budget, and the attacks are matched.

The population is 372 eligible Development groups, 187 GSM8K and 185 HotpotQA, with two candidates per group: one verified-correct answer and one synthetic incorrect answer. Final Test labels were not used. Decision loss charges 1 for a false accept, 1 for a false reject, and 0.2 for uncertainty. The decision threshold is 0.55. Reputation begins at a Beta(1, 1) prior, mean 0.5, with no approved historical observations and no decay.

The resource configuration is a selected setting, not an optimized fit. The coefficient is `1.3399597937725295e-05` loss per millisecond. The budget is `14996.39091498102` milliseconds, bound to frozen calibration `cc7e7ca8882f602b9854bf21b80b8a7bf70f6c70d05ccd12787322a84a12477d`. Feasibility uses those frozen means. Teams smaller than two verifiers are excluded. Teams whose frozen cost exceeds the budget are excluded.

Attacks transform stored verifier reports. The categories are clean, forced support, forced rejection, and confidence inflation. Suppression was unavailable. The declared dependency configuration, `structural_shared_resource_v1`, is an assumption, not a measured dependence. Overlapping groups merge semantic, evidence, and confidence into one failure component and leave rule alone, so each non-clean category contributes two columns. The executed design is 744 × 7 × 3 = 15,624 cells. Policies were solved on the same Development rows that were scored. Uncertainty is handled by a group bootstrap with 2,000 resamples, seed `20261113`, resampling question groups rather than candidate rows.

## Results subsection

Every method returned a pure policy on evidence and rule. The frozen team cost is 108.03258997621015 ms, and the resource penalty on that team is 0.0014475932698523478. The worst-column game value, decision loss plus that penalty, is 0.29096372230211043 for each method. Decision loss in the tables excludes the penalty.

Across 5,208 candidate-attack rows for one method, there were 126 correct accepts, 586 correct rejects, 110 false accepts, 415 false rejects, and 3,971 uncertain decisions. Coverage is 1,237/5,208. The false-acceptance rate is 110/696 and the false-rejection rate is 415/541. Execution failures were 0. The paired comparison against `full_minimax` has mean 0 and interval [0, 0] for both restricted methods, over 372 groups.

The clean column, 744 candidates, has decision loss 0.24327956989247312, coverage 169/744, and selective risk 66/169. Forced support of the model component is the worst column, decision loss 0.2895161290322581, with false accepts 103/104. On HotpotQA that attack classifies 168 of 370 candidates and accepts all of them (74 correct accepts, 94 false accepts). GSM8K remains mostly uncertain: 2,517 of 2,618 pooled rows have decision loss 0.2, and the clean GSM8K cell classifies 11 of 374 candidates.

A rescore of the stored reports found 14 feasible strategies. Evidence and rule is the unique best team. The two aggregations of that team tie. They disagreed on no stored cell. A separate synthetic numerical example can place the two aggregations on opposite sides of the threshold. That example is not part of the Development result. Applying a higher coefficient to the stored decision losses would select rule and semantic. That calculation is a counterfactual, not a second collection. The synthetic resource-sensitivity grid is a different record and is not an estimate of these Development losses.

## Discussion subsection

The result separates two parts of the game. Aggregation restrictions did not matter for this prior and these reports, because a reputation of 0.5 carries zero log-odds weight and zero dependency reliability, and the observed votes did not cross the threshold differently under the two unweighted rules. Team choice did matter: six other feasible teams have higher worst-case loss than evidence and rule. The original question, whether joint selection improves on other selection rules, is not answered here. Greedy, uniform, and fixed-team baselines were not in this comparison.

The verifier record explains the loss pattern. GSM8K semantic reports are all unsure because the inputs have no evidence context. The rule verifier is unsure on 742 of 744 candidates, so the selected team usually follows the evidence vote alone. HotpotQA evidence supplies most of the clean reject signal. Forcing that component to support removes those rejects and produces the false-accept increase. Confidence calls were slow and often unsure, and the solved policy did not include confidence. Recorded wall times differ from the frozen means used for the budget. Those wall times were not substituted into the game.

A zero paired difference with interval [0, 0] should be reported as an observed identity on this sample. It should not be reported as statistical proof that the aggregation rules are equivalent.

## Limitations subsection

Evaluation used Development rows for both fitting and scoring. Final Test labels were not opened. Incorrect candidates are synthetic, not human-verified incorrect answers. Reputation has no approved history. Dependency groups are configured, not measured. Model-weight hashes are unknown. The run was authorized by the research lead without independent approval or other contributors' signatures, and no signature was fabricated. The participant floor and the uniform capability label are assumptions. The coefficient and budget were not optimized. GSM8K decisive counts are small. Report-level attacks are not a demonstration that the underlying models were compromised.

## Figure and table references

Use only files under `evaluation/experiments/experiment3/empirical/figures/` for empirical plots. Each is marked `EMPIRICAL`.

| Paper element | Source |
| --- | --- |
| Overall rates and denominators | Table in section C of `experiment3_final_research_synthesis.md` |
| Attack-wise decision loss | `attack_decision_loss_by_method.svg` and the attack table in the synthesis |
| Benchmark coverage and uncertainty | `benchmark_coverage_uncertainty.svg` |
| Selective risk, with classified denominators on the labels | `benchmark_selective_risk.svg` |
| False acceptance and false rejection by attack | `attack_false_rates.svg` |
| Clean verifier decisions | `verifier_uncertainty.svg` |
| Feasible-team worst-case loss | `team_selection.svg` |
| Frozen cost against clean coverage | `resource_cost_coverage.svg` |
| Earlier loss chart, preserved | `attack_validation_loss.svg` |
| Cell-level benchmark table | `experiment3_empirical_results.md` |

Figures under `evaluation/experiments/experiment3/synthetic/figures/` and the files under `evaluation/experiments/experiment3/sensitivity/` are synthetic or configuration-sensitivity material. They should not appear in an empirical results section except as a labeled aside that a coefficient was not derived from them.

## Empirical and synthetic boundary

| Record | Label |
| --- | --- |
| `empirical/results.json`, metrics, bootstrap, verifier reports, empirical figures | EMPIRICAL |
| Policy rescore of those reports, including the zero-disagreement count | EMPIRICAL diagnosis |
| High-coefficient team switch on the stored decision losses | Counterfactual, not a new collection |
| Controlled three-vote aggregation split | SYNTHETIC illustration |
| `experiment3_resource_sensitivity.md` and `sensitivity/` | SYNTHETIC / configuration sensitivity |
