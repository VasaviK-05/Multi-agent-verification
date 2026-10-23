# Reputation integration

## Learning policy

ReputationManager holds independent Beta-Bernoulli counts for each verifier and
analyzed domain. With configured positive priors a0 and b0:

```
alpha = a0 + successes
beta = b0 + failures
mean = alpha / (alpha + beta)
variance = alpha * beta / ((alpha + beta)^2 * (alpha + beta + 1))
```

Defaults are Beta(1, 1). Observations are integers, not confidence-weighted
pseudo-counts. A returned directional vote succeeds exactly when its normalized
passed flag equals the supplied boolean answer-correctness label. Rejecting an
incorrect answer succeeds. Shared vote normalization skips abstentions, including
legacy neutral/tied judgments and unsupported/structural rules. Explicit decision
metadata follows the existing normalization contract. Agents that never returned
results do not learn. A supported arithmetic rejection with score zero has deterministic vote
confidence one. Other zero-confidence directions still learn under the existing
policy, even though they do not contribute to decision scoring or coverage.
Neither the posterior nor its variance is calibrated answer confidence.

Cold start means zero observations for that verifier/domain. Other domains do
not contribute. Reads expose detached statistics; selector/decision means are
rounded to six decimals. Stable ratio formulas avoid overflowing alpha + beta;
invalid/non-finite priors and unrepresentable counts reject before state changes.
No decay, exploration, or strategic incentives are implemented.

## Scoped feedback and provenance

Validation captures its ID, original domain, detached returned results, decision,
and execution audit. Response mutation and later requests cannot change those
stored votes. validation_context returns another detached copy. Feedback with a
bound ID must match the original votes and domain. Unknown IDs, changed votes,
and mixed result identities reject. Identity-based legacy binding still works.

The backward-compatible record_ground_truth entry point accepts keyword-only
source, defaulting to external_feedback. Existing positional callers still learn
from their supplied boolean; the default does not claim verified ground truth.
Benchmark adaptive and all-verifier callers explicitly pass benchmark_ground_truth,
after each prediction. Earlier examples may affect later examples; the methods
use separate managers. Automatic heuristic lookup still does not train reputation.

Source must be a non-blank string, validated before learning or saving. It is
metadata, not authentication or proof. For scoped events it is retained in the
manager's full-state feedback history. The existing identity policy includes ID,
domain, boolean label, normalized votes, and source. An exact replay learns zero
observations. Changing source alone conflicts; it cannot create another update.
Corrections still require a future explicit workflow.

Direct manager legacy methods retain their existing defaults and counting policy.
An explicit domain with unbound results still takes the unscoped path: each call
is a new observation, without replay identity or provenance history. Its optional
source is validated and passed by benchmark callers, but cannot be recovered from
aggregate counts. The orchestrator does not create retry work for unscoped calls.

## Learned, pending, and saved posteriors

Scoped feedback first applies atomically to the in-memory manager. Each changed
verifier/domain pair then enters a process-local dirty set. Empty and
abstention-only events retain their feedback identity but create no posterior
writes. An event may be learned even if the following posterior save raises.

The existing repository upserts absolute alpha/beta, committing each row
separately. Each successful save clears that dirty pair; a failed or ambiguous
save leaves it pending and its exception visible. An identical feedback retry
learns zero additional observations but retries unfinished pairs. Fully completed
duplicates perform no saves when there is no other pending work. Conflicting or
invalid feedback rejects before any pending saves.

A later valid scoped delivery may also flush older dirty pairs. Writes use current
manager statistics, never a failed event's old posterior snapshot. If A failed and
B subsequently updated the same pair, retrying A writes the posterior including B.
Partial success does not require rewriting completed pairs unless newer learning
has made them dirty again. No rollback restores an older manager snapshot.

One narrowly scoped lock per orchestrator serializes its feedback validation,
learning, and posterior writes, including duplicate/retry calls. The manager keeps
its separate process-local lock for counts and atomic batch reads. Selection and
decision may observe learned state while a save is pending. The orchestration
lock does not block those reads or make selection and later decisions use one
validation-wide reputation version. Each individual batch read is consistent;
immutable selector plans and captured decision details remain unchanged.

This lock does not coordinate other orchestrators, direct manager mutation,
external writers, or other workers. Pending work is lost on process exit and is
not included in manager export. No crash durability, restart recovery,
cross-worker idempotency, or transaction across feedback rows, memory, and
posterior rows is claimed. A successful posterior save does not persist the full
feedback identity or manager state.

## Persistence and API-owner dependencies

Manager export_state/restore_state round-trip configured priors, integer counts,
and scoped feedback history using schema version 1. Export is detached and
JSON-ready. Restore validates the entire document before swapping state, including
counts implied by feedback. A malformed restore leaves the old state intact.

Actual database wiring exists: validation records and returned verifier metadata
are saved separately; verifier_reputation stores alpha/beta; feedback has a unique
validation ID. Current build_reputation_state loads posterior rows but rebuilds a
default-prior manager from joined feedback/results only. It ignores those rows,
loses nondefault priors and observations without replayable feedback, and does not
restore validation contexts. This adapter is unchanged here. Full-state database
persistence is a database-owner dependency; a separate branch is not integrated.

The feedback routes still supply no explicit provenance: current process learning
uses external_feedback. Database replay labels feedback as ground_truth, and the
posterior row writer has no source/history field. Unverified user feedback and
benchmark sources therefore do not yet have complete end-to-end persistence.
The routes also save feedback before resolving the process-local context. Contexts
and retained response objects are not evicted or restored after restart; a request
routed to another worker may lack its context. Route ordering, durable identity,
source propagation, and distributed update coordination remain API/database-owner
work. Do not infer a transaction or trusted label source from a successful call.

## Selection and execution audit

Production consumes one immutable coverage-aware selection plan with a captured
reputation batch, explicit descriptors, complementary initial agents, and eligible
fallbacks. Expected capability does not establish actual coverage. Coverage guards
concern only requested requirements; absent contracts, abstentions, invalid typed
requirements, and missing actual coverage retain uncertainty. Runtime availability
and stopping-policy veto explanations remain in execution_audit.

The response carries that audit even with no results. With nonempty results, the
last result also carries reserved multi_agent_verification.execution metadata for
the existing JSON persistence path. Automatic lookup remains separate from
reputation learning. Unexpected execution exceptions remain visible.
