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

`R(v, d)` is the reputation of verifier `v` in domain `d`, in [0, 1]. `cost(v)` and `latency(v)` are the explicit estimates in the selector table, also in [0, 1]. They are not measured seconds.

```
U(v, d) = R(v, d) - 0.15 * cost(v) - 0.10 * latency(v)
```

The selected list is the highest `U` first. Equal utilities keep the registration order semantic, evidence, rule, confidence.

The count uses where the score sits inside its band, clipped to [0, 1]:

```
easy:   (score - 0)    / 0.35
medium: (score - 0.35) / 0.30
hard:   (score - 0.65) / 0.35

count = min_n + floor((max_n - min_n) * position + 1/2)
```

Default ranges are easy (1, 2), medium (2, 3), hard (3, 4). `floor(x + 1/2)` is half-up on this non-negative number, so a score at the bottom of a band selects `min_n` and a score at the top selects `max_n`. `int(span * score)` did not: with a span of 1 it stayed on `min_n` for every score below 1, including scores that the band already calls hard.

At cold start every `R` is 0.5, so the order is the cost and latency order. The default estimates put `rule` first.

### Reputation

For each verifier and domain, with positive evidence `r` and negative evidence `s`:

```
alpha = 1 + r
beta  = 1 + s
R     = alpha / (alpha + beta) = (r + 1) / (r + s + 2)
```

Cold start is `r = s = 0`, so `R = 0.5`, and only for that pair. Another domain is not copied.

A later label updates one pair:

```
verifier_correct = (verifier_passed == answer_is_correct)
verifier_correct → r += 1
otherwise        → s += 1
```

`answer_is_correct` has to be a boolean from outside the system. The status string from `decide` is not accepted. A caller that sets the update source to anything other than `ground_truth` is rejected. `validate` does not call the update.

### Decision score

For each result, `s` is the verifier confidence in [0, 1] and `v` is `+1` if it passed and `-1` if it rejected. `p` is that verifier's reputation in the analyzer's domain, clamped into `(1e-6, 1 - 1e-6)`:

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

The absolute value in the denominator is required. Dividing by `sum(w_i)` would flip the sign back and undo inversion from `p < 0.5`.

The score is clipped to [-1, 1] and rounded to 6 decimals.

```
score >  0.55 → passed
score < -0.55 → failed
otherwise     → uncertain
```

The abstention band is symmetric about 0. A positive cut pair such as "above 0.55 pass, below 0.45 fail" would mark a tie at 0 as a failure, because that pair assumes a score centered near one half. This score is centered at 0.

No results → `unknown` and score `0`. That zero means "no score". An `uncertain` zero means the weighted votes cancelled or landed in the middle band. Neither number is a probability of a correct answer.

`+1` means every informative verifier contributed a full-confidence pass after inversion. `-1` means the same for reject.

### Early stopping

After each selected verifier, with `n` results, vote `v_i`, and confidence `s_i`:

```
agreement      = all votes equal
avg_confidence = mean(s_i)
margin         = abs(mean(s_i * v_i))
```

The minimum `n` is the selector's minimum for that difficulty (by default 1, 2, and 3). Below that minimum the run continues. A hard question continues after the minimum as well. Otherwise stop only if all votes agree and either:

```
easy band: avg_confidence ≥ 0.75 and margin ≥ 0.60
any non-hard band: avg_confidence ≥ 0.80 and margin ≥ 0.70
```

Disagreement continues. Confidence under those cuts continues. The remaining selected verifiers still run.

## Published foundations

These are standard formulas. Using them here is not a claim that the combination is new.

- **Beta posterior mean.** With a uniform Beta(1, 1) prior, the mean of a Bernoulli success rate after `r` successes and `s` failures is `(r + 1) / (r + s + 2)`. Jøsang and Ismail's Beta reputation system uses that mean as a reputation (Jøsang, A. and Ismail, R., 2002, "The Beta Reputation System", *Proceedings of the 15th Bled Electronic Commerce Conference*). The code stores the same mean per verifier and domain. It does not implement their later discounting of old feedback.
- **Bernoulli log likelihood ratio.** `log(p / (1 - p))` is the weight of evidence for an expert who is correct with probability `p` (Good, I. J., 1950, *Probability and the Weighing of Evidence*). At `p = 0.5` the weight is 0. Below `0.5` it is negative, which reverses the vote. The code follows that sign. It does not turn the weight into a calibrated probability.

## Design choices

These are local choices. They are not the published procedures above, and they are not claimed as a contribution.

- The difficulty features, the trailing-`s` token rule, rounding the score to two decimals before the band cut, and the three named domains.
- A linear penalty on hand-written cost and latency estimates, and running the highest utility first.
- Mapping the in-band score position onto a `(min, max)` count with half-up rounding.
- Multiplying the log-odds weight by the verifier's own confidence, then abstaining when the signed score is inside [-0.55, 0.55].
- On an all-zero weight vector, using the equal-weight mean of `confidence * vote` instead of abstaining immediately. Verifiers with weight 0 are ignored when any other weight is nonzero.
- Not folding the cost estimate into the decision score a second time. Cost affects who is selected.
- The early-stop rule on agreement, mean confidence, and margin, including "hard never stops early". This is not Wald's sequential probability ratio test (Wald, A., 1947, *Sequential Analysis*), which is not implemented.
- The Weighted Majority algorithm's multiplicative update (Littlestone, N. and Warmuth, M. K., 1994, *Information and Computation*) is not implemented. Reputation moves only by Beta counts from external labels.

## Values that still need calibration

Nothing in this table was fitted on a labeled set in this repository.

| Value | Where it lives |
| --- | --- |
| Feature weights 0.30, 0.25, 0.25, 0.20 | `app/analysis/question_analyzer.py` |
| Divisors 40, 3, 2, 3 and score rounding to 2 decimals | same |
| Band cuts 0.35 and 0.65 | same |
| Keyword lists and the trailing-`s` rule | same |
| `lambda_cost = 0.15`, `lambda_latency = 0.10` | `app/selection/verifier_selector.py` |
| Cost and latency estimates for the four verifiers | same |
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
