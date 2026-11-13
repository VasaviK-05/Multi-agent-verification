# research_v1 freeze report

## Status

**Frozen for exploratory History and Development work.**

**Not frozen for confirmatory evaluation.**

**Not protected Final Test ready.**

`research_v1` is the fixed History/Development artifact for exploratory work. It is not a final research dataset and it is not a statistically powered sample. No protected Final Test set exists. This report does not create one, does not open the old exposed final-test files, and does not change research_v1 records, labels, IDs, splits, hashes, or the manifest.

The builder already refuses to overwrite a non-empty research_v1 directory. That immutability is a file-system guard. It is not a confirmatory freeze, because verifier configuration, loss, threshold, budget, aggregation, and the analysis plan are not sealed.

## Existing research_v1 status

Recorded by `evaluation/config/research_dataset.yaml`, `evaluation/datasets/reconciled_candidates/research_v1/manifest.json`, and `validation_summary.json`:

| Item | Recorded value |
|---|---|
| History question groups | 600 (GSM8K 300, HotpotQA 300) |
| Development question groups | 400 (GSM8K 200, HotpotQA 200) |
| Question groups total | 1,000 |
| Candidate records | 2,050 |
| Prepared binary-labelled candidates | 1,179 |
| Unresolved candidates excluded from binary examples | 871 |
| Final Test | Disabled. `source` is null. `final_test_records_or_identities_accessed` is false |
| Complete verifier Attempts | 0 |
| Complete offline Examples | 0 |
| `policy_fitting_ready` | false |
| Human adjudication | Not claimed |
| Manifest date | 2026-11-02 |
| Manifest SHA-256 stored in the manifest | `8cc984bef54b1d7b9436524ffc9cd0d2081fbb9dc6f3c109cc7b5cc901a7c1d1` |

Question groups, candidate records, and binary-labelled candidates are different units. The 1,000 groups are not 2,050 independent questions, and the 1,179 labelled candidates are not a powered sample.

No protected holdout exists. The old final-test partition was already exposed during earlier audits and pilots. Those files cannot be reused as an unseen confirmatory test. This report did not open them.

The group-leakage audit is a conditional pass (`evaluation/docs/research_v1_group_leakage_audit.md`). History and Development question IDs do not overlap. HotpotQA still shares 14 identical paragraphs across the two partitions, including Magic Dirt sentence 0 and Tom Clancy sentence 0 as supporting facts. Semantic and paraphrase leakage was not tested.

Label limits, from the manifest `label_quality` block and the candidate-answer protocol:

- GSM8K verified incorrect labels are only the narrow gold+1 discrete-count rule (215 candidates).
- HotpotQA has zero verified incorrect candidates. Borrowed answers and 50 explicit-negation records remain unresolved.
- Unresolved candidates are not incorrect.
- No reviewer identities or adjudication decisions are claimed.

Source version strings stored in the manifest are `openai/gsm8k main@740312add88f781978c0658806c59bc2815b9866` and `hotpotqa/hotpot_qa distractor@1908d6afbbead072334abe2965f91bd2709910ab`. Local dataset metadata still has empty license and citation fields.

## Protected Final Test requirements

These rules apply to a future confirmatory set. They are not satisfied by research_v1, and nothing in this report implements them.

1. The pool is a new source, or a newly sampled set of groups, that is independent of research_v1 History and Development and of every file used to build or tune them. The old exposed final-test partition is not eligible.
2. Separation is at question-group level. Keeping two candidate rows of the same question on opposite sides of the split is not separation.
3. Before any research use, check overlap of source IDs, question IDs, normalized question text, and context identities against History, Development, and every other training or tuning artifact. Overlap is recorded. It is not silently dropped.
4. Shared HotpotQA context is either removed under a predeclared rule that does not look at scores, or the confirmatory report stratifies those groups and states the limitation. Semantic leakage stays unverified unless a separate audit is run.
5. Candidate construction and labels are frozen before anyone on the research team can read test answers or labels.
6. An independent custodian holds the identities and labels. This report does not appoint a custodian and does not invent an access log or an approval.
7. During development the research team receives no test answers, gold labels, or unresolved-label keys.
8. Each access to the test payload requires an explicit approval and a log entry naming the person, the purpose, and the artifact hash. No such log exists today.
9. The test is opened only after methods, verifiers, loss weights, thresholds, budgets, aggregation, and the analysis plan are frozen and hashed.
10. Test results are not used to tune those choices. A change after seeing test results requires a new confirmatory set.
11. The custodian records hashes and an immutable manifest before release and again after the evaluation, including the code revision and configuration that actually ran.
12. The published result lists every exclusion, failure, skip, and missing output. Undefined metrics stay undefined when a denominator is zero.

The current builder rejects a config that enables Final Test. A future test set needs its own pipeline and custodian. It is not produced by flipping `final_test.enabled` on research_v1.

## Freeze checklist

Use this list twice: once for the exploratory artifact, and again before any confirmatory run. A row marked "recorded" means the research_v1 files already store it. A row marked "not sealed" means it is still open and blocks confirmatory use.

| Checklist item | Exploratory research_v1 | Confirmatory evaluation |
|---|---|---|
| Dataset manifest and file hashes | Recorded. `manifest_sha256` and `output_sha256` / `offline_output_sha256` are inside the manifest. This report does not recompute them. | Not sealed. Recompute and store hashes immediately before and after the confirmatory run. |
| Source versions | Recorded for GSM8K and HotpotQA as cited above. License text is still empty. | Not sealed until license/citation status is accepted or explicitly waived. |
| Label provenance and unresolved ledger | Recorded. Unresolved rows remain in `unresolved_candidates.jsonl`. Human adjudication is not claimed. | Not sealed. Automated labels are not an approved confirmatory gold standard until the team says so. |
| Group and split identities | Recorded. History 600, Development 400, Final Test absent. | Not sealed against a future test set. The leakage audit is only a conditional pass. |
| Dataset config | Recorded as `evaluation/config/research_dataset.yaml`, seed 42, Final Test disabled. | A confirmatory config must not enable the old test partition. |
| Code commit | Not recorded in the manifest. | Required before test access. Not recorded here. |
| Verifier, model, and resource configuration | Not bound. Attempt collection is not execution-ready. | Required. Corpus path, index, model snapshots, and adapter hash must be pinned. |
| Metrics and analysis plan | Defined in `evaluation/docs/evaluation_metrics.md` and the sample-size plan. Interval level and bootstrap draws are not approved. | Required as a frozen plan. Not approved. |
| Loss and threshold | Implementation defaults and an unapproved pilot proposal exist. They are not an approved research setting. | Exploratory until explicitly approved. Not approved here. |
| Leakage audit | Conditional pass, dated with this documentation set. | Must be repeated against the new test pool. Semantic leakage remains unverified. |
| Dataset readiness | `policy_fitting_ready` is false. Zero Attempts and zero offline Examples. | Not ready. |
| No silent edits after freeze | The builder refuses to overwrite the non-empty directory. Do not hand-edit JSONL or the manifest. | Any change after the confirmatory hash is a new version, not a quiet patch. |

## What this freeze allows

Exploratory work may read research_v1 History and Development under the existing label and leakage limitations. That includes a Development-only feasibility pilot, as described in `evaluation/docs/research_v1_sample_size_and_compute_plan.md`, provided the pilot does not modify these files and does not open Final Test.

Exploratory results must be labeled exploratory. They must not be described as confirmatory, as a powered evaluation, or as evidence from a protected holdout.

## What remains unresolved

- No custodian, access log, or approval exists for a protected test.
- No new test groups have been sampled, and none should be sampled by editing research_v1.
- Loss weights, decision threshold, budgets, aggregation, interval level, and bootstrap draws are not frozen.
- Verifier and corpus configuration for a real run is not pinned.
- Shared HotpotQA context and unverified semantic leakage still limit even the exploratory split.
- Candidate labels are automated. HotpotQA still has no verified incorrect class.
- `policy_fitting_ready` remains false until real Attempts and Examples exist and pass the training-manifest checks.
