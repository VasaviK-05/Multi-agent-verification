# Final Test v2 custody evidence index

This index points at existing records. It is not a second custody protocol and it is not an authorization.

Primary report: [final_test_custody_completion_report.md](final_test_custody_completion_report.md).

Team checklist: [final_test_custody_team_review_checklist.md](final_test_custody_team_review_checklist.md).

## Protocol and readiness

- [final_test_custody_protocol.md](final_test_custody_protocol.md) — designated-creator appointment, recorded hashes, and the short enforcement note.
- [final_test_self_custody_protocol.md](final_test_self_custody_protocol.md) — repository self-custody. Not independent custody.
- [final_test_self_custody_amendment_2026-11-13.md](final_test_self_custody_amendment_2026-11-13.md) — dated amendment. Custody status `SELF_CUSTODY`. Labels moved outside the repository. Research-lead approval pending.
- `evaluation/config/research_v1/final_test_label_custody_location.json` — external path and recorded label hash. No label contents.
- `evaluation/config/research_v1/final_test_self_custody_amendment_2026-11-13.json` — machine-readable amendment. Not an approval.
- [final_test_self_custody_limitations.md](final_test_self_custody_limitations.md) — filesystem access, missing OS restrictions, and researcher-bias risk.
- [research_readiness_dashboard.md](research_readiness_dashboard.md) — custody enforcement implemented; independent custody not established; release and scoring not authorized.
- [research_readiness_completion_report.md](research_readiness_completion_report.md) — seven-requirement status. Final Test custody remains `NOT_AUTHORIZED`.

## Appointments and verification

- `evaluation/config/final_test_v2_custodian_appointment.json` — preserved designated-creator appointment. `independent_custodian` false. `custody_independence` `NOT_INDEPENDENT`. `protocol_freeze` `PENDING`. `operating_system_protection` false.
- `evaluation/config/research_v1/independent_custodian_appointment.json` — pending independent appointment. Identity null. Unsigned. `established` false.
- `evaluation/config/research_v1/independent_custody_verification.json` — `independent_verification` `PENDING`. Local hash comparisons `NOT_RUN`. Labels not parsed.
- `evaluation/config/research_v1/final_test_custody_manifest.json` — sealed metadata. `approved` false. Labels not opened by that package.
- `evaluation/config/research_v1/final_test_self_custody.json` — the only self-custody declaration. Limitations are acknowledged. Release and scoring are separate unsigned confirmations. `signed_evidence` is false. This is not a second custody declaration and not signed evidence.
- `evaluation/tests/test_v2_unsigned_self_authorization.py` — synthetic unsigned release and scoring confirmations. They are not live authorizations.

## Authorization templates

These are not approvals.

- `evaluation/config/research_v1/final_test_release_authorization_template.json` — `NOT_AN_APPROVAL`, `NOT_AUTHORIZED`, scoring not granted.
- `evaluation/config/research_v1/final_test_scoring_package.json` — `NOT_AN_APPROVAL`, `scoring_authorized` false.
- `evaluation/artifacts/person1/final_test_authorization_v1/pending_authorization_record.json` — signature null, `approved` false.
- `evaluation/artifacts/person1/final_test_authorization_v1/authorization_readiness.json` — `NOT_READY_FOR_AUTHORIZATION`.
- `evaluation/artifacts/person1/final_test_authorization_v1/prerequisite_checklist.json` — independent custody, OS protection, protocol freeze, evaluation authorization, and label release unmet.
- `evaluation/artifacts/person1/final_test_authorization_v1/manifest_metadata.json` — metadata companion. Not a label file.
- `evaluation/artifacts/person1/final_test_authorization_v1/provenance_audit.json` — identity-overlap record. `labels_opened` false. Semantic leakage `NOT_CLAIMED`.

## Code, tests, and commands

- `evaluation/research_readiness/v2_authorization.py` — independent state machine and the separate self-custody checks.
- `evaluation/scripts/verify_self_custody.py` — self-custody status only. Does not read labels.
- `evaluation/tests/test_v2_self_custody.py` — synthetic self-custody tests.
- `evaluation/data_preparation/final_test_custody.py` — designated appointment loader. It rejects an appointment that claims independence.
- `evaluation/data_preparation/final_test_workflow.py` — `read_custodian_labels` refuses the sealed v2 label path before reading.
- `evaluation/baseline/run_baseline_experiment.py` — refuses a v2 label or v2 custodian dataset path.
- `evaluation/scripts/verify_independent_custody.py` — metadata state report. Do not pass `--hash-bytes` when labels must stay unopened.
- `evaluation/scripts/validate_final_test_custody.py` — manifest metadata only. Does not open the label file.
- `evaluation/scripts/score_final_test_v2.py` — scoring entry point. Refuses and does not score.
- `evaluation/tests/test_v2_custody_enforcement.py` — synthetic fixtures only.
- `tests/test_final_test_v2_custody.py` — existing custody tests. `test_v2_custody_update_preserves_dataset_hashes_and_withholds_evaluation` hashes the real label file and was deselected for this package.
- `tests/test_final_test_workflow.py` — synthetic label-gate tests. Included in the 65 passed.
- `tests/test_research_readiness.py` and `tests/test_experiment3_prerequisites.py` — included in the same run. Experiment 3 readiness is separate from Final Test authorization.

## Leakage and contamination records

- [final_test_leakage_audit.md](final_test_leakage_audit.md) — original provisional-partition check, with the 2026-11-11 correction that it was not a full leakage check.
- [final_test_contamination_audit.md](final_test_contamination_audit.md) — retired provisional partition. 807 of 2,638 groups were previously exposed. Not a v2 label inspection.
- Manifest exposure and leakage flags read by the metadata validator: exposure passed, overlapping groups 0, leakage passed. Those flags are stored metadata. They are not a new label audit.

## Commands used for this package

```text
python -m pytest evaluation/tests/test_v2_custody_enforcement.py tests/test_final_test_workflow.py tests/test_final_test_v2_custody.py tests/test_research_readiness.py tests/test_experiment3_prerequisites.py -q --tb=line -k "not test_v2_custody_update"
python -m evaluation.scripts.validate_final_test_custody
python -m evaluation.scripts.verify_independent_custody
```

The pytest result was 65 passed, 1 deselected, 0 failed. The validators reported `NOT_AUTHORIZED` and `CUSTODY_VERIFICATION_PENDING`.
