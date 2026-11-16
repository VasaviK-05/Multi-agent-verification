# Experiment 2 Approval Reconciliation

**Record type:** Documentation-only approval reconciliation
**Branch:** `experiment-2-budget-sensitivity`
**Date recorded:** 2026-11-16

## 1. Purpose

This document records the distinction between the earlier Development eligibility approval, subsequent Experiment 2 activity approvals reported by the study owner, and the remaining formal research-team sign-off requirement.

It does not replace, modify, or retroactively alter any historical approval manifest, execution record, or experiment artifact.

## 2. Earlier Development eligibility approval

The preserved manifest:

`docs/experiment2-evidence/approved_development_eligibility_artifacts/artifacts/person1/research_v1_exploratory_eligibility_approved_v1/eligibility_manifest.json`

records:

- Approver: Research Lead
- Approval date: 2026-11-13
- Status: `APPROVED_BY_RESEARCH_LEAD`
- Scope: Development eligibility for `research_v1_exploratory_v1` only.

The manifest explicitly excludes authorization for verifier collection, attempt recording, protocol freeze, Experiment 2 budgets, policy fitting, confirmatory evaluation, and Final Test label release.

This approval is recognized only within its recorded scope.

## 3. Separately reported Experiment 2 approvals

The study owner has confirmed that the research lead separately granted approval for the Experiment 2 activities, including:

- Verifier collection
- Attempt recording
- Protocol freeze
- Experiment 2 budget levels
- Policy fitting

These approvals are recorded here as externally reported approvals.

**Documentary limitation:** The inspected repository evidence did not contain a separate signed approval receipt, approval identifier, or complete authorization record establishing these later approvals. This document does not invent an approval ID, approval date, or signed evidence.

The reported approvals must not be confused with the narrower 13 November Development eligibility approval or with approvals for other campaigns.

## 4. Historical metadata discrepancy

The existing Experiment 2 run metadata records:

`budget_levels_require_team_approval = true`

This value is preserved as historical artifact metadata.

It is not treated as proof that approval remains outstanding, given the study owner's subsequent confirmation of approval.

The original metadata is not silently rewritten. This reconciliation record documents the discrepancy without changing the historical evidence.

## 5. Protocol inventory

The preserved `research_protocol_inventory_v1.json` records:

- `approved = false`
- `frozen = false`
- `collection_authorized = false`

These values remain unchanged. They describe that inventory's recorded state and are not retroactively overwritten by this document.

## 6. Scope and safeguards

This reconciliation:

- Does not rerun experiments or verifier campaigns.
- Does not regenerate historical results.
- Does not modify immutable historical manifests or execution records.
- Does not authorize Final Test access or evaluation.
- Does not establish fresh verifier performance or experimental superiority.
- Does not claim that formal Experiment 2 completion has been approved.

The separate `reference-fresh-v1` evidence remains distinct from `multitask-policy42`.

## 7. Remaining closure requirement

Formal Experiment 2 completion remains subject to research-team review and sign-off.

Activity authorization and formal study closure are separate decisions. This document records the reported activity approvals but does not substitute for the final research-team sign-off.

## 8. Reconciliation conclusion

The earlier Development eligibility approval, later reported Experiment 2 activity approvals, and historical protocol/run metadata are distinct records with different scopes and dates.

The available evidence supports documenting the discrepancy and the study owner's approval confirmation. It does not support rewriting historical approval fields or claiming that a signed approval artifact was recovered.

This document is a supplementary reconciliation record, not a replacement for original evidence.
