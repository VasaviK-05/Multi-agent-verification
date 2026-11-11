# Person 1 compliance matrix and validation summary

Executed 2026-11-11 on Git HEAD `13174aa` plus the uncommitted Person 1 changes listed below. Status values: PASS (implemented and verified), FAIL, BLOCKED (cannot be completed by Person 1 without an external input), NOT APPLICABLE.

## Commands and results

| Command | Result |
|---|---|
| `python -m evaluation.data_preparation.person1_validation generate` | wrote `evaluation/datasets/person1/research_v1_person1_v1/` (version `research_v1_person1_v1`); 17 PASS, 3 BLOCKED, 0 FAIL |
| `python -m evaluation.data_preparation.person1_validation validate` | identical recomputation: 0 stored-hash mismatches, 0 recomputed-output mismatches, 0 input changes, generator unchanged; exit 0 |
| `pytest tests/test_person1_validation.py` | 12 passed |
| `pytest` on `test_game_offline`, `test_game_research`, `test_game_foundation`, `test_game_build`, `test_game_completion`, `test_pilot_abstention_contract`, `test_final_test_workflow`, `test_research_dataset_pipeline`, `test_development_feasibility_pilot`, `test_person1_validation` | 315 passed |
| `python -m evaluation.data_preparation.final_test_workflow readiness --config evaluation/config/protocol_readiness.yaml --manifest …/manifest.json` | exploratory LIMITED, confirmatory BLOCKED (every approval item NOT APPROVED; policy fitting BLOCKED) |
| SHA-256 of the result files and the custodian label file, before and after | identical (not overwritten) |

Validation receipt: `evaluation/datasets/person1/research_v1_person1_v1/manifest.json` (generator SHA-256 `2a590b6d…56a0`; `validation_summary.json` SHA-256 `adcce2fb…be2d`).

> **Correction (2026-11-11, later the same day).** The Final Test leakage and isolation rows below were marked PASS on the basis of exact comparisons against research_v1 History and Development only. A content-level audit against every exposed dataset, Development file, baseline output and verifier output found that 807 of the 2,638 provisional Final Test groups (GSM8K 500, HotpotQA 307) had previously been exposed. Those rows are now FAIL, and the provisional Final Test is retired. The frozen `person1_validation` output is unchanged and still reports PASS for its narrower check. See `final_test_contamination_audit.md` and `experiment1_readiness_report.md`.

## Step 1 — research objective

| Requirement | Status | Evidence |
|---|---|---|
| Central claim and primary/supporting outcomes documented | PASS | `research_objective.md` § Central claim, § Primary and supporting outcomes |
| Loss implementation verified | PASS | `outcome_loss`, `summarize`, `validation_loss`; tests listed in `research_objective.md` § Code verification |
| Zero coverage → selective risk undefined | PASS | `summarize` returns `None`; `test_mixed_metrics_are_expectations_and_zero_coverage_risk_undefined` |
| Mixed-policy probabilities | PASS | probability-weighted, sums to 1 per example; `ResearchPolicy.validate_distribution` |
| Worst-case computation | PASS, with a finding | max over attacks of `mean_loss`, which is **cost-augmented**; primary-outcome cost treatment is a pending decision |
| Coverage and minimum-contributor constraints | PASS | `enumerate_strategies`, `finalize_decision`; `test_pilot_abstention_contract.py`, `test_minimum_budget_and_coverage_constraints` |
| Budget feasibility | PASS (mechanism) / BLOCKED (values) | `test_greedy_cannot_relax_budget_or_minimum`; budget values unapproved |
| Four corruption scenarios | PASS | `Attack.kind` literal; suppression/inflation tests |
| Dependency and failure assumptions | PASS (documented) | `DependencyRegistry`; the proposal's shared-unknown assumption is flagged as unverified |
| Comparison machinery mapped | PASS | `comparison.py:METHODS` mapping table |
| Approval of loss, threshold, minimum contributors, budgets, claim | BLOCKED | `person1_approval_checklist.md` items 1–10 |

## Step 2 — datasets and candidates

| Requirement | Status | Evidence |
|---|---|---|
| Inventory and provenance | PASS | `research_v1_inventory_and_provenance.md` |
| Evidence corpus and index identity | PASS | both corpus SHA-256 values recomputed and matched |
| research_v1 counts recomputed | PASS | 1,000 groups; 2,050 candidates (GSM8K 1,000 / HotpotQA 1,050); History 1,240 / Development 810; 964 / 215 / 871; HotpotQA generation 500 / 500 / 50; prepared 701 + 478; all 27 manifest hashes verified |
| Duplicate IDs and group integrity | PASS | 0 duplicate candidate IDs, 0 cross-partition groups, 0 multi-question groups, 0 group-ID mismatches |
| Candidate schema and label distinctions | PASS | `research_v1_label_audit.md` |
| Unresolved review queue | PASS (generated) / BLOCKED (review) | 871 rows, no labels assigned; human review needs named reviewers |
| Metric estimability | PASS | `evaluation_metrics.md` § Which metrics research_v1 can support |
| Direct-arithmetic scope | PASS | excluded for research_v1 (`dataset_selection.md`) |
| Teammate 700 results located and checked | BLOCKED | not found (`research_v1_inventory_and_provenance.md`); other result files checked read-only, with no History or Final Test overlap |

## Step 3 — splits

| Requirement | Status | Evidence |
|---|---|---|
| History and Development rosters | PASS | `dataset_split_protocol.md` § Current research_v1 partitions |
| Canonical Development identity and eligible rosters with hashes | PASS | 387 eligible groups, 478 candidates, 13 ineligible; `research_v1_development_roster.md` |
| 13-candidate rehearsal distinguished | PASS (as far as evidence allows) | no 13-candidate rehearsal artifact exists in the workspace; the only "13" is the 13 ineligible GSM8K groups, documented as such |
| Person 2 cost-collection roster | PASS | `person2_cost_collection_order.jsonl`, label-free, group-complete, size pending; no costs collected |
| Provisional Final Test verified without opening labels | PASS | 1,319 + 1,319 groups, 2,638 benchmark-gold candidates, all hashes and receipts verified, label payload byte-hashed only |
| Final Test leakage audit against research_v1 History/Development | PASS | recomputed comparisons all 0 and equal to the frozen audit |
| Final Test content-level exposure (all exposed datasets, Development files, baseline and verifier outputs) | FAIL | 807 contaminated groups; provisional Final Test retired (`final_test_contamination_audit.md`) |
| Final Test disabled / NOT_AUTHORIZED | PASS | manifest fields |
| Final Test independent custody | BLOCKED | no custodian; broad inherited ACLs |
| Leakage counts 25 / 14 / 14 / 2, others 0 | PASS | reproduced automatically |

## Part E — experiment contracts

| Experiment | Status | Evidence |
|---|---|---|
| 1 Clean and attacked | PASS (contract) / BLOCKED (run) | `experiment_contracts.json`: inputs, roster hash, five attack kinds, seven methods; loss/threshold pending |
| 2 Budget sensitivity | PASS (contract) / BLOCKED | `budgets.values = null`, `minimum_count = 3`, `PENDING_APPROVAL` |
| 3 Aggregation and dependency ablation | PASS (contract) / BLOCKED | two aggregations; no dependency or correlated-failure labels fabricated |
| 4 Live runtime validation | PASS (roster) / BLOCKED | `live_runtime_validation_order.jsonl`; size pending; adapter configuration unset |

## Part F — validation code

| Check | Status |
|---|---|
| Duplicate IDs, composition, provenance, manifest hashes | PASS |
| History/Development leakage | PASS |
| Final Test isolation (hashes, receipt, no label fields, no research_v1 Development overlap, disabled) | PASS (narrow) |
| Final Test freedom from prior exposure | FAIL (retired) |
| Readiness | BLOCKED (reported, not overridden) |
| Teammate compatibility | BLOCKED (700-result artifact absent; available files checked) |
| Versioning: write-once output; `validate` detects drift | PASS (`test_generate_refuses_existing_output`; tamper test) |

## Corrections made

- `final_test_manifest.md` said "not yet allocated" although a provisional Final Test had been generated; rewritten from the verified manifest.
- `dataset_split_protocol.md` said no splits had been generated; the current partitions were added.
- `dataset_selection.md` described the Final Test as only "disabled"; it now describes the provisional partition.
- `research_objective.md` cited a nonexistent `candidate_answer_validation_audit.md`; the citation is now marked as missing.
- No dataset membership, ID, label, partition, or hash was changed, so no new dataset version was needed. The new Person 1 artifacts are a new versioned directory.

## Files changed

- New code: `evaluation/data_preparation/person1_validation.py`, `tests/test_person1_validation.py`.
- New docs: `person1_compliance_matrix.md`, `person1_approval_checklist.md`, `research_v1_inventory_and_provenance.md`, `research_v1_label_audit.md`, `research_v1_development_roster.md`.
- Updated docs: `research_objective.md`, `dataset_selection.md`, `candidate_answer_protocol.md`, `dataset_split_protocol.md`, `evaluation_metrics.md`, `final_test_manifest.md`, `research_v1_group_leakage_audit.md`, `research_protocol_readiness.md`.
- New local artifacts (Git-ignored): `evaluation/datasets/person1/research_v1_person1_v1/` (10 files).

## Limitations

- Semantic and paraphrase leakage were not audited.
- The Final Test roster exposes the gold answers, because every candidate is gold. Isolation is organisational, not technical.
- No verifier Attempts, cost measurements, or experiment outcomes exist. All experiment outputs are contracts only.
- HotpotQA has no verified incorrect candidates in any partition.

## Conclusion

**Person 1 substantially completed, with named blockers.** Every safely implementable data, split, validation, roster, and documentation requirement is implemented and verified. The remaining items need external inputs:

1. Approvals 1–20 in `person1_approval_checklist.md`.
2. A new uncontaminated, mixed-label Final Test (v2; see `final_test_v2_selection_plan.md`) and an independent custodian with OS-level protection. The provisional Final Test is retired.
3. The owner's path or run ID for the "700 results".
4. Human review of the 871 unresolved candidates.
5. Verifier execution (adapter configuration), which in turn blocks Attempts and every experiment.
