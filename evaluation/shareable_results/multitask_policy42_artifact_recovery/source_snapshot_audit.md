# Source snapshot audit

Audit date: 2026-11-15. This note records a read-only search for the original producer script and the recorded application source digest. Recovered campaign JSON was left unchanged. Conclusion: **PARTIALLY VERIFIED**.

The producer script is an exact SHA-256 match and is now stored beside the factual snapshots. The recorded application source digest was not reproduced from any inspected Git tree, dangling object, or the current working tree. That digest is **UNRECOVERABLE WITHIN AVAILABLE SOURCES**. This is a limit of the sources that could be inspected, not a claim that the bytes are gone from every machine that ever ran the campaign.

## Source snapshot inventory

| Path in the publication commit | Git blob | Bytes | SHA-256 |
|---|---|---|---|
| `build/multitask-policy42/sources/LICENSE` | `b03120fdfc027ace0e634e9e0c71581c77f660c0` | 25313 | `a221a27af5e4ef5a9cecce097c718c28f1aaf7d368cb57c994aa447c68d9defc` |
| `build/multitask-policy42/sources/countries-revision.json` | `225b15a9f966479c8be775aa20c9013d9496f3fb` | 99 | `102428d79a671fa4394dd487e75f8daf517fc388aa86793d8b4575a68c170ba7` |
| `build/multitask-policy42/sources/countries.json` | `455b3fd85abcf8fa01e0fca63e84a853c9ff4422` | 1398004 | `0d92fb23b43ae080bd439f5dc5d61a8845395fdd0af1479b433c59fe079bd6fd` |
| `build/multitask-policy42/sources/geonames-countryInfo.txt` | `11f5507ea45b3067c10a2cc2522586d4418355ff` | 32115 | `5c710efde90ee4cca15001c9f6a97ae7a74c7020b365504913ddc3afeb6d3671` |

Copies of those four blobs are in `execution-source/recovered-snapshots/`. `countries-revision.json` records countries source commit `6031f5df137c41c76d180c55a0782185ae3ed05b` from `git ls-remote refs/heads/master`.

None of those four publication paths is a Python script, and none of their SHA-256 values is the recorded producer-script hash. The producer copy added later in this audit is a separate file in the same recovered-snapshots folder.

## Producer script

Recorded producer SHA-256, from both recovered `fit-provenance.json` files: `174a7b965a15e9a6540f06705c7d330b81de9de45187a638dded4acb1bfaa5ea`.

`fit_phase` sets that field to `sha256(Path(__file__).read_bytes())`, the bytes of the script that performed the fit.

Exact match recovered from Git blob `48722f26b49300d60d1ae9ebbb07ce904db3698e`:

| Item | Value |
|---|---|
| Path in those commits | `scripts/multitask_policy42.py` |
| Bytes | 56137 |
| SHA-256 | `174a7b965a15e9a6540f06705c7d330b81de9de45187a638dded4acb1bfaa5ea` |
| Copy | `execution-source/recovered-snapshots/multitask_policy42.py` |
| Commits containing that blob | `a586dd30a71b27e5b846642f45120e4f3c86b465` (2026-10-31, “Codex/offline policy recording pilots (#26)”) and `1415d9cc15df4f995beab4291377870a79198418` (2026-11-01, “Merge remote-tracking branch 'origin/main' into tanmayee-integration”) |

Both commits are reachable from `main`, `raunak-exp-3`, `tanmayee-integration`, and the matching `origin` branches. The copy was written from `git cat-file blob` and rehashed to the recorded digest before it was accepted.

These files were checked and are different bytes, so they were not used as the producer:

| Candidate | Bytes | SHA-256 |
|---|---|---|
| Publication commit `1277e9d3ce91f1395e3deed7e7202748a5a04672` `scripts/multitask_policy42.py`, blob `8d02135c32eac04ea0588175f1aabd522de653be` | 56573 | `60650fc9d21c6716a02efea144a4c4960d743f26cbba2a6dd96161fc194e7b20` |
| Current working tree `scripts/multitask_policy42.py` | 57186 | `7274947d89d065a76a6ffb8465f6d7e1a8a4cb8758cebfd6ffeecb5d5f21ed1c` |
| Fit revision `17b695373f935dc1f5fd09c37cf8917969367f7a` | Path absent | — |

The commit set is the union of `git rev-list --all --reflog` and the fetched commits `1277e9d3…`, `17b69537…`, and `2c9f6974…`: 208 commits. Only two distinct `scripts/multitask_policy42.py` blobs exist in that set. One is the exact producer. The other is the publication script above, present in 49 of those commits. Five dangling commits from `git fsck --dangling` contain either no script at that path or the publication hash `60650fc9…`. Forty-three dangling trees and zero dangling blobs produced no second copy of the producer hash.

## Application source digest

The digest requested for comparison is `d2565ca4897a9e1f938900f4feb80fe675b9229c2acb7b27544781ec1c9bdcaf`. It is stored in the publication file `build/multitask-prototype42-v1/runtime-requirements.json`.

The packager computes it as `content_id` of `[(path, sha256)]` for `sorted(Path('app').rglob('*.py'))`, with `path` from `Path.as_posix()`. `content_id` is SHA-256 of canonical JSON: tuples become lists, object keys are sorted, separators are commas and colons, and the encoding is UTF-8. The same formula is used for `current_application_source_digest` in `fit_phase`, and for `MeasurementSetup.application_source_digest` in `recording_adapters.py` with paths relative to the repository root.

Those procedures hash the working tree’s `app/**/*.py` files. They do not hash `build/multitask-policy42/sources/`.

Recomputation used the same `content_id` procedure: each `*.py` path relative to the repository root, paired with its file SHA-256, sorted by path components, then hashed as canonical JSON.

| Tree | `app/**/*.py` files | Digest | Against `d2565ca4…`, `2926e051…`, and `47597967…` |
|---|---|---|---|
| Publication commit `1277e9d3ce91f1395e3deed7e7202748a5a04672` | 119 | `8c11085693bdd9a969f1e6dd29d30cb06fba09af15d0b09a2fbbbc37c9ffafe7` | Different from all three |
| Fit revision `17b695373f935dc1f5fd09c37cf8917969367f7a` | 105 | `0bf17b9ee18442bd36082aa62855b46e2a5ae270659374141c98aa3f5f543dc1` | Different from all three |
| 131 distinct `app` trees in the 208 reachable and reflog commits | 31–142 | none equal to a recorded digest | No match |
| 5 dangling commits and 43 dangling trees | varies | none equal to a recorded digest | No match |
| Current working tree | 142 | `ce54eac933bc55cd9a944647b42513fa8b96e843e9537f31b2c2d4578ac5fe56` | Different from all three |

The recorded digests remain historical references to working trees that are not stored as these commits. The application source set for `d2565ca4…` was not recovered.

## Locations investigated

Searches were read-only. No campaign was rerun, and no Final Test labels or sealed custody archives were opened.

| Location | What was done | Result |
|---|---|---|
| This clone, `D:\projects\Multi-agent-verification` | Union of `git rev-list --all --reflog` and fetched commits `1277e9d3…`, `17b69537…`, and `2c9f6974…` (208 commits, including stashes). Every distinct `scripts/multitask_policy42.py` blob was hashed. Every distinct `app` tree was digested. | Producer blob found. No application-digest match. |
| Dangling Git objects | `git fsck --dangling`: 5 commits, 43 trees, 0 blobs. Python files in those trees were hashed and digested with the same algorithm. | No producer hash and no recorded application digest. |
| Branches containing the producer blob | `git branch -a --contains` on both producer commits | Present on `main`, `raunak-exp-3`, `tanmayee-integration`, and their `origin` counterparts. |
| Current working tree | Hashed `scripts/multitask_policy42.py` and digested `app/**/*.py` | Both differ from the recorded values. |
| `build/` and `evaluation/` | Filename search for `multitask_policy42.py` | The only hit is the copy extracted during this audit. |
| `C:\Users\Raunak\OneDrive` | Filename search for `multitask_policy42.py`, depth 6 | No file. A full content hash of OneDrive was not run. |
| `C:\Users\Raunak\Backup`, `Backups`, `FileHistory`, and `D:\backup` | Path existence check | Those directories do not exist. |
| CI artifacts | Looked for a local `.github` workflow directory and for a local `gh` client | No `.github` directory in this clone. `gh` is not installed, so remote GitHub Actions artifacts were not queried. |
| Original campaign machine | Compared the recorded fit environment with this host | Fit provenance records Windows 10.0.26200. This host is Windows 10.0.26300. That earlier machine was not accessed. |

## What remains missing

- The working-tree `app/**/*.py` set that yields `d2565ca4897a9e1f938900f4feb80fe675b9229c2acb7b27544781ec1c9bdcaf`.
- The working-tree sets for the collection digest `47597967…` and the fit digest `2926e051…`.
- `artifacts/compound-study-36-v1/local-custody/original-execution-source.zip` (expected SHA-256 `f3a1d6109a94d394d93ab0deacb1e839489f65154265d0d298878f9344062896`).
- A dependency lock or hardware record inside `build/multitask-policy42/sources/`. Environment versions remain only in the recovered fit provenance.

## Classification

**PARTIALLY VERIFIED.** The producer script is an exact hash match. The application source digest `d2565ca4897a9e1f938900f4feb80fe675b9229c2acb7b27544781ec1c9bdcaf` remains unavailable within the sources above. The original execution-source ZIP, expected SHA-256 `f3a1d6109a94d394d93ab0deacb1e839489f65154265d0d298878f9344062896`, also remains unavailable.
