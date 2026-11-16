# Experiment 2 final source-custody reconciliation

Date: 2026-11-16. Read-only. No campaign was rerun, no historical artifact was regenerated or edited, and no Final Test questions, labels, answers, scores, or outcome payloads were opened.

Overall status: **UNRECOVERABLE WITHIN AVAILABLE CUSTODY SOURCES** for the requested execution-source archive and the three requested application source trees. Preserved metadata records those digests and one different source-hash list. The file bytes for the requested trees were not recovered.

The research-protocol Experiment 2 proposal (`evaluation/config/experiments/experiment2_proposal.json`) is “Budget sensitivity,” `PENDING_PERSON2_COSTS_AND_APPROVAL`, `collection_authorized: false`. It does not contain these artifacts. The hashes below are the compound-study execution-source custody record and the multitask-policy42 collection and fit records named in this audit.

## Digest procedure

`application_source_digest` is `content_id` of `[(path, sha256)]` for `sorted((ROOT / 'app').rglob('*.py'))`, with `path` relative to the repository root in POSIX form. `content_id` is SHA-256 of canonical JSON: nested tuples become lists, object keys are sorted, separators are commas and colons, and the encoding is UTF-8 (`app/game/models.py`, `app/game/offline/recording_adapters.py`). Commit trees were hashed the same way from `git ls-tree -r <commit>:app` and `git cat-file blob`. No other hashing procedure was used.

## Search scope

Inspected:

- This clone, including `artifacts/compound-study-36-v1/`, the recovery package `evaluation/shareable_results/multitask_policy42_artifact_recovery/`, and the earlier audits `evaluation/docs/multitask_policy42_provenance_gaps.md`, `multitask_policy42_retrospective_provenance.md`, `multitask_policy42_artifact_recovery_audit.md`, and `source_snapshot_audit.md`.
- Commits `17b695373f935dc1f5fd09c37cf8917969367f7a`, `1277e9d3ce91f1395e3deed7e7202748a5a04672`, and `2c9f697439d1d1c2ed7c0a92645848c0f07f7e3f`, recomputed on 2026-11-16.
- The earlier read-only pass over 208 reachable and reflog commits (131 distinct `app` trees), 5 dangling commits, and 43 dangling trees, which found no match for these three digests (`source_snapshot_audit.md`).
- Filename search for `original-execution-source.zip` in this repository, Downloads, Desktop, Documents, and OneDrive to depth 5.
- `execution-source-custody.json` as a hash list only.

Not available:

- `artifacts/compound-study-36-v1/local-custody/` does not exist in this checkout.
- The machine recorded for the external path in the Phase C audit was not accessed.
- OneDrive was searched by filename to depth 5, not by hashing every file.
- Remote CI artifacts were not queried.
- Current `app/**/*.py` and the current installed packages were not used as substitutes.

## Requested archive

| Item | Result |
|---|---|
| Expected path | `artifacts/compound-study-36-v1/local-custody/original-execution-source.zip` |
| Expected SHA-256 | `f3a1d6109a94d394d93ab0deacb1e839489f65154265d0d298878f9344062896` |
| Present | No. The `local-custody` directory is absent. The filename was not found in the locations above. |
| Classification | **UNRECOVERABLE WITHIN AVAILABLE CUSTODY SOURCES** |

`artifacts/compound-study-36-v1/execution-source-custody.json` names that archive and that SHA-256. The custody file itself is present. Its `publication` field says the archive was excluded by the local gitignore. The file bytes of the ZIP were not recovered, so that statement was not re-hashed.

## Requested application source sets

None of these trees was recovered. Recomputation of the named commits does not reproduce them.

| Recorded role | Digest | Where the digest is stored | Recomputed match |
|---|---|---|---|
| Prototype runtime digest. The fit provenance does not use this value as its fit-time digest. | `d2565ca4897a9e1f938900f4feb80fe675b9229c2acb7b27544781ec1c9bdcaf` | Publication `build/multitask-prototype42-v1/runtime-requirements.json`, cited by `source_snapshot_audit.md` | No |
| Collection digest | `47597967da7d8f05aa56ef1ed6fbd544eb70e607aaf8804e5163e650cea35e4d` | Both recovered `fit-provenance.json` files, field `source_setup.application_source_digest`; `execution-source/collection-source-freeze.json` | No |
| Fit-time working-tree digest | `2926e0513be4c929d33bbcfa15787ee76fd96328a509821d91c71ff0467dc238` | Both recovered `fit-provenance.json` files, field `current_application_source_digest` | No |

| Tree recomputed on 2026-11-16 | `app/**/*.py` files | Digest |
|---|---:|---|
| Fit revision `17b695373f935dc1f5fd09c37cf8917969367f7a` | 105 | `0bf17b9ee18442bd36082aa62855b46e2a5ae270659374141c98aa3f5f543dc1` |
| Publication commit `1277e9d3ce91f1395e3deed7e7202748a5a04672` | 119 | `8c11085693bdd9a969f1e6dd29d30cb06fba09af15d0b09a2fbbbc37c9ffafe7` |
| Custody revision `2c9f697439d1d1c2ed7c0a92645848c0f07f7e3f` | 119 | `8c11085693bdd9a969f1e6dd29d30cb06fba09af15d0b09a2fbbbc37c9ffafe7` |

Each of the three requested source sets is **UNRECOVERABLE WITHIN AVAILABLE CUSTODY SOURCES**. The fit revision is the `code_revision` stored in the fit provenance. It is a commit identifier, not a verified byte match to any of the three digests.

## Custody hash list for a different digest

`execution-source-custody.json` records `source_revision` `2c9f697439d1d1c2ed7c0a92645848c0f07f7e3f` and `application_source_digest` `daf466121a83c800b1116f97c6a07d62685fd1b18d4a7100f47bde0c819a441a`. That digest is not one of the three requested digests.

Recomputing `content_id` over its 120 `files` entries, sorted by path, reproduces `daf466121a83c800b1116f97c6a07d62685fd1b18d4a7100f47bde0c819a441a`. The list is a preserved hash manifest. The corresponding file bytes are not in the commit tree. The commit tree has 119 Python files and omits `app/benchmark/resource_diagnostics.py`, which is present only as a hash in the custody list. Classification of this hash list: **VERIFIED** as metadata. Classification of the source bytes it names: **UNRECOVERABLE WITHIN AVAILABLE CUSTODY SOURCES**.

## Previously recovered producer script

`evaluation/shareable_results/multitask_policy42_artifact_recovery/execution-source/recovered-snapshots/multitask_policy42.py` is the producer script, SHA-256 `174a7b965a15e9a6540f06705c7d330b81de9de45187a638dded4acb1bfaa5ea`, from blob `48722f26b49300d60d1ae9ebbb07ce904db3698e` in commits `a586dd30a71b27e5b846642f45120e4f3c86b465` and `1415d9cc15df4f995beab4291377870a79198418`. It was not modified for this audit. It is one script, not an `app/**/*.py` source set, and it was not substituted for any requested digest. Classification: **VERIFIED** for that script only.

## Dependency and environment evidence

No historical dependency lock or requirements freeze for these digests was recovered. The versions below are the recorded fit-provenance fields in `arithmetic/fit-provenance.json`. They are historical metadata, not a reinstalled environment.

Collection `source_setup.environment`: Windows 10.0.26200, AMD64, Intel64 Family 6 Model 154 Stepping 3, 16 logical CPUs, device `cpu`, concurrency `sequential`, Python `3.11.5`, physical memory 16,876,888,064 bytes, host fingerprint `22668bd8248802aee39bf300193a1cc6bf4ecbbbafed60f64538e50fe31a2ec7`.

Collection `source_setup.dependency_versions`: NumPy 2.4.6, pydantic 2.13.5, sentence-transformers 6.1.0, Transformers 5.17.0, Torch 2.14.0, faiss-cpu 1.15.1, Requests 2.34.2, Safetensors 0.8.0, Tokenizers 0.23.2, Python 3.11.5. sentencepiece is recorded as not installed.

Fit `environment`: NumPy 2.4.6, SciPy 1.17.1, pydantic 2.13.5, Python 3.11.5, CPython, Windows 10.0.26200, AMD64, HiGHS 1.12.0, solver `scipy.optimize.linprog:highs`.

Resource fingerprints recorded on the same collection setup include the evidence corpus `28e6241079b1afab419ebdbaea580510796c648d1855dcc91759ab3d8950b95a`, evidence index `e802300251695e22ff0de258b39da818488722df347e04af20507e240442489b`, local embedding snapshot `23c61c55d84d9ab0045288ba589018e80ff90cf894514f5676e351c14624d255`, local NLI snapshot `a28c08014f62b13be758a1f22d1cbfd30e9f7b0f91d19fbc3bd5c369b11fcf7e`, and Ollama model `a80c4f17acd55265feec403c7aef86be0c25983ab279d83f3bcd3abbcb5b8b72`. Those are recorded hashes, not recovered weight files.

Dependency and environment metadata: **PARTIALLY VERIFIED**. A lockfile and the source trees that produced the three requested digests are absent.

## Confirmation

No campaign was rerun. No historical artifact was rewritten. No Final Test data was accessed. Current application source and current package versions were not presented as the historical source.
