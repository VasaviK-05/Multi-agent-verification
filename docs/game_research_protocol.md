# Stage 5A research protocol and readiness

This stage supplies an offline comparison harness and a preregistration contract.
It supplies no empirical policy, datasets, calibrated penalties, results, novelty
claim or superiority claim. Synthetic tests check implementation arithmetic only.
No production module, verifier, retrieval, database, frontend or default is changed.
Baseline remains the default; server configuration must explicitly enable game mode.

## Verified base and ownership

`vasavi/game-research-evaluation` starts from fetched main
`9d21eba9d3ac823b0ebb6c90195cff524db55253`. Main had no newer changes and its tree
matched reviewed Stage 4 `3dce126cc596dabc108e9cefe573aae4cb0764ac` exactly. The
starting tree/index were clean, with no operation in progress or applicable AGENTS.md.
Version 1, Stage 1–4 documents, actual contracts/replay/artifacts/metrics, achieved
coverage and existing evaluation modules were inspected.

Changes are restricted to these paths (nine new files and one narrow existing-file edit):

- `app/game/offline/attacks.py`: shared pure directional adapter-mapping validation;
  existing attack behavior, normalization and versions are preserved.
- `app/game/research/__init__.py`: isolated package marker.
- `app/game/research/specification.py`: frozen, explicit study configuration.
- `app/game/research/readiness.py`: pure recording, compatibility and scientific readiness gates.
- `app/game/research/__main__.py`: read-only readiness CLI.
- `app/game/research/comparison.py`: development comparisons, freeze and separate final scoring.
- `app/game/research/uncertainty.py`: paired grouped bootstrap, separate pilot/final entries.
- `tests/test_game_research.py`: explicitly synthetic regressions.
- `docs/game_research_spec.template.json`: unresolved, intentionally invalid template.
- `docs/game_research_protocol.md`: protocol, limitations and validation handoff.

## Questions, hypotheses and scope

Before accessing final outcomes, declare the population/category and primary loss
function. Test whether a full minimax policy has lower held-out worst fixed-attack
expected configured loss than uniform and development-selected deterministic
policies. Interpret the estimated difference using the preregistered uncertainty
analysis and any declared practically meaningful effect size. Evidence of reduced
loss supports improvement on that population, attack set and loss; evidence of
increased loss supports harm. Limited data or uncertainty spanning improvement and
harm is inconclusive, and failure to demonstrate reduced loss alone does not falsify
a benefit. Separately test whether dependency aggregation changes that loss versus
the restricted reputation aggregation game. Report clean decision coverage changes
and their uncertainty as well, including possible tradeoffs.
These are hypotheses to preregister, not predictions supported by the fixture tests.
Primary outcomes must be selected explicitly; report all diagnostic outcomes too.
No inference about arbitrary adversaries, upstream compromise or other domains follows.

The attacker sees the frozen policy distribution, candidate identities, dependency
groups, aggregation options, budget and execution contract. It commits to one fixed
action before the defender's team draw. It does not observe that draw or use an
example's truth label to retarget. Actions are clean, forced support, forced rejection,
confidence inflation or suppression of at most one full configured connected group.
Overlaps and bridge verifiers use Stage 1 full-registry components; unknown dependencies
use the explicitly declared supported `shared_unknown` treatment. This is an assumed
conservative grouping, not empirical evidence of independence. No dependency pathway
is inferred from sharing an answer. Directional attacks preserve genuine abstentions;
failed/unavailable recordings never acquire invented reports. Existing versioned
adapters mutate copied report-level outputs, not retrieved documents or models.

Defender actions are all feasible `(team, aggregation)` pairs from existing enumeration.
Eligibility, registration, prerequisites, all required expected capabilities, minimum
size and estimated attempt budget apply without relaxation. Replay attempts the whole
team, uses frozen history reputation and the bound threshold/failure contract, then
enforces achieved coverage. There is no early stop, fallback, replacement or retry.
Expected capabilities never count as achieved certificates.

## Current scientific readiness

Only arithmetic and direct-fact achieved contracts exist. Arithmetic requires a
directional nonzero-confidence factual rule certificate for addition, subtraction,
multiplication or division. A properly recorded arithmetic scope can yield meaningful
decisions, subject to minimum contributors, thresholds and execution outcomes.
Direct-fact requires assessed claims and matching directional NLI evidence rows;
the contract exists but the current evidence producer is not cleared for experiments.
Semantic, comparison, consistency, logical-rule, evidence-retrieval and other
obligations have no achieved certificate here and remain unresolved/public uncertain.
Even a zero-weight obligation cannot be discarded. An entirely unsupported category
may measure uncertainty behavior but cannot support a decisive-verification claim;
this readiness gate blocks it rather than silently redefine the primary population.

The three existing baseline failures are:

- `tests/test_adaptive_pipeline.py::test_actual_evidence_output_contract_is_consumed_without_models[probabilities0-passed]`
- `tests/test_adaptive_pipeline.py::test_actual_evidence_output_contract_is_consumed_without_models[probabilities1-failed]`
- `tests/test_adaptive_pipeline.py::test_actual_conflicting_evidence_cannot_cover_factual_request`

Directional producer outputs return public uncertainty instead of expected pass/fail;
conflicting evidence reports `no_relevant_evidence` instead of `conflict`. These can
distort coverage, loss and the apparent value of aggregation/attacks. Every study
requiring direct-fact/evidence-retrieval, or containing an evidence adapter, is blocked
by the harness until a separately reviewed producer repair updates this gate. There
is no caller boolean to bypass it. Explicitly revising the scientific scope to a
separate arithmetic population is possible before registration; deleting failed
examples from an evidence population is not. No teammate evidence code is modified.

Each spec represents one exact compatible planning category. Domain, analyzer
requirements/validity/versions, reference availability, candidates, prerequisites,
costs, budget, dependencies, loss/provenance and frozen statistics fragment categories.
Records from another category reject; report each category's sample/group counts.
The library never pools categories automatically or drops small categories. Existing
pooled provenance still requires matching domain/reputation/applicability; it does
not implement population pooling or cross-domain learning. A pooled scientific design
requires an explicit future mapping and compatible policies, not relabelled matrices.

## Required inputs, splits and preregistration

`ExperimentSpecification` requires an exact code revision, configuration version,
scientific scope, primary outcomes, primary/sensitivity role, sensitivity plan,
matched-coverage plan and final-test custody/freeze protocol. Sensitivity specs must
reference the primary spec's digest. This records the reference, not authentication
or approval of the scientific plan. Each dataset role requires identity, version,
source, independent label provenance, declared label sources and grouping protocol.
`manifest` holds explicit per-example split identity/question/run IDs and role
assignments. Labels must be independent booleans from existing supported methods.
Source/provenance attestations require human auditing; hashes do not establish truth.

History alone establishes reputation via the existing isolated history manager.
Development alone constructs payoffs and selects strategies/configurations. Final
test is held out until the complete comparison and thresholds are frozen. Existing
manifest validation rejects cross-role example, related-question group, question,
content and execution-ID overlap. Related claims, paraphrases, alternative answers
and derivatives must share a split identity across collection; exact text hashing
cannot discover semantic leakage. Audit grouping before splitting, never after scores.

Record complete independent outputs for every captured candidate, including actual
failures/unavailability. Missing or extra candidates are input errors, not uncertainty
observations. Recording/execution IDs, category, reference state and independent
labels must agree. Explicit model/corpus/prompt/adapter fingerprints and the
`complete_team_independent_v1` collection attestation are mandatory. Fingerprint
identities must be nonempty; truly inapplicable resources need an explicit reason,
not an omitted field. The supplied execution configuration must identify these
actual fingerprints; the harness cannot authenticate a historical collection.

The context requires actual dependency pathways/unknown treatment, every attempt
cost, cost units, budget, false-accept/reject/uncertainty/resource penalties and
versions. The execution contract requires threshold, history priors and failure
rule. Seeds, repetitions, cluster resamples/confidence level and optimizer tolerance
are explicit. No scientific numeric defaults are provided. The JSON template uses
null for all unresolved project inputs and must fail readiness. Obtain the detailed
schema with `ExperimentSpecification.model_json_schema()`; do not fill it with test
fixture values and call it empirical. One sensitivity configuration/category uses
one spec; comparisons across specs must retain the same audited source roster and
split assignments, and explicitly explain changed categories/compatibility bindings.

## Comparisons, freeze and outcomes

`prepare_comparison(spec, development, full_artifact, freeze_record=..., actual_code_revision=...)`
is an explicit development entry. It requires a pre-existing full policy artifact
from Stage 3/4, replays the complete declared development cube to verify the supplied
evaluation, and never fits the full policy. Only the two restricted aggregation
games are optimized here. No empirical call is made as part of Stage 5A implementation.
The complete roster is:

- Full minimax team-and-aggregation policy from the compatible artifact.
- Uniform over the identical full feasible action set, including both aggregation labels.
- Pure strategy minimizing maximum development column loss.
- Pure strategy minimizing clean development loss.
- Minimax over all feasible teams with reputation aggregation fixed, and likewise with
  dependency aggregation fixed. Exact restricted row definitions and numerical
  certificates are retained; neither claims optimality over the full game.
- Captured selector coverage-aware greedy team, with explicitly configured aggregation.
  It must appear exactly in the feasible enumeration. If its soft-target team exceeds
  budget or misses coverage/minimum, readiness fails; it is never repaired silently.

Deterministic ties use lexicographic strategy IDs. All comparisons use identical
candidates, budget, costs, frozen history, labels, fixed attack columns and example
denominators. Research distributions are separate from deployable full `Policy`;
production validation still requires every feasible strategy. The original benchmark's
adaptive path executes real early stopping/fallback and can learn sequentially.
Its majority/all-verifier metrics also lack this public achieved-coverage contract.
Those procedures are not interchangeable with full-team replay and are not included
as equivalent baselines. A faithful adaptive comparison needs separately recorded
prefix/state/fallback behavior and matched history, budget and threat assumptions.
The semantic evaluator downloads data/models and has fixed threshold/partition
choices; it is not imported or executed by this harness. Feedback evaluation is a
placeholder, not a label provider.

Freeze configuration, source manifests/fingerprints, independent history, attacks,
artifact, method definitions, selection rule, thresholds, seeds, primary outcomes,
sensitivity family and statistical plan with an external custody witness. Store
`FrozenComparison` JSON and its digest before opening test labels. The textual
freeze record is an audit reference, not a timestamp or access-control mechanism.
`score_development_pilot` labels outputs `development_pilot`.
`score_frozen_final` is the distinct explicit held-out entry; it validates bindings
and distributions without LP fitting or baseline selection. Neither is exposed by
the readiness CLI. Library callers must supply the actual revision; final custody
must enforce clean committed source and a trusted artifact origin externally.

Per attack/category report expected correct accept/reject, false accept/reject,
uncertain and unresolved counts, denominator, coverage, selective risk, mean estimated
attempt cost and mean configured total loss. Unresolved is a subset diagnostic, not
an additional disjoint class. Use exact strategy weights for each example; selective
risk divides expected errors by expected decisive count, never averages row risks.
Zero decision coverage has undefined risk, not zero error. Every declared example
remains in every attack denominator, including failures and zero-probability rows.
Loss includes configured public-error/uncertainty penalties plus resource weight times
estimated attempt cost, charged once per selected member even when execution fails.
No cost estimate is measured latency or money without separate calibrated provenance.
Report clean action metrics separately and identify all exactly tied worst fixed
attacks. Worst-case expected loss maximizes attack-column expectations, not the
expectation of an attacker that sees the sampled team. It currently includes clean
in the fixed set; also retain every attacked column rather than hiding clean results.

For matched coverage, predeclare development-only threshold grids, target coverage,
tolerance and tie rules. Rebuild execution/context bindings, payoffs and artifacts
for each threshold before freezing. Report unmatched targets explicitly; do not
interpolate test curves or tune thresholds on test. Sensitivities should cover the
application-chosen penalties/resource weight, thresholds, costs/budgets and declared
dependency scenarios. Unsupported unknown-treatment alternatives require a separately
implemented contract; do not simulate them by relabelling `shared_unknown`.

## Grouped uncertainty and reproducibility

`bootstrap_development_pilot` and separate `bootstrap_frozen_final` resample whole
split-identity clusters with replacement, sharing each draw across methods and attacks.
All related examples remain together. They recompute count-based metrics, ratios and
maximal attack expectations on each draw, using exact strategy mixtures. Percentile
intervals and paired full-minus-baseline differences are reported for loss, coverage,
risk and estimated cost, and worst-case expected loss over the fixed attack set.
At least two independent clusters are required. If any draw has undefined risk, its
unconditional risk interval is undefined and the defined-draw count is exposed.
Do not treat strategy/attack repeats or related examples as independent observations.
This clustered, example-weighted percentile procedure conditions on frozen history,
fitted policies and configuration; it does not quantify training/selection uncertainty,
protect against poor group assignments, or supply a simultaneous multiple-comparison
guarantee. Predeclare confirmatory contrasts/corrections; small-cluster inference is
limited even when an interval can be computed.

Bootstrap sampling uncertainty differs from the numerical primal-dual LP tolerance.
The latter is floating-point certificate accuracy, not a confidence interval. Exact
policy integration has no team-sampling Monte Carlo error. If later auditing sampled
deployment draws, use the declared seeds/repetitions and report that randomness
separately, never multiply the scientific sample size by draws.

Run `.venv\Scripts\python.exe -m app.game.research readiness docs/game_research_spec.template.json`.
It exits 2 and emits `ready: false` for unresolved inputs. Valid specs additionally
list feasible rows, fixed actions, greedy feasibility, unsupported achieved contracts,
known evidence blockers and configuration/history compatibility. It performs no
replay, final scoring, model/provider calls, downloads or production writes. The
history check uses a new in-memory manager only. The CLI includes canonical input
digest, actual Git revision, tree cleanliness and LF-normalized research-source digest.
Structured results/freeze/uncertainty include spec, manifest and comparison digests,
revision, category and evidence kind as applicable. Stable IDs use existing canonical
UTF-8 sorted-key JSON; set-like metadata is canonicalized while semantic settings
remain bound. Hashes provide integrity, not provenance authentication.

The shared pure `adapter_incompatibility` helper checks directional recordings
against the existing built-in/generic adapter mapping without transformation or a
second normalizer. Readiness exposes `adapter_blockers` with code, partition,
example ID, verifier name, declared adapter and expected adapter, and returns not
ready on any mismatch. Normalized abstentions and absent reports retain their
existing exemption from directional adapters. Genuine missing recordings remain
separately blocked. Clean/suppression attack behavior and attack versions are unchanged.

## Validation record and unresolved decisions

Final research suite after review fixes: **44 passed**, included in the component
run below. The standalone research command is
`.venv\Scripts\python.exe -u -m pytest tests/test_game_research.py -q -p no:cacheprovider`.
Checks cover unresolved/invalid configuration, explicit unknown treatment, stable
detached identities, leakage and missing recordings, unsupported/evidence gates,
infeasible greedy budgets, restricted action-set metadata/certificates, exact mixed
counts/ratios/failed-attempt costs, fixed attack maxima, development-only selection,
final-label independence, final scoring without optimization, grouped uncertainty,
related-question clustering and fresh-process dry-run isolation. Initial test-fixture
and diagnostic-reporting issues were fixed before this final passing run.

The complete research plus affected Stage 1–4/evaluation checks were split into
two nonoverlapping runs: **656 passed** (research, offline and affected components)
and **239 passed, 3 demonstrated baseline failures**, with one existing Starlette
TestClient deprecation warning (analyzer, pipeline and evaluation). Together these
are **895 passed and the same 3 baseline failures**. Combined file list:

```text
.venv\Scripts\python.exe -u -m pytest
  tests/test_game_research.py
  tests/test_game_runtime.py tests/test_game_offline.py tests/test_game_foundation.py
  tests/test_dependency_aggregation.py tests/test_decision_engine.py
  tests/test_vote_normalization.py tests/test_early_termination.py
  tests/test_verifier_selector.py tests/test_reputation_manager.py
  tests/test_reputation_imports.py tests/test_question_research_context.py
  tests/test_question_analyzer.py tests/test_adaptive_pipeline.py
  tests/test_reputation_integration_upgrade.py tests/test_offline_benchmark.py
  tests/test_analyzer_evaluation.py -q -p no:cacheprovider
```

The three failures named above were independently reproduced in a fresh process:
**3 failed, 1 passed, 88 deselected**. The exported `reproduce_baseline.py` installs
a read-only import loader for orchestration, factual coverage, evidence verifier
and game models. It executes their exact `git show 9d21eba...:<path>` bytes before
pytest imports, selecting the two evidence function names with `-k` and disabling
pytest's cache. Other tracked code used by those baseline cases matches that base;
the offline adapter edit is not used by those cases. No checkout/reset, source
replacement, staging or commit was used. The full affected run and reproduction
used outside-sandbox permission for Windows TestClient/subprocess checks. The full
repository suite, live PostgreSQL and real models/providers were not run.

Both Git whitespace checks passed (the index remains empty). The export also checks
new-file whitespace and reconstructs the complete tracked-and-new-file patch outside the repo,
then compares every LF-normalized byte and hash. Its manifest specifies raw versus
UTF-8 LF normalization; no cache, secret or dependency-generated files are included.
The sole tracked change is the shared adapter check in `app/game/offline/attacks.py`.
It extracts the identical mapping check from the directional branch; the existing
ValueError text, normalization calls, transformations and versions are preserved.
All ten paths remain unstaged/uncommitted. The test subprocesses use `sys.executable`
instead of a platform-specific virtual-environment path.

Review reproduction: a synthetic directional `rule` recording declared `generic_v1`
previously returned `ready=True`, while `fit_policy` raised
`ValueError: unsupported verifier-aware transformation adapter`. The same synthetic
input now returns `ready=False` and identifies both development/final-test mismatches
in structured adapter blockers. Fitting still rejects the invalid adapter, preserving
its contract. Regressions cover all four valid built-in mappings, invalid mappings
and custom/generic mappings, plus abstention/unavailable/failed preservation. Dry-run
tests prohibit transformation, replay, scoring and optimization. The export includes
a fresh-process before/after reproducer and its JSON results. The protocol now
distinguishes evidence of improvement, evidence of harm and inconclusive findings;
failure to demonstrate improvement alone is not proof of no benefit.

No empirical experiment has been run. The unresolved template remains not ready. Project input is still
required for datasets/independent labels/grouping/custody, scientific scope, actual
recordings/fingerprints, dependency pathways, cost units/calibration, losses, primary
and sensitivity choices, matched-coverage rules and final freeze approval. Evidence
readiness additionally needs a separately reviewed producer repair or explicit scope
revision. No scientifically justified pooling or penalty choices are invented here.
