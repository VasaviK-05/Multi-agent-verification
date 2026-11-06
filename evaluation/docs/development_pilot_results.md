# Development feasibility pilot results

## Status

**Blocked before verifier execution.** The local environment has no VERIFIER_COLLECTION_ADAPTER_CONFIG, and no adapter JSON was found under evaluation. The runner's fail-closed preflight therefore made zero verifier calls. No simulated outputs were substituted. This is a recorded blocked pilot, not a completed empirical verifier pilot.

## Dataset and roster

Source dataset: research_v1, Development partition only. The runner read the Development prepared roster and Development reconciled candidates; History inputs and Final Test records were not accessed. Input file hashes are stored in evaluation/datasets/development_pilot/research_v1_feasibility_v2/pilot_manifest.json.

| Benchmark | Development groups | Candidate records | Verified correct | Verified incorrect | Unresolved | Eligible candidates |
|---|---:|---:|---:|---:|---:|---:|
| GSM8K | 200 | 400 | 187 | 91 | 122 | 278 |
| HotpotQA | 200 | 410 | 200 | 0 | 210 | 200 |
| **Total** | **400** | **810** | **387** | **91** | **332** | **478** |

The 478 eligible candidates cover 387 groups. Thirteen groups contain no binary-labelled candidate. Unresolved candidates were left unattempted. The eligible roster would require 478 calls per verifier, 1,912 total, if preflight passed.

## Execution counts and outcomes

| Verifier | GSM8K | HotpotQA | Calls made | Status |
|---|---|---|---:|---|
| Semantic | Not executed | Not executed | 0 | Shared adapter configuration unset |
| Evidence | Not executed | Not executed | 0 | Shared adapter configuration unset |
| Rule | Not executed | Not executed | 0 | Shared adapter configuration unset |
| Confidence | Not executed | Not executed | 0 | Shared adapter configuration unset |

Attemptable groups: **0**. Actual verifier calls: **0 of 1,912 expected**. No call failed or returned unresolved because no call began; the execution failure rate, output coverage, decision outcomes, verifier disagreement, outcome variance, and group-dependence estimates are therefore **unavailable**, not zero. The blocked artifact records zero Attempts and 332 unresolved candidates not attempted.

The pipeline's code supports the four named verifiers for direct calls, but benchmark-specific technical availability was not verified. The rule verifier's scientific applicability to GSM8K/HotpotQA is also not an approved benchmark-eligibility decision. No verifier should be described as available on either benchmark based on this blocked run.

## Runtime, resources, costs, and hashes

No verifier latency, wall-clock pilot duration, resource consumption during calls, or estimated attempt cost was measured. Latency is not used as a proxy for monetary cost or research loss.

Blocked preflight environment recorded: Windows 11, Python 3.12.1, 16 logical CPUs. The runtime package inventory recorded NumPy 2.5.3, Pydantic 2.13.5, sentence-transformers 6.0.1, Transformers 5.17.0, Torch 2.14.0, faiss-cpu 1.15.1, Requests 2.34.2, Safetensors 0.8.0, and Tokenizers 0.23.2. These installed packages do not establish that local weights or services are usable.

Adapter configuration hash, model snapshot hashes, service model digest, corpus hash, and index hash are **not available** because no adapter configuration was supplied. The missing dependency is VERIFIER_COLLECTION_ADAPTER_CONFIG; its absence prevents inspection of those resources.

Recorded hashes from the blocked run:

| Artifact | SHA-256 |
|---|---|
| Development prepared source | 323aaf326f07ae5d999bb3db46e5d761f418e9bc22615d4b5ddd25102ab8cd7f |
| Development reconciled source | 2c6272ae74a68e56ef9476716ce651c593dbe3ea5639ff0fde427cad926b55e3 |
| Pilot runner source | 4c96593567836504004afd27f7524f3debd6d6a1f7de84b939d507c4025e8f05 |
| Existing real-call attempt recorder | 761349b966e62385b7a17578564e34c13d3d210cc8ad4cabe97608025179b8d6 |
| Readiness validator source | bf9e9d5f82f2cb5823ad6124214e670a8b66481266c57436d56f320fb25ed589 |
| Pilot manifest | 10d80727cd44f37d3815c04612db5cfcc84e1749c89498961412583df0fb358c |
| Pilot result summary | 2fb189f2473402c717cdf9741c6b4c8748c560dbba99ede58358e420239550d2 |

Generated artifacts:

- evaluation/datasets/development_pilot/research_v1_feasibility_v2/pilot_manifest.json
- evaluation/datasets/development_pilot/research_v1_feasibility_v2/pilot_results.json
- evaluation/datasets/development_pilot/research_v1_feasibility_v2/artifact_sha256.json

The manifest stores Development input hashes, runner/collector/readiness-validator hashes, environment details, exact counts, and the preflight blocker. The SHA-256 receipt covers the manifest and results summary.

## Sample-size planning implications

This run produces **no outcome-derived variance, paired disagreement, coverage, failure-rate, runtime, or group-dependence estimate**. It cannot support a Final Test sample-size recommendation or a power calculation. The 400 Development groups are the existing partition size, not a selected or statistically justified sample.

Once real calls are possible, report per-verifier group-averaged outcomes and paired differences on the same eligible groups. Estimate candidate-level paired disagreement and within-group dependence only where multiple labeled candidates exist. Preserve group as the resampling unit. A numeric confidence-interval width or power target, interval level, resampling procedure, effect-size target, and compute budget still need approval. HotpotQA currently has no verified incorrect candidates, so its false-acceptance behavior cannot be estimated from this label set.

## Readiness and limits

The readiness validator reports **exploratory readiness: LIMITED** and **confirmatory readiness: BLOCKED**. No offline Examples were created, no policy was fitted, and policy_fitting_ready remains false. Final Test remains disabled.

After the resource owner supplies a reviewed adapter configuration and its local snapshots, corpus/index, and loopback service pass preflight, rerun into a new versioned output directory. Review verifier eligibility by benchmark before interpreting outcomes. Human label adjudication, sample-size assumptions, loss/threshold/resource settings, and confirmatory custody remain separate approvals.
