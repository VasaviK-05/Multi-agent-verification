# Experiment 3 approval decisions

Status: prepared for one research-lead review. Nothing in this document is a signature. Collection remains unauthorized. Final Test labels were not opened.

The bound inventory is `evaluation/experiments/experiment3/approval_package/manifest.json`. Its own status is `PREPARED_FOR_REVIEW`, `approved: false`. Recompute it with `python evaluation/experiments/experiment3/approval_inventory.py` only when an input file changes, then review the diff. The gate does not treat that manifest as an approval.

## A. Decisions requiring approval

| Decision | Current proposed value | State |
|---|---|---|
| False-acceptance loss | 1.0 | Proposed in `experiment3_settings_proposal.json`. Not in `approved_settings`. |
| False-rejection loss | 1.0 | Same proposal. |
| Uncertainty loss | 0.2 | Same proposal. |
| Decision threshold | 0.55 | Same proposal. It is the uncalibrated DecisionEngine default. |
| Suppression | unavailable | Same proposal. The attack enumerator does not apply suppression in this mode. |
| Bootstrap | 2000 resamples, level 0.95, seed 20261113 | Same proposal. |
| Sample | All 372 approved Development groups | Eligibility census, not a power calculation. |
| Missing labels | Exclude unresolved labels. Do not impute. | Same proposal. |
| Resource coefficient | null | No approved protocol contains a number. |
| Verifier budget | null | No approved budget exists. `resource_config.json` has `resource_budget: null`. |
| Cost unit for a future budget | ms | Frozen calibration unit. The collection configuration still says the unit is unnamed and `cost_measurements_available` is false. |
| Reputation initialization | Beta(1, 1), reported cold start 0.5 | Proposal only, in `approval_package/reputation_initialization_proposal.json`. The input record remains `PENDING_APPROVAL`. |
| Reputation smoothing | The same prior. No confidence-weighted counts. | Proposal. |
| Reputation decay | None. The implementation has no decay. | Proposal. |
| Reputation observations | 0 | No approved source. Development labels are not a source. History is not authorized. |
| Verifier roster | semantic, evidence, rule, confidence | Named in the collection configuration and the calibration. Weight hashes are `UNKNOWN`. |
| Dependency model | `structural_shared_resource_v1`, provisional, evidence `none` | Not a measured correlation. |
| Corpus | `development_evidence_corpus_v1`, SHA-256 `f76c6ce19661e2fdae44f87f126825d8efc4b3edb3fa1b381d0130c7f82e5e2b` | Prepared. Freeze status `NOT_FROZEN`. |
| Collection | Not authorized | Authorization template is `NOT_AN_APPROVAL`. |

The specification's dependency scenario still names `provisional_shared_unknown_v1`, while `experiment3_dependency_configuration.json` names `structural_shared_resource_v1`. Both files are unsigned. This package does not rewrite either hash.

`verifier_config.json` records a rule source SHA-256 `bf9d212d6f179e786241559a2ce974a69dcdfa74d3d8f5c59fd8cab2c4b61715`. The collection configuration still has `rule_version_hash: UNKNOWN`. Those were not copied together.

## B. Recommended configuration

Use the proposed loss weights, threshold, suppression mode, bootstrap settings, 372-group census, and no imputation, because those values are already the single proposal and match `research_settings_proposal_v1`.

Use milliseconds from the frozen calibration `cc7e7ca8882f602b9854bf21b80b8a7bf70f6c70d05ccd12787322a84a12477d`. Do not convert the unit.

Leave the resource coefficient and the verifier budget unset until the research lead writes both numbers into `approved_settings`. They cannot be derived from an approved protocol. The calibration freeze says it does not authorize budget selection. `research_settings_proposal_v1` leaves the coefficient `PENDING` and rejects the pilot value `0.1/budget` because that value changes with the budget.

For reputation, the recommendation is the implementation's cold start: prior alpha 1, prior beta 1, no decay, and no observations. That is the only initialization `ReputationManager` implements, and it does not use Development labels or a History snapshot. It stays a proposal until it is signed. No snapshot file was written.

Keep the verifier roster as the four calibrated verifiers. Do not fill model-weight hashes from the name of a model. The collection gate still requires those hashes before `READY_FOR_DEVELOPMENT_COLLECTION`.

Keep `structural_shared_resource_v1` as the provisional dependency description: rule alone, semantic and evidence on the embedding model, evidence and confidence on the NLI model, confidence also on an unpinned generator. Approval of that description would not be a measured-dependence claim.

## C. Alternatives

Resource coefficient and budget have no approved numeric candidates. The consequences of the open choices are:

| Choice | What it does | Why it is not selected here |
|---|---|---|
| Leave both null | The gate cannot reach collection authorization, because signed settings must contain both numbers. Decision-only loss can be defined later without a coefficient. Cost-augmented loss cannot. | This is the current state. |
| Pilot `resource_weight = 0.1/budget` | The coefficient shrinks when the budget grows, so two budgets are not the same penalty. | `research_settings_proposal_v1` already rejects it. |
| One matched budget at or above the sum of the four mean attempt costs, 15104.326431635612 ms | Every method can field the full roster. Aggregation is not confounded with an inability to pay for confidence. | This is a scale fact from the calibration, not an approved budget. |
| One matched budget below the confidence mean, 14925.820978323463 ms | Confidence is infeasible for every method. The comparison no longer holds the roster fixed. | Experiment 3 requires matched resource settings. |

Measured means, 120 non-warmup attempts each: semantic 70.4728633359385 ms, evidence 107.93551665459138 ms, rule 0.09707332161876063 ms, confidence 14925.820978323463 ms.

The loss relationship, from `Metrics` in `app/game/offline/evaluation.py`, is:

```
decision loss = 0 when the decision matches the label;
                false_accept, false_reject, or uncertain otherwise
validation loss = mean decision loss, with cost excluded
mean loss = decision loss + resource_weight * estimated attempt cost
```

`validation_loss` does not include cost. `mean_loss` does. The budget is a feasibility cap in the same unit as estimated cost. It is not added as a third penalty. One budget must be shared by `full_minimax`, `fixed_reputation_weighted`, and `fixed_dependency_group`.

Reputation alternatives are the cold-start proposal above, or continued blocking. History snapshots and Development labels are not alternatives under the current input record.

## D. Approval checklist

The research lead can mark each line. Unsigned lines stay blockers.

- [ ] Accept or replace false acceptance 1.0, false rejection 1.0, uncertainty 0.2, and threshold 0.55.
- [ ] Write a resource coefficient in loss per millisecond. Do not use `0.1/budget`.
- [ ] Write one verifier budget in milliseconds, shared by all three methods.
- [ ] Accept suppression as unavailable, bootstrap 2000 / 0.95 / seed 20261113, and the 372-group census with no imputation.
- [ ] Copy the accepted numbers into `approved_settings` on a signed protocol approval whose `artifact_sha256` is `f64b47cfe206548c57f60d48ebf2404dacce65b46ed05e4210fe68fb8250f529`, or into a new specification whose hash is then recorded. Leave the proposal file unapproved.
- [ ] Sign the corpus record against `f76c6ce19661e2fdae44f87f126825d8efc4b3edb3fa1b381d0130c7f82e5e2b` and set `freeze_status` to `FROZEN` only in that signed record.
- [ ] Sign the dependency record for `structural_shared_resource_v1` hash `c7dc14f867bedd8345184869fa8c10f7fabb554d843ed44df4d8606e993d7c2d`, without calling it measured dependence.
- [ ] Accept or reject the cold-start reputation proposal `5eac889b0904957b2f926dc65a9b10531acd9b1514af0e953b9c01f395d80bad`. Do not train on Development labels.
- [ ] After the three review records are signed, fill verifier hashes and the collection seed, bind the cost measurement id to calibration `cc7e7ca8882f602b9854bf21b80b8a7bf70f6c70d05ccd12787322a84a12477d` if that calibration is the one to use, and only then sign collection authorization.

## E. Execution readiness

The collection gate on this checkout is `READY_FOR_APPROVAL`. `collection_started` is false. The withheld reasons are unsigned protocol settings, an unfrozen corpus, an unsigned dependency record, unauthorized collection, incomplete verifier hashes, a missing seed, unapproved reputation initialization, and a collection configuration that does not bind a cost measurement.

Signing the protocol, corpus, and dependency records moves the gate to `READY_FOR_COLLECTION_AUTHORIZATION`. It does not start verifiers. Collection becomes admissible only after the collection authorization is also signed, the corpus freeze flag agrees, verifier hashes are known, and the seed is set. The runner in `empirical_runner.py` still stops while any of those blockers remain. This preparation run did not call it to collect data.

Cost-augmented loss and a policy artifact remain impossible until the signed settings contain a coefficient and a budget. A reputation snapshot remains impossible until the initialization proposal is signed. Cold-start approval would allow a snapshot of the prior only. It would not create observations.

## Artifact hashes

Working-tree SHA-256. The calibration provenance freeze hash is the LF digest `391094b7a74b6da2c6b617a7f6bf27fbc71e94ad56855df7106e618a9d5c5637`. A CRLF checkout hashes to the value below. The eligibility protocol identity remains the body hash `f2cc0fd108b961bf4795767df4f90e92d7fa0f418ef9865d0206f32d7b45282d`; the table's eligibility row is the complete file.

| Role | Status | SHA-256 |
|---|---|---|
| Protocol specification | proposed | `f64b47cfe206548c57f60d48ebf2404dacce65b46ed05e4210fe68fb8250f529` |
| Loss settings proposal | proposed | `77d773fa7aad43bc0591244b64b78f37dd1142f2a9628d89ead7ad9847d8665f` |
| Settings approval template | proposed | `32d0999200929977d37216be6c08552343aa6fd856428d6ec617301219241de9` |
| Protocol approval template | proposed | `4dcf0fb8af101294c297b3c7c17d033f597de9ea1c73a2f9aa9a28ecf1420e48` |
| Resource proposal | proposed | `9393c6b0caf82778670b971d3c4e5ee5b0c8cbf9b01b34a7c244f5f8f94a498c` |
| Resource declaration | proposed | `96e7adab02539f8bcf12834e73df34590e6daa729c0f4db28b81152b1d6a11cd` |
| Calibration artifact | prepared | `7fbfe418c0c65c3782628ab5117b773f2fc4c8312c33d769934f76d2ff61a7f3` |
| Measurements | prepared | `514e39a1422a1ef0b3846e02f010e6edc4ab1a1aec89e1605e82f03199836a94` |
| Calibration provenance | prepared | `938f4f1fd4b803004cf55c710b41a9d438bc440db5fa11c352afb497144cf9a0` |
| Calibration freeze | approved for that freeze only | `cba1b8861eacdffd77e0e97865eb24bb45ff723a06d174988f0b0c527a3ada72` |
| Reputation proposal | proposed | `5eac889b0904957b2f926dc65a9b10531acd9b1514af0e953b9c01f395d80bad` |
| Reputation inputs | proposed | `19c0032a0e5556d9ccdf2b9a589582536e00c1ed493acca85e43ca2cbf0a67c7` |
| Dependency configuration | proposed | `c7dc14f867bedd8345184869fa8c10f7fabb554d843ed44df4d8606e993d7c2d` |
| Dependency approval template | proposed | `72a4b15bd709bb199a97201a641862dc021197d746fbea2ee8dd108d742e50df` |
| Evidence corpus | prepared | `f76c6ce19661e2fdae44f87f126825d8efc4b3edb3fa1b381d0130c7f82e5e2b` |
| Corpus package | proposed | `7c57f6b29ce681a74767d579d8fb8d82c4f65dd85c5373c8423cd171ee79b72f` |
| Corpus approval template | proposed | `f840ca32639b4a37fa3a4f410be9f4a47431ab9ad23453b360161203a268491b` |
| Collection configuration | proposed | `6f539d60464d684e9633b102f8b06ae6f598c5c4035e0d34f7e8a8d8be3adcda` |
| Collection authorization template | proposed | `c99f0d35b7c2cfed4e04d1ed95e00955f2fcd5d94b9d7aa0ea47bc8a1dfc5fd6` |
| Verifier configuration | proposed | `740319254a30711ecb36f6a1e62cd865896fc264d4eaebf11fda9d10a0db3b97` |
| Runtime manifest | proposed | `7afb2c1ea39588920fde15eb73f033f90840fd3c14b330aa1cac5175001559e7` |
| Development eligibility file | approved for eligibility only | `1ebb4357d599a52d1c1fc8d8951ab39fa6992e846cf997d9e588820c87cbe731` |

No existing approval template was overwritten. No approver name or date was added.
