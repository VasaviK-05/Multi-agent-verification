# Experiment 2 — Calibration Source-Digest Reconciliation Addendum

**Date:** 17 November 2026
**Scope:** Reconciliation of the frozen Development cost-calibration artifact's recorded application source digest.

## 1. Verified calibration identity

- Calibration Git revision: `662bd5cdbf2c8b2dc9885f6bb80e42abf7c5205e`
- Calibration artifact: `artifacts/research-v1-development-cost-calibration-v1/calibration.json`
- Artifact SHA-256: `7fbfe418c0c65c3782628ab5117b773f2fc4c8312c33d769934f76d2ff61a7f3`
- Artifact size: 885,049 bytes
- Recorded application source digest: `ecb12d8934a3d55dd745887ecf9b3c164ea308f3b07eaa895a6d69f246e87e6c`

The calibration artifact's byte-level SHA-256 was verified independently.

## 2. Source-digest reproduction attempt

The recorded source-digest algorithm was recovered from `app/game/offline/build.py` and `app/game/models.py`.

A reconstruction using the recorded Git revision, Python source files, canonical JSON serialization, Windows `Path` ordering, and normalized line endings produced:

`ade428b710d33d2349db119c1f15d7abbf655f3f849b13a18000ba327111aab6`

This does not match the recorded digest:

`ecb12d8934a3d55dd745887ecf9b3c164ea308f3b07eaa895a6d69f246e87e6c`

The reconstruction identified 137 tracked Python files at the historical revision, compared with 138 in the current application tree.

## 3. Disposition

**Status: NOT INDEPENDENTLY REPRODUCED.**

The available historical Git snapshot does not reproduce the calibration's recorded application source digest. The original build-time working-tree snapshot or complete source inputs used to calculate that digest have not been established by this reconciliation.

This is a provenance limitation. It does not establish that the calibration artifact is invalid, altered, or unusable.

The calibration artifact and its original measurements must remain unchanged. No calibration rerun, refit, verifier execution, or Final Test access was performed.

## 4. Experiment 2 impact

- Retain the calibration artifact's verified file identity.
- Retain its recorded source digest as historical metadata.
- Mark independent application-source digest reproduction as unresolved.
- Do not claim complete source compatibility based solely on the recorded Git revision.
- Keep this finding separate from the three previously documented unreproduced historical application-source digests.

## 5. Recommended reporting language

"The frozen Development cost-calibration artifact was verified by byte-level SHA-256. Its recorded application source digest could not be independently reproduced from the referenced historical Git revision using the recovered digest algorithm. The original build-time source snapshot remains unavailable or unestablished. Calibration source provenance is therefore partially verified; this finding does not independently invalidate the recorded measurements."
