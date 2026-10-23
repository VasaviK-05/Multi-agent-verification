# Game engine completion: explicit pooling and resource provenance

Implementation base: main `5b9fae692fc091e78ae0f1a0c94cb3fa3d3aaf84`.
These additions concern the game engine and its input contracts. They do not
modify verifiers, API routes, database repositories or frontend code. Baseline
mode remains the default. No empirical policy or scientific setting is supplied.

## Pooled policies

`app.game.offline.pooling.PoolMember` contains one already history-bound context,
complete manifest, execution contract and attack specification. Every member
retains its own actual domain and history-derived reputation snapshot. There is
no domain relabelling, reputation sharing, or inferred domain mapping.

`fit_pooled_policies(members, pool_id=..., source_weights=...)` accepts at least two
explicit contributing domains. Each positive source weight must be declared and
the weights must sum to one. Other supplied members are applicability targets
only; their development labels do not contribute. Each member still needs the
existing nonempty history/development/final-test manifest, including for a sparse
target. Truly absent target histories/manifests are not fabricated.

The fit checks grouping/content/run identities across the entire pool to prevent
cross-role leakage and duplicated observations across domains. Group identifiers
must be globally meaningful. Semantic relatedness remains the supplier's grouping
responsibility. Candidate strategy definitions, costs, budget, minimum, requirement
signature, reference availability, dependencies, attacks, execution contract,
losses and evidence kind must agree. Domain-specific reputation may differ.

For strategy s and fixed attack a, the pooled payoff is:

`pooled_loss[s,a] = sum(weight[d] * mean_development_loss[d,s,a])`.

Each source cell replays all of that domain's development examples using that
domain's frozen snapshot. Resource loss is included in each source cell and
therefore charged once after weights sum to one. This is a weighted mean of
domain means, not an implicit weighting by dataset size.

The complete captured candidate contracts must also agree, including availability,
capabilities, prerequisites, configuration readiness and selector resource estimates.
Coincidentally equal feasible teams alone do not establish that equivalence.

The return value is `(pool_contract, fitted, source_evaluations)`, where `fitted`
is a tuple of `(domain, pooled_context, policy)` entries. Each policy binds the
exact target context and shared pooled payoff values. Pool membership, source
matrix/manifest/context IDs, weights, explicit target applicability and the payoff
digest participate in compatibility through `PlanningContext.pooling_contract_json`.
Changed payoffs or target settings cannot reuse that binding. The target's ordinary
provenance fields still identify its own datasets; the pooling contract records the
additional contributing evidence. A policy is a transfer of the pooled strategy
distribution, not an empirical guarantee for every target domain.

The pooled LP is solved once. Its identical strategy distribution and numerical
certificate are rebound and arithmetically validated against each target matrix ID;
target binding never reruns the optimizer. This also preserves a single shared
mixture when a degenerate game has multiple valid optima. Each source's context ID
must agree with the same domain's declared applicability entry.

```python
from app.game.offline.pooling import PoolMember, fit_pooled_policies, evaluate_pooled_final_test
from app.game.offline.evaluation import export_artifact

# members are complete, independently labelled, separately bound PoolMember records.
# weights, domain names and pool_id are project inputs, frozen before final scoring.
pool_contract, fitted, development = fit_pooled_policies(
    members, pool_id=pool_id, source_weights=source_weights)
domain, pooled_context, policy = fitted[target_index]
member = next(m for m in members if m.context.plan.domain == domain)
artifact = export_artifact(policy, pooled_context, member.manifest, member.contract,
    member.attacks, applicable_domain=domain)
# Explicit held-out entry point: no pool reconstruction or optimizer call.
final = evaluate_pooled_final_test(policy, pooled_context, member)
```

Preserve the returned development evaluations and frozen pool contract. Final
scoring uses actual strategy probabilities and all target final-test examples,
exactly as ordinary frozen scoring. Development/final labels never update runtime
reputation. Target-only refitting of a pooled context rejects.

The Stage 5A single-domain seven-method comparison CLI/API remains single-domain.
Its readiness check explicitly rejects pooled contexts. Use its readiness on the
original unpooled member specifications, then the explicit pooled APIs above.
A multi-domain seven-method scientific comparison/cluster-bootstrap protocol needs
the testing/research owner's explicit population weighting and grouping design;
this change does not silently repurpose the single-domain comparison protocol.

## Sparse-domain runtime routing

`app.game.domain_routing.DomainRoute` binds:

- a direct DeploymentEpisode;
- a pooled DeploymentEpisode for the exact same unpooled target context/history;
- an explicit positive `minimum_history_observations` threshold.

The declared rule is `minimum_eligible_candidate_history_v1`: use the least
observation count among the captured eligible candidate verifiers. Counts below
the threshold route to the pooled episode; counts equal to or above it route to
the direct episode. This conservative rule/threshold is a project setting, not a
calibrated default. Decisions use frozen counts; live feedback cannot switch a
route mid-episode. New histories require a new direct/pooled episode family.

Supply `domain_routes=(route, ...)` to the existing `GameRuntime` together with a
provider containing both exactly applicable artifacts. The mandatory `episode`
argument is an anchor used for failure audits only when routes are configured;
it is not an implicit default domain. Unmapped domains produce uncertainty without
dispatch. Missing/ambiguous/incompatible artifacts likewise never trigger another
domain, a different strategy, or baseline. Only one provider snapshot and one RNG
draw are used on a successful request. Existing full-team execution is retained.

The execution audit includes `policy_route`, domain, routing rule, frozen count,
threshold, chosen episode and complete pooling lineage. Request data cannot select
the routing threshold or artifact. The engine does not persist these fields itself.

## Resource-bound execution contract

`app.game.resource_provenance` provides frozen `ResourceFingerprint`,
`VerifierResources`, and `ResourceManifest`. Every fingerprint contains an explicit
resource ID, kind and lowercase SHA-256 content digest. Input order is canonical.
Duplicate entries and inconsistent shared-resource identities reject.

Required kinds:

| Verifier identity | Required resource kinds |
| --- | --- |
| Every verifier, including custom identities and rule | implementation, configuration |
| semantic | additionally model |
| evidence | additionally model, corpus, index |
| confidence | additionally model, prompt, service |

Declare every model separately if a verifier uses multiple models. Include other
relevant prompt, service or data resources beyond these minimum kinds. An
implementation digest should identify the complete code/config adapter bundle,
not just one file when other files affect behavior. Hash actual corpus/index bytes
or a canonical manifest of their complete content hashes; file size and mtime do
not establish content identity. Pin actual model revisions/weights. A service
fingerprint identifies a canonical non-secret service/model configuration, not
credentials, authentication tokens, or a claim of uncompromised service behavior.

Use ExecutionContract version `offline_public_decision_v2`, set `resource_manifest`
to the complete all-candidate manifest, and set `execution_configuration_id` to
`resource_manifest.manifest_id`. Existing execution settings remain separately
bound by the complete contract. A resource-bound artifact also validates exact
candidate coverage at load time.

Each recorded `Attempt` carries `observed_resources_json`, the canonical JSON of
its `VerifierResources`. It must be observed before the attempt, including for
failed, unavailable and abstaining attempts. Offline binding checks all partitions,
including independent history. Replay rechecks observations before transformations;
report-corruption attacks preserve these execution-resource records. Empirical
research readiness requires v2 and reports location-specific resource blockers.

For runtime, pass a server-configured `resource_observer` to `GameRuntime`. Its
`snapshot()` method returns a ResourceManifest describing every captured candidate.
The adapter must inspect actual/pinned resources without invoking verifier checks,
mutating reputation, or constructing unselected verifier instances. Missing or
mismatched observations reject before RNG/dispatch. A second snapshot after the
complete team detects changed observations and forces public uncertainty while
retaining attempted costs, numerical output and the audit. Unexpected adapter
programming failures propagate, matching existing runtime failure policy.

The audit includes expected, observed and post-execution resource manifest IDs.
Content identity checks cannot authenticate a dishonest adapter, detect a resource
that changes and changes back between snapshots, or prove upstream independence.
Integration must pin resources for the whole execution window. Shared resource
identity alone does not establish a compromise pathway; the project's dependency
registry still requires an explicit threat-model justification.

Legacy v1 remains supported for existing deployment contracts and synthetic
regressions. Absent new fields are omitted from serialization to preserve earlier
context/manifest/contract compatibility digests. v1 carries no observed-resource
guarantee and cannot pass the new empirical resource readiness gate.

## Ownership and tester handoff

Vasavi supplies these engine contracts, pooling construction, validation, routing
and audit fields. Tanmayee supplies the resource observation/collection adapters,
server configuration and application wiring, and conducts integration/research
validation. Raunak supplies verifier-specific resource facts and repairs. Samika
persists validation-level audits, including empty-result runs. No API/DB/frontend
or verifier implementation changes are included here.

Focused synthetic checks are in `tests/test_game_completion.py`. The testing owner
must additionally validate actual adapter observations against installed resources,
resource pinning/drift, multiple configured domains, exact threshold boundaries,
episode rollover after feedback, durable audit storage and all empirical settings.
For research, freeze source domains/weights, target applicability, sparse threshold,
population/grouping protocol and comparisons before accessing final scores. Report
per-domain and explicitly weighted aggregate results, uncertainty and limitations;
do not infer superiority from solver correctness or synthetic tests.

## Implementation checks in this review copy

- Combined affected engine suite: 721 passed, 3 deselected.
- Focused completion suite: 26 passed, including the final grouping validation.
- The three deselections are the pre-existing stale CLI revision assertion and two
  tests requiring original historical Git objects absent from this reconstructed
  source copy. They are not reported as passes. The testing owner should run them
  in the actual repository after correcting the stale assertion.
- These runs used real Python/Pydantic/SciPy/FAISS imports, controlled verifier
  doubles and an import-only SentenceTransformer stub that raises on construction.
  No models, verifiers, services, database or empirical experiments were executed.
- Original game/docs/test baseline files were checked against 32 GitHub blob hashes
  at the stated main revision. Syntax and whitespace checks passed.

The review archive includes the exact changed-file payloads, full patch, hashes,
test output and application instructions. It is an isolated implementation, not a
claim that the user's Windows checkout or remote branch has been modified.

## Independent Windows integration review

The archive is a proposal, not an approval or instruction to message another owner.
Its manifest's 17 file hashes and patch hash were checked before application.
The original checkout was clean on `vasavi/game-research-evaluation` at
`7a79e1866c22d34da23acae53275d7d072c224c6`. Fetch found main at the archive's exact
base, `5b9fae692fc091e78ae0f1a0c94cb3fa3d3aaf84`. Main includes PR #20 and teammates'
PR #21 verifier/configuration changes. No AGENTS.md applied. The separate branch
`codex/game-pooling-resource-provenance` was created directly from that main.
No merge, reset or replacement of teammate files was used.

After reviewing the complete patch and its callers, `git apply --check` passed.
Normal application then matched every proposed file after LF normalization.
Only the same 17 proposed game, documentation and focused-test paths are changed.
Verifier, route, database, frontend, requirements and environment files match main.
The engine still requires explicit server game-mode configuration.

The independent review found and fixed three P2 implementation gaps:

- `app/game/offline/pooling.py`, `_semantics`: captured candidate contracts were
  omitted, so differing capabilities/configuration could be pooled if their current
  feasible strategy lists happened to coincide. The comparison now includes the
  same semantic candidate fields used by planning compatibility, excluding ranking
  order, utility and domain-specific reputation. A regression failed on the proposal
  and passes after the fix.
- `app/game/pooling_contract.py`, `PoolingContract.check`: imported source lineage
  accepted a missing source applicability entry or a contradictory source context
  ID. Both now reject. Two regression cases failed on the proposal and pass now.
- `app/game/offline/pooling.py`, `fit_pooled_policies`: repeating the optimizer for
  each target did not ensure a single shared mixture in a game with multiple valid
  optima. A controlled solver returning different certified optima reproduced three
  LP calls. Fitting now solves once and validates the same certificate/distribution
  with each target's matrix identity. The regression retains the one-solve assertion.

Additional synthetic regressions cover unequal source sample counts and manual
weighted loss/cost, different frozen histories, unchanged mixtures after changing
target-only development labels, exact sparse thresholds and excluded candidates,
single-domain research rejection, invalid pre/post resource snapshots, retained
costs after drift and propagation of unexpected observer exceptions. A fresh-process
pooled-v2 runtime test blocks all offline imports and optimizer calls while checking
one provider snapshot, one policy draw and two resource observations. Exploratory
test failures from an inconsistent synthetic eligibility flag and a checker double
missing the required BaseVerifier interface were corrected in the new fixtures;
their assertions and existing repository assertions were not weakened.

Before application, a real-environment baseline run on clean main ran
`tests/test_game_research.py tests/test_adaptive_pipeline.py -q -p no:cacheprovider`:
132 passed and four failed. The failures are the three evidence cases already named
in the research protocol, plus
`tests/test_game_research.py::test_cli_unresolved_template_is_read_only_and_reports_digests`.
That test hard-codes `9d21eba...` although the CLI correctly reports actual HEAD
`5b9fae6...`. This baseline failure is retained for its testing owner; no production
revision is falsified and no assertion is changed to get a pass. The two historical
Git-object tests excluded by the proposed archive are included in the actual run.

The initial proposal's focused suite passed 26 cases in this checkout. The expanded
focused suite passed 41 cases after the review fixes. The final affected run was
935 passed and the same four baseline failures, with one existing Starlette
TestClient deprecation warning. No tests were excluded or skipped. Both historical
Git-object checks passed. Exact commands, failures and exclusions are included in the exported manifest and
JUnit report. The checks use the installed local interpreter and dependencies;
there is no import-only SentenceTransformer replacement or test deselection.

These remain implementation checks with synthetic data, not empirical validation.
The single-domain seven-method comparison and grouped uncertainty remain
single-domain. Pooled frozen scoring reports each target separately; a weighted
multi-domain scientific comparison/uncertainty protocol is not supplied. Pooling
requires identical execution/resource contracts and complete target manifests;
zero-observation histories can arise from explicit abstentions but truly absent
target datasets/history are not fabricated. Collection adapters, real weights,
thresholds, dependencies, costs, losses and final-test custody remain project input.

Offline observations attest pre-attempt identities; collectors must pin resources
through collection and preserve any drift externally. Runtime pre/post snapshots
detect observed end-state drift, not transient change-and-return or dishonest
observations. Digests and numeric certificates do not authenticate empirical payoffs,
labels, resource observations or scientific population assumptions. Audit persistence
and adapter/application wiring remain outside this owned patch. No empirical policy,
deployment, production default change or external handoff message was performed.
