# Offline policy workflow: publication handoff

The offline builder, report collector and millisecond cost calibration are implemented.
They retain outcome-free final reservation contracts, independent history reputation,
complete development attack replay, both aggregation methods/all feasible strategies,
solver certificates, export/reload/provider checks and reproducibility diagnostics.
DB/API/persistence integration is outside this work.

The arithmetic pilot was fitted and diagnosed. Rule's frozen reputation 41/42 gives
positive log-odds weight; Semantic's 0.5 gives zero weight. The minimum-two contributor
guard causes 100% development uncertainty under the approved contract. This was
explained, not repaired by weakening protections. Its only team has two aggregation
choices, so it cannot demonstrate team selection or cost optimization. Semantic
supported incorrect candidates as well as correct ones. Results are restricted to
constructed, reference-assisted arithmetic; all original empirical artifacts remain local.
See [the fit](arithmetic_pilot42_fit.md) and [diagnosis](arithmetic_pilot42_abstention.md).

The [factual proposal](studies/factual-team-selection-v1/README.md) is prepared with
seven structurally feasible teams and fourteen aggregation strategies. No factual
policy exists. Evidence/retrieval repair, explicit study/label/custody/settings
choices and fresh compatible recordings/cost measurements remain outstanding.
A push is source publication only: it approves no factual settings or inference run.
The evidence readiness gate and all contributor/coverage/failure protections remain.

## Shareable code versus local outputs

This branch includes source, public-example/synthetic tests, Markdown results/handoffs
and configuration templates. Generated recordings, labels, final reservations/payloads,
approval receipts, preflight snapshots, local model paths, model/index files and build
artifacts are excluded. The pre-existing tracked cost artifact inventory is metadata
only (relative filenames, digests and aggregate costs), not the empirical bundle.
Local JSON snapshots under the two study directories are ignored and preserved.
The old machine-specific empirical-build audit stays uncommitted.

Tests no longer require those ignored study snapshots. Their six public preparation
texts are in tests/factual_fixtures.py, with entirely synthetic reserved-position rows;
no actual final payload is loaded to test preparation. The earlier mixed-source test
read and its correction remain explicitly documented in the factual handoff.

Reusable CLIs require explicit input files and new permission/custody/freeze references.
They cannot manufacture current authorization from the historical pilot chat. The
bounded diagnostic guard rejects non-loopback/credentialed URLs and HTTP redirects.
Preparation/adapter source changes produce new resource/code identities: do not rewrite
historical artifacts or replay old approvals to fit new code.

## Validation

The publication check uses the offline builder/collector/calibration, proposal,
reputation/normalization, solver, provider/runtime and affected game suites. Exact
results are recorded below. Tests use local controlled fixtures, not real inference.
The separate controlled evidence probe reproduces the same three baseline failures:
directional support/rejection becomes uncertain, and a conflict becomes
no_relevant_evidence. One neutral case passes. These are outstanding owner blockers,
not new failures; no verifier/retrieval implementation or readiness gate was changed.

The repository-wide suite and real provider/DB/API execution are outside this check.
Publishing code supplies no robustness, statistical power or efficiency evidence.

## Publication checks (2026-10-28)

- Exported the staged tracked tree with git checkout-index; neither ignored factual
  study request existed there. The full affected command below passed **799 tests
  in 275.16 seconds** from that export.
- Afterwards corrected only the arithmetic preparation exclusion-reason metadata
  (the arithmetic roster does not imply a missing index), and parameterized its
  preflight-ready/unready fixture. **All 6 arithmetic tests passed in 26.26 seconds**.
- Reproduced the stale hard-coded Git revision assertion from an isolated export of
  committed HEAD, then corrected the test to compare against actual Git HEAD.
  The corrected assertion is included in the successful 799-test run.
- Separate evidence probe: **3 reproduced baseline failures, 1 pass, 88 deselected**.
  No readiness gate or verifier/retrieval algorithm was changed to hide them.
- git diff --check and staged whitespace checks pass. A review of 71 changed source,
  documentation and template files found no common credential tokens, user-home
  paths, binaries or files larger than 250 KB. Generated/private snapshots are not
  staged. Original arithmetic proposal/approval/recordings/calibration/artifact
  hashes remain unchanged.

```powershell
.venv/Scripts/python.exe -m pytest tests/test_game_build.py tests/test_game_collection.py tests/test_cost_calibration.py tests/test_project_collection_adapter.py tests/test_diagnostic_collection.py tests/test_arithmetic_pilot.py tests/test_factual_study_draft.py tests/test_factual_team_pilot.py tests/test_pilot_abstention_contract.py tests/test_pilot_preparation_cli.py tests/test_game_foundation.py tests/test_game_offline.py tests/test_game_runtime.py tests/test_game_research.py tests/test_game_completion.py tests/test_dependency_aggregation.py tests/test_decision_engine.py tests/test_early_termination.py tests/test_vote_normalization.py tests/test_verifier_selector.py -q
.venv/Scripts/python.exe -m pytest tests/test_arithmetic_pilot.py -q
.venv/Scripts/python.exe -m pytest tests/test_adaptive_pipeline.py -q -k 'test_actual_evidence_output_contract_is_consumed_without_models or test_actual_conflicting_evidence_cannot_cover_factual_request'
```

The Windows synthetic publication tests ran outside the filesystem sandbox; this
is an environment requirement, not approval for a scientific inference run. The
last command deliberately remains failing until its owners repair the contracts.
