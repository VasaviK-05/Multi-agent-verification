\# Experiment 2 — Consolidated Evidence Register



\## 1. Purpose



This register consolidates the current evidence and documentation status for Experiment 2: Budget Sensitivity Analysis.



It distinguishes:

\- Existing historical campaign evidence

\- Development-only budget sensitivity analysis

\- Separate exploratory evidence

\- Outstanding provenance requirements

\- Protected evaluation data



This register is a documentation and tracking artifact. It does not certify formal Experiment 2 completion.



\## 2. Evidence inventory



| Evidence item | Current status | Notes |

|---|---|---|

| Historical `multitask-policy42` campaign | Partially documented | Historical campaign records exist, but provenance gaps remain |

| Budget sensitivity results | Documented | Results recorded in `EXPERIMENT\_2\_BUDGET\_SENSITIVITY\_RESULTS.md` |

| Budget sensitivity notebook | Cleanup performed; validation/commit pending | Do not rerun cells that write to existing output directories |

| `reference-fresh-v1` exploratory archive | Reviewed separately | Contains Development artifacts; not proof of original campaign continuity |

| Reference-fresh provenance review | Documented | Recorded in `EXPERIMENT\_2\_REFERENCE\_FRESH\_PROVENANCE\_REVIEW.md` |

| Original execution-source custody archive | Outstanding | Not recovered |

| Arithmetic historical training manifest | Outstanding | Original artifact not established |

| Factual historical training manifest | Outstanding | Original artifact not established |

| Arithmetic Development evaluation | Outstanding | Original artifact not established |

| Factual Development evaluation | Outstanding | Original artifact not established |

| Source revision and collection environment verification | Outstanding | Historical source custody remains unresolved |

| Final Test payload | Protected | Not accessed or evaluated |



\## 3. Budget sensitivity findings



The existing Development-only analysis evaluated three approved budget levels:



| Scenario | Budget fraction | Budget |

|---|---:|---:|

| B1 | 50% | 8,297.39 ms |

| B2 | 75% | 12,446.09 ms |

| B3 | 100% | 16,594.78 ms |



The minimax analysis selected the semantic-only, reputation-weighted strategy with probability 1.0 for all three budget scenarios.



Key observations:

\- All 20 cases per scenario remained uncertain.

\- Decision coverage was 0%.

\- No false accepts or false rejects occurred.

\- Mean loss was approximately 0.200615.

\- The 90% clean-coverage constraint was infeasible at all three budget levels.



The result is mathematically optimal under the encoded objective but operationally unhelpful because the selected policy abstains on every case.



\## 4. Baseline findings



The documented baseline analysis reported:



\- `coverage\_aware\_greedy`: 80% clean coverage, 0.04 clean decision loss.

\- `development\_best\_fixed`: 80% clean coverage, 0.04 clean decision loss.

\- `policy`: 66.67% clean coverage, approximately 0.0667 clean decision loss.

\- Suppression: 0% coverage, with unresolved decisions.



Forced-support and forced-rejection analyses also exposed false accepts and false rejects.



These baseline measurements and minimax measurements represent different analytical contexts. They should not be presented as a direct cost-efficiency comparison.



\## 5. Reference-fresh exploratory evidence



The `person3-prerequisite-artifacts.zip` archive contains a separate `reference-fresh-v1` exploratory study.



Findings:

\- Development training-manifest and evaluation artifacts are present.

\- The protocol describes a resumed exploratory study, not an uninterrupted campaign.

\- `policy\_id` and `candidate\_freeze\_id` are null in the artifact identity record.

\- The Development evaluation shares the manifest and compatibility IDs previously associated with `reference-50-v1`.

\- Final Test reservation metadata is present, but the protected payload has not been accessed.



This archive must remain separate from the original `multitask-policy42` campaign evidence.



\## 6. Outstanding provenance requirements



The following remain unresolved:



1\. Recover or establish the original Arithmetic training manifest.

2\. Recover or establish the original Factual training manifest.

3\. Recover or establish the original Arithmetic Development evaluation.

4\. Recover or establish the original Factual Development evaluation.

5\. Locate the original execution-source custody archive.

6\. Verify the original source revision and collection environment.

7\. Resolve outstanding source-to-archive hash and compatibility questions.

8\. Establish the required historical provenance before making a formal completion claim.



The existence of separate exploratory artifacts does not close these requirements.



\## 7. Scope and data-protection constraints



The following constraints apply to further work:



\- Do not inspect, load, or evaluate Final Test payloads.

\- Do not initiate additional verifier executions without a separate justified and approved need.

\- Preserve historical evidence archives unchanged.

\- Keep exploratory evidence separate from historical campaign evidence.

\- Do not modify `main`.

\- Use the existing feature branch and pull-request workflow.

\- Keep application and verifier logic outside the scope of this documentation task.



\## 8. Current overall assessment



| Area | Assessment |

|---|---|

| Budget sensitivity analysis | Documented |

| Minimax findings | Documented |

| Exploratory archive review | Documented separately |

| Original campaign provenance | Incomplete |

| Protected Final Test data | Untouched |

| Formal Experiment 2 completion | Not established |



\## 9. Recommended next action



Continue provenance reconciliation using the original historical evidence sources. Do not substitute `reference-fresh-v1` artifacts for missing original campaign records.



Any future change to the formal completion assessment must be supported by verified source artifacts and documented compatibility evidence.



\---



\*\*Register status:\*\* Documentation snapshot

\*\*Interpretation:\*\* Development analysis documented; original historical provenance remains incomplete; formal Experiment 2 completion is not established.
