# Final Test v2 experimental configuration

Date: 2026-11-13.

**Protocol freeze is `NOT_COMPLETE`.** The researcher states that the research team approved the experimental decisions. That statement is unsigned. It is not a signature, not minutes, and not independent verification. The approved numbers and snapshot hashes are not in the existing artifacts, so those fields are `APPROVED_BY_TEAM_VALUE_REQUIRED` and were not guessed.

Manifest: `evaluation/config/research_v1/final_test_v2_experimental_configuration_manifest.json`.

Manifest SHA-256: `8015549744f5c184149361f54155d3149c75996c1c2809e34568fb62746d6852`.

Git commit inspected: `30c425e43a19d49bd50a216786333a8562731ffc`. That commit does not contain these configuration files. Reproducibility is the file hashes below, not that commit alone.

Labels were not opened, hashed, or read. The external label directory was not accessed. The Final Test experiment was not run. Custody authorization records were not modified.

## Team statement and missing approved values

The unsigned statement does not supply a value. Where a proposal file contains a number, that number remains a proposal. It is not recorded here as the approved value.

| Field | Approved value recovered | Documented proposal, not an approval |
|---|---|---|
| False-acceptance, false-rejection, and uncertainty loss | No | 1.0, 1.0, 0.2 |
| Decision threshold | No | 0.55 |
| Bootstrap resamples, level, and seed | No | 2000, 0.95, 20261113 |
| Attack scenarios | No | clean, forced support, forced rejection, confidence inflation, suppression unavailable |
| Experiment 3 comparison methods | No | full minimax, fixed reputation, fixed dependency group |
| Resource coefficient | No | none |
| Verifier budget | No | none |
| Cost unit | No | none |
| Reputation initialization and update | No | `PENDING_APPROVAL` |
| Collection seed | No | null |
| Model-weight and generator snapshots | No | `UNKNOWN` |
| Evidence corpus approval | No | hash recorded, approval `PROPOSAL_NOT_APPROVED` |
| Measured verifier dependence | No | `none` |
| Baseline configuration | No | `NOT_FROZEN_FOR_THIS_PROTOCOL` |

## Frozen configuration inventory

Nothing in the critical path is frozen. A file hash freezes the bytes of a proposal. It does not turn a proposal into an approved setting.

| Item | Mark | Why |
|---|---|---|
| Development eligibility roster, 372 groups, body hash `f2cc0fd108b961bf4795767df4f90e92d7fa0f418ef9865d0206f32d7b45282d` | APPROVED | Existing research-lead approval for Development eligibility only. Collection is not authorized. |
| Final Test v2 identity | UNRESOLVED for confirmatory use | Version `research_v1_final_test_v2_exploratory_v1`, manifest `e572093a4f0420c03316c89c83b6a7ab665af3af894d19a1428a6b091d3319ee`, roster `3f8fcbf1e698174a9a7cf6c586ec51048bcc07ca11154b36fdef0dadc7796208`, 600 groups, 1,200 candidates. Confirmatory use is `NOT_AUTHORIZED`. |
| Verifier source identities and declared thresholds | PROPOSED | `verifier_config.json`. Weight snapshots and the confidence generator digest are `UNKNOWN`. |
| Structural failure groups | PROPOSED | `structural_shared_resource_v1`. Not a measured correlation. |
| Loss weights 1.0, 1.0, and 0.2 | PROPOSED | Settings proposal only. |
| Decision threshold 0.55 | PROPOSED | Uncalibrated engine default. Not fitted on Development outcomes. |
| Bootstrap 2,000 resamples, level 0.95, seed 20261113 | PROPOSED | Preparation choices, not an approved analysis setting. |
| Attack list, with suppression unavailable | PROPOSED | Not an approved threat model. |
| Comparison methods for Experiment 3 | PROPOSED | `full_minimax`, `fixed_reputation_weighted`, `fixed_dependency_group`. |
| Missing-data rule | PROPOSED | Do not impute. Exclude unresolved labels from binary correctness. |
| Resource coefficient | UNRESOLVED | No number. |
| Verifier budget and cost unit | UNRESOLVED | No measured unit and no budget. |
| Reputation initialization and update | UNRESOLVED | No approved Person 3 policy. |
| Collection random seed | UNRESOLVED | `resource_config.json` seed is null. |
| Model-weight, prompt, and generator snapshot hashes | UNRESOLVED | `UNKNOWN` except the recorded confidence prompt hash and rule source hash. |
| Evidence corpus approval | UNRESOLVED | Corpus hash is recorded. Approval is `PROPOSAL_NOT_APPROVED`. |
| Baselines | UNRESOLVED | `baseline_freeze_package.json` is `NOT_FROZEN_FOR_THIS_PROTOCOL`. |
| Research-lead approval of this configuration | UNRESOLVED | Not requested as a signature and not recorded. |

## Configuration hashes

| File | SHA-256 |
|---|---|
| `evaluation/config/research_v1/verifier_config.json` | `740319254a30711ecb36f6a1e62cd865896fc264d4eaebf11fda9d10a0db3b97` |
| `evaluation/config/research_v1/resource_config.json` | `96e7adab02539f8bcf12834e73df34590e6daa729c0f4db28b81152b1d6a11cd` |
| `evaluation/config/research_v1/environment_manifest.json` | `7afb2c1ea39588920fde15eb73f033f90840fd3c14b330aa1cac5175001559e7` |
| `evaluation/config/research_v1/dataset_manifest.json` | `ba6762dad20d09b8d01b1ca711b4601d198e8095656ceef1fd41ebe3ca190d33` |
| `evaluation/config/research_v1/dataset_eligibility.json` | `09cf343c2cfc9015ead704aa0d3b8322b07da10c83e9b162e9218690a716f005` |
| `evaluation/config/research_v1/baseline_freeze_package.json` | `afba5ee24cf44aaaf796dc22034d20c5a64515b60aaf5530ad430602c9968c6b` |
| `evaluation/config/research_v1/protocol_index.json` | `82ff9e3c9b8e86d7a559c13480a37f5f6fc7c48da88836519be546363c10b93b` |
| `evaluation/config/research_v1/final_test_custody_manifest.json` | `eb386a719a8f515bd741cc6598bf1e69491f026b70e0946ac074060805223cee` |
| `evaluation/config/experiments/experiment1_proposal.json` | `4d1bee16665293ea40e4a51c686bb5301e94f70d58aaf7fe95c868ca93200370` |
| `evaluation/config/experiments/experiment2_proposal.json` | `7be25d1f2cc88a1d5b9a6905352326d41648bb0991218b5fc1d2f8b4ac7ff8d6` |
| `evaluation/config/experiments/experiment3_proposal.json` | `a57df03694a418e04216e55bb763cd9dfd7008f08e7e6323f11b090d0600e1e7` |
| `evaluation/config/experiments/experiment3_specification.json` | `86bead0f3048bd28c0cf344f98fd1330ee626394d52c633be8cd894389aa5032` |
| `evaluation/config/experiments/experiment3_settings_proposal.json` | `77d773fa7aad43bc0591244b64b78f37dd1142f2a9628d89ead7ad9847d8665f` |
| `evaluation/config/experiments/experiment3_dependency_configuration.json` | `c7dc14f867bedd8345184869fa8c10f7fabb554d843ed44df4d8606e993d7c2d` |
| `evaluation/config/experiments/experiment3_reputation_policy_inputs.json` | `19c0032a0e5556d9ccdf2b9a589582536e00c1ed493acca85e43ca2cbf0a67c7` |
| `evaluation/config/experiments/experiment4_proposal.json` | `805cc9e20aac1fe6832a1f5d5e5039e68441e4bd54822c73a37873396d54e65f` |

## Software

The environment manifest, hash `7afb2c1ea39588920fde15eb73f033f90840fd3c14b330aa1cac5175001559e7`, records an observation that is not an approved freeze: Python 3.12.1, Windows 11, sentence-transformers 6.0.1, transformers 5.17.0, torch 2.14.0, faiss-cpu 1.15.1, numpy 2.5.3. Hardware, GPU, and the Ollama version are `UNKNOWN`.

## Baselines, attacks, metrics, and analysis

Proposed comparison methods are the full game (`full_minimax`), a reputation-fixed ablation, and a dependency-group ablation. Experiment 1 also names coverage-aware greedy, deterministic minimax, clean development, and uniform strategies. Those names are not a frozen baseline set.

Proposed attacks are clean, forced support, forced rejection, and confidence inflation. Suppression is unavailable.

Proposed metrics are validation loss, coverage, false acceptance, false rejection, and paired differences against `full_minimax`. Intervals are percentile bootstrap intervals only if the bootstrap settings are later approved. Unresolved labels stay out of binary correctness. Missing pairs and execution failures are counted and not imputed. Final Test outcomes must not be used to change thresholds, policies, baselines, or metrics.

## Custody and readiness

Self-custody remains acknowledged and is not independent custody. Release and scoring confirmations already recorded by the researcher were not changed. They do not complete this protocol freeze. Research-lead approval of the custody amendment is `PENDING`. A separate research-lead scoring authorization is `PENDING`. Labels remain sealed. Execution readiness is not ready.

## What remains before a real freeze

The team statement is recorded. The approved value for every field in the table above is still missing from the artifacts. Weight and generator snapshots are `UNKNOWN`. Until those values are written down without being invented, this manifest stays `PREPARED_NOT_FROZEN` and the protocol stays `NOT_COMPLETE`. Final Test execution is not ready.
