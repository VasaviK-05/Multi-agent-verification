# Compound study 36: primary integration handoff

This document accompanies the versioned [36-group amendment](../../../compound-study-36-v1/amendment.json).
The original [blocked 48-group preparation](../../../compound-empirical-v2/preparation)
is preserved unchanged. The amended experiment uses 12 history, 12 development
and 12 reserved-test entities, with four variants and exactly two planned calls
per answer. Its ceiling is 144 examples / 288 Evidence/Rule attempts and zero
Confidence generations. This is a source-known exploratory study with limited
precision, not unseen-source or broad difficulty generalization.

## Final status and result

- Implementation complete for the bounded protocol: **yes**.
- Empirical compound policy created: **no**, fitting is infeasible.
- Held-out evaluation complete: **no**; the12 reserved groups /48 examples were not collected because there is no feasible candidate.
- Offline handoff ready: **yes**. Live API integration: **pending**, with compound routing unavailable.
- Actual study attempts: **192 of288** (96 history +96 development). Zero Confidence generations, retries, downloads or index rebuilds.

The [empirical fit result](../../../compound-study-36-v1/candidate/infeasible.json)
contains the matrix, infeasibility result and all development decisions. Both
aggregation strategies decide43/48 examples: **89.5833%**, below the unchanged90%
target. Their identical coverage means no mixture can meet the constraint.
Rounding up is not permitted. One additional decided example would be needed,
but no examples were replaced and no threshold or coverage requirement was changed.

The [primary analysis](../../public-audit/artifacts/compound-study-36-v1/analysis-v2/results.json)
is explicitly **unfitted / non-deployable**. Both fixed aggregation plans tie.
There are12 correct accepts,31 correct rejects and5 uncertainties: zero false
acceptances/rejections among43 decisions, selective risk0, decision loss
0.0208333. Uncertainty is10.4167%. Resource-weighted mean loss is0.0212294.
The factual component decides38/48 (79.1667%); arithmetic decides48/48 (100%).
Both component selective risks are0 on their decided cases.

Entity-cluster95% percentile bootstrap intervals are83.3333–95.8333% for whole
coverage and0.0083333–0.0333333 for decision loss (12 clusters, four variants each,
seed1102,1000 replicates). These descriptive small-sample intervals do not change
the predeclared empirical90% eligibility gate or establish unseen-source risk.
There are **no reserved-test performance results**.

Training-only estimated call costs are Evidence **84.070561 ms** and Rule
**0.122528 ms**; the plan budget is **84.193090 ms**. These are verifier-call timer
measurements, excluding model initialization and resource-attestation overhead,
not end-to-end service latency guarantees. No test timing entered calibration.

Raw directional rejection is not sufficient for the declared public decision:

| Entity | Wrong-base factual score | Actual blocker |
|---|---:|---|
| Armenia (AM) |0.233615|Cited contradiction row is labelled entailment; confidence also below threshold|
| Paraguay (PY)|0.123644|Same coverage/threshold blockers|
| Czechia (CZ)|0.352640|Same coverage/threshold blockers|
| Suriname (SR)|0.478680|Contradiction coverage exists; confidence below threshold|
| Nigeria (NG)|0.092088|Cited contradiction row is labelled entailment; confidence also below threshold|

All five cases are wrong-base / internally-correct-math variants. Rule correctly
passes the calculation on the submitted wrong base; the factual judgment remains
unqualified, so the whole answer is uncertain rather than accepted. The same
factual uncertainty appears in their both-wrong variants, but a qualified
arithmetic rejection safely rejects those whole answers. Thus there are10 factual
component uncertainties and5 whole-answer uncertainties. Contributor minima are
met: these failures are not missing verifiers, cold history, budget exclusions or
upstream execution failures.

The deciding evidence contains the correct source value; this is not evidence
that the source fact is absent from the index. Verifier-owner review should use
the complete raw reports and exact inputs in the primary analysis. Under the
current NLI-based contract, public uncertainty is the expected safe behavior.
Whether numeric-mismatch reasoning should have its own consistent, versioned
output/coverage contract is future owner work; do not flip scores, fabricate NLI
confidence or lower thresholds to export this study. Preserve all five regression
cases and require separately approved development validation for any new contract.

Report-level simulated attacks on the fixed plan (not a fitted policy):

| Action | Whole coverage | False accepts | False rejects | Decision loss |
|---|---:|---:|---:|---:|
|Clean|89.5833%|0|0|0.0208333|
|Forced support|100%|36|0|0.75|
|Forced rejection|100%|0|12|0.25|
|Confidence inflation|91.6667%|0|0|0.0166667|
|Suppression|0%|0|0|0.2|

Confidence inflation is an attack simulation, not an alternative clean calibration.
No synthetic attack outcome is counted as an upstream failure or used as a
replacement clean observation. There is no demonstrated strategic benefit beyond
fixed Evidence+Rule, and no qualifying fixed plan meets the deployment target.

### Exact identities and files

- Study: `86d17f7baa56a0a7c3a1ffcfb4b5914aba643fa59c99d17e64f1a7f1f00431f6`.
- Actual joint development matrix: `4d7126a8d652a35045b2682e222e0fd767fef43a5b8b6d9d9e4f5cc074fe90c9`.
- Unfitted development contract: `284e7f29545d2d1cb26f783ee6d241a2d7224de5a5ba35afe2fbb7d60ddeb5a7`.
- Full actual resource manifest: `e23c6f034a4c660d30433d133be3a197db620abbdf22a78907ef5e3687d45ccb`.
- Verified E/R component resource projection: `310364dae8d9d6c001622d4bbe1866ca0646fb8f50c9c50a022e05f5353688c1`.
- No empirical compound policy ID, feasible-policy certificate or selected-candidate freeze exists.

See the [unfitted contract](../../../compound-study-36-v1/analysis-v2/unfitted-contract.json),
[history-only contexts](../../../compound-study-36-v1/analysis-v2),
[actual records and journals](../../../compound-study-36-v1),
[external-resource inventory](../../../compound-study-36-v1/external-resources.json),
and [publication inventory](../../../compound-study-36-v1/publication-inventory.json).
The initial derived analysis is retained; `analysis-v2` corrects display-only
component cost fields and exposes computed strategy IDs without changing raw
records, the matrix, fitting or decisions.

### Engine integration-readiness table

A = synthetic software evidence; B = actual recorded/live output evidence;
C = not exercised or still blocked. These states are not interchangeable.

| Engine | A: software | B: empirical/recorded | C: pending/blocked |
|---|---|---|---|
|Analyzer|finite grammar, malformed input and routing tests|actual component request analyses and owned-router replay; compound signature recognizes direct_fact + arithmetic|broad domain/difficulty adaptation not established|
|Selector / enumerator|sizes1–4 and compatibility fixtures|two aggregation strategies, one E-fact/R-calculation team; no qualifying clean-coverage strategy|no real fitted compound selection; no third useful verifier|
|Reputation|history-only and duplicate-input accounting|E successes24/failures0, Beta(25,1); R successes48/failures0, Beta(49,1); no test updates|not calibrated answer-correctness probabilities|
|Game solver / policy|feasible and infeasible certificate fixtures|empirical matrix; both rows43/48 coverage; any mixture is below90%; infeasibility precheck exercised|no empirical compound policy, probabilities, or feasible numerical certificate|
|Runtime|joint policy sampling and complete-team execution fixtures|actual fixed-plan collection2 calls/answer; actual singleton policies replayed on retained reports|fitted compound-policy runtime and live API not exercised|
|Component adapter|decimals, duplicate fields, wrong-base propagation|92 native calls use submitted base/derived; no gold substitution; arithmetic not sent to NLI|arbitrary prose, other operations and malformed live API requests unsupported/unexercised|
|Decision engine|independent component guards and qualified rejection tests|development whole43/48 decided; fact38/48, math48/48; five wrong-base/math-correct whole uncertainties|held-out evaluation not run; verifier-output contract review needed|
|Resource observer|mismatch and optional active-instance-hook tests|local/live readiness; native factory provenance; pre/post checks match full manifest; no drift|generic API active-instance attestation and relocation integration pending; native observer has no snapshot_for hook|
|Early termination|full-team and prefix-rejection tests|every actual answer had both scheduled calls; no adaptive stopping/expansion|live API game-mode wiring pending; non-game stopping rules untouched|

The [machine-readable table](../../../compound-study-36-v1/integration-readiness.json)
links each claim to concrete evidence. Unit tests alone do not justify “all engines work.”

### Routed teams and acceptance evidence

The [portable acceptance replay](../../../compound-study-36-v1/acceptance-replay/routing.json)
uses real owned routing and retained empirical reports:

- Arithmetic → existing Rule singleton policy, one replayed call, passed.
- Factual → existing Evidence singleton policy, one replayed call, passed.
- Supported compound → `missing_policy`; no qualifying compound policy exists.
- Unsupported operation → `unsupported_category`. Deliberately incompatible resource
  observation → `provenance_incompatible`, with no verifier call.

Real policy selection of **one** is demonstrated. A fixed pair made the actual
study calls, but real empirical policy selection of **two** was **not achieved**.
Real policy selection of **three** was not demonstrated. Larger-team fixtures are
software evidence only. No additional live calls were used for replay.

## Implementation and ownership

The worktree is on `codex/flexible-verifier-teams`, based on
`0b3595ef965d196f93916d10999c7fae63daf7af`. The resource-compatible collection
checkout remains at `2c9f697439d1d1c2ed7c0a92645848c0f07f7e3f`; its existing dirty
work is not part of this publication. Exact inventories and hashes accompany the
study artifacts. No commit, push, merge or API activation is authorized here.

The amendment adds explicitly validated `PartitionSizes` configurations to
[`app/game/offline/compound.py`](../../../../app/game/offline/compound.py). The original
48-group design remains the default, and an explicit amended configuration uses
a distinct study version. Existing artifacts are not reinterpreted. The bridge
validates the version, partition sizes, entity counts and actual call assignments.
The existing producer, V2 adapter, collector, recovery journals, history construction,
solver and component finalization are reused.

One audit-only correction changes successful policy-mediated execution from the
inherited `diagnostic` selection tag to `selected`, preserving failure tags. The
[original source snapshot and correction record](../../../compound-study-36-v1/audit-label-correction.json)
are retained. It does not change inputs, decision semantics, resources, thresholds
or research settings, and did not cause an inference retry.

## Inputs, labels and scope

The [frozen inputs](../../public-audit/artifacts/compound-study-36-v1/preparation-seal.json) bind
the source manifest, partition assignments, descriptor catalog, all answer
variants, loss, .55 decision threshold, 90% clean-development coverage target,
history rule, dependencies, attacks and budget rule. Partition ordering uses the
predeclared `compound-study-v2` seed tag. Entity-cluster bootstrap uses seed 1102
and 1,000 replicates. A group is an entity, not a measure/increment/variant.
Identical component questions cannot leak across partitions under different names.

The independent labels use retained GeoNames population records and the retained
countries snapshot's area values. Whole-answer correctness requires both the
base fact and calculation to be correct. Wrong-base/internally-correct-math is an
explicit negative whole-answer variant and a positive arithmetic-component label.
No labels or true base values are inserted into verifier inputs. All actual
compound references are `None`; Evidence retrieves the configured corpus.

The opt-in grammar is:

```text
What is the <area|population> of <catalog entity>, and what is that <same measure> plus <plain decimal increment>[ square kilometres]? Give both values.
```

Area requires `square kilometres`; population omits that unit. Entity/measure
pairs must be in the explicit finite catalog. Answer JSON has exactly two
decimal-string fields:

```json
{"base":"17818","derived":"17828"}
```

Names are bounded source descriptors. Numbers have at most 15 integer digits and
six fractional digits, with no exponent notation. Duplicate, missing, extra,
nonfinite, boolean or numeric-JSON fields and arbitrary compound prose fail closed.
Only addition is supported; this is not a general compound-language parser.

Stable component IDs are `base_fact` and `derived_sum`. Evidence sees a factual
question and a sentence containing the **submitted** base. Rule sees
`What is <submitted base> + <question increment>?` and the submitted derived
field. The dependency is preserved even when the base is wrong. Derived arithmetic
is not sent to factual NLI as a source fact. V1 two-question behavior remains separate.

## Decision and game responsibilities

History alone determines task/component-specific reputation. Identical bound
checks are deduplicated for history observations; every actual call still has its
own retained result and timing. Mean history/development attempt times determine
per-call cost; test times do not update cost or reputation. The primary budget is
the sum of the two component means, fixed as a rule before collection.

The only supported distinct team is Evidence-for-fact plus Rule-for-calculation.
The two aggregation strategies do not represent different teams. Semantic does
not cover either required check; Confidence generation is outside this study.
Singleton compound plans are infeasible, and no comparable greedy executor or
empirical triple is invented. The baseline is the development-best fixed complete
component plan under matching contracts and coverage constraints.

The minimax primary objective is worst-case validation loss at unchanged clean
coverage. Both legitimate strategies have identical planned calls/cost, so the
secondary cost objective is constant. Resource-weighted loss is also reported
using the declared original loss. Any fit infeasibility must remain a result,
not trigger lowered coverage, altered penalties or forced export.

Components use the existing decision engine's coverage, threshold, reputation,
informative-contributor and execution-failure guards separately. Acceptance needs
every required component to pass. A qualified failure cannot be averaged away by
support for an unrelated component. Missing evidence remains uncertainty. Actual
execution failures and resource drift retain their defined uncertainty overrides.
Contributor counts are distinct influential verifier identities, not independent
failure paths. The declared shared-unknown compromise group can corrupt both
selected verifiers together. Simulated report corruption is not a real upstream
failure experiment.

Game execution completes the selected plan with early termination disabled. There
is no adaptive expansion, team-size quota or easy→one / hard→three rule. Atomic
and compound routing keys differ in question requirements; questions sharing a
supported signature receive the same strategy distribution. Sampling within that
distribution is random selection, not additional question adaptation.

## Loading and runnable entry points

Producer commands are in [`scripts/compound_study.py`](../../../../scripts/compound_study.py):

```text
python -m scripts.compound_study prepare --design amended36 --audit artifacts/compound-empirical-v2/audit --output <new-preparation>
python -m scripts.compound_study collect --study <preparation> --source <compatible-resource-root> --role history --output <new-history>
python -m scripts.compound_study collect --study <preparation> --source <compatible-resource-root> --role development --output <new-development>
python -m scripts.compound_study fit --study <preparation> --history <history> --development <development> --output <new-candidate>
python -m scripts.compound_study collect --study <preparation> --source <compatible-resource-root> --role final_test --frozen <candidate> --output <new-test>
python -m scripts.compound_study evaluate --frozen <candidate> --test <test> --output <new-evaluation>
```

These are reproduction commands, not permission to repeat this study's calls.
Existing output directories cannot be overwritten. Resume uses a new directory
and `--resume-from`, reuses completed outcomes, and rejects ambiguous in-flight
starts rather than retrying them. Preserve the initial journals and freezes.

Deployment artifacts load independently of a local model cache:

```python
from pathlib import Path
from app.game.component_execution import ComponentPolicy

root = Path("artifacts/compound-study-36-v1")
policy = ComponentPolicy.model_validate_json(
    (root / "candidate/policy.json").read_text(encoding="utf-8")
)
```

**There is no `candidate/policy.json` in this result.** The example above is a loading interface for a future feasible export, not a claim this study produced one. An empirical policy is usable only if that export exists and validates. The
owned registry entry is `(policy.contract.question_signature,
policy.contract.budget, True, policy)` in
`QuestionPolicyConfiguration.component_entries`. Frozen atomic artifacts use
`configuration_from_atomic_artifacts`. The executor is
`configuration.router().run(selector, request, validation_id,
provider=atomic_provider, rng=rng, resource_observer=trusted_observer)`.
The request exposes `question`, `answer`, `context`. Configuration and RNG belong
to the server, not the request body. No caller-supplied policy ID selects a policy.

The portable acceptance command is
[`scripts/replay_compound_study_36.py`](../../../../scripts/replay_compound_study_36.py):

```text
python -m scripts.replay_compound_study_36 --study-root artifacts/compound-study-36-v1 --output <new-replay-directory>
```

It reuses actual retained reports and resource observations, makes zero new live
calls, and uses an explicit offline allowlist. It is not an API activation or a
claim about currently active instances. Live use must replace replay interfaces
with the approved actual verifier factory and trusted resource observer.

## Resources, migration and owner work

The full actual resource identity is
`e23c6f034a4c660d30433d133be3a197db620abbdf22a78907ef5e3687d45ccb`.
Constituent E/R contexts use an explicitly verified resource projection; this is
a scope ID, not a separate observed live installation. Every projected entry must
match the full factory observation. No unused verifier costs are guessed.

Local and live readiness are retained in the study's `readiness/` directory.
Factory provenance records assigned implementation classes and whether active
instance attestation is available. File/service checks must not be represented
as proof that unrelated API-selected objects use those resources. Do not claim
all three categories work in one live installation without that instance binding.

External resources excluded from Git publication include model weights/tokenizer
caches, the FAISS/index directory, the local Ollama installation/model, the virtual
environment, DB/user data, credentials and unrelated original-checkout changes.
The embedding snapshot is `sentence-transformers/all-MiniLM-L6-v2` revision
`1110a243fdf4706b3f48f1d95db1a4f5529b4d41`; NLI is
`cross-encoder/nli-deberta-v3-small` revision
`fa2804872c3b4bd748f38c0185cc85775361e735`. Obtain exact approved snapshots and
validate complete directory digests against the retained preflight, not hub aliases.
No downloads were performed for this task. Ollama is a metadata-attested legacy
factory dependency; its presence does not authorize Confidence generations.

The unchanged corpus and independent raw inputs, revision and license notices
are copied under the study's `portable-inputs/`, with hashes. Source URLs are
GeoNames countryInfo and the pinned `mledoze/countries` repository. A newly fetched
mutable countryInfo file may not match the archived snapshot; use the archived
bytes or obtain an exact matching copy from the custodian. These archive copies
do not change the configured corpus/index. Keep source notices with publication.

Canonical original absolute paths in frozen audit manifests are retained as
provenance. Do not rewrite them or expected hashes to make relocation appear
compatible. Portable policy loading and report replay use repository-relative
artifacts; full original-environment producer/audit reload additionally needs its
raw-material and code-location references resolved and hash-validated.

The separate fetched resource-relocation branch was last inspected at `b03ace7`
(`codex/game-resource-relocation-20261102`). No merge was performed. Reconcile its
active-instance `snapshot_for(selector)` and verified index-relocation machinery
with both atomic and component execution gates. Component execution already
honors the optional active-instance hook but requires exact full-manifest equality;
it does not silently authorize relocation. Only a validated, properly bound
index-only exception may be accepted under that branch's proof rules. Other
implementation/configuration mismatches require their own validated transfer or
evaluation; replacing expected digests is not a correction.

The API owner must wire the explicit registry/observer, retain the prototype's
existing outer scope restrictions, define request/response and error presentation,
and complete active-instance and relocation acceptance checks before activation.
The frontend owner must render the structured answer schema, selected team,
component coverage and uncertainty/failure reasons. DB persistence/audit migration
belongs to its owner. No API/frontend/DB schema or teammate verifier algorithm was
edited here, and reserved-test replay does not broaden deployed scope.

Expected negative results include `unsupported_category`, `missing_policy`,
`incompatible_policy`, `answer_binding`, and resource/provenance incompatibility.
Structured numerical rejection differs from evidence unavailability. Preserve
per-component states/reasons and policy/resource IDs in API audit output; do not
flatten them into a single averaged score. Missing reference/new difference-rule
policies and unsupported mixed operations must not fall back to another category.

## Publication and acceptance responsibilities

The [publication inventory](../../../compound-study-36-v1/publication-inventory.json)
contains repository-relative owned source/test/docs and artifact paths with hashes.
It also identifies external resources and excludes `local-custody/` (ignored by the
study-local `.gitignore`). That local custodian archive retains the original
execution source tree, including unrelated uncommitted owner work, for exact
application-source-digest reproduction. Do not publish that archive without owner
review; retain its digest and custody record. No original source files were edited
when making the archive. The portable policy/report replay does not need that
archive or model weights.

Acceptance for this handoff is to reproduce the negative fitting result and safe
missing-policy routing, not to activate an unfitted pair. API/frontend/DB owners
should review the versioned data shapes and resource reconciliation work, preserve
all old policy identifiers, and keep the current deployed scope guard. A future
qualified compound policy needs a separately approved correction/study; do not
consume the untouched reserved outcomes for ad hoc debugging or retuning.

Exact analytical context IDs (not deployable policy contexts):

- `base_fact`: `b8fd7cd3bcc113748a36c1e2abef93c5db56f011119d244b4d2461075990c521`.
- `derived_sum`: `b4975a9064d2c61e0506737c286be32dbc1a555c9a0d7fb14eb6f36d70989fad`.

See [artifact identities](../../../compound-study-36-v1/artifact-identities.json) and the [public file hashes](../../../compound-study-36-v1/file-manifest.json).
