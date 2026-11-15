# Remaining gaps

Originals that are now in this folder are not listed here as missing.

## Not recovered

| Item | Status | What is still required |
|---|---|---|
| `artifacts/compound-study-36-v1/local-custody/original-execution-source.zip` | `NOT_RECOVERABLE` from the publication commit, the fit revision, the custody-metadata revision, and the earlier local archive search | The ZIP whose SHA-256 is `f3a1d6109a94d394d93ab0deacb1e839489f65154265d0d298878f9344062896` |
| Application source digests | Recorded, and recomputed across reachable commits, reflog commits, dangling trees, and the current working tree | A tree whose digest matches `d2565ca4897a9e1f938900f4feb80fe675b9229c2acb7b27544781ec1c9bdcaf`, the collection digest `47597967da7d8f05aa56ef1ed6fbd544eb70e607aaf8804e5163e650cea35e4d`, or the fit digest `2926e0513be4c929d33bbcfa15787ee76fd96328a509821d91c71ff0467dc238`. None of those trees was found. See `source_snapshot_audit.md`. |
| Separate signed authorization | `NOT_RECOVERABLE` as a distinct document | The authority and packaging strings exist only inside the recovered study audit, fit provenance, and prototype manifest |
| Hardware inventory beyond the platform string | Not present in the recovered campaign files | An original hardware record, if one was kept outside Git |

## Not regenerated

Training manifests, Development evaluations, calibration, and recordings were recovered as original blobs, so they were not reproduced. A reproduction was not required and was not run. Later rerun directories were not copied.

## Out of scope for this package

The publication commit also contains the semantic cohort, budget sweeps, and source snapshots under `build/multitask-policy42/sources/`. Those were not extracted. Final Test label archives and custodian ZIPs were not opened.
