# Public version-control boundary

The repository is public. Stage only the exact root-relative paths in public-commit-files.json, after authorization. Do not use `git add .` or stage the entire documentation directory.

The local consolidated bundle contains about 46.5 MB of research documentation/evidence, including duplicated raw question/answer/reference/correctness payloads, provisional labels, source inventories, host paths and installation logs. It is a local review bundle, not an approved public dataset/report release. Full dataset licensing/custody/publication permission is not established by the software review. No individual file exceeds GitHub's hard file-size limit, but that does not make these contents appropriate to publish.

Excluded and preserved locally through this directory's .gitignore:

- archive/ with both original packages and original logs; no evidence is deleted.
- development-scope.json, development-verifier-inputs.source.json and history-source-roster.json with full source payloads/provisional labels.
- full resource-compatibility.json, provenance.json and calibration-evidence.json, which include recorded host/environment/path metadata.
- local file inventories, old readiness reports and raw validation/install logs/source snapshots.

Public replacements are source-resource-summary.json (counts, immutable hashes, unchanged cost/resource expectations and pending status) and evidence-index.json (original archive/member filenames and SHA-256 only). Hashes are integrity references, not compatibility or approval certificates. No private key/token/credential-URL patterns were found in the local scan; this is a bounded pattern scan, not a comprehensive secret audit. Raw/unapproved payloads remain excluded regardless.

The public synthetic smoke needs no private data. Source-specific tests honestly skip if the intentionally excluded Development metadata is absent; strict local revalidation uses RESEARCH_V1_REQUIRE_PRIVATE_INPUTS=1 and fails if required artifacts are missing. The 13 full handoff consistency checks require the local authorized evidence bundle and fail rather than certifying absent data. A public checkout must not claim those checks ran without their evidence. See Handoff A and final-review.md for exact tested profiles.

Scientific approval to collect or publish data is separate from approving this code/documentation commit. The Git workflow must verify staged paths against the allowlist before any future commit.
