# feat(game): research_v1 pre-collection durability and integration handoff

## Scope

- Game-owned durable starts/completions, atomic snapshots and conservative crash recovery.
- Verbatim nonblank offline question handling; stable IDs and exact tuple hashes.
- Duplicate/incomplete-report protections and recording/collector-boundary contracts.
- Opt-in research_v1 proposal, source/resource provenance summaries and [Tabmayee Handoff A](tabmayee-handoff.md).
- Exactly 37 allowlisted public files; raw datasets, provisional label payloads, archive originals, host logs and concrete local paths excluded.

## Validation

Fresh isolated macOS/APFS checks:

- 115 local validation cases/checks passed; zero failures/skips.
- 11 existing policy package/source compatibility regressions passed; zero failures/skips (126 local cases total).
- 18 public-only latest-main synthetic smoke/ownership cases passed; zero failures/skips.
- Public input profile without private metadata: 6 passed, 3 explicitly skipped; no real-input validation is claimed for that profile.
- 40 existing policy/configuration/solution/snapshot artifacts match main byte-for-byte and remain unchanged.
- Ownership, exact-public-allowlist, privacy/portability and diff checks passed.

The former import failure was missing psycopg2 in the isolated environment. Existing code requires that module but neither production requirements file declares a distribution. Installed psycopg2-binary 2.9.13 only in the test environment and documented the test-only setup; production dependency manifests/database code are unchanged. Database connections, sockets, model/verifier execution and fitting are blocked by the guarded runner.

Tested platform: local macOS/APFS, Python3.12, Intel. No live-verifier collection, deployment-platform or Windows certification, physical power-cut test or exactly-once external execution claim. No Final Test payload/evaluation was accessed.

## Compatibility

Existing framework policies, artifact bytes, probabilities, IDs, thresholds, budgets, reputation snapshots and compatibility fingerprints are preserved. No replacement fitted research_v1 policy is introduced. Baseline and existing game selection/aggregation/execution/provenance implementations are unchanged; recording remains opt-in. Only the game-owned offline question-content acceptance expands losslessly; existing valid inputs retain their identities. Application API, orchestrator, verifier implementations, database and production requirements are unchanged.

**Collection remains blocked. Fitting remains blocked. This PR does not authorize either, or merging into main.**

## Remaining dependencies

Scientific parameter/scope/reference/label approvals; research source and resource custody (including disputed historical timing inputs); authentic History reports; Tabmayee's actual collector integration validation; Raunak's verifier/resource checks; and deployment-platform validation. File recording has no PostgreSQL migration prerequisite. See final-review.md, source-resource-checklist.md and Tabmayee Handoff A.
