# Reputation integration

Reputation is an in-memory Beta–Bernoulli table in `ReputationManager`. Selector and decision code read `get_reputation`, which is the posterior mean rounded to 6 decimals. Learning happens only after validation, from an external boolean. `validate` does not learn. A verifier succeeds when its pass/reject vote matches that boolean. Rejecting an incorrect answer is a success.

## What is stored

`export_state` returns schema version `1` with:

- `prior_alpha` and `prior_beta`, finite and positive
- `pairs`: `verifier_name`, `domain`, `successes`, `failures`
- `feedback`: `validation_id`, `domain`, `answer_is_correct`, `source`, and `votes`

Each vote has `verifier_name`, `passed`, and `abstained`. `successes` and `failures` are non-negative integers. The observation count is their sum. Alpha and beta are `prior + successes` and `prior + failures`. The posterior variance is

```text
alpha * beta / ((alpha + beta)^2 * (alpha + beta + 1))
```

That variance, and the mean, are not calibrated answer confidence.

`restore_state` checks the whole document before it replaces the live tables. A malformed, non-finite, or inconsistent document leaves the current manager unchanged. Counts must be at least the observations implied by the feedback records. Extra counts are allowed because `update_reputation` and `update_from_ground_truth` have no validation id and therefore no feedback row. Those legacy methods apply every call again. `record_feedback` does not: the same id and payload is a no-op, and a different payload for a stored id is rejected. A label correction is a future workflow. `source` is stored as caller metadata. It does not authenticate the boolean.

Export and restore are not a database write. Nothing in this module connects to PostgreSQL.

## Orchestrator feedback

Each `validate` call keeps a `validation_id`, the analyzed domain, and a deep copy of the executed results. The response still returns `results`, `final_status`, and `final_score`, and adds `validation_id` and `domain`. The response objects are not the stored snapshot. `validation_context` returns another deep copy. Changing `passed`, `verifier_name`, or nested metadata on the response or on a returned context does not change the snapshot.

`record_feedback` for that id learns from the snapshot only when the supplied votes still match it. A changed vote is rejected and does not learn. The preferred call passes `validation_id`. Omitting the id is accepted only when each result is the same object `validate` returned. The orchestrator retains those response objects and checks them with `is`. The integer id is only a slot. A slot that holds a different object does not match, even when the votes are equal. A newly constructed list with the same votes is not that call. Two runs with the same votes stay distinct because the binding is object identity, not the vote tuple. Results from two runs in one call are rejected.

`validation_context` returns another deep copy of the snapshot. It does not return the retained response objects. Those retained objects and the validation contexts are not evicted. Memory grows with every validation for the life of the process. Dropping a context or a retained result would make delayed feedback and replay protection fail for that id.

An explicit domain with no bound result objects uses `record_unscoped_ground_truth`. That path has no validation id and no replay protection. Matching votes do not promote it into the bound path.

The contexts live in the orchestrator process. They do not survive a restart. The reputation manager lock makes one process's reads and updates atomic with each other. It is not multi-process safety and it is not a database transaction.

## Benchmark

Adaptive feedback uses the validation id, after the prediction. All-verifiers feedback also runs after `decide`. It skips abstentions and counts only observations that were applied. The two methods do not share a reputation table. All-verifiers feedback is unscoped, so running the same example twice counts twice.

`schema_version` must be the integer `1`. Booleans, floats, and strings are rejected. A rejected restore leaves the previous priors, counts, and feedback in place.

Posterior mean and variance use a ratio form of the Beta formulas so large and tiny finite priors do not overflow the sums. A prior or a restored count that cannot be converted to a finite float exactly is rejected before the live tables change. Legacy updates, unscoped updates, and feedback batches use that same check on the proposed counts before they commit. The check runs inside the process lock. If any pair in the proposal cannot be represented, the call raises and leaves every count and every feedback record unchanged. A failed batch does not store its validation ids.

## PostgreSQL is not wired

No migration in this repository creates the reputation tables. `app/database/models.py` has a `DomainReputationRecord` with `verifier_name`, `domain`, a single `reputation` float, and `updated_at`. It does not store priors, successes, failures, variance, or feedback votes. `FeedbackRecord` stores `validation_id`, `is_correct`, an optional ground-truth string, and a comment. It does not store the executed votes or a deduplication payload. `ValidationRepository` methods are no-ops.

`app/ground_truth/storage.py` inserts into `ground_truth_labels` (`ground_truth_id`, `validation_id`, `question_id`, `label`, `source`, `labeled_at`). `label` is a string. Reputation does not read that table and does not treat the string as a boolean label.

A later database adapter would need the export fields above, and it would also need durable storage for each validation id, its domain, and the executed-result snapshot. Neither the reputation tables nor those validation contexts are written to PostgreSQL. Automatic persistence is outstanding.
