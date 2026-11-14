# Experiment 3 integration audit

Audit date: 2026-11-14. Checkout: branch `raunak-exp-3`, commit `5485c54eaaecc1e338d4b1e3b889353a7a34ce98`. The requested branch name `raunak-research-evaluation` points at `d2c7d79` (`checkpoint 7`), which is an ancestor and does not contain the Experiment 3 runner or the merged cost-calibration bundle. This audit uses `raunak-exp-3`, where both are present.

Final Test labels were not opened. No eligibility, corpus, or calibration file was rewritten.

## What is already on the branch

`evaluation/experiments/experiment3/` has a collection gate, a corpus and eligibility audit, a synthetic fixture, and hypothetical dependency figures. `app/game/research/comparison.py` defines `full_minimax`, `fixed_reputation_weighted`, and `fixed_dependency_group` on a development payoff matrix. `app/reputation/reputation_manager.py` is the reputation implementation. `app/game/policy.py` builds a policy by enumerating feasible strategies and solving the minimax program. `app/game/offline/calibration.py` defines the millisecond calibration artifact and `apply_calibration`.

`evaluation/docs/experiment3_protocol.md` records the protocol as `PENDING_APPROVAL`. `assess()` on this checkout returns `READY_FOR_APPROVAL`. That status means the specification package is internally consistent. It does not mean collection is authorized.

## Approved Development roster

Manifest: `evaluation/artifacts/person1/research_v1_exploratory_eligibility_approved_v1/eligibility_manifest.json`.

| Fact | Value |
|---|---|
| Body SHA-256 | `f2cc0fd108b961bf4795767df4f90e92d7fa0f418ef9865d0206f32d7b45282d` |
| Dataset | `research_v1_exploratory_v1` |
| Eligible groups | 372 (GSM8K 187, HotpotQA 185) |
| Eligible candidates | 744 |
| Label protocol | `provisional_automated_labeling_v1` |
| `collection_authorized` | false |
| `recording_authorized` | false |
| `final_test_authorized` | false |

The manifest's `does_not_authorize` list includes verifier collection, attempt recording, protocol freeze, and policy fitting. Each eligible group in `development_eligible.jsonl` pairs one `VERIFIED_CORRECT` candidate with one `SYNTHETIC_INCORRECT` candidate. LF-normalized hashes of the eligibility outputs match `output_sha256`. Working-tree JSONL files contain CR bytes and were not rewritten. Leakage clearance remains `NOT_CLAIMED`.

## Frozen cost calibration

Bundle: `artifacts/research-v1-development-cost-calibration-v1/`. The freeze scope is Development-only. It does not authorize Final Test access, policy fitting, or budget selection.

| File | Frozen SHA-256 | Check |
|---|---|---|
| `calibration.json` | `7fbfe418c0c65c3782628ab5117b773f2fc4c8312c33d769934f76d2ff61a7f3` | Working-tree bytes match. 885,049 bytes. |
| `measurements.json` | `514e39a1422a1ef0b3846e02f010e6edc4ab1a1aec89e1605e82f03199836a94` | Working-tree bytes match. 427,057 bytes. |
| `calibration-provenance.json` | `391094b7a74b6da2c6b617a7f6bf27fbc71e94ad56855df7106e618a9d5c5637` | LF-normalized bytes match. A CRLF checkout is 2,629 bytes with raw SHA-256 `938f4f1fd4b803004cf55c710b41a9d438bc440db5fa11c352afb497144cf9a0`. The committed blob is the 2,565-byte LF file. |
| `freeze-manifest.json` | not stored inside itself | Working-tree SHA-256 `cba1b8861eacdffd77e0e97865eb24bb45ff723a06d174988f0b0c527a3ada72`. |

Calibration identity `cc7e7ca8882f602b9854bf21b80b8a7bf70f6c70d05ccd12787322a84a12477d`. Input digest `543991e00c2c3d19b31f30d226167021a22a27d78cf6c3d0cab3645e9ebed629`. Method `mean_attempt_wall_time_ms_v1`. Unit `ms`. Warm-ups are excluded. 488 development attempts are in the measurement file: 480 calibration attempts and 8 warm-ups, 122 per verifier before the warm-up exclusion, all `returned`, dataset `research_v1_exploratory_v1`.

Mean attempt cost in milliseconds, 120 attempts each, from `calibration.json`:

| Verifier | Mean ms |
|---|---|
| semantic | 70.4728633359385 |
| evidence | 107.93551665459138 |
| rule | 0.09707332161876063 |
| confidence | 14925.820978323463 |

Resource manifest id recorded by the freeze: `754bfa8ec4b43881a183c64478d791496e6a21d2e68b3c862d85a8e89beda10c`. Setup fingerprint: `83c114806aa6eb3ba06664b8d3d6bd1892699f0c588990e0fb88f35bcc37f1ee`. Measurement code revision: `662bd5cdbf2c8b2dc9885f6bb80e42abf7c5205e`. Provenance record `rv1_dev_v1_calibration_input_e2970024e7550fbf67b0ce0513bab7cc248710f281ba3d833f4aa38d1190ad9d`. `CalibrationArtifact` validation of `calibration.json` succeeded. The computed resource manifest id and setup fingerprint match the freeze record. That check is stored in `evaluation/experiments/experiment3/empirical/run_manifest.json`.

`evaluation/config/experiments/experiment3_collection_configuration.json` still says `cost_measurements_available: false` and leaves the cost unit as the placeholder "Person 2 measured attempt-cost units". That file is the artifact named by the unsigned collection authorization, whose recorded SHA-256 is `6f539d60464d684e9633b102f8b06ae6f598c5c4035e0d34f7e8a8d8be3adcda`. It was not edited. The frozen calibration is therefore available to the runner, and it is not yet the collection configuration's cost measurement id.

## Historical rehearsal

`docs/research_v1-recording-handoff/evidence-index.json` records `research_v1_development_rehearsal_662bd5c.zip`, SHA-256 `f688faff1cf4a25abe30d7e6516a0eab58bd0015a78d6863054c0435491d10f0`, 18,333 bytes. `docs/experiment1/phase-c/audit-results.json` lists the same archive at `/Users/vasavi/Downloads/research_v1_development_rehearsal_662bd5c.zip` and sets `payload_members_opened` to false. The ZIP is not in this checkout, so its attempt count was not recomputed and its payload was not read. It is diagnostic context for code revision `662bd5c` only. It is not the 372-group Experiment 3 dataset. The 488 calibration attempts above are a different Development collection.

## Unresolved protocol decisions

These remain unsigned in `evaluation/config/experiments/approvals/`:

1. Protocol approval `experiment3_protocol_approval_record.json` is `NOT_AN_APPROVAL`. `approved_settings` is null. The settings proposal's false-acceptance weight 1.0, false-rejection weight 1.0, uncertainty weight 0.2, and threshold 0.55 are `PROPOSED_PENDING_APPROVAL`. Resource coefficient and verifier budget have no proposed number.
2. Corpus approval is unsigned. Freeze status is not a signed `FROZEN` record.
3. Dependency approval is unsigned. `structural_shared_resource_v1` is `PROVISIONAL`, with `empirical_evidence: none`. Rule is alone. Semantic and evidence share the embedding model. Evidence and confidence share the NLI model. Confidence also depends on an unpinned generator. Overlapping membership is a shared-resource description, not a measured correlation. The game's `DependencyRegistry` would connect semantic, evidence, and confidence into one component because evidence belongs to both model groups. That collapse was not written back into the provisional configuration.
4. Collection authorization is `NOT_AUTHORIZED`. Verifier model-weight hashes, the rule version hash, hardware, software lock, and the collection seed are `UNKNOWN` or null. Suppression remains unavailable.
5. Reputation inputs are `PENDING_PERSON3` with zero observations. Initialization, update rule, smoothing, and the export format are `PENDING_APPROVAL`. Development outcomes are explicitly not a reputation source. History may be used only after an approved update rule, which is absent.

No approval value was invented to close these gaps.
