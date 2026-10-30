# Arithmetic pilot42: investigation of development abstention

## Finding and disposition

No implementation defect was verified. This is intended behavior under the explicitly versioned contributor contract, combined with a limited pilot and the approved minimax objective. No decision semantics, thresholds, loss weights, capability declarations, prior, calibration, recordings, approval or policy were changed. There is no corrected/rebuilt policy: the original remains compatible with the unchanged semantics.

The branch inspected was `codex/game-pooling-resource-provenance`. No applicable AGENTS.md was found in the workspace/ancestors or relevant source/test/docs directories. Existing working-tree changes, including concurrent factual-study work, were preserved. This investigation adds this document, synthetic contract tests and ignored diagnostic files under `build/arithmetic-pilot42/investigation/`.

## Exact inputs and reproduction

Approval binds configuration digest `af723595edffe54fbd8cd6f1d3c082bd718c53edfddd2d063bdda8aa6094ad41`. The runner asserts the approved configuration equals the original proposal's nested configuration, loads its manifest, planning context and execution contract, and reloads `fitted-policy/policy.json` through `PolicyArtifact` (including certificate validation). `construct_payoffs` replays all 40 development candidates for both strategies and all five attack scenarios. Its matrix equals the artifact matrix exactly. Direct public `finalize_decision` explanations equal clean public replay explanations for all 80 example/strategy pairs.

Files:

- `build/arithmetic-pilot42/investigation/diagnose.py`: guarded, repeatable development replay and direct finalization, no optimizer.
- `build/arithmetic-pilot42/investigation/traces.json`: all 80 clean traces, original raw reports, normalized votes, weights, contributions, preliminary/public decisions, reason codes, per-scenario metrics, exact planning context, execution contract and original input/output SHA256 hashes.
- `build/arithmetic-pilot42/investigation/fidelity.py` and `fidelity.json`: raw collection payload / retained Attempt / exported training report identity checks and retained prerequisite/capability metadata.
- `build/arithmetic-pilot42/investigation/runtime-correct.py`, `runtime-incorrect.py` and corresponding JSON: in-memory provider/runtime parity using retained reports and original pre/post resource observations, without verifier inference or live resource claims.

The audit hook rejects every open beneath `custody/` and every network connection. Production DB/API/orchestration imports are blocked; optimization, calibration and final evaluators are patched to fail. No final-test payload is loaded. Original file hashes are checked unchanged. Resource, strategy feasibility and execution provenance checks run through existing replay rather than being bypassed.

## Trace: correct answer

`arith-add-01-correct`: question `What is 17 + 4?`, answer `21`, reference `Exact arithmetic reference: 17 + 4 = 21.`

Rule returns SUPPORT, passed=true, raw score=1, factual `arithmetic_addition`. Its outcome-bit score is not a probability; the named deterministic rule normalizes to confidence=1 and signed mass=+1. Semantic returns SUPPORT, passed=true, cosine score/confidence/mass=0.7885075808142631. Neither report is an abstention or structural-only check.

Frozen history in routed domain `general`: Rule has 40 successes/0 failures, Beta(41,1), posterior mean 41/42; Semantic has 20 successes/20 failures, Beta(21,21), posterior mean 1/2. Their exact log-odds weights are 3.7135720667043066 and 0. The snapshot uses unrounded posterior means, not the rounded selector display value.

Reputation numerator = 3.7135720667043066 * 1 + 0 * 0.7885075808142631 = 3.7135720667043066. Denominator = |3.7135720667043066| + |0| = 3.7135720667043066. Raw score=+1, preliminary passed because +1 > 0.55. The nonzero denominator means equal-weight fallback does not apply. Semantic is excluded with `zero_log_odds_weight`; contributor count=1, required minimum=2. Final public status is uncertain with exactly `minimum_contributors`.

## Trace: incorrect answer

`arith-add-01-incorrect`: same question/reference, answer `22`.

Rule returns REJECT, passed=false, raw outcome-bit score=0. It correctly normalizes to confidence=1 and mass=-1, **not zero confidence**. Semantic returns SUPPORT, passed=true, score/confidence/mass=0.7537461751780665. Frozen history, domain and effective weights are unchanged.

Reputation numerator=-3.7135720667043066, denominator=3.7135720667043066, score=-1. Preliminary failed because -1 < -0.55. Again only Rule counts, so final public status is uncertain with `minimum_contributors`. There is no score-normalization defect and Semantic's incorrect support is not itself the direct finalization cause; its history-derived zero weight triggers the legitimate two-contributor guard.

## Coverage, prerequisites and execution across all examples

All 40 clean candidates route to the captured `general` snapshot; analyzer domain status is unknown and its recorded routed domain is general, not a mismatched domain lookup. The easy plan requires two participants. Required capability is arithmetic; expected covered is arithmetic and expected uncovered is empty. Candidate descriptors advertise arithmetic (Rule) and semantic_comparison (Semantic); the latter is not a required capability. Actual factual achieved coverage is arithmetic for correct **and rejected** arithmetic checks. Semantic similarity establishes no factual capability. All clean unresolved sets are empty.

Semantic requires reference text; every development reference is present and matches the captured reference-available state. Both descriptors have configured readiness/prerequisite status `unknown`, meaning no positive readiness claim; this is eligible under the existing contract, not `missing_reference` or `unavailable`. Retained execution and pre/post resource observations establish both actually returned directional reports. There are no missing recordings, excluded reports from failed prerequisites, unavailable/failed executions, missing achieved coverage, unresolved requirements, or boundary decisions in clean data. Budget and resource compatibility checks pass. Strict decision boundaries are >+0.55 and <-0.55; equality is uncertain. Here all numerical scores are ±1, so boundary handling is irrelevant to the observed abstention.

Clean cause counts for reputation: `minimum_contributors` 40/40; every other finalization reason 0/40. Dependency grouping has no clean finalization reasons and makes 20 correct accepts and 20 correct rejects.

The raw collection payloads preserve direction, score semantics, rule_kind/rule and Semantic reference/model metadata; training export preserves the reports. Runtime and offline use the same public finalizer. The retained-data runtime check is a compatibility test, not a new invocation of the verifiers.

## Why dependency grouping differs

The contract `baseline_log_odds_active_group_v1` intentionally uses different contributor definitions. Reputation counts nonzero effective log-odds contributors (or directional votes in the all-zero equal-weight fallback). Dependency grouping counts active nonstructural reports, including zero-reliability members. This distinction is documented in `docs/game_offline_evaluation.md` and covered by the existing zero-reliability group test; it is not an offline adapter mapping error.

Both pilot verifiers belong to one conservative unknown dependency group. Group reliability strengths are max(0,2p-1): Rule=20/21=0.9523809523809523, Semantic=0. Group numerator is ±20/21 + 0*SemanticMass, denominator=20/21, giving group score ±1. Group influence=20/21. Outer numerator=±20/21, denominator=20/21, final score=±1. Both reports are active, so contributor count=2 and the public decisions are decisive. Semantic adds no mathematical influence but does count under this existing grouping contract. Changing that definition would be a separately versioned scientific/runtime contract change, not a justified bug fix for reputation's guard.

Relevant code: `app/decision/vote_normalization.py:161`, `app/decision/decision_engine.py:97`, `app/decision/decision_engine.py:410`, `app/decision/early_termination.py:129`, `app/decision/early_termination.py:165`, `app/decision/dependency_aggregation.py:95`, `app/game/finalization.py:51`, `app/decision/coverage.py:12`, `app/game/offline/replay.py:44`.

## Before / after development results (unchanged)

These are development results, not final-test evidence. Per scenario the following triples are validation loss / decision coverage / cost-inclusive objective:

- Fitted reputation policy, probability 1: clean **0.2 / 0% / 0.3**; forced support **0.2 / 0% / 0.3**; forced rejection **0.2 / 0% / 0.3**; confidence inflation **0.2 / 0% / 0.3**; suppression **0.2 / 0% / 0.3**. Uncertainty is 100% in every scenario. All five tie as worst case.
- Dependency grouping, probability 0: clean **0 / 100% / 0.1**; forced support **0.5 / 100% / 0.6**; forced rejection **0.5 / 100% / 0.6**; confidence inflation **0 / 100% / 0.1**; suppression **0.2 / 0% / 0.3**. Uncertainty is respectively 0%, 0%, 0%, 0%, 100%. Its worst scenarios are forced support and forced rejection.

Both strategies' expected estimated attempt cost is 12.94808874517912 ms per candidate. The approved resource weight contributes 0.1 to every objective. Validation loss remains separate from this charge. The matrix rows are **not equivalent**: maximum difference is 0.3; only suppression ties. Given false accept/reject loss=1 and uncertainty loss=0.2, minimax legitimately prefers robust uncertainty (0.3) over grouping's worst-case 0.6. This is not evidence of superior clean accuracy.

## Action and ownership

No core code fix, semantic version bump, incompatibility marker or rebuild is warranted by this diagnosis. The original artifact/approval/calibration/recordings are preserved. The existing recordings remain valid for their original contracts. New tests lock the observed contributor distinction, informative decisive cases and coverage/execution/abstention protections without relaxing guards.

A future study should supply a genuinely informative second verifier on independently labelled history and development, with truthful capability/prerequisite/resource contracts; that requires an approved roster/design, new recordings and calibration where resources change. Alternatively, studying a legitimate single-contributor regime or a different grouped contributor rule requires explicit scientific approval and consistent versioned/runtime changes; do not relabel easy examples hard, duplicate verifiers, inflate priors, lower thresholds/minimums, or alter loss weights to manufacture decisions. Selecting the existing grouping baseline alone improves clean coverage but exposes the measured 0.5 worst-case validation loss; it is not a correction of the approved minimax fit.

The minimum-two constraint and two-candidate roster allow exactly one team with two aggregation choices. This pilot cannot demonstrate adaptive team selection or cost optimization. Semantic supported every recorded candidate, including incorrect answers. Conclusions apply only to this constructed, reference-assisted arithmetic pilot. No general empirical efficacy or final-test result is established.

## Commands and validation

From repository root:

```powershell
.venv/Scripts/python.exe build/arithmetic-pilot42/investigation/diagnose.py
.venv/Scripts/python.exe build/arithmetic-pilot42/investigation/fidelity.py
.venv/Scripts/python.exe build/arithmetic-pilot42/investigation/runtime-correct.py
.venv/Scripts/python.exe build/arithmetic-pilot42/investigation/runtime-incorrect.py
.venv/Scripts/python.exe -m pytest tests/test_pilot_abstention_contract.py -q
.venv/Scripts/python.exe -m pytest tests/test_pilot_abstention_contract.py tests/test_game_offline.py tests/test_game_runtime.py tests/test_dependency_aggregation.py tests/test_decision_engine.py tests/test_early_termination.py tests/test_vote_normalization.py tests/test_verifier_selector.py -q
```

The runtime scripts create their JSON report exclusively; use a new report path if rerunning after the first execution. The diagnostic/fidelity scripts replace only their own new investigation reports. Results: the new synthetic contract suite passed 12/12. The full affected suite passed 476/476 in 94.56 seconds, including existing missing-reference prerequisite, runtime drift/compatibility, coverage, normalization and early-termination checks. No new or baseline test failures occurred in these runs. Both historical runtime checks passed, all 160 raw/attempt/export report comparisons passed, and all original input/artifact hashes remained unchanged.

## Shared-code availability

Referenced `build/` recordings, fitted artifacts, approval receipts and diagnostic
traces are local-only and are not distributed by this Git branch. This Markdown
report preserves their historical results and limitations. No new inference or
final evaluation is authorized by publishing the source.
