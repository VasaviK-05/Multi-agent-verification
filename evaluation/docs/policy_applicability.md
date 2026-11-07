# Policy Applicability

## 1. Purpose

This document defines the evidence-backed applicability boundaries of the Reference and Compound policies retained in the reviewed package at this checkout. It treats the current repository package as a frozen, scoped integration artifact, not as a general-purpose policy catalog.

The following are separate claims and are not equivalent:

- **Package existence:** package or policy bytes are present in the repository.
- **Package compatibility:** code validates the package against its declared contract, policy, route, and resource identities.
- **Successful route selection:** a request resolves uniquely to a registered policy under its route/signature/budget and any allowlist.
- **Controlled execution:** a test or replay exercises dispatch and finalization with controlled dependencies or retained reports.
- **Native live acceptance:** actual verifier instances execute a bounded live case and meet the acceptance conditions for that case.
- **Applicability to a new research benchmark:** policy scope, fitted population, route, resources, and evaluation contract match the final benchmark.

Evidence for an earlier item does not automatically prove a later one. In particular, package presence and replay do not by themselves establish native API acceptance or applicability to a new benchmark.

## 2. Current policy/package inventory

The reviewed flexible package is `reconciliation/policies.json`, version `supported_policy_bundle_v1`, bundle ID `6286898cfdd5ef75b2a09f6556dc2c8fcc1b4f192a6d77dd6decf843867c0882`. `scripts/policy_package.py` verifies the bundle digest and validates its atomic artifacts and Compound `ComponentPolicy`. It registers explicit routes and the package's literal `allowed_questions`; it does not search the filesystem for more policies. The package metadata says `deployment_active: false`; that field is metadata, not a runtime compatibility check or proof of activation.

### Reference package/policy

- **Artifact:** `ee32392c870fba30b08b4f7509af645019d9f8b92dc7c39bafeceb8207745c8f`.
- **Policy:** `c05a50fb5fc3651c8dc5d1bd55ec02086c3f4c26e49e7145393cb007e7149cda`.
- **Matrix:** `90c7f9564573f410b648c7f3b09a23c59a2998da6df0d0f194f4fbab50fb5a13`.
- **Task scope:** bounded paraphrase/reference-comparison frames. The question must be an exact package-allowlisted string of the form `Paraphrase this reference: <reference text>.` and the supplied `context` must match the reference source expected by the Reference route. The registered Reference analyzer/version and fitted task signature must resolve to this artifact.
- **Verifier/team:** the frozen policy assigns probability 1/6 to the Semantic singleton and 5/6 to Semantic+Confidence, both with reputation-weighted aggregation. The realized team is selected from the fitted distribution; the runtime does not force Confidence into every request. Semantic needs legitimate reference context. Confidence measures judgment agreement, not factual truth or independent corroboration. Semantic's neutral History reputation means its singleton branch can remain uncertain.
- **Frozen identities/resources:** resource/configuration identity `7dc5ab6098f803133284f413ad577970073c99f12fb020c6b4a2dc75b9642ffb`; fitted contract, history/reputation, costs, execution semantics, resource manifest, and policy are content-bound. The recorded Reference service is Ollama 0.40.14 with model `llama3.2:3b` and digest `sha256:a80c4f17acd55265feec403c7aef86be0c25983ab279d83f3bcd3abbcb5b8b72`; the associated evidence resource record also binds the corpus/index/receipt, embedding/NLI resources, implementation, prompt, and adapter settings.
- **Evidence source:** `artifacts/remaining-category-studies-v1/reference-50-v1/fit/`, `evaluation/`, and `publication-identities.json`; package registration in `reconciliation/policies.json`; scope and compatibility details in `docs/compound_reference_fitting_verification_20261105.md` and `docs/policy-resource-compatibility-diff.md`.

The 50% clean-Development coverage floor is a separately versioned, post-Development amendment for this Reference study. The original 90% target was recorded as infeasible. Neither threshold is a general Reference policy guarantee or a target for another benchmark.

### Compound package/policy

- **Package registration:** the Compound entry is the `compound_policy` in `reconciliation/policies.json`, under the same bundle ID above. It is a component policy rather than a `PolicyArtifact` with a separate artifact ID.
- **Policy:** `0192b98e50ab5dcbd40ca78a0d4a3ec3978dfe8086edcb615802c21024c83532`.
- **Contract:** `0b93b2782afbf1da65be0064dd7a0218f6e347abda1568f2da3d15daa1fbf3e6`.
- **Matrix:** `bd4918e38503ec6ab990c83d687c1bc648015823a5ca2fa9ad18473421ab9970`.
- **Task scope:** source-backed V2 numeric fact-plus-addition with two required obligations: a factual `base_fact` and a `derived_sum` calculation from the submitted base and question increment. A source-backed catalog, versioned question grammar/signature, bound answer, costs/budget, and component contract jointly constrain the route.
- **Verifier/team:** the frozen component assignment is exactly Evidence for `base_fact` and Rule for `derived_sum`. The component contract requires the complete ordered obligations and a common aggregation semantics; the acceptance rule requires all required components to pass, permits a qualified component rejection to reject, and leaves incomplete/abstaining/unresolved obligations uncertain. This is not a generic verifier subset or an empirically demonstrated strategic team-selection advantage.
- **Answer binding:** the answer is a string containing JSON with exactly `base` and `derived` fields, both bounded plain decimal strings. The factual question is formed from the submitted `base`; the arithmetic check tests `derived` against that same submitted base plus the question increment. The runtime does not substitute a gold fact or silently repair malformed answers.
- **Frozen identities/resources:** the study package records actual resource identity `e23c6f034a4c660d30433d133be3a197db620abbdf22a78907ef5e3687d45ccb`; scoped E/R execution uses resource/configuration scope `310364dae8d9d6c001622d4bbe1866ca0646fb8f50c9c50a022e05f5353688c1`. The bound Evidence and Rule implementations/configurations and Evidence corpus, index, embedding, and NLI resources must match. Compound scoped E/R has no Ollama dependency.
- **Evidence source:** `artifacts/remaining-category-studies-v1/compound-85/candidate/policy.json`, its `contract.json`, `matrix.json`, and `amendment.json`; the package registration; and `docs/compound_reference_fitting_verification_20261105.md`.

The retained Compound policy uses a post-Development 85% clean-coverage amendment. The source report records the original 90% target as infeasible. This floor is specific to that fit. Keep its provenance separate from `artifacts/compound-study-36-v1/completion-report.md`, which describes the original 36-group run as infeasible with no policy exported, and from `artifacts/compound-empirical-v2/completion-report.md`, which says that separate producer's required empirical study was blocked before collection and exported no Compound policy. The frozen package policy is present and separately identified; those other completion records must not be represented as its policy-generation record.

Other atomic artifacts in the same package (including Rule/Evidence and the Reference artifact) have their own task/context signatures, history, costs, and resource bindings. Their presence does not broaden the Reference or Compound applicability described above.

## 3. Question and route applicability

The package's `allowed_questions` contains **69 exact question strings**: 30 Reference paraphrase prompts, 36 valid area/population fact-plus-addition prompts, one area/population-shaped multiplication prompt retained as an unsupported negative case, one standalone population fact, and one arithmetic question. Separately, the embedded Compound catalog contains 38 entity/measure descriptors. Therefore, allowlist membership alone does not imply that a string is a valid Compound component route. The relevant literal strings are the `allowed_questions` array in `reconciliation/policies.json`.

The current Compound route additionally requires all of the following:

1. Exact membership in the package allowlist.
2. Match of the finite V2 grammar in `app/game/component_sources.py`: `What is the <area|population> of <catalog entity>, and what is that same measure plus <bounded decimal>[ square kilometres]? Give both values.`
3. A unique matching entity/measure descriptor in the embedded `source_backed_component_catalog_v2` catalog (38 descriptors in the package).
4. Correct units for the measure, matching route signature/budget, valid structured answer binding, and a compatible registered component policy.

The current Reference route requires exact allowlist membership, the registered Reference question format/version, a unique atomic task signature and budget, and the required reference context. The route's analyzer uses the Reference paraphrase framing; a semantically similar but non-allowlisted string is outside this package route.

The single standalone factual question and arithmetic question in the bundle exercise their separate atomic routes; they do not enlarge Compound into arbitrary facts or arithmetic, or Reference into general comparison. The prototype bundle loader in `app/game/prototype_bundle.py` is another explicit package path with its own declared arithmetic/factual tasks, question IDs, and unsupported semantic-comparison task; it does not relax the flexible package restrictions.

When no unique route/policy exists, a question is outside the allowlist, the category is unsupported, or the route cannot validate its policy/binding/resources, the runtime fails closed with an unavailable/uncertain result and a route/selection reason. It does not silently fall back to another task's artifact. Route, question signature, and budget are part of applicability because the policy was fitted and validated for those exact conditions.

## 4. Verifier and team applicability

**Reference** requires the configured Semantic verifier and, on the pair branch, Confidence. Its strategy probabilities and frozen reputation snapshot are part of the policy. Semantic comparison needs the legitimate reference text; Semantic similarity is not factual correctness. Confidence's judgment agreement is not itself evidence or an independent source. A selected verifier name is not necessarily an informative contributor; finalization may keep the public result uncertain if contributor or coverage obligations are not met.

**Compound** binds Evidence to the factual component and Rule to the arithmetic component. `ComponentContract.component_assignments` fixes those identities; V2 rejects a different assignment. Component inputs, report identities, binding IDs, ordered execution states, common aggregation semantics, cost budget, and the exact contract are validated. Both checks are necessary for a complete Compound decision. Replacing Evidence, routing the sum to a different verifier, flattening the two reports into a generic vote, or treating a single passed component as a complete answer changes the policy contract.

The component contract specifies `all_required_pass_any_qualified_reject_v1`, informative contributor semantics, resource-bound component contracts, and a minimum distinct influential contributor count. Actual finalization also respects the bound coverage/decision semantics and treats abstention, unavailable/failed execution, missing coverage, or insufficient contributors as uncertainty where required. Exact behavior is versioned in `app/game/component_execution.py`, `app/game/finalization.py`, and `app/game/execution_contract.py`.

## 5. Resource and configuration applicability

### Portable artifact requirements

`ResourceManifest` records verifier implementation and configuration fingerprints and required model, corpus, index, prompt, or service identities. The policy/context/contract bind the resource and execution configuration identities. Runtime construction validates those frozen identities and snapshots the actual selected verifier instances before dispatch; incompatible observations fail closed. Route-specific relocations require separate explicit binding settings and an accepted proof. A relocation proof does not authorize unrelated model, corpus, index, receipt, service, implementation, or semantic-setting changes.

The Reference resource record binds Semantic's embedding model and Evidence's corpus/index/embedding/NLI path as well as Confidence's prompt, model and service identities. Its required Ollama server version is 0.40.14; the recorded compatibility diagnosis says 0.40.11 is not compatible even with the same model digest. Compound E/R uses only its bound Evidence and Rule scope, including the Evidence model/corpus/index resources, and does not require Ollama.

### Machine-local evidence and unresolved activation

Saved adapter configuration, model directories, current service observations, physical indexes, and preflight results are machine-local observations. `adapter.json` and historical records include machine-specific resource path information; this document intentionally does not reproduce those paths. Their presence does not mean the current host still has matching bytes or a running compatible service.

The package-level source/provenance records and resource hashes are portable identity requirements. They are not independent proof that an adapter's claim is true or that a different host satisfies it. The later recorded package verification reports Reference construction/binding with zero calls, zero Compound attempts in its failed local attempt, and no active API acceptance. Same-process target configuration, actual selected verifier instance attestation, compatible resources, and bounded live API acceptance remain unestablished by that package verification.

## 6. Existing evidence of applicability

| Policy/package | Evidence type | Source/path | What it proves | What it does not prove |
|---|---|---|---|---|
| Reference | Package/fitting/provenance evidence | `artifacts/remaining-category-studies-v1/reference-50-v1/fit/policy.json`; `artifacts/remaining-category-studies-v1/reference-50-v1/fit/contract.json`; `artifacts/remaining-category-studies-v1/reference-50-v1/fit/summary.json`; `artifacts/remaining-category-studies-v1/reference-50-v1/amendment.json`; `artifacts/remaining-category-studies-v1/reference-50-v1/publication-identities.json` | A frozen fitted policy, matrix, contract, task/reputation/resource identity, and explicit post-Development 50% coverage amendment exist. | General Reference applicability, a new benchmark fit, or live service/API activation. |
| Reference | Recorded replay/frozen evaluation | `artifacts/remaining-category-studies-v1/reference-50-v1/evaluation/results.json`; `artifacts/remaining-category-studies-v1/reference-50-v1/selection-replay/reference-routing.json`; `docs/compound_reference_fitting_verification_20261105.md` | The retained Reference study has a frozen reserved evaluation and replayed fitted singleton/pair selection on recorded reports. | New live verifier calls, independent corroboration, population guarantee, or current-host compatibility. |
| Reference | Controlled-dependency integration | `tests/test_flexible_runtime_dispatch.py`; `tests/test_reconciliation_execution.py`; `tests/test_reference_50.py` | Controlled routing/compatibility and Reference fitted-policy contract behavior are exercised in tests. | Native model/service execution or current deployment readiness. Tests were not run for this documentation task. |
| Reference | Package/fitting/provenance evidence | `reconciliation/local-acceptance-summary.json`; `docs/compound_reference_verification_20261105.json` | A later local check constructed Reference instances and bound/compared before/after resource proofs with zero verifier attempts and zero generations. | It is construction/binding evidence, not a live Reference verifier acceptance or API request. Historical Reference research calls are study data, not current API acceptance. |
| Compound | Package/fitting/provenance evidence | `artifacts/remaining-category-studies-v1/compound-85/candidate/policy.json`; `artifacts/remaining-category-studies-v1/compound-85/candidate/contract.json`; `artifacts/remaining-category-studies-v1/compound-85/candidate/matrix.json`; `artifacts/remaining-category-studies-v1/compound-85/amendment.json`; `docs/compound_reference_fitting_verification_20261105.md` | The distinct 85%-amended empirical ComponentPolicy, matrix, team assignments, resource identities, and fitting provenance exist. | That the separate `compound-study-36-v1` or `compound-empirical-v2` completion report generated this package policy, or that the policy applies beyond its bound category/resources. |
| Compound | Recorded replay/frozen evaluation | `artifacts/compound-study-36-v1/acceptance-replay/routing.json`; `artifacts/remaining-category-studies-v1/publication-acceptance/routing.json`; `docs/compound_reference_fitting_verification_20261105.md` | Retained reports exercise the frozen Evidence-for-fact/Rule-for-sum component route and recorded Development/reserved results within the declared scope. | New native calls, active API acceptance, a future held-out benchmark result, or a strategic team-selection advantage beyond the fixed assigned pair. |
| Compound | Controlled-dependency integration | `tests/test_component_execution.py`; `tests/test_flexible_runtime_dispatch.py`; `tests/test_reconciliation_execution.py` | Controlled tests cover exact answer binding, component report/binding identities, success/rejection/uncertainty, missing policy, and resource mismatch behavior. | Native verifier quality, live resource compatibility, or general question coverage. Tests were not run for this documentation task. |
| Compound | Native live acceptance | `docs/compound_reference_fitting_verification_20261105.md`; `reconciliation/local-acceptance-summary.json` | The report records earlier bounded local direct Compound acceptance with four native component calls; a later local package attempt records zero calls after a selector-construction error and no retry. | Integrated teammate API acceptance, current-host readiness, or a repeated acceptance after that later failure. |
| Both | Package/fitting/provenance evidence | `reconciliation/policies.json`; `scripts/policy_package.py`; `app/game/deployment.py` | Bundle digest, exact allowlist, policy contract validation, and explicit runtime package-path restrictions are implemented. | Successful runtime activation on any unspecified host. |

Evidence chronology matters. The later package verification states zero new native calls/generations and `live_activation_proven: false`; it does not erase older study collections or the earlier bounded direct Compound acceptance, but neither older evidence upgrades the later package check to current API acceptance.

## 7. Current applicability boundary

**Reference:** This package is currently evidenced as applicable only when the request is one of its exact allowlisted Reference paraphrase strings, the Reference analyzer/version and task signature select the registered frozen Reference artifact uniquely, legitimate matching Reference text is present in `context`, the fitted Semantic or Semantic+Confidence team is executed with the bound reputation/aggregation/coverage contract, and required model/service/corpus/index/implementation identities pass the applicable resource checks.

**Compound:** This package is currently evidenced as applicable only when the request is one of the allowlisted valid fact-plus-addition questions, its measure/entity/units satisfy the package's finite V2 source-backed catalog and question signature, the answer has exactly the bound decimal-string `base` and `derived` fields, the registered policy binds Evidence to `base_fact` and Rule to `derived_sum`, costs/budget and finalization satisfy the frozen contract, and required E/R resource identities pass compatibility checks.

**For both:** This evidence does not establish applicability to arbitrary new questions or a future benchmark unless the new benchmark's scope and data are declared, its policies are fitted/justified for that scope, routes and answer binding match, verifier and resource identities are compatible, and benchmark-specific evaluation and acceptance evidence are produced. Exact package membership is necessary for the current allowlisted routes but does not alone prove policy suitability or host readiness.

## 8. Why removing an allowlist is insufficient

The allowlist is only one route gate. `QuestionPolicyConfiguration` still classifies the question, derives a signature, resolves a unique registered route and budget, validates the artifact/component contract, and checks resource compatibility. The Compound V2 parser only accepts a finite source-backed fact-plus-addition grammar and catalog; the answer binder enforces typed decimal-string fields and component dependencies. Reference relies on a particular paraphrase analyzer/version, legitimate reference context, and fitted task signature. Removing the allowlist would not change any of these conditions.

It would also not create training evidence for a new question population. The fitted distributions depend on their History and Development records, reputation snapshots, costs, losses, attack assumptions, coverage amendments, verifier teams, and task/resource bindings. `PolicyArtifact` validates the policy against the exact context, feasible strategy set, contract, and execution configuration; `ComponentPolicy` validates its component obligations and source/resource contract. A new population or task semantics can therefore require a different compatible policy, not broader string matching.

Nor would allowlist removal make verifiers available, reconcile model/service/corpus/index changes, satisfy contributor or achieved-coverage guards, or supply final-test protocol and matched baselines. These each have separate contracts and evidence. The package explicitly fails closed on missing routes and incompatible resources; bypassing the allowlist would only bypass a restriction without establishing those other requirements.

## 9. Future benchmark applicability requirements

### Depends on Person 1

- Define the final dataset and scientific benchmark scope.
- Define question groups/categories and the exact candidate-answer setup, including Compound answer representation if that task remains in scope.
- Decide History, Development, and final-test split assignments, group leakage controls, and final-test custody.
- Decide the evidence corpus/index inputs and their provenance/resource identity, including whether Reference context and factual Evidence retrieval are part of the benchmark.

These choices establish the target population and question/resource applicability against which policies must be assessed.

### Depends on Person 3

- Supply compatible experimental policies for Person 1's finalized scope and resource/configuration identities.
- Fit policies using the declared History/Development roles and the accepted objectives/contracts; preserve policy identity, bindings, and fitting provenance.
- Define and execute matched baselines on the same scope and compatible execution assumptions.
- Complete the required policy evaluation/finalization under the predeclared protocol before final-test outcomes are used to make claims.

### Can be prepared independently now

- Maintain the applicability contract/checklist below and the code-level schema/route map.
- Keep current-package, replay, native, and controlled-test evidence explicitly separated and preserve existing IDs/provenance.
- Prepare documentation for how route, resource, policy, and execution-contract identities will be recorded and reviewed once Person 1 and Person 3 inputs arrive.

## 10. Explicit applicability contract

Do not mark a policy applicable to a benchmark until the following record is complete and reviewed:

| Applicability field | Required declaration/evidence | Dependency/status |
|---|---|---|
| Supported question/task scope | Exact task categories, parser/analyzer version, route conditions, explicit allowlist or equivalent boundary, unsupported cases. | **Pending Person 1** benchmark scope and groups; current package values are package-specific. |
| Verifier/team identity | Verifier implementations, selected team or distribution, component bindings, output/aggregation/finalization contract, contributor and failure rules. | Person 3 supplies compatible experimental policy; runtime owners record actual execution identity. |
| Policy identity/version | Policy, matrix, contract, artifact/package digest, fitted probabilities, feasible strategy definitions. | **Pending Person 3** final-benchmark policies; current identities are historical package evidence. |
| Resource identities | Implementation/configuration/model/prompt/service/corpus/index/receipt fingerprints as applicable; actual selected instances observed. | Person 1 decides corpus/index scope; integration preflight/attestation remains required on target host. |
| Model/service configuration | Exact required model/service identity and compatible sampling/prompt settings where used; no secrets. | Person 3 policy binding plus target resource/service attestation. |
| Compatibility/attestation | Successful exact policy-context-contract validation, route resolution, budget check, resource proof, and before/after observation where required. | Must be produced for the final target; repository schemas alone are insufficient. |
| Coverage/decision contract | Required task outputs, minimum coverage/contributor behavior, acceptance/rejection/uncertainty and failure rules. | **Pending Person 1** task obligations and Person 3 compatible fitted contract. |
| Fitting/evaluation population | Dataset/group identity, independent labels, History/Development provenance, costs/losses, policy-fitting record, final evaluation evidence. | **Person 1:** dataset/groups/splits. **Person 3:** policy fit and evaluation. |
| Benchmark split/protocol relationship | Matched methods, split custody, no leakage, fixed analysis/acceptance plan, and how final-test outcomes are reserved/used. | **Pending Person 1** split/protocol inputs and Person 3 matched-baseline/evaluation work. |

The contract should cite immutable IDs and exact repository records, but hashes establish byte identity only; they do not authenticate labels, resource observations, or benchmark representativeness.

## 11. Evidence inventory

| Evidence | Type | Repository/artifact source | Applicability established | Limitation |
|---|---|---|---|---|
| Flexible package digest, allowlist, and loader | Package/fitting/provenance evidence | `reconciliation/policies.json`; `scripts/policy_package.py`; `app/game/deployment.py` | Which frozen artifact/component registrations and exact allowed question strings make up this package. | Package existence/validation is not activation or a general applicability claim. |
| Reference fitted policy and contract | Package/fitting/provenance evidence | `artifacts/remaining-category-studies-v1/reference-50-v1/fit/policy.json`; `fit/contract.json`; `fit/summary.json`; `publication-identities.json` | Frozen Reference task, strategy distribution, matrix, context, and resource identities. | Post-Development study-specific 50% coverage floor; no automatic transfer to new data. |
| Reference reserved evaluation and team replay | Recorded replay/frozen evaluation | `artifacts/remaining-category-studies-v1/reference-50-v1/evaluation/results.json`; `selection-replay/reference-routing.json`; `publication-results.json` | Recorded retained-run outcomes and sampled team replay against the package's study evidence. | Historical, bounded sample; not current live/API acceptance or population validity. |
| Compound fitted ComponentPolicy and amended contract | Package/fitting/provenance evidence | `artifacts/remaining-category-studies-v1/compound-85/candidate/policy.json`; `artifacts/remaining-category-studies-v1/compound-85/candidate/contract.json`; `artifacts/remaining-category-studies-v1/compound-85/candidate/matrix.json`; `artifacts/remaining-category-studies-v1/compound-85/amendment.json` | Frozen component assignment, IDs, resource binding, and the 85% post-Development fit amendment. | Separate from the infeasible original 36-group completion and blocked `compound-empirical-v2` producer. |
| Compound retained report execution | Recorded replay/frozen evaluation | `artifacts/compound-study-36-v1/acceptance-replay/routing.json`; `artifacts/remaining-category-studies-v1/publication-acceptance/routing.json`; `artifacts/compound-empirical-v2/routing.json` | Selected routes, component binding/finalization behavior, and retained reports for the cases each artifact records. | Some replay records are Development-only or no-live-call; see each record's partition/limitation fields. |
| Route, answer binding, policy compatibility | Focused unit/contract test | `tests/test_component_execution.py`; `tests/test_flexible_runtime_dispatch.py`; `tests/test_reconciliation_execution.py`; `tests/test_reference_50.py` | Code contracts for finite routing, bindings, policy/team integrity, missing/incompatible paths, and fitted Reference amendment. | Does not establish native verifier behavior; no tests were run for this document. |
| Earlier bounded Compound direct acceptance and later local check | Native live acceptance | `docs/compound_reference_fitting_verification_20261105.md`; `reconciliation/local-acceptance-summary.json` | Historical local direct Compound case used four native component calls; later package attempt failed before calls and was not retried. | Neither proves integrated teammate API acceptance or current-host compatibility. |
| Reference resource compatibility requirements | Package/fitting/provenance evidence | `docs/policy-resource-compatibility-diff.md`; `docs/game_policy_compatibility_diagnosis.md`; `docs/game_resource_relocation.md`; `artifacts/remaining-category-studies-v1/reference-50-v1/service-observation.json` | Required service, model, corpus/index, implementation, adapter, and restricted relocation identities. | Saved observations are host/time-specific; current target activation is unresolved. |
| Later package verification acceptance boundary | Recorded replay/frozen evaluation | `docs/compound_reference_verification_20261105.json`; `reconciliation/local-acceptance-summary.json`; `artifacts/remaining-category-studies-v1/publication-acceptance/routing.json` | Retained verification distinguished route/replay/construction from live acceptance and recorded zero new calls in the later audit. | Does not prove native API execution; it explicitly reports no active API proof. |
