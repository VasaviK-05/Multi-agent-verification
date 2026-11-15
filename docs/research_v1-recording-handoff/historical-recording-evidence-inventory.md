# Historical Recording Evidence Inventory

## Scope and evidence boundary

This inventory summarizes an existing **historical Development rehearsal**. It is evidence of what that rehearsal recorded; it is **not a current authorized controlled collection run** and does not approve a runtime configuration or authorize further recording.

The counts below were derived from the original `attempts.jsonl` records. Report contents are not reproduced here.

## Historical rehearsal inventory

Source: `evaluation/datasets/development_pilot/runs/research_v1_rehearsal_662bd5c/attempts.jsonl`

| Measure | Recorded evidence |
|---|---:|
| Attempt rows | 52 |
| Verifiers | confidence: 13; evidence: 13; rule: 13; semantic: 13 |
| Rows with a report payload | 52 |
| Outcomes | 47 abstention; 5 directional |
| Rows with a duration | 52 |
| Timing statuses | 52 `returned` |
| Recorded failures | 0 |

The paired hash sidecar is `evaluation/datasets/development_pilot/runs/research_v1_rehearsal_662bd5c/artifact_sha256.json`. Its `attempts.jsonl` entry is `54b183679376e6f6279106fbe714c90c124e4dce117190242efc56b58f71bc46`; a read-only SHA-256 recomputation of the attempts file matched that value.

The raw historical Development rehearsal records are maintained and provided separately from the publication branch at the paths above. `attempts.jsonl` and its checksum sidecar are the underlying evidence for the historical counts and checksum reported here. This evidence is not a current controlled-run record and does not establish current runtime readiness, resource compatibility, or collection authorization. The raw report records are not being added to the publication branch as part of this documentation update.

## Failure evidence boundary

The historical rehearsal contains no recorded failure: all 52 timing statuses are `returned`, and the outcome states are abstention or directional.

Failure retention is demonstrated separately by the synthetic test `tests/test_game_collection.py::test_failures_retained_without_dropping_or_stopping`. It injects fake `VerifierUnavailable`, `VerifierExecutionFailure`, `TimeoutError`, and `RuntimeError` outcomes and checks that rows and timing statuses are retained. The synthetic test `tests/test_game_collection.py::test_prerequisites_unavailable_and_abstention_are_distinct` distinguishes an executed abstention from a prerequisite-ineligible, unexecuted `unavailable` outcome. These tests do not constitute historical live failure evidence.

## What this evidence supports

The historical Development rehearsal supports the claim that actual execution records contained verifier report payloads, outcome states including abstentions, and returned timing measurements for the four listed verifiers. The checksum match supports the integrity of the attempts file against its recorded sidecar value.

Together with the synthetic tests, this supports the engineering claim that failure outcomes and prerequisite-unavailable outcomes have distinct recording behavior. The evidence sources remain separate: the rehearsal is historical execution evidence; the failure-path tests are synthetic evidence.

## What this evidence does not establish

This inventory does not establish:

- current runtime readiness or current resource compatibility;
- current live service compatibility;
- an approved research-specific runtime configuration;
- a new authorized controlled collection run;
- historical live failure evidence;
- collection authorization or supported-platform durability certification.

## Relationship to Vasavi's checklist Item 2

Historical evidence supports recorded reports, abstentions/outcomes, and returned timings. Synthetic tests support failure recording and the distinction between abstention and prerequisite unavailability. A recorded failure is absent from the historical rehearsal.

The remaining evidence gap is a **new, owner-authorized controlled run** using a reviewed configuration and validated resources/platform that records the relevant outcomes and timings. This document and the cited evidence do not authorize or perform that run.
