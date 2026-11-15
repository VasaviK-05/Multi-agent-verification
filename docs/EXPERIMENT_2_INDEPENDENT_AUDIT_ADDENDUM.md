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
3. Obtain owner/custodian disposition of the rehearsal contamination discrepancy, or document the source as unrecoverable.
4. Reconcile recorded approvals with stale artifact metadata.
5. Obtain research-team sign-off before declaring formal Experiment 2 completion.

**Final status:** Numerical audit reproduced; compatibility and provenance limitations documented; formal closure pending.