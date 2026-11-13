# Final Test v2 custody team review checklist

Review the evidence in [final_test_custody_completion_report.md](final_test_custody_completion_report.md) and [final_test_custody_evidence_index.md](final_test_custody_evidence_index.md).

Blank fields are unsigned. Do not treat a blank, a template, or this checklist as approval. Do not open Final Test v2 labels while completing this review.

Verbal or team protocol approval is recorded only as `VERBAL_TEAM_APPROVAL_STATED` with `signed_evidence` false. Do not describe that statement as a signature. It does not confirm release or scoring. Release confirmation and scoring confirmation are separate actions and are not checked in the live declaration.

## Unsigned acknowledgment review

| Field | Entry |
|---|---|
| Reviewer name | |
| Role | |
| Date | |
| Evidence reference | `evaluation/config/research_v1/final_test_self_custody.json` protocol_approval; `unsigned_release_decision`; `unsigned_scoring_decision` |
| Decision | |
| Signature | |

Current evidence: limitations are acknowledged. Release is `AUTHORIZED`. Scoring is `AUTHORIZED` by a separate unsigned confirmation. `signed_evidence` is false. Independent custody is `NOT_ESTABLISHED`. Labels remain sealed. Final Test execution is `NOT_RUN`.

## Technical enforcement review

| Field | Entry |
|---|---|
| Reviewer name | |
| Role | |
| Date | |
| Evidence reference | `evaluation/research_readiness/v2_authorization.py`; `evaluation/tests/test_v2_custody_enforcement.py`; pytest 65 passed, 1 deselected, 0 failed |
| Decision | |
| Signature | |

Confirm the reviewer checked that release and scoring are separate, that the scoring command refuses, and that the sealed label path is refused before a read. Application checks do not replace operating-system access control.

## Custodian independence review

| Field | Entry |
|---|---|
| Reviewer name | |
| Role | |
| Date | |
| Evidence reference | `evaluation/config/final_test_v2_custodian_appointment.json`; `evaluation/config/research_v1/independent_custodian_appointment.json` |
| Decision | |
| Signature | |

Current evidence: designated custodian is the dataset creator; independent custodian id is null; identity verification is `PENDING`. A decision of approved requires external identity evidence that this checklist does not contain.

## Hash verification review

| Field | Entry |
|---|---|
| Reviewer name | |
| Role | |
| Date | |
| Evidence reference | Recorded hashes in `evaluation/config/research_v1/independent_custody_verification.json`. Local comparisons are `NOT_RUN`. |
| Decision | |
| Signature | |

Recorded manifest content hash: `e572093a4f0420c03316c89c83b6a7ab665af3af894d19a1428a6b091d3319ee`.

Recorded label hash: `35b126ba350a942f42f11d1845e16e01fd755516d20b53faf3aaf616143858a6`.

Recorded roster hash: `3f8fcbf1e698174a9a7cf6c586ec51048bcc07ca11154b36fdef0dadc7796208`.

These are recorded values. They are not an independent recomputation. Do not hash the label file from the developer checkout and call that independent verification.

## OS access-control review

| Field | Entry |
|---|---|
| Reviewer name | |
| Role | |
| Date | |
| Evidence reference | `python -m evaluation.scripts.verify_independent_custody` access report |
| Decision | |
| Signature | |

Current evidence: label path exists; current account can read it; `os_access_denial` is `PENDING`; `developer_read_denied` is false. Python path checks are not operating-system access control.

## Protocol freeze approval

| Field | Entry |
|---|---|
| Reviewer name | |
| Role | |
| Date | |
| Evidence reference | Designated appointment `protocol_freeze` `PENDING`; verification `protocol_sha256` null |
| Decision | |
| Signature | |

## Release authorization approval

| Field | Entry |
|---|---|
| Reviewer name | |
| Role | |
| Date | |
| Evidence reference | `evaluation/config/research_v1/final_test_release_authorization_template.json` status `NOT_AN_APPROVAL` |
| Decision | |
| Signature | |

Release must stay separate from scoring. This template does not authorize release.

## Scoring authorization approval

| Field | Entry |
|---|---|
| Reviewer name | |
| Role | |
| Date | |
| Evidence reference | `evaluation/config/research_v1/final_test_scoring_package.json`; `evaluation/scripts/score_final_test_v2.py` |
| Decision | |
| Signature | |

Scoring is `NOT_AUTHORIZED`. The scoring command was not permitted to score.

## Sealed-label acknowledgment

| Field | Entry |
|---|---|
| Reviewer name | |
| Role | |
| Date | |
| Evidence reference | Metadata validator `label_file_opened` false; this review did not open `labels.jsonl` |
| Decision | |
| Signature | |

Acknowledgment text, to be signed only if true: Final Test v2 labels remained sealed for this review. No Final Test experiment was executed. Independent custody is not established. Protocol freeze, release, and scoring remain unauthorized.
