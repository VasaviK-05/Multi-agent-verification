# Final Test v2 custody completion report

This report consolidates existing custody records. It does not appoint a custodian, freeze a protocol, release labels, or authorize scoring.

## 1. Executive summary

**CUSTODY ENFORCEMENT IMPLEMENTED — INDEPENDENT CUSTODY NOT ESTABLISHED**

- Final Test v2 remains sealed.
- Release is not authorized.
- Scoring is not authorized.
- Protocol is not frozen.
- No empirical Final Test experiment was executed.

Dataset `research_v1_final_test_v2_exploratory_v1` is `NOT_AUTHORIZED` and `enabled: false`. The designated-creator appointment is unchanged and records `NOT_INDEPENDENT`. The separate independent-appointment file has a null custodian id, no signature, and `established: false`.

Repository self-custody is recorded in `final_test_self_custody_protocol.md`. It is `IMPLEMENTED` as a non-independent declaration. It does not establish independent custody, freeze the protocol, release labels, or authorize scoring. No OS-level access restriction was added.

## 2. Technical implementation

The central check is `evaluation/research_readiness/v2_authorization.py`. It does not read label bytes.

`custody_state` derives one state from the appointment, the verification record, a protocol record, a release record, and a scoring record. A JSON file existing on disk does not move the state to established, frozen, released, or authorized. The live records currently produce `CUSTODY_VERIFICATION_PENDING`.

Fail-closed rules:

- A missing appointment yields `CUSTODY_NOT_ESTABLISHED`.
- An appointment is rejected when the custodian id is missing, matches the dataset creator, carries a role that conflicts with `independent_custodian`, lacks `VERIFIED_EXTERNAL` identity verification, or lacks a signature and approval date.
- `established: true` on the appointment is treated as a self-declaration, not evidence.
- Release and scoring records must be approved, signed, unexpired, and unrevoked. Templates and `NOT_AN_APPROVAL` records are unsigned.
- Each authorization must match the recorded manifest hash, label hash, roster hash, dataset version, custodian id, and frozen protocol hash. A null protocol hash is `protocol_not_frozen`.
- A release record may not set `scoring_authorized` true. A scoring record may not set `label_release` to `AUTHORIZED`. Scoring also requires scope `final_test_v2_scoring` and an authorized scorer.

Sealed label reads go through `read_custodian_labels` in `evaluation/data_preparation/final_test_workflow.py`. Before any read, that function calls `refuse_sealed_label_without_release` when the path is `evaluation/datasets/_custodian/final_test_research_v1_v2/labels.jsonl`. Other paths, including synthetic fixtures and the retired v1 label file, stay on the existing gate.

`evaluation/scripts/score_final_test_v2.py` loads the release template and scoring package, calls `refuse_v2_scoring`, and does not open labels. Even a future binding check that passed would still raise, because no scoring implementation is enabled while the labels stay sealed.

`evaluation/baseline/run_baseline_experiment.py` refuses a dataset argument that is the sealed label path or contains `final_test_research_v1_v2`. Its default dataset is unchanged. Development, history, and synthetic collection continue to use `evaluation/research_readiness/guards.py`, which rejects any path or partition containing `final_test`.

These checks are application checks. `verify_independent_custody` reports that the label path exists and that the current account can read it. That report is not an operating-system access-control boundary. A process with filesystem access can still read the Git-ignored label file.

## 3. Verification evidence

Command, run from the repository root with `PYTHONIOENCODING=utf-8` and `.venv\Scripts\python.exe`:

```text
python -m pytest evaluation/tests/test_v2_custody_enforcement.py tests/test_final_test_workflow.py tests/test_final_test_v2_custody.py tests/test_research_readiness.py tests/test_experiment3_prerequisites.py -q --tb=line -k "not test_v2_custody_update"
```

Result: **65 passed, 1 deselected, 0 failed** (9.89s).

A later run added `evaluation/tests/test_v2_self_custody.py` to that command. Result: **71 passed, 1 deselected, 0 failed** (9.92s). `python -m evaluation.scripts.verify_self_custody` reported self-custody `IMPLEMENTED`, independent custody `NOT_ESTABLISHED`, protocol freeze `PENDING`, release `NOT_AUTHORIZED`, scoring `NOT_AUTHORIZED`, and `labels_opened` false.

The deselected test is `tests/test_final_test_v2_custody.py::test_v2_custody_update_preserves_dataset_hashes_and_withholds_evaluation`. It hashes the real label file with `sha256_file`. It was not run. It is not a passed test.

The synthetic suite in `evaluation/tests/test_v2_custody_enforcement.py` covers a missing appointment, the dataset creator named as independent custodian, conflicting roles, missing verification, hash mismatches, an unfrozen protocol, unsigned release and scoring, release without scoring, scoring without release, a different dataset, sealed-path refusal, the scoring command, a synthetic signed path, development fixtures, error text, expiry, revocation, and the live pending records. It does not use the real label file.

Metadata validator:

```text
python -m evaluation.scripts.validate_final_test_custody
```

Result: exit 0. `label_file_opened` is false. Status is `NOT_AUTHORIZED`. `custody_independence` is `NOT_INDEPENDENT`. `label_release` and `confirmatory_use` are `NOT_AUTHORIZED`. Blockers are empty because the seal is intact, not because release is approved. `exposure_passed` is true and `exposure_overlapping_groups` is 0. `leakage_passed` is true. Those flags are fields already stored on the manifest. This command did not open the label file.

Custody verifier, without `--hash-bytes`:

```text
python -m evaluation.scripts.verify_independent_custody
```

Result: exit 0. `custody_state` is `CUSTODY_VERIFICATION_PENDING`. Appointment blockers are `missing_independent_custodian_identity`, `missing_independent_verification`, and `unsigned_independent_appointment`. `independent_verification` is `PENDING`. `labels_parsed` is false. `current_account_can_read_label_file` is true. `os_access_denial` is `PENDING`. `protocol_freeze` is `PENDING`. `release_authorized` and `scoring_authorized` are false.

`--hash-bytes` was not used. No label bytes were hashed for this report.

## 4. Current custody state

| Requirement | Status | Evidence |
|---|---|---|
| Custody enforcement | IMPLEMENTED | `v2_authorization.py`, workflow gate, scoring command, baseline path refusal, synthetic tests |
| Independent custodian identity | PENDING | `independent_custodian_appointment.json` identity_verification `PENDING`, id null |
| Independent appointment | PENDING | Same file: unsigned, `established` false, status `CUSTODY_VERIFICATION_PENDING` |
| Independent hash verification | PENDING | `independent_custody_verification.json`: `independent_verification` `PENDING`, local hash comparisons `NOT_RUN` |
| Developer-account denial | PENDING | Verifier access report: current account can read the label path; `developer_read_denied` false |
| Custody established | NOT_ESTABLISHED | Appointment blockers above; designated appointment remains `NOT_INDEPENDENT` |
| Protocol freeze | PENDING | Designated appointment `protocol_freeze` `PENDING`; verification `protocol_sha256` null |
| Release authorization | NOT_AUTHORIZED | Release template `NOT_AN_APPROVAL`; manifest `label_release` `NOT_AUTHORIZED` |
| Scoring authorization | NOT_AUTHORIZED | Scoring package `scoring_authorized` false; scoring command refuses |
| Final Test execution | NOT_RUN | No Final Test scoring command was allowed to proceed; no Final Test metrics were produced |

## 5. Integrity evidence

These hashes are copied from existing metadata. They were not recomputed for this report. None of them is an independent verification. `local_manifest_sha256_matches`, `local_label_sha256_matches`, and `local_roster_sha256_matches` are all `NOT_RUN`.

| Artifact | Recorded SHA-256 | Where recorded | Independently verified |
|---|---|---|---|
| Manifest content | `e572093a4f0420c03316c89c83b6a7ab665af3af894d19a1428a6b091d3319ee` | Custody manifest, authorization readiness, release template | No |
| Manifest file | `58c55bf8d10f9f5a1ba847de93eccfde2f3edd87b79417f87c22bb9bb429bb69` | `authorization_readiness.json`, pending authorization record | No; not recomputed here |
| Label file | `35b126ba350a942f42f11d1845e16e01fd755516d20b53faf3aaf616143858a6` | Custody protocol and verification record `expected_label_sha256` | No; label file not opened |
| Evaluation roster | `3f8fcbf1e698174a9a7cf6c586ec51048bcc07ca11154b36fdef0dadc7796208` | Custody protocol and verification record `expected_roster_sha256` | No; not recomputed here |

The label hash is a previously recorded digest. This package did not hash or parse `labels.jsonl`.

Recorded manifest metadata from the validator: 600 groups, 1,200 candidates, `human_verified_labels` 0, `retired_final_test_reused` false, human approval and adjudication `DEFERRED`.

Existing leakage records, not new audits:

- `evaluation/artifacts/person1/final_test_authorization_v1/provenance_audit.json` records `labels_opened` false, identity-overlap counts of 0 against history, development, exploratory, and the retired v1 roster, and `semantic_leakage` `NOT_CLAIMED`.
- The metadata validator read `exposure_audit.passed` true, overlapping groups 0, and `leakage_audit.passed` true from the manifest.
- `evaluation/docs/final_test_contamination_audit.md` and `evaluation/docs/final_test_leakage_audit.md` describe the retired provisional partition, not a new v2 label inspection. That provisional partition remains retired.

## 6. Remaining external actions

1. Independently verify custodian identity. The id must be a stable non-secret token, and it must not be the dataset creator, developer, candidate-answer author, verifier tuner, or development evaluator. A chat claim is not evidence.
2. Transfer label storage to independently controlled custody.
3. Deny developer and researcher account read access, and record that denial. The current account can still read the label path.
4. Independently recompute and verify the manifest, label, and roster hashes outside this checkout. Record the comparison. A local `--hash-bytes` run would still be `PENDING`, not independent verification, and was not run.
5. Freeze the research protocol with the existing signed-protocol mechanism. The protocol hash is null.
6. Sign release authorization separately. The release template is `NOT_AN_APPROVAL` and must not grant scoring.
7. Sign scoring authorization separately. It must not grant label release.
8. Bind both authorizations to the frozen protocol hash, the three dataset hashes, the custodian id, the scoring scope, and the authorized scorer.

## 7. Research team review checklist

The sign-off form is `evaluation/docs/final_test_custody_team_review_checklist.md`. Reviewers can confirm the enforcement code and tests. They cannot sign custody, freeze, release, or scoring from this report alone. Those lines stay blank until the external evidence exists.

## Repository self-custody

No independent custodian is available. The researcher and dataset creator remains the non-independent custodian. `evaluation/config/research_v1/final_test_self_custody.json` records that mode. `independent_custodian` stays false. The independent appointment file was not changed.

`self_release_blockers` and `self_scoring_blockers` require a signed protocol hash before release, a separate signed release, and a separate signed scoring record. A self-custody record is rejected by the independent authorization functions. The sealed label reader still uses only the independent gate. Limitations are in `final_test_self_custody_limitations.md`.

The researcher explicitly acknowledged the self-custody limitations, confirmed release, and later confirmed scoring in `final_test_self_custody.json`. Scoring is the separate `scoring_authorization` object. `signed_evidence` is false. There is no signature. Independent custody is not established. The manifest hash, roster hash, and dataset version matched the recorded values before scoring was stored. The manifest itself remains `NOT_AUTHORIZED`, the label file was not opened, and the experiment was not run.

## 8. Final conclusion

Final Test v2 authorization infrastructure is implemented and tested. Actual independent custody has not yet been established. Final Test v2 remains sealed and cannot be scored until custody, protocol freeze, release, and scoring authorization requirements are satisfied.
