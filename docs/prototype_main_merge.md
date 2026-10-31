# Prototype feature / main merge verification

Incoming main: `54cd119d5c60557ecbba52879c5023858db87996`.
Feature before merge: `7a272b9cba20e7f6b9d567b49e989ae0579241c0`.
Operation: merge origin/main into `codex/offline-policy-recording-pilots` only.
No main update, rebase, force push or activation is part of this operation.

## Reviewed conflicts

- `docs/game_policy_build.md`: preserve the feature's current approved restricted
  prototype status and historical upstream merge findings. Incoming statements that
  no factual policy exists describe the earlier state, not the completed study;
  the retained historical sections identify their original scope.
- `scripts/run_factual_diagnostic.py`: preserve configurable local-only network
  ceilings with validated nonnegative integer limits and the original default
  generation30/metadata100 behavior. Incoming code has no additional behavior lost
  by this backward-compatible resolution.

All six incoming persistence files (repository, migration, migration/reconciliation
utilities, persistence smoke script and tests) are retained byte-for-byte as Git
blobs from incoming main. They are not wired into the policy runtime. No database
operation or migration was executed; repository tests use fake connections.
Verifier/retrieval/generation, DB/API/frontend and unrelated orchestration code
have no feature-specific modifications relative to incoming main.

## Restored teammate artifacts

The earlier feature cleanup deletions were already present on main via squash
PR25. To undo only that cleanup as explicitly requested, restore these seven last
tracked upstream blobs from `e9b0a10`, without modifying their contents:

```text
corpus_evidence_test_results.json
data/articles_13083_index/chunks.json
data/articles_13083_index/faiss.index
data/articles_13083_index/manifest.json
data/verification_traces/C01.json
data/verification_traces/C03.json
data/verification_traces/C14.json
```

Every pre-existing local copy was first preserved byte-for-byte under
`build/prototype-main-merge-review/preserved-local/`, with SHA-256 proof. The restored
index entries equal the original upstream blob IDs exactly. The payloads were
handled as opaque bytes, not loaded as study inputs or final-test evidence. No
teammate corpus/index/trace deletion remains in the feature diff against main.
Existing ignore patterns do not remove these restored tracked files.

## Combined validation

Executed on the combined working tree:

```powershell
.venv/Scripts/python.exe -m pytest tests/test_game_prototype_bundle.py tests/test_game_task_conditioning.py tests/test_game_runtime.py tests/test_game_three_outcomes.py tests/test_game_reliability_first.py tests/test_game_clean_coverage.py tests/test_game_collection.py tests/test_game_offline.py tests/test_game_evidence_validation.py tests/test_real_evidence_diagnostic.py tests/test_verifier_cost_repository.py -q
```

Result: **262 passed**. No test assertions were changed and no test failures remain.
The staged whitespace check reports one **reproduced upstream** formatting warning:
`tests/test_verifier_cost_repository.py:376: new blank line at EOF`. The identical
warning occurs in `git diff 54cd119^ 54cd119 --check`; the incoming test blob is
unchanged rather than cleaned up by this merge. Conflict-marker scans and the
resolution/owned-file whitespace checks are clean.

The supplied bundle remains
`98b8f2654163fe95e84a1b916a94174ddc37aa399429bba94f99890573168d34`.
Both policy bytes, artifact IDs and all probabilities are unchanged. The merged
loader verifies certificates, file hashes, exact compatibility and40-question scopes,
and loads the documented extracted-ZIP layout. Original arithmetic/capital/
reliability-first artifacts reload; seven historical preservation hashes still match.

The existing retained-report validator was rerun with only its output directory
redirected to `build/prototype-main-merge-review/retained-runtime-merged/`:11 actual
analyzer/task-router/provider/finalizer traces demonstrate acceptance, rejection and
uncertainty, and14 reference/resource/budget/scope/unsupported-task checks fail safely.
This uses recorded-resource observer simulation, not new inference or live resources.

A separate read-only `inspect_setup` check hashes actual local model/corpus/index/
implementation bytes and saved service metadata without constructing models or
making network requests. Its resource manifest still equals both artifact contracts:
`e23c6f034a4c660d30433d133be3a197db620abbdf22a78907ef5e3687d45ccb`.
The new independent persistence module changes the whole-application source digest;
that historical packaging metadata was not rewritten. It does not change the bound
verifier-resource manifest or execution semantics. No old measurement is presented
as evidence of changed resources. Live service availability still requires the
existing live observer before execution; this task makes no live-availability claim.

The untracked `docs/game_empirical_build_audit.md`, supplied ZIP, private study data,
generated resources and historical artifacts remain preserved. No final-test payload,
fresh inference/collection/calibration/fitting, production write, activation or new
integration was performed. The original reference-required, prepared-question-only
arithmetic50% and experimental factual25% scope and all uncertainty/attack limitations
in [the prototype handoff](multitask_prototype_bundle.md) remain unchanged.
