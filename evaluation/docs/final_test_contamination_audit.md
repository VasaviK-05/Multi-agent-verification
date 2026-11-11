# Final Test contamination audit (content level)

**Verdict: CONTAMINATED. The provisional Final Test `research_v1_final_test_provisional_v1` is retired and must never be used for confirmatory evaluation.**

807 of its 2,638 question groups (GSM8K 500 of 1,319; HotpotQA 307 of 1,319) appear, by normalized question text, in files that were previously exposed, used as Development data, reviewed, or already run through the framework. The original leakage audit missed this because it compared the roster only with the research_v1 History and Development candidate files, and the builder's exposure guard only checked that the old unified `final_test.json` was not configured as a source *path*.

## Method

- Generator: `python -m evaluation.data_preparation.experiment1_preparation generate` (write-once), reproduced exactly by `... validate`.
- Output: `evaluation/datasets/experiment1_preparation/experiment1_preparation_v1/final_test_contamination_audit.json` (SHA-256 `931134bbec80aaecaaa2623759faded2943f41b0c70e74708986dbee18dc8ac8`).
- Target: the evaluation roster (`evaluation_roster.jsonl`, SHA-256 `5af06474…f823c4`; manifest `cc186376…db87e46`). Only `question`, `benchmark`, group and source IDs were used.
- Compared against every JSON/JSONL file under `evaluation/datasets/`, `evaluation/results/` and `data/test_benchmark.jsonl`: 141 files, each recorded with its SHA-256. Every string stored under a `question` key, at any depth, was normalized (lowercase, alphanumerics only) and matched exactly.
- Custodian label directories (`_custodian`) were not opened. No label, gold answer or correctness field was read.

ID matching was not used: the old unified files number GSM8K test items differently, so ID comparisons both miss real overlaps and report coincidental ones.

## Results

| Exposure category | GSM8K groups | HotpotQA groups |
|---|---:|---:|
| Exposed Final Test files (`unified/final_test.json`, `processed/final_test.json`) | 500 | 170 |
| Development files (`unified/development.json`, `processed/development.json`) | 0 | 149 |
| Baseline outputs (`evaluation/results/baseline/baseline_results.jsonl`) | 0 | 30 |
| Verifier outputs (`evaluation/results/evidence_hotpotqa_results.json`) | 0 | 1 |
| Other derived datasets (adjudication queues) | 500 | 143 |
| **Contaminated groups (union)** | **500** | **307** |
| Clean groups remaining | 819 | 1,012 |

A group can appear in several categories, so the rows are not additive. Per file:

| File | GSM8K | HotpotQA |
|---|---:|---:|
| `evaluation/datasets/unified/final_test.json` | 500 | 88 |
| `evaluation/datasets/processed/final_test.json` | 0 | 83 |
| `evaluation/datasets/unified/development.json` | 0 | 55 |
| `evaluation/datasets/processed/development.json` | 0 | 95 |
| `evaluation/datasets/adjudication/v1/gsm8k_blinded_review_queue.jsonl` | 500 | 0 |
| `evaluation/datasets/adjudication/v1/hotpotqa_blinded_review_queue.jsonl` | 0 | 143 |
| `evaluation/datasets/adjudication/pilot_v1_seed_20261101/gsm8k_review_queue.jsonl` | 10 | 0 |
| `evaluation/results/baseline/baseline_results.jsonl` | 0 | 30 |
| `evaluation/results/evidence_hotpotqa_results.json` | 0 | 1 |

No overlap was found with research_v1 History or Development candidate files, which is consistent with the original audit.

## Consequences

- The manifest field `previously_exposed_final_test_reused: false` described the configured source path, not the content. It is incorrect as a content claim. The manifest is hash-bound and was not edited; the correction is recorded here and in the retirement registry.
- The 819 GSM8K and 1,012 HotpotQA groups without exact overlap are not a clean holdout either. The whole roster, including every gold answer, has been read by tooling and people, and paraphrases and shared passages were not tested. Do not salvage a subset as a Final Test.
- Even without contamination, the set is all benchmark-gold, so false acceptance, correct rejection and forced-support attack effects are not estimable on it.

## Retirement

- Registry: `evaluation/config/final_test_retirements.json` lists the manifest SHA-256 with `confirmatory_use: PERMANENTLY_FORBIDDEN`.
- `final_test_workflow.read_custodian_labels` refuses retired manifests before reading the authorization file or writing the access log.
- `final_test_workflow.validate_readiness` reports the retired set as BLOCKED with `retired_permanently_forbidden_for_confirmatory_use`.
- All provisional files (evaluation roster, manifest, leakage audit, receipts, custodian labels) are preserved byte-for-byte. Their hashes still match the manifest.
- Its questions and paragraphs are part of the exposure set for any future Final Test (see `final_test_v2_selection_plan.md`).

## Builder fix

`final_test_workflow.build` now scans the same exposure roots, excludes any source row whose normalized question was previously exposed (`previously_exposed_question`), fails closed if a selected group still overlaps, and records a computed `exposure_audit` in the manifest instead of the hardcoded flag. Tests: `tests/test_final_test_retirement.py`.

## Limitations

Exact normalized question text only. Paraphrases, translated or templated duplicates, and shared evidence passages are not detected by this verdict. The v2 pool plan additionally excludes exact shared HotpotQA paragraphs.
