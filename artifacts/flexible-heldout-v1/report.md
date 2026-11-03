# Frozen flexible-team held-out evaluation

Freeze ID: `bcba68b5bd2857246fb3c4d9248f0eb2af4fd891b5b694335799826942ae519e`. Candidates, history, probabilities, thresholds, contributor/coverage contracts, budgets and attacks were frozen before opening test payloads or collecting reports.

Each cohort contains 40 examples in 20 paired groups (20 correct and 20 incorrect). TrainingManifest and released DatasetManifest enforce example, group, question, content and run exclusions. These are source-known procedural reservations, not blinded unseen-source tests. The prepared corpus already contains most retained test facts and permitted references were fixed before outcomes; this is not an unseen-document or reference-free test.

Methods: frozen flexible policy; development-best fixed strategy satisfying the same 90% development coverage floor and reliability-first ranking; existing coverage-aware selector initial team with reputation-weighted aggregation. All three use the matching minimum-one finalization and resources. Greedy is a complete-team selection baseline, not the legacy adaptive stopping pipeline.

Minimum-two is reported only as the same fixed greedy team finalized under its original minimum-two contract. All minimum-two fits were infeasible; no minimum-two policy/probabilities were fabricated.

FA/FR rates below divide by all 40 examples; conditional FA divides by the 20 incorrect examples and conditional FR by the 20 correct examples. Selective risk divides errors by decided cases and is undefined at zero coverage. Decision loss excludes cost and is (FA+FR+0.2*uncertain)/40.

## arithmetic

Policy ID: `c6a1f9c14bf2337aa3202124a2ed087616d48a46d70f56e7f37aba0a2a446e14`. Final partition ID: `40c5bfaf47798eb02ec2aadcb5c4760a5ff4c684013e2f2c2b346e3bbcc1ca61`.

Collection: 160 verifier calls; complete=True.

The fitted flexible policy equals the development-best fixed strategy: True. This comparison shows equivalence, not a game-theory advantage.

frozen_flexible: accepts 20, rejects 20, uncertain 0; coverage 1.0; FA 0.0/40, FR 0.0/40; conditional FA 0.0, conditional FR 0.0; decision loss 0.0; selective risk 0.0.
Development -> held-out coverage: 1.0 -> 1.0; decision loss: 0.0 -> 0.0.
Selection counts (offline replay): {'rule': 40}. Size probabilities: {'1': 1.0, '2': 0.0, '3': 0.0, '4': 0.0}. Historical selected-team cost estimate 9.678209995036013 ms.
Selected failures/unavailable attempts: 0; affected cases 0. Uncertainty reasons: {}.
95% paired-group bootstrap intervals (10000 resamples, seed20261102): {"coverage": {"interval95": [1.0, 1.0], "undefined_resample_fraction": 0.0}, "decision_loss": {"interval95": [0.0, 0.0], "undefined_resample_fraction": 0.0}, "false_accept_rate_all": {"interval95": [0.0, 0.0], "undefined_resample_fraction": 0.0}, "false_accept_rate_incorrect": {"interval95": [0.0, 0.0], "undefined_resample_fraction": 0.0}, "false_reject_rate_all": {"interval95": [0.0, 0.0], "undefined_resample_fraction": 0.0}, "false_reject_rate_correct": {"interval95": [0.0, 0.0], "undefined_resample_fraction": 0.0}, "selective_risk": {"interval95": [0.0, 0.0], "undefined_resample_fraction": 0.0}, "uncertainty_rate": {"interval95": [0.0, 0.0], "undefined_resample_fraction": 0.0}}.

development_best_fixed: accepts 20, rejects 20, uncertain 0; coverage 1.0; FA 0.0/40, FR 0.0/40; conditional FA 0.0, conditional FR 0.0; decision loss 0.0; selective risk 0.0.
Development -> held-out coverage: 1.0 -> 1.0; decision loss: 0.0 -> 0.0.
Selection counts (offline replay): {'rule': 40}. Size probabilities: {'1': 1.0, '2': 0.0, '3': 0.0, '4': 0.0}. Historical selected-team cost estimate 9.678209995036013 ms.
Selected failures/unavailable attempts: 0; affected cases 0. Uncertainty reasons: {}.
95% paired-group bootstrap intervals (10000 resamples, seed20261102): {"coverage": {"interval95": [1.0, 1.0], "undefined_resample_fraction": 0.0}, "decision_loss": {"interval95": [0.0, 0.0], "undefined_resample_fraction": 0.0}, "false_accept_rate_all": {"interval95": [0.0, 0.0], "undefined_resample_fraction": 0.0}, "false_accept_rate_incorrect": {"interval95": [0.0, 0.0], "undefined_resample_fraction": 0.0}, "false_reject_rate_all": {"interval95": [0.0, 0.0], "undefined_resample_fraction": 0.0}, "false_reject_rate_correct": {"interval95": [0.0, 0.0], "undefined_resample_fraction": 0.0}, "selective_risk": {"interval95": [0.0, 0.0], "undefined_resample_fraction": 0.0}, "uncertainty_rate": {"interval95": [0.0, 0.0], "undefined_resample_fraction": 0.0}}.

coverage_aware_greedy: accepts 15, rejects 20, uncertain 5; coverage 0.875; FA 0.0/40, FR 0.0/40; conditional FA 0.0, conditional FR 0.0; decision loss 0.025; selective risk 0.0.
Development -> held-out coverage: 0.875 -> 0.875; decision loss: 0.025 -> 0.025.
Selection counts (offline replay): {'confidence,rule': 40}. Size probabilities: {'1': 0.0, '2': 1.0, '3': 0.0, '4': 0.0}. Historical selected-team cost estimate 21137.283848738298 ms.
Selected failures/unavailable attempts: 0; affected cases 0. Uncertainty reasons: {'decision_threshold': 5}.
95% paired-group bootstrap intervals (10000 resamples, seed20261102): {"coverage": {"interval95": [0.775, 0.95], "undefined_resample_fraction": 0.0}, "decision_loss": {"interval95": [0.01, 0.045], "undefined_resample_fraction": 0.0}, "false_accept_rate_all": {"interval95": [0.0, 0.0], "undefined_resample_fraction": 0.0}, "false_accept_rate_incorrect": {"interval95": [0.0, 0.0], "undefined_resample_fraction": 0.0}, "false_reject_rate_all": {"interval95": [0.0, 0.0], "undefined_resample_fraction": 0.0}, "false_reject_rate_correct": {"interval95": [0.0, 0.0], "undefined_resample_fraction": 0.0}, "selective_risk": {"interval95": [0.0, 0.0], "undefined_resample_fraction": 0.0}, "uncertainty_rate": {"interval95": [0.05, 0.225], "undefined_resample_fraction": 0.0}}.

Paired flexible-minus-baseline intervals: {"frozen_flexible-minus-coverage_aware_greedy": {"coverage": {"interval95": [0.050000000000000044, 0.22499999999999998], "undefined_resample_fraction": 0.0}, "decision_loss": {"interval95": [-0.045, -0.01], "undefined_resample_fraction": 0.0}, "false_accept_rate_all": {"interval95": [0.0, 0.0], "undefined_resample_fraction": 0.0}, "false_accept_rate_incorrect": {"interval95": [0.0, 0.0], "undefined_resample_fraction": 0.0}, "false_reject_rate_all": {"interval95": [0.0, 0.0], "undefined_resample_fraction": 0.0}, "false_reject_rate_correct": {"interval95": [0.0, 0.0], "undefined_resample_fraction": 0.0}, "selective_risk": {"interval95": [0.0, 0.0], "undefined_resample_fraction": 0.0}, "uncertainty_rate": {"interval95": [-0.225, -0.05], "undefined_resample_fraction": 0.0}}, "frozen_flexible-minus-development_best_fixed": {"coverage": {"interval95": [0.0, 0.0], "undefined_resample_fraction": 0.0}, "decision_loss": {"interval95": [0.0, 0.0], "undefined_resample_fraction": 0.0}, "false_accept_rate_all": {"interval95": [0.0, 0.0], "undefined_resample_fraction": 0.0}, "false_accept_rate_incorrect": {"interval95": [0.0, 0.0], "undefined_resample_fraction": 0.0}, "false_reject_rate_all": {"interval95": [0.0, 0.0], "undefined_resample_fraction": 0.0}, "false_reject_rate_correct": {"interval95": [0.0, 0.0], "undefined_resample_fraction": 0.0}, "selective_risk": {"interval95": [0.0, 0.0], "undefined_resample_fraction": 0.0}, "uncertainty_rate": {"interval95": [0.0, 0.0], "undefined_resample_fraction": 0.0}}}.

Minimum-two fixed greedy contract ablation: {"accepts": 15, "cases_with_execution_failure": 0, "contributor_counts": {"1": 1, "2": 39}, "correct_accept": 15.0, "correct_examples": 20, "correct_reject": 19.0, "decision_coverage": 0.85, "decision_loss": 0.030000000000000006, "estimated_resource_cost": 21137.283848738298, "examples": 40, "execution_failure_attempts": 0, "false_accept": 0.0, "false_accept_rate_all": 0.0, "false_accept_rate_incorrect": 0.0, "false_reject": 0.0, "false_reject_rate_all": 0.0, "false_reject_rate_correct": 0.0, "incorrect_examples": 20, "mean_loss": 0.12943056963409857, "rejects": 19, "selective_risk": 0.0, "uncertain": 6.0, "uncertainties": 6, "uncertainty_rate": 0.15, "uncertainty_reasons": {"decision_threshold": 5, "minimum_contributors": 1}, "unresolved": 0.0}.

Measured individual call costs: {"confidence": {"executed": 40, "includes_failures": true, "mean_ms": 12042.058099998394, "p95_nearest_rank_ms": 12079.961100127548}, "evidence": {"executed": 40, "includes_failures": true, "mean_ms": 37.26698749815114, "p95_nearest_rank_ms": 61.95599981583655}, "rule": {"executed": 40, "includes_failures": true, "mean_ms": 0.22236750810407102, "p95_nearest_rank_ms": 0.18839980475604534}, "semantic": {"executed": 40, "includes_failures": true, "mean_ms": 27.55002000485547, "p95_nearest_rank_ms": 39.66820007190108}}. Full-roster recording excludes initialization and resource-observer overhead from these call timers. It does not measure singleton deployment end-to-end latency.

Simulated report-level attacks (flexible candidate):
- forced_support: coverage 1.0, FA 20.0, FR 0.0, uncertainty 0, decision loss 0.5, selective risk 0.5.
- forced_rejection: coverage 1.0, FA 0.0, FR 20.0, uncertainty 0, decision loss 0.5, selective risk 0.5.
- confidence_inflation: coverage 1.0, FA 0.0, FR 0.0, uncertainty 0, decision loss 0.0, selective risk 0.0.
- suppression: coverage 0.0, FA 0.0, FR 0.0, uncertainty 40, decision loss 0.2, selective risk None.

## factual

Policy ID: `0df33426333e0f7bbe6418fdf7900719dbda5182f68d50405b593b3341ec9d0d`. Final partition ID: `65ee91855d773d5ae030fdb1e051f06fd99a0f51fb44fe3608ddf5820e616ca1`.

Collection: 160 verifier calls; complete=True.

The fitted flexible policy equals the development-best fixed strategy: True. This comparison shows equivalence, not a game-theory advantage.

frozen_flexible: accepts 19, rejects 20, uncertain 1; coverage 0.975; FA 0.0/40, FR 1.0/40; conditional FA 0.0, conditional FR 0.05; decision loss 0.03; selective risk 0.02564102564102564.
Development -> held-out coverage: 0.975 -> 0.975; decision loss: 0.03 -> 0.03.
Selection counts (offline replay): {'evidence': 40}. Size probabilities: {'1': 1.0, '2': 0.0, '3': 0.0, '4': 0.0}. Historical selected-team cost estimate 188.79894875281025 ms.
Selected failures/unavailable attempts: 0; affected cases 0. Uncertainty reasons: {'minimum_contributors': 1, 'missing_achieved_coverage': 1, 'decision_threshold': 1}.
95% paired-group bootstrap intervals (10000 resamples, seed20261102): {"coverage": {"interval95": [0.925, 1.0], "undefined_resample_fraction": 0.0}, "decision_loss": {"interval95": [0.0, 0.08499999999999999], "undefined_resample_fraction": 0.0}, "false_accept_rate_all": {"interval95": [0.0, 0.0], "undefined_resample_fraction": 0.0}, "false_accept_rate_incorrect": {"interval95": [0.0, 0.0], "undefined_resample_fraction": 0.0}, "false_reject_rate_all": {"interval95": [0.0, 0.075], "undefined_resample_fraction": 0.0}, "false_reject_rate_correct": {"interval95": [0.0, 0.15], "undefined_resample_fraction": 0.0}, "selective_risk": {"interval95": [0.0, 0.07894736842105263], "undefined_resample_fraction": 0.0}, "uncertainty_rate": {"interval95": [0.0, 0.075], "undefined_resample_fraction": 0.0}}.

development_best_fixed: accepts 19, rejects 20, uncertain 1; coverage 0.975; FA 0.0/40, FR 1.0/40; conditional FA 0.0, conditional FR 0.05; decision loss 0.03; selective risk 0.02564102564102564.
Development -> held-out coverage: 0.975 -> 0.975; decision loss: 0.03 -> 0.03.
Selection counts (offline replay): {'evidence': 40}. Size probabilities: {'1': 1.0, '2': 0.0, '3': 0.0, '4': 0.0}. Historical selected-team cost estimate 188.79894875281025 ms.
Selected failures/unavailable attempts: 0; affected cases 0. Uncertainty reasons: {'minimum_contributors': 1, 'missing_achieved_coverage': 1, 'decision_threshold': 1}.
95% paired-group bootstrap intervals (10000 resamples, seed20261102): {"coverage": {"interval95": [0.925, 1.0], "undefined_resample_fraction": 0.0}, "decision_loss": {"interval95": [0.0, 0.08499999999999999], "undefined_resample_fraction": 0.0}, "false_accept_rate_all": {"interval95": [0.0, 0.0], "undefined_resample_fraction": 0.0}, "false_accept_rate_incorrect": {"interval95": [0.0, 0.0], "undefined_resample_fraction": 0.0}, "false_reject_rate_all": {"interval95": [0.0, 0.075], "undefined_resample_fraction": 0.0}, "false_reject_rate_correct": {"interval95": [0.0, 0.15], "undefined_resample_fraction": 0.0}, "selective_risk": {"interval95": [0.0, 0.07894736842105263], "undefined_resample_fraction": 0.0}, "uncertainty_rate": {"interval95": [0.0, 0.075], "undefined_resample_fraction": 0.0}}.

coverage_aware_greedy: accepts 16, rejects 20, uncertain 4; coverage 0.9; FA 0.0/40, FR 1.0/40; conditional FA 0.0, conditional FR 0.05; decision loss 0.045; selective risk 0.027777777777777776.
Development -> held-out coverage: 0.9 -> 0.9; decision loss: 0.045 -> 0.045.
Selection counts (offline replay): {'confidence,evidence': 40}. Size probabilities: {'1': 0.0, '2': 1.0, '3': 0.0, '4': 0.0}. Historical selected-team cost estimate 15921.25526748423 ms.
Selected failures/unavailable attempts: 0; affected cases 0. Uncertainty reasons: {'minimum_contributors': 1, 'missing_achieved_coverage': 1, 'decision_threshold': 4}.
95% paired-group bootstrap intervals (10000 resamples, seed20261102): {"coverage": {"interval95": [0.8, 0.975], "undefined_resample_fraction": 0.0}, "decision_loss": {"interval95": [0.01, 0.1], "undefined_resample_fraction": 0.0}, "false_accept_rate_all": {"interval95": [0.0, 0.0], "undefined_resample_fraction": 0.0}, "false_accept_rate_incorrect": {"interval95": [0.0, 0.0], "undefined_resample_fraction": 0.0}, "false_reject_rate_all": {"interval95": [0.0, 0.075], "undefined_resample_fraction": 0.0}, "false_reject_rate_correct": {"interval95": [0.0, 0.15], "undefined_resample_fraction": 0.0}, "selective_risk": {"interval95": [0.0, 0.08571428571428572], "undefined_resample_fraction": 0.0}, "uncertainty_rate": {"interval95": [0.025, 0.2], "undefined_resample_fraction": 0.0}}.

Paired flexible-minus-baseline intervals: {"frozen_flexible-minus-coverage_aware_greedy": {"coverage": {"interval95": [0.0, 0.15000000000000002], "undefined_resample_fraction": 0.0}, "decision_loss": {"interval95": [-0.030000000000000013, 0.0], "undefined_resample_fraction": 0.0}, "false_accept_rate_all": {"interval95": [0.0, 0.0], "undefined_resample_fraction": 0.0}, "false_accept_rate_incorrect": {"interval95": [0.0, 0.0], "undefined_resample_fraction": 0.0}, "false_reject_rate_all": {"interval95": [0.0, 0.0], "undefined_resample_fraction": 0.0}, "false_reject_rate_correct": {"interval95": [0.0, 0.0], "undefined_resample_fraction": 0.0}, "selective_risk": {"interval95": [-0.008791208791208788, 0.0], "undefined_resample_fraction": 0.0}, "uncertainty_rate": {"interval95": [-0.15000000000000002, 0.0], "undefined_resample_fraction": 0.0}}, "frozen_flexible-minus-development_best_fixed": {"coverage": {"interval95": [0.0, 0.0], "undefined_resample_fraction": 0.0}, "decision_loss": {"interval95": [0.0, 0.0], "undefined_resample_fraction": 0.0}, "false_accept_rate_all": {"interval95": [0.0, 0.0], "undefined_resample_fraction": 0.0}, "false_accept_rate_incorrect": {"interval95": [0.0, 0.0], "undefined_resample_fraction": 0.0}, "false_reject_rate_all": {"interval95": [0.0, 0.0], "undefined_resample_fraction": 0.0}, "false_reject_rate_correct": {"interval95": [0.0, 0.0], "undefined_resample_fraction": 0.0}, "selective_risk": {"interval95": [0.0, 0.0], "undefined_resample_fraction": 0.0}, "uncertainty_rate": {"interval95": [0.0, 0.0], "undefined_resample_fraction": 0.0}}}.

Minimum-two fixed greedy contract ablation: {"accepts": 6, "cases_with_execution_failure": 0, "contributor_counts": {"0": 1, "1": 19, "2": 20}, "correct_accept": 6.0, "correct_examples": 20, "correct_reject": 10.0, "decision_coverage": 0.425, "decision_loss": 0.14, "estimated_resource_cost": 15921.25526748423, "examples": 40, "execution_failure_attempts": 0, "false_accept": 0.0, "false_accept_rate_all": 0.0, "false_accept_rate_incorrect": 0.0, "false_reject": 1.0, "false_reject_rate_all": 0.025, "false_reject_rate_correct": 0.05, "incorrect_examples": 20, "mean_loss": 0.239725705793547, "rejects": 11, "selective_risk": 0.058823529411764705, "uncertain": 23.0, "uncertainties": 23, "uncertainty_rate": 0.575, "uncertainty_reasons": {"decision_threshold": 4, "minimum_contributors": 20, "missing_achieved_coverage": 1}, "unresolved": 1.0}.

Measured individual call costs: {"confidence": {"executed": 40, "includes_failures": true, "mean_ms": 13775.649857480312, "p95_nearest_rank_ms": 14672.4733998999}, "evidence": {"executed": 40, "includes_failures": true, "mean_ms": 194.0926175157074, "p95_nearest_rank_ms": 408.31740014255047}, "rule": {"executed": 40, "includes_failures": true, "mean_ms": 0.1367099757771939, "p95_nearest_rank_ms": 0.2359999343752861}, "semantic": {"executed": 40, "includes_failures": true, "mean_ms": 51.58403249224648, "p95_nearest_rank_ms": 83.15410022623837}}. Full-roster recording excludes initialization and resource-observer overhead from these call timers. It does not measure singleton deployment end-to-end latency.

Simulated report-level attacks (flexible candidate):
- forced_support: coverage 0.975, FA 19.0, FR 0.0, uncertainty 1, decision loss 0.48, selective risk 0.48717948717948717.
- forced_rejection: coverage 0.975, FA 0.0, FR 20.0, uncertainty 1, decision loss 0.505, selective risk 0.5128205128205128.
- confidence_inflation: coverage 0.975, FA 0.0, FR 1.0, uncertainty 1, decision loss 0.03, selective risk 0.02564102564102564.
- suppression: coverage 0.0, FA 0.0, FR 0.0, uncertainty 40, decision loss 0.2, selective risk None.

## Interpretation and handoff

The 90% development constraint was not assumed to hold on test. Shared dependencies connect the declared failure group across selected verifiers: adding team members does not establish independent protection. Report corruption is simulated and is not an actual upstream compromise experiment.

Percentile bootstrap intervals preserve paired answers and paired methods. With only 20 source-known groups, zero observed errors can produce a degenerate zero-width interval; that is not a guarantee of zero population error. Results support only the narrow retained arithmetic/factual cohorts, with one local generation realization and the recorded corpus snapshot.

Recommendation: retain these as offline candidates and collect broader independently grouped and source-independent evidence before general adoption. A minimum-two contract can reduce decisions but its infeasible fit supplies no deployable fallback policy. This study does not establish minimax superiority or broad domain/difficulty adaptation.

Reproduce preparation with scripts.flexible_heldout, collection with scripts/collect_flexible_heldout.py from the resource-compatible original checkout, then evaluation with scripts.evaluate_flexible_heldout. All paths and exact IDs are in freeze-manifest.json, precollection-seal.json, per-cohort collector-provenance.json, and heldout-results.json. The final partitions remain evaluation-only: never pass them into fitting or reputation updates.

Later integration must keep each frozen policy/context/contract together, validate actual resource identity and explicitly review this limited evidence. No semantic cohort was collected. No policy was refitted, no reputation updated, and nothing committed, pushed, merged or activated.
