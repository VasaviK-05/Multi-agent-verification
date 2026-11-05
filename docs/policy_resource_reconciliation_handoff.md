# Policy/framework completion handoff

The existing owned framework is locally complete within its frozen scope. The
arithmetic/factual resource-contract blocker is repaired by an explicit singleton
execution transfer; the full compound path now has native acceptance. No API,
frontend, DB, answer-generation, deployment or verifier/retrieval algorithm code
was changed. No broader question support, new fitted teams, refit or new study was
introduced. This is the scope freeze for the 15-day final-review window.

Run the commands below from this delivery checkout, not the dirty offline-policy
host checkout. The teammate's running environment remains inaccessible and is not
claimed validated by local results.

## Delivery and preserved identities

* Delivery branch: `codex/framework-local-acceptance-v1`, based on fetched main
  `68e2871f386468eb28620a6fd61bdf325d1dd498` (PR #31 includes reconciliation merge
  content `836cb9d096bd29455b7657674596928981297376`). The exact delivery commit is
  the branch HEAD in the delivery message and `git rev-parse HEAD`.
* Original policy publication: `9f774678c5e4d845690022bcfd0a2550b1b3eaec`.
* Original bundle remains byte-for-byte unchanged: SHA-256
  `3ab4040b7df7b86eaa0b914459429bceefb129790073b60657ceb54ebffad184`; bundle ID
  `6286898cfdd5ef75b2a09f6556dc2c8fcc1b4f192a6d77dd6decf843867c0882`.
* Original policies, probability vectors (including zero-probability strategies),
  certificates, matrices, histories, reputation snapshots, thresholds, coverage
  rules, costs, budgets and empirical evaluations remain unchanged. No frozen
  artifact under `artifacts/` was edited.
* `reconciliation/framework-source-state-v1.json` records the exact application
  source inventory, Python/dependency versions and tested execution-file hashes.
  It is a new source/setup identity, not a historical measurement identity.
* Existing unrelated host changes remain in the original checkout. All work was
  isolated at `build/framework-local-acceptance`. No AGENTS.md was found.

## Exact repairs

1. `app/game/offline/singleton_compatibility.py` implements the separate pinned
   singleton transfer, its native factories, actual-instance observer and guarded
   selector. `reconciliation/singleton-transfer-v1.json` binds the two original
   atomic artifacts, their unique strategies, source identities and leaf resource
   scopes. Transfer ID:
   `ddbb12d1a91ee520887ee0462e81a57ea34109b821487b8cc045a90b268eec87`.
2. `app/game/execution.py` accepts that explicit proof for those exact artifacts,
   while ordinary full-manifest and reference validation remains strict. Pre/post
   singleton proofs and observed IDs are retained separately in the audit.
3. `app/game/offline/reconciled_resources.py` shares the existing local Evidence
   construction with the singleton path and supports an explicit Evidence-only
   resource scope. All six embedding/tokenizer/model/NLI/retriever/Evidence
   constructor call expressions are AST-identical to the previous compound
   factory; only helper extraction changed. Native algorithms were not edited.
   The compound capability-registration fix already on main is now exercised by
   complete native execution.
4. `scripts/framework_acceptance.py` persists a fixed six-request plan, journals
   every started/completed call, enforces total/category/per-request limits,
   blocks duplicate calls and HTTP, and uses the real router/factories/finalizer.
5. `scripts/verify_framework_delivery.py` checks original artifact/resource pins,
   the separately versioned software overlay, transfer, acceptance accounting and
   exact correspondence between delivery code and native-tested code. The target
   capture script now inventories the singleton adapter too.

Only owned execution/compatibility adapters, their tests, source-preservation
attributes, metadata and this handoff were changed. Analyzer/selector/reputation/
decision/early-termination baseline behavior was regression-tested and retained.

## Why singleton contraction preserves behavior

This repair **does not contract the planning context**. The captured four-candidate
plan, dependency registry, all sixteen strategies, zero probabilities, history,
requirements, aggregation, costs and finalization remain intact. Both artifacts
have exactly one positive probability, exactly 1.0, selecting one native object.
The explicit transfer rejects any other artifact or strategy support.

`SingletonSelector` plans with the original four names and explicit capability
metadata. Frozen planning still supplies the original reputation statistics.
Only the certified singleton can be resolved; resolving an unused name raises
before constructing anything. Unused candidates are metadata, not synthetic
verifiers or fabricated observations. No Confidence/Ollama object/service is
needed for the Rule or Evidence execution closure.

The required closures are Rule's no-argument native constructor/source/settings,
and Evidence's existing regex claim generation, embedding/tokenizer, corpus,
FAISS/chunks/build receipt and NLI/tokenizer. Source bytes are pinned; selected
native classes/default constructor settings and actual object identities are
checked. Settings, model parameter versions and required resources are observed
before/after. A different native object, changed code/model/corpus/index/settings,
wrong relocation intermediate, different policy or changed probability rejects.

Retained-report metamorphic tests compare the original full-roster execution with
the transferred path at RNG values 0, 0.5 and the largest float below 1. Context,
strategy, aggregation, thresholds, frozen reputation, costs, coverage, numerical
verdict and public result match. This proves the execution/finalization invariant
for the same reports; it does not invent new empirical performance. The new native
campaign separately confirms real selected objects execute correctly.

Historical full manifest, historical selected scope, source/config-transferred
intermediate and actual observation remain distinct. The observer never returns
an old full manifest in place of an actual scoped observation. A plain scoped
snapshot still cannot satisfy the original full-manifest runtime. This is a
separate atomic transfer; the compound execution proof is not reused to authorize
singletons. Exact source-review facts are shared through pinned byte identities.

## Concrete entry points and request formats

```python
import random
from scripts.reconciliation import load_bundle, configuration, selector_for
from app.game.offline.singleton_compatibility import create_singleton
from app.game.offline.reconciled_resources import create_scoped
from app.models.schemas import ValidationRequest

routes, provider, compound = load_bundle()
config = configuration("build/adapter.local.json")
arithmetic, factual, reference = provider.snapshot()

# Do not replace this selector with a one-candidate planning selector.
selector, observer = create_singleton(config, arithmetic)  # or factual
request = ValidationRequest(question="What is 328 + 536?", answer="864", context="864")
result = routes.router().run(selector, request, "owner-validation-id",
    provider=provider, rng=random.Random(1103), resource_observer=observer)

# Compound uses exactly the injected native E/R pool and scoped capabilities.
pool, compound_observer = create_scoped(config, compound)
compound_selector = selector_for(pool)
request = ValidationRequest(
    question="What is the population of Cameroon, and what is that population plus 1000? Give both values.",
    answer='{"base":"29879337","derived":"29880337"}', context=None)
result = routes.router().run(compound_selector, request, "owner-component-validation-id",
    provider=provider, rng=random.Random(1103), resource_observer=compound_observer)
```

Use the existing exact bundle allowlist and catalog; no general question support
is claimed. Atomic context/reference presence remains part of the original route.
The accepted factual example is `What is the population of Belgium?`, answer and
context `The population of Belgium is 11941781.` (pinned source snapshot truth).
Missing required reference presence does not silently become another route.

Compound `answer` is a string containing JSON with exactly two plain decimal
strings, `base` and `derived`. Numeric JSON values, duplicates, missing/extra fields,
malformed text and unsupported templates fail before calls. Evidence checks the
submitted base; Rule checks the submitted base plus increment. No gold base is
substituted. Component IDs and binding IDs are retained. Qualified component
failure rejects; all qualified passes accept; abstention/missing coverage can be
uncertain. No early stopping, hidden fallback, request-provided policy selection
or test-label input to routing is added.

Store `result.summary` alongside the original policy/context/contract IDs,
selected and attempted teams, per-call states, required/achieved/unresolved
coverage and finalization. Atomic audits contain
`singleton_resource_compatibility` and `singleton_resource_compatibility_after`;
compound audits contain `resource_compatibility` and its `_after` counterpart.

## Resource IDs and relocation

The original atomic artifacts are:

* Arithmetic artifact `cf4507400b26f79ab63366ab64b25ef779870fb85f8c33f7aa60a735a4762477`,
  context `5f217f601b87ab4d2889b59ca9bda07d8a07a6774d074625f8b01c2050cb736d`,
  selected strategy `afbd22f1ed2281814985af413a3945c5706d1aa838eba2d1b79cc391371521ac`.
* Factual artifact `e7c4eb8f3fce899cd52e75bb2b43efab2198ddba794b3605664946a8dc06094d`,
  context `d25662648b1266587bfa82698e78aace645f5160c91f05d5e235a4cefb2d782b`,
  selected strategy `3e05661eb80a54b012f4ca25761368edb71affb4fc33e29c90cd2ff8af35b6b3`.
* Their original full manifest remains
  `e23c6f034a4c660d30433d133be3a197db620abbdf22a78907ef5e3687d45ccb`.
  Historical Rule scope is `ee2df40ffe3f9603d001287fd066269fcaf4b4e1c714df93c3fe1a792ae5b5d6`;
  historical Evidence scope is `9f3bbad0dc3d670c168f57f41f09ec034c73ddd12b5e47050da51aed2cea2e01`.
* Compound policy remains
  `0192b98e50ab5dcbd40ca78a0d4a3ec3978dfe8086edcb615802c21024c83532`,
  contract `0b93b2782afbf1da65be0064dd7a0218f6e347abda1568f2da3d15daa1fbf3e6`,
  historical scope `310364dae8d9d6c001622d4bbe1866ca0646fb8f50c9c50a022e05f5353688c1`.

Local intermediate/actual scope IDs were Rule
`550a0ab2b4454a27b5f7e80346f04716ad492f8b5d32e833c9fa7370079a179a`,
Evidence `362b9be00eeadbc204042d508faa524b7105812ee716f1498f83d62696bc7611`, and
compound `012cee47d0c816b89bb792d987ade2204abebf9ab026737a0967bac503987de9`.
Paths/settings can give another installation different derived IDs; it must prove
its own observations, not copy these IDs. The exact native proofs and pre/post
checks are in `reconciliation/framework-native-evidence-v1.json`.

Required external content remains embedding
`23c61c55d84d9ab0045288ba589018e80ff90cf894514f5676e351c14624d255`, NLI
`a28c08014f62b13be758a1f22d1cbfd30e9f7b0f91d19fbc3bd5c369b11fcf7e`, corpus
`28e6241079b1afab419ebdbaea580510796c648d1855dcc91759ab3d8950b95a`, and physical
index/receipt aggregate `e802300251695e22ff0de258b39da818488722df347e04af20507e240442489b`.
See `artifacts/compound-study-36-v1/external-resources.json` for individual files.
Rule does not read unused model/corpus/index/service resources. Evidence retains
all its genuine local requirements and performs no generation.

For an existing copied Evidence installation, set the local configuration's
`resource_relocation_binding` to a fresh intended metadata path, then call
`prepare_singleton_relocation(config, factual)`. Write the returned binding with
exclusive creation; do not overwrite an old proof. Compound uses
`python -m scripts.reconciliation prepare-relocation ...` as before. Rule has no
index relocation dependency and rejects an index binding.

Both paths validate exact historical physical index/receipt bytes before mapping
only the logical index identity through existing `verify_relocated_index`. The
binding must name the derived **intermediate manifest for the particular scope**,
not the original full/pair manifest. The native retriever rechecks the same proof
before load. Existing native relocation path/time restrictions remain; rejected
cases must not be repaired by rewriting the historical manifest or algorithms.
No corpus/index rewrite, rebuild or download occurs in these adapters.

## Local validation and native accounting

The predeclared plan is `reconciliation/local-acceptance-plan-v1.json`, ID
`da850b53f862eb590b9dd3185da035f8aa9a95ec0a9fdcf286941a27856a3017`. Examples and
labels came from existing independent arithmetic/factual frames, the pinned
GeoNames source and the existing Cameroon correct/wrong-math development cases.
They were fixed before inference and never replaced after outcomes.

The fresh campaign completed **8 starts / 8 completions**, exactly 2 Rule singleton,
2 Evidence singleton and 4 compound E/R calls. The six outcomes were pass/reject
for arithmetic, pass/reject for factual, and pass/reject for compound. Every
required capability was achieved; component identities, binding, actual native
instances, pre/post resource proofs and finalization validated. No uncertainty,
execution failure, resource drift, fallback, retries or Confidence generations
occurred. HTTP was forbidden. No policy/threshold/budget/reputation was updated.

`reconciliation/framework-native-evidence-v1.json` contains sanitized outcomes,
all 16 start/completion ledger entries, proof IDs, tested source hashes and hashes
of retained raw local logs. It publishes no weights or resource snapshots. Raw
journals/results remain in ignored `build/completion-acceptance-v1/native`.
Earlier incomplete compound/reference attempts remain unchanged and are not
relabelled successful. This is a new, separate acceptance campaign.

The final owned regression run passed **605 tests**, including baseline analyzer,
selector, reputation, decision, early termination, game/runtime, singleton drift,
component binding, reference, relocation, package and API-audit fixtures. Three
pre-existing tests that directly call native Rule were deliberately deselected
to honor the eight-call campaign cap; stopping semantics were exercised with
report fixtures. There is one existing Starlette/httpx deprecation warning. No
dependency was installed or changed. Evidence-only relocation and wrong-scope
proof rejection were additionally checked in the focused suite. Seven retained
router replay cases passed separately; they are not fresh inference.

## Reference requirements and evidence boundary

The frozen reference artifact is
`ee32392c870fba30b08b4f7509af645019d9f8b92dc7c39bafeceb8207745c8f`;
policy `c05a50fb5fc3651c8dc5d1bd55ec02086c3f4c26e49e7145393cb007e7149cda`;
context `dda2320b4a1dea8b63df7886cb4d78f481cda1466c8428c8ae6dccf9432388f7`.
Its own full resource manifest is
`7dc5ab6098f803133284f413ad577970073c99f12fb020c6b4a2dc75b9642ffb`.

A fresh construction/service/actual-instance binding check passed, with stable
pre/post manifest `055dbe02ae08d23a1573c33844c59abcb376dba0242226038a2d5557a48cbea4`.
It made **zero verifier calls and zero generations**. The result is separately
retained in `reconciliation/framework-reference-binding-v1.json`.

Reference still requires Ollama **0.40.14**, `llama3.2:3b`, digest
`sha256:a80c4f17acd55265feec403c7aef86be0c25983ab279d83f3bcd3abbcb5b8b72`,
loopback `http://localhost:11434/api/generate`, five samples, temperature 0.8,
timeout 60, CPU, the unchanged prompt
`dc09c40fa96b3410833dd681cd674806dbffc8301db4c5890a5b3043b86b868b`, and its local
resources. Same model digest alone does not prove service equivalence. The old
atomic full-roster 0.40.5 requirement is historical, not imposed on reference or
the independently authorized local singletons.

Use `create_reference(config, reference_artifact)` and `selector_for(pool)` for
construction, then `reference_observer.snapshot_for(actual_selector)` and
`authorize_artifact(...)`. Only the exact reference artifact can use that proof.
The fitted mix, old evaluation and required service/prompt/sampling checks remain
unchanged. No fresh end-to-end reference sampling was requested or claimed.

## Evidence and paper-claim status

| Existing category | Fitted policy and frozen empirical evaluation | Current direct-runtime acceptance | API/deployment acceptance | Material limits |
|---|---|---|---|---|
| Arithmetic | Rule probability 1; reserved 40/40 decisions correct, 20 groups; matching fixed strategy ties | Correct and incorrect cases passed expectations; 2 native calls; full plan preserved | Other owner, not validated here | Finite supported frames/reference context; no broad arithmetic or game-theory superiority claim |
| Factual | Evidence probability 1; reserved 40 cases, 97.5% coverage, 1 false reject, 1 uncertainty; fixed strategy ties | Correct and incorrect cases passed expectations; 2 native calls | Other owner, not validated here | Source-known facts largely in corpus; no unseen-source/world-truth generalization; known selected-verifier error remains in frozen results |
| Compound E/R | Fixed E+R; reserved 45/48 decisions, no observed errors and 3 uncertainties; 85% floor chosen after development; fixed pair ties | Correct/wrong-math cases passed; 4 native calls with submitted-answer binding and complete finalization | Other owner, not validated here | Original 90% infeasibility preserved; shared dependencies do not establish independent corroboration |
| Reference | Experimental Semantic 1/6, Semantic+Confidence 5/6; 20 reserved answers/10 groups; expected coverage 66.67% vs fixed pair 80%; loss .0667 vs .04 | Fresh construction/service/binding only; zero new verifier calls/generations | Other owner, not validated here | 50% floor chosen after observed 60% development coverage; original 90% infeasibility retained; no new reference end-to-end inference |

Sources: `artifacts/flexible-heldout-v1/summary.md`, compound frozen results and
`docs/supported_category_policy_integration.md`, plus
`artifacts/remaining-category-studies-v1/reference-50-v1/publication-results.json`.
Native acceptance reuses predeclared source-known/history-development examples;
it is not a new held-out experiment and does not enlarge those sample sizes.

Supported paper claims are bounded framework implementation, typed/certified
finite-game optimization under declared budgets/coverage/attack assumptions,
reproducible frozen results, and now tested local proof-aware execution for the
existing singleton and pair policies. Within one category the distribution is
frozen; this is not universal per-answer optimization. Current fitted selections
have size one or two; there is no demonstrated triple selection. Report-level
forced-support/rejection attacks can cause errors; suppression can remove
coverage. These simulations are not observed upstream compromises. Shared
embedding/NLI/failure groups mean verifier names are not independent evidence.

Do not claim general verification accuracy, population safety from zero observed
errors, source-independent/blinded generalization, universal game-theoretic
superiority, end-to-end deployment latency savings, or publication acceptance.
Atomic/compound fixed baselines tie; reference's fixed pair has better clean
coverage/loss while the mix trades abstention against the modeled corruption
objective. Post-development coverage-floor amendments must remain disclosed.

Future scope only, not work for this deadline: wider question/source/cohort
validation, independently evaluated failure paths/larger teams, and end-to-end
operational performance/uncertainty assessment. None was started here.

## Verification and separately versioned overlays

```powershell
python -m scripts.verify_framework_delivery
python -m scripts.verify_reconciliation_package
python -m scripts.replay_remaining_policies --output build/fresh-recorded-replay
```

`verify_framework_delivery` validates the new transfer/native evidence and its
exact tested code, all original resource/source pins, original typed artifacts
and the completion overlay. The immutable original inventory still has 484/487
matching files; its three changed integration-source paths are `.gitattributes`,
`app/game/execution.py` and `app/game/component_execution.py`. All frozen artifact
bytes match. `framework-completion-review-v1.json` links the previous merge review
to this new software layer without changing either old review or old hashes.
The old whole-publication/merge-source check correctly rejects newer source
bytes; it is not silently redefined as a passed historical observation.

The native campaign command is retained for separately authorized reproduction:

```powershell
python -m scripts.framework_acceptance --configuration build/adapter.local.json --output build/fresh-native-acceptance
```

Do not run it again on this computer under the already-consumed eight-call
budget. It creates a fresh directory, writes its plan before construction, checks
all native contexts before calls, then journals the fixed six requests without
retry or replacement. Reference reproduction is construction/binding only:
`python -m scripts.reconciliation reference --configuration build/adapter.local.json --output build/fresh-reference-binding`.

## API/integration owner tasks (not remaining framework repairs)

1. Fetch main or this delivery into an isolated review checkout, preserving the
   running checkout's changes. Commands use the current delivery, not a deleted
   historical branch:

   ```powershell
   git fetch origin main codex/framework-local-acceptance-v1
   git worktree add ../framework-review origin/codex/framework-local-acceptance-v1
   ```

2. Capture the actual target without importing its app or generating. The script
   uses stdlib only and omits credential-bearing URLs/unknown secret fields:

   ```powershell
   python scripts/capture_reconciliation_target.py --target C:/actual/running-checkout --configuration C:/actual/adapter.json --output C:/fresh-target-capture.json --service-metadata
   ```

   Compare exact source/configuration/resource identities with this delivery;
   missing or different required resources must be restored or reviewed, never
   accepted by copying a historical manifest. Use already available matching
   resources and `reconciliation/adapter.template.json`; no auto-download exists.

3. Connect the **same actual** factory-created selector/observer to the server's
   owned policy dispatcher. Preserve the existing API/DB audit/persistence paths.
   A separately constructed factory's proof is not actual server-instance proof.
   The current orchestrator's game-runtime slot expects GameRuntime, not a
   QuestionPolicyRouter object: the API owner must adapt its dispatch/response
   wiring to the callable router above, not pass the wrong object type. Compound
   component reports are in `summary.attempts`; preserve their component/binding/
   validation IDs and separate original/intermediate/observed proofs in storage.
   Request generation/frontend owners must provide the exact serialized answer
   schema and display uncertain/explicit failure outcomes without silent repair.

4. Validate same-process `snapshot_for(actual_selector)` and target direct/API
   execution plus persistence under the integration owner's separate call budget.
   This is environment/wiring acceptance, not a request to fix our local adapters.
   Target service/resource/source differences, if present, remain explicit blocks.

There are **no remaining owned local policy/framework blockers for this fixed
scope**. API wiring, target-machine instance/resource attestation, persistence,
frontend/generation formatting and deployment acceptance belong to those owners.
Known research limitations above remain limitations, not hidden implementation
tasks or reasons to refit.

`deployment_active:false` is unchanged package metadata; the published loader
never enforced it as an activation gate. Server-owned activation configuration
and resource validation remain separate gates. This work did not merge main,
activate deployment, change global generation, or validate the teammate's live API.
