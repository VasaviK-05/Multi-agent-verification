# Development-only feasibility pilot

## Scope and boundary

The pilot runner is evaluation/data_preparation/run_development_feasibility_pilot.py. It reads only:

- evaluation/datasets/offline_examples/research_v1/development_prepared.jsonl
- evaluation/datasets/reconciled_candidates/research_v1/development_candidates.jsonl

It validates that every row belongs to Development, checks candidate identity and binary-label provenance, and never opens a History roster or any Final Test path. It does not modify source datasets, labels, manifests, or partitions. It calls the existing local-only project adapter and reuses the real TimedVerifier/Attempt recorder from run_verifier_attempts.py. It does not use baseline result files, mock outputs, or simulated verifier results.

Only candidates with an existing verified binary label and complete verifier input are scheduled. Unresolved candidates stay in a separate identity-only unresolved_not_attempted.jsonl ledger; they are not assigned labels or sent to verifiers. The input payload contains benchmark, question, candidate answer, and permitted evidence context only. The label is retained in memory for descriptive outcome analysis but is never sent to the verifier.

The roster is exhaustive for the eligible Development records; there is no sampled subset or invented pilot size. The current inventory has 478 eligible candidates in 387 groups, so four verifiers imply 1,912 calls if local preflight passes. The full Development partition has 400 groups; 13 groups have no binary-labelled candidate and cannot contribute an eligible outcome. This is a feasibility workload count, not a statistical sample-size claim.

## Reproducibility and resource pinning

Before any call, the project adapter must pass inspect_setup with a reviewed VERIFIER_COLLECTION_ADAPTER_CONFIG. Its manifest binds the adapter JSON hash, source hashes, source revision/digest, dependency versions, model snapshots, service observation, evidence corpus and index identities, and hardware/thread settings. Each Attempt records its resource observation and execution configuration ID. The roster is sorted by benchmark and candidate ID; no random sampling is used.

Run from the repository root:

~~~powershell
$env:VERIFIER_COLLECTION_ADAPTER_CONFIG = "path\to\reviewed_project_adapter.json"
.\.venv\Scripts\python.exe -m evaluation.data_preparation.run_development_feasibility_pilot run
~~~

The output directory is versioned and immutable when non-empty. --resume only accepts an identical input, code, resource, and configuration manifest. Validate outputs with:

~~~powershell
.\.venv\Scripts\python.exe -m evaluation.data_preparation.run_development_feasibility_pilot validate
~~~

When adapter configuration or resource preflight is unavailable, run writes a BLOCKED_PREFLIGHT manifest and result summary, makes zero calls, and records the missing requirement. It does not imply that each verifier is intrinsically unavailable; it marks each as not executed because the shared preflight gate failed.

## Measurements

The report separates real verifier states (directional, abstention, unavailable, failed, and missing output), verifier decisions, coverage, pairwise directional disagreement, descriptive group-level correctness variance, and within-group candidate-outcome association where enough paired data exist. Latency is a measured duration, not an estimated attempt cost and not research loss. The direct-call runner has no approved cost schedule, so cost remains unavailable rather than being inferred from duration.

The pilot does not construct offline Example records or fit policies. That conversion requires complete validated Attempts plus approved label, planning, cache, and readiness contracts. policy_fitting_ready remains false independently of whether direct calls succeed.

## Tests and limitations

Tests use fake verifier objects only to exercise the collector's failure and integrity handling. They do not count as verifier executions or pilot observations. Exact duplicate identity checks and source hashes do not establish semantic independence. Current benchmark label coverage is asymmetric: HotpotQA has no verified incorrect Development candidate, and the 91 GSM8K verified incorrect Development candidates come from the narrow gold+1 discrete-count rule. No human adjudication is claimed.
