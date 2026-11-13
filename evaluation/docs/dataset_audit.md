# Evaluation dataset audit

Audit performed against the checked-in files on 2026-11-01. Counts below are observed from the local Arrow datasets and JSON records. Dataset card/version metadata and source commit references are reported where stored; no downloaded corpus is assumed current beyond its local fingerprint.

## Inventory and counts

| Dataset / local version | Available source partitions and examples | Label / candidate observations | Audit status |
|---|---|---|---|
| FEVER v1.0 (`labelled_dev` etc.; source `train` 311,431 rows, `labelled_dev` 37,566, `paper_dev` 18,999, `paper_test` 18,567; also unlabelled dev/test 19,998 each) | The Arrow rows are evidence-annotation rows, not unique claims. Existing preparation combines rows by claim ID. | Three independent benchmark labels: SUPPORTS, REFUTES, NOT ENOUGH INFO. The unified sample has 2,000/500/500 claims by History/Development/Final test. | Gold label provenance is the FEVER annotation. Evidence titles/IDs/sentence IDs are retained in source data, but the referenced evidence sentence text is not included in the unified records. |
| GSM8K `main`, local source commit `740312add88f781978c0658806c59bc2815b9866` | Train 7,473; test 1,319. Existing unified counts: 2,000/500/500 questions. | Each prepared question has one `benchmark_gold` candidate marked correct and one `synthetic_numeric_perturbation` marked incorrect; 4,000/1,000/1,000 candidate rows respectively. No independent wrong-answer annotation. | The extracted gold number comes from the `####` answer marker. Candidate error label is a construction rule, not a benchmark label, and must be audited for question-specific ambiguity. |
| HotpotQA distractor, local source commit `1908d6afbbead072334abe2965f91bd2709910ab` | Train 90,447; validation 7,405. Existing unified counts: 2,000/500/500 questions. | Each prepared question has one `benchmark_gold` candidate and one `synthetic_cross_example_answer` candidate, for 4,000/1,000/1,000 candidates. No independent wrong-answer annotation. | Gold answer, context paragraphs, supporting facts, type and difficulty are sourced from HotpotQA. Cross-example answer is not guaranteed false and requires independent verification. |
| MultiNLI / GLUE `mnli`, local source commit `bcdcba79d07bc864c1c254ccfcedcce55bcc9a8c` | Train 392,702; validation matched 9,815; validation mismatched 9,832; test matched 9,796; test mismatched 9,847. Existing unified counts: 2,000/500/500. | Entailment / neutral / contradiction labels exist in the source. | Not suitable for the question/candidate-answer acceptance interface without changing the task mapping; do not include in this evaluation. |

The separate `datasets/processed/` artifacts contain FEVER and HotpotQA only: history 4,000, development 1,000, final test 1,000. Their manifests report those same totals. HotpotQA rows in these files are gold-answer-only, so they contain no incorrect candidates. These are distinct from `datasets/unified/` and must not be treated as equivalent partitions.

The `datasets/unified/` files each contain four benchmarks: 8,000 history, 2,000 development, and 2,000 final-test questions, with 2,000/500/500 questions per benchmark. Existing exact IDs do not overlap between these three files. However, they have no `group_id`, no label-provenance fields, and no recorded split-generation receipt or final-test custody metadata. Exact-ID disjointness does not establish paraphrase or related-example disjointness. Current split construction intermixes unrelated source splits (including GSM8K train for history/development and GSM8K test for final test) in a deterministic sample. FEVER sampled source splits are train, paper_dev, and paper_test, respectively; HotpotQA uses train for history and randomly divided validation for development/final test; MultiNLI uses train, matched validation, and mismatched validation. A source-level difference alone does not establish no semantic overlap.

IDs in the existing JSON records are unique within each file. FEVER IDs derive from source claim IDs; HotpotQA IDs derive from source IDs; GSM8K and MultiNLI IDs encode source split and row index. These are useful stable identifiers if accompanied by dataset version. No shared related-example group IDs are present. In paired candidate sets, answer variants are within the same question record but are expanded into distinct experiment instances by the baseline adapter.

## Candidate labels and data quality

| Existing unified partitions | Benchmark | Questions | Correct candidate labels | Incorrect candidate labels | Gold / provenance |
|---|---:|---:|---:|---:|---|
| History | GSM8K | 2,000 | 2,000 | 2,000 | Gold number extracted from GSM8K answer; synthetic negative is gold + 1 |
| Development | GSM8K | 500 | 500 | 500 | Same construction |
| Final test | GSM8K | 500 | 500 | 500 | Same construction |
| History | HotpotQA | 2,000 | 2,000 | 2,000 | Gold answer from HotpotQA; negative borrowed from another row's answer |
| Development | HotpotQA | 500 | 500 | 500 | Same construction |
| Final test | HotpotQA | 500 | 500 | 500 | Same construction |

Correctness labels exist in the prepared candidate objects as `expected_correct`, but the source benchmark only independently establishes the canonical answer, not the synthetic negative's incorrectness. The unified FEVER examples have benchmark labels but are not answer-candidate variants. NOT ENOUGH INFO is a third “insufficient evidence to label” class, not an incorrect candidate.

The baseline result file represents 1,232 unique instances: HotpotQA 496, GSM8K 490, FEVER 246. All are marked `completed`; roles are accept 574, reject 576, abstain 82. Benchmark gold roles correctly retain FEVER NOT ENOUGH INFO as abstain. Compared with the present unified development file, expected adapter instances would be 1,000 each for HotpotQA and GSM8K and 500 for FEVER; the result has 496, 490, and 246 respectively. The result rows do not identify why these many instances are absent. Reconcile the expected-versus-observed inventory before reuse.

## Evidence availability

The configured/default retriever is `app/verifiers/evidence_retriever.py`: `EVIDENCE_CORPUS_PATH` overrides the default `data/evidence_corpus.json`. The checked-in baseline protocol records `data/articles_13083.json` as the baseline run's evidence corpus. Its index manifest records SHA-256 `b26539d013201a0435884098ae8bd3544342d0a815964bf104b9524808e9bfa8`, 13,083 articles, 500-word chunks, and `all-MiniLM-L6-v2`. The default corpus `data/evidence_corpus.json` has 500 articles and SHA-256 `668b48aa59c758d6e5d082f9d07b9c544730c545ae3af36728e68a0144ec6ec5`. Corpus choice must be frozen and recorded for a new run.

Measured against the baseline's 13,083-article corpus using direct title matching:

| Existing unified split | FEVER claims with any cited title present | HotpotQA questions with any context title present | HotpotQA questions with all supporting-fact titles present | Supporting-title occurrences present |
|---|---:|---:|---:|---:|
| History | 0/2,000 | 28/2,000 | 0/2,000 | 5/4,753 |
| Development | 0/500 | 7/500 | 0/500 | 1/1,218 |
| Final test | 0/500 | 11/500 | 0/500 | 6/1,211 |

The baseline report's separate count of 0/301 distinct FEVER titles in development agrees with this audit. Title presence is only a preliminary availability check; it does not show that retrieval returns relevant text or that a verifier can use it successfully. Under the corpus-backed setting, FEVER and HotpotQA would largely be evidence-absent. If benchmark-provided context is supplied directly, evaluation is reference-assisted and every comparison method must receive the same permitted context. The existing HotpotQA evaluator also builds per-example corpora from reference paragraphs; that is a different resource condition and must not be conflated with the configured shared corpus.

## Readiness and unresolved items

The current files are audit inputs, not a research-ready dataset. Incorrect candidate labels have not been independently adjudicated; no grouping metadata or protected final-test custody exists; corpus identity varies by experiment; direct arithmetic versus word problems are not annotated; and the final-test pool has already been loaded into the workspace and used in an existing prepared artifact. Do not report new held-out results from these files as protected final-test results. Team approval is needed for population, candidate-label audit, split policy, loss/constraints, corpus policy, and custody before final partitions are created.
