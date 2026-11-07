# Baseline Comparison

## 1. Purpose and scope

This document records the baseline strategies and comparative results used in the capstone's offline multi-agent verification experiments.

The comparisons cover:
- Individual feasible-team diagnostics.
- Unconstrained cost-inclusive optimization policies.
- Greedy-team selection.
- Uniform feasible-strategy mixing.
- The fitted policy and its development performance.

The authoritative sources are `docs/multitask_policy_results.md` and `docs/factual_policy42_results.md`.

All reported comparisons are based on retained development evidence. They are exploratory engineering diagnostics, not held-out research results.

## 2. Comparison principles

Comparisons must use the same declared question scope, verifier roster, execution guards and applicable resource assumptions.

Keep validation loss, decision coverage, uncertainty, false acceptance, false rejection and estimated cost distinct.

A lower estimated cost does not establish better verification. A mathematically optimal objective does not necessarily produce a useful operational policy.

Do not interpret development comparisons as proof of generalization, robustness or efficiency improvement.

## 3. Individual-team coverage comparisons

The 2026-10-31 multi-task engineering campaign evaluated seven feasible teams and both aggregation methods per cohort, giving fourteen strategies per task.

All three primary 90% clean-coverage optimization problems were infeasible.

The maximum individual-strategy clean coverage was:

| Task | Maximum coverage | Correct decisions | Clean validation loss |
|---|---:|---:|---:|
| Arithmetic | 82.5% | 33/40 | 0.035 |
| Semantic equivalence | 0% | 0/40 | 0.2 |
| Factual | 37.5% | 15/40 | 0.125 |

### 3.1 Arithmetic

Rule + Confidence achieved 82.5% clean coverage, with fourteen accepts and nineteen rejects, and zero false acceptances or rejections.

Forced-support and forced-rejection attacks each produced 95% coverage but also nineteen corresponding false decisions and validation loss 0.485.

Suppression produced zero coverage and validation loss 0.2. Confidence inflation retained the clean metrics.

The maximum clean coverage remained below the 90% target.

### 3.2 Semantic equivalence

Maximum clean coverage was zero.

Confidence was the only informative contributor. Every strategy failed the minimum-two-contributor requirement, even when its preliminary score was decisive.

All scenario validation losses were 0.2 with 100% uncertainty.

A similarity measurement cannot create a second informative contributor or an independent source.

### 3.3 Factual verification

Evidence + Confidence achieved 37.5% clean coverage, with eight accepts and seven rejects, zero false acceptances or rejections, and 25 uncertainties.

Forced support produced 47.5% coverage with eight false acceptances and loss 0.305. Forced rejection produced 47.5% coverage with eleven false rejections and loss 0.38.

Suppression produced zero coverage and loss 0.2. Confidence inflation retained the clean metrics.

Adding more roster members did not improve maximum clean coverage.

## 4. Unconstrained cost-inclusive optimization baselines

A separate historical comparison fitted the old cost-inclusive objective for each cohort, independently of the infeasible primary 90%-coverage formulation.

| Task | Selected team | Estimated cost (ms) | Cost-inclusive objective |
|---|---|---:|---:|
| Arithmetic | Evidence + Rule | 91.130921 | 0.200428683 |
| Semantic | Rule + Semantic | 42.432737 | 0.200267673 |
| Factual | Evidence + Rule | 188.903554 | 0.201183232 |

Each selected strategy used reputation-weighted aggregation with probability one. The other thirteen strategy probabilities were zero.

All three policies had:
- Zero decision coverage.
- Zero false acceptance and false rejection.
- 100% uncertainty.
- Validation loss 0.2 in clean and all four attack scenarios.

All probability mass was assigned to zero-clean-coverage strategies. The result represents cheap abstention under the cost-inclusive objective, not useful verification.

The two aggregation methods had equivalent payoffs for the selected always-abstaining comparison teams. The solver's allocation does not establish aggregation superiority.

### 4.1 Artifact validation

The three comparison artifacts were exported and reloaded, certificate-validated, and compared against independent payoff reconstruction/refitting.

Matrix values and probabilities matched at absolute tolerance `1e-12` and relative tolerance zero. Reputation records matched exactly.

No numerical certificate for a qualifying primary policy exists because the primary optimization problem was infeasible.

## 5. Factual Policy42 development baselines

The factual Policy42 campaign compared its fitted policy against two retained development baselines.

### 5.1 Greedy-team baseline

The captured full-team greedy baseline selected Evidence + Confidence using reputation-weighted aggregation.

| Metric | Clean | Forced support | Forced rejection | Inflation | Suppression |
|---|---:|---:|---:|---:|---:|
| Validation loss | 0.01 | 0.505 | 0.48 | 0.01 | 0.2 |
| Decision coverage | 95% | 97.5% | 97.5% | 95% | 0% |

The clean result achieved 95% coverage with validation loss 0.01.

Under forced-support and forced-rejection attacks, coverage remained high but false decisions increased substantially.

### 5.2 Uniform feasible-strategy mixing

Uniform mixing distributed probability across feasible strategies.

| Metric | Clean | Forced support | Forced rejection | Inflation | Suppression |
|---|---:|---:|---:|---:|---:|
| Validation loss | 0.0621428571 | 0.4164285714 | 0.4057142857 | 0.0621428571 | 0.2 |
| Decision coverage | 68.9285714% | Not specified | Not specified | Not specified | 0% |

The clean result had higher validation loss and lower coverage than the greedy-team baseline.

The source handoff reports the attack losses for forced support and forced rejection, but does not provide their corresponding coverage percentages in this summary. They are therefore not inferred here.

### 5.3 Interpretation

These are complete-team development comparisons using the same public decision guards.

They are not equivalent to production baseline early-stopping or feedback behaviour.

The comparisons do not establish held-out superiority or measured efficiency improvement. Detailed counts and separate cost-inclusive objectives remain in the retained development report.

## 6. Measured verifier costs

The multi-task campaign measured the mean of all 80 first and subsequent verifier attempts per cohort. Failures and first calls were retained; no warmup samples were removed.

| Task | Confidence (ms) | Evidence (ms) | Rule (ms) | Semantic (ms) | Full-roster budget (ms) |
|---|---:|---:|---:|---:|---:|
| Arithmetic | 21,127.605639 | 81.452711 | 9.678210 | 39.598705 | 21,258.335265 |
| Semantic | 15,778.139944 | 31.851542 | 0.109292 | 42.323445 | 15,852.424224 |
| Factual | 15,732.456319 | 188.798949 | 0.104605 | 43.686593 | 15,965.046465 |

These values are verifier-attempt wall-clock milliseconds, not monetary costs or guaranteed request latency.

Initialization, resource hashing and checkpoint overhead are outside the `verify` timers. Shared-machine contention also limits portability.

Timing differences do not demonstrate efficiency improvement.

## 7. Comparison interpretation

The comparisons demonstrate different tradeoffs:

- The greedy-team baseline achieved high clean coverage in the factual development set, but forced attacks increased validation loss.
- Uniform feasible-strategy mixing achieved lower clean coverage and higher clean validation loss than greedy selection.
- The fitted factual policy selected Evidence + Rule with probability one but abstained on every clean example because the minimum-two-contributor guard was not satisfied.
- The unconstrained multi-task policies also selected zero-coverage strategies under their cost-inclusive objective.

These results show that optimization objectives, contributor requirements and verifier informativeness can materially affect decision coverage.

No single comparison establishes universal superiority. In particular, lower cost and higher coverage must not be interpreted independently of error rates, uncertainty and attack outcomes.

## 8. Limitations and threats to interpretation

All reported baseline comparisons use prepared development data.

The datasets are reference-assisted and constructed within declared task scopes. They do not establish open-domain verification performance or unseen-task generalization.

Additional limitations include:
- The reserved final groups were procedural/source-known, not independently blinded.
- The two factual source lineages may overlap and are not independent human adjudications.
- One arithmetic-development Confidence attempt timed out after 60 seconds; its failure and duration remain included.
- All three task cohorts shared one machine, so measured costs include contention.
- Similarity measurements and contributor counts do not establish independent evidence sources.
- The shared-unknown dependency model conservatively connects the verifier roster.

The results do not establish held-out poisoning resistance, production-baseline equivalence or measured efficiency improvement.

## 9. Current transfer-evaluation restrictions

The current transfer experiment must apply the original frozen policy to fresh paired clean and altered recordings.

Historical baseline results remain separate from current transfer results.

During transfer evaluation:
- Do not refit or recalibrate policies.
- Do not change probabilities, thresholds, losses or contributor guards.
- Do not update reputation using new reports.
- Do not select a favorable subset of outcomes.
- Preserve all failures, abstentions and started attempts.
- Report observed timings separately from frozen configured cost diagnostics.

The comparison must retain the complete verifier roster in both conditions.

A real transfer experiment remains not ready until the required approvals, current-resource observations, altered resources, paired recordings and resource-bound Evidence proofs are supplied.

## 10. Final conclusion

The historical comparisons show that high clean coverage can coexist with increased error under forced attacks, while cost-minimizing optimization can select policies that abstain on every example.

The factual greedy baseline, uniform mixing and fitted Policy42 policy provide useful development comparisons, but none establishes universal superiority.

The primary multi-task 90%-coverage formulations were infeasible under their fixed settings. Those constraints must not be relaxed after observing the results merely to obtain a feasible policy.

Future scientific changes require a new preregistered experiment and explicit study-owner approval. They must remain separate from the current frozen-policy transfer evaluation.

