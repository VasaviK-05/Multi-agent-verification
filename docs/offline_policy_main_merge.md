# Offline policy branch: main merge verification, 2026-10-29

Merged incoming origin/main `e9b0a10d31f63de908f9f306ae0dd4b37844194e` into
`codex/offline-policy-recording-pilots` at feature tip
`de49b73bda68608da6b27319fdfdbd940323b48b`. The operation was explicitly authorized;
main is not the destination. No reset, clean, stash, force-push or study execution
was used. No applicable AGENTS.md was found.

## Five conflict resolutions

- `app/game/offline/recording_adapters.py`: retain the common project/rule factories
  and our additional arithmetic observer/factory. The two versions differ only by
  that addition; narrow observed resources, local-only model loading and actual
  pre/post fingerprints remain intact.
- `app/game/offline/records.py`: the conflict is import order only. Keep Field,
  StrictBool and serialization/validation helpers. Both sides' outcome-free
  ReservedExample/FinalTestReservation/TrainingManifest implementations are
  identical. No final labels, reports or outcome paths enter fitting.
- `docs/game_policy_build.md`: retain the shared builder/collector/calibration
  workflow and later arithmetic/factual handoff, rather than restoring the older
  statement that no empirical arithmetic policy was fitted. Historical results and
  current integration status are distinguished.
- `tests/test_diagnostic_collection.py`: keep shared diagnostic export/custody
  protections plus our loopback, bounded-request and redirect-denial tests.
- `tests/test_project_collection_adapter.py`: retain incoming use of the actual
  EvidenceRetriever.MANIFEST_VERSION and its explicit rejection of legacy v1.
  Do not relax resource preflight or silently upgrade an existing index receipt.

All existing strategy/solver/artifact, pooling, metadata reservation, calibration,
recording, resource, coverage, contributor, prerequisite and failure contracts remain.
Incoming production DB/API, migration, service, orchestration, claim/retrieval and
verifier files are byte-identical to origin/main: no additional production behavior
or algorithm changes were introduced while resolving conflicts.

## Test boundary integration

Main added snapshot bootstrap/persistence and audit writes. Existing offline tests
mocked only the earlier aggregate-row operations, causing PostgreSQL connection
refusals before reaching the evidence probes. Extend only test boundaries for the
new snapshot/audit calls. API tests bootstrap an empty in-memory snapshot during
module import and immediately restore the real loader. Repository SQL tests still
use their own fake connections and assert SQL/commit/rollback behavior.

The incoming snapshot-save failure test now injects controlled verifier handles,
while retaining its real manager, failure injection and exact rollback assertion;
it does not initialize default model/provider adapters. No assertion was removed
or weakened. Audit mocks accept the incoming positional validation ID signature.
Initial fixture-only integration errors were corrected and rerun, not classified
as successful checks or scientific results.

## Verified evidence status and remaining blockers

The three historical failing public evidence cases are repaired in controlled
checks: **all four original probe cases pass**, including the neutral control.
The selected tokenizer, topic gate, contradiction/conflict, claim coverage, output
contract, generation parsing and diagnostic checks pass (**46 model-free checks**).
Do not infer empirical accuracy, robustness or efficiency from these results.

The conservative evidence readiness gate is intentionally unchanged. Passing
controlled probes does not authorize a factual study or retrospectively rebind
reports/calibration to changed source. The seven structurally feasible factual
teams and both aggregations remain the proposed design; no factual policy exists.
Study/label/custody/settings decisions, fresh resource observations, approved
recordings and costs remain outstanding. Incoming retrieval requires manifest v2;
historical v1 index/receipt bindings cannot simply be relabelled or reused.

One incoming test,
`test_low_semantic_keyword_collision_is_ineligible_before_nli`, fails because
`data/articles_13083.json` is absent. The exact FileNotFoundError reproduces on an
unchanged origin/main export. The corpus producer/evidence-test owner must supply
that resource or separately redesign a self-contained fixture. The assertion was
not removed, skipped or weakened. Model-backed/full-corpus tests were not completed;
the selected model-free checks are not a substitute for that validation.

## Validation

- **928 passed**, one upstream Starlette/httpx deprecation warning, in the combined
  offline policy, collector, calibration, provenance, solver/provider/runtime,
  benchmark, adaptive pipeline, mocked API, audit and reputation repository suites.
- **72 passed** in the additional reputation manager/import/retry/provenance suite.
- **46 passed** in the selected model-free evidence/retrieval/generation/diagnostic
  suite. Four original public evidence probes also passed separately; counts overlap.
- The original arithmetic PolicyArtifact reloads and validates its numerical
  certificate and compatibility ID. Its original artifact ID remains
  `6b52c2cc954d461a9a1d34d4ffcf23b048a77f494104fbca7a7f038271167a94`.
  A custody-open guard stayed active during reload; no fit or final evaluation ran.
- Whitespace checks and tracked-source conflict-marker checks pass. Unit tests use
  controlled verifier/storage boundaries, not a live DB deployment. No schema
  migration was applied and no production write succeeded or was required.

The combined suite selected the previous publication's twenty offline/game/decision
files plus `test_offline_benchmark`, `test_adaptive_pipeline`, `test_audit_repository`,
`test_reputation_repository`, `test_audit_api` and `test_ground_truth_persistence`.
Additional reputation files were `test_reputation_integration_upgrade`,
`test_reputation_manager` and `test_reputation_imports`. Windows TestClient and
synthetic atomic-publication tests ran outside the filesystem sandbox. The initial
sandbox TestClient invocation was stopped rather than counted as a pass.

## Local data preservation and exclusions

The original untracked `docs/game_empirical_build_audit.md` digest and inventoried
private pilot/study files remain unchanged. Historical arithmetic approvals,
recordings, calibration, fitted artifacts and final payloads were not rewritten.
Only tracked handoff Markdown was updated to distinguish historical blockers from
current controlled-check results. Final-test payload contents were not opened.

Exception: an initial broad evidence invocation reached a model-backed fixture and
rebuilt the generic ignored `data/evidence_index/test_evidence_corpus` cache before
it was stopped. I should have excluded that fixture at the outset. Its rebuilt
bytes remain local; exact preservation of that cache cannot be claimed. The
separate witnessed pilot index and inventoried study artifacts are unchanged. No
rebuild is presented as approved calibration, empirical recording or fresh study
resource provenance. Further checks were explicitly selected to be model-free.

Seven generated files already committed upstream (the corpus result JSON, three
articles_13083_index files and three verification trace JSON files) are excluded
from this merge's resulting tree and retained locally with ignore rules. Runtime
code has no read dependency on these artifacts. They still exist in upstream Git
history; no history rewrite was attempted. No local/private recording, final
payload, model weights or build artifact was staged. This merge and push approve
no factual settings, inference campaign or final evaluation.
