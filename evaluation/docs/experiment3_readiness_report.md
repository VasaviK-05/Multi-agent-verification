# Experiment 3 readiness report

Empirical Experiment 3 was not run. Final Test labels were not opened. The working-tree corpus matches the recorded LF bytes. The corpus is not approved or frozen. Collection is not authorized. This chat is not a research-lead approval. On 2026-11-13 the collection gate returned `READY_FOR_APPROVAL` and `collection_started` false.

## Current status

`assess()` returns `READY_FOR_APPROVAL`. `protocol_complete` is true. Analysis blockers are the pending statistical settings and the absent empirical result rows. Empirical recordings are 0, costs are unavailable, and Person 3 observations are 0. Development collection is not authorized.

`evaluation/tests/test_experiment3_execution_gate.py`, `tests/test_experiment3_prerequisites.py`, `tests/test_experiment3_visualizations.py`, and `tests/test_research_readiness.py`: 45 passed. `tests/test_experiment3_synthetic.py` cannot be collected. `app.game.dependencies` does not define `controlled_two_group_registry`, `shared_unknown_registry`, or `CONTROLLED_SYNTHETIC_ASSUMPTION`, and the preserved runner bytecode cannot be executed. The existing `synthetic/results.json` was not overwritten.

## Proposed settings

The specification keeps unresolved fields null. Recommendations live only in `evaluation/config/experiments/experiment3_settings_proposal.json`, each marked `PROPOSED_PENDING_APPROVAL`.

| Parameter | Recommendation | Why it is offered |
|---|---|---|
| False acceptance loss | 1.0, range 1 to 5 | Matches the uncalibrated pilot, which treats a false acceptance as equal to a false rejection. A higher weight favors rejection. |
| False rejection loss | 1.0, range 1 to 5 | Keeps the other error from being free. Raising it favors acceptance and can reverse a paired difference. |
| Uncertainty loss | 0.2, range 0.1 to 0.5 | Charges abstention less than an error. A larger penalty can make decisive methods look better on loss. |
| Resource coefficient | No number | Person 2 has not named a cost unit. A positive coefficient below the false-acceptance weight per attempt is the open range. This coefficient decides whether cost or errors dominate. |
| Decision threshold | 0.55, range 0.5 to 0.6 | Current uncalibrated DecisionEngine default. Every method must use the same approved threshold. |
| Verifier budget | No number | One matched budget in Person 2 units. Experiment 2's three levels are a different question. Different budgets would confound aggregation with resources. |
| Suppression mode | unavailable | The existing attack enumerator records suppression as unavailable. |
| Bootstrap resamples | 2000, range 1000 to 5000 | Percentile endpoints for a few hundred groups change little past this count. The mean does not depend on the count. |
| Confidence level | 0.95, range 0.9 to 0.95 | Conventional reporting level, fixed before outcomes exist. A lower level makes intervals narrower. |
| Bootstrap seed | 20261113 | Preparation date, used only to order resamples. |
| Sample size | All 372 approved groups | The approved roster after quarantine. The older count of 387 is obsolete. This is a census, not a power calculation. |
| Matched conditions | Groups, reports, reputation, costs, loss, threshold, attacks, and budget | Only aggregation, and separately the dependency configuration, may change between cells. |
| Attacks | clean, forced support, forced rejection, confidence inflation, suppression unavailable | Existing report-corruption columns. |
| Missing data | Exclude unresolved labels from binary correctness. Count missing pairs and failed executions. Do not impute. | Imputation could create a difference where a method did not run. |

## Corpus approval requirements

The corpus approval template is `evaluation/config/experiments/approvals/experiment3_corpus_approval_record.json`. It is `NOT_AN_APPROVAL`. Approver and date are empty. Freeze status is `NOT_FROZEN`.

The record is ready to cite `development_evidence_corpus_v1`, corpus SHA-256 `f76c6ce19661e2fdae44f87f126825d8efc4b3edb3fa1b381d0130c7f82e5e2b`, index `idx-c1dc6980912b`, the preparation report, and `evaluation/docs/experiment3_corpus_provenance_reconciliation.md`. The corpus has 1,844 unique sorted articles. Index bytes were not changed. Repository attributes keep LF for the restored corpus. Limitations that stay on the record: one retrieval miss, gold-answer strings in 177 of 185 paragraph sets, an unknown embedding-weight snapshot, GSM8K marked not applicable, and leakage not claimed.

A freeze is valid only when a signed corpus approval sets `freeze_status` to `FROZEN` and the corpus package `frozen` flag agrees. This package does not freeze the corpus.

## Dependency design

The declared model is `structural_shared_resource_v1`. Rule stands alone. Semantic and evidence share the embedding model. Evidence and confidence share the NLI model. Confidence also depends on an unpinned generator. These groups are shared-resource risks, not measured correlations. The empirical heatmap is not estimable until paired failure recordings exist.

No paired failure recording exists. The decision package does not claim measured dependence. If the heatmap is required before such recordings exist, the research lead can approve two labeled stress tests: each verifier in its own group, and semantic plus evidence together with rule and confidence separate. Those rows are hypothetical. The synthetic two-group fixture remains a scoring check. The recommendation is in `evaluation/config/experiments/experiment3_dependency_decision.json`.

## Approval templates

These files require an approver role, a date, the artifact identifier, the artifact SHA-256, a decision, a scope, and conditions. None of those identities or dates is filled.

1. `evaluation/config/experiments/approvals/experiment3_protocol_approval_record.json` — specification `f64b47cfe206548c57f60d48ebf2404dacce65b46ed05e4210fe68fb8250f529`.
2. `evaluation/config/experiments/approvals/experiment3_corpus_approval_record.json` — corpus `f76c6ce19661e2fdae44f87f126825d8efc4b3edb3fa1b381d0130c7f82e5e2b`.
3. `evaluation/config/experiments/approvals/experiment3_dependency_approval_record.json` — dependency configuration `39d94f453f199c51d9a387c71d4f6fe2bf8cbe6bd63c5cac1267d79a1a8f0a34`.
4. `evaluation/config/experiments/approvals/experiment3_collection_authorization_record.json` — collection configuration `089b99427a8a02b92ad03d98e2a88a525850484d3d90b8079aeca29538294811`.

The validator accepts a record only when its status, decision, and approved flag say approved, the approver and date are present, and the artifact hash matches the file. A proposal file cannot advance the status. An inline approved flag without that record blocks.

## Approval sequence

1. Research lead accepts or revises the proposed settings, copies the accepted values into the protocol approval's `approved_settings`, and signs that record against the specification hash. That signature freezes the protocol.
2. Research lead signs the corpus record against the corpus hash and sets the freeze only in that same signed record.
3. Research lead signs the dependency record, stating whether the heatmap stress tests are in scope. That signature is not a measured-dependence claim.
4. Research lead signs the collection authorization only after the three records above are signed. Person 2 then supplies the unknown collection fields. `assess()` reaches `READY_FOR_DEVELOPMENT_COLLECTION` only when the authorization is signed, the corpus freeze agrees, verifier hashes are known, and the random seed is set.
5. Person 2 collects Development recordings and costs. Person 3 exports reputation observations. `assess()` reaches `READY_FOR_EMPIRICAL_EXPERIMENT` only then. Empirical figures wait for `READY_FOR_EMPIRICAL_EXPERIMENT_ANALYSIS`.

## Person 2

The collection file leaves model snapshot hashes, prompt hashes, hardware, software, code revision, random seed, timeout, retries, warmup, and the cost unit as unknown. Person 2 fills those after authorization and then records Development attempts with `related_group_id`, benchmark, attack, verifier reports, costs, execution status, decision, coverage, uncertainty, configuration id, and provenance. Current code defaults were not copied in as historical settings.

## Person 3

Reputation inputs remain `PENDING_PERSON3` with zero observations. Person 3 still chooses the reputation source, initialization, update rule, and smoothing, then exports a policy after the recordings and the approved settings exist. The synthetic fixture is not that source.

## Research-lead decisions still required

Accept or replace each proposed loss weight, the uncertainty loss, the decision threshold, suppression mode, bootstrap count, confidence level, and seed. Choose a resource coefficient and one matched verifier budget after Person 2 names the cost unit. Confirm the 372-group census, the matched conditions, the attack list, and the missing-data policy. Approve and freeze the corpus with its stated limitations. Approve the structural shared-resource groups for the aggregation ablation and decide whether hypothetical heatmap rows are in scope. Approval is not a measured-dependence claim. Authorize collection only after those approvals.

## Synthetic fixture

The fixture under `evaluation/experiments/experiment3/synthetic/` is `SYNTHETIC`. On hand-built reports, `shared_unknown` worst-case losses were joint 0.4, fixed reputation 0.4, and fixed dependency 1.2. The controlled two-group assumption brought all three worst-case losses to 0.4, while clean losses still differed. Those figures validate the scoring machinery. They are not measured verifier dependence, cost, or robustness.

## Required figures

The grouped bars compare the three aggregation methods on validation loss and decision coverage under matched conditions. The paired-difference plot shows ablation loss minus full-game loss, with zero meaning identical loss. The dependency heatmap is not estimable from current empirical inputs. A synthetic two-group figure can be drawn only with the `SYNTHETIC` label.
