# Runtime Configuration

## 1. Purpose and scope

This document records the integrated execution paths and policy/resource identities supported by the repository at the inspected revision, together with the strongest execution evidence retained in this checkout. “Verified” here means that the relevant code, contract, or recorded run evidence was inspected; it does not mean that every path is active on a particular deployment host.

It establishes the repository revision, supported baseline/game dispatch, the reviewed frozen Reference and Compound package definitions, their route and resource constraints, and the kinds of behavior evidenced by tests, replays, historical native runs, and persistence records. It does not establish current process environment values, live service availability, current resource compatibility on another machine, population-level benchmark validity, or current API activation of the flexible Reference/Compound routes.

The frozen Reference and Compound packages are package-specific configurations with frozen inputs and narrow route/resource bindings. They are not automatically applicable to a future research benchmark merely because this runtime can load and execute them. A future benchmark requires its own scope and compatible experimental policy configuration.

## 2. Repository and execution identity

Inspected repository revision:

- Branch: `tanmayee-main-integration-review`
- HEAD: `9b8959d6dfc9f873ebbcd6dbfbf5fbe17b46a4d5`
- The commit is a merge commit with integration and main-line parents. The local working tree was clean before this documentation task.

The `EXECUTION_MODE` setting accepts `baseline` or `game`; the default in `app/utils/config.py` is `baseline`. Game mode requires exactly one configured deployment source: a flexible package, prototype bundle, or single policy artifact. Relevant configuration names are `GAME_FLEXIBLE_POLICY_PACKAGE_PATH`, `GAME_FLEXIBLE_ADAPTER_CONFIG_PATH`, route-specific relocation binding settings, `GAME_POLICY_BUNDLE_PATH`, and `GAME_POLICY_ARTIFACT_PATH`. This checkout does not establish which values are set in a running process, so no host-specific values are asserted here.

Relevant entry points are `app/main.py` (FastAPI application and startup recovery), `app/api/routes.py` (`POST /validate`), `app/services/validation_service.py` (mode dispatch), `app/orchestration/validation_orchestrator.py` (baseline/game execution and decision flow), `app/game/deployment.py` (configured game runtime construction and flexible dispatch), `app/game/execution.py` (single-artifact game execution), and `app/game/question_routing.py` (explicit flexible category routing).

## 3. Runtime architecture and execution flow

At the API boundary, `POST /validate` passes the request to `ValidationService`. The service constructs a baseline orchestrator by default, or creates a configured game runtime when `EXECUTION_MODE=game`. The orchestrator then uses the selected execution path. The route persists the returned validation, audit, verifier output, and (when present) ground-truth data through the repository layer.

**Baseline:** the orchestrator analyzes the question, asks `VerifierSelector` for a ranked plan, executes eligible verifiers with its adaptive early-termination path, and combines available reports through the decision engine and coverage checks. Baseline planning is selector-driven; it does not sample a frozen game policy. Baseline is the default setting, but actual deployment state is not inferred from that default.

**Game:** the service constructs a server-configured `GameRuntime`, `PrototypeGameRuntime`, or `FlexiblePolicyGameRuntime` from exactly one configured source. For the reviewed flexible package, question-only classification and the explicit registry resolve the route/signature/budget and a compatible frozen artifact or component policy. The frozen distribution is validated and sampled with a server-owned RNG. The selected complete team executes; game mode does not use baseline early stopping. Finalization applies the selected aggregation contract, contributor and coverage obligations, and execution/resource outcomes. In flexible Compound execution, each required component is checked under its bound team and the component decisions are joined according to the component contract.

The configured runtime returns a `ValidationResponse` and an execution summary. The `/validate` route saves the validation row, creates/updates the audit, and saves verifier outputs. Persisted `validation_executions`/attempt journals are an additional path when `persist_execution` is enabled. These code paths establish intended persistence structure; successful persistence for a particular run is established only by corresponding recorded database evidence.

## 4. Current policy/runtime configuration

### A. Currently frozen/package-specific configuration

The reviewed flexible registration is `reconciliation/policies.json`, bundle version `supported_policy_bundle_v1`, bundle ID `6286898cfdd5ef75b2a09f6556dc2c8fcc1b4f192a6d77dd6decf843867c0882`. `FlexiblePolicyGameRuntime` accepts only that resolved repository package path; the loader validates the package and builds an explicit provider/router. There is no implicit search for arbitrary policy files. The package metadata has `deployment_active: false`; that metadata is not itself the runtime loader gate, and it is not evidence of active deployment.

The package registers atomic Rule, Evidence, and Semantic artifacts plus a Compound component policy and bounded Reference route. Key frozen study identities include:

- **Compound:** policy `0192b98e50ab5dcbd40ca78a0d4a3ec3978dfe8086edcb615802c21024c83532`, contract `0b93b2782afbf1da65be0064dd7a0218f6e347abda1568f2da3d15daa1fbf3e6`, matrix `bd4918e38503ec6ab990c83d687c1bc648015823a5ca2fa9ad18473421ab9970`. The frozen component assignment is Evidence for `base_fact` and Rule for `derived_sum`; both obligations must pass for acceptance, a qualified rejection rejects, and unresolved obligations or contributor/coverage guards produce uncertainty. The package uses the post-development 85% clean-coverage amendment. The original 90% target was infeasible on its Development data; 85% is not a future benchmark target.
- **Reference:** artifact `ee32392c870fba30b08b4f7509af645019d9f8b92dc7c39bafeceb8207745c8f`, policy `c05a50fb5fc3651c8dc5d1bd55ec02086c3f4c26e49e7145393cb007e7149cda`, matrix `90c7f9564573f410b648c7f3b09a23c59a2998da6df0d0f194f4fbab50fb5a13`. The frozen mixture selects Semantic alone with probability 1/6 and Semantic+Confidence with probability 5/6, both using reputation-weighted aggregation. Its route is bounded to registered Reference paraphrase frames and requires the Reference text in `context`. The post-development 50% clean-coverage amendment is specific to that study; the original 90% target was infeasible.
- The same bundle also carries frozen atomic policy artifacts for Rule and Evidence. Their presence does not broaden the Reference or Compound component contracts, nor validate them for unrelated future tasks.

For the flexible routes, selection is registry and signature based: question features, requirements/domain, Reference presence, allowlist, budget, artifact/context compatibility, and resource proofs must resolve consistently. Compound uses its declared catalog/template and typed answer binding. Reference uses its bounded paraphrase route. A missing route, unsupported category, bad binding, incompatible resource, or invalid policy is handled as unavailable/uncertain before or during dispatch; the router does not silently substitute a different policy. Policy validation checks exact feasible strategy definitions and fitted probabilities rather than trimming teams or renormalizing probabilities.

### B. Future experimental policies required for a future benchmark

A future benchmark requires policies fitted or otherwise justified for Person 1's declared dataset, groups, answer space, route and resource choices, plus compatible experimental policies and matched baselines from Person 3. It needs new explicit scope and compatibility bindings where the benchmark differs. Existing frozen probabilities, allowlists, component bindings, coverage amendments, service identities, or package metadata are not defaults for that benchmark. Removing an allowlist by itself would not establish new policy applicability.

## 5. Verifier and service configuration

| Verifier | Role and supported dependency | Route/output and contribution limits |
|---|---|---|
| Semantic | Embedding similarity via a configured SentenceTransformer model. | Used for the bounded Reference comparison route with actual reference text in `context`. Emits support/reject/unsure according to configured similarity thresholds. Similarity is not factual correctness. Its built-in capability is `semantic_comparison` and requires reference context. |
| Evidence | Evidence retrieval over the configured corpus/index plus embedding and NLI resources; relevance/topic gates precede NLI. | Used for factual evidence, including Compound `base_fact`. Emits directional support/rejection or abstention/unsure. Its coverage is limited to the configured corpus, retriever gates, and claim handling; retrieval does not certify general corpus coverage. |
| Rule | Deterministic implemented checks; no model/service dependency. | Used for supported rule patterns, including Compound `derived_sum` arithmetic. A successful or failed implemented check is directional; unsupported questions do not become general factual judgments. |
| Confidence | Agreement among support/reject/unsure judgments. The default provider lazily uses `SelfConsistencyJudge` and the configured local Ollama service/model; injected judgments/providers are also supported. | Participates in the Reference mixture. Agreement is a consistency signal, not accuracy, factual evidence, or independent corroboration. Invalid, tied, unsure, or missing judgments abstain. |

The collection adapter schema defaults to loopback Ollama `/api/generate`, `llama3.2:3b`, five samples, temperature 0.8, and 60-second timeout; it constrains the URL to credential-free loopback. These are adapter defaults, not proof of current process settings. The frozen Reference resource record identifies Ollama 0.40.14 and `llama3.2:3b` with a recorded model digest. The Reference verification notes identify 0.40.14 as required and explicitly say a 0.40.11 target is incompatible. No credentials or local model paths are included here.

## 6. Resource and compatibility verification

`ResourceManifest` binds per-verifier implementation and configuration fingerprints, plus required model/corpus/index/prompt/service identities where applicable. Manifests must cover exactly the captured candidates; shared resource IDs cannot conflict. `ProjectObserver`/route observers inspect the actual selected verifier instances. The flexible runtime requests `snapshot_for(actual_selector)` before dispatch, records the observed manifest/proof, and fails closed on compatibility errors. Execution checks resources again after calls where the observer contract provides that check.

Explicit relocation is route-scoped. The flexible runtime deliberately does not inherit a generic collector relocation binding: factual, Compound, and Reference have separate binding settings, while arithmetic has no such binding. Relocation proofs bind the expected/historical and observed manifests and verified content hashes; they authorize only the explicitly permitted resource delta. Missing, malformed, or mismatching proof does not waive the remaining resource checks. Reference checks its service/model and Evidence index, receipt, corpus, embedding/NLI resources, implementations, and semantic settings. Compound scoped E/R has no Ollama dependency.

There is a critical provenance distinction: `ResourceManifest` and adapter code validate consistency of adapter-supplied observations; they do not independently authenticate the truth of a collection claim. Hashes and saved attestations are not signatures. A repository artifact is portable evidence of its recorded identity, not evidence that the current host has those bytes or services.

Machine-local evidence includes `adapter.json`, saved resource/service observations, and preflight records under `artifacts/`. Some historical adapter records contain host-specific paths; those paths are not reproduced here. Repository-level evidence includes the schemas, compatibility rules, frozen policy/package bytes, portable manifests, and replay/test results. The current checkout does not prove that its host currently satisfies the frozen Reference Ollama 0.40.14 requirement or all model/index pins.

## 7. Verified execution behavior

Evidence classes are reported separately below; the categories are not interchangeable.

| Behavior | Evidence type | What the retained evidence supports | Limit |
|---|---|---|---|
| Baseline selection, verifier execution, decisions and API persistence path | Focused unit/contract test | Baseline orchestration, report normalization, decision, and persistence contracts are covered by repository tests such as `tests/test_adaptive_pipeline.py`, `tests/test_decision_engine.py`, `tests/test_validation.py`, and `tests/test_audit_api.py`. | Tests do not establish a live service or current deployment. No tests were run for this documentation task. |
| Single-artifact game acceptance/report behavior | PostgreSQL persistence | `docs/game_mode_http_audit_20261104.md` records one historical persisted `/validate` game run: Rule was directional, Evidence abstained, and the public result remained uncertain under a two-contributor minimum. It includes validation/audit/output rows and matched resource-manifest IDs. | This is one historical local game-mode run, not current host attestation, nor acceptance of the flexible Reference/Compound package routes. |
| Compound using a genuinely selected frozen team | Recorded replay/frozen evaluation | `artifacts/compound-study-36-v1/acceptance-replay/routing.json` and `artifacts/remaining-category-studies-v1/publication-acceptance/routing.json` retain selected-policy routing/replay; `docs/compound_reference_verification_20261105.md` records frozen Evidence-for-fact plus Rule-for-sum selection and Development/reserved results. | Replays use retained reports; they are not new live verifier calls or held-out API acceptance. The 2026-11-05 verification explicitly records zero new native calls and no live activation proof. |
| Reference fitted selection and outcomes | Recorded replay/frozen evaluation | `artifacts/remaining-category-studies-v1/reference-50-v1/fit/` and `evaluation/` retain the policy, fitted mix, Development and reserved evaluation records. The frozen mixture assigns 1/6 to Semantic alone and 5/6 to Semantic+Confidence. | Recorded collection/evaluation is historical and does not establish current API activation or current host compatibility. The Semantic-only branch can remain uncertain under contributor/reputation semantics. |
| Flexible dispatch, selected teams, component binding, failures and uncertainty guards | Controlled-dependency integration; Focused unit/contract test | `tests/test_flexible_runtime_dispatch.py`, `tests/test_component_execution.py`, `tests/test_game_three_outcomes.py`, and recorded route replays cover synthetic/controlled routing, binding, rejection/unavailability, and finalization contracts. | Controlled reports/factories are not native verifier acceptance. |
| Resource/scope/compatibility failures | Recorded replay/frozen evaluation; Focused unit/contract test | Frozen route replay records unsupported/missing routes and a `resource_incompatible` fixture with no dispatch; resource and binding contracts reject mismatches. | A replay fixture does not prove current machine resources; tests do not substitute for live target attestation. |
| Native Reference and Compound attempts in the later package verification | Native live acceptance (none in that verification) | `reconciliation/local-acceptance-summary.json` records zero native attempts for both actions; Reference was native construction/binding only. `docs/compound_reference_verification_20261105.json` records zero new native calls/generations and `live_activation_proven: false`. | Therefore the package verification must not be described as native Reference/Compound acceptance. Earlier study collections are historical native data, not proof of this integrated API deployment. |
| Timing/cost evidence | Recorded replay/frozen evaluation | `artifacts/capability-probes-v1/timings-summary.json`, `docs/compound_reference_fitting_verification_20261105.md`, and cost-calibration documents retain per-attempt timing/cost estimates. | Per-verifier historical timers exclude some initialization/resource overhead and are not end-to-end API latency or monetary prices. They are not measurements from this task or necessarily this host. |

For retained Compound Development evidence, 48 examples yielded 12 correct accepts, 31 correct rejects, five uncertainties, and no recorded false accept/reject; clean decision coverage was 43/48. These are study outcomes, not universal accuracy. The original 90% clean-coverage target was infeasible; the retained policy uses an explicitly post-development 85% amendment. Reference's retained 50% coverage amendment is likewise post-development and study-specific. Neither configured floor should be promoted as a benchmark requirement.

## 8. Persistence and audit configuration

The `/validate` route writes the validation record and audit, persists verifier outputs, and updates the audit with selection plan, selected verifiers, coverage, contributor/decision details, attempt/cost summaries, and failure status when persistence steps fail. When enabled, the orchestrator also writes `validation_executions` and `live_verifier_attempts` lifecycle records with plan digests, execution order, attempt outcome, reports/errors, duration/cost metadata, leases, and recovery state. `app/main.py` invokes incomplete-execution recovery during application startup; startup aborts if that recovery raises.

Schema contracts are in `db/migrations/003_validation_audit.sql`, `004_audit_execution_metadata.sql`, and `008_live_verifier_recovery.sql` through `012_report_validation_id_text.sql`. The latest migrations include attempt identity/idempotency, leases and recovery, and text ID compatibility for report/snapshot IDs. These are source-level migration contracts; no migration was run for this task. `tests/test_migration_runner.py`, `tests/test_execution_journal_lifecycle.py`, and related repository tests provide focused contract coverage.

The retained HTTP audit is evidence of PostgreSQL persistence for that specific historical game-mode run. It does not establish full native crash/failure behavior for every execution state, exactly-once external verifier calls across process crashes, or PostgreSQL persistence for the current flexible Reference/Compound deployment. Code-level lease recovery cannot prevent an external verifier side effect from occurring immediately before a process failure unless the provider itself supplies idempotency.

## 9. Current applicability boundary

The frozen policies apply only inside their bound package and compatibility contexts:

- Compound is a bounded fact-plus-derived-sum task. Its answer binding requires the declared structured string fields and binds the sum to the submitted base value. Its frozen team assigns Evidence to the factual base and Rule to the arithmetic derivative; required component checks are joined under the component finalization contract.
- Reference is a bounded paraphrase/reference-comparison task; the legitimate reference text is required in `context`, and the fitted Reference policy uses Semantic and, probabilistically, Confidence. Reference model/service and evidence resources must match their frozen requirements.
- Atomic Rule/Evidence/other package artifacts remain bound to their own contexts, feasible strategy sets, costs, dependencies, coverage semantics, and resource manifests.

All routes require compatible policy/context/contract identities, unique route and budget resolution, valid verifier/report identities, and applicable resource proofs. Contributor minimums, achieved coverage, incomplete/failed attempts, and unknown/unsupported requirements can force a public `uncertain` outcome even when a numerical subdecision is directional. A package allowlist only narrows what the current package accepts; removing an allowlist alone would establish none of the required dataset, policy, route, answer-binding, resource, service, cost, or coverage compatibility for a new benchmark.

## 10. Research-validation implications

### Already verified

- The integration code has explicit baseline/game mode dispatch and an explicit frozen-package runtime path.
- The repository contains frozen Reference and Compound artifacts, route-specific bindings, fit/evaluation evidence, resource contracts, and recorded replay/integration/test evidence.
- The package verification records zero new native Reference/Compound verifier calls and does not claim active live API deployment.
- Historical PostgreSQL persistence exists for a single-artifact game-mode validation; migration and journal contracts are present in source/tests.

### Reusable as historical/current-package evidence

- Frozen IDs, certificates, package routing, post-development amendments, historical collected verifier reports, recorded evaluations/replays, and per-attempt timing/cost summaries may be cited with their exact scope and evidence type.
- Resource manifests, service observations, and compatibility rules can guide preflight for the exact frozen package. Machine-local observations remain local and time-bound.
- Focused test and controlled-dependency results support code contracts and wiring, not native verifier quality or deployment readiness.

### Must be established for the final benchmark

- **Person 1 dependency:** the final dataset and benchmark scope, groups, candidate answers, split assignments, and corpus/index decisions must be defined and validated. These determine route and resource applicability.
- **Person 3 dependency:** compatible experimental policies must be produced for that declared scope, including policy fitting and matched baselines. Existing Reference/Compound package policies do not satisfy this dependency automatically.
- The final benchmark must bind its actual verifier/service/resource identities and execution configuration, settle coverage/contributor/failure semantics and costs, and preserve separately classified execution/acceptance evidence. No numerical benchmark target is inferred by this document.

## 11. Evidence inventory

| Evidence | Type | Repository/artifact source | What it establishes | Limitation |
|---|---|---|---|---|
| Mode selection and API wiring | Focused unit/contract test | `app/utils/config.py`; `app/services/validation_service.py`; `app/api/routes.py`; `app/orchestration/validation_orchestrator.py` | Code-supported baseline/game entry points and validation/persistence flow. | Source inspection does not show current host environment or active mode. |
| Flexible package identity and routes | Recorded replay/frozen evaluation | `reconciliation/policies.json`; `app/game/deployment.py`; `app/game/question_routing.py`; `docs/compound_reference_fitting_verification_20261105.md` | Reviewed package identity, explicit route resolution, frozen artifact validation, Reference/Compound bindings. | Package presence is not deployment activation; local machine must satisfy resource checks. |
| Compound policy and outcomes | Recorded replay/frozen evaluation | `artifacts/remaining-category-studies-v1/compound-85/candidate/policy.json`; `artifacts/compound-study-36-v1/completion-report.md`; `artifacts/compound-study-36-v1/acceptance-replay/routing.json` | Frozen policy IDs/contract, Component Evidence+Rule roles, Development outcome counts, retained replay. | 85% floor was selected after Development; replay does not prove live API execution. |
| Reference policy and evaluation | Recorded replay/frozen evaluation | `artifacts/remaining-category-studies-v1/reference-50-v1/fit/policy.json`; `artifacts/remaining-category-studies-v1/reference-50-v1/evaluation/results.json`; `artifacts/remaining-category-studies-v1/reference-50-v1/fit-report-note.json` | Fitted Reference policy and recorded reserved evaluation under its amended 50% floor. | Historical evaluation and resource identity do not establish present host/API activation. |
| Native integrated package acceptance boundary | Native live acceptance (none for package verification) | `reconciliation/local-acceptance-summary.json`; `docs/compound_reference_verification_20261105.json` | Later package verification attempted no new native calls; Reference evidence was construction/binding only. | Explicitly not active API acceptance. |
| Historical game HTTP run and persistence | PostgreSQL persistence | `docs/game_mode_http_audit_20261104.md` | One persisted game-mode validation, verifier outputs, resource audit, and contributor-guard uncertainty. | One historical run; not current flexible-package API acceptance. |
| Runtime compatibility and relocations | Focused unit/contract test | `app/game/resource_provenance.py`; `app/game/offline/resource_relocation.py`; `docs/game_resource_relocation.md`; `docs/policy-resource-compatibility-diff.md` | Required fingerprints, exact candidate coverage, and narrowly scoped relocation proof rules. | Adapter evidence is consistency checking, not independent attestation of its source truth. |
| Verifier roles and resources | Focused unit/contract test | `app/verifiers/semantic_verifier.py`; `app/verifiers/evidence_verifier.py`; `app/verifiers/rule_verifier.py`; `app/verifiers/confidence_verifier.py`; `app/benchmark/project_adapter.py` | Implemented output semantics and model/service/resource dependencies. | Defaults and implementation roles do not imply calibrated capability or availability. |
| Timings and costs | Recorded replay/frozen evaluation | `artifacts/capability-probes-v1/timings-summary.json`; `docs/verifier_cost_results.md`; `docs/compound_reference_fitting_verification_20261105.md` | Historical measured attempts and fitted cost inputs. | Not end-to-end latency, current-host timing, or monetary price. |
| Persistence/migration contract | Focused unit/contract test | `db/migrations/003_validation_audit.sql`; `db/migrations/008_live_verifier_recovery.sql`–`012_report_validation_id_text.sql`; `tests/test_execution_journal_lifecycle.py`; `tests/test_migration_runner.py` | Source schema/lifecycle/recovery contract and focused test coverage retained in repository. | No migration/database action occurred for this task; tests do not establish all crash windows. |
