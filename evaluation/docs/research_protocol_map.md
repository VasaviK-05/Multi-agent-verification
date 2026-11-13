# Research protocol map

Status of this map: proposal inventory, not a freeze. Development eligibility for `research_v1_exploratory_v1` is approved. Loss, threshold, budgets, attacks, dependency, sample size, and protocol freeze are not. Collection and Final Test evaluation are not authorized.

| Item | Reference | Status |
|---|---|---|
| Settings proposal | `evaluation/config/research_settings_proposal_v1.json` | `approved: false`; approver null |
| Readiness flags | `evaluation/config/protocol_readiness.yaml` | every scientific `approved` flag is false |
| Experiment 1 | `evaluation/docs/experiment1_protocol.md`; `evaluation/config/experiments/experiment1_proposal.json` | `PENDING_APPROVAL`; specification ID null |
| Experiment 2 | `evaluation/docs/experiment2_protocol.md`; `evaluation/config/experiments/experiment2_proposal.json` | budgets null; blocked on Person 2 |
| Experiment 3 | `evaluation/docs/experiment3_protocol.md`; `evaluation/config/experiments/experiment3_proposal.json` | empirical run pending; synthetic fixture is separate |
| Experiment 4 | `evaluation/docs/experiment4_protocol.md`; `evaluation/config/experiments/experiment4_proposal.json` | blocked on Person 2 and Person 3 |
| `research_v1` | `evaluation/datasets/reconciled_candidates/research_v1/` | built population; its eligibility roster is `research_v1_person1_v1` |
| `research_v1_exploratory_v1` | snapshot manifest SHA-256 `5e55dbd17bf968eaa7768819945ab3adfc3b30d850817b859c63015e9db03764` | provisional labels |
| Exploratory eligibility | `evaluation/artifacts/person1/research_v1_exploratory_eligibility_approved_v1/` | `APPROVED_BY_RESEARCH_LEAD`, Research Lead, 2026-11-13; body SHA-256 `f2cc0fd108b961bf4795767df4f90e92d7fa0f418ef9865d0206f32d7b45282d`; file SHA-256 `75087c28f01e566be0572c149a182f5b02872f2973bcb32156bb607ecdac1eaa`; 744 candidates, 372 groups. The provisional audit `9f220e4d9affa2e10d088cd6afcd2587b318912a4b4f0568d5617e3976693ac4` is preserved and is not this roster. Not the 478-candidate `research_v1` roster |
| Final Test v2 | recorded content hash `e572093a4f0420c03316c89c83b6a7ab665af3af894d19a1428a6b091d3319ee` | `NOT_AUTHORIZED`; designated non-independent custody; protocol freeze pending |
| Retired Final Test | `research_v1_final_test_provisional_v1` | retired; not reusable |
| Loss, threshold, coverage, attacks, dependency, bootstrap | settings proposal | proposed or pending; not approved |
| Cost measurements | none | Person 2 |
| Fitted policies | none for this protocol | Person 3 |

Experiments 1 and 3 share the same proposed methods, loss, attacks, and eligibility rule. Experiment 2 may change only the budget, and only after the resource coefficient is a fixed approved number. Experiment 4 consumes a Person 3 policy; it does not refit one. Final Test v2 is prohibited for all four development activities.

File hashes of the proposal JSON records are written by `exploratory_eligibility.protocol_inventory` to `evaluation/artifacts/person1/research_protocol_inventory_v1.json`.
