# Experiment 3 reputation and policy integration

The experiment uses `app.reputation.reputation_manager.ReputationManager` and `app.game.policy.build_policy`. No second reputation manager was added. No experiment snapshot or policy artifact was written.

## Reputation update

For each verifier and domain, with prior `a0 = ReputationManager.DEFAULT_ALPHA` and `b0 = ReputationManager.DEFAULT_BETA`:

```
alpha = a0 + successes
beta = b0 + failures
mean = alpha / (alpha + beta)
variance = alpha * beta / ((alpha + beta)^2 * (alpha + beta + 1))
```

Both defaults are 1.0. The reported reputation is `round(mean, 6)`. With no observations that value is 0.5. Successes and failures are integers. A directional vote is a success when its passed flag equals the external boolean label. Rejecting an incorrect answer is a success. Abstentions and verifiers that did not run add no observation. `record_feedback` ignores an exact replay of the same validation id and rejects a changed label or vote list for that id.

## Smoothing and decay

The only smoothing is the Beta(1, 1) prior. Counts are not confidence-weighted. There is no decay, no EWMA, and no exploration bonus. The module documents the prior as uncalibrated. `evaluation/config/experiments/experiment3_reputation_policy_inputs.json` leaves initialization and smoothing at `PENDING_APPROVAL`, so the code default was not adopted as the Experiment 3 snapshot.

## Roster

The collection configuration and the frozen calibration name the same four verifiers: `semantic`, `evidence`, `rule`, `confidence`. Reputation state is stored per verifier and domain. No domain for the Experiment 3 snapshot is approved.

## History and persistence

`export_state` returns schema version 1: priors, integer counts, and scoped feedback. `restore_state` replaces the manager only after the whole payload validates. A second export of a restored manager matches the first. That round trip is the reproducibility check, and it does not create observations.

`app.game.offline.records.history_reputation` can learn from a history partition only. The Experiment 3 input file allows history after an approved update rule and says Development outcomes are not a reputation source. The update rule is `PENDING_APPROVAL`, so `history_reputation` was not called and no History snapshot was loaded.

`docs/reputation_integration.md` records that the database adapter rebuilds a default-prior manager from feedback and does not restore a full exported state. That adapter was not used for this experiment.

## Policy builder

`build_policy` checks the planning context against the payoff matrix, enumerates the feasible strategies, and solves the minimax program. `prepare_comparison` keeps the full-game solution for `full_minimax`. For `fixed_reputation_weighted` and `fixed_dependency_group` it restricts the matrix to that aggregation and solves the restricted game. `app.game.offline.build.verify_equivalent` refits the same specification and compares the matrix, the reputation snapshot, and the probabilities.

Those functions were not called for Experiment 3. A policy artifact needs empirical Development reports, an approved loss and threshold, a resource coefficient, a verifier budget, and an approved reputation source. None of those inputs is signed. The calibration freeze states that it does not authorize policy fitting or budget selection. The eligibility manifest also withholds policy fitting. `apply_calibration` requires an explicit `budget_ms` and `resource_weight_per_ms`; neither number exists in the protocol approval.

## What was not substituted

The cold-start vector of 0.5 was not saved as the experiment snapshot. The synthetic fixture was not used as a reputation source. No policy file was exported. The blockers are in `evaluation/experiments/experiment3/empirical/run_manifest.json` under `reputation.snapshot_blockers` and `policy.blockers`.
