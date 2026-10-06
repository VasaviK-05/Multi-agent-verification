# Difficulty, selection, reputation, and the decision score

This note states the formulas in the code, then separates three things: published foundations the formulas use, design choices made for this prototype, and constants that still need calibration. It does not claim a new method, a patent, or a measured gain over another system.

## What the code computes

### Difficulty and domain

Whole tokens are the lower-cased question with punctuation replaced by spaces. A token matches a cue when it equals the cue or the cue plus a trailing `s`. That is not a stemmer.

```
length_score   = min(word_count / 40, 1)
clause_score   = min((question_marks + semicolons + " and " + " also " + " additionally ") / 3, 1)
reasoning_score = min(reasoning_cue_hits / 2, 1)
domain_score   = min(domain_cue_hits / 3, 1)

raw = 0.30 * length_score + 0.25 * clause_score + 0.25 * reasoning_score + 0.20 * domain_score
difficulty_score = round(clip(raw, 0, 1), 2)
```

`word_count` is `question.split()`, so punctuation can stay attached to a word. Cue hits use the token set instead.

```
difficulty_score < 0.35        → easy
0.35 ≤ difficulty_score < 0.65 → medium
difficulty_score ≥ 0.65        → hard
```

Domain is the cue list with the unique highest hit count. Zero hits, or a tie, yield `general`.

`difficulty_score` is a rank in [0, 1]. It is not a probability that the question is hard.

### How many verifiers, and which ones

`R(v, d)` is the reputation of verifier `v` in domain `d`, in [0, 1]. `cost(v)` and `latency(v)` are the explicit estimates in the selector table, also in [0, 1]. They are not measured seconds. The default confidence profile is cost 0.9 and latency 1.0: provisional estimates for five default sampling generations, not measured timings. Explicit supplied judgments can be cheaper; custom profiles override the defaults. Resource weights and profile fields must be finite non-boolean numbers in [0, 1]. Ranges must be positive integer pairs with minimum <= maximum. Difficulty scores must be finite non-boolean numbers; finite out-of-range scores retain clamping. Registered verifier names must be unique, non-blank strings without surrounding whitespace. Caller configurations are copied, including nested profiles and range pairs.

```
U(v, d) = R(v, d) - 0.15 * cost(v) - 0.10 * latency(v)
U(v, d, q) = U(v, d) + 0.20 * S(v, q)
```

`utility(name, domain)` still returns `U(v, d)`. Ranking uses `U(v, d, q)`. `S(v, q)` is 0 when `verification_types` is empty, so that ranking matches `U(v, d)`. Otherwise each unique label has an equal share. Labels mapped below add that share to one verifier. A repeated label is counted once. An unknown label matches nobody and still uses a share, so duplicates and longer lists cannot push a bonus above 1. `S` is a hint in [0, 1], not a measured chance that the verifier applies.

| Verification type | Suitability hint |
| --- | --- |
| `arithmetic`, `logical_rule` | `rule` |
| `direct_fact`, `evidence_retrieval` | `evidence` |
| `semantic_comparison` | `semantic` |
| `consistency` | `confidence` |

The hint is not coverage. The rule verifier only matches a few deterministic patterns and otherwise abstains as unsupported. Semantic comparison abstains without reference context. Consistency uses supplied judgments when available; otherwise the default provider samples five generations and can abstain when sampling fails or judgments are not directional. Evidence can abstain when retrieval or NLI is not directional. `iter_ranked` still yields every registered candidate so an abstention can fall through to the next one. Reputation stays `R(v, analysis.domain)`. Domain candidates are not mixed into that reputation.

The selected list is the highest `U(v, d, q)` first. Equal utilities keep registration order. For the built-in verifiers that order is semantic, evidence, rule, confidence. Injected verifiers keep the order in which they were supplied. `explain_ranking` reports reputation, the resource penalty, the suitability contribution, and the final utility without constructing a default verifier.

The count uses where the score sits inside its band, clipped to [0, 1]:

```
easy:   (score - 0)    / 0.35
medium: (score - 0.35) / 0.30
hard:   (score - 0.65) / 0.35

count = min_n + floor((max_n - min_n) * position + 1/2)
```

Default ranges are easy (2, 2), medium (2, 3), hard (3, 4). Valid custom ranges remain supported. Two easy votes do not guarantee factual coverage or resolve disagreement; coverage and zero-confidence stopping counts require separate integration safeguards. `floor(x + 1/2)` is half-up on this non-negative number, so a score at the bottom of a band selects `min_n` and a score at the top selects `max_n`. `int(span * score)` did not: with a span of 1 it stayed on `min_n` for every score below 1, including scores that the band already calls hard.

At cold start every `R` is 0.5. When `verification_types` is empty, ranking follows the resource estimates, and the default estimates put `rule` first. When `verification_types` is not empty, suitability also affects that order.

### Reputation

For each verifier and domain, successes `r` and failures `s` are integer counts. With the default prior:

```
alpha = 1 + r
beta  = 1 + s
R     = alpha / (alpha + beta) = (r + 1) / (r + s + 2)
variance = alpha * beta / ((alpha + beta)^2 * (alpha + beta + 1))
```

`r` and `s` are stored. The observation count is `r + s`. It is not computed by subtracting the prior from alpha and beta. Cold start is `r = s = 0`, so `R = 0.5`, and only for that pair. Another domain is not copied. `R` and the variance are a Beta–Bernoulli belief about the verifier. They are not the probability that an answer is correct.

A later external boolean updates one pair:

```
verifier_correct = (verifier_passed == answer_is_correct)
verifier_correct → r += 1
otherwise        → s += 1
```

Rejecting an incorrect answer is a success. `answer_is_correct` has to be a boolean from outside the system. The status string from `decide`, a consensus, a confidence score, and a reference-answer string are not labels. `validate` does not call the update. Abstentions and verifiers that did not run add no observation.

`update_reputation` and `update_from_ground_truth` have no validation identity, so a repeated call is another observation. On those methods the source tag must be the string `ground_truth`. Any other tag is refused. The tag is caller metadata, not authentication and not proof that the boolean is true.

`record_feedback` binds the boolean, the original domain, and the executed votes to a validation id. The same delivery again does nothing. A different label or vote list for an id that is already stored is rejected and does not change counts. Changing a stored label needs a future correction workflow. Two validations of the same question text are different ids. The orchestrator stores each run's domain with that id. Feedback for an earlier run does not use the domain of a later run. See `docs/reputation_integration.md`.

### Decision score

Every supplied result is validated before exclusion. Abstentions and results
with normalized vote confidence zero are excluded from the scoring pool,
both denominators, and the choice between log-odds aggregation and fallback.
Zero-confidence directions remain in `DecisionDetail.votes` with their actual
`passed` flag, `abstained=False`, and zero confidence and contribution. They
still receive directional reputation observations from external labels.
A factual rule rejection with stored score zero has normalized confidence
one and remains eligible.

Scoring results use normalized confidence `s` in (0, 1] and vote `v` = `+1` on pass and `-1` on reject. `p` is that verifier's reputation in the analyzer's domain, clamped into `(eps, 1 - eps)`. The default `eps` is `1e-6`. An `eps` so small that `1 - eps` rounds to `1` is rejected before the division:

```
w    = log(p / (1 - p))
mass = s * v
```

| Reputation | Weight | Effect on the vote |
| --- | --- | --- |
| `p > 0.5` | `w > 0` | follow the vote |
| `p = 0.5` | `w = 0` | ignore it if any other weight is nonzero |
| `p < 0.5` | `w < 0` | invert the vote |

```
score = sum(w_i * mass_i) / sum(|w_i|)    when some |w_i| > 0
score = sum(mass_i) / n                   when every w_i is 0
```

These sums and `n` range over the scoring pool only. In log-odds mode,
zero-weight results are ignored. Fallback also applies to experienced
verifiers whose balanced counts or six-decimal rounding yield reputation
0.5; it does not depend on the observation count.

Thus support confidence 0.9 plus rejection confidence zero scores 0.9,
at the prior or with equal nonzero reputations. A learned weight on only
the zero-confidence result cannot suppress the untouched support's fallback.
If no scoring results remain, status is `uncertain` and score is zero:
`aggregation="abstentions"` means all results abstained;
`aggregation="zero_confidence"` means at least one result was directional
but all directional confidences were zero, possibly mixed with abstentions.

The absolute value in the denominator is required. Dividing by `sum(w_i)` would flip the sign back and undo inversion from `p < 0.5`.

The raw score is clipped to [-1, 1]. Status uses that unrounded value and a threshold that is finite and strictly between 0 and 1. The default is 0.55. `decide` returns the raw score rounded to 6 decimals, so the displayed score can equal the threshold after the raw score has already crossed it. Status still follows the raw comparison.

```
raw >  threshold → passed
raw < -threshold → failed
otherwise        → uncertain
```

The abstention band is symmetric about 0. A positive cut pair such as "above 0.55 pass, below 0.45 fail" would mark a tie at 0 as a failure, because that pair assumes a score centered near one half. This score is centered at 0.

`p` is the six-decimal reputation from one batch read of the requested verifier/domain pairs. That read does not update reputation. Weights use those rounded means, the same values `get_reputation` returns.

No results → `unknown` and score `0`. That zero means "no score". An `uncertain` zero means the weighted votes cancelled, every verifier abstained, or the score landed in the middle band. Neither number is a probability of a correct answer.

### What each verifier's score means

The legacy abstention cues below apply only when `metadata.decision` is
absent. Explicit decisions use the contract in the next section; the
existing score-to-confidence scales still apply to directional votes.

| Verifier | Raw `score` | How the decision reads it |
| --- | --- | --- |
| rule, `metadata.rule` set and not `unsupported` | `1` if the rule passed, `0` if it failed | Deterministic vote, and only when the verifier name is `rule`. Confidence is 1, so a failure is mass `-1`, not `0`. The same metadata on another verifier does not grant confidence 1. |
| rule, `metadata.rule == "unsupported"` | `0`, `passed` false | Abstention. Not evidence that the answer is wrong. |
| semantic, no reference context | `0`, `passed` false | Abstention. |
| semantic, with context | cosine similarity | Confidence of the `passed` vote. |
| evidence, nothing retrieved | `0`, `passed` false | Abstention. |
| evidence, NLI label `neutral` | confidence in that label | Abstention. Neutral is not a contradiction. |
| evidence, entailment or contradiction | NLI confidence of that label | Confidence of the pass or reject vote. |
| confidence, no judgments | `0`, `passed` false | Abstention. |
| confidence, tied highest judgment count | agreement fraction stored by the verifier | Abstention, in either judgment order. Not a pass or a reject. |
| confidence, unique majority `support` or `reject` | agreement fraction | Confidence of that vote. |
| any verifier, score outside [0, 1] or non-finite | not a usable vote | Rejected. Not clipped into a confidence. |

### Explicit verifier decisions

When `metadata.decision` is present, vote normalization requires exactly
`SUPPORT`, `REJECT`, or `UNSURE`. This contract takes precedence over legacy
reasoning phrases, rule labels, NLI labels, and judgment metadata.
`SUPPORT` requires `passed=True`; `REJECT` requires `passed=False`.
Invalid values (including null) or contradictory directional fields raise
`ValueError` before aggregation or reputation learning changes state.

`UNSURE` always abstains, with zero vote confidence, no signed mass, no
early-stop eligibility, and no reputation observation. A successful
structural check may retain `passed=True` and its stored score while
abstaining from factual correctness. These reporting fields are preserved.
Absent decisions retain the legacy interpretation, including abstention
for structural/range rule outputs. A supported factual rule rejection with
stored score zero remains a deterministic rejection with confidence one.
This does not change score calibration, weights, thresholds, or stopping
policy. The current orchestrator completes the selector target without
calling early termination; restoring that wiring is deferred work.

### Fallback when a verifier abstains

Candidates are tried in utility order, not only the initial difficulty subset. Each abstention is kept on the response with `metadata.pipeline_role = "abstention"` and a `pipeline_note` saying it was not a vote. The current orchestrator runs until there are enough informative votes for the difficulty target or the list is exhausted. The standalone early-termination engine ignores abstentions, including `unsupported`. Reputation updates skip them too.

`+1` means every result actually included in aggregation contributed a
full-confidence pass after negative-weight inversion, if applicable.
`-1` means the same for reject. Abstentions, zero-confidence directions,
and zero-weight directions in log-odds mode do not establish unanimity.

### Early stopping

This describes the standalone engine. The current orchestrator does not
call it. Repair 7 must wire the shared engine and selector minimum, satisfy
requested factual capabilities before using an approved stop, and preserve
the exact accepted decision snapshot. Standalone approval does not establish
factual coverage or independence between verifiers with different names.

Stopping calls `DecisionEngine.decide_detailed` once on the current prefix
and analyzer domain. All supplied results are validated before exclusion.
The immutable detail supplies normalized confidence, original directions,
weights, effective contributions, status, and raw score. No accepted decision
is silently recomputed. Numerical aggregation and reputation learning remain
unchanged.

Abstentions, normalized zero-confidence directions, and structural/range/format-only
rule outputs do not count toward the minimum, agreement, or confidence average.
For `verifier_name == "rule"`, `metadata.rule_kind == "structural"` identifies
those outputs; `"factual"` retains eligibility, including arithmetic and the
explicit `format_validity` question. Results with absent/null kind use only
the existing legacy structural labels: `probability_range`, `percentage_range`,
`email_regex`, `url_regex`, `date_regex`, `id_regex`, and `json_structure`.
The same metadata on another verifier does not classify it as a structural rule.
A factual arithmetic rejection with stored score zero has normalized confidence
one and remains eligible. Structural rejections retain their reporting,
numerical contribution, and learning behavior despite exclusion from stopping.

Default contributor minima match the selector: easy 2, medium 2, hard 3.
Easy and medium enforce a floor of two even if a caller supplies minimum one;
a larger explicit minimum remains binding. Hard questions never stop early.
Boolean, nonnumeric, and nonfinite difficulty scores are rejected. Finite
scores retain their existing behavior; stopping thresholds depend on the band.

In equal-weight fallback, effective direction is the original direction.
In log-odds mode, zero-weight directions do not count as contributors and
negative weights invert effective direction. Contributors must effectively
agree, and the decision must already be `passed` or `failed` under the engine's
strict status threshold. Additionally, any original-direction disagreement
among validated, positive-confidence, non-abstaining, nonstructural results
vetoes stopping, including zero-weight dissent or dissent that inversion
would turn into effective agreement. This is a conservative stopping policy,
not a change to numerical weights. It does not establish calibrated correctness.

The existing inclusive cuts use unrounded values:

```
easy:   mean contributor confidence ≥ 0.75 and |raw score| ≥ 0.60
medium: mean contributor confidence ≥ 0.80 and |raw score| ≥ 0.70
```

Those cuts remain configurable finite values in [0, 1]. On approval, the
returned `decision` is the exact immutable detail used for the assessment;
later feedback does not rewrite it. Reaching a selector target or exhausting
candidates is not an approved early stop. There is no weaker target-count
stopping path in this engine. Coverage-unavailable and exhaustion handling
remain orchestration work for Repair 7.

## Published foundations

These are standard formulas. Using them here is not a claim that the combination is new.

- **Beta posterior mean.** With a uniform Beta(1, 1) prior, the mean of a Bernoulli success rate after `r` successes and `s` failures is `(r + 1) / (r + s + 2)`. Jøsang and Ismail's Beta reputation system uses that mean as a reputation (Jøsang, A. and Ismail, R., 2002, "The Beta Reputation System", *Proceedings of the 15th Bled Electronic Commerce Conference*). The code stores the same mean per verifier and domain. It does not implement their later discounting of old feedback.
- **Bernoulli log likelihood ratio.** `log(p / (1 - p))` is the weight of evidence for an expert who is correct with probability `p` (Good, I. J., 1950, *Probability and the Weighing of Evidence*). At `p = 0.5` the weight is 0. Below `0.5` it is negative, which reverses the vote. The code follows that sign. It does not turn the weight into a calibrated probability.

## Design choices

These are local choices. They are not the published procedures above, and they are not claimed as a contribution.

- The difficulty features, the trailing-`s` token rule, rounding the score to two decimals before the band cut, and the three named domains.
- A linear penalty on hand-written cost and latency estimates, plus an uncalibrated suitability bonus from `verification_types`, and running the highest utility first.
- Mapping the in-band score position onto a `(min, max)` count with half-up rounding.
- Reading a supported rule's 0/1 score as a deterministic vote (confidence 1), and treating unsupported rules, missing semantic context, non-directional evidence, and missing confidence judgments as abstentions.
- Multiplying the log-odds weight by that confidence, then abstaining when the unrounded signed score is inside [-threshold, threshold]. The default threshold is 0.55. The returned score is rounded to 6 decimals after that comparison.
- After an abstention, consulting the next verifier in utility order and recording why in `pipeline_note`.
- On an all-zero weight vector, using the equal-weight mean of `confidence * vote` instead of abstaining immediately. Verifiers with weight 0 are ignored when any other weight is nonzero.
- Excluding normalized zero-confidence results from scoring without changing their directional reporting or reputation learning. The aggregation-mode choice uses only positive-confidence, non-abstaining results.
- Not folding the cost estimate into the decision score a second time. Cost affects who is selected.
- Stopping early only when contributing directions agree, confidence and absolute raw score clear the band cuts, and `decide_detailed` is already `passed` or `failed`. Hard questions never stop early. This is not Wald's sequential probability ratio test (Wald, A., 1947, *Sequential Analysis*), which is not implemented.
- The Weighted Majority algorithm's multiplicative update (Littlestone, N. and Warmuth, M. K., 1994, *Information and Computation*) is not implemented. Reputation moves only by Beta counts from external labels.

Sparse-data dominance and inversion remain unchanged: one correct observation
can give a verifier sole numerical influence over untouched opposing votes;
one incorrect observation can invert its vote. Normalization cancels weight
magnitude when only one nonzero weight remains. Observation counts and
posterior variance do not temper these weights. Regression tests describe
these current policies, not empirical evidence of reliability. Similarity,
NLI probabilities, and agreement fractions are uncalibrated confidence scales,
not interchangeable probabilities of answer correctness.

## Values that still need calibration

Nothing in this table was fitted on a labeled set in this repository.

| Value | Where it lives |
| --- | --- |
| Feature weights 0.30, 0.25, 0.25, 0.20 | `app/analysis/heuristic.py` |
| Divisors 40, 3, 2, 3 and score rounding to 2 decimals | `app/analysis/heuristic.py` |
| Band cuts 0.35 and 0.65 | `app/analysis/heuristic.py` |
| Keyword lists and the trailing-`s` rule | `app/analysis/heuristic.py` |
| `lambda_cost = 0.15`, `lambda_latency = 0.10`, `lambda_suitability = 0.20` | `app/selection/verifier_selector.py` |
| Cost and latency estimates for the four verifiers | same |
| Verification-type suitability map | same |
| Count ranges (1, 2), (2, 3), (3, 4) | same |
| Beta prior `alpha = beta = 1` and the +1 update | `app/reputation/reputation_manager.py` |
| Decision abstention margin 0.55, reputation clamp `1e-6` | `app/decision/decision_engine.py` |
| Early-stop minima and the 0.75 / 0.60 and 0.80 / 0.70 cuts | `app/decision/early_termination.py` |

## What a comparison requires

`app/benchmark/offline_benchmark.py` runs only on examples the caller provides. Each example needs a question, an answer, and a boolean label. The report gives, for adaptive selection, unweighted majority, and running every verifier:

- accuracy on the examples that were not abstentions
- coverage and abstention count
- verifier calls
- wall-clock milliseconds measured around `verify`

Abstentions are left out of the accuracy numerator and denominator so coverage has to be read with accuracy. There is no checked-in dataset and no checked-in scoreboard. A command such as `python -m app.benchmark.offline_benchmark --data examples.jsonl` prints the counts for that file. It does not decide which method is better.
