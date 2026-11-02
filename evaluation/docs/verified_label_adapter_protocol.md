# Verified-candidate offline preparation protocol

## Purpose and boundary

`evaluation/data_preparation/build_offline_examples.py` converts the reconciled GSM8K/HotpotQA candidate labels into a versioned preparation format for later offline recording collection. It does not construct `app.game.offline.records.Example` instances, does not create verifier attempts, and does not fit or evaluate a policy. Unresolved candidates are written to an explicit exclusion ledger.

Inputs are limited to `evaluation/datasets/reconciled_candidates/v1/` and its manifests/summaries. The builder does not read unified datasets, raw benchmarks, pilot/adjudication directories, or Final Test records or identities. It refuses to overwrite a non-empty output directory. No reconciled source files are modified.

## Offline record contract inspection

The adapter was checked against `app/game/offline/records.py`:

- `Example.label_method` is a Pydantic literal that accepts `independent_human` or `independent_ground_truth`.
- A usable `Example` also requires nonempty `Attempt` records, `validation_id`, `execution_configuration_id`, `domain`, `planning_category`, and `cache_contract`. Each `Attempt` requires verifier identity, outcome state, execution/configuration IDs, report provenance, adapter version, and—when applicable—a valid report.
- `TrainingManifest` accepts History and Development outcome partitions plus an outcome-free `FinalTestReservation`; it rejects final-test outcome records in training input and checks example/group/question/content/run identities for cross-role leakage.
- `history_reputation()` consumes recorded directional attempts and independent labels from History. `construct_payoffs()` uses Development recordings. A candidate-label row alone cannot supply either verifier outcomes or actual attempt costs.

The current sources have no verifier `Attempt`, validation/run ID, execution configuration, domain, or planning category. Creating those fields or constructing an `Example` would fabricate records or bypass contract requirements. Therefore this output is **label preparation only**; complete verifier-attempt collection is a required next stage.

### Label-method compatibility

The Pydantic contract structurally accepts `independent_ground_truth`; it does not inspect or certify the underlying validation method. The adapter maps only the four method/status combinations present in the reconciled artifact to that value:

| Benchmark and status | Reconciled validation basis |
|---|---|
| GSM8K `verified_correct` | Benchmark source match plus independent exact arithmetic replay |
| GSM8K `verified_incorrect` | Raw worked-solution source match, exact arithmetic replay, and distinct exact-count construction |
| HotpotQA `verified_correct` | Benchmark answer match with supplied supporting-context provenance |
| HotpotQA `verified_incorrect` | Source answer plus supporting-context evidence and explicit-negation construction |

This is a structural mapping, not a claim of human adjudication. `independent_ground_truth` records the provenance category used by the offline model; the schema does not decide whether source replay or controlled construction is methodologically sufficient. The research team must approve these bases for the study before treating the prepared labels as final ground truth. The framework under evaluation is not used as a label judge.

## Preparation behavior

1. Map `verified_correct` to `answer_is_correct: true` and `verified_incorrect` to `false`, retaining the original status, method, construction version, candidate/source/group IDs, partition, evidence condition, and complete provenance.
2. Keep every unresolved row in `excluded_unresolved.jsonl`, including its source record and unresolved reason. The exclusion contains no `answer_is_correct` field.
3. Use canonical candidate ID as the prospective `example_id`, source dataset ID as a benchmark-qualified `question_id`, and `related_group_id` as `split_identity`.
4. Preserve History/Development assignment for every candidate and reject a question group assigned to both.
5. Record the context condition. GSM8K worked solutions remain label-validation provenance, not verifier input. HotpotQA remains benchmark-context-assisted with no shared-corpus retrieval claim.
6. Mark every prepared row `label_prepared_only_not_offline_Example` and list missing recording fields. No `Attempt`, `validation_id`, or execution-configuration ID is emitted.

## Output and reproducibility

Run from the repository root:

```powershell
.\.venv\Scripts\python.exe evaluation/data_preparation/build_offline_examples.py build
.\.venv\Scripts\python.exe evaluation/data_preparation/build_offline_examples.py validate
```

The default versioned output is `evaluation/datasets/offline_examples/v1_reconciled_candidates/`:

- `history_prepared.jsonl`
- `development_prepared.jsonl`
- `excluded_unresolved.jsonl`
- `manifest.json`
- `validation_summary.json`
- `README.md`

The manifest stores hashes of the reconciled inputs and generated outputs, a digest of its own canonical content, the label-method allowlist/basis, and all candidate and exclusion counts. Output ordering and JSON serialization are deterministic for the same source bytes. The validator checks source/output/manifest hashes, status mapping, unresolved ledger completeness, identity/group/partition preservation, and that no recording fields were fabricated.

## Observed counts

“Prepared labelled candidates” are candidate records with a binary label; they are not complete offline `Example` records. “Excluded unresolved candidates” remain outside binary scoring. Group-status counts can overlap because one question may have both a labelled candidate and an unresolved variant.

| Benchmark | Partition | Prepared labelled candidates (correct / incorrect) | Excluded unresolved candidates | Groups with labelled candidate | Groups with unresolved candidate | Total independent groups |
|---|---|---:|---:|---:|---:|---:|
| GSM8K | History | 112 (72 / 40) | 48 | 72 | 40 | 80 |
| GSM8K | Development | 29 (19 / 10) | 11 | 19 | 10 | 20 |
| HotpotQA | History | 120 (80 / 40) | 80 | 80 | 80 | 80 |
| HotpotQA | Development | 30 (20 / 10) | 20 | 20 | 20 | 20 |
| **Combined** | **History + Development** | **291 (191 / 100)** | **159** | — | — | **200 across benchmarks** |

**Complete verifier-attempt records: 0. Fully validated offline `Example` objects: 0.** All 291 labelled rows are preparation-stage records awaiting appropriate verifier recording and execution provenance.

## Next required steps

1. Approve or revise the method-specific `independent_ground_truth` mapping.
2. Finalize domain/planning-category and evidence-context mappings without exposing label-only evidence to verifiers unintentionally.
3. Collect genuine complete-team verifier attempts under a frozen execution configuration, with observed failures and resource provenance recorded.
4. Join those records to these candidate identities without changing partition/group assignments, then validate actual `Example`, `Attempt`, and `TrainingManifest` models.
5. Only after those checks and approval should offline reputation construction or payoff fitting begin.

No policy fitting, holdout creation, or research experiment was run for this preparation.
