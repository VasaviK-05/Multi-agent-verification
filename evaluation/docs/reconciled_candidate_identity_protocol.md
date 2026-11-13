# Reconciled candidate identity protocol v1

## Purpose and boundaries

This artifact joins the controlled-negative candidates in `evaluation/datasets/verified_negative_candidates/v1/` to their parent questions and candidate identities in `evaluation/datasets/verified_subset/v1_seed_20261104/`. It is an identity/provenance reconciliation, not a label adapter or an offline experiment manifest. It does not perform policy fitting or run any of the four research experiments.

The builder reads only the named verified-subset files, controlled-negative files, their manifests/summaries, and the three protocol documents listed in the machine-readable manifest. It does not read unified datasets, raw benchmark sources, pilot/adjudication files, or any Final Test record or identity. It writes only to the new versioned output directory and refuses to overwrite a non-empty directory. SHA-256 hashes of the input files are recorded and checked before and after generation and on validation.

## Identity reconciliation rules

### GSM8K

Each of the 50 controlled-negative rows is joined by `dataset_id` to exactly one original verified-subset `source_candidate_index == 1` record. The candidate answers must be numerically equal under strict exact numeric normalization, and parent question, gold answer, and partition must agree.

The output retains the original subset candidate ID as the canonical ID. It emits one candidate row, not both the source row and controlled-negative row. The original row is retained unchanged inside `source_candidate_record`; `source_correctness_status` remains `unresolved`; the reconciled active `correctness_status` becomes `verified_incorrect` with the controlled construction's method, evidence, rationale, confidence category, and `candidate_generation_method` attached under `reconciliation.validation_basis`. The controlled-negative candidate ID is retained as provenance. This is a versioned status reconciliation, not a second observation.

All other GSM8K records retain their original status. In particular, unresolved candidates that did not match one of the 50 validated controls remain `unresolved`.

### HotpotQA

The 200 original verified-subset candidate records are retained with their original candidate IDs and full source record nested unchanged. The 50 explicit-negation records are appended under their own controlled-negative candidate IDs. Each receives the `related_group_id`, question, and partition joined from its original `dataset_id`; these are checked against the negative record's question, answer, and partition provenance.

The original gold candidates remain `verified_correct`, original borrowed candidates remain `unresolved`, and explicit-negation candidates retain `verified_incorrect`. No status is inferred from answer-string mismatch. The evidence and validation basis remain in the nested original/source candidate record.

## Reproducible outputs

Run from the repository root:

```powershell
.\.venv\Scripts\python.exe evaluation/data_preparation/reconcile_verified_candidates.py build
.\.venv\Scripts\python.exe evaluation/data_preparation/reconcile_verified_candidates.py validate
```

The default output is `evaluation/datasets/reconciled_candidates/v1/`:

- `gsm8k_reconciled.jsonl`
- `hotpotqa_reconciled.jsonl`
- `manifest.json`
- `validation_summary.json`
- `README.md`

The manifest records source hashes, output hashes, the algorithm version, candidate reconciliation counts, and a group roster containing source question IDs, related group IDs, and partitions. It contains no Final Test identity. The validator verifies candidate-ID uniqueness, preserved source candidate identity/status, parent question/group/partition mapping, group disjointness between History and Development, no duplicate GSM8K numeric candidate observations, and retained HotpotQA source variants.

## Observed counts

Candidate counts are records; question-group counts are independent question units. Group counts by status are **non-exclusive**: a group is counted for every status represented among its candidate variants.

| Benchmark | Partition | Candidate records | Verified correct | Verified incorrect | Unresolved | Independent question groups | Groups with correct / incorrect / unresolved candidate |
|---|---|---:|---:|---:|---:|---:|---|
| GSM8K | History | 160 | 72 | 40 | 48 | 80 | 72 / 40 / 40 |
| GSM8K | Development | 40 | 19 | 10 | 11 | 20 | 19 / 10 / 10 |
| HotpotQA | History | 200 | 80 | 40 | 80 | 80 | 80 / 40 / 80 |
| HotpotQA | Development | 50 | 20 | 10 | 20 | 20 | 20 / 10 / 20 |

| Benchmark | Reconciled candidate records | Verified correct | Verified incorrect | Unresolved | Independent question groups |
|---|---:|---:|---:|---:|---:|
| GSM8K | 200 | 91 | 50 | 59 | 100 |
| HotpotQA | 250 | 100 | 50 | 100 | 100 |
| **Combined** | **450** | **191** | **100** | **159** | **200 across two benchmarks** |

GSM8K's 50 controlled candidates match 50 pre-existing candidate IDs and add zero rows. HotpotQA retains 200 original records and appends 50 explicit-negation records. Each benchmark has 100 groups total, split into 80 History and 20 Development, with no group overlap between those partitions. The 200 combined groups are benchmark-specific; the same numeric group count across different benchmarks does not imply cross-benchmark independence of source populations.

## Integrity and limitations

The output distinguishes candidate-record counts from group counts and reports group-by-status counts as non-exclusive. It preserves unresolved statuses and original source records. `verified_incorrect` for GSM8K is the controlled, exact discrete-count increment outcome; for HotpotQA it is the explicit-negation outcome under the supplied benchmark-context evidence condition. Neither status is a human adjudication or evidence of natural error prevalence.

This artifact does not decide whether these provenance methods satisfy the offline evaluator's `independent_ground_truth` contract. The offline label adapter remains out of scope. No History/Development-to-Final-Test allocation is changed, and no new split or holdout is created.
