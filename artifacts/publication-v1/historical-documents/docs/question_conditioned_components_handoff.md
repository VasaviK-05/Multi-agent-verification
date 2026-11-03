# Question-conditioned teams and bounded components: owned framework handoff

This is an opt-in framework change, with no API/default activation. The two
frozen empirical policies still choose Rule alone for arithmetic and Evidence
alone for direct facts. No real fitted policy currently chooses a pair or triple.
Reference probes and this compound smoke test are not fitted policies.

## What works

`app.game.question_routing.QuestionPolicyConfiguration` configures explicit
registrations. `configuration_from_atomic_artifacts(artifacts, allowlist=...)`
validates supplied `PolicyArtifact` objects and returns a configuration and frozen
provider. `configuration.router().run(selector, request, validation_id,
provider=provider, rng=rng, resource_observer=observer)` is the API-owner entry point.
The request must expose `question`, `answer` and `context`. Nothing is registered
globally. Existing `TaskPolicyRouter`, `PrototypeRouter` and prototype allowlists
remain in place. Integrating this interface must retain the existing outer
prototype allowlist; an explicit configuration allowlist can further restrict it.

The wrapper derives a question-only signature and reuses `TaskPolicyRouter` for
registration uniqueness, lookup and atomic execution. The key consists of the
task/domain/requirement/rule identity, difficulty band and score, and reference
presence; budget selects an explicitly registered budget variant. Compound keys
add the versioned measure/check/dependency shape. The answer, labels, ground truth
and verifier findings never select the route or strategy. Difficulty is the
existing heuristic feature, not a measured correctness label. These narrow data
do not establish broad difficulty adaptation.

For compatible questions in one signature, the registered policy supplies the
same distribution. Sampling within that distribution is random selection, not
additional question adaptation. Team sizes 1–4 are feasible where capabilities,
coverage, informative minima and budget permit them. There is no easy→one or
hard→three rule and no team-size quota. The compound roster currently needs at
least Evidence plus Rule because no existing single verifier supplies both checks.

`artifacts/question-conditioned-components-v1/real-routing.json` demonstrates,
without inference, that the actual history questions “What is 328 + 536?” and
“What is the population of Belgium?” resolve to their frozen singleton policies.
The original policy/context IDs are checked against the prior freeze manifest.
The software tests use explicitly synthetic joint games to exercise pair/triple
policy sampling. Those artificial payoff matrices are software fixtures only.

Missing categories return `missing_policy`; unsupported questions return
`unsupported_category`; incompatible policies/resources fail before dispatch.
No nearest-policy or cross-task-history fallback is supplied. Reference
comparison, the newly versioned difference wording, and both compound categories
have no registered empirical policy in this handoff.

## Component protocol

`app.game.component_binding` is the pure input adapter. Version
`fact_plus_sum_binding_v1` accepts only the two already diagnosed questions:

* What is the area of Bahrain, and what is that area plus 10 square kilometres? Give both values.
* What is the population of Belgium, and what is that population plus 1000? Give both values.

Matching is case-insensitive with surrounding whitespace stripped. It does not
accept arbitrary compound prose, other operations, countries, increments or units.
The answer is a JSON object with **exactly two decimal-string fields**, for example
`{"base":"765","derived":"775"}`. Duplicate, absent or extra fields, JSON numbers,
booleans, exponents, nonfinite numbers and ambiguous prose fail closed. Values
are bounded to 15 integer digits and six fractional digits.

Stable components are `base_fact` (`direct_fact`) and `derived_sum` (`arithmetic`,
dependent on `base_fact`). For that example, the existing Evidence interface gets
“What is the area of Bahrain?” / “The area of Bahrain is 765 square kilometres.”
Rule gets “What is 765 + 10?” / “775”. Both values come from the submitted fields;
the increment comes from the question. A wrong base 766 produces the calculation
“What is 766 + 10?”—the adapter never replaces it with a known true base. The
derived arithmetic is never presented to Evidence as a source fact.

The existing optional reference is passed through the verifier interface; it is
not used to fill either field. Existing Evidence retrieves its configured corpus.
Ground-truth labels remain separate from the live collector. The two source
facts have independently labelled **history** provenance, recorded in
`source-fact-provenance.json`; they are not new blind evaluation groups.

## Contract, decisions and accounting

`app.game.component_execution` defines `ComponentContract` (version
`component_complete_team_v1`), `Obligation`, `ComponentStrategy`, `ComponentPolicy`
and `JointDevelopmentBinding`. A contract binds the question signature, parser,
dependency and decision versions, both frozen constituent planning contexts and
execution contracts, resource manifests, history weights, budgets and minima.
Each context must require exactly its component's check and retain bound
informative contributor semantics. Both components share the declared dependency
registry and resource manifest; task-specific per-call cost estimates may differ.

`enumerate_component_strategies(contract)` reuses atomic feasible enumeration and
forms complete joint plans, with one aggregation rule and at most four distinct
verifiers. Its joint strategy ID hashes the contract and all component assignments.
The sum of **every planned call's** cost must fit the joint budget. Confidence
assigned to both components incurs two calls and two charges; union team size is
still one Confidence identity. No verifier is added after seeing findings.

`run_component_policy(...)` validates the separately registered joint policy,
minimax certificate, exact joint strategy axis and contract before sampling a
whole plan. Atomic `Policy`/`PolicyArtifact` objects cannot validate as component
policies. Empirical joint policies require `JointDevelopmentBinding` with exact
contract/matrix IDs, distinct history/development/reserved-test IDs, sealed
manifest/group-partition digests, label and attack protocol IDs. This is a trusted
offline provenance declaration, like the existing atomic deployment bindings;
it is not proof that supplied labels or experiments are valid. A policy producer
must validate and review those source manifests before export. No empirical joint
binding or payoff matrix has been created in this task. Synthetic policies require
explicit `allow_synthetic_for_tests=True` and are marked in the output.

`run_component_diagnostic(...)` is the separate diagnostic harness. It validates
the same plan, capability, budget, input, resource and decision gates, but its
output is labelled `diagnostic_no_policy` and cannot authorize production routing.
`scripts.component_scenarios.diagnostic_contract` explicitly borrows unchanged
constituent history for this scenario, removing training/deployment bindings. It
does not turn atomic recordings into compound empirical payoffs or reliability.

All component plans are checked against frozen selection inputs before dispatch.
Each component is finalized with the existing `finalize_decision`: original
coverage recognition, thresholds, task-family reputation, dependency aggregation,
informative minima and execution-failure guards remain effective. Acceptance
requires both component decisions to pass. A qualified failure of either required
component rejects; unrelated support cannot average it away. Missing coverage or
unavailable evidence remains uncertain. The all-selected-returned failure contract,
joint distinct-contributor minimum and resource drift can override the joint result
to uncertainty. Unexpected programming/report-validation errors propagate, as in
the existing atomic runtime; only explicitly classified recoverable failures are
recorded as execution failures.

Audit output retains the complete plan ID, component/binding/call/request-derived
validation IDs, reports, achieved/unresolved coverage, states, reasons, numerical
component decisions and timings. Contributor accounting unions influential verifier
names across components. It does **not** assert independent confirmations: the
retained dependency registry includes the shared-unknown compromise group. Repeated
calls do not create additional independent failure paths.

Resources must match before and after execution. The optional upstream
`observer.snapshot_for(selector)` active-instance attestation hook is honored;
otherwise the existing `snapshot()` interface is used. Exact manifest equality is
required here. No relocation exception is silently imported or enabled.

## Bounded live smoke

All eight predeclared examples were executed once: four answer variants for each
of the two questions. There were exactly 16 attempts, eight Evidence and eight
Rule. Every call returned. There were zero Confidence generations, zero retries,
zero blocked network requests, eight local metadata GETs, and unchanged pre/post
resource manifests. No downloads, corpus changes or index rebuilds occurred.

Both correct examples passed. All six incorrect examples failed: correct-base /
wrong-math, wrong-base / internally correct math, and both-wrong for each question.
The area examples therefore produce passed for 765/775, failed for 765/774, and
failed for 766/776. The same behavior is covered by deterministic unit fixtures.
These are known-source diagnostic examples, not independent held-out performance
or evidence that a joint game policy improves on a fixed team.

Mean measured verifier-call time was 100.174 ms for Evidence (52.503–364.645 ms)
and 0.159 ms for Rule (0.144–0.187 ms). These exclude factory loading and are not
service latency guarantees. Raw reports and live timings remain in
`live/attempts.jsonl`; starts were fsynced before each attempt. Replay timings are
separately labelled in `component-outcomes.json`.

After the live run, the adapter was tightened to reject countries/increments
outside these two questions. No calls were repeated. The exact executed adapter
bytes and original SHA are retained as `binding-at-smoke.py`; the additional scope
guard and current hash are documented in `binding-scope-change.diff` and
`post-smoke-scope-guard.json`. Original protocol/seal files were not rewritten.

## Review and integration

New source files: `app/game/component_binding.py`, `component_execution.py`,
`question_routing.py`; the sole additional edit to existing framework source is
`TaskPolicyRouter.resolve` and its equivalent use by `run`. Pre-existing dirty
changes to other files are preserved. Helpers/diagnostics are
`scripts/component_scenarios.py`, `prepare_component_smoke.py`,
`collect_component_smoke.py`, `evaluate_component_smoke.py`, and
`describe_question_registry.py`. Focused fixtures are in
`tests/test_component_execution.py`.

The API owner should explicitly construct validated atomic artifacts from the
existing context/contract/policy files, call `configuration_from_atomic_artifacts`,
retain the prototype allowlist, and supply the unchanged selector, RNG and trusted
resource observer. The component entry-point keyword arguments are
`rng`, `resource_observer`, and test-only `allow_synthetic_for_tests`; configuration
entries are `(signature, budget, primary, ComponentPolicy)`. An unavailable route
can be registered as `(signature, budget, primary, None, reason)`. Keep component
entries empty until a reviewed empirical component policy exists. No API, DB,
frontend or verifier changes are needed for the structured diagnostic protocol.

Upstream was fetched without switching or overwriting this worktree. `origin/main`
is the current base `0b3595e`. The additional remote branch
`origin/codex/game-resource-relocation-20261102` is at `b03ace7`; it adds active
resource attestation and verified relocation, with changes overlapping
`app/game/execution.py` and the project adapter. It was inspected, not merged.
Any later integration must reconcile those resource changes explicitly and retain
their proof checks. No teammate retrieval/generation algorithms were edited.

No commit, push, merge, activation, refit, reputation/threshold change, dependency
change, held-out tuning or broad collection was performed. Existing frozen and
historical artifacts are checked byte-for-byte by `preservation-before.json` and
`verification.json`. The full validation commands/results are recorded in
`checks.json` alongside this handoff's artifacts.

## Remaining empirical work, bounded and separate

1. There is no compatible reference policy, new difference-rule policy or joint
   compound policy. The existing singleton optima are legitimate: larger teams
   did not improve the development worst-case objective and cost more under the
   declared shared compromise model. This task does not change that objective.
2. Before any new collection, predeclare supported question-only categories,
   question rules and grouped source/operand identities; fix loss, coverage,
   dependency/attack assumptions, resource configuration and baselines. Keep all
   answer variants and shared source/template groups in one partition. The two
   compound questions here are only two source groups and cannot justify separate
   history/development/test fits. Additional independent questions need a separately
   authorized study; this implementation does not expand the current scope.
3. A possible next bounded study is at most 48 independent question groups,
   16 history / 16 development / 16 reserved test, and at most four independently
   labelled answer variants per group. Predeclare any difficulty strata from
   numeric syntax/required steps alone; do not infer broad easy/hard adaptation
   from these addition/factual templates. At most four planned component calls per
   answer gives a ceiling of 768 attempts. Confidence calls/generations require
   separate explicit authorization and their own fixed ceiling. Collect complete
   component-bound reports with the declared shared failures; do not infer
   independence from verifier names or fabricate additional failure outcomes.
4. Fit on development only, with history-only weights and a reserved test never
   used for category selection. Compare against the development-best fixed team,
   existing singleton baselines where compatible, fixed Evidence+Rule for compounds,
   and a fixed auxiliary triple only where its actual calls/checks are supported.
   Report component and whole-answer coverage, false acceptance/rejection,
   uncertainty, selective risk, clean/worst-case loss and per-call cost/latency.
   Freeze a conditional candidate only if it improves a predeclared objective at
   the fixed coverage constraint over the best fixed baseline; otherwise keep the
   fixed policy, including a singleton if optimal. Report small-group uncertainty.

The runtime/import interface is implemented; source-manifest validation, genuinely
grouped empirical collection, joint payoff construction and policy fitting belong
to that future offline study. No synthetic fixture or smoke recording has been
exported as an empirical compound policy.
