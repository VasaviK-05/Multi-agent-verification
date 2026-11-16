# multitask-policy42 artifact recovery audit

This record was written on 2026-11-15, after the original `multitask-policy42` campaign. It reports a read-only search of the sources available in this checkout. It does not recreate manifests, evaluations, policies, recordings, or calibration, and it does not claim that this document existed during the original execution.

## Search scope

Searched in this environment:

- The working tree, including gitignored `build/`.
- The local Git object database, including objects that would be dangling. `git cat-file` does not resolve the cited commits or blobs.
- All local branches, `origin` remote-tracking branches, and tags. No tags exist. No fetch was performed.
- `git log --all` and `git rev-list --all --objects` for `build/multitask-policy42`, `build/multitask-uncertainty-sweep42`, and `artifacts/compound-study-36-v1/local-custody/original-execution-source.zip`. Those paths have no Git object in this clone.
- `git reflog --all` for the cited commit prefixes and the campaign name. No matching reflog entry.
- ZIP central directories, excluding archives whose paths contain `final_test`, `_custodian`, or `sealed`. Members whose names contain `label` or `final_test` were not read.
- `Downloads`, `Desktop`, and `Documents` to depth 3 for campaign filenames.
- Existing provenance citations under `docs/experiment1/phase-c/`, `artifacts/flexible-heldout-v1/`, `artifacts/compound-study-36-v1/`, and `artifacts/publication-v1/`.

Protected Final Test label files, backups, and Final Test or custodian ZIPs were not opened, hashed, or extracted. `D:\projects\final-test-v2-sealed-custody` was not entered. `build/multitask-prototype42-current-v1-rerun1` and `build/multitask-policy42-phase2-v1` were identified and were not used as original campaign outputs.

## Inventory

| Artifact | Classification | Where the bytes are |
|---|---|---|
| `build/multitask-policy42/arithmetic/training-manifest.json` | `NOT_FOUND_AFTER_SEARCH`; provenance `PARTIALLY_TRACEABLE` | Absent here. Prior recovery record cites commit `1277e9d3ce91f1395e3deed7e7202748a5a04672` and SHA-256 `c87d65246015919c02d86c4c83f39e0ded6ede02d25aa551a034b66a738ed485`. That commit is not in this clone, so the hash was not recomputed. |
| `build/multitask-policy42/factual/training-manifest.json` | `NOT_FOUND_AFTER_SEARCH`; provenance `PARTIALLY_TRACEABLE` | Same commit citation. Recorded SHA-256 `9be8da9773eaced47faae3ff49e4e1536391be21824bb29f1e2c664cf5fd6e3c`. Hash not recomputed. |
| `build/multitask-policy42/arithmetic/development-evaluation.json` | `NOT_FOUND_AFTER_SEARCH`; provenance `PARTIALLY_TRACEABLE` | Same commit citation. Recorded SHA-256 `e146f2adafe5cfde34395aa4478e2f584d68c597f96a7f8e4efbd7c7c9c87a97`. Hash not recomputed. |
| `build/multitask-policy42/factual/development-evaluation.json` | `NOT_FOUND_AFTER_SEARCH`; provenance `PARTIALLY_TRACEABLE` | Same commit citation. Recorded SHA-256 `fb00b72373e64d08f3566c119a12a19e35af0994bbbb32d1036dbe498ffe86b9`. Hash not recomputed. |
| `build/multitask-policy42/arithmetic/calibration.json` | `NOT_FOUND_AFTER_SEARCH` | No file, Git object, or archive member. No reference SHA-256 for this path was found. |
| `build/multitask-policy42/factual/calibration.json` | `NOT_FOUND_AFTER_SEARCH` | No file, Git object, or archive member. No reference SHA-256 for this path was found. |
| `build/multitask-uncertainty-sweep42/arithmetic/coverage-50/policy.json` | `NOT_FOUND_AFTER_SEARCH`; parent link `PARTIALLY_TRACEABLE` | Declared source of the packaged Arithmetic policy. The parent file is absent. |
| `build/multitask-uncertainty-sweep42/factual/coverage-25/policy.json` | `NOT_FOUND_AFTER_SEARCH`; parent link `PARTIALLY_TRACEABLE` | Declared source of the packaged Factual policy. The parent file is absent. |
| `artifacts/compound-study-36-v1/local-custody/original-execution-source.zip` | `NOT_FOUND_AFTER_SEARCH` | Custody metadata records SHA-256 `f3a1d6109a94d394d93ab0deacb1e839489f65154265d0d298878f9344062896`. The ZIP is absent. The hash was not matched to any scanned archive. |
| `artifacts/policies/multitask-prototype42-v1.zip` | `RECOVERED_AND_HASH_VERIFIED` as the packaged bundle, not as an original training or Development file | 41,243 bytes. SHA-256 `99516fbe460e816c68601509ca7e202cbcd3880d8d4250ec655f422244ec657c`. Git blob `33c7cee96711e80dce4b11aa73ef95a1b555cba2` at `d9c19adc00d9ade7292e02557205dc5fcf1e41b9`. |

No requested original file was `RECOVERED_HASH_MISMATCH` or `RECOVERED_WITHOUT_REFERENCE_HASH`. A hash match requires the bytes. Those bytes were not present for the original manifests, evaluations, calibration files, parent policies, or execution-source ZIP.

## Citations that are not the original files

These records repeat hashes or paths. They are not substitutes for the missing bytes.

- `docs/experiment1/phase-c/recovery-investigation.json` and `docs/experiment1/phase-c/CONTINUATION.md` assign the four training and Development hashes to commit `1277e9d3ce91f1395e3deed7e7202748a5a04672`. This clone cannot open that commit.
- `artifacts/publication-v1/public-audit/artifacts/flexible-teams-v1/input-hashes.json` maps the same four hashes to the canonical `build/multitask-policy42` paths.
- `artifacts/flexible-heldout-v1/evaluation-specification.json` and `artifacts/compound-study-36-v1/atomic-replay-inputs.json` cite the two training-manifest hashes.
- `artifacts/compound-study-36-v1/execution-source-custody.json` records the execution-source ZIP hash, source revision `2c9f697439d1d1c2ed7c0a92645848c0f07f7e3f`, and application digest `daf466121a83c800b1116f97c6a07d62685fd1b18d4a7100f47bde0c819a441a`. The revision is not in this clone. The digest was not recomputed.
- `artifacts/research-v1-development-cost-calibration-v1/calibration.json` is a later research_v1 cost calibration. It is not a `multitask-policy42` calibration file.

## Packaged policies checked in this audit

`artifacts/policies/multitask-prototype42-v1.zip` contains Arithmetic and Factual policy bundles and Development metrics. Verified identities:

- Bundle version `bounded_task_policy_bundle_v1`.
- Approval string: `User packaging approval bff23d52-aafc-4be6-8adb-3c7e8f88836c: arithmetic existing50%, factual existing25% experimental; no activation`.
- Arithmetic artifact ID `e4981bb78a278f216efb0ece9b79eca8381fbaacdf6315e8bcb4cbc6bbb638f2`. Member `arithmetic/policy.json` is 45,134 bytes, SHA-256 `ec1be5b69766948bbb444557806a6895cddf573f37c97e03472531685dde282c`. `source_evaluation_id` `b1101768d7a2ba0ea44da68708767c2301a54a3006be9f9116f4b471cef3e76d`. Calibration ID `9678fb81adb197893d768db84dd5e8196ca5780600ccfd6a15c71d61f1da41a0`.
- Factual artifact ID `c66e137fd64f61222e4a69cf0e025b91bc1d3ae075166743f2c795acd9d7cd79`. Member `factual/policy.json` is 44,449 bytes, SHA-256 `df1bef32fa422cadb29cc6034b9968ea9fd01d3dcea847e6d7e96382c0889d87`. `source_evaluation_id` `28268477feeadf614f121eb138718a9c304a7b9bd4f6522400343bfff7d1750c`. Calibration ID `084b056eefcc44842c7d66f6896b70b35b33d3f7cc11ecf4cb8c88ff7119e63d`.
- Shared execution configuration `e23c6f034a4c660d30433d133be3a197db620abbdf22a78907ef5e3687d45ccb`.
- `runtime-requirements.json` records source revision `17b695373f935dc1f5fd09c37cf8917969367f7a`, application digest `d2565ca4897a9e1f938900f4feb80fe675b9229c2acb7b27544781ec1c9bdcaf`, and packager SHA-256 `584ee68129922a6bf71ea5bff0f82d42bf38494266c873dd5fad015a5a57848d`.

The packager hash matches Git blob `407b0bd875918833496dc41ada8ce8e61da4d7d3` (`scripts/package_multitask_prototype.py` at `d9c19ad` and `2c3813b58761b4b10a05d41d532d8d10575d16a3`), 11,198 bytes. The current working-tree copy of that script is a later file, SHA-256 `a33463395021fe8c3ee474cd2bfcf959ee5929fd1cff46b5bbb51a56300469a0`. The historical blob is the packager linked to the ZIP.

That historical packager sets `SOURCE` to `build/multitask-uncertainty-sweep42` and `STUDY` to `build/multitask-policy42`. It copies `arithmetic/coverage-50/policy.json` and `factual/coverage-25/policy.json` and reads each cohort's `calibration.json`. Those inputs are absent, so the byte copy from the parent policies was not rechecked.

The packaged `source_evaluation_id` values equal the Development content IDs that `recovery-investigation.json` attributes to the original Development files. That equality is a match between the package and a later audit record. It is not a new hash of the missing Development files. The same audit says those older Development records differ from a later current-policy binding (`a59218d2a00b4f09c4ef6e444682d3e20381ebd45b8c5bc76a89b923ed6658df` and `ee242866bcaff592167ec3ba21723c82c916b576b49187c27dbc7b643a04effc`). The prototype binds to the older IDs.

Dataset names inside both packaged policies are `multitask42-arithmetic-*` and `multitask42-factual-*`. Those names connect the policies to the campaign vocabulary. They do not prove byte identity with the missing manifests.

## Later artifacts kept separate

`build/multitask-prototype42-current-v1-rerun1` is a later bundle. Its approval text says original artifacts remain historical. Its artifact IDs are `1a336129b0c32b8634e434be7c1ff3a8ef73f79353270be03ce61ecf2e91f697` and `d65f9a06e87621225d948cc3412f1098141893460e360661a08fb105cdc38dbb`. Its `source_evaluation_id` values are `8bc5948c651bcd3fdf243187af0c815bbc19d026563dd3929856aa8ae4c71712` and `23dbb17397a919967ea788e792c0ea933bdb6fe4993ea90b0ec08d9486a365e0`. Policy file hashes are `965c55fd4987c359fc3e12491b224dc5c3807a0707a17c4c9905466cc3dbe901` and `a4e20be215f66af908f05b2c9dc4efe414c9ae6ca14a56d1141d65ed41c222b9`.

`build/multitask-policy42-phase2-v1/campaign-checkpoint.json` records those same later policy hashes and different calibration IDs (`357ca8dc3dfb273de028ba4bd7b317b6b223fb8c907d2513bcd1228452cf3c13` and `42ad21401196b164eee5847d1e7f1b1d211fa7302bd9e0224e807ebdac181f04`). The checkpoint lists recording hashes. The recording files are not in that directory.

## Campaign authority strings

`scripts/multitask_policy42.py` contains the authority string `User request 40cf4c15-2260-48ef-b3a1-7154d0d47554` for exploratory collection and reliability-first fits. The ZIP contains the packaging approval string cited above. No signed campaign-authorization or collection-authorization record for `multitask-policy42` was found. `docs/multitask_policy_results.md` describes the campaign as an exploratory engineering run of 240 history/development candidates and 960 verifier attempts. That document is a results narrative, not the missing recording manifest.

## Environment recorded by the package

The ZIP records Python 3.11.5, Windows 10.0.26200, AMD64, NumPy 2.4.6, SciPy 1.17.1, PyTorch 2.14.0, transformers 5.17.0, and sentence-transformers 6.1.0. Source revision `17b695373f935dc1f5fd09c37cf8917969367f7a` is not in this clone. No campaign lockfile or separate hardware log was found. The execution-source ZIP is the registered container for the original source export, and it is absent.

## Experiments left unchanged

During this audit, Experiment 3 `results.json`, `metrics.json`, and `bootstrap_results.json`, and Experiment 1 `development/metrics.json`, still match their previously recorded SHA-256 values. No experiment file was rewritten. Final Test labels were not accessed.
