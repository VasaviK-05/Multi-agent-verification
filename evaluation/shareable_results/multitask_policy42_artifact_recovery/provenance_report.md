# Provenance

Recovery date: 2026-11-15. Method: `git fetch origin 1277e9d3ce91f1395e3deed7e7202748a5a04672`, then `git cat-file` of the listed paths. The blobs were written only under this shareable directory. The ignored `build/multitask-policy42` tree was not recreated. No experiment directory was written.

Publication commit: `1277e9d3ce91f1395e3deed7e7202748a5a04672`, 2026-11-01, message “Publish original owned study inputs and preservation handoff.” That commit was absent from this clone before the fetch. It is now in the local object database. No branch was created or moved, and nothing was committed or pushed.

## Originally generated

`scripts/multitask_policy42.py` in the publication commit prepares frames, and `fit_phase` writes `calibration.json` from the completed recording bundle, then `training-manifest.json` and `development-evaluation.json`. The recovered `fit-provenance.json` files record that procedure:

- Authority string: `User request 40cf4c15-2260-48ef-b3a1-7154d0d47554: task-conditioned exploratory collection and reliability-first fits`
- Code revision recorded at fit: `17b695373f935dc1f5fd09c37cf8917969367f7a`
- Producer script SHA-256 recorded at fit: `174a7b965a15e9a6540f06705c7d330b81de9de45187a638dded4acb1bfaa5ea`
- Collection application digest: `47597967da7d8f05aa56ef1ed6fbd544eb70e607aaf8804e5163e650cea35e4d`
- Fit-time application digest: `2926e0513be4c929d33bbcfa15787ee76fd96328a509821d91c71ff0467dc238`
- Settings in `authorization/study-audit.json`: seed 42, losses 1.0 / 1.0 / 0.2, priors 1.0 / 1.0, threshold 0.55, `q_min` 0.9
- Preparation version: `multitask_frames_v2_exact_source_numbers`
- Split rule recorded there: uniform `n=min(60, 3*floor(eligible/3))`, seed 42, twenty groups per partition, no outcome-based exclusions

The exact producer script is `execution-source/recovered-snapshots/multitask_policy42.py`, Git blob `48722f26b49300d60d1ae9ebbb07ce904db3698e`, SHA-256 `174a7b965a15e9a6540f06705c7d330b81de9de45187a638dded4acb1bfaa5ea`. It is the `scripts/multitask_policy42.py` blob in commits `a586dd30a71b27e5b846642f45120e4f3c86b465` and `1415d9cc15df4f995beab4291377870a79198418`. The publication copy hashes to `60650fc9d21c6716a02efea144a4c4960d743f26cbba2a6dd96161fc194e7b20` and was not substituted. Commit `17b69537` does not contain that path. The application source digest was not reproduced; see `source_snapshot_audit.md`.

## Byte verification

| File | SHA-256 | Result |
|---|---|---|
| `arithmetic/training-manifest.json` | `c87d65246015919c02d86c4c83f39e0ded6ede02d25aa551a034b66a738ed485` | Matches the historical file hash |
| `factual/training-manifest.json` | `9be8da9773eaced47faae3ff49e4e1536391be21824bb29f1e2c664cf5fd6e3c` | Matches the historical file hash |
| `arithmetic/development-evaluation.json` | `e146f2adafe5cfde34395aa4478e2f584d68c597f96a7f8e4efbd7c7c9c87a97` | Matches the historical file hash. Content ID `b1101768d7a2ba0ea44da68708767c2301a54a3006be9f9116f4b471cef3e76d` |
| `factual/development-evaluation.json` | `fb00b72373e64d08f3566c119a12a19e35af0994bbbb32d1036dbe498ffe86b9` | Matches the historical file hash. Content ID `28268477feeadf614f121eb138718a9c304a7b9bd4f6522400343bfff7d1750c` |
| `arithmetic/calibration.json` | `3e9a9c5c68ffc8976f172b465a414c3a4748b8cc762149c8500cec1557a99770` | Calibration ID `9678fb81adb197893d768db84dd5e8196ca5780600ccfd6a15c71d61f1da41a0` and input digest `71f3709b1c8c398c3f5c321ce6246b09d7dea292e6a603e1c6d9cc1751ef5ff3` match. No earlier file hash was on record. |
| `factual/calibration.json` | `767124a949d96aa2bf6142ca2b9abc77d0fecb76314425885bb38da84338f13e` | Calibration ID `084b056eefcc44842c7d66f6896b70b35b33d3f7cc11ecf4cb8c88ff7119e63d` and input digest `f270fcb53ca16bba54daf4ba517a1556cb50bdd0d231d4b51d81f54b20cf97f1` match. No earlier file hash was on record. |

Training manifest IDs inside the fit provenance are `3a0e3dae9e7ca6652178656942442495e076f9dc48f9d34f82f95c5971c39db3` for Arithmetic and `071125d9bf7a870e9f79fb204181c10ceb17485c8f4b18de3b5cc0845c341d8a` for Factual.

## Policies

`related_original_policies/arithmetic-coverage-50-policy.json` is the publication blob `build/multitask-uncertainty-sweep42/arithmetic/coverage-50/policy.json`, SHA-256 `ec1be5b69766948bbb444557806a6895cddf573f37c97e03472531685dde282c`.

`related_original_policies/factual-coverage-25-policy.json` is `build/multitask-uncertainty-sweep42/factual/coverage-25/policy.json`, SHA-256 `df1bef32fa422cadb29cc6034b9968ea9fd01d3dcea847e6d7e96382c0889d87`.

Those two hashes are the same as the Arithmetic and Factual policy members inside `artifacts/policies/multitask-prototype42-v1.zip`. The ZIP in this commit is 41,243 bytes, SHA-256 `99516fbe460e816c68601509ca7e202cbcd3880d8d4250ec655f422244ec657c`, the same object as the ZIP already tracked at `artifacts/policies/multitask-prototype42-v1.zip`. A copy is in `related_original_policies/`.

## Environment recorded with the fit

Python 3.11.5, CPython, Windows 10.0.26200, AMD64, NumPy 2.4.6, SciPy 1.17.1, PyTorch is not in the solver environment block, pydantic 2.13.5, HiGHS 1.12.0, solver `scipy.optimize.linprog:highs`. `authorization/campaign-execution.json` says three cohort workers overlapped on one local CPU and Ollama service, with per-cohort attempt wall times under that contention. No separate hardware model, GPU, or lockfile was in the recovered campaign files.

## Authorization evidence that was recovered

`authorization/study-audit.json` and both `fit-provenance.json` files contain the campaign authority string. `authorization/prototype-bundle-manifest.json` is the publication file `build/multitask-prototype42-v1/manifest.json` and contains `User packaging approval bff23d52-aafc-4be6-8adb-3c7e8f88836c`. These are the original embedded records. No separate signed approval document was in the commit.

## Execution source

`artifacts/compound-study-36-v1/local-custody/original-execution-source.zip` is not in this commit, in `17b69537`, or in `2c9f697439d1d1c2ed7c0a92645848c0f07f7e3f`. It was not recreated.

Recorded source identities, which are not substitutes for that ZIP:

- Fit code revision `17b695373f935dc1f5fd09c37cf8917969367f7a`, tree `a0297b1c504545f1687bc1efa1e240223aa68128`, message “Merge latest origin/main into offline policy recording pilots.”
- Custody metadata revision `2c9f697439d1d1c2ed7c0a92645848c0f07f7e3f`, tree `52a4d433f6a513479a5eb09bff1575e7e65a7e10`. This is a different commit from the fit revision.
- Collection application digest `47597967da7d8f05aa56ef1ed6fbd544eb70e607aaf8804e5163e650cea35e4d`, also stored in `execution-source/collection-source-freeze.json`.

Those digests were not recomputed against a full working tree in this delivery.
