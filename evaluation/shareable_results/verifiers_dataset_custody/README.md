# Verifiers and Dataset Custody

This package is a handoff of the verifier and dataset-custody records. It copies existing evidence and states what that evidence does and does not approve. It does not change Experiment 3, Experiment 1, verifier code, datasets, or Final Test labels.

No file here is a new approval, a signature, or an independent-custody appointment.

## Read first

1. This README
2. [07_readiness_and_outstanding_items.md](07_readiness_and_outstanding_items.md)
3. The document for the responsibility you are checking

| Document | What it contains |
| --- | --- |
| [01_task_support.md](01_task_support.md) | Direct-arithmetic and direct-factual support by verifier |
| [02_verifier_versions_and_resources.md](02_verifier_versions_and_resources.md) | Source hashes, model names, UNKNOWN digests, corpus and index |
| [03_dataset_manifests_and_provenance.md](03_dataset_manifests_and_provenance.md) | Approved Development roster, exploratory History, stale hash sidecar |
| [04_verifier_cost_calibration.md](04_verifier_cost_calibration.md) | Frozen millisecond calibration shared by Experiment 3 and Experiment 1 |
| [05_final_test_v2_custody.md](05_final_test_v2_custody.md) | Self-custody metadata and the contradictory authorization fields |
| [06_dated_protocol_amendment.md](06_dated_protocol_amendment.md) | The 2026-11-13 amendment and its missing research-lead approval |
| [07_readiness_and_outstanding_items.md](07_readiness_and_outstanding_items.md) | Status table and remaining decisions |

`manifest.json` lists every file in this package, its source path, SHA-256, and status.

## What is authoritative

- Development eligibility for 372 groups is the approved roster in `evidence/development_eligibility_manifest.json`. Approval covers that roster only. Collection, recording, protocol freeze, and Final Test release remain unauthorized in that file.
- Verifier source hashes in `evidence/verifier_config.json` match the current Python sources. The config itself is `DECLARED_PENDING_APPROVAL`.
- The cost freeze in `evidence/cost_calibration_freeze_manifest.json` freezes measurements. It does not authorize policy fitting or budget selection.
- Final Test metadata records a sealed dataset and self-custody. It does not authorize scoring.

## What is not approval

- History in `evidence/exploratory_dataset_manifest.json` is `EXPLORATORY_PROVISIONAL_LABELS`. There is no approved History eligibility manifest.
- The evidence-corpus manifest is `PROPOSAL_NOT_APPROVED`.
- Model-weight hashes, the evidence prompt hash, and the confidence generator digest are `UNKNOWN`.
- The self-custody record contains inconsistent scoring fields. This package does not resolve them.
- `evidence/development_eligibility_manifest.file_sha256.txt` does not match the current eligibility file. It is included unchanged so the mismatch stays visible.

## Decisions still required

A research lead still has to approve the 2026-11-13 custody amendment, freeze the study configuration, and authorize any Final Test scoring in a separate signed record. An independent custodian is not appointed. Human adjudication of synthetic incorrect labels is not done.

## Final Test boundary

This package does not contain Final Test labels or answers. `evidence/final_test_access_log.jsonl` is one metadata line. The word `labels` in that line is a field name. The sealed label file was not opened, parsed, copied, or rehashed for this package.
