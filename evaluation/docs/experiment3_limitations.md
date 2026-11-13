# Experiment 3 limitations

- The protocol is `PENDING_APPROVAL` and is not frozen. Unsigned templates are not approvals.
- Resource coefficient, verifier budget, and the cost unit are unresolved. A loss that includes cost cannot be computed.
- Reputation initialization, update, and smoothing are `PENDING_APPROVAL`. Person 3 observations are 0. Development outcomes are not a reputation source.
- Verifier snapshot hashes, prompt hashes, hardware, timeout, retries, and the collection seed are unknown. The corpus is not approved. Embedding weights are `UNKNOWN`. Leakage clearance is `NOT_CLAIMED`. Gold-answer strings remain a recorded corpus limitation.
- `provisional_shared_unknown_v1` puts all verifiers in one failure group, so it cannot separate independent and correlated failures. `structural_shared_resource_v1` is an unapproved structural grouping, not a measured correlation.
- Hypothetical dependency configurations have no loss values. They are not measured dependencies.
- The synthetic fixture uses hand-built reports for verifiers named `a`, `b`, and `c`. Its losses are not Development results. Suppression in that fixture is part of the fixture's attack list; the proposed Development setting still marks suppression unavailable.
- The synthetic runner cannot be loaded. Existing fixture outputs were preserved rather than regenerated.
- Eligibility JSONL files in the working tree use CR bytes. Their LF-normalized hashes match. They were not rewritten.
- No claim is made that aggregation choice or dependency modeling improves validation performance.
