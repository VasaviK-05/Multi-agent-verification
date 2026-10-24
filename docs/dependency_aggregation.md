# Stage 2: dependency aggregation and frozen reputation

This stage adds numerical decision strategies only. Production continues to use
the original live reputation-weighted calls. Orchestration, stopping, coverage
enforcement, feedback, verifiers, retrieval and persistence are unchanged. There
is no production game-mode switch, attack simulation or payoff construction here.

## Interfaces

The existing `DecisionEngine.decide` and `decide_detailed` methods accept additive
keyword-only arguments:

- `snapshot`: `FrozenReputationSnapshot` made from a validated `PlanningContext`;
- `aggregation`: `reputation_weighted` (default) or `dependency_group`;
- `dependencies`: optional registry for dependency aggregation; if supplied, it
  must equal the snapshot's captured registry, including version and assumptions;
- `team`: optional sequence of unique verifier names bounding permissible reports;
- `validation_id`: optional nonblank run identity, following the existing
  orchestration/feedback naming contract. These identifiers are not authentication.

```python
from app.decision.decision_engine import DecisionEngine
from app.game.decision_inputs import FrozenReputationSnapshot

# planning_context and reports come from the caller's captured evaluation episode.
snapshot = FrozenReputationSnapshot.from_planning_context(planning_context)
engine = DecisionEngine()
baseline = engine.decide_detailed(
    reports, domain=planning_context.plan.domain, snapshot=snapshot,
)
grouped = engine.decide_detailed(
    reports, domain=planning_context.plan.domain, snapshot=snapshot,
    aggregation="dependency_group", team=sampled_strategy.verifiers,
    validation_id=validation_id,
)
audit = grouped.to_dict()
```

`decide` returns the existing `(status, rounded_score)` pair for either strategy.
`decide_detailed` returns the original `DecisionDetail` and original vote shapes
for ordinary live baseline calls. Opt-in calls return `AggregationDetail`, a
compatible frozen dataclass subclass; `asdict()` still works and `to_dict()`
returns a fully detached JSON-shaped audit. No existing base-model fields were
added. Domain omission still uses the engine's configured default domain, so
callers must pass the matching domain for snapshots from another domain.

The adapter retains the entire validated context, full detached reputation
statistics and the Stage 1 snapshot identifier. It reuses PlanningContext's
validation for counts, finite means/variances and consistency. Both methods use
the original captured posterior means, not the rounded candidate values, and
never read live reputation when a snapshot is supplied. An invalid identifier,
domain mismatch, missing participant/team statistics or inconsistent context
raises before aggregation, including for empty report lists. Aggregation never
updates reputation. Later live updates cannot change a frozen result.

Implementation versions are `log_odds_v1` and `groups_v1`. The snapshot's version
for the requested aggregation must match. These versions identify formulas, not
scientific calibration. The Stage 1 engine's labels now have decision
implementations, but sampled-policy execution remains a later stage.

## Formula and classification

Both methods reuse `is_abstention`, `vote_confidence` and `signed_mass`; no
verifier-specific normalization is redefined here. Abstentions and zero-confidence
directional reports remain in the explanations with reasons, but do not score.
Supported deterministic rule rejections retain strength -1 even with stored score
0; evidence neutrality and confidence ties follow the existing normalizer.

For dependency aggregation the registry builds full connected components before
projecting onto the team. Absent bridge verifiers cannot split a configured group.
Only active participating reports determine each group score and influence:

1. `a_i = max(0, 2*r_i - 1)`; below-chance reputation is never inverted.
2. `z_g = fsum(a_i*m_i)/fsum(a_i)`, or the unweighted active-member mean if the
   reliability sum is zero.
3. `b_g = max(a_i)` over active members, never over excluded or absent reports.
4. `s = fsum(b_g*z_g)/fsum(b_g)`, or the unweighted active-group mean if the
   influence sum is zero.

All reductions use `math.fsum`. Groups with no active reports do not enter the
score or the group list. Zero-influence active groups are explained but add no
influence while a positive-influence group exists. No reports yield `unknown`;
all abstentions yield `uncertain` with aggregation `abstentions`; directional
zero-confidence-only pools yield `uncertain` with aggregation `zero_confidence`.
There is no epsilon band. The existing strict cuts classify the bounded unrounded
score: `s > threshold` passes, `s < -threshold` fails, otherwise uncertain. The
displayed score is rounded only afterward. The configured threshold is retained.

The frozen reputation-weighted method keeps the existing log-odds formula and
below-chance inversion. Its all-zero-log-odds fallback remains the active-report
mean. Live calls retain their six-decimal reputation rounding; frozen calls
deliberately use full captured means, so near-half reputations may behave
differently from the live baseline. No change is made to baseline learning.

## Report identity and duplicate equality

The canonical identity is `(effective validation_id, verifier_name)`. A report may
carry a `metadata.validation_id` annotation. The actual application currently
keeps its authoritative validation ID on the response/context and binds feedback
by stored object identity; this annotation is an additive caller contract and
does not replace that binding.

- An explicit `validation_id` binds legacy unannotated reports in the supplied
  batch; every annotated report must match it.
- Without an explicit ID, fully annotated reports must all share one ID, which
  is inferred. Mixing annotated and unannotated reports is rejected as ambiguous.
- Fully unannotated legacy reports form one call-local batch with ID `None`.
  There is no cross-call deduplication, persistence or claim of authenticated run
  provenance. Callers must not concatenate unrelated legacy runs into one batch.
- Explicit team membership rejects extra report names and duplicate team names.
  Missing reports are listed but do not force numerical uncertainty here: execution
  completeness and achieved coverage are later orchestration responsibilities.

Dependency aggregation canonicalizes exact duplicate identities/reports once and
rejects any conflicting report with the same identity. Duplicate equality uses
**all serialized report fields**: verifier name, score, passed, reasoning and the
entire metadata object, including normalization-relevant decisions, judgments,
rule outcomes and evidence labels. Object key order is ignored; list order and
every metadata value are preserved. Metadata must be finite, acyclic native JSON
(string keys, lists, scalars); tuples, sets and serializer coercions are rejected.
Thus bool/int differences or unsupported containers cannot conceal conflicting
normalization inputs. Exact duplicates have no effect; distinct reports within a
group can change its mean, as the specified formula permits.

Snapshot-only baseline calls retain the legacy duplicate-name rejection and input
order. Baseline calls opt into the additional identity/JSON contract only when
`team` or `validation_id` is supplied; they still reject duplicates. Such opt-in
identity batches, and all dependency batches, have stable verifier-name ordering.
Reports are deep-copied for the opt-in identity path; caller reports, registry
configuration, snapshot and reputation manager are never mutated.

## Explanation fields and limits

Extended details include aggregation ID/version, snapshot ID, effective validation
ID, supplied/observed team, missing reports, dependency configuration digest/version
and assumptions. Votes include normalized signed strength (None for abstention),
full reputation, reliability strength, inclusion flag/reason and failure-group ID.
Active groups expose members, reliability sum, score, maximum reliability influence,
weighted numerator contribution and member fallback. The final fallback is recorded
separately. `threshold`, `raw_score`, `score` and `status` preserve the existing
classification convention; `lower_cut` and `upper_cut` explicitly expose
`(-threshold, threshold)` with strict comparisons.

For dependency votes `weight` is reliability `a_i`, and `contribution` is the
within-group weighted numerator term `a_i*m_i`. For groups it is `b_g*z_g`.
Fallback formulas use the separately reported strengths/scores rather than these
zero numerator terms. `included` means active for group evaluation; a report with
zero reliability may have no weighted influence while others have positive strength.
For baseline extended votes, weight/contribution retain their original log-odds or
equal-weight meaning. A full dependency registry is not exposed as observed truth;
its configured assumptions remain unchanged by reports or metadata provenance.

These are numerical classifications, **not achieved verification coverage**.
Neither method dispatches verifiers, enforces minimum team execution, checks a
resource budget nor authorizes production game mode. Complete-team execution,
coverage overrides, policy retrieval and audit persistence remain later work.
The code does not invent dependency pathways, calibrated costs/penalties, dataset
partitions or pooling choices; resource declarations in tests are synthetic.

## Validation and review handoff

Starting state: clean `vasavi/game-engine-foundation` at reviewed foundation commit
`c49438f305e4e1efe83b1e33d678e9af24ed96f8`. No applicable `AGENTS.md` was found in
the repository or its ancestor directories. The Version 1 specification and Stage 1
handoff were read before implementation. HEAD and branch remain unchanged.

Exact changed files and rationale:

- `app/decision/decision_engine.py`: additive keyword-only strategy/snapshot/identity
  dispatch; the original reputation-weighted calculations are reused unchanged,
  with an optional captured-mean input replacing only the live acquisition step.
- `app/decision/dependency_aggregation.py`: specified group formulas and detached
  per-verifier/group explanations; extended subclasses preserve base-model shapes.
- `app/decision/report_identity.py`: opt-in identity validation and exact duplicate
  canonicalization with strict JSON equality and no normalization metadata loss.
- `app/game/decision_inputs.py`: validated immutable PlanningContext adapter,
  full-precision means, matching domains/participants, snapshot and version checks.
- `app/game/models.py`: comment-only update acknowledging the separate decision
  implementation; no Stage 1 model, identifier, solver or planning behavior changes.
- `tests/test_dependency_aggregation.py`: focused Stage 2 regression coverage;
  teammate-owned tests are unchanged.
- `docs/dependency_aggregation.md`: interfaces, runnable-in-context usage example,
  identity/equality decisions, formulas, assumptions and verification record.

Checks were run with `.\.venv\Scripts\python.exe -m pytest`:

```text
tests/test_dependency_aggregation.py tests/test_game_foundation.py
tests/test_decision_engine.py tests/test_vote_normalization.py
tests/test_reputation_manager.py tests/test_reputation_imports.py
tests/test_verifier_selector.py tests/test_early_termination.py
tests/test_question_research_context.py tests/test_question_analyzer.py -q
```

Result: **547 passed**, including all **99 foundation** and **68 Stage 2** cases.
Tests cover both member/group weighted formulas and both zero-weight fallbacks,
cold start and below-chance behavior, active zero reliability, correlated versus
independent groups, maximum active influence, excluded/absent high reputations,
overlaps/absent bridges/shared unknowns, duplicate/conflicting/mixed identities,
JSON coercion/cycles, strict raw cuts, permutation invariance, frozen statistics
and live-read prohibitions, update isolation, baseline inversion/shapes and serializable
detached explanations. Fresh interpreter import-order regression checks also pass.

```text
tests/test_adaptive_pipeline.py tests/test_reputation_integration_upgrade.py -q
```

Result outside the sandbox: **112 passed, 3 demonstrated baseline failures**:

- `tests/test_adaptive_pipeline.py::test_actual_evidence_output_contract_is_consumed_without_models[probabilities0-passed]`
- `tests/test_adaptive_pipeline.py::test_actual_evidence_output_contract_is_consumed_without_models[probabilities1-failed]`
- `tests/test_adaptive_pipeline.py::test_actual_conflicting_evidence_cannot_cover_factual_request`

The two directional cases still return public uncertainty; the conflicting-evidence
case returns `no_relevant_evidence` instead of `conflict`. For isolated baseline
reproduction, a fresh Python process installed a read-only `MetaPathFinder`/loader
for only `app.decision.decision_engine`, executing the committed source obtained
with `git show HEAD:app/decision/decision_engine.py` in its module namespace before
pytest imports. All other code/tests remained the actual tree. The command selected
the two test function names using `-k` and disabled pytest's cache provider; result:
**3 failed, 1 passed, 88 deselected**, matching the modified-tree failures. No working
file was replaced, and no checkout/reset or staging was used. Baseline HEAD was
the foundation commit above. These verifier/evidence-related failures were not fixed.

`git diff --check` passed. The complete tracked diff and every new source/test/doc
file were reviewed for ownership and compatibility. The full repository suite and
live PostgreSQL deployment were not tested. There are no known unresolved Stage 2
defects from these checks; the implementation is ready for independent review,
with all changes left unstaged and uncommitted.

Design choices requiring awareness: dependency aggregation requires a snapshot;
legacy unannotated rows can establish only call-local identity, not authenticated
provenance; strict JSON duplicate equality deliberately rejects non-JSON metadata;
numerical pass/fail does not enforce execution completeness or achieved coverage.
Actual dependency/cost/loss/data/pooling configuration remains project input.
