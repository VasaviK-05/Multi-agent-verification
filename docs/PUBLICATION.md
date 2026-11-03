# Publication record

Branch: `codex/flexible-verifier-teams` in the public [repository](https://github.com/VasaviK-05/Multi-agent-verification).

The reviewed implementation, policies, frozen evaluations and public audit views are in content commit [1139dd2d2a47e8fecbbbd2744d1d2e25908bf7ee](https://github.com/VasaviK-05/Multi-agent-verification/commit/1139dd2d2a47e8fecbbbd2744d1d2e25908bf7ee). Implementation base: `0b3595ef965d196f93916d10999c7fae63daf7af`.

This documentation/metadata overlay follows that content commit. Its own identity is the branch HEAD reported by Git and the final delivery; a document cannot contain its own commit hash. No policy or evaluation changes occur in this overlay. `file-hashes.json` records the original content commit; `file-hashes-v2.json` is authoritative for this final metadata overlay. Exact versions and the overlay file list are in [publication-record.json](../artifacts/publication-v1/publication-record.json).

Prepublication evidence:51 owned regression tests passed; typed policies/certificates, portable category replay, serialized-JSON HTTP example and direct-router replay validated. The final staged content was checked against its byte manifest, with no local-home path disclosure, credential match or invalid JSON found.350 previously completed artifact files remained byte-identical. Canonical local-only originals remain ignored and unchanged; only separately identified public audit views are distributed.

After cloning this branch, use existing approved Python dependencies and run:

```text
python -m scripts.verify_publication
python -m scripts.replay_remaining_policies --output <fresh-output>
python -m scripts.direct_router_example
```

These commands do not perform model inference. Models/index/service/environment and canonical private-path source audits are external; see the primary handoff and source notices. Actual-instance observation and verified relocation belong to integration owners. This is ready for scoped integration handover, not deployment activation.
