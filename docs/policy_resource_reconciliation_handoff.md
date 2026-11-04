# Policy/resource reconciliation handoff

This feature branch supplies an opt-in, proof-aware compound execution seam and a
reference-specific full-resource seam. It does not activate deployment or change
API, frontend, DB, answer generation, verifier or retrieval algorithms.
Run package commands from the isolated feature checkout, not the offline-policy
host checkout.

## Main conflict-resolution addendum

The feature parent is `03a0fa161d7ca783258a3114d17ede7de537476e`; the merged
main parent is `c7be1489b26ec7e0f2237acb71ca4f97000d7a8f`. The feature worktree
was clean and no merge/rebase/cherry-pick was in progress before merging main.
The dirty offline-policy host checkout was not used for the merge.

Eight paths conflicted: `.gitattributes`,
`app/analysis/capability_probe_analyzer.py`, `app/game/component_execution.py`,
`app/game/execution.py`, `app/game/execution_contract.py`,
`app/game/finalization.py`, `app/game/models.py`, and
`app/game/task_conditioning.py`. Both complete implementations were compared.
The analyzer, contract, finalization, models and task router have identical source
lines on both parents; their exact publication encoding was retained. Component
execution keeps main's dispatch/finalization plus the opt-in proof seam and
separate historical/pre/post observations. Game execution keeps selected-instance
observations, ProjectObserver audit output, strict relocation authorization and
reference proofs, and incorporates main's distinct selected-team/informative
minimum audit fields. The attributes file combines the full publication inventory
with later reconciliation-specific byte-preservation rules.

None of these seven resolved Python files contributes directly to the pinned
implementation/configuration resource fingerprints. The attribute resolution can
affect those contributors' checkout encodings, so all fourteen pinned contributing
source/dependency files were rehashed: every original pin still matches. No
expected resource hash or capsule ID was changed and no new verifier-equivalence
exception was added. The whole application-source digest and revision are new;
they must never be relabelled as the original measured setup. API, DB, selector,
ProjectObserver and native verifier/retrieval source files remain unchanged from
the feature parent. Historical policies, certificates and evaluations remain
unchanged.

`reconciliation/main-merge-review-v1.json` records both parents, all eight source
resolutions, and exact original/merged source-overlay identities. The canonical
`scripts.verify_publication` check intentionally reports three modified integration
source paths: `.gitattributes`, `app/game/execution.py`, and
`app/game/component_execution.py`. This is not a resource mismatch and is not
reported as an unchanged whole publication. Its other 484 inventoried files,
including every frozen publication artifact, still match. Use the separately
versioned overlay audit without changing the original publication inventories:

```powershell
python -m scripts.verify_reconciliation_merge
python -m scripts.verify_reconciliation_package
```

That audit checks the reviewed source overlays, the unchanged original inventory,
original resource pins and typed frozen policies. The original canonical checker
can still be run on the immutable publication checkout. Portable replay remains
retained-report evidence. No live verifier acceptance, generations, refit, download,
index rebuild or activation was performed to resolve this merge. The prior
singleton-contraction, incomplete compound acceptance and teammate live-API
limitations below are unchanged.

Merge verification: 297 compatibility, relocation, selector, routing, reference,
reputation/injection and API audit tests passed outside the sandbox. Another
18 synthetic held-out-recording and no-dispatch answer-binding tests passed.
The threaded
API client stalled in the sandbox; no API/DB implementation was changed to avoid
that restriction. One new audit test initially assumed the synthetic selected
floor was two; its fixture expectation was corrected to the actual floor of one,
while testing a distinct informative floor of two. The final suite passes. The
immutable publication checkout still passes all 487 byte/certificate checks;
merged overlay audit, package identities and seven portable replay cases pass.
There is one existing Starlette/httpx deprecation warning; no dependency was
installed or changed.

Whitespace checks on the merge's code, docs and reconciliation changes pass.
The all-imported-files check reports 525 existing whitespace findings in six
frozen license/source/diff artifacts. Every one of those file blobs is identical
to fetched main; they were deliberately preserved rather than rewriting frozen
history. Their exact paths and classifications are in the merge review record.

## Source state and scope

* Feature branch: `codex/policy-resource-reconciliation-v1`. Its exact delivery
  commit is the branch HEAD returned by `git rev-parse HEAD` and the delivery
  message; this document cannot embed its own commit identity.
* Integration base and refreshed relocation ref:
  `2c3813b58761b4b10a05d41d532d8d10575d16a3`.
* Frozen policy publication: `9f774678c5e4d845690022bcfd0a2550b1b3eaec`.
* PR base incorporated into the feature by merge:
  `main` at `c7be1489b26ec7e0f2237acb71ca4f97000d7a8f`. This updates the
  reconciliation branch; it does not merge or activate the feature into main.
* Local policy-bound host: `C:/Users/jhaan/Multi-agent-verification`, branch
  `codex/offline-policy-recording-pilots`, HEAD
  `2c9f697439d1d1c2ed7c0a92645848c0f07f7e3f`. Its existing execution/recording
  adapter changes, two test changes and untracked resource diagnostics remain
  untouched. Reconciliation is isolated at `build/policy-resource-reconciliation`.
* The teammate's running checkout, previously
  `C:/Users/User/Multi-agent-verification-integration`, is inaccessible. Fetched
  source and local native objects are not evidence of that running deployment.

`reconciliation/host-state.json` records the five original dirty/untracked paths,
checks their preserved hashes, and explicitly corrects an initial status-parser
path truncation using canonical custody identity without rewriting that record.

No applicable AGENTS.md was found. The remote is the supplied
`VasaviK-05/Multi-agent-verification` GitHub repository. All feature changes are
owned compatibility/routing/observation code, support for the published frozen
contracts, tests, metadata and documentation. Existing policies/certificates,
matrices and historical outcomes retain their original bytes/identities.

## Root cause and review

The policy measures historical source bytes, not every later source tree bearing
those filenames. Shared schema and adapter files contribute to every aggregate
implementation fingerprint. The schema adds request validation and response
metadata; it does not change VerificationResult. The adapter adds relocation
handling and a configuration field. EvidenceRetriever adds a proof-aware load
path, while its other methods and the verifier algorithm classes are unchanged.

The exact old/new file hashes and aggregate identities are in the pinned source
capsules. `reconciliation/source-review.patch` shows source changes with line
endings normalized for review; hashes still bind exact bytes. The original
canonical custody ZIP was available locally and used for comparison; it is not
published. `reconciliation/review-invariants.json` records unchanged class ASTs.
The existing source table is `docs/policy-resource-compatibility-diff.md`.

An additional observation difference was found: the integration full inspector
hashes a reserialized logical index manifest even without relocation. That yields
logical index ID `1120818b811644ee5fc343d63498355dd0beb49776e0fd8f5dbc484e4a922e7d`
from unchanged physical index/receipt ID
`e802300251695e22ff0de258b39da818488722df347e04af20507e240442489b`.
The reference proof explicitly binds this serialization-only difference. It does
not rewrite the physical manifest or disguise a new observation as historical.

`.gitattributes` pins reviewed critical source checkout bytes to CRLF and frozen
JSON to byte preservation. Use a Git checkout with attributes applied; do not
normalize verifier code to make a fingerprint pass. All other code/resource
changes reject until independently reviewed. No arbitrary future version is
allowed by a matching filename or passing tests.

## What the artifacts authorize

* `reconciliation/policies.json`: exact original bundle, SHA-256
  `3ab4040b7df7b86eaa0b914459429bceefb129790073b60657ceb54ebffad184`, bundle ID
  `6286898cfdd5ef75b2a09f6556dc2c8fcc1b4f192a6d77dd6decf843867c0882`.
  Loading validates typed artifacts/certificates; it does not observe resources.
* `docs/policy-source-capsule-v2.json`: exact E/R source transition, pinned ID
  `d78864a6cceb0262408617c724c8789f93811f9b72aa87856abb57dc49d24993`.
  Its legacy `observed_manifest_id` field is explicitly a **source-only** identity,
  not a live resource observation. The capsule alone cannot authorize execution.
* `reconciliation/integration-dependencies.json`: pinned additional relocation,
  active-observer and selection dependency bytes; ID
  `9bd64bb4876aa9108afff2ed23dde10fdc469013d44f5440338934c566962e9b`.
* `reconciliation/reference-source.json`: separately reviewed full-roster source
  transition, ID `8ae545bf6762dfcc1708be8ef41f347e9f8d2d94d0d05ad8a13782ed639579bc`.
  It is restricted in code to the exact reference artifact below.
* `reconciliation/reference-service.json`: the reference policy's current-service
  metadata. It is not substituted for an actual live service observation.
* Runtime `scoped_source_relocation_composition_v1`: separately identified proof
  linking historical E/R scope, source/config-transferred intermediate manifest,
  actual observed manifest, actual selected objects and optional relocation proof.
* Runtime `reference_source_resource_transition_v1`: separate full reference proof
  including actual objects, original/intermediate/observed identities, optional
  relocation and optional exact logical-manifest serialization attestation.

The capsule does not replace expected hashes. Historical and observed manifests
remain separate. Intermediate manifests are derived compatibility artifacts,
never historical measurements. Required corpus, vectors, chunks, receipt,
models/tokenizers and all non-permitted settings still reject changes.

## Compound wiring: actual callable entry points

The published compound policy ID is
`0192b98e50ab5dcbd40ca78a0d4a3ec3978dfe8086edcb615802c21024c83532`; contract ID
`0b93b2782afbf1da65be0064dd7a0218f6e347abda1568f2da3d15daa1fbf3e6`.
Historical E/R scope is
`310364dae8d9d6c001622d4bbe1866ca0646fb8f50c9c50a022e05f5353688c1`.
Component contexts are `b8fd7cd3bcc113748a36c1e2abef93c5db56f011119d244b4d2461075990c521`
and `b4975a9064d2c61e0506737c286be32dbc1a555c9a0d7fb14eb6f36d70989fad`.
Both component execution-contract content IDs are
`44d2121722a1be2f395dd07969b744dd88d770167d71865e1a6217512ade4ef2`.

```python
import random
from scripts.reconciliation import load_bundle, configuration, selector_for
from app.game.offline.reconciled_resources import create_scoped
from app.models.schemas import ValidationRequest

routes, provider, compound = load_bundle()
config = configuration("build/adapter.local.json")
pool, observer = create_scoped(config, compound)
actual_selector = selector_for(pool)  # registers capabilities for these names only
before = observer.snapshot_for(actual_selector)
proof = observer.authorize_component(compound.policy_id,
    compound.contract.actual_resources, before)
# Inject THIS selector and observer into the owner's server-owned runtime.
request = ValidationRequest(
    question="What is the population of Cameroon, and what is that population plus 1000? Give both values.",
    answer='{"base":"29879337","derived":"29880337"}', context=None)
result = routes.router().run(actual_selector, request, "owned-validation-id",
    provider=provider, rng=random.Random(1103), resource_observer=observer)
```

`create_scoped` validates resources before constructing only native Evidence and
Rule. It performs no Confidence construction, Ollama metadata requests or
network-based provisioning. Constructors use local-files-only model loading.
The observer checks the selected object identities, constructor/dependency state,
model parameter versions and file/source observations before and after dispatch.
All actual observations and both proof IDs remain in the execution summary.

The proof-aware seam is in `run_component_policy` / `run_component_diagnostic`.
Ordinary callers retain strict manifest equality. A plain scoped snapshot is
still rejected against a historical full manifest. The diagnostic entry point
cannot authorize a source transition by itself. The factory accepts only the
pinned compound policy; source/config changes cannot authorize another policy.

The answer is JSON **text in a string**, exactly `base` and `derived`, each a
plain decimal string. Numeric JSON fields, duplicates, extra/missing fields and
unsupported text fail binding before calls. Supported questions are the exact
bundle allowlist/catalog templates. Evidence checks the submitted base fact;
Rule checks the submitted base plus question increment. No gold base is supplied.
Both qualified component passes accept, qualified failure rejects, and missing
coverage/abstention/drift may yield uncertainty. All selected calls complete;
early stopping and fallback stay disabled. An uncertain result is legitimate.

## Relocation composition and preparation

Source/config compatibility changes only exact reviewed source identities,
addition of the binding field, and content-verified corpus/index path references.
Non-path settings must equal the original frozen configuration. This produces a
separately named intermediate manifest. The physical historical index/receipt
aggregate must still reconstruct its pinned historical identity. A changed vector
file cannot be excused by crafting a new binding with the old index fingerprint.

The existing `verify_relocated_index` must then validate the binding against the
**intermediate manifest**, not the original full or original E/R manifest. It
rehashes corpus, vectors, chunks, manifest and receipt; checks models/settings;
and permits only manifest path/mtime relocation. EvidenceRetriever receives that
same proof and rechecks it before loading. No rebuild/save fallback is added.

For a copied resource installation, edit a local copy of
`reconciliation/adapter.template.json` to point at the already available exact
model snapshots, corpus, index and receipt. Set `resource_relocation_binding` to
the absolute future path `<fresh-proof-directory>/binding.json`, then run:

```powershell
python -m scripts.reconciliation prepare-relocation --configuration build/adapter.local.json --output build/fresh-relocation-proof
python -m scripts.reconciliation inspect --configuration build/adapter.local.json --output build/fresh-preflight
```

The configured binding path must equal the first command's output/binding.json.
Preparation writes only a fresh metadata binding after byte checks; it never
rewrites a manifest, downloads, rebuilds or changes the corpus. Without relocation,
leave the field null. A binding for the wrong intermediate rejects.

## Reference's own contract and binding

Reference artifact ID:
`ee32392c870fba30b08b4f7509af645019d9f8b92dc7c39bafeceb8207745c8f`;
policy `c05a50fb5fc3651c8dc5d1bd55ec02086c3f4c26e49e7145393cb007e7149cda`;
context `dda2320b4a1dea8b63df7886cb4d78f481cda1466c8428c8ae6dccf9432388f7`;
contract-content `dc55c285163a32b70e21d5267847063945b587fd28cd44a4852a4f0dba813fa0`.
Its historical full resource manifest is
`7dc5ab6098f803133284f413ad577970073c99f12fb020c6b4a2dc75b9642ffb`.
Run `python -m scripts.verify_reconciliation_package` for all atomic matrix,
policy, context and contract identities, including arithmetic/factual.

Reference requires loopback `http://localhost:11434/api/generate`, Ollama
`0.40.14`, model `llama3.2:3b`, digest
`sha256:a80c4f17acd55265feec403c7aef86be0c25983ab279d83f3bcd3abbcb5b8b72`,
five samples, temperature 0.8, timeout 60, CPU, unchanged native prompt hash
`dc09c40fa96b3410833dd681cd674806dbffc8301db4c5890a5b3043b86b868b`, plus its
local NLI/embedding/corpus/index dependencies. Matching digest alone is insufficient.
Its prompt, source bytes, effective sampler settings and live service metadata are
checked. The old atomic policies' Ollama 0.40.5 contract is not applied to reference.

```python
from app.game.offline.reference_compatibility import create_reference
artifact = next(v for v in provider.snapshot()
    if v.artifact_id == "ee32392c870fba30b08b4f7509af645019d9f8b92dc7c39bafeceb8207745c8f")
reference_pool, reference_observer = create_reference(config, artifact)
reference_selector = selector_for(reference_pool)
observed = reference_observer.snapshot_for(reference_selector)
reference_proof = reference_observer.authorize_artifact(artifact, observed)
```

The reference-aware seam in GameRuntime accepts only the bound exact artifact,
keeps the full roster/resource contract, and retains pre/post drift rejection.
The command below constructs and binds native reference objects and checks live
metadata, but deliberately invokes no verifier or Confidence generation:

```powershell
python -m scripts.reconciliation reference --configuration build/adapter.local.json --output build/fresh-reference-binding
```

Reference requests, if separately approved for actual execution by the integration
owner, remain exact `Paraphrase this reference: <fixed allowed text>` frames with
that same text as context. No new reference inference is claimed by this package.

## Atomic singleton review

Arithmetic artifact `cf4507400b26f79ab63366ab64b25ef779870fb85f8c33f7aa60a735a4762477`
and factual artifact `e7c4eb8f3fce899cd52e75bb2b43efab2198ddba794b3605664946a8dc06094d`
select Rule and Evidence respectively, but their captured candidate plans and
resource contracts still bind all four candidates and original full manifest
`e23c6f034a4c660d30433d133be3a197db620abbdf22a78907ef5e3687d45ccb`.
Their frozen service requirement is 0.40.5. These are different contracts from
compound and reference. A singleton resource projection alone would fail the
captured candidate/planning contract. No separate singleton transfer authorizing
that planning change is available. Both remain blocked; the policy/resource
owner must review an independent candidate/dependency contraction proof and
its frozen planning/finalization invariants before proposing an execution seam.
No refit or new evaluation is automatically launched to hide this gap.

## Completed verification and honest native accounting

`reconciliation/local-acceptance-summary.json` contains the sanitized local
acceptance record and hashes of earlier incomplete records. Raw local outputs
remain ignored under `build/acceptance-20261104`; older records remain on the
policy host and were never relabelled as passed.

* Published byte/certificate loading: 487 files verified; original publication
  remains unchanged. Package verification reconstructs old/new implementation
  identities from contributing file hashes and validates all frozen artifacts.
* Original portable replay: seven retained-report routing cases completed. This
  is separate from native inference and the proof-aware seam's synthetic tests.
* Final compatibility/relocation/runtime/reliability suite: 134 passed; portable
  capture credential-filtering test passed separately. A further reference seam
  test validates frozen routing with synthetic reports and no native generation.
* Local compound preflight: exact required resources validated; intermediate and
  actual scope `012cee47d0c816b89bb792d987ade2204abebf9ab026737a0967bac503987de9`.
* Exactly one fresh compound acceptance was attempted. It constructed the local
  native models, then stopped before inference because selector capability keys
  included unused names. **Zero native verifier calls, zero generations.** The
  wiring is corrected and regression-tested. There was no native retry; complete
  compound execution/finalization acceptance remains unproved locally.
* Fresh native reference construction/binding: passed, with stable pre/post
  observations, zero verifier calls and zero generations. Actual full resource ID
  `055dbe02ae08d23a1573c33844c59abcb376dba0242226038a2d5557a48cbea4`, intermediate
  `bc0d5c4989b0e51294d161fee4131c5b87a2590bd11729f8c868b2ced41edbf1`, proof
  `e2f9b2d3e5aac00face2c5213a9e9a322ebab01226a05815bc0ec375c3c9806d`.
  This does not test reference-generated answers or an API process.

| Category | Local software validation | Local native acceptance | Teammate live API acceptance |
|---|---|---|---|
| Arithmetic | Frozen load/replay pass; contraction blocked | Not claimed | Not validated; independent singleton proof needed |
| Factual | Frozen load/replay pass; contraction blocked | Not claimed | Not validated; independent singleton proof needed |
| Compound | Composition, routing/finalization and negative tests pass | Fresh run blocked before calls; fix tested, no retry | Not validated; target identities and actual injected instances required |
| Reference | Own contract/proof/seam tests pass | Construction/service/binding pass; zero generations | Not validated; target service and same-process actual objects required |

## Teammate capture and validation commands

First fetch/review in an isolated worktree, preserving the running checkout and
all its dirty files. Do not infer its version from the fetched ref:

```powershell
git fetch origin codex/policy-resource-reconciliation-v1
git worktree add ../policy-resource-reconciliation-review FETCH_HEAD
```

Run this **stdlib-only** script from the review worktree against the actual
running checkout and its actual configuration file. Substitute the existing paths;
no assumption is made that those paths exist on another computer:

```powershell
python scripts/capture_reconciliation_target.py --target C:/Users/User/Multi-agent-verification-integration --configuration C:/path/to/actual-adapter.json --output C:/path/to/fresh-target-capture.json --service-metadata
```

It captures exact HEAD/branch/remote/dirty inventory, relevant source hashes,
declared whitelisted configuration, model/tokenizer file hashes, corpus/index/
receipt/binding hashes and credential-free loopback metadata. It does not import
the target app, read .env, copy resources, initialize models or generate. Missing
files remain explicit; secrets/credential-bearing URLs are omitted. It cannot
attest an already running Python process's effective constructor settings.

The integration owner must additionally record the actual runtime's execution
mode, constructor/wiring entry point, selector/observer types and selected object
classes, effective Evidence thresholds/retriever settings, Semantic comparison
mode, NLI/embedding associations and Confidence sampler/labeler settings. Supply
reviewed uncommitted diffs for mismatching relevant source files and any relevant
untracked sources; exclude credentials, DB/user data and resource snapshots.

After reconciling exact target source with this branch and configuring already
available matching resources in the review checkout:

```powershell
python -m scripts.verify_reconciliation_package
python -m scripts.reconciliation inspect --configuration build/adapter.local.json --output build/fresh-inspection
python -m pytest tests/test_policy_source_compatibility.py tests/test_reconciled_resources.py tests/test_reconciliation_execution.py tests/test_reconciliation_capture.py tests/test_game_resource_relocation.py tests/test_game_runtime.py tests/test_game_reliability_first.py -q
```

Only the integration owner can connect the SAME pool/selector/observer objects to
her server configuration. Retain `observer.snapshot_for(actual_selector)` and the
execution summary's pre/post observations/proofs from that same process. A
separate factory's passing observation is insufficient. Do not copy a historical
manifest over an observed one to make a check pass.

If she separately authorizes the missing bounded target acceptance, use a fresh
directory and the one-example/no-generation command, retaining all failures:

```powershell
python -m scripts.reconciliation compound --configuration build/adapter.local.json --output build/fresh-compound-acceptance
```

The command persists its plan before construction, journals every native call,
forbids HTTP, caps two calls and does not retry. It checks the complete policy
execution, component identities, proof and finalization; genuine uncertainty is
not counted as failure solely because it is undecided. Running this CLI on her
machine still establishes direct-runtime acceptance, not API persistence or her
server's injection, until those actual server objects are checked.

## Integration files, activation and next owners

Integrate this feature commit as a reviewed unit over its stated base. New files
under `app/game/offline/`, `app/game/component_*`, `app/game/question_routing.py`,
the two analysis adapters, support changes in game execution/contracts/models/
finalization/task routing, scripts, tests, `.gitattributes` and `reconciliation/`
are required together. There are no API/frontend/DB/generation/verifier algorithm
changes. Private custody archives, weights, model caches, generated resource
snapshots and unrelated host changes are excluded from the commit.

The integration owner owns actual target capture, dirty-source review, wiring,
missing compound native acceptance and same-process/API validation. The
policy/resource owner owns any separate singleton contraction. Changed algorithms,
models, corpus or generation/service settings remain blocked pending exact
restoration or separately authorized evaluation; no broad experiment is implied.

`deployment_active:false` remains unchanged package metadata. The published loader
does not enforce it as an activation gate. Server-owned operational activation
and resource validation are separate requirements. No deployment was activated,
and no category is declared ready for the teammate's live API.
