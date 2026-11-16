# Experiment 2 Supporting Evidence

This folder contains supporting artifacts for the Experiment 2 documentation.

## Evidence collections

- `recovery_package_v2/` — recovered historical campaign artifacts and source materials.
- `approved_development_eligibility_artifacts/` — approved Development eligibility records and related materials. Check the manifests to distinguish approved from provisional records.
- `rehearsal_provenance_comparison/` — rehearsal input-mapping and provenance-comparison evidence.
- `supplementary_development_results/` — supplementary Development results. These are not the three-budget Experiment 2 evaluation.

## Scope and limitations

- Rehearsal input-level correspondence does not establish canonical recording identity or label equivalence.
- Historical source provenance remains partially verified.
- Supplementary results must not be presented as the completed three-budget campaign.
- Final Test labels and payloads were not accessed or evaluated as part of this evidence review.
- Preserve recovered source artifacts unchanged.

See the Experiment 2 reports in the repository's `docs/` directory for interpretation, findings and limitations.

## Rehearsal contamination-flag audit

- **Supporting audit:** `../../evaluation/docs/rehearsal_contamination_flag_audit.md`
- **Original source branch:** `raunak-exp-3`
- **Original source commit:** `2dd4037af38801ac0c9f042e03486e18bb1c9bd1`
- **Classification:** Unrecoverable within available sources.
- The recovered producer code writes all four contamination-related flags as `false`. No recovered transformation explains the derived report's `true` values.
- The 32 rehearsal attempts were not admitted into a research dataset. Experiment 3 records `used_as_experiment3_dataset: false`.
- Identity-level exclusion of all 32 attempts remains unverified because the original `attempts.jsonl` was unavailable.
- The 32 attempts remain excluded from admitted Experiment 2 evidence.
- This finding does not establish that contamination occurred or prove that contamination was impossible.

## Approval reconciliation

- **Supplementary record:** ../EXPERIMENT_2_APPROVAL_RECONCILIATION.md
- Records the distinction between Development eligibility approval and separately reported Experiment 2 activity approvals.
- Documents the historical approval-metadata discrepancy without rewriting original manifests or execution records.
- The later activity approvals are reported by the study owner; a separate signed approval artifact was not located in the inspected repository evidence.
- Formal research-team sign-off remains a separate closure requirement.


## Final source-custody reconciliation

- **Owner-published source:** `evaluation/docs/experiment2_final_source_custody_reconciliation.md`
- **Source branch / commit:** `raunak-exp-3` / `3860bc7` (16 November 2026)
- **Disposition:** The requested original execution-source archive and three requested application source sets are unrecoverable within the custody sources inspected.
- The separate 120-entry source-hash list is verified as metadata only; its corresponding source bytes were not recovered.
- The previously recovered producer script is verified independently and does not substitute for the missing application source sets.
- Search limitations remain explicit: the external machine was not accessed, OneDrive was searched by filename rather than exhaustive content hashing, and remote CI artifacts were not queried.
- The research-protocol proposal's pending-approval metadata remains unchanged and distinct from the study owner's separately reported Experiment 2 activity approvals.
- No historical campaign was rerun, no historical artifact was regenerated, and no Final Test outcome data was accessed for this reconciliation.
