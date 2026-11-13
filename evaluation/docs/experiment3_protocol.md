# Experiment 3 protocol

Status: `PENDING_APPROVAL`. Readiness is `READY_FOR_APPROVAL`. The protocol is not approved, not frozen, and collection is not authorized. The empirical experiment has not been run.

Specification: `evaluation/docs/experiment3_protocol_specification.md` and `evaluation/config/experiments/experiment3_specification.json`. Configuration pointers: `evaluation/config/research_v1/verifier_config.json`, `evaluation/config/research_v1/resource_config.json`, and `evaluation/config/research_v1/environment_manifest.json`.

## Questions

1. What is the effect of aggregation when reports, questions, reputation inputs, costs, loss, coverage rules, and attacks stay fixed?
2. What is the effect of the declared dependency structure on which verifiers an attack can target together?

The synthetic fixture under `evaluation/experiments/experiment3/synthetic/` is `SYNTHETIC`. It is not an empirical result.

## Population

Approved Development eligibility: 744 candidates, 372 groups, GSM8K 187, HotpotQA 185. Body SHA-256 `f2cc0fd108b961bf4795767df4f90e92d7fa0f418ef9865d0206f32d7b45282d`. Final Test is prohibited. Unresolved labels are excluded from binary correctness and are not imputed.

## Methods and dependency

Aggregations: `full_minimax`, `fixed_reputation_weighted`, `fixed_dependency_group`.

The dependency configuration is `structural_shared_resource_v1`, status `PROVISIONAL`, empirical evidence `none`. Rule is alone. Semantic and evidence share the embedding model. Evidence and confidence share the NLI model. Confidence also depends on an unpinned generator. These groups are shared-resource risks, not measured correlations. The empirical heatmap stays not estimable until paired failure recordings exist.

## Conditions

Proposed attacks are clean, forced support, forced rejection, confidence inflation, and suppression unavailable. Loss weights, the resource coefficient, the decision threshold, the verifier budget, and the bootstrap settings remain pending in `evaluation/config/experiments/experiment3_settings_proposal.json`. The coefficient and the budget have no recommended number.

## Recordings and stop

Person 2 recordings and Person 3 reputation observations are absent. Do not collect them, and do not score Final Test, until the protocol, corpus, dependency, and collection records are signed.
