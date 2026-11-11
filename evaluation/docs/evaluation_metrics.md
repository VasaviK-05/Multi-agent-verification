# Evaluation metric definitions

## Outcomes and denominator conventions

Let each evaluated candidate have gold status `accept`, `reject`, or, where the task supports it, `abstain/insufficient evidence`. The framework outcomes are definitive accept, definitive reject, abstain, or execution failure. The current baseline maps `passed` to accept, `failed` to reject, and `uncertain`/`unknown` to abstention. A failed execution is separate from an intentional abstention.

- **Correct acceptance:** gold accept and definitive accept.
- **Correct rejection:** gold reject and definitive reject.
- **False acceptance:** gold reject and definitive accept. Report both count and rate over all gold-reject candidates; abstentions remain in that denominator.
- **False rejection:** gold accept and definitive reject. Report count and rate over all gold-accept candidates; abstentions remain in that denominator.
- **Coverage:** definitive decisions divided by eligible candidate attempts. State whether failed executions are included in the denominator; preferred operational coverage includes all scheduled eligible attempts so failures reduce coverage.
- **Abstention rate:** intentional abstentions divided by eligible attempts, reported separately from failures.
- **Selective risk:** loss/error among definitive decisions only. Report its denominator. If decision coverage is zero, selective risk is undefined (`NA`), not zero.
- **Validation loss:** expected per-example loss under the approved loss matrix, averaged over eligible groups/examples as declared. The project currently has no declared research loss matrix or penalty values. Do not substitute accuracy, verifier score, or the baseline `prediction_correct` indicator without team approval.
- **Estimated attempt cost:** sum of the predeclared cost for each verifier attempt, including retries/fallbacks if charged, per evaluated example. The baseline records attempt counts and wall-clock latency but no approved common cost schedule. Report latency separately from modeled cost.
- **Execution failure rate:** scheduled attempts that terminate in a technical/runtime failure divided by scheduled eligible attempts. Keep the exception record and reason.
- **Unresolved coverage:** eligible examples without a resolvable accept/reject outcome, including intentional abstention and failure; report components separately so unresolved evidence is not confused with execution failure.

The current baseline `metrics.py` uses `passed`/`failed` as definitive, `uncertain`/`unknown` as abstention, and excludes abstentions from definitive binary precision/recall. Its `coverage` is definitive completed records divided by completed records; execution failures are summarized separately. Existing false-acceptance/rejection rates include abstained examples in gold-role denominators. These are implementation definitions, not a fully approved research loss.

## Mixed strategies and seeds

For a mixed policy with strategy probabilities (p_s), compute expected loss as Σ_s p_s L_s and expected cost/coverage components with the same probability weighting when outcomes are available for every pure strategy. If execution is sampled, use a predeclared seed set or repeated draws and report Monte Carlo uncertainty; never select the most favorable seed. A seed controls reproducibility, not a method-selection criterion. Prefer analytical expectation when pure-strategy outcomes can be evaluated without adaptive leakage.

## Paired uncertainty and related groups

Compare methods on the same held-out examples and resource condition. Calculate paired differences, resampling whole related-example groups with replacement; retain all candidate variants and related rows together in each draw. This preserves within-question dependence and prevents artificially narrow intervals from treating paired or paraphrased records as independent. Use a predeclared interval level and number of bootstrap draws; the project has not set these values, so team approval is required. Report group count as the effective resampling unit count.

## Failures, abstentions, and zero coverage

An abstention is a valid system outcome indicating insufficient confidence/evidence or a policy choice not to decide. An execution failure means the intended computation did not complete. Report both and state the primary loss treatment for each. Do not score abstention as rejection. Do not silently remove failures from operational coverage or cost. When there are no definitive decisions, report selective risk as undefined and show zero coverage, counts, and unresolved rate.

## Primary outcome and its implementation

The protocol's primary outcome is worst-case expected validation loss across the declared scenarios (`research_objective.md`). In code, `app/game/research/comparison.py:_score` reports `worst_case_expected_loss = max over attacks of Metrics.mean_loss`. `mean_loss` includes `resource_weight × estimated cost`; `Metrics.validation_loss(loss)` excludes it. Report which one is primary once the team decides; until then, report both from the same per-attack `Metrics`.

## Which metrics research_v1 can support

Recomputed from research_v1 labels by `person1_validation` (machine-readable copy in `experiment_contracts.json` → `estimability`). "After Attempts" means the metric becomes computable only once real verifier Attempts are recorded; currently there are 0.

| Partition:benchmark | Correct / incorrect / unresolved | False acceptance | False rejection | Coverage, abstention, selective risk | Loss, cost, worst case |
|---|---|---|---|---|---|
| History:GSM8K | 277 / 124 / 199 | after Attempts | after Attempts | after Attempts | blocked (loss weights, Person 2 costs, Attempts) |
| History:HotpotQA | 300 / 0 / 340 | **not estimable** (0 incorrect) | after Attempts | after Attempts | blocked |
| Development:GSM8K | 187 / 91 / 122 | after Attempts | after Attempts | after Attempts | blocked |
| Development:HotpotQA | 200 / 0 / 210 | **not estimable** (0 incorrect) | after Attempts | after Attempts | blocked |
| Final Test (provisional) | 2,638 / 0 / 0 (manifest aggregate) | **not estimable** (0 incorrect) | after authorization | after authorization | blocked |

Consequences:

- HotpotQA reputation from History can only reflect behaviour on correct candidates, so it cannot learn false-acceptance tendencies on that benchmark.
- Any pooled false-acceptance figure on research_v1 is GSM8K-only and must be labelled as such.
- Unresolved candidates are excluded from binary metrics and never counted as incorrect.

## Still requiring approval

Approve loss values, any scenario weights or worst-case aggregation, denominator treatment in the primary estimand, cost schedule, interval level/bootstrap draws, mixed-strategy evaluation method, and handling of missing labels/evidence before the confirmatory comparison.
