# Verified-subset preparation protocol

## Purpose and scope

This protocol constructs a smaller, reproducible GSM8K/HotpotQA candidate population from the existing History and Development partitions. The initial target is 100 questions per benchmark (both candidate variants remain together, so 200 candidate records per benchmark when each source row has its expected pair). Target size is not a quota for verified labels: if a validation basis is insufficient, the candidate remains `unresolved`.

This subset is for evaluating methods on a clearly described population. It does not establish correctness prevalence across all benchmark examples. No candidate is judged by the multi-agent framework under evaluation.

## Read boundaries and source audit

The builder reads only:

- `evaluation/datasets/unified/history.json` and `development.json`.
- GSM8K raw `train` only, which supplies source rows for the existing GSM8K History and Development IDs.
- HotpotQA raw `train` only for selected History examples.
- The first 5,000 records of each existing v1 adjudication JSONL, whose verified source-order boundary is 4,000 History and 1,000 Development candidates.

HotpotQA Development context is taken from the existing unified Development rows and checked against the Development source-answer provenance already recorded in the adjudication overlay. The upstream HotpotQA validation split is not opened because it co-occurs with identities already used for the existing exposed Final Test partition. GSM8K raw `test`, unified `final_test.json`, HotpotQA raw `validation`, and every Final Test adjudication row are outside the read scope. Source hashes and selected IDs are recorded in the generated `subset_manifest.json`.

Existing candidate construction is in `evaluation/prepare_all_benchmarks.py`: GSM8K candidates use the benchmark final answer and a synthetic numeric perturbation; HotpotQA uses the benchmark answer and a borrowed cross-example answer. Existing adjudication source records classify the benchmark-gold candidates as source matches and generated alternatives as unresolved. The builder does not use `expected_correct` as correctness ground truth.

## Reproducible selection and grouping

Default seed: **20261104**. Sampling is without replacement from sorted eligible records and stratified by existing partition: target 80 History and 20 Development questions per benchmark, proportional to the 2,000:500 available partition sizes. If an exact-question group is duplicated across partitions, only one representative is eligible. Grouping is by benchmark plus lowercase alphanumeric-normalized question. Both candidate variants of each selected question are retained together. The manifest stores the actual counts and all selected question/candidate IDs.

The unified data do not contain semantic related-example group IDs. Exact normalized duplicates and stable source IDs can be handled; paraphrases, related entities, shared facts, and broader semantic leakage cannot be ruled out. The group field is a reproducible exact-question key, not a claim that all related examples have been clustered.

## Candidate validation and labels

Every candidate row records candidate/example ID, benchmark and version, partition, answer and gold answer, candidate-generation method, correctness status, method, evidence/provenance, rationale, confidence category, and an unresolved reason when applicable. Permitted statuses are `verified_correct`, `verified_incorrect`, and `unresolved`.

### GSM8K

For each selected question, the builder links its encoded source split/index to the local raw GSM8K training row and checks that the source question and final answer match. It reads the original worked solution, independently evaluates each tagged arithmetic expression using exact rational arithmetic, checks every displayed result, and requires the last checked result and `####` answer to agree before a benchmark-gold-equivalent numeric candidate is marked `verified_correct`.

Numeric normalization supports signed integers, comma-grouped values, decimal notation, and fractions with exact rational comparison. Thus equivalent representations such as `1,000`, `1000.0`, and `1000` compare equally. Unsupported or failed arithmetic annotations make the replay incomplete and prevent this path from verifying a candidate.

This procedure independently recomputes displayed arithmetic; it does not independently solve the natural-language interpretation of every word problem. A non-matching synthetic answer stays `unresolved`, even if it is `gold + 1`: numeric difference alone does not establish semantic incorrectness. No generated candidate is automatically marked `verified_incorrect`. A `verified_correct` benchmark candidate is explicitly labeled as a benchmark-source match plus arithmetic replay, not as independent human verification.

### HotpotQA

For History examples, source IDs, question, answer, context and supporting facts are checked against raw HotpotQA `train`. For Development examples, the existing unified Development context and support annotations are used; the mixed raw validation split is not opened. The source answer is cross-checked against the existing source-provenance overlay.

The evaluation is **benchmark-context-assisted**: the supplied per-question context and supporting facts are used, not retrieval from the shared 13,083-article corpus. For each candidate, record the SQuAD-style normalized exact match and token F1 against the benchmark answer. Both metrics are diagnostics only: mismatch or low F1 does not prove factual incorrectness. Benchmark-answer matches are marked `verified_correct` only when the benchmark source match and supporting-fact-to-context provenance are present; this is not an independent human semantic judgment. Borrowed answers that do not match remain `unresolved` until question-conditioned factual adjudication establishes their status. No borrowed candidate is automatically marked incorrect.

Evidence entries retain the supporting-fact title and sentence ID and include the associated benchmark context paragraph. Unified Development preserves paragraph text and fact references but not sentence boundaries, so the exported evidence does not claim to extract a precise supporting sentence. Where support references cannot be mapped to non-empty context, factual verification is unresolved.

## Interpretation, metrics, and limitations

`validation_summary.json` reports question/candidate counts by benchmark, status, partition, source method and validation method. Benchmark source matching is separated from arithmetic replay or HotpotQA context provenance. `quality_check.json` records structural and provenance checks.

Unresolved candidates must be excluded from binary correctness metrics or reported as unresolved under a predeclared metric policy; they must never be silently treated as incorrect. The subset retains every candidate for the selected questions so the amount of unresolved coverage is visible. The resulting performance population may be smaller than 100 fully resolved questions per benchmark and can differ in difficulty from the full source benchmark.

No human decisions are fabricated or entered. Only independent arithmetic computation and benchmark-source/context provenance are used. Exact-match/F1 and `expected_correct` do not independently adjudicate synthetic alternatives. Final Test remains untouched, and the subset does not restore its protected/unseen status. The four main research experiments are outside this preparation step.

## Reproduction and validation

From the repository root:

```powershell
.\.venv\Scripts\python.exe evaluation\data_preparation\build_verified_subset.py build --seed 20261104
.\.venv\Scripts\python.exe evaluation\data_preparation\build_verified_subset.py validate --subset-dir evaluation\datasets\verified_subset\v1_seed_20261104
```

The builder refuses to overwrite a non-empty output directory. It validates unique candidate IDs, unique exact-question groups, correct candidate pair retention, History/Development-only provenance, source linkage, status values, evidence for verified labels, unresolved reasons, and selected IDs against the manifest. It never opens Final Test paths or runs experiment code.
