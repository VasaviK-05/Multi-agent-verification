# Experiment 2 — Consolidated Evidence Register

## 1. Purpose

This register consolidates the current evidence and documentation status for Experiment 2: Budget Sensitivity Analysis.

It distinguishes:
- Original historical `multitask-policy42` campaign evidence.
- Development-only budget sensitivity analysis.
- Separate `reference-fresh-v1` exploratory evidence.
- Recovered and independently verified provenance artifacts.
- Remaining historical source-provenance limitations.
- Protected evaluation data.

This register is a documentation and tracking artifact. It does not certify formal Experiment 2 completion.

## 2. Historical campaign evidence inventory

| Evidence item | Current status | Notes |
|---|---|---|
| Original Arithmetic training manifest | Recovered and hash-verified | Original historical artifact |
| Original Factual training manifest | Recovered and hash-verified | Original historical artifact |
| Original Arithmetic Development evaluation | Recovered and hash-verified | Original historical artifact |
| Original Factual Development evaluation | Recovered and hash-verified | Original historical artifact |
| Arithmetic and Factual calibration files | Recovered | Included in recovery package |
| Arithmetic and Factual recording bundles | Recovered | Original `recordings.json` files |
| Arithmetic and Factual collection reports | Recovered | Included in recovery package |
| Arithmetic and Factual fit provenance | Recovered | Producer identity and historical references recorded |
| Original producer script | Recovered and independently hash-verified | Exact recorded SHA-256 matched |
| Four country-data source snapshots | Recovered and hash-verified | Match recorded source hashes |
| Original application source corresponding to historical digest | Unrecovered | Recorded digest could not be independently reproduced |
| Original execution-source ZIP | Unavailable | Not recovered |
| Original hardware inventory | Not available | Detailed hardware record not established |
| Separate signed authorization document | Not recovered | Authorization references exist in recovered records |
| Budget sensitivity results | Documented | `EXPERIMENT_2_BUDGET_SENSITIVITY_RESULTS.md` |
| Budget sensitivity notebook | Cleanup performed; validation/commit status pending | Do not rerun cells that write to existing output directories |
| `reference-fresh-v1` exploratory archive | Reviewed separately | Not proof of original campaign continuity |
| Reference-fresh provenance review | Documented separately | `EXPERIMENT_2_REFERENCE_FRESH_PROVENANCE_REVIEW.md` |
| Final Test payload | Protected | Not accessed or evaluated |

## 3. Recovery package verification

The updated recovery package is:

`recovery_package_v2.zip`

Package SHA-256:

`b8b070eb96a2a608c52e9a504965cc88f06a97a444efabc7db526fc8810504c2`

Independent integrity checks established:

- 30 ZIP members.
- 29 manifest entries.
- All 29 manifest file hashes matched their actual file bytes.
- All 29 manifest file sizes matched.
- The outer ZIP SHA-256 matched the supplied package hash.
- The recovered original producer script matched its exact recorded SHA-256.

Original producer script SHA-256:

`174a7b965a15e9a6540f06705c7d330b81de9de45187a638dded4acb1bfaa5ea`

The producer script identity is supported by matching recorded values in both Arithmetic and Factual fit-provenance records.

The recovered producer script closes the previously outstanding exact producer-script recovery requirement.

These checks establish package integrity and the producer-script hash match. They do not independently establish the missing application source.

## 4. Budget sensitivity findings

The existing Development-only analysis evaluated three approved budget levels:

| Scenario | Budget fraction | Budget |
|---|---:|---:|
| B1 | 50% | 8,297.39 ms |
| B2 | 75% | 12,446.09 ms |
| B3 | 100% | 16,594.78 ms |

The minimax analysis selected the semantic-only, reputation-weighted strategy with probability 1.0 for all three budget scenarios.

Key observations:

- All 20 cases per scenario remained uncertain.
- Decision coverage was 0%.
- No false accepts or false rejects occurred.
- Mean loss was approximately 0.200615.
- The 90% clean-coverage constraint was infeasible at all three budget levels.

The result is mathematically optimal under the encoded objective but operationally unhelpful because the selected policy abstains on every case.

## 5. Baseline findings

The documented baseline analysis reported:

- `coverage_aware_greedy`: 80% clean coverage, 0.04 clean decision loss.
- `development_best_fixed`: 80% clean coverage, 0.04 clean decision loss.
- `policy`: 66.67% clean coverage, approximately 0.0667 clean decision loss.
- Suppression: 0% coverage, with unresolved decisions.

Forced-support and forced-rejection analyses also exposed false accepts and false rejects.

These baseline measurements and minimax measurements represent different analytical contexts. They should not be presented as a direct cost-efficiency comparison.

## 6. Separate reference-fresh exploratory evidence

The `person3-prerequisite-artifacts.zip` archive contains a separate `reference-fresh-v1` exploratory study.

Findings:

- Development training-manifest and evaluation artifacts are present.
- The protocol describes a resumed exploratory study, not an uninterrupted campaign.
- `policy_id` and `candidate_freeze_id` are null in the artifact identity record.
- The Development evaluation shares the manifest and compatibility IDs previously associated with `reference-50-v1`.
- Final Test reservation metadata is present, but the protected payload has not been accessed.

This archive must remain separate from the original `multitask-policy42` campaign evidence.

It does not replace or establish continuity with the original historical campaign.

## 7. Remaining historical provenance limitations

The following remain unresolved:

### 7.1 Application source

The expected application source digest is:

`d2565ca4897a9e1f938900f4feb80fe675b9229c2acb7b27544781ec1c9bdcaf`

Additional historical application digests include:

- Collection digest: `47597967da7d8f05aa56ef1ed6fbd544eb70e607aaf8804e5163e650cea35e4d`
- Fit digest: `2926e0513be4c929d33bbcfa15787ee76fd96328a509821d91c71ff0467dc238`

These application source digests could not be independently reproduced from the available committed source trees and recovered working-tree sources.

The original application source files corresponding to those historical digests remain unavailable.

### 7.1.1 Calibration source-digest reconciliation

A separate reconciliation was performed for the Development calibration artifact:

- Calibration Git revision: `662bd5cdbf2c8b2dc9885f6bb80e42abf7c5205e`
- Calibration artifact SHA-256: `7fbfe418c0c65c3782628ab5117b773f2fc4c8312c33d769934f76d2ff61a7f3`
- Recorded application source digest: `ecb12d8934a3d55dd745887ecf9b3c164ea308f3b07eaa895a6d69f246e87e6`
- Reconstructed application source digest: `ade428b710d33d2349db119c1f15d7abbf655f3f849b13a18000ba327111aab6`

The calibration artifact's file hash was verified, but its recorded application source digest could not be independently reproduced from the referenced Git tree. The original build-time working-tree snapshot or complete source inputs have not been established.

**Disposition:** Calibration source provenance remains partially verified; the digest mismatch does not, by itself, establish that the calibration artifact is invalid or tampered with. See `EXPERIMENT_2_CALIBRATION_SOURCE_DIGEST_ADDENDUM.md` for the detailed reconciliation.

### 7.2 Original execution-source archive

The original execution-source ZIP has not been recovered.

The recovered producer script does not substitute for the complete application source and execution environment.

### 7.3 Environment and authorization records

- Detailed hardware inventory is unavailable.
- A separate signed authorization document has not been recovered.
- Existing authorization references and environment-version records remain preserved in the recovered evidence.

### 7.4 Search coverage

The additional recovery investigation covered:

- 208 Git commits.
- Dangling Git objects.
- Accessible working-tree sources.
- Available historical source snapshots.

The exact application source corresponding to the recorded digests was not recovered.

These are documented search findings, not proof that no other inaccessible copy exists.

## 8. Scope and data-protection constraints

The following constraints apply to further work:

- Do not inspect, load, or evaluate Final Test payloads.
- Do not initiate additional verifier executions without a separate justified and approved need.
- Preserve historical evidence archives unchanged.
- Keep exploratory evidence separate from historical campaign evidence.
- Do not modify `main`.
- Keep application and verifier logic outside the scope of this documentation task.
- Do not regenerate historical manifests, evaluations, recordings or campaign outputs.
- Retain original package hashes and recovered evidence for auditability.

## 9. Current overall assessment

| Area | Assessment |
|---|---|
| Budget sensitivity analysis | Documented |
| Minimax findings | Documented |
| Original Arithmetic/Factual training manifests | Recovered and hash-verified |
| Original Arithmetic/Factual Development evaluations | Recovered and hash-verified |
| Calibration and recording bundles | Recovered |
| Original producer script | Independently hash-verified |
| Country-data source snapshots | Hash-verified |
| Application source digests | Unresolved |
| Original execution-source ZIP | Unavailable |
| Exploratory archive review | Documented separately |
| Protected Final Test data | Untouched |
| Formal Experiment 2 completion | Not established |

## 10. Recommended next action

The original historical artifact recovery phase has substantially progressed.

The remaining work is limited to deciding how the unresolved application-source and execution-source provenance limitations should be handled in the final research reporting.

Do not substitute exploratory artifacts, publication scripts or reconstructed files for unavailable original historical source material.

Any change to the formal completion assessment must be supported by verified source artifacts and documented compatibility evidence, with the team's agreement.

---

**Register status:** Updated after recovery package v2 verification.

**Overall interpretation:** Original campaign training and Development evaluation artifacts recovered; original producer script and factual source snapshots verified; application source provenance and original execution-source archive remain unresolved; formal Experiment 2 completion is not established.