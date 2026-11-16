# Experiment 3 final protocol decision

Superseded for execution: the research-lead instruction selects the low coefficient `1.3399597937725295e-05` loss per millisecond and the confidence-entry budget `14996.39091498102` milliseconds, bound to calibration `cc7e7ca8882f602b9854bf21b80b8a7bf70f6c70d05ccd12787322a84a12477d`. The permissive budget discussed below was the earlier review candidate. It is not the executed budget. The selection is not an empirically optimized parameter, and this memo was not signed.



Status: this memo is not a signature. No approver name or date was written into an approval record. The executed configuration is the superseded note above. Final Test labels were not opened. Synthetic sensitivity results are not empirical findings.

The bound inventory is `evaluation/experiments/experiment3/approval_package/manifest.json`, SHA-256 `4007cd02a180598b52ad1d3eab9bc05483f3cf0a8a5e38516cc755f73d334798`. Its status is `PREPARED_FOR_REVIEW`, `approved: false`, `collection_authorized: false`. The gate does not treat that manifest as an approval.

## Experimental design

Two questions are in `experiment3_protocol_specification_v1`, still `PENDING_APPROVAL`:

- What is the effect of the aggregation strategy when verifier reports and the other controlled inputs stay fixed?
- What is the effect of the declared dependency structure on attack targets and decisions?

Methods, one shared budget and one shared loss for all three:

- `full_minimax`
- `fixed_reputation_weighted`
- `fixed_dependency_group`

Declared conditions for collection are clean, forced support, forced rejection, and confidence inflation. Suppression stays `unavailable`. The attack enumerator does not apply suppression in that mode.

Population: the approved Development eligibility census, not a power calculation. Dataset `research_v1_exploratory_v1`. 372 groups (GSM8K 187, HotpotQA 185) and 744 candidates. Eligibility body SHA-256 `f2cc0fd108b961bf4795767df4f90e92d7fa0f418ef9865d0206f32d7b45282d`. That approval authorizes eligibility only. `collection_authorized`, `recording_authorized`, and `final_test_authorized` are false. `final_test` is a prohibited partition.

Analysis, proposed and not yet in `approved_settings`: paired comparison on `related_group_id`, resample groups with replacement, 2,000 resamples, 95% interval, seed `20261113`. Do not compare independent method means. Unresolved labels stay out of binary correctness. Do not impute them.

## Loss configuration

Proposed in `experiment3_settings_proposal.json`. Pending approval. Not copied into `approved_settings`.

| Setting | Proposed value | Consequence |
|---|---:|---|
| False acceptance | 1.0 | A passed decision on an incorrect answer costs the same as a false rejection. |
| False rejection | 1.0 | A failed decision on a correct answer costs the same as a false acceptance. |
| Uncertainty | 0.2 | An uncertain decision costs less than a wrong decision, so abstention is allowed and not free. |
| Threshold | 0.55 | The uncalibrated DecisionEngine default. It is not fitted on Development outcomes. |

`validation_loss` is the mean decision loss and excludes cost. `mean_loss` adds `resource_weight * estimated attempt cost`. The budget is a feasibility cap in milliseconds. It is not a third penalty. Raising the uncertainty weight makes decisive methods look better on loss even when they make more errors. Moving the threshold changes acceptance, coverage, and loss for every method. The comparison is valid only if all three methods use the same signed values.

## Resource configuration

SYNTHETIC / CONFIGURATION-SENSITIVITY ANALYSIS, in `evaluation/docs/experiment3_resource_sensitivity.md`. It is not an empirical result. Frozen means, 120 non-warmup attempts each, calibration `cc7e7ca8882f602b9854bf21b80b8a7bf70f6c70d05ccd12787322a84a12477d`, unit milliseconds:

| Verifier | Mean ms |
|---|---:|
| semantic | 70.4728633359385 |
| evidence | 107.93551665459138 |
| rule | 0.09707332161876063 |
| confidence | 14925.820978323463 |

Confidence is about 98.8% of the four-mean sum, 15104.326431635613 ms. That sum is the cost of calling every verifier once. The calibration freeze does not authorize budget selection. No loss-per-millisecond coefficient can be derived from those times, and the synthetic fixture scores verifiers `a`, `b`, and `c`, not this roster.

Coefficients are loss per millisecond. None is approved.

| Coefficient | Value | What the grid showed |
|---|---:|---|
| Zero | 0 | Allowed by `LossConfiguration.resource_weight`. Decision loss is unmixed with cost. Every feasible team is optimal when decision loss does not depend on the team. |
| Low | 1.3399597937725295e-05 | 0.2 / confidence mean. One confidence attempt costs one uncertain decision. The gap versus the cheapest team is about 0.199, so avoiding one uncertain decision can still justify confidence. |
| Moderate | 6.699798968862647e-05 | 1.0 / confidence mean. One confidence attempt costs one false acceptance. The gap is about 0.995, so only a near-complete error reduction would pay for confidence. |
| High | 0.2 / semantic mean | A confidence attempt costs about 42. Confidence's penalty exceeds every loss on the proposed scale, so a permissive budget would not put confidence in the cost-augmented optimum. |

Budgets are enumerated team costs, in milliseconds. None is approved. `0.1/budget` is rejected by the settings proposal because the penalty would change with the budget.

| Budget | Value (ms) | Feasibility |
|---|---:|---|
| Restrictive | 70.56993665755726 | Cheapest pair, rule + semantic. At the hard floor of 3, no team is feasible. |
| Moderate | 178.50545331214863 | The only confidence-free triple. Confidence is infeasible at both participant floors. |
| Confidence boundary | 14996.39091498102 | Cheapest triple that includes confidence. |
| Permissive | 15104.326431635613 | Every team, including the full roster. This is the four-mean sum used as a feasibility threshold, not as a selected protocol budget. |

The coefficient does not change which teams are feasible. The budget and the participant floor do. Any positive coefficient keeps only the cheapest feasible team unless that team's decision loss is worse by more than the gap above. Floor 2's cheapest team is rule + semantic. Floor 3's cheapest team is semantic + evidence + rule. Those floors are the selector defaults. Experiment 3 has not approved a floor.

Decision loss and the resource penalty stay separate. The fixture's own 0.1 weight is not applied to milliseconds.

### Review candidate, not an approval

For review only, the candidate is the low coefficient and the permissive budget:

- `resource_coefficient` = `0.2 / 14925.820978323463` = `1.3399597937725295e-05` loss per millisecond
- `verifier_budget` = `15104.326431635613` milliseconds, shared by all three methods

Why this pair, and why it is not approved: the high coefficient lets resource cost dominate decision loss; the moderate coefficient makes confidence worth fielding only to avoid almost a whole error; zero does not price confidence at all. The restrictive cap is infeasible at the hard floor. The moderate cap bans confidence for every method and confounds aggregation with roster availability. The permissive cap is the smallest cap that keeps every team feasible, so the aggregation comparison is not a hidden roster ban. It is still the four-mean sum. The freeze does not authorize it. The lead may instead write the confidence-boundary budget if a tighter cap that still admits one confidence team at floor 3 is preferred. Either choice has to be written by the lead. This memo does not write it into `approved_settings`.

The same numbers are stored, with `approved: false`, as `review_candidate` on `experiment3_resource_approval_record.json`. The signable fields `resource_coefficient_loss_per_ms` and `verifier_budget_ms` are null.

## Reputation

`ReputationManager` is the only implementation. With prior alpha 1 and prior beta 1:

```
alpha = 1 + successes
beta = 1 + failures
reported reputation = round(alpha / (alpha + beta), 6)
```

With zero observations the reported value is 0.5. There is no decay, no EWMA, and no confidence-weighted counts. The prior is uncalibrated. Development labels are not a reputation source. History may be used only after an approved update rule, which does not exist. No snapshot was written.

The proposal `5eac889b0904957b2f926dc65a9b10531acd9b1514af0e953b9c01f395d80bad` asks the lead to accept that cold start. Signing it would allow a prior-only snapshot. It would not create observations. The input record remains `PENDING_APPROVAL` and cannot approve itself.

## Dependency assumptions

`experiment3_dependency_configuration.json` (`structural_shared_resource_v1`) is a configured description: rule alone, semantic and evidence on the embedding model, evidence and confidence on the NLI model, confidence also on an unpinned generator. `empirical_evidence` is `none`. `measured_dependence_claim` is false. Approving that file would not be a measured-correlation claim.

The specification's heatmap still names `provisional_shared_unknown_v1`. Both files are unsigned. This package does not rewrite either hash. The synthetic two-group registry is a controlled assumption. It is not an empirical alternative. Because evidence sits in two configured groups, the game's `DependencyRegistry` would connect semantic, evidence, and confidence into one component. That collapse was not written into the configuration.

## Limitations

- Each eligible group pairs one `VERIFIED_CORRECT` candidate with one `SYNTHETIC_INCORRECT` candidate. The incorrect class is synthetic by construction. It is not a naturally occurring error sample.
- Unresolved labels are excluded from binary correctness and are not imputed. Execution failures are reported and are not treated as correct or incorrect.
- The cost calibration is 120 non-warmup attempts per verifier on the exploratory Development measurement run. It does not establish that those means will match attempt times on the 372-group collection. Confidence dominates the sum, so a small change in its mean moves every budget that includes it.
- There are no empirical Experiment 3 result rows. `empirical/results.json` is `NOT_COLLECTED`. The synthetic fixture and the sensitivity grid must not be cited as Development effects.
- Verifier weight hashes, the rule version hash, the collection seed, hardware, and the software lock are `UNKNOWN` or null. The collection configuration still says the cost unit is unnamed and `cost_measurements_available` is false. That file was not edited, because the unsigned collection authorization binds its hash.
- Leakage clearance is `NOT_CLAIMED`. The corpus freeze status is `NOT_FROZEN`.

## Approval workflow

Every row below is the working-tree SHA-256. Existing artifact bytes were not rewritten except for two new unsigned templates and the manifest that lists them. The cost-calibration freeze remains Vasavi's freeze of the cost measurements only. It is not an Experiment 3 protocol signature. Eligibility remains an eligibility approval only.

| Role | Path | Version | Status | SHA-256 | Depends on | Signer |
|---|---|---|---|---|---|---|
| Protocol | `evaluation/config/experiments/experiment3_specification.json` | `experiment3_protocol_specification_v1` | proposed | `f64b47cfe206548c57f60d48ebf2404dacce65b46ed05e4210fe68fb8250f529` | eligibility manifest, settings proposal | research lead |
| Loss settings | `evaluation/config/experiments/experiment3_settings_proposal.json` | `experiment3_settings_proposal_v1` | proposed | `77d773fa7aad43bc0591244b64b78f37dd1142f2a9628d89ead7ad9847d8665f` | none | research lead |
| Settings template | `evaluation/config/experiments/approvals/experiment3_settings_approval_record.json` | `experiment3_settings_approval_record_v1` | proposed | `32d0999200929977d37216be6c08552343aa6fd856428d6ec617301219241de9` | settings proposal | research lead |
| Protocol template | `evaluation/config/experiments/approvals/experiment3_protocol_approval_record.json` | `experiment3_protocol_approval_record_v1` | proposed | `4dcf0fb8af101294c297b3c7c17d033f597de9ea1c73a2f9aa9a28ecf1420e48` | specification | research lead |
| Resource proposal | `evaluation/experiments/experiment3/approval_package/resource_configuration_proposal.json` | `experiment3_resource_configuration_proposal_v1` | proposed | `9393c6b0caf82778670b971d3c4e5ee5b0c8cbf9b01b34a7c244f5f8f94a498c` | cost-calibration freeze | research lead |
| Resource template | `evaluation/config/experiments/approvals/experiment3_resource_approval_record.json` | `experiment3_resource_approval_record_v1` | proposed | `c4f847ced524d703d971b053277511fe7330a84cf57d968c5cd9a9a87125e1dd` | resource proposal | research lead |
| Resource declaration | `evaluation/config/research_v1/resource_config.json` | `research_v1_resource_config_v1` | proposed | `96e7adab02539f8bcf12834e73df34590e6daa729c0f4db28b81152b1d6a11cd` | corpus file | research lead |
| Calibration | `artifacts/research-v1-development-cost-calibration-v1/calibration.json` | `verifier_cost_calibration_v1` | prepared | `7fbfe418c0c65c3782628ab5117b773f2fc4c8312c33d769934f76d2ff61a7f3` | measurements | none for this protocol |
| Measurements | `artifacts/research-v1-development-cost-calibration-v1/measurements.json` | `verifier_measurements_v1` | prepared | `514e39a1422a1ef0b3846e02f010e6edc4ab1a1aec89e1605e82f03199836a94` | none | none for this protocol |
| Calibration provenance | `artifacts/research-v1-development-cost-calibration-v1/calibration-provenance.json` | `research_v1_development_calibration_input_provenance_v1` | prepared | `938f4f1fd4b803004cf55c710b41a9d438bc440db5fa11c352afb497144cf9a0` | measurements | none for this protocol |
| Calibration freeze | `artifacts/research-v1-development-cost-calibration-v1/freeze-manifest.json` | `research_v1_development_cost_calibration_freeze_v1` | approved for that freeze only | `cba1b8861eacdffd77e0e97865eb24bb45ff723a06d174988f0b0c527a3ada72` | calibration, measurements, provenance | not an Experiment 3 signature |
| Reputation proposal | `evaluation/experiments/experiment3/approval_package/reputation_initialization_proposal.json` | `experiment3_reputation_initialization_proposal_v1` | proposed | `5eac889b0904957b2f926dc65a9b10531acd9b1514af0e953b9c01f395d80bad` | reputation inputs | research lead |
| Reputation template | `evaluation/config/experiments/approvals/experiment3_reputation_approval_record.json` | `experiment3_reputation_approval_record_v1` | proposed | `066cbf7af0fd2faebb93052368aff49d151d2b5923701f2a41e068da0ebed96f` | reputation proposal | research lead |
| Reputation inputs | `evaluation/config/experiments/experiment3_reputation_policy_inputs.json` | `experiment3_reputation_policy_inputs_v1` | proposed | `19c0032a0e5556d9ccdf2b9a589582536e00c1ed493acca85e43ca2cbf0a67c7` | none | research lead |
| Dependency configuration | `evaluation/config/experiments/experiment3_dependency_configuration.json` | `experiment3_dependency_configuration_v1` | proposed | `c7dc14f867bedd8345184869fa8c10f7fabb554d843ed44df4d8606e993d7c2d` | none | research lead |
| Dependency template | `evaluation/config/experiments/approvals/experiment3_dependency_approval_record.json` | `experiment3_dependency_approval_record_v1` | proposed | `72a4b15bd709bb199a97201a641862dc021197d746fbea2ee8dd108d742e50df` | dependency configuration | research lead |
| Corpus file | `evaluation/artifacts/person1/development_evidence_corpus_v1/corpus.json` | corpus bytes, no record version | prepared | `f76c6ce19661e2fdae44f87f126825d8efc4b3edb3fa1b381d0130c7f82e5e2b` | none | research lead, via the corpus approval |
| Corpus package | `evaluation/config/experiments/experiment3_corpus_approval_package.json` | `development_evidence_corpus_approval_package_v1` | proposed | `7c57f6b29ce681a74767d579d8fb8d82c4f65dd85c5373c8423cd171ee79b72f` | corpus file | research lead |
| Corpus template | `evaluation/config/experiments/approvals/experiment3_corpus_approval_record.json` | `experiment3_corpus_approval_record_v1` | proposed | `f840ca32639b4a37fa3a4f410be9f4a47431ab9ad23453b360161203a268491b` | corpus file | research lead |
| Collection configuration | `evaluation/config/experiments/experiment3_collection_configuration.json` | `experiment3_development_collection_configuration_v1` | proposed | `6f539d60464d684e9633b102f8b06ae6f598c5c4035e0d34f7e8a8d8be3adcda` | eligibility manifest, corpus file | research lead, after Person 2 fills hashes, seed, and cost id |
| Collection template | `evaluation/config/experiments/approvals/experiment3_collection_authorization_record.json` | `experiment3_collection_authorization_record_v1` | proposed | `c99f0d35b7c2cfed4e04d1ed95e00955f2fcd5d94b9d7aa0ea47bc8a1dfc5fd6` | collection configuration | research lead |
| Verifier configuration | `evaluation/config/research_v1/verifier_config.json` | `research_v1_verifier_config_v1` | proposed | `740319254a30711ecb36f6a1e62cd865896fc264d4eaebf11fda9d10a0db3b97` | none | Person 2 supplies hashes; research lead accepts them in the collection authorization |
| Runtime manifest | `evaluation/config/research_v1/environment_manifest.json` | `research_v1_environment_manifest_v1` | proposed | `7afb2c1ea39588920fde15eb73f033f90840fd3c14b330aa1cac5175001559e7` | none | Person 2 records the runtime; research lead accepts the collection authorization |
| Development eligibility | `evaluation/artifacts/person1/research_v1_exploratory_eligibility_approved_v1/eligibility_manifest.json` | `research_v1_exploratory_eligibility_approved_v1` | approved for eligibility only | `1ebb4357d599a52d1c1fc8d8951ab39fa6992e846cf997d9e588820c87cbe731` | none | not a collection signature |

A signed record counts only when `status`, `decision`, and `approved` are the approved values and `approver` and `approval_date` are present. `artifact_sha256` must equal the current file hash. A stale hash blocks the package. The resource record's coefficient and budget must equal `approved_settings` on the protocol record. The collection authorization binds the collection configuration hash. The reputation approval binds the initialization proposal hash. The protocol approval binds the specification hash.

## Pending research decisions

The lead still has to decide, in writing, on a signed record:

1. Accept or replace false acceptance 1.0, false rejection 1.0, uncertainty 0.2, and threshold 0.55.
2. Accept, replace, or reject the review candidate: low coefficient `1.3399597937725295e-05` loss per ms, permissive budget `15104.326431635613` ms. Write the chosen numbers into both the protocol `approved_settings` and the resource approval. Do not use `0.1/budget`.
3. Accept suppression as unavailable, bootstrap 2000 / 0.95 / seed `20261113`, and the 372-group census with no imputation.
4. Sign the corpus record against `f76c6ce19661e2fdae44f87f126825d8efc4b3edb3fa1b381d0130c7f82e5e2b` and set `freeze_status` to `FROZEN` only on that signed record.
5. Sign `structural_shared_resource_v1` without calling it measured dependence, or replace the file and bind the new hash.
6. Accept or reject the cold-start reputation proposal. Do not train on Development labels.
7. Have Person 2 fill verifier weight hashes, the rule version hash, and the collection seed. Set `cost_measurements_available` to true and `cost_measurement_id` to `cc7e7ca8882f602b9854bf21b80b8a7bf70f6c70d05ccd12787322a84a12477d` only if that calibration is the one to use. Then sign collection authorization against the updated collection-configuration hash.

## Collection gate

On this checkout `assess()` returns `READY_FOR_APPROVAL`. `collection_started` is false. `blockers` is empty. Collection is withheld because protocol settings are unsigned, the resource coefficient and budget are unsigned, the corpus is not signed and frozen, the dependency approval is unsigned, collection is not authorized, verifier hashes are incomplete, the seed is missing, reputation initialization is not approved, and the collection configuration does not bind a cost measurement.

The gate blocks a missing record, an unsigned record that claims approval, a stale `artifact_sha256`, a Final Test path, a self-approved settings proposal, a self-approved reputation input file, and a signed resource record whose numbers differ from the protocol settings. It does not open collection while verifier hashes, the seed, the cost measurement id, the resource numbers, or the reputation approval are missing. `UNKNOWN` hashes do not by themselves make the unsigned package internally inconsistent. They do keep collection closed.

`READY_FOR_DEVELOPMENT_COLLECTION` does not call verifiers. `empirical_runner.py` still stops while any blocker remains.

## How to authorize empirical execution

1. Review this memo, `experiment3_approval_decisions.md`, and `experiment3_resource_sensitivity.md`.
2. Write the accepted loss, threshold, bootstrap settings, coefficient, and budget into `approved_settings` on a signed protocol approval whose `artifact_sha256` is `f64b47cfe206548c57f60d48ebf2404dacce65b46ed05e4210fe68fb8250f529`, or into a new specification whose hash is then recorded. Leave the proposal file unapproved.
3. Write the same coefficient and budget into `experiment3_resource_approval_record.json`, set its signature fields, and keep `artifact_sha256` equal to the resource proposal hash.
4. Sign the corpus approval against the corpus file hash and set freeze status `FROZEN` on that signed record and on the corpus package together.
5. Sign the dependency approval against `c7dc14f867bedd8345184869fa8c10f7fabb554d843ed44df4d8606e993d7c2d`, or against a replacement file. Do not mark `empirical_evidence` as recorded unless paired failure observations exist.
6. Sign the reputation approval against `5eac889b0904957b2f926dc65a9b10531acd9b1514af0e953b9c01f395d80bad` if the cold start is accepted.
7. Fill verifier hashes and `environment.random_seed` on the collection configuration. Set `cost_measurements_available` true and `cost_measurement_id` to the calibration id above if that bundle is adopted. Recompute the collection file hash. Sign `experiment3_collection_authorization_record.json` with that hash and `collection_authorized: true`.
8. Run `python -c "from evaluation.experiments.experiment3.collection_gate import collection_allowed; import json; print(json.dumps(collection_allowed(), default=str)[:2000])"`. Proceed only if `status` is `READY_FOR_DEVELOPMENT_COLLECTION` and `reason` is null. That command does not start verifiers.
9. Only after that status, run the Development collector as a separate explicit step. Do not point it at Final Test labels. Do not treat `evaluation/experiments/experiment3/synthetic/` as recordings.

Recompute the manifest with `python evaluation/experiments/experiment3/approval_inventory.py` after any signed file changes, then review the diff. A manifest that sets `approved` or `collection_authorized` is rejected.
