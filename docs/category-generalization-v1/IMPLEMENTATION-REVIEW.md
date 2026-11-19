> **19 November 2026 update:** [engineering review v3](ENGINEERING-ACCEPTANCE-v3.md)
> supersedes prior implementation/testing blockers and the mandatory-new-fit
> interpretation. Compatible unseen instances now reuse the unchanged fitted
> policy through an opt-in scope; exact routes retain precedence. Confidence has
> a new game-only v5 consistency output contract. No new empirical certification,
> fitting or deployment occurred. Original findings below remain historical.

# Follow-up implementation review (2026-11-17)

This work remains **INCOMPLETE / NOT ACTIVATED / NOT CERTIFIED**. No native verifier
method, Ollama generation, fitting campaign, published-artifact mutation, merge,
API/frontend/database/generator/verifier edit or dependency installation occurred.

## Implemented and consumed

The previous `CategoryApplicability` is one generic v1 schema, not four separate
certificates. It declares artifact/task IDs, distribution/exclusions, reviewer,
three report digests, scenarios, evaluated teams and semantic challenge families.
`validate_artifact` validates exact PolicyArtifact identity, task binding and team
coverage; `configuration_from_category_artifacts` delegates to the old atomic
configuration helper. No prior deployment/runtime caller consumes it. Its free
text distribution is not an executable eligibility rule; its digests do not
verify reports. Calling that helper alone could register historical artifacts
without demonstrating broader scientific scope. It remains a low-level API and
is **not** the approved new runtime entry point.

New `category_runtime.py` provides:

* `CategoryInputContract` v2: bounded full-match question grammar, explicit
  requirement obligations, reference presence, answer contract and category
  planning profile. Candidate answers never choose the route; incorrect answers
  remain eligible. The contract hash enters the analyzer/task identity.
* `ReviewedCategory` v2 consumes the v1 declaration AND retained report bytes;
  validates SHA256, role, scope/artifact binding and distinct development/held-out
  dataset identities. Runtime construction also demands every exact policy
  strategy ID (team AND aggregation) in each report. These checks verify
  integrity/declarations, not reviewer authority, independence or accuracy.
* `CategoryGameRuntime` requires empirical, task-aware, resource-bound frozen
  artifacts fitted under the new input-contract identity. It uses the existing
  TaskPolicyRouter -> GameRuntime -> frozen planning -> minimax sampling ->
  complete-team native dispatch -> finalization path. It does not select a team
  by category, alter probabilities, weaken provenance or add fallback. Selector
  and actual-instance resource observer must be explicitly supplied by the owner.
* `ExactFirstCategoryDispatcher` preserves every request belonging to the legacy
  allowlist, verbatim, including failures. It never falls back from an existing
  exact route into a category route. Multiple matching categories/budgets fail
  closed; this initial version requires a unique installed profile per input.
* `category_deployment.create_category_game_runtime` wraps the actual bounded
  FlexiblePolicyGameRuntime in a subclass accepted by the unchanged orchestrator
  type guard. It captures the actual legacy configuration and instance; it does
  not reconstruct old RNGs, resources or factories. Other legacy runtime kinds
  are intentionally rejected until their exact-registration protection is defined.

There is no settings/env/HTTP-request activation path for these additions. No new
artifact/report/binding is installed. The default runtime remains unchanged.
Dependency-light schema imports were enabled by making the old declaration's
TaskSnapshotBinding import local to artifact validation; validation still runs.

## Static runtime traces

### `What is 4 + 4?`, candidate `8` or `9`

It is absent from the published 69-question allowlist. In the existing flexible
runtime `QuestionPolicyRouter.resolve` rejects it BEFORE classification, resource
construction, RNG or dispatch. PrototypeRouter likewise enforces declared exact
question IDs. The single-artifact GameRuntime path has no allowlist itself, but
that is not proof of certified category applicability and is not promoted here.

If classified independently by the existing CapabilityProbeAnalyzer, the
heuristic identifies arithmetic, general/unknown domain, easy, score .12
(5/40*.30 + 1/3*.25 rounds to .12), task rules
`explicit_task_questions_v1`. The packaged arithmetic policy has that score but
**reference_available=True**. A bare request has reference=False and cannot even
resolve that frozen task signature. Adding reference text would repair only this
prerequisite mismatch, not the allowlist/scientific scope or resource identity.
Its frozen compatibility ID is
`5f217f601b87ab4d2889b59ca9bda07d8a07a6774d074625f8b01c2050cb736d`.

In the new opt-in path, exact registrations win first. An unseen input must match
one reviewed v2 grammar/profile; absence/ambiguity is unavailable. Missing required
reference or judgment-label context is rejected. Arithmetic additionally must
match the actual Rule arithmetic patterns (import constants only; no verify call).
The fresh category analysis uses contract-bound scoring identity, so the old
artifact cannot be substituted. With a NEW certified artifact, TaskPolicyRouter
resolves exact task/profile/budget; GameRuntime clones frozen reputation state,
recaptures selector planning and compares compatibility IDs; retrieves exactly
one validated empirical artifact; attests actual resources including candidates;
checks budget/costs; samples the stored minimax mixture; invokes each selected
verifier exactly once; normalizes reports; finalizes with frozen reputation,
dependency grouping, output coverage and contributor minima; then checks resource
drift. Any missing contributor/coverage or incomplete required execution remains
uncertain. This path has been inspected, **not executed end to end**.

### Evidence factual example

`What is the capital of Bhutan?` is a grammar example, **not an assertion that the
configured corpus contains sufficient Bhutan evidence**. The legacy package
rejects unseen wording at its allowlist. Standalone task classification can mark
`direct_fact`; the actual corpus/index/model/configuration must still match the
fitted artifact. The packaged factual profile is easy/.13/reference=True, which
is not automatically compatible with every factual wording or a bare request.
The v2 path admits only the certified factual grammar/distribution; retrieval and
claim-level NLI/evidence-quality gates are unchanged. Missing evidence remains
abstention and cannot establish achieved direct_fact coverage. Root `corpus.json`
is not assumed to be the configured `build/multitask-policy42` corpus.

### Semantic reference example

`Paraphrase this reference: Mira delivered twelve parcels to Noor.` plus exactly
that reference text is a candidate unseen comparison input. The old router's
bounded-reference analyzer is only enabled together with an allowlist and uses a
fixed .1 score/version. Generic task analysis has a different identity; simply
removing the allowlist does not preserve that frozen policy identity. The v2
reference profile supplies a separately bound category identity. Existing
TaskPolicyRouter's `Paraphrase this reference:` source/context equality guard is
retained, as are Semantic label-context rejection, model/mode/thresholds and
reputation/coverage/contributor checks. High similarity on number, negation,
entity or relationship contradictions is a verifier limitation. Native
contradiction observations have not been collected.

### Confidence: critical additional blocker

The generic historical task analyzer never emits `consistency` for ordinary
questions, and the published registry has no standalone consistency policy.
More importantly, `app/decision/coverage.py:task_capabilities` recognizes only
arithmetic, direct_fact and semantic_comparison outputs. It does NOT grant
achieved `consistency` coverage to Confidence, or standalone evidence_retrieval
coverage to Evidence. A consistency-only route could sample and execute but would
remain unresolved/uncertain at finalization even with excellent judgments.
New runtime installation explicitly rejects those unsupported achieved-output
requirements instead of waiving coverage. Rule comparisons/adult/structural checks
also lack the arithmetic output contract and are not newly certified here.

Confidence CAN be a real selected/informative participant on arithmetic, factual
or reference-backed policies, with coverage supplied by compatible reports. Its
native provider, 5-sample contract where configured, temperature, prompts, shared
NLI/model dependencies, costs, failure/timeout behavior and reputation remain
unchanged. New policies must demonstrate positive minimax mass on any Confidence
teams claimed as selected. Do not force Confidence into a team to manufacture a
successful minimax demonstration. Standalone consistency certification additionally
needs an explicitly reviewed versioned game-owned achieved-output contract and
execution integration; a new fit alone will not solve it.

### Multi-verifier execution

For four eligible candidates the existing enumerator considers 15 nonempty teams
x 2 aggregations. Obligations, references, participant minima, cost budgets and
eligibility remove infeasible teams. With only Rule supplying arithmetic coverage,
for example, at most 8 teams x 2 aggregations remain before other constraints.
A policy may legitimately put zero mass on most of them. New atomic-category
artifacts may select compatible combinations through this same engine. Distinct
fact-plus-calculation component questions still require ComponentPolicy, answer
binding and source-backed descriptors. They are not flattened into the new
arithmetic grammar; the old component execution path is preserved. Generalizing
component-source distributions needs a separate component certification package.

## Backward compatibility evidence and limits

Before runtime additions, `validation/preservation-before.json` captured 661
existing source/artifact files and three embedded registration inventories:
reconciliation, minimal package and prototype-policy package, each listing the
same 69 exact questions. Full embedded policies include matrices, probability
vectors, compatibility IDs, execution contracts and resources. All existing
captured source/artifact bytes remain identical in the after-check. New files are
additive; unrelated dirty work was preserved.

The boundary unittest iterates all 69 questions and checks exact delegation of
selector, analysis, request and validation ID with no category call. Exact failure
is returned without fallback. This is real composition testing with probe
runtimes, **not native verification or executable policy-route certification**.
`validation/capture_routes.py` is prepared to compare actual legacy router
resolutions against composed resolutions for every question with no reference,
external reference and label context (207 checks), including policy ID,
compatibility ID, probabilities, resources, budget and unavailable reasons.
It currently cannot import: `httpx` is missing. The required dynamic before/after
behavior capture could not be completed; the original routing code was therefore
left byte-identical. Full behavior preservation remains an explicit blocking gate.
Any observed routing/identity/probability/resource/behavior difference must block
release, even if unrelated to the new path. No baseline is regenerated to hide it.

## Testing environment

No `.venv`, `pyproject.toml`, Pipfile or pytest config was found. Intended manifests
are `requirements.txt` and optional `requirements-verifier-collection.txt` (which
includes the first). The documented Windows resource runtime and old temporary
Intel-Mac test environment are not available; `/private/tmp/research-v1-planning-tests`
is absent. Available /usr/local Python is 3.12.0; /usr/bin Python has neither
pytest nor pydantic. Python 3.12 has pydantic/scipy/numpy but lacks pytest, httpx,
faiss, torch, sentence_transformers, fastapi and dotenv. Exact findings are in
`validation/environment.json`. No packages were installed.

Actual checks: **10 unittest tests passed / 0 failures**; **0 pytest tests ran**
(`No module named pytest`, process exit 1 before collection). Syntax compilation
passed. Preserved bytes/registrations check passed. Real router/import tests and
native/regression execution remain blocked. Prior documentation records an
incompatible Intel-Mac torch/Transformers/NumPy resolution; blindly repeating an
unbounded install on this host is not a validated fix.

After separate authorization, on an isolated supported environment (preferably
owner-provided CPU Linux with Python 3.11), these are the exact setup commands from
repository root. The unpinned manifests still require import validation; these
commands are not a claim that every platform resolves a working model stack:

```sh
python3.11 -m venv /tmp/category-verification-v2
/tmp/category-verification-v2/bin/python -m pip install -r requirements-verifier-collection.txt
/tmp/category-verification-v2/bin/python -m pip check
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 /tmp/category-verification-v2/bin/python -c 'import pytest; from app.game.models import PlanningContext; from app.game.category_runtime import CategoryGameRuntime'
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 /tmp/category-verification-v2/bin/python -m pytest -q tests/test_category_applicability.py tests/test_category_runtime_boundary.py tests/test_policy_package.py tests/test_game_three_outcomes.py tests/test_game_task_conditioning.py tests/test_flexible_runtime_dispatch.py
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 /tmp/category-verification-v2/bin/python docs/category-generalization-v1/validation/capture_routes.py > /tmp/category-exact-routing-v2.json
/tmp/category-verification-v2/bin/python docs/research_v1-precollection-proposal/validation/run_planning_checks.py
/tmp/category-verification-v2/bin/python docs/category-generalization-v1/validation/preservation.py
```

Existing regression fixtures may invoke injected verifiers or synthetic LPs; they
must not invoke native constructors/providers or use production fitting data.
`run_planning_checks.py` actively forbids verification, collection, fitting and
networking. No model downloads or Ollama service startup is part of setup.
Dependency-version changes or a production import refactor need separate review.

## Completion gates

See CERTIFICATION-PLAN.md. No new category is certified. No complete native
previously-unseen-question demonstration exists under a category-certified policy.
A declaration, a loaded artifact, successful routing, successful native execution
and independent certified evaluation are five different milestones. This change
only advances implementation/integrity/boundary-testing preparation.
