# Retrospective provenance for multitask-policy42

Created 2026-11-15, after the original campaign and after the read-only search in `multitask_policy42_artifact_recovery_audit.md`. This file did not exist during the original execution. It preserves identifiers and recorded hashes. It does not reconstruct original manifests, evaluations, timestamps, or authorization records.

Retrospective documentation makes the remaining chain easier to follow. It does not replace missing original evidence and it does not authorize Experiment 2 completion.

## Status of each layer

| Layer | Status on 2026-11-15 | How to read it |
|---|---|---|
| Original campaign tree `build/multitask-policy42` | Absent from this checkout and from this Git database | Paths and recorded hashes below are citations. |
| Original sweep parents `build/multitask-uncertainty-sweep42` | Absent | Named by the historical packager. |
| Packaged bundle `artifacts/policies/multitask-prototype42-v1.zip` | Present and hash-verified | A packaging of existing policies. It is not the training manifest or the Development evaluation file. |
| Later rerun `build/multitask-prototype42-current-v1-rerun1` and Phase 2 checkpoint | Present locally, gitignored | Different artifact IDs, calibration IDs, and `source_evaluation_id` values. Not originals. |
| This document and the two companion notes | Retrospective | Written after the search. |

## Verified in this checkout

- Prototype ZIP: 41,243 bytes, SHA-256 `99516fbe460e816c68601509ca7e202cbcd3880d8d4250ec655f422244ec657c`, blob `33c7cee96711e80dce4b11aa73ef95a1b555cba2`, commit `d9c19adc00d9ade7292e02557205dc5fcf1e41b9`.
- Historical packager blob `407b0bd875918833496dc41ada8ce8e61da4d7d3`, SHA-256 `584ee68129922a6bf71ea5bff0f82d42bf38494266c873dd5fad015a5a57848d`, equal to the hash stored in the ZIP `runtime-requirements.json`.
- Arithmetic packaged policy member SHA-256 `ec1be5b69766948bbb444557806a6895cddf573f37c97e03472531685dde282c`, artifact ID `e4981bb78a278f216efb0ece9b79eca8381fbaacdf6315e8bcb4cbc6bbb638f2`.
- Factual packaged policy member SHA-256 `df1bef32fa422cadb29cc6034b9968ea9fd01d3dcea847e6d7e96382c0889d87`, artifact ID `c66e137fd64f61222e4a69cf0e025b91bc1d3ae075166743f2c795acd9d7cd79`.
- Packager source constants: study directory `build/multitask-policy42`; parent policies `build/multitask-uncertainty-sweep42/arithmetic/coverage-50/policy.json` and `build/multitask-uncertainty-sweep42/factual/coverage-25/policy.json`.

## Recorded original identifiers, not rehashed here

These values come from existing records. This audit did not recompute them from original bytes.

| Path | Recorded SHA-256 | Recorded location |
|---|---|---|
| `build/multitask-policy42/arithmetic/training-manifest.json` | `c87d65246015919c02d86c4c83f39e0ded6ede02d25aa551a034b66a738ed485` | `1277e9d3ce91f1395e3deed7e7202748a5a04672` in the prior recovery record. Commit absent here. |
| `build/multitask-policy42/factual/training-manifest.json` | `9be8da9773eaced47faae3ff49e4e1536391be21824bb29f1e2c664cf5fd6e3c` | Same commit. Absent here. |
| `build/multitask-policy42/arithmetic/development-evaluation.json` | `e146f2adafe5cfde34395aa4478e2f584d68c597f96a7f8e4efbd7c7c9c87a97` | Same commit. Content ID recorded as `b1101768d7a2ba0ea44da68708767c2301a54a3006be9f9116f4b471cef3e76d`. |
| `build/multitask-policy42/factual/development-evaluation.json` | `fb00b72373e64d08f3566c119a12a19e35af0994bbbb32d1036dbe498ffe86b9` | Same commit. Content ID recorded as `28268477feeadf614f121eb138718a9c304a7b9bd4f6522400343bfff7d1750c`. |
| `artifacts/compound-study-36-v1/local-custody/original-execution-source.zip` | `f3a1d6109a94d394d93ab0deacb1e839489f65154265d0d298878f9344062896` | Named by `execution-source-custody.json`. File absent. |

The packaged Arithmetic and Factual `source_evaluation_id` values are the two content IDs in the table. That is a link between the package and the prior audit's description of the older Development files. It becomes a byte-verified link only when those Development files are hashed again.

## Inferred, and still unverified

- The historical packager's statement that it copied the sweep policies without changing bytes. The parent files are missing, so the inference stands on the script and the packaged members.
- The inference that those sweep policies were fitted from `build/multitask-policy42` training and Development files. Dataset names and the evaluation-ID match support that reading. The training manifests and calibration files are missing.
- The inference that source revision `17b695373f935dc1f5fd09c37cf8917969367f7a` is the campaign code snapshot. The ZIP records it. The commit is not in this clone.
- The inference that user-request strings `40cf4c15-2260-48ef-b3a1-7154d0d47554` and `bff23d52-aafc-4be6-8adb-3c7e8f88836c` were the campaign and packaging authorizations. They are strings in the script and the ZIP. No signed record was found.

## Explicitly not claimed

- These notes were not part of the original campaign.
- The later rerun and Phase 2 checkpoint are not the original campaign outputs.
- Research_v1 cost calibration is not the campaign calibration.
- Matching dataset names or Development metrics are not, by themselves, proof of byte-level derivation.
- Absence from this working tree is not proof that the original files never existed. The prior recovery record says the four training and Development files were published in a commit this clone does not have.
- This provenance note does not decide Experiment 2 completion.
