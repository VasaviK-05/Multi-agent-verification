# Coverage-aware verifier selection

Policy `coverage_greedy_v1` is a deterministic coverage-aware heuristic. It
does not establish strategic incentives, equilibrium, novelty, independence,
or global optimality. Analyzer requirements and all resource/tradeoff
constants remain uncalibrated research inputs.

## Inputs and precedence

`VerifierSelector.plan(analysis, context)` uses typed `QuestionResearchContext`
when present and valid. Version `question_context_v1` is supported. Recognized
requirements are canonicalized; nonnegative finite weights in [0,1] are
normalized across those requirements. A zero-weight requirement remains an
obligation. Recognized requirements need a positive total weight.

Validate the relationship between the full weight vector and requirement list
before filtering or normalization. Any positive weight for an omitted label
invalidates context, whether the label is recognized or unrecognized. The audit
retains each omitted label and its original finite weight in
`requirements.weight_discrepancies`; the label is not silently added as a
requirement. Extra zero-weight entries remain valid and do not create obligations.
This preserves the analyzer's existing six-key vector, which assigns zero to
labels outside its identified requirements; it does not impose a new exact-key
constraint on the weight mapping.

Only an absent context permits fallback to recognized legacy
`verification_types`, with equal weights. Unknown labels remain observable
and uncovered. Conflicting legacy hints are recorded, never merged into
authoritative context. An invalid present context is recorded as invalid,
does not trigger legacy fallback, disables early stopping, and guards the
public status to uncertain. `requirements_known` means recognized requirements
exist; it never proves the analyzer identified every obligation.

The plan captures requirement source/status, normalized weights, legacy
hints (including separately recorded unrecognized legacy labels), disagreement,
unknown authoritative labels, validation errors, relevant analysis
inputs and provenance, utility weights/mapping, candidate explanations,
exclusions, initial team, fallback queue, and expected gaps. Audit records
contain serializable values, never verifier objects.

## Utility and deterministic selection

The base ranking formula is unchanged:

```
U(v,q) = R(v, analysis.domain)
         - lambda_cost * cost(v) - lambda_latency * latency(v)
         + lambda_suitability * S(v,q)
```

Default lambdas are 0.15, 0.10, and 0.20. `S` is the share of unique
authoritative requirement labels mapped to a verifier by the existing
suitability map. Unsupported labels consume a share but map to nobody by
default. Suitability is a routing hint, not a capability declaration.

One `statistics_batch` call obtains detached reputation statistics under
the manager's process-local lock. The plan uses the mean rounded to six
decimals, matching `get_reputation`. All selection and explanations use
these captured values. Later feedback cannot mutate the frozen plan.
This does not snapshot the separate decision engine's future reads or
provide database/multiprocess transaction isolation.

Among eligible candidates adding uncovered expected requirements, choose
the greatest sum of newly covered normalized weights; break ties by utility,
then original registration order. Repeat until no further coverage can be
added. Fill remaining initial slots by utility, then registration order, up
to the existing difficulty target. Required specialists may exceed that
soft target. Never duplicate candidates. Remaining eligible candidates form
the fallback queue in utility/registration order. Unknown requirements use
utility ordering and the existing initial target, with coverage marked unknown.

Cost and latency are **dimensionless relative estimates in [0,1]**, not money,
tokens, milliseconds, or measured runtimes. They and their weights remain
uncalibrated. An absent profile uses 0.5/0.5; malformed supplied profiles raise.
Target bands/ranges remain easy (2,2), medium (2,3), hard (3,4), with the
existing within-band half-up interpolation.

## Capabilities, prerequisites, and execution

Factory-built rule expects bounded arithmetic patterns, not arbitrary logic.
Evidence expects factual retrieval/NLI limited to its configured corpus and
relevance gates. Semantic expects reference comparison, not factual evidence;
missing/blank context or a recognized judgment-label list is an observable
missing prerequisite. Confidence expects consistency, not factual evidence.
Unknown provider/corpus/model readiness is eligible, not confirmed unavailable.
Planning constructs no verifiers and performs no model or readiness probes.

Injected agents, even ones named `rule` or `evidence`, have unknown capabilities
unless supplied via `capabilities={name: CapabilityDescriptor(...)}`. Descriptors
may specify `requires_reference`, `readiness` (ready/unknown/unavailable), an
explicit unavailable reason, and limitations. A name-based suitability bonus
does not grant an injected agent capabilities.

Production builds one plan with the actual request context, then lazily resolves
and attempts the initial team followed by fallbacks. Only explicit
`VerifierUnavailable` is recoverable; it records a failed attempt without
fabricating a verifier vote. Unexpected construction/verification errors remain
visible. Returned result identity must match the planned candidate.

Expected coverage never satisfies achieved coverage. Existing arithmetic and
direct-fact guards still require actual qualifying metadata, non-abstention,
and positive vote confidence. Recognized requirements without implemented
achieved-coverage contracts (logical_rule, semantic_comparison, consistency,
evidence_retrieval) remain explicitly unproven, even when a descriptor expects
them. Unrecognized requirements also remain uncovered. Public status is
uncertain while required achieved coverage is missing.

Early termination retains existing thresholds, contributor checks, disagreement
vetoes, and accepted decision snapshots. It additionally requires completion of
the initial team and actual coverage of identified requirements. Unknown or
invalid requirements disable early termination. Hard questions exhaust eligible
candidates. Abstention/unavailability/missing coverage continues to fallbacks.
At exhaustion the existing numerical aggregation remains unchanged; minimum
contributors and missing coverage still guard the public status. Unknown
coverage alone does not force a numerical support/rejection decision.

When the numerical stopping assessment is sufficient but execution policy vetoes
stopping, `stopping_policy_vetoes` records the verifier, result count, original
numerical assessment, and explicit reason codes. Reasons distinguish invalid
context, unknown/unsupported requirements, an incomplete initial team, hard
questions, missing achieved coverage, and absent achieved-coverage contracts.
This history can include an earlier veto followed by a later accepted stop.
`last_stopping_assessment` remains the numerical assessment; `termination` and
`public_status` remain the actual execution outcome and guarded public decision.

## Compatibility and storage

`select`, `iter_ranked`, `explain_ranking`, `ranking_utility`, `utility`, and count
methods retain their legacy behavior for existing callers. In particular,
legacy `select()` remains utility top-k, and legacy ranking uses legacy hints.
They do not apply request prerequisites or the coverage-first policy.
Production uses `plan()` and `resolve()` instead. The plan records its own
candidate explanations; no second ranking is used during execution.

`ValidationResponse.selected_verifiers` still lists agents returning results,
including abstentions. `execution_audit` is additive, optional, and defaults to
None for older callers. It contains the plan, attempted names, returned-result
names, explicit unavailability, achieved coverage, and execution summary.
The final result also carries that audit under
`metadata["multi_agent_verification.execution"]` when results exist.

Execution audit version `execution_audit_v2` separates planning from observations:

- `selection_plan` is immutable and is never updated by execution.
- `runtime_availability[name]` is `unobserved` until an attempt returns a result
  (`returned_result`) or raises the narrow `VerifierUnavailable` (`unavailable`).
  This includes candidates excluded during planning: their configured readiness
  is in the plan, and they have no runtime observation.
- Per-requirement `planned_candidates` lists eligible explicitly declared
  candidates. `unattempted` tracks which of those have not been attempted.
- The historical boolean `coverage.available` is retained, but now means at
  least one declared or output-qualified candidate **returned a result** for
  this requirement during this run. It is exactly `bool(runtime_available)`.
  It does not mean achieved coverage, future service health, or availability of
  unattempted candidates. `runtime_available` lists those returned candidates;
  `runtime_unavailable` lists declared candidates raising `VerifierUnavailable`.
- A returned abstention can establish this observed availability for a declared
  candidate, but never achieved coverage. An undeclared candidate needs actual
  qualifying output metadata to be associated with a requirement. A familiar
  verifier name or a suitability mapping alone grants no capability/availability.

Earlier unversioned audit data used `coverage.available` for planned or hinted
availability as well. Consumers needing that old planning information should use
`planned_candidates` on v2 records rather than interpreting unattempted agents as
confirmed runtime-available. Repository/frontend code currently does not interpret
this boolean; its tests have been updated for the explicit observation contract.

The current route passes result metadata to `save_verifier_outputs`, whose JSON
serialization retains the nonempty-run audit in `verifier_outputs.metadata`.
This serialization path is tested with a fake database connection; live database
durability is not tested here. The separate response `execution_audit` field is
not persisted by current repositories. **Empty/all-unavailable runs have response
and in-memory context audit only** because they have no result row. No database
schema/repository or frontend changes were made.

## Local validation (2026-10-21)

After the P2 corrections, the final combined run was **697 passed, 8 deselected,
1 deprecation warning** in 24.54 seconds. The warning concerns the installed Starlette/httpx TestClient
integration, not selection behavior. The command below was run outside the
Windows sandbox after its event-loop socket restriction stalled TestClient.
Database and automatic ground-truth boundaries are mocked in pipeline/benchmark
tests; API routing, schemas, planning, aggregation and feedback mathematics
remain real. Repository JSON serialization is tested using a fake connection.

Exact command from the repository root (PowerShell):

```powershell
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'; $env:PYTHONDONTWRITEBYTECODE='1'; $env:HF_HUB_OFFLINE='1'; $env:TRANSFORMERS_OFFLINE='1'; .\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/test_verifier_selector.py tests/test_adaptive_pipeline.py tests/test_question_analyzer.py tests/test_question_analyzer_ollama.py tests/test_question_research_context.py tests/test_analyzer_evaluation.py tests/test_reputation_manager.py tests/test_reputation_imports.py tests/test_decision_engine.py tests/test_early_termination.py tests/test_vote_normalization.py tests/test_offline_benchmark.py tests/test_rule_verifier.py tests/test_semantic_verifier.py tests/test_confidence_verifier.py tests/test_evidence_verifier.py -q --tb=short -k 'not (real_label_map_is_checked or correct_capital_answer or wrong_capital_answer or incorrect_artificial_intelligence_answer or who_question or topic_outside_corpus_is_an_abstention or unrelated_answer or multi_claim_answer_with_an_unsupported_sentence)'
```

Focused P2 validation ran first under the same offline environment settings:

```powershell
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/test_verifier_selector.py tests/test_adaptive_pipeline.py -q --tb=short -k p2
```

Result: **14 passed, 186 deselected** in 13.07 seconds. These deselections are
the other selector/pipeline tests excluded by the focused `-k p2` filter, not
the eight real-model exclusions of the combined run. The fixes reproduce the
original inconsistent-vector input as invalid (public uncertain even with
qualifying support/rejection), and the only-specialist-unavailable input with
`coverage.available=false`, no achieved coverage, and an unchanged plan.

This is a broad offline regression run, not the entire repository suite.
The eight deselections are model-backed evidence tests. The separate live-model
verifier/retriever suite, self-consistency suite with a service probe at collection,
and unisolated health/validation modules with database bootstrap were not run.
No models were downloaded and no live inference was invoked. Live database
durability and real service availability remain outside this validation.

`git diff --check` passed. HEAD and branch were unchanged; no commit/push was made.
