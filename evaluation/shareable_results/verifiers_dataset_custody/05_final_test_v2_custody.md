# Final Test v2 self-custody

This document uses metadata only. The sealed label file and its backup were not opened, parsed, copied, or rehashed. Nothing in this package grants scoring permission or appoints an independent custodian.

## Dataset identity

From `evidence/final_test_custody_metadata.json`:

| Field | Value |
| --- | --- |
| Manifest id | `research_v1_final_test_v2_exploratory_v1` |
| Partition | `final_test` |
| Status | `NOT_AUTHORIZED` |
| Enabled | false |
| Groups | 600 |
| Candidates | 1200 |
| Content SHA-256 recorded | `e572093a4f0420c03316c89c83b6a7ab665af3af894d19a1428a6b091d3319ee` |
| Roster SHA-256 | `3f8fcbf1e698174a9a7cf6c586ec51048bcc07ca11154b36fdef0dadc7796208` |
| Dataset-manifest file SHA-256 recorded in the metadata | `58c55bf8d10f9f5a1ba847de93eccfde2f3edd87b79417f87c22bb9bb429bb69` |
| Label protocol | `provisional_automated_labeling_v1` |
| `labels_opened` | false |
| Evaluation authorization | `PENDING` |
| Label release | `NOT_AUTHORIZED` |
| Confirmatory use | `NOT_AUTHORIZED` |
| Human approval | `DEFERRED` |
| Custody | `DESIGNATED_CUSTODIAN_IS_DATASET_CREATOR`, `NOT_INDEPENDENT` |

The dataset-manifest file hash above is the value stored inside the metadata record for `evaluation/datasets/final_test_research_v1_eval_v2/manifest.json`. This package did not open that dataset directory and did not recompute that hash.

The same manifest and roster hashes appear in `evidence/final_test_self_custody.json`. The recorded label SHA-256, which this package did not recompute, is `35b126ba350a942f42f11d1845e16e01fd755516d20b53faf3aaf616143858a6`. `label_bytes_hashed_by_this_record` is false. Recorded size is 1,390,739 bytes.

## Appointment

`evidence/final_test_custodian_appointment.json` appoints the dataset creator as the designated Final Test custodian on 2026-11-11. The appointee name is in that copied record and is not repeated here. `independent_custodian` is false. `custody_independence` is `NOT_INDEPENDENT`. `evaluation_authorized` is false. `label_release` is `NOT_AUTHORIZED`. `protocol_freeze` is `PENDING`. Operating-system protection in that appointment is false. The appointment says it does not authorize evaluation or label release.

`evaluation/config/research_v1/independent_custodian_appointment.json` remains `CUSTODY_VERIFICATION_PENDING`, `established` false, with a null custodian id and a null signature. It is not copied as an approval because it establishes nothing. Self-custody does not fill that record.

## Label location and access log

`evidence/final_test_label_location_metadata.json`, dated 2026-11-13, says the label file is outside the Git repository. It records the path and a backup path, `hash_verified_without_parsing` true, `labels_parsed` false, and `source_removed_after_hash_match` true. `research_lead_approval` is `PENDING`. Access text: the directory ACL grants only the relocating account, and that account can still read the file.

`evidence/final_test_access_log.jsonl` is the existing one-line log. It records relocation on 2026-11-13, the same label hash and byte size, `labels_parsed` false, `backup_hash_matches` true, `scoring_performed` false, and research-lead approval `PENDING`. It does not contain label rows or answers. The string `labels` in that line is part of the field names `labels_parsed` and the previous path.

## Authorization fields that disagree

`evidence/final_test_self_custody.json` is included unchanged. Read these fields together:

- `approved` is false. `approver`, `approval_date`, and `signature` are null.
- `protocol_freeze` is `PENDING`. `protocol_sha256` is null.
- `independent_custody` and `independent_custodian` are false.
- `signed_evidence` is false. Protocol approval evidence form is `UNSIGNED_VERBAL_ACKNOWLEDGMENT`. The note says that statement is not a signature and does not authorize release or scoring.
- Top-level `scoring_authorized` is false and `scoring_confirmed` is false.
- Top-level `label_release` is `NOT_AUTHORIZED`.
- The status string is `SELF_CUSTODY_ACKNOWLEDGED_RELEASE_AND_SCORING_AUTHORIZED`.
- The nested `scoring_authorization` object sets `scoring_authorized` true and `scoring_confirmed` true, with `evidence_form` `RESEARCHER_SELF_AUTHORIZATION` and `signature` null. Its own note says it does not open labels or run the experiment.

Those fields are inconsistent. This package does not delete either side and does not change `approved`, `scoring_authorized`, `independent_custodian`, or any freeze flag.

`evaluation/research_readiness/v2_authorization.py` function `refuse_self_custody_live` refuses live scoring from the recorded declaration. A self-custody record cannot satisfy the independent-custody gate. The code refusal is not a signed research-lead denial, and it is not a signed approval.

## What is still missing

- A research-lead signature on the custody amendment.
- A non-null protocol SHA-256 and a completed protocol freeze.
- An independent custodian whose identity is not the dataset creator.
- A scoring authorization that is separate, signed, and consistent with the seal.
- An independent check of the sealed label bytes. This package deliberately does not provide that check.

Experiment 3's run manifest records `final_test_accessed` false for the Development collection. That statement is in the experiment artifact, which this package does not modify. It is not a substitute for independent custody.
