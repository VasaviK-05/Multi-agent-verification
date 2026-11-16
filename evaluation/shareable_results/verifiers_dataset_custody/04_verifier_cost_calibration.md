# Verifier cost calibration

The compatible calibration is the Development cost freeze. This package copies the existing artifacts. Calibration was not rerun.

| Field | Value |
| --- | --- |
| Freeze version | `research_v1_development_cost_calibration_freeze_v1` |
| Calibration id | `cc7e7ca8882f602b9854bf21b80b8a7bf70f6c70d05ccd12787322a84a12477d` |
| Calibration file SHA-256 | `7fbfe418c0c65c3782628ab5117b773f2fc4c8312c33d769934f76d2ff61a7f3` |
| Measurements SHA-256 | `514e39a1422a1ef0b3846e02f010e6edc4ab1a1aec89e1605e82f03199836a94` |
| Provenance record id | `rv1_dev_v1_calibration_input_e2970024e7550fbf67b0ce0513bab7cc248710f281ba3d833f4aa38d1190ad9d` |
| Input digest | `543991e00c2c3d19b31f30d226167021a22a27d78cf6c3d0cab3645e9ebed629` |
| Method | `mean_attempt_wall_time_ms_v1` |
| Unit | milliseconds of attempt wall time |
| Warm-ups | excluded from the mean |
| Attempts | 488 total, 480 eligible, 8 excluded warm-ups |
| Eligible per verifier | 120 semantic, 120 evidence, 120 rule, 120 confidence |
| Warm-ups per verifier | 2 each |
| Included non-returned attempts | 0 |
| Failures in the Experiment 3 run summary | 0 for each verifier |

Copied files:

- `evidence/cost_calibration.json`
- `evidence/cost_calibration_provenance.json`
- `evidence/cost_calibration_freeze_manifest.json`

The measurements file is not copied. Its SHA-256 is the freeze record above. `evaluation/experiments/experiment3/empirical/run_manifest.json` reports that the working-tree measurements file matched that hash. This package did not rewrite that run manifest.

## Means

| Verifier | Attempts | Mean ms | Median ms | Nearest-rank p95 ms |
| --- | ---: | ---: | ---: | ---: |
| semantic | 120 | 70.4728633359385 | 38.655450101941824 | 189.06880007125437 |
| evidence | 120 | 107.93551665459138 | 63.834649859927595 | 340.4300999827683 |
| rule | 120 | 0.09707332161876063 | 0.07880001794546843 | 0.2321999054402113 |
| confidence | 120 | 14925.820978323463 | 13753.990900004283 | 24120.17620005645 |

Confidence used `llama3.2:3b` with 5 samples in the freeze runtime block. The model-weight digest is not in the freeze. Resource manifest id `754bfa8ec4b43881a183c64478d791496e6a21d2e68b3c862d85a8e89beda10c`. Setup fingerprint `83c114806aa6eb3ba06664b8d3d6bd1892699f0c588990e0fb88f35bcc37f1ee`.

## Population and approval scope

Collection-level dataset id: `research_v1_exploratory_v1`. Permitted pair: development with that dataset id. The provenance says the reservation guard used metadata only and included no Final Test payloads.

The freeze records an approver for the cost-calibration freeze only, from the task instruction that created the freeze. The name is in the copied freeze file and is not repeated here. `development_only` is true. `final_test_access_or_execution_authorized` is false. `policy_fitting_or_budget_selection_authorized_by_this_freeze` is false. This is not a global project freeze and not an external witness.

The freeze authorizes keeping these measurements fixed. It does not itself authorize choosing a budget or fitting a policy from them.

`evaluation/config/research_v1/collection_manifest.json` still says `cost_unit` `UNKNOWN` and `approved` false. That collection manifest is older in status than this freeze. The freeze is the calibration record. The collection manifest is not a second calibration.

## Experiment 3 and Experiment 1

Experiment 3 stores calibration id `cc7e7ca8882f602b9854bf21b80b8a7bf70f6c70d05ccd12787322a84a12477d` in `evaluation/experiments/experiment3/execution_readiness.py` and in `evaluation/experiments/experiment3/empirical/run_manifest.json`.

Experiment 1's offline replay imports `score` from `evaluation/experiments/experiment3/empirical_executor.py`. That scorer uses the Experiment 3 budget, coefficient, and frozen means. Experiment 1 does not have a separate calibration. The two experiments are compatible because they share this freeze. Experiment 1 did not rerun verifiers or replace the calibration files.
