# Dated protocol amendment

Machine record: `evidence/final_test_protocol_amendment.json`. Narrative source, not rewritten by this package: `evaluation/docs/final_test_self_custody_amendment_2026-11-13.md`.

| Field | Value |
| --- | --- |
| Record type | `final_test_v2_self_custody_amendment_v1` |
| Date | 2026-11-13 |
| Custody status | `SELF_CUSTODY` |
| Independent custody | false |
| Independent verification | false |
| Signed evidence | false |
| Approver | null |
| Approval date | null |
| Research-lead approval | `PENDING` |
| Research-lead scoring authorization | `PENDING` |
| Operational scoring | `NOT_AUTHORIZED_UNTIL_FREEZE_AND_RESEARCH_LEAD_AUTHORIZATION` |
| Labels parsed by this amendment | false |
| Experiment executed | false |

## What changed

The amendment sets operational custody to `SELF_CUSTODY` and records that the label file moved outside the repository. The location record is `evidence/final_test_label_location_metadata.json`. It preserves, and does not replace:

- `evaluation/config/final_test_v2_custodian_appointment.json`
- `evaluation/config/research_v1/independent_custodian_appointment.json`
- `evaluation/config/research_v1/final_test_self_custody.json`

The preserved self-custody declaration still contains the contradictory scoring fields described in [05_final_test_v2_custody.md](05_final_test_v2_custody.md). The amendment says the researcher's earlier unsigned scoring confirmation is preserved and does not unseal the labels.

## Seal

The seal text is `SEALED_UNTIL_STUDY_CONFIGURATION_POLICIES_BASELINES_AND_EVALUATION_RULES_ARE_FROZEN`.

All four flags are false:

- `study_configuration_frozen`
- `policies_frozen`
- `baselines_frozen`
- `evaluation_rules_frozen`

`evaluation/config/research_v1/final_test_v2_experimental_configuration_manifest.json` still marks loss, threshold, bootstrap, coefficient, budget, model-weight hashes, and the evidence-corpus approval as `APPROVED_BY_TEAM_VALUE_REQUIRED` with `approved_value` null. That file is a pending inventory. It is not copied as an approval.

## Timing relative to Experiment 3

The amendment date is 2026-11-13. Experiment 3's empirical run manifest records the completing collection process from 2026-11-14T11:24:21.194Z to 2026-11-14T11:56:55.911Z. The amendment predates that Development collection.

The amendment does not authorize that collection. Experiment 3 did not use Final Test labels. The collection's own manifest says `final_test_accessed` is false. The amendment also does not supply the missing numeric protocol approvals. Those remain pending in the experimental-configuration inventory.

## Missing authorization

There is no research-lead signature, no approval date, and no protocol hash. Verbal or team statements recorded elsewhere are marked unsigned. This package does not add an approval after the fact.

The methodology note in `evaluation/docs/scientific_protocol_index.md` says any later Final Test result must disclose that the dataset creator retained access, that repository controls do not stop a direct read, and that independent custody was not established. That index still describes collection as unauthorized. That sentence is stale for the completed Development run and current for Final Test scoring.
