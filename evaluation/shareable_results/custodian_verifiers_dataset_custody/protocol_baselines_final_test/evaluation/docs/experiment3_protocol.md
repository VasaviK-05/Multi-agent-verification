# Experiment 3 protocol

Status: selected research configuration. Development collection completed under the research-lead instruction recorded in `evaluation/experiments/experiment3/execution_configuration.json`. The completed grid is 15,624 empirical cells. Independent human approval and other contributors' signatures were not obtained. This document is not a signature.

The coefficient and verifier budget are a selected research configuration. They are not empirically optimized parameters.

Specification file: `evaluation/config/experiments/experiment3_specification.json`. That file is unchanged and still has unsigned proposal fields. The execution configuration is the record that binds the values used for collection.

## Questions

1. What is the effect of the aggregation method when verifier reports, questions, the reputation prior, costs, loss, and attacks stay matched?
2. What is the effect of the declared dependency structure on which verifiers an attack can move together?

Synthetic fixtures under `evaluation/experiments/experiment3/synthetic/` and the sensitivity grid under `evaluation/experiments/experiment3/sensitivity/` stay `SYNTHETIC`. They are not empirical findings.

## Population

Approved Development eligibility manifest `evaluation/artifacts/person1/research_v1_exploratory_eligibility_approved_v1/eligibility_manifest.json`.

- Dataset `research_v1_exploratory_v1`.
- 372 groups: GSM8K 187, HotpotQA 185.
- 744 candidates, two per group: one `VERIFIED_CORRECT` and one `SYNTHETIC_INCORRECT`.
- Unresolved candidates and ineligible groups are excluded.
- The manifest still has `collection_authorized: false`, `recording_authorized: false`, and `final_test_authorized: false`. Those flags were not edited. Execution authority is the separate research-lead record, not a change to this manifest.
- Complete-file SHA-256 `1ebb4357d599a52d1c1fc8d8951ab39fa6992e846cf997d9e588820c87cbe731`.
- Question text and candidate answers are read only from `evaluation/datasets/research_v1_exploratory/research_v1_exploratory_v1/development_verifier_inputs.jsonl`, joined to eligible candidate ids. Sealed Final Test labels are not opened.

`SYNTHETIC_INCORRECT` candidates are generated negatives. They are not human-verified incorrect answers. No human-verified incorrect candidate is in the approved population.

## Decision configuration

- False acceptance loss: 1.0
- False rejection loss: 1.0
- Uncertainty loss: 0.2
- Decision threshold: 0.55
- Suppression: unavailable, and suppression is not a collected condition
- Decision loss is `outcome_loss`: 0 for a correct accept or correct reject, otherwise the matching loss above. Resource penalty is reported separately as coefficient times estimated team cost.

## Resource configuration

- Coefficient: `1.3399597937725295e-05` loss per millisecond. This is 0.2 divided by the frozen confidence mean. It is a scale choice, not a fitted utility.
- Budget: `14996.39091498102` milliseconds. This is the estimated cost of the cheapest size-3 team that contains confidence (confidence, semantic, and rule) under `enumerate_strategies` and the frozen means. It is the confidence-entry boundary from the sensitivity grid, not a measured optimum.
- Calibration id: `cc7e7ca8882f602b9854bf21b80b8a7bf70f6c70d05ccd12787322a84a12477d`.
- Attempt costs used for feasibility are the frozen non-warmup means. They are not remeasured during this run.
- Participant floor: 2, the selector default for easy and medium items. Experiment 3 has no separate approved floor. At this budget the full four-verifier roster is infeasible. Teams whose estimated cost exceeds the budget are excluded.
- Expected coverage uses a uniform capability label so coverage rules do not remove additional teams. That is a configuration assumption, not an empirical capability measurement.

## Reputation

- `ReputationManager` prior `Beta(1, 1)`, reported mean 0.5.
- No decay.
- Approved historical observations: 0. None were manufactured.
- The planning snapshot is that prior. Development outcomes are not written back into reputation before the policy is solved.

## Dependency

Configuration `structural_shared_resource_v1` (`evaluation/config/experiments/experiment3_dependency_configuration.json`, SHA-256 `c7dc14f867bedd8345184869fa8c10f7fabb554d843ed44df4d8606e993d7c2d`).

The groups are structural assumptions: rule alone; semantic and evidence share the embedding model; evidence and confidence share the NLI model; confidence also depends on the generator. `empirical_evidence` is `none`. `measured_dependence_claim` is false.

`DependencyRegistry` accepts only `unknown_treatment = shared_unknown` and merges verifiers that share a dependency. With these groups, semantic, evidence, and confidence form one component and rule stays separate. That merge is a consequence of the overlap, not a new measurement.

## Conditions and methods

Conditions: clean, forced support, forced rejection, confidence inflation.

The four kinds are clean, forced support, forced rejection, and confidence inflation. Suppression stays unavailable. `enumerate_attacks` still lists suppression; the executor drops those columns.

`structural_shared_resource_v1` has two failure components, so each non-clean kind is one column per component rather than one column for the whole roster. The cell count is 744 candidates × 7 attack columns × 3 methods = 15,624. The 8,928 count would apply only if every non-clean kind corrupted all four verifiers together. That is not the structural attack grid. Clean has no members. The other columns are the merged component (semantic, evidence, confidence) and the rule component.

Methods, solved with `solve_minimax` on the empirical mean of decision loss plus resource penalty:

- `full_minimax`
- `fixed_reputation_weighted`
- `fixed_dependency_group`

Fixed methods use `restricted_matrix` to keep one aggregation. The reported decision for each cell is the decision of the modal strategy in that method's solved distribution. The mixture and game value are stored with the policy.

## Statistics

- Paired bootstrap over question groups, not candidate rows.
- 2,000 resamples.
- 95% interval.
- Seed `20261113`.
- Unresolved labels are excluded and not imputed.
- A confidence interval is not a significance claim.

## Authorization

Experiment 3 Development execution is authorized by the research lead under the documented session instruction. The execution configuration records that independent human approval and contributor signatures were not obtained, and that no signature was fabricated. Changing an `approved` flag does not satisfy the readiness check. The check requires the authorization statement, the selected values, the calibration binding, the eligibility roster, and the dependency file's recorded lack of measured evidence.
