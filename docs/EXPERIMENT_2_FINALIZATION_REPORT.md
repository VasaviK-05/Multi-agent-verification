# Experiment 2 — Finalization Report

**Prepared:** 15 November 2026  
**Scope:** Consolidated status of the historical `multitask-policy42` campaign, the Development-only budget-sensitivity analysis, and associated provenance/rehearsal evidence.

## 1. Executive determination

The existing evidence is sufficient to publish a transparent **Development-only budget-sensitivity result and historical evidence-recovery report**. It is not sufficient to claim that every part of the original historical campaign has been independently reproduced or that a confirmatory Final Test evaluation has been completed.

The report therefore separates:

1. completed empirical/analytical work that can be reported now;
2. recovered historical artifacts whose integrity has been checked;
3. unresolved archival or semantic-reconciliation limitations that must remain disclosed.

The study owner has confirmed that the required approvals have been obtained. This report does not reopen approval requests or classify approval as an outstanding action. Where preserved artifacts still contain older `not_authorized` or approval-related metadata, those values are recorded as artifact contents and should be reconciled against the approval record by the responsible owner; they are not silently rewritten.

## 2. Completed work that can be reported

### 2.1 Historical artifact recovery and integrity

The latest recovery package, `recovery_package_v2.zip`, has SHA-256 `b8b070eb96a2a608c52e9a504965cc88f06a97a444efabc7db526fc8810504c2`. It contains 30 ZIP members and an internal manifest with 29 entries. All 29 manifest-listed files independently matched their recorded SHA-256 hashes and byte sizes.

Recovered historical materials include:

- Arithmetic and Factual training manifests;
- Arithmetic and Factual Development evaluations;
- calibration files and original `recordings.json` bundles;
- collection reports and four factual country-data source snapshots;
- the exact original producer script.

The producer script at `execution-source/recovered-snapshots/multitask_policy42.py` has SHA-256 `174a7b965a15e9a6540f06705c7d330b81de9de45187a638dded4acb1bfaa5ea`, matching the hash recorded in the recovered fit-provenance records. The recovery report identifies Git blob `48722f26b49300d60d1ae9ebbb07ce904db3698e`.

These checks establish package integrity and recovery of the listed artifacts. They do not independently recreate the historical runtime or reproduce every historical execution.

### 2.2 Development-only budget sensitivity

The three evaluated budgets are:

| Scenario | Fraction | Budget |
|---|---:|---:|
| B1 | 50% | 8,297.39 ms |
| B2 | 75% | 12,446.09 ms |
| B3 | 100% | 16,594.78 ms |

The existing minimax analysis selected the semantic-only, reputation-weighted strategy with probability 1.0 at all three budgets. Its estimated strategy cost was 102.0714 ms and its reported game value/worst-case Development loss was approximately 0.200615.

For every budget and each of the five reported scenarios (clean, forced support, forced rejection, confidence inflation, suppression), the policy abstained on all 20 examples: 0% decision coverage, 20 uncertain outcomes, zero false accepts, and zero false rejects.

The 90% clean-coverage constraint was infeasible at all three budgets. The maximum clean coverage among available strategies was 0% at B1, 0% at B2, and 60% at B3.

The preliminary baseline had 80% clean coverage and 0.04 clean decision loss, but showed vulnerability under forced-support and forced-rejection scenarios. The preliminary baseline and minimax cost estimates were generated under different estimation contexts and must not be presented as a direct cost-efficiency comparison.

**Interpretation:** the optimization is internally consistent for the encoded game, but the selected minimax policy is operationally degenerate because it abstains on every case. Increasing the budget from B1 to B3 did not change the selected strategy or decision coverage. The evidence does not support a claim of successful operational budget sensitivity or adversarial robustness.

### 2.3 Approved Development eligibility and rehearsal mapping

The approved Development eligibility manifest contains 744 eligible candidates across 372 groups and 15 quarantined shared-context groups. Its approval is for Development eligibility only; the manifest's narrower scope must be retained.

The rehearsal provenance comparison mapped 13 rehearsal candidates / 52 attempt rows. Eight candidates (32 attempt rows) had exact repository-defined input-hash matches. Four additional candidates shared group/question identity but had no exact input match; one group was absent from the approved roster. No candidate-ID overlap or remapping was found.

The 32 exact input matches are **conditional mappings**, not canonical recorded-attempt equivalence. The rehearsal lacks the canonical `attempt_id`, original `RecordingRequest`, request ID, and exact planning JSON needed to establish that stronger identity. The mapped labels are provisional automated labels with `human_verified=false`; they are not treated as independently verified ground truth. Therefore, zero of the 32 attempts are admitted as canonical recorded evidence on the basis of this mapping alone.

## 3. Evidence limitations to disclose

### 3.1 Historical application-source provenance

The following historical application-source digests remain unreproduced:

- `d2565ca4897a9e1f938900f4feb80fe675b9229c2acb7b27544781ec1c9bdcaf`
- `47597967da7d8f05aa56ef1ed6fbd544eb70e607aaf8804e5163e650cea35e4d`
- `2926e0513be4c929d33bbcfa15787ee76fd96328a509821d91c71ff0467dc238`

The original execution-source ZIP with expected SHA-256 `f3a1d6109a94d394d93ab0deacb1e839489f65154265d0d298878f9344062896` was not recovered. The separate signed authorization document and detailed hardware inventory were also not recovered, although authorization strings exist in the recovered audit/provenance records. The source audit documents a bounded search across 208 commits, dangling Git objects, and accessible working-tree sources.

**Classification:** historical provenance is **PARTIALLY VERIFIED**, not fully independently reproduced. The producer script recovery closes the earlier producer-script gap, but it does not close the application-source digest or execution-source archive gaps.

### 3.2 Calibration record consistency

The supplied frozen calibration bundle records 488 Development observations, with 480 retained after eight warmups. The bundle includes `measurements.json`, `calibration.json`, `calibration-provenance.json`, and `freeze-manifest.json`.

A v3 run-manifest/measurements inconsistency remains documented. No independent external execution witness was located. Report the calibration bundle as supplied frozen calibration evidence with this consistency limitation; do not describe it as independently witnessed.

### 3.3 Rehearsal contamination-flag semantics

The rehearsal's `pilot_manifest.json` records `final_test_accessed=false`, `history_inputs_read=false`, `labels_or_gold_sent_to_verifiers=false`, and `policy_fitting_performed=false`. The corresponding `pilot_results.json` omits three of those fields (it records `final_test_accessed=false`). A derived `validation_report.json` records all four `pilot_flags` as true and gives an aggregate `PASS_FOR_RECORDED_PILOT_FLAGS` disposition.

The meaning and transformation of these fields are unresolved. Do not invert booleans, infer semantics from the aggregate PASS label, or use the 32 mapped attempts as canonical evidence until the owner/custodian supplies the original field definitions, source logs/access records, producer code, and transformation explanation. This is a semantic reconciliation issue, not a reason to discard the otherwise verified input-hash comparison.

### 3.4 Final Test metadata boundary

Custodian package metadata was inspected without opening Final Test labels or payloads. The v2 metadata identifies 1,200 candidates / 600 groups and reports zero human-verified labels, deferred human adjudication/approval, `custody_status=PENDING_NO_INDEPENDENT_CUSTODIAN`, `confirmatory_use=NOT_AUTHORIZED`, and `enabled=false`.

The user has separately confirmed that required approvals have been obtained. Preserve that confirmation as an external approval record and reconcile the stale or conflicting metadata through the responsible custodian. A reservation hash or package-integrity check alone does not establish independent custody. No Final Test label, payload, or outcome was accessed for this report, and no Final Test performance claim is made.

## 4. Separation of evidence streams

- `multitask-policy42` remains the original historical campaign.
- `reference-fresh-v1` remains a separate resumed exploratory study and is not a substitute for original campaign provenance.
- The supplementary Arithmetic/Factual policy results are supplementary Development analyses, not the three-budget Experiment 2 analysis.
- The live-checkpoint recovery handoff is a separate backend durability workstream and is not Experiment 2 evidence.

Do not merge identifiers, manifests, policies, labels, or results across these streams without an explicit, recorded compatibility basis.

## 5. Claims permitted in the final submission

The submission may state that:

1. a substantial set of original historical artifacts was recovered and its included manifest integrity was independently checked;
2. the exact original producer script was recovered and its recorded hash matched;
3. a Development-only three-budget minimax analysis was completed on reused Development outcomes;
4. the minimax solution abstained on every evaluated case at all three budgets;
5. the 90% clean-coverage requirement was infeasible at all three budgets;
6. the preliminary baseline had higher clean coverage but was vulnerable to specified directional attacks;
7. rehearsal input-level equivalence was established for 32 attempt rows, while canonical recording and label equivalence were not established.

The submission must not claim that:

- the original historical runtime/application source was fully reproduced;
- the minimax policy achieved useful decision coverage or adversarial robustness;
- the preliminary baseline and minimax estimates establish a direct cost-efficiency win;
- the rehearsal's 32 conditional rows are canonical accepted recordings;
- `reference-fresh-v1` replaces the original campaign;
- Final Test evaluation or confirmatory performance was completed.

## 6. Final status

| Component | Status |
|---|---|
| Historical artifact recovery package integrity | VERIFIED for all 29 manifest entries |
| Original producer script identity | VERIFIED by exact recorded SHA-256 |
| Historical application-source provenance | PARTIALLY VERIFIED; three digests unreproduced |
| Development-only B1/B2/B3 minimax analysis | COMPLETED as an existing-data analysis |
| 90% clean-coverage feasibility | INFEASIBLE at all three budgets on available Development outcomes |
| Rehearsal input-hash mapping | VERIFIED for 32 rows; conditional only |
| Canonical admission of rehearsal rows | NOT ESTABLISHED |
| Calibration bundle | SUPPLIED; v3 consistency issue remains |
| Rehearsal contamination semantics | UNRESOLVED |
| Final Test labels/payloads | NOT ACCESSED |
| Overall historical provenance | PARTIALLY VERIFIED |

**Recommended overall wording:** “Experiment 2's available Development-only budget-sensitivity analysis and substantial historical artifact recovery are complete and documented. The minimax policy was operationally degenerate under the evaluated objective, and the historical provenance record remains partially verified with explicitly disclosed archival and semantic-reconciliation limitations. No Final Test performance claim is made.”

## 7. Finalization actions

1. Keep this report and the existing evidence register on the experiment branch; do not rewrite preserved historical manifests or source artifacts.
2. Attach or reference the external approval record that the study owner confirms is already obtained, and reconcile stale approval fields without changing the original evidence files.
3. Record the calibration v3 discrepancy and rehearsal contamination-field reconciliation as disclosed limitations unless the responsible owners can resolve them from existing records.
4. Run only documentation/integrity checks on the final branch diff. Do not rerun historical campaigns, collect new verifier outputs, refit policies, or inspect Final Test labels as a shortcut to closure.
