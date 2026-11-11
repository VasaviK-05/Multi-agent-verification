# research_v1 dataset inventory and provenance

Inventory taken 2026-11-11 from the working tree at Git HEAD `13174aa` (`evaluation/datasets/` is Git-ignored, so artifacts are local). Row counts were measured directly. Hashes listed here were verified by `person1_validation`.

## Research artifacts in use

| Artifact | Rows | Role |
|---|---:|---|
| `reconciled_candidates/research_v1/history_candidates.jsonl` | 1,240 | History candidates (all labels) |
| `reconciled_candidates/research_v1/development_candidates.jsonl` | 810 | Development candidates (all labels) |
| `reconciled_candidates/research_v1/gsm8k_reconciled.jsonl` / `hotpotqa_reconciled.jsonl` | 1,000 / 1,050 | Per-benchmark views of the same 2,050 records |
| `reconciled_candidates/research_v1/unresolved_candidates.jsonl` | 871 | Unresolved subset |
| `offline_examples/research_v1/history_prepared.jsonl` | 701 | Binary-labelled History |
| `offline_examples/research_v1/development_prepared.jsonl` | 478 | Binary-labelled Development |
| `offline_examples/research_v1/excluded_unresolved.jsonl` | 871 | Excluded with reason |
| `final_test_research_v1_eval_v1/evaluation_roster.jsonl` | 2,638 | Provisional Final Test roster (no label fields) |
| `_custodian/final_test_research_v1_v1/custodian_labels.jsonl` | not opened | Final Test labels (byte hash verified only) |
| `person1/research_v1_person1_v1/*` | see roster doc | Person 1 rosters, queue, contracts, validation summary |
| `development_pilot/research_v1_feasibility_v1`, `_v2` | — | Blocked feasibility pilots: 0 verifier calls, `BLOCKED_PREFLIGHT` |

## Older or pilot artifacts (not research_v1)

| Artifact | Rows | Note |
|---|---:|---|
| `unified/{history,development,final_test}.json` | 8,000 / 2,000 / 2,000 | Older unified split; `final_test.json` is exposed. research_v1 drew its groups from unified History/Development |
| `processed/final_test.json` | 1,000 | Exposed; not a holdout |
| `offline_examples/research_pilot`, `v1_reconciled_candidates` | 203+61 / 232+59 prepared | Earlier preparations |
| `reconciled_candidates/research_pilot`, `v1` | 380+110 / 200+250 | Earlier reconciliations |
| `verified_subset/v1_seed_20261104`, `verified_negative_candidates/v1` | 400 / 100 | Earlier subsets |
| `adjudication/pilot_v1…v3`, `adjudication/v1` | 60 per pilot; 6,000 per benchmark in v1 | Review queues/templates; no completed research_v1 human labels |

## Source provenance

| Benchmark | Source version | research_v1 split | Final Test split |
|---|---|---|---|
| GSM8K | `openai/gsm8k main@740312add88f781978c0658806c59bc2815b9866` | train | test |
| HotpotQA | `hotpotqa/hotpot_qa distractor@1908d6afbbead072334abe2965f91bd2709910ab` | train | validation |

All 2,050 research_v1 records and all 2,638 Final Test roster rows carry the expected source version (0 mismatches). The research_v1 manifest records 15 source-file hashes and 12 output hashes; all 27 match the files on disk, and the manifest self-hash `8cc984be…a7c1d1` verifies. License and citation fields in the local `dataset_info.json` files are empty, so licensing is pending.

## Evidence corpus identity

| Corpus | SHA-256 (verified) | Index |
|---|---|---|
| `data/articles_13083.json` (set by `.env` `EVIDENCE_CORPUS_PATH`) | `b26539d013201a0435884098ae8bd3544342d0a815964bf104b9524808e9bfa8` | `idx-6d28c9c49dac` |
| `data/evidence_corpus.json` (retriever code default) | `668b48aa59c758d6e5d082f9d07b9c544730c545ae3af36728e68a0144ec6ec5` | `idx-9c87422f0357` |

research_v1 HotpotQA uses supplied reference context and binds neither corpus. An Evidence Verifier run must record which corpus and index it loaded.

## Existing result files and the "700 results"

Read-only compatibility check (`teammate_compatibility.json`). File hashes were identical before and after the run.

| File | Rows | Unique questions | research_v1 History overlap | research_v1 Development overlap | Final Test overlap |
|---|---:|---:|---:|---:|---:|
| `evaluation/results/rule_gsm8k_results.json` | 1,000 | 500 | 0 | 200 | 0 |
| `evaluation/results/evidence_hotpotqa_results.json` | 10 | 5 | 0 | 2 | 0 |
| `evaluation/results/baseline/baseline_results.jsonl` (partial baseline run) | 1,232 | 739 | 0 | 191 | 0 |

These runs used the older `unified/development.json`, so they overlap research_v1 **Development** questions only. That is allowed, because Development is the tuning partition, but the outcomes must not be described as held-out results. They have no History or Final Test overlap.

No artifact matching "the teammate's 700 results" was found. The search covered `evaluation/results`, every dataset directory, all local and remote branch file lists for result/cost/attempt files, and the application database (largest table: 32 rows). The nearest count is `history_prepared.jsonl` (701 rows), but that file is a Person 1 label preparation, not verifier results. Status: **BLOCKED pending the owner's file path or run identifier.** Nothing was recovered or overwritten.
