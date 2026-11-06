# research_v1 group-level leakage audit

## Audit scope and files inspected

This audit checks whether History and Development in `research_v1` share question groups, source examples, or context. It does not change the dataset. Final Test files were not opened. `research_dataset.yaml` sets `final_test.enabled` to false, and a protected holdout is not available.

Files read:

- `evaluation/config/research_dataset.yaml`
- `evaluation/datasets/reconciled_candidates/research_v1/manifest.json`
- `evaluation/datasets/reconciled_candidates/research_v1/validation_summary.json`
- `evaluation/datasets/reconciled_candidates/research_v1/history_candidates.jsonl` (1,240 candidate records)
- `evaluation/datasets/reconciled_candidates/research_v1/development_candidates.jsonl` (810 candidate records)
- `evaluation/datasets/unified/history.json` and `evaluation/datasets/unified/development.json`, used only to test whether HotpotQA donor IDs fall in the other unified partition
- Grouping code: `evaluation/data_preparation/build_research_dataset.py` (`group_id`) and `evaluation/data_preparation/build_verified_subset.py` (`norm_question`)
- Existing leakage checks in `evaluation/data_preparation/build_research_dataset.py` (`validate_candidate_rows`) and `tests/test_research_dataset_pipeline.py`
- `evaluation/docs/research_scale_dataset_protocol.md` and `evaluation/docs/dataset_selection.md`

The reconciled JSONL files are the records that were compared. Manifest counts were used as the expected roster, not as a substitute for the comparison.

## Methodology

`research_dataset.yaml` sets `grouping_method` to `exact_normalized_question_with_source_id_preserved`. The builder normalizes a question by lowercasing it and removing every character that is not an ASCII letter or digit (`norm_question`). The group ID is `gsm8k-q-` or `hotpotqa-q-` plus the first 16 hex characters of the SHA-256 of that normalized text. The original `dataset_id` is stored separately.

For GSM8K and HotpotQA separately, History was compared with Development on:

- `related_group_id`
- `dataset_id`
- `candidate_id`
- raw question text
- `norm_question` text
- recomputed group ID versus the stored group ID
- HotpotQA `evidence_provenance.source_id`
- HotpotQA `evidence_provenance.context_hashes`
- HotpotQA supporting-fact `(title, sentence_id)` pairs
- SHA-256 of each original context paragraph text, and context titles
- `donor_dataset_id` on HotpotQA borrowed candidates, checked against the selected research_v1 IDs and against unified History and Development IDs

GSM8K rows do not carry a context passage. Their `evidence_provenance.source_id` is null. Their question identity was checked with `dataset_id`, which is the GSM8K source question ID.

No embedding or paraphrase model was run. Semantic leakage is unverified.

## Exact duplicate results

| Check | GSM8K | HotpotQA |
|---|---:|---:|
| History candidate records | 600 | 640 |
| Development candidate records | 400 | 410 |
| History question groups | 300 | 300 |
| Development question groups | 200 | 200 |
| Group IDs in both partitions | 0 | 0 |
| Raw questions in both partitions | 0 | 0 |
| Normalized questions in both partitions | 0 | 0 |
| `dataset_id` values in both partitions | 0 | 0 |
| `candidate_id` values in both partitions | 0 | 0 |
| Groups whose stored ID differs from `group_id(benchmark, question)` | 0 | 0 |
| Groups whose candidates disagree on question, `dataset_id`, or partition | 0 | 0 |

Each group ID is the hash of one normalized question, and every stored group ID matches that hash. A repeated normalized question inside a partition would have produced the same group ID. None did. Combined, the 1,000 question groups are partition-disjoint under this exact normalization.

## Group and source-ID overlap

Unified History contains 8,000 IDs and unified Development contains 2,000 IDs. Those two ID sets are disjoint. This count includes every benchmark in those files. It is not a Final Test comparison.

HotpotQA `evidence_provenance.source_id` is present for all 300 History groups and all 200 Development groups. The two sets do not intersect.

GSM8K `evidence_provenance.source_id` is null on all 1,000 GSM8K candidate records (600 History, 400 Development). That null is not a shared source example. The GSM8K source question IDs are the `dataset_id` values, and those do not intersect.

HotpotQA borrowed-answer rows record `donor_dataset_id` on 400 candidates. All 400 donors occur in the same unified partition as the recipient. None occur in the other unified partition. Of those 400, 113 donors are themselves selected research_v1 questions in the same partition, and 287 are same-partition unified questions that were not selected into research_v1. Borrowing does not cross History and Development.

## Context and source leakage

GSM8K has no supplied context, so it has no cross-partition paragraph overlap.

HotpotQA does. These are different question groups that reuse the same source passage. They are not duplicate questions.

| HotpotQA context check | Count |
|---|---:|
| `evidence_provenance.context_hashes` present in both partitions | 25 |
| History groups involved in those hashes | 15 |
| Development groups involved in those hashes | 15 |
| Exact original paragraph texts present in both partitions | 14 |
| Context titles present in both partitions | 14 |
| Supporting-fact `(title, sentence_id)` pairs present in both partitions | 2 |

The 14 shared paragraph titles are Warren Commission, National Liberation Army (Colombia), Beast (Magic Dirt album), Raúl Sánchez (musician), Magic Dirt, Magic Dirt (US Version), Girl (Magic Dirt album), The Dirt Bike Kid, Exeter Book, Kevin Garnett, I Love NY (2015 film), Tom Clancy, Drag Me Down, and Neo Geo Cup '98: The Road to the Victory. Each shared text belongs to one History group and one Development group.

Two of those passages are also cited as supporting facts on both sides:

| Supporting fact | History group and question | Development group and question |
|---|---|---|
| Magic Dirt, sentence 0 | `hotpotqa-q-8372a9bf768803d0`: "Which artist released more singles, Magic Dirt or Ida Maria?" | `hotpotqa-q-c623c214f6cb4f2f`: "Which band was formed first, Circus Diablo or Magic Dirt?" |
| Tom Clancy, sentence 0 | `hotpotqa-q-6a0a65d3825dbeed`: "Which writer of Against All Enemies was born April 12, 1947?" | `hotpotqa-q-bcb56e82d06d5416`: "What type of media does Locked On and Tom Clancy have in common?" |

The stored provenance hash intersection (25) is larger than the exact paragraph-text intersection (14). Both counts were measured. The 14 paragraph texts are the direct evidence of shared context. The extra provenance hashes were not reclassified.

This matters because research_v1 HotpotQA is a source/reference-context condition. A Development question can be shown a paragraph that also appears in a History question. That is shared-source leakage. It is not evidence that the same question was assigned to both partitions.

## Semantic leakage limitations

No semantic, paraphrase, entity, or near-duplicate comparison was run. Exact normalization only removes case and punctuation. Questions that use different words for the same fact can still sit in opposite partitions. The protocol already states that paraphrases, shared entities, and common evidence sources are not ruled out by the current schema. This audit does not change that limit.

Shared HotpotQA passages, especially the two shared supporting facts, are a concrete form of related-question leakage that exact question matching does not catch.

## Verdict

**Conditional pass.**

History and Development are disjoint for question groups, normalized questions, raw questions, dataset IDs, candidate IDs, HotpotQA source IDs, and HotpotQA donor IDs. GSM8K has no context to leak.

The result is not a full pass because 15 History HotpotQA groups and 15 Development HotpotQA groups share recorded context hashes, 14 paragraph texts are identical across partitions, and 2 supporting-fact identifiers are shared. Semantic leakage was not tested.

## Remediation recommendations

Do not edit research_v1 in place. Do not drop rows because of a score.

1. Before any reference-assisted HotpotQA comparison, either accept shared benchmark passages as a documented limitation or build a new dataset version that keeps only one side of each shared-paragraph pair.
2. If a pair is removed, record the group ID, the shared title, and the reason, and preserve the original record in an exclusion ledger. Prefer a rule that does not look at labels or model output. Do not use Final Test to choose the side that remains.
3. Treat the Magic Dirt and Tom Clancy pairs as the minimum set to review, because those pages are supporting facts on both sides, not only distractors.
4. Leave semantic and paraphrase leakage marked unverified unless a separate, predeclared similarity audit is run. Do not describe the current normalization as a semantic check.

## Confirmation

No dataset records, questions, candidate answers, labels, group IDs, split assignments, hashes, or manifest counts were modified. The only file written by this audit is this report.
