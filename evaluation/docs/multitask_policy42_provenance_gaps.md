# multitask-policy42 provenance gaps

This note was written on 2026-11-15, after the original campaign. It lists evidence that is still missing. Retrospective notes can point at those gaps. They do not fill them.

The search behind this note is `multitask_policy42_artifact_recovery_audit.md`.

## Gaps that block byte-level recovery

| Missing evidence | What exists instead | What would close the gap |
|---|---|---|
| Arithmetic and Factual `training-manifest.json` | Recorded SHA-256 values `c87d65246015919c02d86c4c83f39e0ded6ede02d25aa551a034b66a738ed485` and `9be8da9773eaced47faae3ff49e4e1536391be21824bb29f1e2c664cf5fd6e3c`, attributed to `1277e9d3ce91f1395e3deed7e7202748a5a04672` | The raw files, or a Git object database that contains that commit and blobs `5cdac6495c540360d55a389b0cfc8f1b507cb308` and the factual training blob named by the recovery record. A new hash must match before the files are treated as originals. |
| Arithmetic and Factual `development-evaluation.json` | Recorded SHA-256 values `e146f2adafe5cfde34395aa4478e2f584d68c597f96a7f8e4efbd7c7c9c87a97` and `fb00b72373e64d08f3566c119a12a19e35af0994bbbb32d1036dbe498ffe86b9`. Packaged `source_evaluation_id` values match the content IDs recorded for these older files. | The same commit or the raw files. Recompute SHA-256 and the content ID. The later current-policy IDs `a59218d2…` and `ee242866…` are a different binding and must stay distinct. |
| Cohort `calibration.json` files | ZIP `costs.json` summaries with calibration IDs `9678fb81adb197893d768db84dd5e8196ca5780600ccfd6a15c71d61f1da41a0` and `084b056eefcc44842c7d66f6896b70b35b33d3f7cc11ecf4cb8c88ff7119e63d`, plus input digests `71f3709b…` and `f270fcb5…` | The original `build/multitask-policy42/{arithmetic,factual}/calibration.json` bytes. No reference file hash is on record, so identity has to be shown by calibration ID and input digest, then a new file hash recorded. |
| Parent sweep policies | Historical packager names `build/multitask-uncertainty-sweep42/arithmetic/coverage-50/policy.json` and `factual/coverage-25/policy.json` | Those two files. Their SHA-256 must equal the packaged members `ec1be5b6…` and `df1bef32…` before the copy claim is byte-verified. |
| Execution-source ZIP | `execution-source-custody.json` expects SHA-256 `f3a1d6109a94d394d93ab0deacb1e839489f65154265d0d298878f9344062896`, source revision `2c9f697439d1d1c2ed7c0a92645848c0f07f7e3f` | The ZIP with that hash, plus the revision in a Git database. |
| Recording manifests and recordings | Results narrative says 960 verifier attempts. The packager says recordings stay outside the ZIP. Phase 2 lists different recording hashes for a later run. | Original `build/multitask-policy42` collection or recording files, with hashes tied to the packaged calibration IDs rather than the Phase 2 checkpoint. |
| Campaign source snapshot | ZIP `source_revision` `17b695373f935dc1f5fd09c37cf8917969367f7a` and application digest `d2565ca4897a9e1f938900f4feb80fe675b9229c2acb7b27544781ec1c9bdcaf` | That commit, and a digest recomputed from the tree it names. |
| Signed authorization | Script string `40cf4c15-2260-48ef-b3a1-7154d0d47554` and ZIP string `bff23d52-aafc-4be6-8adb-3c7e8f88836c` | An original authorization record if one was created. This audit did not find one and does not invent one. |

## What available sources do not contain

This clone's object database does not contain `1277e9d3ce91f1395e3deed7e7202748a5a04672`, `17b695373f935dc1f5fd09c37cf8917969367f7a`, or `2c9f697439d1d1c2ed7c0a92645848c0f07f7e3f`. Remote-tracking branches were inspected without fetching. `build/` contains only the Phase 2 checkpoint and the current-v1 rerun. Scanned non-label ZIPs do not contain the campaign paths. User `Downloads`, `Desktop`, and `Documents` to depth 3 did not contain the filenames.

The prior recovery write-up describes a search on another machine, including reflogs and temporary checkouts, that located the four training and Development files in `1277e9d` and did not locate the execution-source ZIP. That write-up is evidence of a prior claim. It is not the artifact, and this checkout cannot repeat the hash.

## Partial links that remain valid

- The packaged prototype ZIP is present and matches its recorded SHA-256.
- The historical packager blob matches the packager hash stored in the ZIP.
- The packager names the campaign directory and the sweep parent policies.
- The packaged Development evaluation IDs match the IDs the prior audit computed for the older campaign Development files.
- Training-manifest hashes are cited consistently by the recovery record, `input-hashes.json`, the flexible-heldout specification, and compound-study replay inputs.

These links support a partial derivation story. They leave the original bytes unverified in this environment.

## Evidence required from the original executor or artifact holder

1. Commit `1277e9d3ce91f1395e3deed7e7202748a5a04672`, or the four training and Development files whose SHA-256 values match the recorded hashes.
2. The two sweep parent `policy.json` files, for comparison with the packaged member hashes.
3. The two campaign `calibration.json` files and the recording bundle the packager reads from `build/multitask-policy42`.
4. `original-execution-source.zip` with SHA-256 `f3a1d6109a94d394d93ab0deacb1e839489f65154265d0d298878f9344062896`.
5. Commits `17b695373f935dc1f5fd09c37cf8917969367f7a` and `2c9f697439d1d1c2ed7c0a92645848c0f07f7e3f`, if the recorded source revisions are to be checked.
6. Any original authorization record for requests `40cf4c15-2260-48ef-b3a1-7154d0d47554` and `bff23d52-aafc-4be6-8adb-3c7e8f88836c`, if one exists outside this repository.

Supplying a later rerun, a Phase 2 checkpoint, or a research_v1 cost calibration does not close these gaps.
