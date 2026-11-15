# Approved eligibility compatibility review

## Verdict

Prepared on feature branch `codex/research-v1-eligibility-approved-v1`, based exactly on latest remotely rechecked main `9c38f4de402d510bb13111da592a4f29abe03a24` (merged PR #35). No upstream delta, commit, staging, push, PR, merge or teammate message was performed. The shared original checkout and its unrelated work were not modified.

Game-side compatibility and non-verifier handoff are ready for review. Collection and fitting are not ready or authorized. Read [updated Handoff A](tabmayee-handoff.md), [current blockers](blocker-register.csv) and [superseded assumptions](superseded-assumptions.md).

## Verified facts

The exact user-pinned manifest body SHA matches. Complete-file sidecar and all five supporting output hashes match; see verification-receipt.json for full hashes and hash definitions. Approved eligibility is 744 unique candidates /372 paired groups, GSM8K 187 and HotpotQA 185 groups. All 15 shared-context HotpotQA groups are excluded. Exclusions are 375 rows, including 13 group summaries rather than candidate rows.

The eligibility ZIP alone is insufficient for dispatch. The separately supplied original source package matches the manifest's source hash; all 744 approved original candidate/verifier-input tuples join without mismatch, no payload is missing from that supplement, and only the quarantined 30 original candidates are removed. Sixteen retained questions have outer whitespace; no tuple normalization was performed. Public scope metadata contains stable IDs and hashes, not raw question/answer/context or per-candidate correctness labels.

All labels retain provisional_automated_labeling_v1 and human_verified=false. Approval does not attest independent correctness. Semantic clearance remains NOT_CLAIMED; threshold findings and manual reviews do not prove absence of semantic leakage. Eligibility approval is resolved and must not be requested again.

Four existing adapter schemas and prerequisites remain compatible; no verifier was instantiated or executed. Counts are 2976 slots and, conditionally, 2602 dispatches plus374 Semantic exclusions. The concrete label/reference/request profile is still unresolved, so schema compatibility is not a runnable study or a live-resource certificate.

The generator path is absent at its declared d9fd453 commit (commit exists; named file does not). Generator bytes/actual revision/dirty inventory/run/transfer custody remain missing. This does not undo the user's designated eligibility approval; it prevents claiming complete producer provenance. Source and runtime/resource custody must be resolved separately.

Historical root JSON proposal/source summary/validator bytes are unchanged. Historical Markdown bodies are retained beneath version pointers, with original Git/hash identities pinned. Package A is unrelated untracked work outside this checkout and was read-only audited, not copied or edited. See superseded-assumptions.md for both inventories.

## Fresh guarded validation

Environment: isolated Python 3.12.0, macOS 26.5.2 x86_64, APFS. Package versions are the compatible isolated environment documented in ../environment.md (httpx0.28.1, pytest9.2.0, pydantic2.14.3, numpy1.26.4, torch2.2.2, transformers4.48.3, sentence-transformers3.4.1, faiss-cpu1.16.0; psycopg2-binary2.9.13 installed environment-only). No dependency manifest or database code changed.

Use `"$TEST_PYTHON" docs/research_v1-recording-handoff/validation/run_checks.py MODE` from repository root; Handoff A specifies evidence environment variables. The runner blocks live verifier/model construction/execution, network/DNS, database connections, fitting and prohibited payload access.

| Mode | Passed | Failed | Skipped | Deselected |
|---|---:|---:|---:|---:|
| eligibility (final expanded suite, supplied archives mandatory) |32|0|0|0|
| filesystem |27|0|0|0|
| planning |11|0|0|88|
| boundaries (includes ownership) |18|0|0|0|
| existing-boundaries |20|0|0|3|
| regression (policy package + source compatibility) |11|0|0|0|
| input (public checkout, historical private metadata absent) |6|0|3|0|
| **Total** |**125**|**0**|**3**|**91**|

SCHEMA_IMPORT_PASS also observed. The three optional input skips concern absent historical private metadata; the new archive-backed eligibility/source/verbatim checks ran without skips. The old 13 source-package handoff checks were not rerun or counted as new-roster validation. Earlier 25-case eligibility iteration is superseded by the final32 and not double-counted. The initial test mistakenly compared an empty findings list with integer0; corrected the test to match the authenticated schema, with no artifact or application change.

All 40 existing fitted policy/configuration/context/contract/solution/reputation/snapshot artifacts have identical SHA-256 bytes versus main. All existing tracked app and test files are unchanged; only the new opt-in helper/test are added there. Therefore existing policy probabilities, IDs, budgets, thresholds, snapshots, compatibility fingerprints, selection/aggregation/resource/production execution code are unchanged. The 11 regression cases passed. No replacement fitted policy or production integration is introduced.

Ownership check returns unexpected=[], diff whitespace check passes, and changed-file host-path/credential scan reports no findings. No teammate file, raw dataset, archive, verifier resource, API route, database or existing policy artifact is part of the patch. Original external archives remain unmodified. Local logs remain external to the public package.

## Limits and owners

This is synthetic non-verifier engineering validation plus read-only artifact identity checking, not end-to-end service validation or intended-platform/Windows certification. A full runnable request, independent-label representation, approved reference serialization, semantic disposition, actual resources and factory/observer integration remain unverified.

- Vasavi: label estimand/mapping, reference/analyzer/requirements and semantic-risk disposition; operational protocol and explicit recording authorization. Planning minima/coverage/thresholds/losses/budgets/dependencies/attack/version approvals are additionally needed before fitting, not prerequisites to raw capture by themselves.
- Tabmayee: immutable request/reservation, prerequisite-aware factory/observer, typed timeout/error boundary, durable start/completion acknowledgments and conservative resume, deployment-platform validation.
- Raunak/source producers: actual source generator/run/transfer custody, verifier/resource suitability and exact config/model/prompt/service/corpus/index/receipt observations.
- History custodian + Vasavi: authentic report-bearing History/reputation inputs, split/exposure reservation/disposition without Final Test disclosure.
- Samika: no database work requested in this file-only preparation.

No live verifier, service, database, migration, report collection, policy fitting or Final Test payload evaluation/access was performed. Collection and fitting remain blocked.

## Exact changed-file list

- `app/game/offline/eligibility.py`
- `docs/research_v1-recording-handoff/README.md`
- `docs/research_v1-recording-handoff/decisions-required.md`
- `docs/research_v1-recording-handoff/eligibility-approved-v1/blocker-register.csv`
- `docs/research_v1-recording-handoff/eligibility-approved-v1/historical-identities.json`
- `docs/research_v1-recording-handoff/eligibility-approved-v1/recording-config.proposed.json`
- `docs/research_v1-recording-handoff/eligibility-approved-v1/remaining-decisions.md`
- `docs/research_v1-recording-handoff/eligibility-approved-v1/review.md`
- `docs/research_v1-recording-handoff/eligibility-approved-v1/scope.ids.json`
- `docs/research_v1-recording-handoff/eligibility-approved-v1/superseded-assumptions.md`
- `docs/research_v1-recording-handoff/eligibility-approved-v1/tabmayee-handoff.md`
- `docs/research_v1-recording-handoff/eligibility-approved-v1/verification-receipt.json`
- `docs/research_v1-recording-handoff/final-review.md`
- `docs/research_v1-recording-handoff/owned-files.json`
- `docs/research_v1-recording-handoff/recording-contract.md`
- `docs/research_v1-recording-handoff/tabmayee-handoff.md`
- `docs/research_v1-recording-handoff/validation/run_checks.py`
- `tests/test_research_v1_eligibility.py`

Total: 18 files (7 existing game-side documents/validation files changed; 11 new game-side source/test/metadata/document files). No files are staged.
