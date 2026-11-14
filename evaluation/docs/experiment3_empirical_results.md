# Experiment 3 empirical results

Evidence label: `EMPIRICAL`. These numbers are computed from `evaluation/experiments/experiment3/empirical/results.json`, `metrics.json`, and `bootstrap_results.json`. Synthetic sensitivity results and synthetic figures are a different record and are not used below.

The collection is complete. Status `COMPLETE`. Completed cells 15,624 of 15,624. Candidates 744. Groups 372. `final_test_accessed` is false. Execution failures are 0. No gold label was imputed.

The 8,928 count is not this run. It would be 744 candidates × 4 attack kinds × 3 methods. `structural_shared_resource_v1` has two failure components, so each non-clean kind is two columns and suppression is dropped: 744 × 7 × 3 = 15,624. That deviation is recorded in `results.json` as `cell_count_note`.

## What was compared

Methods: `full_minimax`, `fixed_reputation_weighted`, `fixed_dependency_group`.

Attack columns: clean; forced support, forced rejection, and confidence inflation on `['confidence', 'evidence', 'semantic']`; and the same three kinds on `['rule']`.

Each method solved `solve_minimax` on the mean, over the 744 Development candidates, of decision loss plus resource penalty. Fixed methods keep one aggregation through `restricted_matrix`. The reported decision is the modal strategy. Every solved policy is pure (probability 1).

All three methods selected evidence and rule.

- Team cost from frozen means: 108.03258997621015 ms (evidence 107.93551665459138 + rule 0.09707332161876063).
- Resource penalty: `1.3399597937725295e-05` × that cost = 0.0014475932698523478.
- `full_minimax` and `fixed_reputation_weighted` modal strategy `7bebbe44c42c138b65816273a8807e0be825e5543903862c49970aa7f92813ac`.
- `fixed_dependency_group` modal strategy `ad0b8ffb719c57171af3713fed9ef5ee56abfeb911bb36d093c9e29406ae23f0`.
- Game value, decision loss plus the resource penalty on the worst attack column: 0.29096372230211043 for every method.

The strategy identifiers differ because each aggregation has its own strategy object. The selected verifiers, costs, decisions, and losses do not differ. Across 5,208 candidate-attack cells, all three methods have the same decision and the same validation loss. Mismatch count: 0.

Policies were fit on the same Development rows that are scored. This is an in-sample comparison. It is not a Final Test result.

`validation_loss` below is decision loss only. The resource penalty is constant and is not inside those means. `mean_recorded_attempt_cost` in `metrics.json` is the average of the two member means, about 54.016 ms. It is not the team cost.

## Overall, one method

Because the methods match, the totals below are for one method. Multiplying by three recovers the summed counts in `metrics.json`.

Denominator: 5,208 rows = 744 candidates × 7 attacks.

| Quantity | Count or value | Denominator |
| --- | ---: | --- |
| Mean decision loss | 0.2533026113671275 | 5208 |
| GSM8K mean decision loss | 0.21061879297173414 | 2618 (374 × 7) |
| HotpotQA mean decision loss | 0.29644787644787646 | 2590 (370 × 7) |
| Correct accept | 126 | 5208 |
| Correct reject | 586 | 5208 |
| False accept | 110 | 5208 |
| False reject | 415 | 5208 |
| Uncertain | 3971 | 5208 |
| Coverage | 1237/5208 = 0.2375 | classified / rows |
| Uncertainty rate | 3971/5208 = 0.7625 | uncertain / rows |
| False acceptance rate | 110/696 = 0.1580 | false accepts / (false accepts + correct rejects) |
| False rejection rate | 415/541 = 0.7671 | false rejects / (false rejects + correct accepts) |
| Selective risk | 525/1237 = 0.4244 | (false accepts + false rejects) / classified |
| Execution failures | 0 | 5208 |

These overall rates pool benchmarks and attack columns. They are not the clean-condition rate. GSM8K coverage across its 2,618 rows is 0.0386 and its uncertainty rate is 0.9614. HotpotQA coverage across its 2,590 rows is 0.4386 and its uncertainty rate is 0.5614.

## By benchmark and attack

The table is `full_minimax`. The other two methods are identical on every row, including the counts. Each rate uses the classified decisions in that cell, not the full candidate count. GSM8K cells classify 11 or 19 of 374 candidates. A rate of 0.9000 there is 9 false accepts out of 10 classified negatives.

| Benchmark | Attack | Candidates | Classified | Decision loss | Coverage | Uncertainty | CA | CR | FA | FR | FAR | FRR | Selective risk |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| GSM8K | clean | 374 | 11 | 0.2075 | 0.0294 | 0.9706 | 0 | 6 | 0 | 5 | 0.0000 | 1.0000 | 0.4545 |
| GSM8K | confidence_inflation [confidence,evidence,semantic] | 374 | 19 | 0.2139 | 0.0508 | 0.9492 | 0 | 10 | 0 | 9 | 0.0000 | 1.0000 | 0.4737 |
| GSM8K | confidence_inflation [rule] | 374 | 11 | 0.2075 | 0.0294 | 0.9706 | 0 | 6 | 0 | 5 | 0.0000 | 1.0000 | 0.4545 |
| GSM8K | forced_rejection [confidence,evidence,semantic] | 374 | 19 | 0.2139 | 0.0508 | 0.9492 | 0 | 10 | 0 | 9 | 0.0000 | 1.0000 | 0.4737 |
| GSM8K | forced_rejection [rule] | 374 | 11 | 0.2075 | 0.0294 | 0.9706 | 0 | 6 | 0 | 5 | 0.0000 | 1.0000 | 0.4545 |
| GSM8K | forced_support [confidence,evidence,semantic] | 374 | 19 | 0.2166 | 0.0508 | 0.9492 | 8 | 1 | 9 | 1 | 0.9000 | 0.1111 | 0.5263 |
| GSM8K | forced_support [rule] | 374 | 11 | 0.2075 | 0.0294 | 0.9706 | 1 | 5 | 1 | 4 | 0.1667 | 0.8000 | 0.4545 |
| HotpotQA | clean | 370 | 158 | 0.2795 | 0.4270 | 0.5730 | 8 | 89 | 1 | 60 | 0.0111 | 0.8824 | 0.3861 |
| HotpotQA | confidence_inflation [confidence,evidence,semantic] | 370 | 168 | 0.2849 | 0.4541 | 0.5459 | 11 | 92 | 2 | 63 | 0.0213 | 0.8514 | 0.3869 |
| HotpotQA | confidence_inflation [rule] | 370 | 158 | 0.2795 | 0.4270 | 0.5730 | 8 | 89 | 1 | 60 | 0.0111 | 0.8824 | 0.3861 |
| HotpotQA | forced_rejection [confidence,evidence,semantic] | 370 | 168 | 0.3092 | 0.4541 | 0.5459 | 0 | 94 | 0 | 74 | 0.0000 | 1.0000 | 0.4405 |
| HotpotQA | forced_rejection [rule] | 370 | 158 | 0.2795 | 0.4270 | 0.5730 | 8 | 89 | 1 | 60 | 0.0111 | 0.8824 | 0.3861 |
| HotpotQA | forced_support [confidence,evidence,semantic] | 370 | 168 | 0.3632 | 0.4541 | 0.5459 | 74 | 0 | 94 | 0 | 1.0000 | 0.0000 | 0.5595 |
| HotpotQA | forced_support [rule] | 370 | 158 | 0.2795 | 0.4270 | 0.5730 | 8 | 89 | 1 | 60 | 0.0111 | 0.8824 | 0.3861 |

The highest decision loss is HotpotQA forced support on the confidence/evidence/semantic component: 0.36324324324324325 on 370 candidates, 168 classified, 94 false accepts, 0 correct rejects, 74 correct accepts, 0 false rejects. False acceptance rate 1 and false rejection rate 0 are descriptions of that cell, not a general finding.

Rule-targeted columns match the clean column except GSM8K forced support on rule, which moves a few of the 11 classified decisions. That pattern matches the recordings: rule is `UNSURE` on 742 of 744 candidates, so rejecting or inflating an already unsure rule report usually does not change the evidence-plus-rule decision.

## Paired differences

Group-level paired bootstrap. Seed `20261113`. 2,000 resamples. 95% interval. The resample unit is `related_group_id`. Candidate losses inside a group are averaged before the methods are subtracted. Sample size 2,604 is 372 groups × 7 attacks. Missing pairs: 0.

| Contrast against `full_minimax` | Mean difference | Groups | Interval |
| --- | ---: | ---: | --- |
| `fixed_reputation_weighted` | 0.0 | 372 | [0.0, 0.0] |
| `fixed_dependency_group` | 0.0 | 372 | [0.0, 0.0] |

Every one of the 2,604 paired differences is zero, so the interval is degenerate. This does not support a claim that one method has lower loss than another on this collection. It also does not support a general claim that the methods are equivalent. The cold-start prior is the same for every verifier, the budget excludes the full roster and confidence-plus-evidence, and both aggregations selected evidence and rule.

## Recorded verifier behavior

All 744 reports have `ok: true` for semantic, evidence, rule, and confidence. Mean recorded seconds: semantic 0.030, evidence 0.210, rule about 0, confidence 13.247. These durations are observations of this run. Feasibility still uses the frozen calibration means, not these durations.

| Verifier | GSM8K (374) | HotpotQA (370) |
| --- | --- | --- |
| semantic | UNSURE 374, all `no_context` | SUPPORT 150, UNSURE 143, REJECT 77 |
| evidence | UNSURE 357, REJECT 17, SUPPORT 0 | UNSURE 202, REJECT 155, SUPPORT 13 |
| rule | UNSURE 372, REJECT 2 | UNSURE 370 |
| confidence | UNSURE 306, REJECT 46, SUPPORT 22 | UNSURE 252, REJECT 69, SUPPORT 49 |

GSM8K semantic abstention is the empty evidence context on those Development inputs. The selected team does not include semantic or confidence. High GSM8K uncertainty follows from evidence and rule both abstaining on most of those items.

## Interpretation

Under this selected budget, this cold-start prior, and these reports, changing the aggregation method did not change the selected team or any decision. Uncertainty dominates, especially on GSM8K. The attack that most increases decision loss is forced support of the merged confidence/evidence/semantic component, and on HotpotQA that cell accepts every classified candidate. Confidence inflation and forced rejection of that component move HotpotQA loss by less, and rule-only attacks are mostly inert.

The coefficient and budget remain a selected configuration. They were not fit to these outcomes.

## Figure

`evaluation/experiments/experiment3/empirical/figures/attack_validation_loss.svg` plots the decision losses in the table. It is marked `EMPIRICAL`.
