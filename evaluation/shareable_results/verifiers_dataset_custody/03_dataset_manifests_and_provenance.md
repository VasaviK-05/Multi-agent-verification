# Dataset manifests and provenance

## Approved Development eligibility

Authoritative file: `evidence/development_eligibility_manifest.json`.

| Field | Value |
| --- | --- |
| Manifest id | `research_v1_exploratory_eligibility_approved_v1` |
| Dataset version | `research_v1_exploratory_v1` |
| Approval status | `APPROVED_BY_RESEARCH_LEAD` |
| Approver | `Research Lead` |
| Approval date | `2026-11-13` |
| Scope | Development eligibility for `research_v1_exploratory_v1` only |
| Body SHA-256 | `f2cc0fd108b961bf4795767df4f90e92d7fa0f418ef9865d0206f32d7b45282d` |
| Complete-file SHA-256 | `1ebb4357d599a52d1c1fc8d8951ab39fa6992e846cf997d9e588820c87cbe731` |
| Generator revision | `d9fd453afe9bfe601ace8e1d30b80a9e593c8484` |
| Eligibility protocol | `paired_binary_group_v1` |
| Label protocol | `provisional_automated_labeling_v1` |

Counts: 372 eligible groups, 744 eligible candidates, 375 excluded rows, 0 label-validation-failed groups. Before quarantine there were 387 provisionally paired groups. Fifteen shared-context groups were quarantined.

| Benchmark | VERIFIED_CORRECT | SYNTHETIC_INCORRECT | Eligible groups |
| --- | ---: | ---: | ---: |
| GSM8K | 187 | 187 | 187 |
| HotpotQA | 185 | 185 | 185 |

`collection_authorized`, `recording_authorized`, `final_test_authorized`, and `frozen_protocol` are false. The manifest does not authorize verifier collection, attempt recording, protocol freeze, Experiment 2 budgets, Final Test label release, confirmatory evaluation, or policy fitting. `semantic_clearance` is `NOT_CLAIMED`. `human_verified` on the eligible rows is false. There is no human-verified incorrect candidate in this roster.

The approval is a JSON status. It is not a detached signature.

## Group and candidate identifiers

`evidence/development_group_assignments.jsonl` is the byte copy of the approved assignment file. It has 387 rows. 372 have `eligible` true: GSM8K 187 and HotpotQA 185. The other 15 are HotpotQA rows with `eligible` false and exclusion reason `shared_history_reference_context`. Each row has `related_group_id` and `question_id`. It does not list candidate ids.

`evidence/development_eligible.jsonl` is the byte copy of the eligible-candidate file. It has 744 rows. Each row has `candidate_id`, `related_group_id`, `question_id`, `benchmark`, `label_class`, `label_protocol`, `label_method`, and `label_source`. It does not contain answer text. Label classes are only `VERIFIED_CORRECT` and `SYNTHETIC_INCORRECT`.

The eligibility manifest publishes SHA-256 values for its output files. On this Windows working tree those JSONL files use CRLF newlines. Replacing CRLF with LF reproduces the published hashes. The copies in this package keep the working-tree bytes, so their file hashes are the raw hashes below. The published hashes are the LF form. The row contents are the same.

| File | Working-tree SHA-256 | LF SHA-256 published in the eligibility manifest |
| --- | --- | --- |
| `development_eligible.jsonl` | `80f69e8a56c69554dfcae6cc4a8e2381ff2d6b5130216968ae002a50dc8d26ca` | `7ce9d93faf27a61b8fc810025febc4d375629f525565574b55208569bbd462ea` |
| `group_assignments.jsonl` | `5c1008cdc2539fff941fc7161f4818d0689976b1aefb9c978144cd99d99d8cb1` | `8d73ffae8b91e66fce53278f665de6ecfa0ab69a5a51168976a52e231950df73` |

The same LF relationship holds for the files that were not copied: `development_excluded.jsonl` LF `9556d19d5c9d86801986a1684913759280468b9767344555bf329d0326887cbf`, `label_validation.jsonl` LF `aa130b41ab312c4f5548e9b0b8a2c97171d8a41643457098a49303030dffee1f`, and `leakage_audit.json` `4c15def559393a00d84bf9b57efe52637aebead7a6ab20c472fc43433919efd2`. This package does not rewrite the JSONL files to LF.

Source manifest SHA-256 recorded by the eligibility file: `5e55dbd17bf968eaa7768819945ab3adfc3b30d850817b859c63015e9db03764`.

## Stale hash sidecar

`evidence/development_eligibility_manifest.file_sha256.txt` is the original sidecar, copied unchanged. Its text is:

`75087c28f01e566be0572c149a182f5b02872f2973bcb32156bb607ecdac1eaa`

The current `eligibility_manifest.json` bytes hash to `1ebb4357d599a52d1c1fc8d8951ab39fa6992e846cf997d9e588820c87cbe731`. The sidecar does not match the file. This package does not replace the sidecar and does not treat `75087c28…` as the file hash. The body hash `f2cc0fd1…` is the digest the eligibility file itself publishes, with the body-hash field removed before hashing.

## History is not approved

No approved History eligibility manifest exists. The provisional eligibility record says History is not an eligibility population.

`evidence/exploratory_dataset_manifest.json` is the exploratory build `research_v1_exploratory_v1`. Its status is `EXPLORATORY_PROVISIONAL_LABELS`. `human_approval` is `DEFERRED`. `human_verified_labels` is 0. `final_test_read` is false. It is not an approval.

Exploratory History counts in that file:

| Benchmark | Groups | VERIFIED_CORRECT | SYNTHETIC_INCORRECT | UNRESOLVED | HUMAN_VERIFIED_INCORRECT |
| --- | ---: | ---: | ---: | ---: | ---: |
| GSM8K | 277 | 277 | 277 | 199 | 0 |
| HotpotQA | 300 | 300 | 299 | 340 | 0 |

Exploratory Development in the same file is larger than the approved roster: HotpotQA has 200 groups there, before the 15-group quarantine. Use the approved eligibility file for the 372-group roster.

`evaluation/config/research_v1/dataset_approval_package.json` is `NOT_APPROVED`. It cites the Development eligibility decision as already made and still requires benchmark approval, a decision on synthetic labels, and a separate collection authorization. That package file is not copied here because it is a pending decision record rather than an approved manifest. Its path is the place a later approval would have to be recorded.
