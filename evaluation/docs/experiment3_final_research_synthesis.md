# Experiment 3 final research synthesis

This note is the research narrative for the completed Development run. Measurement details, cell-level tables, and hashes stay in `experiment3_empirical_results.md`, `experiment3_policy_diagnosis.md`, `experiment3_limitations.md`, and `experiment3_reproducibility.md`. Synthetic configuration sweeps stay in `experiment3_resource_sensitivity.md`. Nothing here is a Final Test result.

The original objective in `research_objective.md` asks whether joint team-and-aggregation selection improves validation under resource limits and report corruption. Experiment 3 was the aggregation-and-dependency slice of that question: hold the reports, budget, loss, threshold, and attacks fixed, and compare the joint minimax policy with the same game restricted to reputation-weighted aggregation and to dependency-group aggregation. The run answers that slice on Development. It does not answer the broader claim against greedy, uniform, or fixed-team baselines. Those comparators belong to Experiment 1, which has not been collected.

## A. Research objective

Experiment 3 evaluates three uses of the same Development payoff matrix.

- `full_minimax` may choose both the verifier team and the aggregation.
- `fixed_reputation_weighted` may choose the team but must aggregate with reputation weights.
- `fixed_dependency_group` may choose the team but must aggregate by the declared dependency components.

The attacks are report transformations: clean, forced support, forced rejection, and confidence inflation. Suppression was specified as unavailable and was not collected. The resource question in this experiment is whether one shared budget and one shared loss-per-millisecond coefficient change which team the game selects. The coefficient and budget were chosen as a research configuration. They were not fit to the outcomes.

## B. Experimental methodology

Population: the approved Development eligibility manifest, 372 groups (GSM8K 187, HotpotQA 185), 744 candidates, two per group. One candidate in each pair is `VERIFIED_CORRECT`. The other is `SYNTHETIC_INCORRECT`. Unresolved and ineligible rows are excluded. Sealed Final Test labels were not opened. `final_test_accessed` is false.

Attack design: four categories. `structural_shared_resource_v1` has two failure components, `[confidence, evidence, semantic]` and `[rule]`, because the declared groups overlap. Each non-clean category is one column per component. Clean has no members. That is 7 columns, not 4. The collected grid is 744 candidates × 7 columns × 3 methods = 15,624 complete cells. The 8,928 count would be one column per category. That is not the grid that ran. Duplicate keys: 0. Execution failures: 0.

Decision loss: false acceptance 1.0, false rejection 1.0, uncertainty 0.2. Threshold 0.55. The reported `validation_loss` is decision loss only. The game objective adds `coefficient × frozen team cost`.

Resource configuration: coefficient `1.3399597937725295e-05` loss per millisecond, budget `14996.39091498102` ms, calibration id `cc7e7ca8882f602b9854bf21b80b8a7bf70f6c70d05ccd12787322a84a12477d`. Feasibility uses the frozen non-warmup means. Participant floor 2 and uniform expected capabilities are configuration assumptions.

Reputation: `Beta(1, 1)`, mean 0.5, no decay, zero approved historical observations. Development labels were not written back as reputation updates before the policies were solved. Policies were fit and scored on the same 744 rows.

Bootstrap: paired over `related_group_id`, 2,000 resamples, 95% interval, seed `20261113`. Candidate rows in a group are averaged before the methods are subtracted. An interval is not a significance claim.

## C. Empirical results

All three methods selected evidence + rule, estimated frozen cost 108.03258997621015 ms, and made the same decision on every candidate-attack cell. Mean paired difference versus `full_minimax`: 0.0 on 372 groups and 2,604 group-attack pairs. Both 95% intervals are [0.0, 0.0]. The interval is degenerate because every paired difference is zero.

The headline rates below are for one method, pooled over all 7 attacks. Each candidate is counted seven times. Denominator 5,208 = 744 × 7. They are not the clean-condition rates. The other two methods match these counts.

| Quantity | Value | Numerator | Denominator |
| --- | ---: | ---: | --- |
| Mean decision loss | 0.2533026113671275 | sum of decision losses | 5208 |
| Correct accept | 126 | 126 | 5208 |
| Correct reject | 586 | 586 | 5208 |
| False accept | 110 | 110 | 5208 |
| False reject | 415 | 415 | 5208 |
| Uncertain | 3971 | 3971 | 5208 |
| Coverage | 0.23751920122887865 (23.75%) | 1237 classified | 5208 |
| Uncertainty | 0.7624807987711214 (76.25%) | 3971 | 5208 |
| Selective risk | 0.4244139046079224 (42.44%) | 525 errors | 1237 classified |
| False acceptance rate | 0.15804597701149425 (15.80%) | 110 | 696 classified negatives |
| False rejection rate | 0.767097966728281 (76.71%) | 415 | 541 classified positives |
| Execution failures | 0 | 0 | 5208 |

Clean condition only, one method, 744 candidates: decision loss 0.24327956989247312, coverage 169/744, uncertainty 575/744, selective risk 66/169, false acceptance 1/96, false rejection 65/73.

Pooled attack columns, one method, 744 candidates each. Team cost is 108.03258997621015 ms on every row. Execution failures are 0.

| Attack | Decision loss | CA | CR | FA | FR | Uncertain | Coverage | Selective risk | FAR | FRR |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| clean | 0.24327956989247312 | 8 | 95 | 1 | 65 | 575 | 169/744 | 66/169 | 1/96 | 65/73 |
| confidence inflation, model component | 0.24919354838709679 | 11 | 102 | 2 | 72 | 557 | 187/744 | 74/187 | 2/104 | 72/83 |
| confidence inflation, rule | 0.24327956989247312 | 8 | 95 | 1 | 65 | 575 | 169/744 | 66/169 | 1/96 | 65/73 |
| forced rejection, model component | 0.26129032258064516 | 0 | 104 | 0 | 83 | 557 | 187/744 | 83/187 | 0/104 | 83/83 |
| forced rejection, rule | 0.24327956989247312 | 8 | 95 | 1 | 65 | 575 | 169/744 | 66/169 | 1/96 | 65/73 |
| forced support, model component | 0.2895161290322581 | 82 | 1 | 103 | 1 | 557 | 187/744 | 104/187 | 103/104 | 1/83 |
| forced support, rule | 0.24327956989247312 | 9 | 94 | 2 | 64 | 575 | 169/744 | 66/169 | 2/96 | 64/73 |

GSM8K contributes 2,618 of the pooled rows (374 candidates × 7). Decision loss is 0 on 53, 0.2 on 2,517, and 1 on 48. Mean 0.21061879297173414. Coverage 101/2618. Uncertainty 2517/2618. Clean GSM8K classifies 11 of 374 candidates. HotpotQA contributes 2,590 rows (370 × 7). Decision loss is 0 on 659, 0.2 on 1,454, and 1 on 477. Mean 0.29644787644787646. Coverage 1136/2590. Uncertainty 1454/2590. HotpotQA forced support of the model component classifies 168 of 370 candidates and accepts every one of them: 74 correct accepts and 94 false accepts.

The benchmark-by-attack table with the remaining cell counts is in `experiment3_empirical_results.md`. Those counts were recomputed from `results.json` and match `metrics.json`.

The game value, worst attack column of decision loss plus the resource penalty, is 0.29096372230211043 for every method. That is not the pooled mean 0.2533026113671275. The penalty on the selected team is 0.0014475932698523478.

## D. Policy-selection diagnosis

`enumerate_strategies` admits 14 strategies: 7 teams × 2 aggregations. Singletons are rejected by the floor of 2. Teams that contain both confidence and evidence, including the full roster, are rejected because their frozen cost exceeds the budget. Confidence + rule, confidence + semantic, and confidence + rule + semantic remain feasible.

Evidence + rule is the unique best team under the configured objective. Its worst augmented loss is 0.29096372230211043. The next team, rule + semantic, is 0.2979886195303902. `full_minimax` has two optimal strategies, both on evidence + rule, one for each aggregation. The solver returned probability 1 on the reputation-weighted strategy. Each restricted method has one optimal strategy, and each independently selects the same verifiers.

`log_odds_weight(0.5)` is 0, and dependency reliability at reputation 0.5 is 0. Both aggregations therefore fall back to unweighted averages. On a team with one informative verifier per component, those averages are the same function. On the stored reports they also agreed on every larger feasible team: 0 decision disagreements in 5,208 cells per team, and identical attack-wise loss vectors.

A synthetic control with semantic SUPPORT 1, evidence SUPPORT 1, and rule REJECT 0.2 makes reputation-weighted aggregation return `passed` (score 0.6) and dependency-group aggregation return `uncertain` (score 0.4). That control shows the rules can separate. It is not an empirical separation.

## E. Verifier diagnosis

All 744 stored calls returned `ok` for all four verifiers.

| Verifier | GSM8K (374) | HotpotQA (370) |
| --- | --- | --- |
| semantic | UNSURE 374, reason `no_context` | SUPPORT 150, UNSURE 143, REJECT 77 |
| evidence | UNSURE 357, REJECT 17, SUPPORT 0 | UNSURE 202, REJECT 155, SUPPORT 13 |
| rule | UNSURE 372, REJECT 2 | UNSURE 370 |
| confidence | UNSURE 306, REJECT 46, SUPPORT 22 | UNSURE 252, REJECT 69, SUPPORT 49 |

GSM8K semantic abstains because those Development inputs have an empty evidence context. Rule abstains on 742 of 744 candidates, so the selected evidence + rule team usually has only the evidence vote. That is why GSM8K coverage is low and why most rule-targeted attacks match clean.

HotpotQA evidence is the useful clean signal: 155 REJECT and 13 SUPPORT. Forced support of the model component changes those 168 directional HotpotQA evidence reports to SUPPORT and leaves 202 UNSURE. The reject votes disappear, and the HotpotQA cell accepts every classified candidate. Confidence is UNSURE on 558 of 744 candidates and is the slow verifier. Mean recorded confidence time is 13.247461921640073 seconds. It was not part of the selected team.

These patterns are properties of the current verifier implementations and inputs. They are not a general ranking of verifier families.

## F. Resource analysis

Recorded mean milliseconds on this run, against the frozen means used for feasibility:

| Verifier | Recorded ms | Frozen ms |
| --- | ---: | ---: |
| confidence | 13247.461921640073 | 14925.820978323463 |
| evidence | 209.85769489201903 | 107.93551665459138 |
| rule | 0.0422251338726886 | 0.09707332161876063 |
| semantic | 29.967247043469964 | 70.4728633359385 |

The sum of the recorded means is under the budget. The sum of the frozen means is over it. A budget applied to this run's wall times would have admitted confidence + evidence and the full roster. The experiment did not substitute those times.

The selected budget is the frozen cost of confidence + semantic + rule, the cheapest size-3 team that contains confidence. It is a boundary taken from the configuration grid, not an optimized operating point. Confidence is absent from the solved team because evidence + rule has the lower worst-case objective, including at a zero penalty. Confidence-bearing teams that remain feasible carry a penalty of about 0.200 and a higher worst-case loss.

On the stored decision losses, a zero penalty and the moderate coefficient `6.699798968862647e-05` keep evidence + rule. The high coefficient `0.0028379718168483666`, equal to 0.2 divided by the frozen semantic mean, would switch the optimum to rule + semantic. That high-coefficient result is a counterfactual on the stored losses. It was not collected as a new experiment.

`experiment3_resource_sensitivity.md` is a synthetic fixture and a configuration grid. It recommended that a coefficient not be derived from that file. It is not empirical evidence that a positive coefficient always selects the cheapest team. On these Development reports, the selected coefficient does not.

## G. Scientific interpretation

The Development experiment establishes four facts.

1. Under this prior, budget, loss, and these reports, changing the aggregation restriction does not change the selected team or any decision.
2. The joint game still separates teams. Evidence + rule is the unique minimax team. Six other feasible teams have higher worst-case loss.
3. Uncertainty dominates, especially on GSM8K, because the selected verifiers usually abstain there.
4. Forced support of the declared model component is the worst column, and on HotpotQA it removes the evidence reject votes.

Identical method outcomes are a valid negative finding about aggregation separation on this configuration. They are not a proof that the methods are equivalent. The bootstrap interval is [0, 0] because the paired sample contains only zeros. A confidence interval around a constant zero does not test equivalence under other priors, budgets, or report distributions. The synthetic control is the existence proof that the two aggregations can disagree. It was not observed here.

The original "does joint selection improve validation" question remains open. This run has no greedy, uniform, or fixed-team comparator. It has no held-out Development split and no Final Test. It does not show that dependency structure was measured.

## H. Limitations

- Development rows were used both to fit the policies and to score them.
- Final Test labels were not accessed. `final_test_authorized` remains false.
- `SYNTHETIC_INCORRECT` candidates are generated negatives. No human-verified incorrect candidate is in the approved population.
- Reputation is a cold start. Approved historical observations are zero.
- Dependency groups are structural assumptions. `empirical_evidence` is `none`.
- Model-weight snapshot hashes remain `UNKNOWN`.
- Independent human approval and other contributors' signatures were not obtained. No signature was fabricated. Automated integrity checks replaced those prerequisites for this run.
- The participant floor of 2 and the uniform capability label are configuration assumptions.
- The coefficient and budget were selected, not empirically optimized.
- Feasibility used frozen means, not this run's wall times.
- No empirical separation among the three aggregation methods was observed.
- GSM8K semantic inputs have empty context, and the rule verifier abstains on almost every candidate. Rates on GSM8K cells that classify 11 or 19 of 374 candidates are unstable.
- Attacks corrupt stored reports. They do not demonstrate model or corpus compromise.
