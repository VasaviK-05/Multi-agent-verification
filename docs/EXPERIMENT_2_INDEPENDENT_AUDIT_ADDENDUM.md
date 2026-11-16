# Experiment 2 — Independent Budget Sensitivity Audit Addendum

**Date:** 16 November 2026  
**Branch:** `experiment-2-budget-sensitivity`  
**Scope:** Independent validation of existing Development-only budget sensitivity results and review of the associated coverage and budget-reuse code.

## 1. Purpose

This addendum records the independent numerical audit of the three-budget minimax analysis. It supplements the existing Experiment 2 results and evidence register. It does not replace historical artifacts or assert that unresolved provenance issues have been resolved.

## 2. Independent numerical validation

The three budget levels were checked against the supplied Development evaluation and the recorded results.

| Measure | B1 — 50% | B2 — 75% | B3 — 100% |
|---|---:|---:|---:|
| Budget (ms) | 8,297.392291 | 12,446.088437 | 16,594.784582 |
| Feasible strategies | 8 | 8 | 16 |
| Minimax worst-case loss | 0.20061508 | 0.20061508 | 0.20061508 |
| Selected strategy | Semantic-only | Semantic-only | Semantic-only |
| Selected strategy probability | 1.0 | 1.0 | 1.0 |

The independent calculations reproduced the recorded minimax values and strategy selection.

The Development evaluation contains 1,600 outcome records for the 16-strategy, five-attack, 20-example evaluation. The recorded budget projections reuse 800, 800 and 1,600 outcomes for B1, B2 and B3 respectively.

No new verifier executions or Final Test evaluations were performed for this audit.

## 3. Interpretation of clean coverage

The selected semantic-only strategy has 0% clean coverage. Other feasible strategies have 60% clean coverage.

The supplied `coverage_contract.py` describes the coverage obligation as additive and Development-only, explicitly distinguishing it from an attacked-coverage promise.

Its `check_coverage_matrix()` function verifies:
- The coverage constraint is bound to the planning context.
- The training binding matches the context's offline evaluation identity.
- The coverage-augmented matrix retains the original Development payoff matrix identity.

The supplied file defines a `CoverageCertificate`, but does not itself implement or demonstrate the certificate-generation and optimization enforcement path.

**Disposition:** The coverage metadata binding is verified. Whether the 50% minimum is enforced by the optimization certificate remains unconfirmed from the supplied source.

## 4. Budget-reuse compatibility limitation

Review of `budget_sensitivity.py` identified that `execution_contract_json` is excluded from the source/target context equality comparison.

The notebook's target-context construction also sets this field to `None`.

Consequently, the reuse guard does not independently establish equality of source and target execution contracts. The existing numerical results remain reproducible, but the code's stronger claim that only the hard budget changes requires qualification.

**Disposition:** Record as a compatibility-validation limitation. No historical results or source code were modified as part of this audit.

## 5. Research and data boundaries

This audit:
- Used existing Development evidence.
- Did not regenerate historical campaign artifacts.
- Did not execute verifiers.
- Did not access Final Test labels or payloads.
- Did not fit or activate a new policy.
- Did not modify teammate-owned verifier, reputation or model logic.

## 6. Overall conclusion

The three-budget minimax numerical results and associated Development metric summaries are independently reproduced.

The audit does not establish complete historical provenance, rehearsal admission, coverage-certificate enforcement, or full execution-contract compatibility.

The results may be reported as independently numerically reproduced Development-only budget sensitivity findings, subject to the limitations above. Formal Experiment 2 closure remains subject to research-team review and sign-off.

## 7. Required closure actions

1. Confirm the coverage-certificate enforcement path from its implementation and recorded certificate.
2. Record the execution-contract equality limitation in the evidence register.
3. **Closed as an unrecoverable provenance limitation:** Raunak's read-only audit documents that the original rehearsal archive and the source material needed to explain the false-to-true flag discrepancy were unavailable within inspected custody sources. The 32 attempts remain excluded from admitted Experiment 2 evidence; identity-level exclusion remains unverified.
4. **Recorded, not silently reconciled in historical artifacts:** the study owner separately reports research-lead approval for Experiment 2 collection, recording, protocol freeze, budget levels and policy fitting. The research-protocol proposal still records `PENDING_PERSON2_COSTS_AND_APPROVAL` and `collection_authorized: false`; preserve that historical metadata and distinguish it from the separately reported activity approvals. The separate signed approval artifact was not located in the inspected repository evidence.
5. Obtain research-team sign-off before declaring formal Experiment 2 completion.

**Final status:** Numerical audit reproduced; compatibility and provenance limitations documented; formal closure pending.

## 8. Final source-custody reconciliation

Raunak's owner-published read-only reconciliation dated 16 November 2026 classifies the requested original execution-source archive and all three requested application source sets as **UNRECOVERABLE WITHIN AVAILABLE CUSTODY SOURCES**. It separately verifies the 120-entry custody hash list as metadata only, not the source bytes, and confirms the previously recovered producer script only within that script's own scope.

The search boundary remains explicit: the external machine was not accessed, OneDrive was searched by filename rather than by hashing every file, and remote CI artifacts were not queried. The historical dependency lock and complete source trees were not recovered. Do not substitute current application files, installed packages, or the producer script for the missing historical source sets.

The proposal at `evaluation/config/experiments/experiment2_proposal.json` retains `PENDING_PERSON2_COSTS_AND_APPROVAL` and `collection_authorized: false`. These are historical proposal fields. They are distinct from the study owner's separately reported research-lead approvals for Experiment 2 activities; the separate signed approval artifact was not located in the inspected repository evidence. Do not rewrite the proposal or infer an approval identifier.

**Supporting owner reconciliation:** `evaluation/docs/experiment2_final_source_custody_reconciliation.md`, branch `raunak-exp-3`, commit `3860bc7`.

**Disposition:** Source-custody limitation documented; no historical artifacts changed; formal Experiment 2 sign-off remains outstanding.
