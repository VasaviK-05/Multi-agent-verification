# Final-test manifest (not yet allocated)

**Status: NOT READY / NO PROTECTED FINAL-TEST PARTITION CREATED.** This manifest documents known source identity and fields that must be completed after the team approves benchmark selection, candidate adjudication, grouping, split size, corpus condition, and custody. The current workspace already contains files named `final_test.json`; they are exposed development artifacts and are not a protected holdout for a new confirmatory claim.

## Proposed population fields

| Field | Approved value |
|---|---|
| Dataset names and versions | Pending team approval. Audited options: GSM8K `main` (source commit `740312add88f781978c0658806c59bc2815b9866`); HotpotQA `distractor` (source commit `1908d6afbbead072334abe2965f91bd2709910ab`); optional FEVER v1.0. MultiNLI excluded from answer-validation interface. |
| Independent related-example groups | Not allocated; group discovery and paraphrase/link audit required. |
| Number of questions | Not allocated. |
| Number of candidate answers | Not allocated; depends on independently adjudicated candidates. |
| Correct/incorrect label counts | Not allocated; do not expose final-test labels in this manifest. |
| Partition information | New custodian-controlled holdout required; current `unified/final_test.json` (2,000 rows, 500 per each of four benchmarks) and `processed/final_test.json` (1,000 rows) are not protected. |
| Grouping method | Pending approval; group source question, paraphrases, all candidate variants, and related examples before splitting. |
| Random seed | Pending approval and assignment; record algorithm/version and seed in custodian receipt. |
| Evidence resource | Pending condition choice. Current candidate corpus identities: `data/articles_13083.json`, SHA-256 `b26539d013201a0435884098ae8bd3544342d0a815964bf104b9524808e9bfa8`; `data/evidence_corpus.json`, SHA-256 `668b48aa59c758d6e5d082f9d07b9c544730c545ae3af36728e68a0144ec6ec5`. Record corpus and index version actually used, or mark reference-assisted context identity per example. |
| File hashes | Not applicable until a new partition is authorized and generated. Then record SHA-256 for each partition and source manifest. |
| Final-test custody | Not established. A custodian must retain labels and identities, restrict access, record access, receive frozen policy/configuration hashes, run the evaluation, and release outcomes after completion. |

## Completion rule

Complete this manifest only from the validated generated partition and custodian receipt. Do not include final-test candidate strings or labels in a public manifest. Until then, do not describe the research dataset as ready or report current final-test files as unseen held-out evaluation.
