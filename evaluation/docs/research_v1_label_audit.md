# research_v1 candidate label audit

Machine check performed 2026-11-11 by `person1_validation` over the reconciled and prepared research_v1 files. No labels were added, changed, or inferred. No human review is claimed (`independent_human_review` is false on all 2,050 records).

## Counts

| Partition | Benchmark | Candidates | Verified correct | Verified incorrect | Unresolved |
|---|---|---:|---:|---:|---:|
| History | GSM8K | 600 | 277 | 124 | 199 |
| History | HotpotQA | 640 | 300 | 0 | 340 |
| Development | GSM8K | 400 | 187 | 91 | 122 |
| Development | HotpotQA | 410 | 200 | 0 | 210 |
| **Total** | | **2,050** | **964** | **215** | **871** |

No status outside the three declared values occurs.

## Label method by candidate type

| Benchmark | Generation method | Records | Possible labels under the declared method |
|---|---|---:|---|
| GSM8K | `benchmark_gold` | 500 | `verified_correct` if worked-solution replay confirms; otherwise unresolved (36 unresolved) |
| GSM8K | `synthetic_numeric_perturbation` | 500 | `verified_incorrect` only under the narrow gold+1 discrete-count rule (215); otherwise unresolved (285) |
| HotpotQA | `benchmark_gold` | 500 | `verified_correct` (benchmark answer plus mapped supporting-fact context) |
| HotpotQA | `synthetic_cross_example_answer` | 500 | always unresolved; never automatically incorrect |
| HotpotQA | `explicit_negation_of_context_supported_benchmark_answer` | 50 | unresolved (demoted from prior status) |

## Consistency checks (all PASS)

| Check | Result |
|---|---|
| Binary candidates without a `validation_method` | 0 |
| Unresolved candidates without an `unresolved_reason` | 0 |
| Prepared rows whose `answer_is_correct` disagrees with `correctness_status` | 0 |
| Prepared rows that are not binary-labelled | 0 |
| Binary candidates missing from the prepared files | 0 |
| Excluded rows that are not unresolved / that carry a binary label | 0 / 0 |
| Prepared totals | History 701, Development 478 (1,179) |
| Excluded unresolved | 871 |

## Unresolved reasons (871)

| Benchmark / method | Reason (abbreviated) | Count |
|---|---|---:|
| HotpotQA cross-example | requires (independent) question-conditioned factual adjudication | 500 |
| GSM8K perturbation | requires question-semantic review unless the narrow rule applies / complete arithmetic evidence | 285 |
| HotpotQA negation | negation and string match do not establish target-question correctness | 50 |
| GSM8K gold | worked-solution replay did not establish the result | 27 |
| GSM8K gold | requires independent semantic review or complete arithmetic evidence | 9 |

The queue for independent review is `unresolved_review_queue.jsonl` (see `research_v1_development_roster.md`). Every row is `PENDING_INDEPENDENT_HUMAN_REVIEW` with no assigned label.

## Findings

- HotpotQA has no verified incorrect candidate in any partition. False acceptance is not estimable for HotpotQA.
- GSM8K negatives come from one narrow synthetic rule, so GSM8K false-acceptance estimates describe only that construction.
- 36 GSM8K gold answers are unresolved. That is a property of the conservative replay rule, not evidence that the gold answers are wrong.
- Label provenance is automated and deterministic. Scientific acceptance of automated labels is pending (`person1_approval_checklist.md`).
