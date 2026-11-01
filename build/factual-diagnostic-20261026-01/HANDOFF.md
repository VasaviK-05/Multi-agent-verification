# Factual diagnostic repair handoff

One authorized diagnostic pass completed: 24/24 attempts and returned calls, 30
local generations and 100 metadata GET requests. All 24 timings have verified
pre/post resource observations. There were no execution failures, raised timeouts,
interruptions or missing measurements. Rule abstained on all six factual questions;
confidence abstained on two. These are returned judgments, not execution failures.
Confidence reports contain no provider-error fields in this run.

Labels are absent from the diagnostic request. Scientific custody, study settings
and calibration freeze remain unapproved. No accuracy calculation, calibration
artifact, training export or policy fit was performed. Raw reports/timings and
observations are retained together in `collection/recordings.json` and the flushed
`collection/attempts.jsonl` journal. Final examples were excluded using only their
draft identity/content metadata; no final labels, reports or payloads were opened.

## Evidence/public-coverage owner

The existing controlled probe was rerun without loading real models or collecting
additional real examples. Three failures and one neutral-case pass reproduce:

- Entailment probabilities 0.95/0.04/0.01 should yield public `passed` and directional
  `direct_fact` coverage. Actual public result is `uncertain`.
- Contradiction probability 0.95 should yield public `failed` and directional factual
  coverage. Actual result is `uncertain`.
- Strong conflicting support/rejection should yield `uncertain`, reason `conflict`
  and no directional coverage. Public uncertainty occurs, but actual reason is
  `no_relevant_evidence`.

Reproducer:

```powershell
.venv/Scripts/python.exe -m pytest tests/test_adaptive_pipeline.py -q -k "test_actual_evidence_output_contract_is_consumed_without_models or test_actual_conflicting_evidence_cannot_cover_factual_request"
```

Relevant interfaces: `EvidenceVerifier.verify` calls `select_on_topic` before NLI;
the discarded evidence then becomes no-relevant-evidence abstention. The active
`content_terms` definition at `app/verifiers/evidence_retriever.py:137` is a later
override using plain whitespace splitting. It retains punctuation and stopwords.
The earlier normalized tokenizer at line 123 is overridden. Likewise the later
`anchor_weights` / `topic_coverage` / `select_on_topic` definitions at
`app/verifiers/evidence_verifier.py:562`, `:580`, `:593` override earlier versions.

Likely contributing cause: with the controlled question "Who wrote Hamlet?", the
active tokenizer yields `who`, `wrote`, `hamlet?`. The evidence title/premise has
`hamlet`/`hamlet.`; only `wrote` overlaps, giving 1/3 coverage with the fixture's
equal weights, below the 0.5 topic gate. Relevant chunks can be discarded before
their strong NLI probabilities reach aggregation. In actual corpus-backed retrieval,
the active weighting path can also omit absent anchors, so behavior differs from
the fallback fixture. This is a source-based causal hypothesis for the integration
owner to verify, not a scientific diagnosis from six examples.

Repair scope: review duplicate overrides and restore a consistent term/anchor
contract across retrieval weighting, topic gating and premise extraction. Preserve
relevance, conflict and abstention semantics; do not disable gates or coerce statuses
to make tests pass. Rerun the three failing probes, neutral control, evidence unit
tests and public achieved-coverage tests. No production verifier code was changed
in this diagnostic task.

All six real evidence calls returned directional reports here. That does not repair
or invalidate the controlled probe failures and does not establish answer correctness.
The existing `known_evidence_contract_failures_require_repair_or_explicit_scope_revision`
gate in `app/game/research/readiness.py` remains active for fitting.

## Analyzer/offline context-contract owner

Four captured examples retain unknown requirements:

- e04: "What is Python?"
- e05: "What is artificial intelligence?"
- e06: "What is machine learning?"
- e07: "Who developed the theory of relativity?"

`app/analysis/heuristic.py:135` uses bounded routing patterns, not general semantic
question classification. Definitions do not match its direct-fact pattern; the
`who` pattern lists wrote/authored/invented/discovered/founded, not developed.
Those inputs therefore return an empty verification-type list.
`build_research_context` in `app/analysis/research_context.py:12` deliberately maps
absent hints to `requirements_known=False`, rather than inventing requirements.
The Germany and India capital questions match `direct_fact` and remain known.

This is a conservative routing limitation, not a timeout or missing measurement.
The diagnostic collector dispatches registered, prerequisite-eligible candidates
independently of whether requirements are known, so it did not block timing
collection. Fitting is different: `app/game/strategies.py:17` rejects unknown/empty
requirements, and `export_training` requires a compatible captured analysis/cohort.
The complete six-example set still cannot be forced into one current context.

Repair/decision: agree the intended requirements/rubric for definitions and
"developed" attribution queries, then make a separately reviewed analyzer change
or approve an explicit different cohort contract. Regenerate actual analyzer outputs
afterward. Do not hand-edit this run's captured requirements or silently drop rows.

## Collection contract change and validation

The old smoke format still required independent labels and a witnessed scientific
reservation, which this authorization did not approve. A narrowly versioned
`DiagnosticRecordingRequest` now reuses the existing collector. It fixes intended
use to smoke, requires absent labels/study approval, uses an unwitnessed metadata-only
exclusion roster and marks cache semantics diagnostic-only. The original study schema
was not relaxed. Training export and calibration measurement export reject this type;
linked AttemptMeasurements remain available for diagnostic summaries.

The one-off runner enforces local HTTP endpoints and hard 30-generation/100-metadata
request ceilings. Offline model loading is enforced. Tests cover ordinary and
diagnostic collection, final exclusion, no label/approval promotion, export guards,
network ceilings and denial of external endpoints: 27 affected checks passed. The
separate three existing evidence failures remain explicitly reported, not hidden.

Next action: hand the evidence routing/coverage and analyzer/cohort issues to their
owners for review. Study label/custody/freeze decisions remain separate. These six
timings are provisional engineering observations; no project-wide cost, monetary
cost, CPU-time, accuracy or policy-improvement claim is supported.
