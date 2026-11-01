# Broader verifier-cost collection: prepared, not authorized

Prepared 2026-10-28. No new verifier attempt, generation, model initialization,
download or live metadata request was made. Original diagnostic artifacts are unchanged.

## Concrete roster and limits

`roster.json` contains all populated inputs, captured actual heuristic analyses,
prerequisite plans, character/word lengths, source identities and execution order.
Source: the six factual diagnostic preparation rows and the separately authorized
arithmetic pilot's 80 history/development rows. Original answers, references, roles,
groups and example IDs are preserved. Only run IDs are new. Labels are removed.
No final contents/outcomes were opened; only both requests' exclusion metadata was used.

There are 43 history and 43 development examples: addition 14, subtraction 24,
multiplication 22, division 20, factual 6. Every category schedules all four verifiers;
each verifier receives 86 examples. Answer lengths span 2–199 characters / 1–29 words.
Arithmetic answers exercise active numerical rule checks, including substantive positive
and negative candidates already present in the approved source. Factual examples exercise
the rule unsupported/abstention path. Inputs were not modified to force any judgment.

One pass, no warmups, no retries. A single `random.Random(20261028)` shuffle fixes example
order; candidate order is semantic, evidence, rule, confidence. All measured first-call
effects are retained. Sequential calls, CPU, existing five confidence samples at temperature
0.8 with seeds 0..4 and 60-second per-generation timeout. Models initialize once in the
collector process. Existing retrieval/model caches remain as implemented; no cache flushing
or assumption of cold/warm state. Resource hashing and construction are outside the timer.

The recording proposal has **344 attempts, at most 430 local generation calls and
1,380 live metadata GETs (4 factory + 4 per attempted call), zero downloads and paid
services**. Preflight here only hashes local resources and saved service observations;
the factory must revalidate service identity live before attempts. Logical model hashing
can exceed 460 GB over 690 observations, outside verifier timings. Generation timeout
allowances sum to 25,800 seconds, not an elapsed-runtime forecast.

This convenience engineering sample targets these specific local factual and constructed
reference-assisted arithmetic paths. It is arithmetic-heavy, has no long-form answers,
structural/format checks, multilingual, large corpus, concurrent serving or designed
failure/timeout sample. It cannot establish representative project-wide costs or reliable
tails. Do not create failures or change answers to fill a desired outcome quota.
Statuses, abstentions and failures for new attempts are unknown until execution.
Historical rule/semantic arithmetic calls all returned directional results; historical
factual rule calls all abstained and confidence abstained twice. Evidence usefulness
remains affected by the known topic-gating defect.

## Readiness and setup

`resource-preflight.json`: local bindings ready, including separately built ten-chunk
index receipt. New inspection matches factual setup
`93029e22dfadd1babdfb360f70252113ede0ca17f58bf106ee18b44aea8a9750`.
No execution-relevant application change was found. It differs from the arithmetic
setup; no old measurements are pooled or rebound. Any subsequent application/resource
change requires a fresh inspected identity, new request and fresh measurements.

The evidence regression still has three failures and one neutral control pass: strong
entailment/rejection become uncertainty; conflict reports no_relevant_evidence. See the
original handoff's duplicate tokenizer/topic-gate analysis. Actual heuristic requirements
remain unknown for four factual questions. These affect verification usefulness/fitting,
not valid per-call timing. Owners must repair them separately; no algorithms or routing
outputs were manually changed here. Policy fitting is outside this task.

`recording-request.pending.json` uses the existing label-free diagnostic schema and
same report/measurement collector. All split/prerequisite fields validate; its sole
schema failure is `preparation_authorization: Input should be a valid string` because
new permission is deliberately null. It has no scientific custody or approval claim.
This path retains reports and verified per-attempt resources, but **cannot export calibration**.
Approval of execution alone does not change that contract.

## Existing legitimate calibration

`existing-calibration-validation.json` reload-validates the existing arithmetic artifact
against its original measurement export and recomputes its digest/estimator through
CalibrationArtifact. Existing calibration ID:
`c32267151f0fdf265ca502652f11f6828d967b985ab1efbd7a33fdd69d117398`.
Input digest: `eb72570f52aa22fe074bbdfa40b53db5e4c2d27a6a6ca4b3a29c6a2276f1b307`.
Setup: `a560bccc2d7f5a99fd33c0b0b502c23c7c4a968e7ca683c3550cdc6bb8835ae2`.
All 80 calls per verifier included; zero failures, timeouts, abstentions or exclusions.
No recalibration or duplicate artifact was necessary. This only describes that historical
two-thread CPU, rule/semantic, constructed arithmetic setup. It does not calibrate all four.

The six-example diagnostic remains blocked by its explicit diagnostic export guard,
unapproved scientific reservation and absent freeze. No new calibration was produced.

## Commands after real permission (do not execute both alternatives)

For report-preserving diagnostic collection, copy the pending request to a new
`recording-request.authorized.json` and replace ONLY its null preparation_authorization
with the genuine scope-specific human approval reference. Record this plan's workload
with that approval; do not insert study/custody/freeze approvals. Then:

```powershell
$env:HF_HUB_OFFLINE='1'
$env:TRANSFORMERS_OFFLINE='1'
$env:NO_PROXY='localhost,127.0.0.1,::1'
$env:VERIFIER_COLLECTION_ADAPTER_CONFIG=(Resolve-Path build/broader-cost-measurement-20261028-v1/adapter.json).Path
.venv/Scripts/python.exe -m app.game.offline.collect validate build/broader-cost-measurement-20261028-v1/recording-request.authorized.json
.venv/Scripts/python.exe -m app.benchmark.project_adapter preflight build/broader-cost-measurement-20261028-v1/adapter.json --output build/broader-cost-measurement-20261028-v1/preflight-before-run.json
.venv/Scripts/python.exe -m app.game.offline.collect collect build/broader-cost-measurement-20261028-v1/recording-request.authorized.json --output-dir build/broader-cost-measurement-20261028-v1/recordings
.venv/Scripts/python.exe -m app.game.offline.collect check build/broader-cost-measurement-20261028-v1/recordings
```

For calibration instead, `cost-request.pending.json` is a fully populated **alternative**
existing label-free cost-only request, requiring real new preparation permission and a
genuine combined final reservation custody record. `calibration-settings.pending.json`
requires the identical genuine reservation and a real measurement freeze record.
Warmup rule proposed is include all (no warmups scheduled). Neither record was invented.
This alternative uses the existing two-value factory: **344 attempts, up to 430 generations,
4 factory metadata GETs**, zero downloads/paid services; it stops on a raised exception,
preserving partial measurements. Unlike the recording bridge it does not retain full
reports/per-call resource snapshots or abstention counts; those cannot be fabricated.
Choose/approve the workflow explicitly before execution; do not run both as one approval.

After those real records exist, save new `.authorized.json` copies and run:

```powershell
# Same offline environment and adapter config as above.
.venv/Scripts/python.exe -m app.benchmark.collect_costs build/broader-cost-measurement-20261028-v1/cost-request.authorized.json --output build/broader-cost-measurement-20261028-v1/measurements.json
.venv/Scripts/python.exe -m app.game.offline.calibration build/broader-cost-measurement-20261028-v1/calibration-settings.authorized.json --measurements build/broader-cost-measurement-20261028-v1/measurements.json --output build/broader-cost-measurement-20261028-v1/calibration-v1.json
```

No correctness labels are needed for that cost-only path. Missing verifier observations
block calibration; failed measured attempts are included. No diagnostic promotion,
fabricated witness, loss/prior/budget/resource-weight choice or policy fitting is allowed.
Costs estimate sums of verifier-attempt wall times in milliseconds, not money, CPU time
or parallel request latency.
