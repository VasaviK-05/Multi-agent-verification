# Verifier-cost branch merge with main

Merged main commit `cda61de0bdc01171cceaf3d8bc6dac6b62c61145` into feature
tip `268289fdb4a616142ec7d5c62e7bc7ad66af94bf` in a separate clean worktree.
No applicable AGENTS.md or prior merge/rebase was present. The original dirty
checkout was never switched, stashed, reset, cleaned or staged.

## Conflict resolutions and compatibility

- `app/game/offline/records.py`: preserve the resource-observed Attempt contract
  and the feature's ReservedExample, FinalTestReservation and TrainingManifest.
  Resolve the import conflict with `Field` present for digest/minimum-length
  validation, alongside StrictBool and the existing serializer/validators.
- `app/game/policy.py`: retain main's exact feasible-strategy and pooled-matrix
  checks. Preserve the feature's optional explicit solver tolerance, forwarding
  it only when supplied. Existing callers still invoke the original default
  `solve_minimax(matrix)` protocol; no solver default or research setting changed.
- Evaluation/readiness auto-merges were reviewed: training-only manifest binding,
  separate final release, resource checks and scientific/evidence gates remain.
  Offline build -> fit_policy -> build_policy tolerance signatures agree, and
  default pooling callers remain compatible. The shared benchmark timer and
  recording/custody export guards were not altered.
- Main's EvidenceRetriever now requires index manifest v2. Update the synthetic
  project-adapter fixture to read its declared MANIFEST_VERSION and add explicit
  rejection of legacy v1. Do not relax preflight or rewrite historical indexes.
  The fixture mismatch was reproduced before the fix.

Incoming API/database/service/orchestration/migration files are identical to main.
No additional integration or verifier algorithm change was introduced by resolution.
There was no unsupported scientific or behavioral choice to defer to the owner.

## Validation

The focused offline run selected these files under `tests/` with `python -m pytest ... -q`:
`test_cost_calibration`, `test_project_collection_adapter`, `test_game_collection`,
`test_diagnostic_collection`, `test_game_build`, `test_game_offline`,
`test_game_research`, `test_game_foundation`, `test_game_runtime`,
`test_game_completion`, `test_verifier_selector`, `test_offline_benchmark`,
`test_audit_repository`, `test_reputation_repository`.
HF_HUB_OFFLINE and TRANSFORMERS_OFFLINE were set. All fixtures for the cost workflow
are synthetic; this validation did not rerun empirical collection or fit a real policy.

Result: **530 passed, seven failed**. Two publication cases failed with sandbox
WinError5 on file rename; both passed when those exact tests were rerun outside
the sandbox (`test_game_build.py -k test_cli_end_to_end_never_opens_final_outcomes`).
Thus **532 distinct selected checks passed**; five failures are independently
reproduced with unchanged origin/main sources:

- Research CLI `test_cli_unresolved_template_is_read_only_and_reports_digests`
  hard-codes revision `9d21eba...` instead of accepting the actual checkout revision.
- Runtime `test_detached_audit_and_existing_external_feedback_identity_binding`
  and benchmark `test_benchmark_feedback_propagates_source_without_replacing_learning`,
  `test_unknown_requirements_exhaust_candidates_in_benchmark`, and
  `test_all_verifiers_skip_abstentions_and_learn_after_the_prediction` reach main's
  new persisted feedback path. Outside-sandbox baseline reruns all fail because
  no local PostgreSQL server is available. No database writes succeeded.

Additional inherited API tests (`test_ground_truth_persistence`, `test_audit_api`)
cannot collect because main initializes database-backed state at import. This
also reproduces on unchanged origin/main outside the sandbox, with connection
refused. Repository unit tests themselves passed: 19 on the baseline, also covered
in the focused merged run. Their counts overlap and are not added.

The three controlled public evidence probes still fail, with the neutral control
passing, identically on main and merged sources. For this comparison only, an
in-process stub returned None from the new database bootstrap loader so existing
unit fixtures could supply empty reputation state. No judgment assertion or
production source was changed. The initial broader run that included live-model
evidence tests was stopped; it is not reported as a completed suite.

No failures were hidden by changing scientific gates, judgment expectations,
database behavior or production startup. No unresolved merge entries/conflict
markers remain, and staged/working-tree whitespace checks pass.

## Preserved empirical data and workspace

The historical calibration still reloads under merged schemas and agrees with
all 344 measurements and frozen-file hashes:
`1a2abc5663193e025f9c7e62805dbad5e9d6b720a1a6895b7f40e91f779ab992`.
Its arithmetic-heavy sample/old setup scope is unchanged. Main's source/manifest
changes do not authorize rebinding it to a new setup, recollection or index upgrade.

Before/after preservation checks compare the original HEAD, index, binary diffs,
36 dirty/untracked files and 47 empirical/proposal files. Their bytes remain
unchanged, including the original calibration/measurements/freeze receipt. No
empirical build output is staged or pushed. The separate merge worktree is retained
for review; the dirty checkout deliberately stays at its original HEAD/index even
when the remote feature branch advances. No PR or push to main is part of this work.
