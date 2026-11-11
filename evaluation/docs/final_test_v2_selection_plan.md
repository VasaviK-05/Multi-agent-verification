# Final Test v2 selection plan (label-free, not authorized)

> **Update 2026-11-11: an exploratory v2 has been built under temporary research mode.** See `exploratory_dataset_and_final_test_v2.md`.
> - Version `research_v1_final_test_v2_exploratory_v1`, manifest `478001c7…b499031`.
> - It follows this plan's pools (both eligible-ID hashes reproduced exactly) and procedure. The pending decisions below were replaced by automated, provisional choices:
>   - synthetic negative rules (GSM8K gold+1; HotpotQA yes/no, other entity, number increment, distractor title);
>   - the GSM8K train source;
>   - seed 20261111;
>   - 300 groups per benchmark;
>   - groups without a negative skipped.
> - All negatives are SYNTHETIC_INCORRECT. Human approval and adjudication are DEFERRED. Custody is `DESIGNATED_CUSTODIAN_IS_DATASET_CREATOR` (the dataset creator, not an independent custodian). Evaluation authorization stays PENDING, and the manifest stays NOT_AUTHORIZED.
>
> The plan text below is unchanged and still describes what a confirmatory v2 would need.

This is a plan, not a dataset. No v2 roster, candidate or label exists. No answer, gold label, worked solution or supporting-fact column was loaded to produce it. Building v2 needs the team decisions listed below and an independent custodian.

## Eligible source pools

- Generator: `python -m evaluation.data_preparation.experiment1_preparation generate`.
- Output: `evaluation/datasets/experiment1_preparation/experiment1_preparation_v1/final_test_v2_selection_plan.json` (SHA-256 `5354eedc04d43a785cbdd253a62204bd95db40cecbc3df993bf1736670ee60ce`).
- Raw columns read: GSM8K `question`; HotpotQA `id`, `question`, `context`.
- Exposure set: 145 files under `evaluation/datasets/`, `evaluation/results/` and `data/test_benchmark.jsonl`, including the retired provisional Final Test roster. That gives 13,892 exposed normalized questions and 124,526 exposed exact paragraph hashes (HotpotQA only).

A source row is eligible when all three hold:
- its normalized question is not in the exposure set;
- it is not a duplicate within the benchmark pool;
- for HotpotQA, none of its paragraphs is an exposed exact paragraph.

| Benchmark | Split | Source rows | Eligible | Main exclusion reasons (rows can have several) | Eligible-ID SHA-256 |
|---|---|---:|---:|---|---|
| GSM8K | test | 1,319 | **0** | exposed question 1,319 | `37517e5f…5b570` |
| GSM8K | train | 7,473 | **4,973** | exposed question 2,500 | `9168c406…b234c` |
| HotpotQA | validation | 7,405 | **1,590** | exposed paragraph 5,815; exposed question 2,877 | `88114b49…eb782` |
| HotpotQA | train | 90,447 | **30,758** | exposed paragraph 59,686; exposed question 3,951; duplicate 13 | `0b07e9c4…6e9f4` |

Full hashes are in the plan JSON. The GSM8K test split is exhausted: every question is either in the old exposed files or in the retired provisional set. A GSM8K v2 Final Test therefore has to come from the 4,973 train questions that no partition has used. That needs team approval and should be disclosed in any report.

## Candidate design (pending approval)

- **Unit:** one question group with two candidates, the benchmark gold answer and one verified-incorrect answer. This paired design keeps group-level bootstrap and paired comparisons intact. Class proportions follow from it; no target prevalence is chosen.
- **GSM8K negatives:** the existing gold+1 discrete-count rule (`build_verified_negative_candidates.validate_gsm_discrete_count_negative`, with full worked-solution replay). It is accepted for History/Development but not yet approved for Final Test use. It applies only to "how many" integer questions without ratio or rounding cues, so many groups will not qualify.
- **HotpotQA negatives:** no approved method. Explicit negation and cross-example donor answers are unresolved under the current protocol (`build_research_dataset.py`). Options: blinded human adjudication of cross-example candidates (pilot v3 has 0 of 60 decisions), or a newly approved rule such as the yes/no complement. Without one, HotpotQA claims in v2 are limited to false rejection.
- **Groups with no verifiable negative:** drop, or keep gold-only and report separately. Pending decision; it must be made before any system output is seen.
- **Unresolved candidates:** excluded from binary metrics and counted. Never relabelled incorrect.
- **Sample size:** pending an approved power or precision justification. The pools above are upper bounds before within-pool deduplication.

## Procedure for the custodian (after approval)

1. Rebuild the eligible pools from the recorded inputs and check each eligible-ID SHA-256.
2. Remove within-pool shared paragraphs and supporting facts, then draw groups with a seed fixed and recorded before drawing.
3. Apply the approved negative rules in the custodian space; groups without a negative follow the approved decision.
4. Write a new versioned roster and separate custodian labels with `final_test_workflow`. Its manifest must contain a passing `exposure_audit` (method `normalized_question_text_v1`) and per-benchmark label counts that include both classes. The current builder only produces gold candidates and only accepts GSM8K test and HotpotQA validation splits, so v2 needs a reviewed builder extension for train sources and negatives.
5. Prepare a `FinalTestReservation` (`app/game/offline/records.py`) from the roster: one `ReservedExample` per candidate. Labels stay sealed until authorization.
6. Confirmatory status needs an authorization record (`approved`, `manifest_sha256`, `approver`, `custodian`) passed to `final_test_workflow readiness --authorization`. The manifest itself stays `NOT_AUTHORIZED`.

## Development must match

Development has no HotpotQA verified-incorrect candidates (see `experiment1_readiness_report.md`). A policy fitted there cannot learn HotpotQA false acceptance. The same approved negative rules should be applied to History and Development, which changes labels and therefore requires a new research_v1 version. The current version stays preserved.
