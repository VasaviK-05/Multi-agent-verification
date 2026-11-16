# Experiment 2 — Rehearsal Provenance Closure Note

**Status:** Development-only evidence package documented; historical source provenance remains partially verified, and the rehearsal contamination discrepancy is closed as an unrecoverable provenance limitation.

## 1. Purpose

This note records the outcome of the rehearsal provenance investigation and defines the conditions under which the affected rehearsal attempts may be reconsidered.

## 2. Evidence reviewed

The investigation reviewed:
- The recovered `multitask-policy42` historical artifacts and producer script.
- The approved Development eligibility manifest.
- The rehearsal provenance comparison and mapping-validation packages.
- The rehearsal pilot manifest, pilot results and derived validation report.
- The available source-review archives and provenance documentation.

## 3. Findings

Eight rehearsal candidates have exact normalized verifier-input correspondence with approved Development candidates, representing 32 corresponding verifier-attempt rows.

This establishes input-level correspondence only. It does not establish canonical recording identity, label equivalence, or complete source and execution compatibility.

The rehearsal manifest records the relevant contamination event fields as false. The derived validation report records four corresponding pilot flags as true and reports `PASS_FOR_RECORDED_PILOT_FLAGS`.

The available evidence does not establish the semantics or transformation that produced those flags.

## 4. Disposition

All 32 mapped rehearsal attempts remain conditional and excluded from policy fitting.

No original historical records, rehearsal records, labels, or derived reports are to be modified to force consistency.

The discrepancy must be reopened only when the report-generation source, field definitions, or equivalent owner/custodian evidence establishes the meaning and transformation of the flags.

## 5. Experiment 2 reporting boundary

The budget-sensitivity findings may be reported as existing Development-only analysis. Supplementary Development results must remain separately identified.

The historical source audit remains partially verified. The rehearsal mapping does not establish full recording compatibility. The unresolved contamination discrepancy prevents admission of the 32 rehearsal attempts.

No claim of full formal Experiment 2 completion or confirmatory validation should be made on the basis of this evidence package.

## 6. Final Test boundary

Final Test labels and payloads remain reserved. This work does not authorize access, evaluation, or policy fitting against Final Test data.

## 7. Closure decision

The current evidence package can be finalized as a documented Development-only research submission with explicit limitations.

The rehearsal contamination discrepancy has been closed as an unrecoverable provenance limitation. Historical source provenance remains partially verified, and identity-level exclusion of the 32 rehearsal attempts remains unverified.

### Rehearsal contamination discrepancy — Final disposition

The false-to-true discrepancy in the rehearsal contamination flags has been reviewed by Raunak through a read-only audit.

The recovered producer code at commit `662bd5c` writes all four contamination-related flags as false. However, the available sources do not contain the original rehearsal archive, its manifest and results, or the schema, validation rule, or transformation responsible for the derived report's true values.

The discrepancy is therefore classified as an **unrecoverable provenance limitation**. The derived true flags are not treated as evidence that contamination occurred, and the original false flags are not treated as proof that contamination was impossible.

The 32 rehearsal attempts were not admitted into a research dataset. Experiment 3 records `used_as_experiment3_dataset: false`. However, identity-level exclusion of all 32 attempts remains unverified because `attempts.jsonl` was unavailable.

The 32 attempts remain excluded from admitted Experiment 2 evidence. This limitation is retained explicitly in the final provenance record.

**Supporting audit:** `evaluation/docs/rehearsal_contamination_flag_audit.md`

**Disposition:** Closed as an unrecoverable provenance limitation, with identity-level exclusion remaining unverified.
