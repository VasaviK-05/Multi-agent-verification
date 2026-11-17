# E4 — Established results

This package contains measured E4 results and their supporting records: four-verifier latency evidence, an independently timed Rule-only API execution, historical calibration and current cost observations, two exact selected-report finalization comparisons, and observed compatibility/execution checks.

## Contents

| Group | Established result | Files |
|---|---|---|
| Per-verifier latency | Separate Development rehearsal, historical API and reported local-diagnostic timings; original current API timing scopes remain separate. | [latency data](data/latency/), [rehearsal records](evidence/development-rehearsal/), [historical responses](evidence/historical-api/) |
| Runtime breakdown | Startup loading plus a directly timestamped synchronous endpoint partition; four direct overhead intervals, with nested aggregation separated from finalization. | [Runtime method](methods/runtime-timing.md), [stage data](data/runtime/stages.csv), [timing events](evidence/current-api/timed/timing-events.jsonl) |
| Estimated/actual cost | All 480 included historical calibration observations and the separately identified current Rule external-call observation. | [Cost method](methods/cost-comparison.md), [calibration data](data/calibration/) |
| Selected-report parity | Two exact comparisons against original saved API outputs, using unchanged selected Rule reports and frozen finalization inputs. | [Parity method](methods/selected-report-parity.md), [comparison table](data/parity/comparisons.csv), [paired outputs](data/parity/) |
| Compatibility/execution | Measured current Rule compatibility, historical resource/scope guards, budget-compatible execution and completed journals/audits/readbacks. | [Observed checks](compatibility-execution.md), [current API evidence](evidence/current-api/) |

## Evidence populations and interpretation

Development rehearsal: 52 returned attempts, 13 per verifier; 47 abstentions and five Semantic SUPPORT outcomes. Historical API: 16 response records contain 15 verifier reports. Reported direct diagnostics: eight Evidence and ten Semantic per-call timings; Rule/Confidence report aggregates retain their aggregate scope. Per-call datasets retain recorded observations, including abstentions and outliers.

The two original current API cases submit `What is 328 + 536?`, context `864`, and answers `864`/`865`. They return Rule SUPPORT/final passed and Rule REJECT/final failed. Both use a Rule-only selected team and reputation-weighted aggregation; their persistence readbacks are included. The package also retains the successful corrected stage-timed execution of the correct case. Its execution ID is `6cb09591-3858-4f81-8ec5-53d34cc6deae`.

| Measured boundary | Observed ms | Scope |
|---|---:|---|
| Bundle/policy loading | 159.6854 | Separate startup interval |
| Policy selection | 11.5038 | Request |
| Verifier wrapper stage | 1.2731 | Request |
| Aggregation | 6.4430 | Request |
| Finalization exclusive of aggregation | 11.6234 | Two direct request intervals |
| Remaining endpoint overhead | 613.7017 | Four direct request intervals |

The endpoint partition is 644.545 ms. The exact external native Rule call is 1.1290 ms, **nested inside** the verifier wrapper measurement and never added separately to that total. Loading is not added to the request partition. Internal, journal and HTTP timings are different scopes. These are bounded engineering observations with measurement overhead, not general performance estimates.

Frozen Rule estimated cost is 9.678209995036013 ms, budget 21258.33526502247 ms. The current cost comparison uses the exact external native verify-call timer. Historical calibration estimates are in-sample means of 120 included calls per verifier; eight warmups remain in the 488-observation raw source. The current point is kept separate from those distributions.

Parity is explicitly **selected-report runtime finalization**: numerical decision details, final status, coverage, reasons and execution states match in both pairs. Recorded rejection is an answer decision, not an execution exception. Historical Reference response records support historical timings; the current integrated evidence in this package is Rule-only.

## Integrity

[sources.json](provenance/sources.json) records original paths, SHA-256 values and extraction/metadata-normalization steps. Copied raw records retain their original bytes. Experimental values are unchanged; path metadata in derived CSVs is package-relative. Original local paths inside immutable raw records are historical provenance, not required document links. [files.md](files.md) lists every included file. [SHA256SUMS](SHA256SUMS) hashes every file except itself; [integrity.json](provenance/integrity.json) records packaging checks. This publication contains textual methodology and machine-readable evidence; image exports and plotting deliverables are excluded.
