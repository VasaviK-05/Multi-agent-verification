# Stage 3: isolated report replay and empirical payoff construction

This library implements report-level corruption experiments, not upstream evidence
compromise. It runs no verifiers, retrieval, generation, fallback queue, early
stopping, database writes, or production dispatch. No dataset or fitted empirical
policy is included. All test reports, resource estimates, losses and pathways are
explicitly synthetic fixtures; their results are correctness checks, not research
performance measurements.

## Starting state and ownership

The branch was created as `vasavi/game-offline-evaluation` from fetched
`origin/main` at `566961f52346d490746231f9636851a6ddb403f4`. That commit was the
latest main and its tree matched reviewed Stage 2 merge commit
`2465e8268df14f1fc047da1bb4df7e8b291236b2`. The starting working tree/index were
clean. No applicable AGENTS.md was found. Version 1, the Stage 3 request, and both
foundation and aggregation documents were read. Main had no newer changes.

The only changes to existing code are an optional offline compatibility binding
in `app/game/models.py`, and extraction of the existing pure factual-output helper
from `app/orchestration/validation_orchestrator.py`. The orchestrator imports the
same function under its original private name and retains the arithmetic constant.
Its execution, stopping, feedback, database and coverage rules are otherwise
unchanged. Verifier, retrieval, corpus, generation, frontend, database, existing
tests and teammate-owned evaluation modules are unchanged.

## Records and independent splits

`app.game.offline.records` provides frozen, revalidated, detached records:

- `Attempt`: verifier identity, explicit outcome, canonical report JSON, execution
  ID, execution configuration, report provenance and a declared attack adapter.
- `Example`: original question/answer/reference, domain, planning category, unique
  example/question/run identities, shared split identity, independent boolean
  correctness label, label source/method, cache contract, and all candidate outcomes.
- `Partition`: one nonempty history, development or final-test role and dataset ID.
  Examples and runs are unique within each partition.
- `DatasetManifest`: exactly one of each role, distinct dataset IDs, evidence kind
  and a version. Content IDs canonicalize partition/example/attempt ordering.

An independent label must explicitly be `True` or `False`; strings, missing labels
and agreement-derived label methods reject. `independent_human` and
`independent_ground_truth` are caller declarations, not authentication. The library
never derives correctness from consensus or a framework decision. Data collection
must establish the truth and independence of these declarations.

Cross-role overlap is checked using example ID, shared split identity, question ID,
run ID and exact question/answer/reference content digest. Related claims and
alternate answers must carry a common split identity/question ID. Different
partition names cannot conceal these overlaps. Semantic paraphrases cannot be
automatically identified from text; the supplier must assign their grouping IDs.
Repeated related examples may share a group within one role. Every declared
development example remains in every matrix cell's denominator.

Returned directional reports, returned abstentions, unavailable checks, failed
attempts and missing recordings are distinct states. Returned states must agree
with the current normalizer and carry a report. Other states cannot carry a report.
Reports are stored as canonical strict JSON strings, and access returns detached
VerificationResult instances. Nonfinite report metadata and identity mismatches
reject through the existing Stage 2 canonical-report validator.

Replay currently requires an explicit outcome for every captured candidate,
including an explicit unavailable outcome when genuinely observed. A missing
recording, omitted candidate or extra candidate is an input error; it is never
silently turned into a failure, uncertainty observation, or dropped example.

Cache reuse requires `complete_team_independent_v1`: recordings were produced by
complete independent checks of the same supplied question/answer/reference under
the declared configuration, with no team/order/prefix-dependent behavior or shared
mutable execution state. Example and attempt execution/configuration IDs must
match, and the reference-availability state must match planning. The caller must
include corpus/model/prompt/version and other relevant upstream fingerprints in
the execution configuration and retain detailed report provenance. This attestation
cannot make an incompatible cache valid; this library cannot independently audit
how historical reports were collected.

Each evaluation accepts one compatible planning category, computed by
`category_id(context)` before offline binding. It binds the existing domain,
requirements/validity, analyzer versions, candidates/prerequisites, budget, costs,
dependencies and frozen reputation. Records from another category reject; callers
partition them and build separate games. There is no automatic pooling choice.

## History and frozen episodes

`history_reputation(history_partition_or_manifest, prior_alpha=..., prior_beta=...)`
always creates a fresh, nonpersistent ReputationManager. It accepts only the history
role, skips unavailable/failed/abstaining reports, and compares each directional
verifier decision with the independently labelled answer. Missing history recordings
reject. No caller manager is mutated and no production feedback is written.

Build a history Partition first, establish an isolated manager with explicit priors,
capture a PlanningContext using that manager, then assign its `category_id` to the
compatible records and construct the complete disjoint manifest. Example category
annotations on history records do not influence learning. They can be filled after
context capture. Finally bind the evaluation:

```python
from app.game.offline.records import history_reputation
from app.game.offline.evaluation import bind_evaluation, fit_policy, evaluate_final_test

manager = history_reputation(history_partition, prior_alpha=alpha, prior_beta=beta)
# Use manager in the existing selector/capture_context APIs. Supply real costs,
# losses, dependencies, aggregation versions and manifest dataset provenance.
# Build the full manifest with the captured pre-binding category_id.
context = bind_evaluation(context, manifest, replay_contract, attack_specification)
policy, development = fit_policy(context, manifest, replay_contract, attack_specification)
held_out = evaluate_final_test(policy, context, manifest, replay_contract, attack_specification)
```

Binding recomputes history statistics in another isolated manager and requires exact
equality to every captured full statistic, not rounded candidate means. Explicit
priors in the replay contract avoid reconstruction from alpha/count subtraction.
The captured snapshot remains unchanged by development/test labels or replay.

`ReplayContract` requires version `offline_public_decision_v1`, coverage version
`factual_output_contract_v1`, contributor version `baseline_log_odds_active_group_v1`,
an explicit finite decision threshold, explicit history priors, execution
configuration ID and one explicit failure contract. No empirical defaults are supplied.

The minimal context extension is optional `offline_evaluation_id`. Its digest binds
version `offline_evaluation_binding_v1`, the complete manifest, attack specification,
and replay contract. It participates in existing matrix/policy compatibility.
Legacy contexts without that binding preserve their previous compatibility digests.
Changing threshold, history, datasets/reports/labels, attack adapters, suppression,
execution configuration, failure rules or any version requires a fresh binding and
compatible policy. Losses, units, costs, budgets and aggregation versions remain
bound by Stage 1. Dataset IDs and evidence kind must match PayoffProvenance, and
its attack specification must equal `AttackSpecification.specification_id`.

The manifest contains final-test labels for integrity/role validation only; fitting
never scores them. In an access-controlled study, data custody must separately
prevent developers from viewing those labels while tuning. Hashes do not enforce
organizational blind evaluation.

## Fixed attack columns and adapters

`AttackSpecification(version="report_corruption_v1", suppression=...)` requires
explicit unavailable or abstention suppression. `enumerate_attacks` builds clean
plus four transformations per full connected failure group in the entire captured
registry, including shared unknowns and absent bridge nodes. Only afterward does
replay project each action onto a selected team. The attacker never gets a label
or chooses a target after seeing that team. An outside-team target is ineffective,
not retargeted. Action IDs bind full group membership, kind and specification.

`transform` copies/revalidates reports. Forced support/rejection produces normalized
strength +1/-1; confidence inflation sets magnitude to one retaining direction;
suppression removes a returned report or makes it explicitly abstain. Directional
attacks preserve genuine abstentions, and no attack creates a report from an
unavailable, failed or missing outcome. Postconditions use the existing normalizer.

Declared adapters are `rule_v1`, `evidence_v1`, `confidence_v1`, `semantic_v1` for
built-in identities and `generic_v1` for other normalized result contracts. Rules
retain rule identity/kind and use correctness bits. Forced confidence attacks update
judgments and majority along with passed/decision/score. Forced evidence attacks
corrupt the existing direction's evidence rows and existing claim decisions; they
never fabricate missing rows/claims. Confidence inflation leaves those claim and
evidence structures untouched. Semantic/generic adapters honor the authoritative
decision contract. Mismatched adapters, unsupported evidence shapes and failed
normalization postconditions reject explicitly. Adding a verifier convention needs
a versioned supported adapter; score-only mutation is not a universal adapter.

Audits identify attack/version, validation/verifier identity, before/after states and
normalized masses/directions and achieved coverage, effectiveness and a reason, explicitly labelled report-level
corruption. Original reports and provenance remain in the content-addressed
manifest; detailed post-aggregation explanations are retained per replay outcome.

## Public decisions, loss and metrics

`replay` is the lower-level replay primitive; fitting/final-test entry points enforce
the complete manifest/binding. It validates exact feasible strategy definitions,
uses only that complete team, its aggregation, threshold and frozen snapshot. It
does not resolve/execute verifiers, call early-stopping assessment, or append fallback.

Coverage uses the extracted unchanged factual helper. Only current arithmetic and
direct-fact certificates can establish their respective requirements. Expected
capabilities alone cannot certify coverage. Unsupported achieved contracts remain
explicitly unresolved. Minimum contributor count reuses the captured execution
floor. Frozen reputation-weighted replay uses the existing baseline contributor
count, including zero-log-odds exclusion. Dependency aggregation counts active
nonstructural directional reports, including zero-reliability fallback members.
This explicit game replay extension does not alter baseline stopping behavior.

`all_selected_returned` requires every selected attempt to return a report, in
addition to contributors and coverage. `allow_failed_if_covered` permits recorded
failures/unavailability only when minimum contributors and achieved coverage still
hold. Neither turns a missing recording into an execution outcome. Any failed
execution condition or unresolved coverage forces public uncertainty even when
the numerical aggregate is decisive. No-result and abstention distinctions remain
available in the underlying decision audit. Low-level replay may compare contracts;
policy evaluation requires the exact bound contract.

`construct_payoffs` builds exactly every feasible team/aggregation row and every
fixed attack column. Each cell is mean public-decision loss over all development
examples plus resource_weight times the selected team's estimated attempt cost.
The full attempt estimate is charged exactly once, including failed attempts, using
the same units as planning budget. No uncertainty-driven example omission occurs.
Empty/incomplete inputs, incompatible records and nonfinite payoffs reject.

Correct acceptance/rejection has loss zero. False acceptance/rejection uses the
explicit corresponding penalty; uncertain/unknown/unresolved uses the explicit
uncertainty penalty. These application choices are not scientifically calibrated.
`fit_policy` feeds that fully bound matrix to the existing validated minimax builder.
`evaluate_final_test` validates an already frozen policy and sums outcomes using its
actual strategy distribution, including zero-probability strategies without selecting
the best one. It performs no optimization or learning on final-test labels.

Per-example outcomes retain numerical/public decisions, reasons, contributor and
coverage diagnostics, attempt states/cost, attack audits, and serialized decision
explanations. Cell and mixed-policy metrics expose correct/false accept/reject,
uncertain and unresolved counts (unresolved is a subset diagnostic), coverage,
selective risk, expected attempt cost and mean total loss. Selective risk is None
when decision coverage is zero. Mixed counts are expectations, not observed integer
counts. These outputs support later matched-coverage and configuration-sensitivity
analysis; this stage supplies no pooling, calibrated penalties, partitions or claims
about research performance.

## Validation and handoff

Changed paths:

- `app/decision/coverage.py`: pure unchanged factual certificate helper.
- `app/orchestration/validation_orchestrator.py`: import that helper; baseline preserved.
- `app/game/models.py`: optional offline binding; legacy digest preservation.
- `app/game/offline/__init__.py`: isolated package marker.
- `app/game/offline/records.py`: independent data, identity, cache and history contracts.
- `app/game/offline/attacks.py`: fixed full-registry actions and audited copied transforms.
- `app/game/offline/replay.py`: versioned full-team execution/coverage semantics.
- `app/game/offline/evaluation.py`: empirical development construction, policy fitting,
  separate held-out mixed-policy evaluation and metrics.
- `tests/test_game_offline.py`: synthetic focused regressions and committed-source parity.
- `docs/game_offline_evaluation.md`: interfaces, assumptions and validation record.

Final combined component run: **594 passed**, including Stage 1 (99), Stage 2
(68), offline (47), and existing decision, normalization, early termination,
selector, reputation, import and analyzer/context components. Commands use
`.\.venv\Scripts\python.exe -m pytest`:

```text
tests/test_game_offline.py tests/test_game_foundation.py
tests/test_dependency_aggregation.py tests/test_decision_engine.py
tests/test_vote_normalization.py tests/test_early_termination.py
tests/test_verifier_selector.py tests/test_reputation_manager.py
tests/test_reputation_imports.py tests/test_question_research_context.py
tests/test_question_analyzer.py -q
```

The final focused run passed **48 offline cases** after adding coverage-aware
attack-effectiveness diagnostics; a report can change achieved coverage even when
its normalized vote mass is unchanged.
Coverage includes attack scope/postconditions and abstention/failure preservation,
copied-state isolation, leakage and independent-label rejection, stable full-group
columns, coverage/public overrides and baseline parity, failure costs, explicit
zero-coverage risk, hand-calculated payoffs, mixed expectations, history precision,
configuration rejection, development-to-policy construction, final-test no-fitting,
legacy digest preservation and database-free import isolation.
Both Git whitespace checks and explicit new-file whitespace checks passed.

Affected pipeline/reputation integration: 112 passed, three demonstrated baseline
failures, with the usual Starlette TestClient deprecation warning:

- `tests/test_adaptive_pipeline.py::test_actual_evidence_output_contract_is_consumed_without_models[probabilities0-passed]`
- `tests/test_adaptive_pipeline.py::test_actual_evidence_output_contract_is_consumed_without_models[probabilities1-failed]`
- `tests/test_adaptive_pipeline.py::test_actual_conflicting_evidence_cannot_cover_factual_request`

The first two yield public uncertainty; the third produces no_relevant_evidence
instead of conflict. A fresh Python process installed a read-only MetaPathFinder
loading committed `app.orchestration.validation_orchestrator` and `app.game.models`
source via `git show 566961f52346d490746231f9636851a6ddb403f4:<path>`. It selected
the two test function names with `-k`, disabled pytest's cache provider, and got
3 failed, 1 passed, 88 deselected. No working files were replaced or reset. The
reproduction script is included beside the export artifact, outside the repository.
These verifier/evidence failures remain outside this stage's ownership.

No full repository suite, live PostgreSQL integration, real dataset evaluation or
upstream compromise experiment was run. Actual labels/grouping provenance,
dependency pathways, calibrated costs/units, penalties, primary/sensitivity settings,
dataset custody and pooling remain explicit project inputs. Production mode is
unchanged. Changes remain unstaged and uncommitted for review.
