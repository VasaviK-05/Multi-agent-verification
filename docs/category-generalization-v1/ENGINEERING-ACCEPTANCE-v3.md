# Category runtime engineering review — 19 November 2026

**Category engineering tests pass; the full legacy suite is not clean. No new
question distribution is empirically certified and deployment is inactive.**

## Git isolation

Original checkout: `codex/evidence-poisoning-phase1`, commit
`e38a96d367610065e3679ec22fa162cfcc94daf5`, with unrelated dirty/untracked work.
It was not checked out, reset, stashed, merged or used as the feature-branch base.
The user explicitly approved `codex/category-generalization-v3`; it is isolated at
`/private/tmp/category-generalization-v3`, based on fetched main
`b3150012d7097729cd676317006a13d577585c82`. Only category source, tests and docs
were transferred. No evidence-poisoning/Experiment-1 research commits were copied.

The original 661-file inventory remains intact. A separate 24-entry main-base
transition records upstream source changes and omitted unrelated branch files;
no artifact/resource/policy differences were permitted. A separate five-file
source overlay records only the additive game contract integration. Neither is a
replacement baseline. Historical artifact directories and the three 69-question
registration inventories remain byte-identical. The five tracked application
changes are `artifacts.py`, `execution_contract.py`, `finalization.py`,
`offline/evaluation.py`, and `research/readiness.py`, all under `app/game/`.
No API, database, orchestrator, frontend, generator or verifier implementation was
edited. No dependency manifest, decision threshold, old probability or old
coverage rule was edited.

## Root cause and policy reuse correction

The frozen flexible package rejects `What is 4 + 4?` at its exact question
allowlist before dispatch. It also matches routes on an exact surface difficulty
score. The underlying `PlanningContext.compatibility_id` intentionally omits the
raw score, while retaining minimum team size, requirement signature, candidate
eligibility, analyzer version, reputation, dependencies, execution configuration,
costs and budget. Thus two inputs with different surface scores can have exactly
the same genuine policy compatibility ID.

The earlier `CategoryInputContract` v2 additionally put its hash in task identity.
That remains useful for a genuinely NEW contract, including completed-consistency
coverage, but requiring it for every unseen instance would unnecessarily require
new artifacts. This part of the initial implementation/14-profile proposal is
superseded by the user's compatibility clarification.

New `reusable_policy.py` provides `ReusablePolicyScope` v1 and
`ReusablePolicyGameRuntime`. The separately versioned installation scope pins the
existing artifact ID, compatibility ID and original analyzer rules. It does NOT
change the policy's task identity. It classifies fresh questions with the original
supported analyzer, checks task/reference/parser prerequisites, then delegates to
unchanged `GameRuntime` for full frozen-selector/context recapture, compatible
policy retrieval, resource observation, budget checks, original minimax sampling,
complete execution and guarded finalization. It never calls a fitter or greedy
selection in place of the policy. Per-question identities are execution/audit
identities, not fitting/lookup keys. Multiple matching compatible scopes fail
closed. Genuinely changed requirements/resources/configurations still reject.

The existing arithmetic artifact is
`cf4507400b26f79ab63366ab64b25ef779870fb85f8c33f7aa60a735a4762477`, policy
`c6a1f9c14bf2337aa3202124a2ed087616d48a46d70f56e7f37aba0a2a446e14`, compatibility
`5f217f601b87ab4d2889b59ca9bda07d8a07a6774d074625f8b01c2050cb736d`.
Its Rule/reputation-weighted probability remains exactly 1, with all other
original strategy probabilities retained. Tests show seen `What is 328 + 536?`,
unseen `What is 4 + 4?`, wrong candidate `9`, and `Calculate 4 + 4.` use this SAME
artifact/policy. The last wording has a different surface difficulty score and
still satisfies the actual context contract. No old policy JSON is rewritten.
The artifact still requires reference presence: a bare question with no context
is legitimately incompatible with this particular historical artifact. No
reference is fabricated or taken from held-out labels to make it pass.

Fresh mock verifiers log each new question, answer and context and construct a
new report for that invocation. They do not read development report recordings.
Tests cover `/validate` and `/generate-and-validate` through the existing route,
service and orchestrator. Generation and persistence are explicitly mocked; no
real generator, DB connection or native verifier is run in these acceptance
checks. Mock generation changes the same unseen question's answer from `8` to `9`
and the public decision changes from pass to fail without changing its policy.
These are engineering tests, not native execution or new empirical measurements.

Existing factual and bounded-reference artifacts are also reused with fresh mock
reports. The real reference mixture (Semantic 1/6, Semantic+Confidence 5/6) is
unchanged. Its neutral-reputation singleton branch remains uncertain. Different
team sizes are not forced to acquire positive mass. Evidence quality, actual
corpus/index identity, native model readiness and actual-instance attestation are
still execution obligations; a mock resource fixture is not a live provenance
proof. Scientific support beyond the old evaluation is explicitly labeled
`historical_evaluation_unchanged`, not automatically certified by routing success.

`ExactFirstCategoryDispatcher` preserves every historical exact route, including
errors, unavailable outcomes and reference variations. No fallback from such a
route is introduced. The owned adapter forwards main's optional execution journal
and passes the unchanged orchestrator runtime type boundary. It is never selected
by a new setting or activated by this work.

## Completed Confidence consistency assessment

`consistency_assessment.py` defines `native_consistency_assessment_v1`. It checks
native-shaped provider source, sample/model/temperature/count metadata, matching
sample and judgment labels/counts, stable directional majority, decision/passed/
score consistency and nonempty claim. Missing/malformed/zero-confidence/abstaining
or failed assessment cannot establish achieved consistency. Report metadata is
not an authenticity proof: exact model/prompt/service/implementation/sampling
resources must separately pass the engine's attestation.

The new opt-in `offline_public_decision_v5` + `game_assessment_output_v3` binds an
explicit assessment contract into context compatibility. Old v1-v4 contracts omit
the new optional field when serialized and retain their prior semantics. A v5
contract cannot be relabeled v4 or stripped of its assessment contract. Existing
global `app/decision/coverage.py` is unchanged.

Only this new game contract can add achieved `consistency`. It does not add
arithmetic, factual or semantic correctness. Stable but wrong model outputs can
complete a consistency assessment. Existing reputation and dependency aggregation
remain authoritative; no reputation is increased in production. Invalid active
Confidence assessments cannot satisfy informative-contributor minima and force
uncertainty; duplicate/conflicting report identities remain rejected by the
existing canonical-report guards. Failed/unavailable selected members do not
cause early termination or fallback.

A v5 consistency policy requires a genuinely compatible artifact because its
execution/output contract changes. This is distinct from refitting an unchanged
arithmetic policy merely for a new question. No such v5 policy has been fitted.
Standalone `evidence_retrieval` remains explicitly unsupported as a separate
achieved obligation: current native evidence outputs support qualified
`direct_fact`, not a separately specified retrieval-only completion certificate.
There is no new alias from corpus presence to achieved factual coverage.

## Working isolated environment

The initial unconstrained install succeeded at metadata level but failed imports:
Torch 2.2.2 versus Transformers 5.23.0 requiring Torch >=2.6, plus NumPy 2.5.5 ABI
warnings. That environment remains separate and was not repaired by arbitrary
version changes. After explicit user review, ONE controlled second install used
publisher metadata and matching Intel-Mac binary wheels. One additionally approved
missing dependency, psycopg2-binary 2.9.10, was verified to have the exact
`cp312-cp312-macosx_12_0_x86_64` wheel and installed with binary-only/no-deps flags.
It was never used for a database connection.

Working environment: `/private/tmp/category-engineering-v4`, Python **3.12.0**,
Intel x86_64 macOS. Versions: Torch **2.2.2**, NumPy **1.26.4**, Transformers
**4.49.0**, Sentence Transformers **3.4.1**, tokenizers **0.21.0**, HF Hub
**0.29.3**, SciPy **1.15.2**, FAISS CPU **1.10.0**, pytest **8.3.5**, pydantic
**2.11.3**, FastAPI **0.115.11**, Starlette **0.46.1**, httpx **0.28.1**, and
psycopg2-binary **2.9.10**. `pip check` and game/model-library import smoke tests
pass. All resolved packages are in `validation/environment-v4.freeze.txt`.

Rationale: [Sentence Transformers 3.4.1 metadata](https://pypi.org/pypi/sentence-transformers/3.4.1/json)
requires Transformers >=4.41,<5 and Torch >=1.11. [Transformers 4.49.0 metadata](https://pypi.org/pypi/transformers/4.49.0/json)
accepts the selected Hub/tokenizers versions. [Torch 2.2.2](https://pypi.org/pypi/torch/2.2.2/json)
and [NumPy 1.26.4](https://pypi.org/pypi/numpy/1.26.4/json) publish Python 3.12
Intel-Mac wheels; the NumPy 1.x choice avoids the observed Torch ABI mismatch.
SciPy/FAISS constraints also admit NumPy 1.26.4. Full primary metadata/wheel review
is retained in `validation/reviewed-dependencies-v4.json`. This environment is for
mock/engineering tests; it does not establish native historical model equivalence.

## Validation results and limits

Final count receipts are in `validation/TEST-RESULTS-v3.json`: **120 category tests passed** (zero failures/skips); **756 core tests passed, one pre-existing failure, 17 native cases deselected**. Targeted clean-base reproduction: seven pre-existing failures and one pass. Category tests cover
all four complete engine paths, one/two/three/four-member teams, both aggregations,
requirements, missing/changed references, unsupported input, wrong answers/formats,
missing/incompatible policies, budget infeasibility, frozen reputation, resource
drift, failure/abstention, contributor/coverage enforcement, duplicate identities,
complete teams, journal propagation and orchestrator/API adapters.

Dynamic actual-router projections compare **69 questions x 3 contexts = 207**,
before/after: policy/artifact/compatibility IDs, complete strategies and
probabilities, contracts, costs/budgets, resources, reference condition, reputation
snapshot, classifications and unavailable reasons. Before/after records are equal.
They are not native execution results. The before capture was preserved; no
baseline was regenerated to conceal a difference.

Known failures are disclosed, not weakened or fixed in teammate code. The selected
core run has one pre-existing Python 3.12 deep-JSON expectation failure: parser
returns `invalid_schema` where the test expects `malformed_json`. Six legacy API
fixtures are also stale against main's orchestrator/persistence/lifespan interface.
Raw logs and before/after route captures are archived losslessly as `.gz`; `validation/RAW-EVIDENCE-ARCHIVES-v3.json` records both raw and archive hashes. Use `gzip -dc <archive>` to inspect original bytes. All seven reproduce on untouched main `b315001` in the same environment. Their
source files are unchanged by this branch. Native Rule/live-service cases are
explicitly deselected to respect the no-native-execution authorization, not
reported as passing. New API tests mock the current interfaces correctly.

The first broad run used a profiler-only native guard that disabled itself after
an intercepted exception. Its log is retained but is NOT a reliable zero-native-
Rule-call receipt; any deterministic Rule calls after that point were not
accounted. No model inference/generation results are claimed from it. Subsequent
acceptance runs use persistent method-level prohibitions, thread profiling,
network audit denial and a psycopg2-connect prohibition. The new fixtures execute
mock verifiers only; native ML model access and Ollama requests are blocked.
No weight download, index rebuild, service change, empirical fitting/collection,
production environment change, merge or deployment activation occurred.

## Certification readiness

| Category | Contract | Runtime-tested | Achieved coverage validated | New policy fitted | Certified |
|---|---|---|---|---|---|
| Rule | Existing arithmetic parser/output; v4 plus reuse scope | Yes, fresh mocks and old fitted policy through API | Yes, synthetic output contract | No | No new distribution certification |
| Evidence | Frozen corpus/index; qualified direct_fact output | Yes, fresh mocks and existing fitted policy | Yes, synthetic evidence/abstention gates | No | No new distribution certification |
| Semantic | Legitimate reference and original comparison semantics | Yes, mocks and both branches of real historical mixture | Yes, comparison only; contradictions remain a documented limitation | No | No new distribution certification |
| Confidence | New game-only completed native assessment v1 / execution v5 | Yes, synthetic reports including failure/low agreement and shared groups | Yes, consistency only, never truth | No | No |
| Multi-verifier | Existing feasible subsets, original mixtures, full execution | Yes, sizes 1–4 / both aggregations, synthetic | Yes, existing contributors/dependencies/coverage | No | No new distribution certification |

## Revised bounded pilot (not started)

Four scopes are a useful initial target: arithmetic, corpus-backed factual,
reference comparison and standalone consistency. Fourteen separately collected
profiles are NOT required merely to test new wordings. Reuse existing fitted
policies where task/context is genuinely compatible; independent evaluation can
assess their broader distribution WITHOUT refitting. Only changed contracts,
resources, budgets or actual task classes demand new compatible artifacts.
Optional minimum-team/reference variants can replay the SAME eligible per-case
recordings when the declared collection/dependency contract permits it; do not
repeat native Confidence generations just to evaluate another team/aggregation.
Do not share a generated judgment trace across different candidate answers unless
that separate caching/labeling contract has been reviewed; current provider calls
remain per candidate.

Recommend a **24-case development-only diagnostic pilot**: six cases per scope.
Semantic cases include two supported paraphrases plus changed numbers, negation,
entities and relationships. Other scopes include correct/incorrect and
uncertain/unsupported/resource failures. At most 18 reference-absent cases x three
eligible verifiers + six reference-present cases x four = **78 verifier attempts**,
and at most 24 x five = **120 Ollama generations**, no retries, proposed two-hour
outer wall-clock ceiling. This is a ceiling, not a completed manifest, execution
authorization, sufficient scientific sample or a completion guarantee. At 60
seconds/generation, generation timeout bounds alone can consume two hours.
Resource initialization and Evidence/Semantic latency are additional; stop and
retain incomplete custody rather than fabricate a normal completed team.

Reserve independent history/development/untouched held-out groups separately before
any fitting/evaluation. Pilot data must not become untouched test data. Required
remaining approvals/evidence: source and resource locks, explicit per-case
manifest, real instance attestation, independent labels and custody, history for
new task/contract classes, calibrated budgets, baseline metrics and independently
reviewed applicability. The unchanged fitted arithmetic policy does not need a
new fit for every fresh arithmetic instance. No pilot ran.
