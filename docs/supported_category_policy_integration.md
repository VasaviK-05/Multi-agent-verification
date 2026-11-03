# Owned verifier-team prototype: integration handoff

Branch: `codex/flexible-verifier-teams`. Implementation base: `0b3595ef965d196f93916d10999c7fae63daf7af`. Publication content commit and GitHub links are recorded in the publication record accompanying this handoff. No merge into main or deployment activation is performed. API, frontend, DB and answer generation are their owners’ work.

## Available policies and final reference result

Arithmetic selects Rule alone; factual selects Evidence alone. Their completed reserved results remain frozen. Compound selects Evidence+Rule and retains 45/48 reserved decisions, zero errors and three uncertainties. Its 85% development floor was explicitly selected after development; the original 90% infeasibility result is preserved. Compound equals its matching fixed plan under every simulated attack.

Reference now has a separately versioned experimental 50% clean-development coverage configuration, chosen **after observing 60% development coverage**. The original 90% infeasibility files remain unchanged. Reconstructed history/development reports, contracts, costs, source evaluation and payoffs exactly match that original run; only the fitting coverage constraint changes. 50% is neither acceptance rate nor accuracy and does not improve verifier quality.

The fitted reference mix is **Semantic alone 1/6; Semantic+Confidence 5/6**, both reputation-weighted. These probabilities come from the certified optimizer; neither Confidence use nor a pair was forced. Semantic’s neutral Beta(11,11) history makes its singleton branch uncertain. The mix deliberately trades clean coverage against the declared report-corruption objective. Development clean coverage is 50%, decision loss 0.10; the fixed pair has 60% coverage and loss 0.08. The mix’s worst development validation loss is 0.391667 versus 0.43 for the fixed pair. This mathematical abstention trade-off is not broad superiority or independent corroboration.

The [identities](../artifacts/remaining-category-studies-v1/reference-50-v1/publication-identities.json), [policy artifact](../artifacts/remaining-category-studies-v1/reference-50-v1/fit/policy.json), [contract](../artifacts/remaining-category-studies-v1/reference-50-v1/fit/contract.json), [matrix](../artifacts/remaining-category-studies-v1/reference-50-v1/fit/matrix.json), [amendment](../artifacts/remaining-category-studies-v1/reference-50-v1/amendment.json), [freeze](../artifacts/publication-v1/public-audit/artifacts/remaining-category-studies-v1/reference-50-v1/fit/freeze.json) and [reserved results](../artifacts/remaining-category-studies-v1/reference-50-v1/evaluation/results.json) provide exact provenance. The [report-label clarification](../artifacts/remaining-category-studies-v1/reference-50-v1/fit-report-note.json) corrects an inherited summary flag without changing policy or outcomes.

## Reserved evaluation

Exactly 20 reserved answers in 10 groups were collected once: 80 native verifier calls and 100 local Confidence generation requests. Cumulative reference accounting is **255 starts, 254 completed native calls and 372 generation starts**, including all interrupted/discarded/replacement work. One original outcome/duration remains unknown. No additional retry, refit, threshold change or reputation update followed reserved outcomes.

| Method | Coverage | Expected correct accepts | Expected correct rejects | False accepts | False rejects | Uncertain | Selective risk | Decision loss |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| policy | 66.67% | 8.333 | 5 | 0 | 0 | 6.667 | 0.0 | 0.066667 |
| development_best_fixed | 80.00% | 10 | 6 | 0 | 0 | 4 | 0.0 | 0.040000 |
| coverage_aware_greedy | 80.00% | 10 | 6 | 0 | 0 | 4 | 0.0 | 0.040000 |

Policy counts above are expectations over the frozen mixed strategy and may be fractional; fixed/greedy counts are ordinary counts. They are not native full-roster collection counts. The [seeded actual router replay](../artifacts/remaining-category-studies-v1/reference-50-v1/selection-replay/reference-routing.json) selected teams with counts `{"confidence,semantic": 18, "semantic": 2}` using persistent seed1103. This is retained-report replay, not new inference or API activation. Its supplementary selection-audit specification was recorded before inspecting reserved reports; primary policy metrics integrate the frozen probabilities.

Reference report-level attack decision losses: `{"coverage_aware_greedy": {"clean": 0.04, "confidence_inflation": 0.04, "forced_rejection": 0.54, "forced_support": 0.33999999999999997, "suppression": 0.2}, "development_best_fixed": {"clean": 0.04, "confidence_inflation": 0.04, "forced_rejection": 0.54, "forced_support": 0.33999999999999997, "suppression": 0.2}, "policy": {"clean": 0.06666666666666664, "confidence_inflation": 0.06666666666666664, "forced_rejection": 0.4833333333333332, "forced_support": 0.31666666666666665, "suppression": 0.19999999999999998}}`. Attacks can corrupt all names in one shared failure group. They are simulated report corruption, not observed upstream compromises.

Group-respecting 95% percentile intervals: `{"coverage_aware_greedy": {"coverage": {"interval95": [0.65, 0.95], "undefined_fraction": 0.0}, "decision_loss": {"interval95": [0.01, 0.07], "undefined_fraction": 0.0}, "selective_risk": {"interval95": [0.0, 0.0], "undefined_fraction": 0.0}}, "development_best_fixed": {"coverage": {"interval95": [0.65, 0.95], "undefined_fraction": 0.0}, "decision_loss": {"interval95": [0.01, 0.07], "undefined_fraction": 0.0}, "selective_risk": {"interval95": [0.0, 0.0], "undefined_fraction": 0.0}}, "policy": {"coverage": {"interval95": [0.5416666666666667, 0.7916666666666669], "undefined_fraction": 0.0}, "decision_loss": {"interval95": [0.04166666666666663, 0.09166666666666666], "undefined_fraction": 0.0}, "selective_risk": {"interval95": [0.0, 0.0], "undefined_fraction": 0.0}}}`. Resampling keeps both variants together: 10 groups, 1000 replicates, seed1103. Small-sample or zero-error intervals do not prove population safety.

Measured reserved call times (ms): `{"confidence": {"count": 20, "mean": 17903.41090999991}, "evidence": {"count": 20, "mean": 54.540149999957066}, "rule": {"count": 20, "mean": 0.1396749999912572}, "semantic": {"count": 20, "mean": 60.484205000147995}}`. These per-verifier timers exclude initialization/resource-observation overhead and are not end-to-end API latency or prices. Test timings do not recalibrate the frozen history/development budget.

## Compound answer contract and ownership

`ValidationRequest.answer` is **a string**, not a typed object. It carries serialized JSON text with exactly two plain decimal-string fields, `base` and `derived`. The proposed answer comes from the user or generation system. Verifiers consume component inputs and return reports; they do not produce, repair or normalize that submitted structure.

The adapter derives the factual check from submitted `base`, and checks submitted `derived` against that same base plus the question increment. No gold value is substituted. Prose, malformed JSON, duplicate/missing/extra fields, JSON numeric values and unsupported decimal forms trigger `answer_binding` errors, not factual rejection. Generation/integration owners must produce and validate the schema before verification; no LLM parser or silent correction is added.

Runnable direct-router example, using actual retained development reports and zero inference:

```text
python -m scripts.direct_router_example
```

The [example source](../scripts/direct_router_example.py) constructs `ValidationRequest`, injects server-owned registry/provider/RNG/observer, and calls `configuration.router().run(...)`. Expected result: Evidence+Rule, two calls, passed, early stopping disabled. For live execution the API owner must supply approved native instances and trusted compatible observation; replay is not live readiness.

Proposed HTTP request for the API owner — **intended contract after owned-router wiring, not a claim the existing endpoint implements compound routing**:

```http
POST /validate
Content-Type: application/json

{
  "question": "What is the population of Cameroon, and what is that population plus 1000? Give both values.",
  "answer": "{\"base\":\"29879337\",\"derived\":\"29880337\"}",
  "context": null
}
```

The escaped inner JSON is deliberate. Sending an object in `answer` does not match the current Pydantic string field. API schemas, routes, generation, frontend and DB components were not changed.

## Setup, resources and reproducibility

Use the repository baseline and its existing Python dependencies. Exact executed versions, resource fingerprints and service metadata are in the [current inspection](../artifacts/remaining-category-studies-v1/reference-current-v1/inspection.json). Models/index/service are external; see the [third-party/source notices](THIRD_PARTY_NOTICES.md) and pinned [resource inventory](../artifacts/compound-study-36-v1/external-resources.json). No model/corpus/index downloads or rebuilds were performed. This is not a self-contained live deployment.

Reference uses the verified current Ollama 0.40.14/model digest and unchanged prompts, five-sample/.8 settings, local NLI/embedding resources, corpus/index and implementations. Old 0.40.5 identity remains historical, not equivalent. The [transition record](../artifacts/remaining-category-studies-v1/reference-current-v1/amendment.json) links 45 exactly resource-equivalent non-Confidence reports; 14 old Confidence reports are audit-only. 40 compatible Confidence reports enter training, and 20 new ones belong only to reserved evaluation.

The publication is public. Canonical audit originals containing personal local path prefixes remain local and unchanged. Separate redacted public views disclose original/public hashes and identity effects in [owned-files.json](../artifacts/publication-v1/owned-files.json). Those views are not canonical whole-freeze inputs. Deployable policy/context/matrix bytes and certificates are unchanged and portable. To verify an original whole-freeze/source audit, obtain its exact canonical original from the custodian by relative filename and SHA-256; do not substitute a redacted view or rewrite expected resource hashes.

Final offline verification and acceptance:

```text
python -m scripts.verify_publication
python -m scripts.replay_remaining_policies --output <fresh-output>
python -m scripts.direct_router_example
python -m pytest tests/test_reference_50.py tests/test_component_execution.py tests/test_reference_transition.py tests/test_scoped_er_adapter.py tests/test_reference_study.py tests/test_heldout_collection.py tests/test_flexible_teams.py -q
```

Expected: typed certificates/allowlists validate; singleton and pair routing succeeds; reference samples its fitted singleton/pair mix; unknown/missing/incompatible routes fail explicitly; no real triple or live API readiness is claimed. API-owner active-instance/relocation acceptance remains separate from report replay.

## Policies, routing and execution

The [identity index](../artifacts/remaining-category-studies-v1/reference-50-v1/publication-identities.json)
reports actual policy, matrix, context, contract-content, resource and setup IDs.
The reference entry is experimental, fitted under a post-development 50% floor, and evaluated once without refitting.

The minimal [policy bundle](../artifacts/remaining-category-studies-v1/prototype-policy-package-v1/policies.json) contains available typed atomic/component artifacts and explicit question allowlist. Exact policy/context/matrix/resource IDs and selection evidence are in the [acceptance replay](../artifacts/remaining-category-studies-v1/current-acceptance/routing.json). No fitted policy selects a triple. Synthetic fixtures do not count.

Question-only analyzer → task/domain/requirements/reference/difficulty signature → explicit category/budget registry → compatible frozen policy → strategy sampling → all selected calls → public finalizer. Within one signature/budget the distribution is shared; random sampling within it is not extra question adaptation. Reference uses opt-in `bounded_reference_frames_v1`, constant easy/.1 score; it does not claim measured easy/hard adaptation. Missing/unsupported/incompatible policies fail closed, without answer-correctness or verifier-output categories.

Selected names, attempted calls, achieved capabilities and informative contributors are distinct audit fields. Complete-team game execution disables early stopping and preserves failed/abstaining results. Repeated verifier use on different components counts every call, not just distinct names. Frozen training cost estimates never use test timing. Individual verifier timers exclude initialization and resource attestation and are not end-to-end API latency or monetary prices.

## Supported inputs and portable examples

Atomic scope remains the original narrow addition/pinned factual cohorts. Compound supports exact study allowlist questions of the form `What is the area of <catalog entity>, and what is that area plus <decimal> square kilometres? Give both values.` or the corresponding population template. Other operations, arbitrary prose and unknown categories are unsupported. Reference questions are the30 exact `Paraphrase this reference: <fixed text>` frames with that legitimate text as context. Source catalogs/allowlists do not authorize arbitrary API expansion.

Compound answer format: `{"base":"765","derived":"775"}` — exactly two decimal strings. Duplicate/missing/extra fields and JSON numeric values fail binding. Evidence sees the submitted base fact; Rule checks the submitted base plus increment against derived. No gold base is substituted. All component passes accept; any qualified component failure rejects; otherwise uncertain.

```python
from scripts.policy_package import load
configuration, provider, compound = load("artifacts/remaining-category-studies-v1/prototype-policy-package-v1/policies.json")
router = configuration.router()
# router.run(selector, request, validation_id, provider=provider,
#            rng=server_rng, resource_observer=trusted_observer)
```

The bundle loader reads repository-relative artifact bytes only, without dereferencing model caches, original private source paths, DB or services. Historical absolute-path strings remain provenance. Request exposes question/answer/context; registry, RNG, budgets and observers belong to the server. No request-supplied policy ID chooses a policy.

```text
python -m scripts.replay_remaining_policies --output <fresh-replay-directory>
python -m pytest tests/test_reference_transition.py tests/test_reference_study.py tests/test_scoped_er_adapter.py -q
```

Replay uses real frozen policies and retained compatible reports; it is not fresh inference or live API activation. Actual native reference collection is separately journalled. Do not claim all categories share one live installation: completed atomic policies bind their original full resource identity.

## Scoped compound resources and ownership

The [scoped E/R adapter](../scripts/scoped_er_adapter.py), [transfer](../artifacts/remaining-category-studies-v1/scoped-er-v1/transfer.json), [reserved results](../artifacts/remaining-category-studies-v1/scoped-er-v1/reserved-results.json) and [cluster intervals](../artifacts/remaining-category-studies-v1/scoped-er-v1/uncertainty-supplement.json) retain completed compound evidence. E/R projection ID is `310364dae8d9d6c001622d4bbe1866ca0646fb8f50c9c50a022e05f5353688c1`. Evidence uses local regex/template ClaimGenerator, embeddings, corpus/index retrieval and NLI; Rule is local. Scoped execution constructs neither Confidence nor Ollama and forbids network. Actual 96 calls/0 generations completed without service dependence.

The original full-manifest runtime still rejects scoped observations without a proof-aware integration. Scoped observer `snapshot_for(selector)` checks selected native-instance identity; required resource drift is rejected pre/post. Native full-roster observer verifies files/service but its collection factory provenance is not a generic API active-instance attestation. API owner must bind the actual installed selected objects and implement a narrowly verified relocation proof, without changing expected historical hashes. The separate resource-relocation work remains unmerged.

API/backend owner: install explicit registry/provider and proof-aware observer, retain scope guards, validate structured requests, expose explicit unsupported/missing-policy/answer-binding/provenance failures, and preserve policy/strategy/context/resource IDs, selected/attempted names, informative contributors, achieved/unresolved coverage, per-call states, component reasons, final verdict and early-stopping-disabled fields. Frontend owner: render schema, components, uncertainty and failures. DB owner: persist audit identities and states without updating frozen reputation from test. Verifier owners: own algorithm/output-contract changes, separately validated; none were edited here. Those implementation and activation tasks are outside owned offline completion.

## Resources, attacks and publication

Exact dependency versions are in current inspection/setup. External model/file inventories are in [external-resources.json](../artifacts/compound-study-36-v1/external-resources.json): embedding all-MiniLM-L6-v2 revision1110a243fdf4706b3f48f1d95db1a4f5529b4d41; NLI nli-deberta-v3-small revisionfa2804872c3b4bd748f38c0185cc85775361e735. Validate every file SHA-256/size and canonical directory digest, corpus/index/build receipt and actual service metadata. Mutable aliases are insufficient. No downloads, corpus expansion/index rebuild or global service modification occurred.

Shared embeddings connect Evidence/Semantic and shared NLI connects Evidence/Confidence; unresolved risks place all names in one shared-unknown failure group. Report-corruption attacks can corrupt all selected names together. Different names are not independent failure paths. Attack results are simulated report corruption, not measured upstream compromise. Small grouped percentile intervals and zero observed errors do not establish population safety.

The [supporting publication inventory](../artifacts/publication-v1/file-hashes.json) lists exact owned source/tests/docs/artifacts and hashes on the baseline. The minimal bundle is for loading; supporting journals/manifests/raw source notices are separate reproducibility evidence. Exclude model caches/weights, index directories, environments, Ollama installation, DB/user data, credentials and `compound-study-36-v1/local-custody/` original-source archive containing unrelated owner changes. Original local path strings require identity-disclosure review; never rewrite frozen artifacts to hide provenance. No API implementation or activation is required to review this owned package.
