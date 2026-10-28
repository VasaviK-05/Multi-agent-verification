# Stage 4: compatible artifacts and explicit game execution

Stage 3 was still uncommitted on `vasavi/game-offline-evaluation` at
`566961f52346d490746231f9636851a6ddb403f4`. Its ten files matched the regenerated
Stage 3 review export after LF normalization. The index was empty. Fetching found
no newer main or branch changes, and no AGENTS.md applied. The verified Stage 3
source passed 595 affected component tests before Stage 4 editing.

To preserve that review boundary, all Stage 4 edits live in the isolated
`stage4-runtime-workspace` beside the review export, not in the original repository.
`stage4-source-baseline` is an exact source copy made before editing, with a separate
raw/LF manifest. Neither copy contains Git metadata, ignored secrets, dependencies,
or a virtual environment. Tests use the existing interpreter and a launcher that
pins application/test imports to the isolated copy while allowing read-only Git
parity checks against the original committed baseline. No Stage 4 branch, staging,
commit, merge or push was performed. The Stage 4 patch is relative to verified
Stage 3, not a replacement for its export. Apply it only after accepting that base.

The Version 1 specification and complete Stage 1–3 documentation were read, together
with the actual orchestrator, selector, policy/certificate validation, decision and
normalization code, replay, coverage, response serialization and feedback binding.

## Artifact and offline construction

`ExecutionContract` in `app.game.execution_contract` is the dataset-free definition
of the existing replay contract. `ReplayContract` remains an import-compatible
alias. Its version is `offline_public_decision_v1`, retaining the existing coverage,
contributor and failure semantics. Threshold validation now rejects endpoints 0/1
up front, as DecisionEngine already requires strict interior thresholds. History
priors remain training provenance fields; runtime never reconstructs history.

`PlanningContext.execution_contract_json` is optional canonical contract JSON.
When present it participates in the existing compatibility hash, therefore in the
matrix and policy. It binds the actual threshold, contract versions, failure rule,
configuration identity and priors independently of the opaque dataset-manifest
digest. Legacy absent values are omitted from serialization; original legacy
compatibility hashes remain unchanged.

Fresh offline binding populates this explicit contract before constructing payoffs
and policies. Existing opaque-only Stage 3 bindings retain legacy offline evaluation
behavior, but cannot be exported as deployable artifacts. They need a new explicitly
bound context and rebuilt policy; runtime never relabels an old empirical matrix.
`category_id` excludes both training/deployment bindings, preserving pre-binding
planning categories. The one existing offline test-helper adjustment resets both
fields when constructing a new unbound context; no assertions were weakened.

`PolicyArtifact(version="deployable_game_policy_v1", ...)` contains:

- The original `Policy` with matrix, exact strategy definitions, provenance,
  numerical certificate and strategy probabilities.
- The complete captured `PlanningContext` and frozen reputation statistics.
- The explicit `ExecutionContract` and execution-configuration identity.
- An explicitly registered `applicable_domain`.

Construction and JSON loading revalidate nested models, policy/context/matrix
compatibility, enumeration/row definitions, numerical primal-dual certificate and
supported aggregation versions (`log_odds_v1`, `groups_v1`). The contract must equal
the JSON bound in the context, and configuration identities must agree. Changing
only a threshold/contract, or changing both it and the context while retaining the
old policy, rejects. These integrity digests are not signatures or independent
proof of the origin/calibration of empirical matrices; deployments must trust and
control their configured artifact source.

Offline export uses the existing role/history validation before artifact creation:

```python
from app.game.offline.evaluation import bind_evaluation, fit_policy, export_artifact

context = bind_evaluation(context, manifest, contract, attack_specification)
policy, development = fit_policy(context, manifest, contract, attack_specification)
artifact = export_artifact(policy, context, manifest, contract, attack_specification,
                           applicable_domain=context.plan.domain)
artifact_json = artifact.model_dump_json()
```

All dataset records/labels stay offline. The artifact carries only their immutable
provenance identifiers and frozen statistics. Runtime loads no dataset, reconstructs
no history, builds no payoff and calls no optimizer. Certificate verification uses
the existing arithmetic verifier, not a new LP run. Numerical solver dependencies
may be imported by existing policy code; their optimizer is never invoked at runtime.

No empirical policy or application inputs are included. Synthetic provenance
survives JSON serialization and is rejected by retrieval unless the explicitly named
server-only `allow_synthetic_for_tests=True` flag is set.

## Providers, episodes and applicability

`PolicyProvider.snapshot()` supplies one immutable tuple of registered artifacts.
`InMemoryPolicyProvider` validates/detaches registrations and atomically replaces
the tuple under a lock. Storage and database policy schemas are out of scope.

`DeploymentEpisode(episode_id, context, contract, execution_configuration_id)` is
trusted server configuration. Its context includes the frozen reputation and
current budget, costs, dependencies, analysis/configuration provenance and versions.
It requires an explicit contract binding. A new episode with changed statistics or
settings needs a compatible rebuilt/retrieved policy. Live feedback updates remain
on the original manager and do not mutate the episode.

`GameRuntime(provider, episode, rng, allow_synthetic_for_tests=False)` captures the
episode and provider snapshot once per run. It clones the selector's mutable
planning configuration and substitutes a read-only frozen-statistics adapter only
on that clone. It reuses the actual selector plan, capability and prerequisite
definitions, including the single batch-read interface. No live reputation read,
manager replacement or verifier construction occurs during planning/retrieval.
Selected runtime resolution shares the existing operational lazy-instance cache;
no unselected verifier is constructed. Custom selector subclasses must retain the
documented plan/resolve and captured configuration contracts; this narrow adapter
does not provide a general clone protocol for arbitrary stateful selector overrides.

The newly captured request context must match the configured episode's complete
compatibility ID. This checks the existing analyzer validity/requirements/signature,
domain/status, reference availability, candidates/eligibility/prerequisites,
capabilities, execution minimum, relevant configuration/version fields, budget,
costs/units, dependencies and frozen snapshot. No request-supplied compatibility ID
is trusted. Provider artifacts are revalidated and must match exactly. Strategies
are never pruned, probabilities never renormalized, and no coverage/budget rule is
relaxed to make lookup succeed.

Explicit weighted cross-domain development pooling and sparse-domain routing are
provided by `app.game.offline.pooling` and `DomainRoute`. They retain exact target
domain/reputation bindings and require declared source weights/applicability.
Resource-bound v2 contracts also validate adapter-supplied fingerprints before and
after execution. See [pooling and provenance](game_pooling_and_provenance.md) for
interfaces, ownership and the remaining empirical/integration responsibilities.

Missing, invalid, incompatible, synthetic-disallowed, ambiguous and infeasible
selection yields public uncertainty and a structured selection status/reason with
zero dispatch and zero estimated attempt cost. Invalid server configuration may
reject at construction/loading before a request can run. Unexpected provider or
programming exceptions remain visible; they are not silently replaced by baseline.

## Explicit orchestration and complete-team execution

```python
from app.game.artifacts import PolicyArtifact, DeploymentEpisode, InMemoryPolicyProvider
from app.game.execution import GameRuntime
from app.orchestration.validation_orchestrator import ValidationOrchestrator

artifact = PolicyArtifact.model_validate_json(artifact_json)
episode = DeploymentEpisode(episode_id=episode_id, context=artifact.context,
    contract=artifact.contract, execution_configuration_id=current_execution_config_id)
provider = InMemoryPolicyProvider((artifact,))
runtime = GameRuntime(provider=provider, episode=episode, rng=rng)
orchestrator = ValidationOrchestrator(verifier_selector=selector,
    reputation_manager=live_manager, execution_mode="game", game_runtime=runtime)
```

The server must supply the actual current execution-configuration identity, not
blindly echo an old artifact identity after models/corpora/prompts change. Provider
and episode configuration are trusted deployment inputs, not request metadata.
The ordinary request schema gains no policy, snapshot, dependency or mode fields.
The existing ValidationService accepts the explicitly configured orchestrator.
Default route/service/orchestrator construction remains baseline mode.

Baseline selection, fallback, early stopping, reputation, automatic external
ground-truth lookup, response fields and feedback behavior retain their existing
code path. Game mode requires explicit `execution_mode="game"` plus a GameRuntime;
supplying a runtime without that mode rejects configuration. In game mode the
automatic ground-truth evaluator is neither constructed nor called: runtime needs
no labels and performs no automatic experimental feedback.

Game execution validates all exact strategy costs against the declared budget
before RNG sampling or any dispatch, then samples once using the injected RNG.
It attempts every selected verifier in canonical team order, even after a decisive
report. It never calls early stopping, appends fallback, retries, replaces a failed
member, or silently switches to baseline.

`VerifierUnavailable` is recorded as unavailable. Only the explicitly identified
`VerifierExecutionFailure` is recorded as failed; adapters must deliberately
translate a classified recoverable failure to that exception. Ordinary RuntimeError,
ValueError, unexpected construction/import errors, malformed reports and wrong
verifier/run identities propagate without storing a validation or learning votes.
Returned reports are detached and validated through the existing normalizer and
canonical report identity/strict JSON contract. Unannotated legacy reports bind to
the current run; annotated reports must match it. Zero confidence remains directional
but cannot supply achieved coverage. No attacks are applied or imported by runtime.

Costs are configured estimates in the declared budget units. The selected cost is
checked before dispatch; attempted cost sums each selected attempt once, including
explicit unavailable/failed construction or execution. They are not measured
latency, money, or a guaranteed physical-resource bound.

## Shared finalization and audit/feedback

`finalize_decision` is a pure dataset-free helper shared with offline replay.
It verifies the exact selected strategy, complete ordered execution states and
normalized report identities, then aggregates using the contract threshold and
frozen snapshot. It shares the same baseline contributor count and dependency-group
active-member/structural-exclusion rule previously used by Stage 3.

Only observed factual-output certificates establish arithmetic/direct-fact coverage;
expected capabilities never become certificates. Other achieved contracts remain
unresolved. The helper preserves raw-score strict cuts, no-result `unknown`,
all-abstention and zero-confidence distinctions in numerical audits. Public output
is uncertain when minimum contributors, required achieved coverage or the evaluated
execution contract fails. Both `all_selected_returned` and
`allow_failed_if_covered` retain their meanings. Missing recordings remain an offline
input error, distinct from genuinely observed runtime unavailable/failed attempts.

The existing response `execution_audit` exposes `game_execution_audit_v1`, mode,
episode/artifact/policy/matrix/snapshot/strategy IDs, training provenance digest,
team, aggregation, threshold/contract, dependency assumptions, budget/units,
selected/attempted estimated costs, ordered attempt outcomes, selection failures,
numerical decision, achieved/unresolved requirements and override reasons.
Nonempty results also carry the same detached JSON audit in the existing reserved
metadata slot. `selected_verifiers` is the sampled team, including failed members;
`results` contains only returned reports. Selection failures retain an audit even
when no result exists. No schema or migration was changed; durable storage of
audits for empty-result runs remains a separate persistence integration requirement.

Validation IDs, detached stored results and later identity-bound external feedback
reuse the existing orchestrator methods unchanged. Public decisions never become
labels. Valid external feedback updates only the live manager under existing
replay/provenance rules; it cannot change the frozen episode. The stored response
object bindings continue to reject mixed runs and conflicting feedback.

## Review scope and validation

Exact changed paths and rationale:

- `app/game/artifacts.py`: validated artifacts, frozen deployment episodes and provider interface/in-memory registry.
- `app/game/execution.py`: compatible retrieval, one sample, complete-team execution and structured audits/failures.
- `app/game/execution_contract.py`: dataset-free shared versioned replay/execution contract.
- `app/game/finalization.py`: pure shared aggregation, contributor, coverage and failure finalization.
- `app/game/frozen_planning.py`: narrow frozen-statistics selector adapter without live-manager mutation.
- `app/game/models.py`: optional serialized execution binding and legacy serialization/digest preservation.
- `app/game/offline/evaluation.py`: bind explicit contract before new fitting and export validated artifacts offline.
- `app/game/offline/replay.py`: retained ReplayContract alias and shared finalization adapter.
- `app/orchestration/validation_orchestrator.py`: explicit opt-in game dispatch and compatible response/feedback binding.
- `tests/test_game_offline.py`: reset the new optional binding in the existing unbind helper.
- `tests/test_game_runtime.py`: clearly labelled synthetic artifact/provider/execution/parity regressions.
- `docs/game_runtime_integration.md`: interfaces, usage, limitations and validation handoff.
They are limited to game artifact/execution modules, explicit orchestrator dispatch,
minimal contract/finalization/offline-export adapters, focused tests and this document.
Verifier, retrieval, corpus, generation, frontend, database/schema, routes, service
and teammate-owned evaluation modules are untouched. The original Stage 3 working
tree and export remain byte-identical to their captured source manifest.

Validation results:

- Verified original Stage 3 source: 595 affected component tests passed.
- Isolated Stage 4 combined run: 754 passed, 3 demonstrated baseline failures,
  plus the existing Starlette TestClient deprecation warning. This includes Stage
  1–3, 47 initial runtime cases, decision/normalization, selector, reputation,
  stopping, analyzer/context, adaptive pipeline and reputation integration tests.
- Expanded focused runtime suite: 59 passed, including the subsequent coverage,
  inactive-team, budget-before-construction, pooled-domain, new-episode and
  detached-artifact regressions.
- The fresh-process serialized-artifact test was strengthened afterward to execute
  GameRuntime.run while blocking offline imports and optimizer calls: 1 passed,
  58 deselected. It also asserts that execution imported no database module.

Commands use the existing virtual environment and `stage4-run-tests.py` launcher,
with `-q -p no:cacheprovider`. The launcher pins imports to the isolated source and
passes its absolute test paths to pytest. Component checks covered:

```text
tests/test_game_runtime.py tests/test_game_offline.py tests/test_game_foundation.py
tests/test_dependency_aggregation.py tests/test_decision_engine.py
 tests/test_vote_normalization.py tests/test_early_termination.py
 tests/test_verifier_selector.py tests/test_reputation_manager.py
 tests/test_reputation_imports.py tests/test_question_research_context.py
 tests/test_question_analyzer.py tests/test_adaptive_pipeline.py
 tests/test_reputation_integration_upgrade.py
```

The three failures were independently reproduced by selecting the same tests in
an unmodified original Stage 3 process, without the Stage 4 launcher or source
replacement: 3 failed, 1 passed, 88 deselected. Tests are:

- `tests/test_adaptive_pipeline.py::test_actual_evidence_output_contract_is_consumed_without_models[probabilities0-passed]`
- `tests/test_adaptive_pipeline.py::test_actual_evidence_output_contract_is_consumed_without_models[probabilities1-failed]`
- `tests/test_adaptive_pipeline.py::test_actual_conflicting_evidence_cannot_cover_factual_request`

The first two retain public uncertainty; the third reports no_relevant_evidence
rather than conflict. Baseline command: the original interpreter ran
`-m pytest tests/test_adaptive_pipeline.py -q -p no:cacheprovider -k
"actual_evidence_output_contract_is_consumed_without_models or
actual_conflicting_evidence_cannot_cover_factual_request"` in the original tree.
Its full source manifest, Stage 3 hashes, branch, HEAD and empty index were
verified before/after. No teammate-owned test or verifier code was changed.

Some early sandboxed test attempts did not finish promptly;
completed runs used explicit cache disabling and the existing outside-sandbox
permission for Windows subprocess/TestClient checks. No live PostgreSQL, real
models/providers, full-repository suite or empirical research evaluation was run.

Ownership and compatibility inspection found no remaining in-scope blocker for
independent Stage 4 review. All syntax/whitespace and baseline-plus-patch integrity
checks are recorded in the review manifest. The Stage 4 export includes the complete Stage-3-relative patch and
full contents of every changed/new file. Its hash conventions distinguish raw
working bytes from UTF-8 LF-normalized payloads; caches, dependency files and secrets
are excluded. No test result is an empirical policy-performance claim.

Remaining project decisions are the actual empirical artifact and its trustworthy
provenance, independent datasets/labels, pooling applicability, dependency pathways,
cost/penalty calibration, primary/sensitivity settings, deployment episode rollover
and real model/corpus/configuration fingerprints. Provider persistence, authentication
of deployed artifacts, empty-result audit persistence, production deployment and
research experiments remain outside this stage. Baseline stays the default.
