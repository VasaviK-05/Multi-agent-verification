# Approved bounded prototype bundle v1

This is a completed engineering package of the existing approved arithmetic50%
and experimental factual25% policies, not another fit, optimizer variant or
activation. Approval is user request `bff23d52-aafc-4be6-8adb-3c7e8f88836c`, bound to
the exact existing artifact/context identities below. All settings and probability
values are unchanged, including zero and tiny values. Semantic equivalence has no
deployed entry; its always-abstaining diagnostic artifact is excluded.

## Package and exact identities

Directory: `build/multitask-prototype42-v1/`.
Distributable archive: `build/multitask-prototype42-v1.zip`.
Bundle ID: `98b8f2654163fe95e84a1b916a94174ddc37aa399429bba94f99890573168d34`.

- Arithmetic artifact `arithmetic/policy.json`:
  `e4981bb78a278f216efb0ece9b79eca8381fbaacdf6315e8bcb4cbc6bbb638f2`.
  Compatibility ID:
  `377f7cd11628734774e81fed0b383e85c764cae08585b035e3b4398a2a1c8ca9`.
- Factual artifact `factual/policy.json` (experimental):
  `c66e137fd64f61222e4a69cf0e025b91bc1d3ae075166743f2c795acd9d7cd79`.
  Compatibility ID:
  `3c5ee90716ad592089eb9be8c77da9b54af255d26d8bafba3561c4e8c38d73e8`.
- Both retain execution/resource identity:
  `e23c6f034a4c660d30433d133be3a197db620abbdf22a78907ef5e3687d45ccb`.
  Full task/reputation/calibration IDs and all file hashes are in `manifest.json`.

The original policy bytes are copied exactly. Each task directory contains an
explicit `episode.json`, frozen `reputation.json`, `costs.json`, exact
`resources.json` expectations and `development-metrics.json`. The root includes
software/source metadata, an external-resource adapter template and integration
README. Every package file is listed/hash-checked; unexpected files reject. No
final labels, raw recordings, model weights, corpus, credentials or machine-specific
private paths are included. Partial/draft packaging directories and private
execution audits remain outside the distributable archive.

## Load and validate

From the compatible repository/runtime (the bundle does not embed application code):

```powershell
.venv/Scripts/python.exe -m app.game.offline.prototype validate --bundle build/multitask-prototype42-v1
```

For an extracted archive, replace the bundle path with that extraction directory.
The loader verifies file hashes, original PolicyArtifact numerical certificates,
episode/context identities, frozen reputation, costs, resource expectations and
all reported strategy probabilities. It does not load external models or attest
their live availability. Synthetic artifacts require an explicit test-only flag.

```python
from app.analysis.task_analyzer import TaskQuestionAnalyzer
from app.game.prototype_bundle import load_prototype

bundle = load_prototype("build/multitask-prototype42-v1")
assert bundle.manifest.bundle_id == "98b8f2654163fe95e84a1b916a94174ddc37aa399429bba94f99890573168d34"
provider = bundle.provider()
router = bundle.router()
analyzer = TaskQuestionAnalyzer()
# Integration supplies a legitimate selector, request, validation ID, caller RNG
# and live resource observer. router.run(...) delegates to existing GameRuntime.
# Nothing is activated or wired into an API by loading this package.
```

To reproduce packaging in a fresh workspace/output location with the preserved
external study inputs, use `python -m scripts.package_multitask_prototype`. The
producer refuses an existing destination. Do not rerun it over the supplied package.
It validates existing calibration consistency and copies artifacts; it never fits,
collects, recalibrates or changes probabilities.

## Scope and reference conditions

Both approved episodes require usable user reference context. No no-reference
episode exists. Absent/blank context fails `task_out_of_scope`; a judgment-list
context cannot satisfy the existing reference prerequisite and fails compatibility.
Reference availability is not a relevance/truth/sufficiency classifier. Evidence's
own prerequisites are not changed.

The bundle uses actual `TaskQuestionAnalyzer` rules and task-isolated histories,
then restricts routing to each task's40 prepared history/development question
identities. No final-test metadata or outcomes are used to expand that scope.
Arithmetic is constructed three-digit additions; factual scope is the prepared
source-snapshot population/currency/area questions. This is not an open-domain
deployment claim. Unseen questions fail `study_scope_mismatch`; new answers or
references even to known questions have no measured performance guarantee.

Semantic equivalence and other unsupported known tasks fail `task_out_of_scope`;
unknown requirements fail `task_unknown`. Changed budget has no compatible route;
changed resources fail `provenance_incompatible`. No fallback borrows another
task's reputation, policy, reference assumption or resource identity.

## Actual selection, not forced verifier use

All14 feasible strategies and both aggregations remain serialized per policy.
All positive-probability plans here have two verifiers. Three verifier types are
materially used across the two policies; that does not mean one request runs three
verifiers, or that every selected verifier is informative in that task.

- Arithmetic: weighted Confidence+Rule probability **0.6060604653198649**;
  weighted Evidence+Rule **0.3939392902356899**; grouped Rule+Semantic
  **2.444444452815835e-7**. Every other strategy has zero probability.
  Rule is selected essentially100%, Confidence60.606%, Evidence39.394%,
  Semantic0.0000244444%. Rule and Confidence provide material informative
  participation. Evidence's selection is on the zero-clean-coverage branch;
  it is not evidence of useful arithmetic checking.
- Factual: weighted Confidence+Evidence probability **2/3**, weighted
  Evidence+Rule **1/3** (actual serialized binary floats preserved). All other
  probabilities are zero. Evidence is selected100%, Confidence66.667%,
  Rule33.333%, Semantic0%. The Rule-containing branch has zero clean coverage.
- Probability assigned to zero-clean-coverage plans is **0.3939392902356899**
  for arithmetic and **0.33333333333333337** for factual. That deliberate
  policy-level abstention remains disclosed, not pruned or renormalized.

The tiny Semantic mass is an unchanged numerical allocation, not evidence of
material usefulness, aggregation superiority or a deployed semantic-equivalence
capability. Its already measured limitations remain documented in prior studies.

## Demonstrated three-outcome behavior and scores

Private replay audit: `build/multitask-prototype42-v1-validation/execution-traces.json`.
It is intentionally outside the package because it contains retained development
reports. Actual analyzer → bounded task router → provider → selected-team public
finalization matches replay in11 representative traces, including every positive
strategy and acceptance/rejection/uncertainty for both tasks. No new models ran.

- Arithmetic Confidence+Rule: `addition-391-635-correct` accepted at signed raw
  score **0.863818529525**, two informative contributors; `addition-307-503-incorrect`
  rejected at **-1**; `addition-307-503-correct` remained uncertain despite score
  **+1**, because the retained Confidence provider-timeout abstention left only
  one informative contributor. This preserves the contributor guard.
- Factual Confidence+Evidence: `AO-correct` accepted at **0.996160417049**,
  `AO-incorrect` rejected at **-0.999925203794**, both with two contributors;
  `AZ-incorrect` remained uncertain at **-0.999859094620** with only one
  informative contributor. A decisive numerical score does not override guards.

Rule's supported arithmetic score is a deterministic correctness bit; Semantic's
score is uncalibrated cosine resemblance to reference; Evidence's score is NLI
class strength; Confidence's score is judgment agreement. Normalization retains
the explicit directional/UNSURE contracts. None is a calibrated probability of
answer correctness. Aggregate scores are signed decision signals, also not
probabilities: strictly greater than+0.55 accepts, strictly less than-0.55 rejects;
ties and the intervening band are uncertain. Prerequisite, achieved-coverage,
informative contributor and execution guards may override a preliminary decision.
Full raw metadata, normalized contributions, team/aggregation, policy IDs, public
reasons and estimated costs are in the private audit.

## Development evidence and limitations

Each task has20 related development groups and40 independently binary-labelled
candidates. Coverage is expected over the fitted distribution/population, not a
request confidence or request-specific routing decision. Abstentions do not change
the correctness labels; zero errors through abstention are not perfect accuracy.

- Arithmetic: clean expected coverage50%, uncertainty50%, FA/FR0, selective risk0
  among decided cases, validation loss0.10, mean estimated cost12846.372147 ms.
  Forced support/rejection coverage57.5757558%, expected FA11.5151506 or
  FR11.5151518 of40; losses0.372727252/0.372727283. Confidence inflation gives
  approximately50% coverage/loss0.100000009; suppression gives zero coverage and
  loss0.2. Worst validation loss **0.372727283**.
- Factual: clean expected coverage25%, uncertainty75%, FA/FR0, selective risk0,
  validation loss0.15, mean cost10677.138030 ms. Forced support/rejection coverage
  31.666667%, expected FA5.333333 or FR7.333333 of40; losses0.27/0.32.
  Confidence inflation retains clean metrics; suppression gives zero coverage/
  loss0.2. Worst validation loss **0.32**.

These validation losses exclude resource penalty. Per-attack uncertainty, selective
risk, reason counts and the separate old cost-inclusive diagnostic are included
in development-metrics.json. All informative verifiers are linked by shared models
and conservative shared-unknown dependencies; one compromise group can affect
them together. No independence, robustness improvement, research superiority or
unseen-question guarantee is established. Timings are summed measured verifier-
attempt wall milliseconds under shared-machine contention, not money or end-to-end
latency. Original full-roster budgets remain21258.335265 ms /15965.046465 ms.

## External requirements and integration-owner handoff

The package is loadable without models. Execution still needs exact compatible
external resources: installed all-MiniLM-L6-v2 embedding and nli-deberta-v3-small
weights, llama3.2:3b local service/model and reviewed service observation, the
isolated57-document corpus/index-v2/observed build receipt, and compatible public
adapter/verifier implementation bytes. Hashes are in resources.json; versions and
source metadata are in runtime-requirements.json. No weights, corpus or index are
implied to be bundled.

The adapter template has placeholders for excluded local snapshot/receipt/service
observation locations, and preserves original relative corpus/index layout that
contributes to configuration identity. A new machine/path/service must satisfy
the existing observer/provenance contract; do not rewrite IDs or relax checks to
claim compatibility. A different bound resource/configuration requires a separate
compatible artifact decision, not silent rebinding. Live resource availability was
not revalidated in this no-inference task.

Integration owner must pin the bundle ID plus compatible source/dependencies,
load through `load_prototype`, supply the actual analyzer, legitimate selector,
caller RNG and live observer, and preserve the explicit scoped/reference-required
episodes and three-outcome finalization. Preserve all probabilities and error/
uncertainty distinctions. Do not wire APIs, activate, expand scope, release final
evaluation, modify thresholds or claim unseen performance without separate
authorization. Factual remains experimental. There is no semantic policy to
activate and no new Semantic investigation or verifier-owner implementation task
was performed here.

## Validation and changed files

Focused package/task/runtime/three-outcome/reliability tests passed130/130. Initial
new synthetic package fixtures lacked the required reference flag; correcting those
fixtures resolved the two failures without weakening the loader. There are no
remaining or reproduced baseline failures. Package corruption, unsafe paths,
unlisted files, private-path scanning, synthetic-production rejection, episode/
cost/resource/reputation mismatches and probability tampering are tested.

Retained execution verifies11 traces and14 safe failures, with zero network or
generation calls, using a **recorded-resource observer simulation**, not new live
resource evidence. Original arithmetic/capital/reliability-first artifacts reload
with their historical IDs, and seven stored preservation hashes for historical
policies, calibration, approval and recordings still match. Original selected
policies match bundled bytes. Extracted-ZIP validation checks the documented layout.

Exact current-task changed/new files:

```text
app/game/prototype_bundle.py
app/game/offline/prototype.py
scripts/package_multitask_prototype.py
scripts/validate_multitask_prototype.py
tests/test_game_prototype_bundle.py
docs/multitask_prototype_bundle.md
docs/game_policy_build.md
```

No verifier/retrieval/generation, DB/API/frontend or unrelated orchestration changes;
no final payload access, inference, fit, recalibration, production writes, commits,
pushes, merges or activation. Previous dirty work and historical artifacts remain.

Private execution audit reproduction (fresh audit destination only):

```powershell
.venv/Scripts/python.exe -m scripts.validate_multitask_prototype
.venv/Scripts/python.exe -m pytest tests/test_game_prototype_bundle.py tests/test_game_task_conditioning.py tests/test_game_runtime.py tests/test_game_three_outcomes.py tests/test_game_reliability_first.py -q
git diff --check
```
