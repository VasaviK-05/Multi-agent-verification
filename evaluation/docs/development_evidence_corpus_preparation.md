# Development evidence corpus preparation

Status: `PROPOSAL_NOT_APPROVED`. This corpus is a Development coverage resource for the approved exploratory roster. It is not frozen, not a confirmatory result, and not a Final Test corpus. Collection and verifier-attempt recording remain unauthorized. Final Test labels were not opened.

Corpus version: `development_evidence_corpus_v1`

Directory: `evaluation/artifacts/person1/development_evidence_corpus_v1/`

## 1. Existing corpus assessment

Both documented corpora are present on disk and match the hashes already recorded in the research inventory. They were not modified.

| Corpus | Path | Articles | SHA-256 | Index | Status |
|---|---|---:|---|---|---|
| Baseline configured corpus | `data/articles_13083.json` | 13,083 | `b26539d013201a0435884098ae8bd3544342d0a815964bf104b9524808e9bfa8` | `data/evidence_index/articles_13083/`, `idx-6d28c9c49dac`, chunk size 500, `all-MiniLM-L6-v2` | `ORIGINAL_VERIFIED_IN_PLACE` |
| Retriever code default | `data/evidence_corpus.json` | 500 | `668b48aa59c758d6e5d082f9d07b9c544730c545ae3af36728e68a0144ec6ec5` | `data/evidence_index/evidence_corpus/`, `idx-9c87422f0357`, chunk size 500, `all-MiniLM-L6-v2` | `ORIGINAL_VERIFIED_IN_PLACE` |

The files are gitignored. Git history does not contain `data/articles_13083.json`. The working-tree bytes match the documented hash, so the file was verified in place rather than reconstructed.

Against the 185 eligible HotpotQA Development questions, supporting-fact titles were compared after lowercasing and removing non-alphanumeric characters:

| Existing corpus | Questions with at least one supporting title | Questions with every supporting title |
|---|---:|---:|
| `articles_13083.json` | 2 | 0 |
| `evidence_corpus.json` | 0 | 0 |

Read-only FAISS search, question text only, top 5, same embedding model as the saved indexes:

| Existing corpus | Supporting title returned in the retrieved set | Any retrieved chunk with cosine ≥ 0.78 |
|---|---:|---:|
| `articles_13083` | 1 / 185 | 0 / 185 |
| `evidence_corpus` (500) | 0 / 185 | 0 / 185 |

The existing corpora do not cover the eligible HotpotQA questions. GSM8K does not use this factual corpus. The Evidence Verifier's code default remains `data/evidence_corpus.json` unless `EVIDENCE_CORPUS_PATH` is set. `research_v1` still binds neither corpus.

## 2. Development question coverage analysis

Roster: `research_v1_exploratory_eligibility_approved_v1`. Eligible questions: 372 (one per eligible group).

| Benchmark | Eligible questions | External factual evidence | Result |
|---|---:|---|---|
| GSM8K | 187 | Not required. These are arithmetic word problems. Worked solutions were not added to the corpus. | `not_applicable_arithmetic_no_external_evidence_required` |
| HotpotQA | 185 | Supporting-fact titles in the benchmark reference paragraphs | All 185 have every supporting title in the new corpus. Retrieval returned a supporting title for 184. |

Coverage here means the reference paragraph is present or retrieved. It is not a judgment of answer correctness or verifier accuracy.

## 3. Corpus expansion decision

The 13,083-article and 500-article corpora were left unchanged. A new corpus was built because those corpora contain the supporting titles for 2 and 0 of the 185 eligible HotpotQA questions.

Included text is the benchmark-supplied reference paragraph (`title` and `text` on `evidence_context`) for each eligible HotpotQA Development question. Distractor paragraphs are included because they are part of that supplied context. They were not selected with candidate answers or labels. GSM8K solution text was excluded so a worked answer would not be written into the factual corpus. Paragraphs whose hash matched a History paragraph were to be excluded; the eligible set produced 0 such paragraphs.

The new corpus therefore has title coverage by inclusion of those paragraphs. Retrieval is still a separate test: the query is the question alone, and a supporting title has to come back from the index.

## 4. Source provenance and inclusion rules

| Field | Recorded value |
|---|---|
| HotpotQA release | `hotpotqa/hotpot_qa distractor@1908d6afbbead072334abe2965f91bd2709910ab` |
| Article URL | Derived from the paragraph title as an English Wikipedia URL. Status: `DERIVED_FROM_TITLE_NOT_FETCHED` |
| Publication date | `UNKNOWN` |
| Web retrieval date | none |
| Article id | `hotpot-para-` plus the first 16 hex characters of SHA-256 of `title + NUL + text` |
| Provenance ledger | `source_provenance.jsonl` |

Inclusion ledger counts: 1,844 unique articles and 1,850 paragraph-to-question rows (1,480 distractor rows, 370 supporting-fact-title rows). Six paragraphs are shared by more than one eligible question, which is why 1,850 rows collapse to 1,844 articles.

Corpus article fields are only `id`, `title`, `text`, and `url`. Candidate answers, gold answers, and labels are not fields.

## 5. Retrieval coverage results

Retriever: `EvidenceRetriever`, chunk size 500, embedding model name `all-MiniLM-L6-v2`. The model-weight snapshot hash is `UNKNOWN`; this run did not hash the Hugging Face cache. Query: question text only. Top k: 5. The retriever also appends lexical hits, so a row can contain more than five chunks. A title hit means a retrieved chunk title matches a supporting-fact title. Cosine ≥ 0.78 is the gate described in `app/verifiers/evidence_verifier.py`. That gate was not changed after seeing these results.

New corpus, 185 HotpotQA questions:

| Outcome | Questions |
|---|---:|
| Every supporting title present in the corpus | 185 |
| Supporting title returned by retrieval | 184 |
| Supporting title returned and at least one such hit has cosine ≥ 0.78 | 19 |
| Supporting title returned, all such hits below 0.78 | 165 |
| No supporting title in the retrieved set | 1 |
| Any retrieved chunk at cosine ≥ 0.78 | 20 |

Among the 184 title hits, the best supporting-title cosine has minimum 0.276, median 0.650, and maximum 0.930.

GSM8K: 187 questions were queried against the same index. Every row is `not_applicable_arithmetic_no_external_evidence_required`. None had a chunk at cosine ≥ 0.78.

## 6. Benchmark-wise coverage

| Benchmark | Questions | Corpus presence of required external evidence | Retrieval of that evidence |
|---|---:|---|---|
| HotpotQA | 185 | 185 / 185 supporting-title sets present | 184 / 185 supporting titles retrieved; 19 / 185 also clear cosine 0.78 |
| GSM8K | 187 | Not applicable | Not an evidence-retrieval success rate |

Source-wise, every new article comes from HotpotQA benchmark reference paragraphs. No second publisher was fetched. The two pre-existing corpora, reported above, are separate sources and do not supply the supporting-title sets.

## 7. Leakage and contamination audit

This audit does not support a leakage-free claim.

- History paragraph-hash overlap with the included eligible paragraphs: 0. No History-overlapping paragraph was kept.
- Final Test questions, labels, and evidence were not read and were not used to choose articles or retrieval settings.
- Corpus JSON keys do not include `candidate_answer`, `gold_answer`, or label fields.
- Gold-answer strings of length at least 4 occur inside the question's own reference paragraphs for 177 of 185 HotpotQA questions. Eight gold answers are shorter than 4 characters and were not counted. This is the benchmark paragraph containing the answer string. The answer field was not copied in.
- Candidate-answer strings of length at least 4 produced 0 substring hits in the question's own paragraphs. 185 candidate strings are shorter than 4 characters and were not treated as hits.
- Correct and synthetic-incorrect candidates of a question share one retrieval query, the question text, and one corpus. Retrieval was not run separately per candidate answer.
- One eligible question remains a retrieval miss: `HotpotQA:hotpot_5a84bda45542992a431d1a96` (`hotpotqa-q-86641bb3de923331`). Its supporting titles, `The Absent-Minded Professor` and `Fred MacMurray`, are in the corpus. The retrieved titles were other articles. Maximum cosine was 0.473. The miss was left in place.
- Semantic equivalence between a retrieved distractor and a supporting page was not adjudicated. Title match is the coverage rule used here.

## 8. Corpus and index version and hashes

| File | SHA-256 |
|---|---|
| `corpus.json` | `f76c6ce19661e2fdae44f87f126825d8efc4b3edb3fa1b381d0130c7f82e5e2b` |
| `source_manifest.json` | `72bbcf728e68bf185e1208937f1705e91885241af221acd0d8586b01068a8b85` |
| `source_provenance.jsonl` | `397f23a0519ba3bda0800cf7891c721747b50634ca041afec41391048e3c20bb` |
| `coverage_new_corpus.jsonl` | `f467dd6d16864a0e0fcfda6d14d692b995fbf246e17772616fa9db8224a65221` |
| `coverage_articles_13083.jsonl` | `2952371fba18853e6ce8cbfa68811c687991436e4ce4156b0f6b1c961501b25d` |
| `coverage_evidence_corpus_500.jsonl` | `c953ad686dbd0f0432ef157940bad3f776488c1f6021657b3e7e8f7ba36331a1` |
| `leakage_audit.json` | `fa7a77736cd6e6d64514b2b3bc5a855dfc056a1e5cdf3e6db20348e5f1812585` |
| `evidence_index/corpus/manifest.json` | `2a7ce5a45101e26c73bd4a8c3255d4c743166b24e9339f4d8f5fe983a9ab8521` |
| `evidence_index/corpus/chunks.json` | `1d207b208905a3ce3a85c4c567ecc5cc8b24106d43964ebda046a7da51963bc7` |
| `evidence_index/corpus/faiss.index` | `037e4923b2c69c86b5f7fb83c8589c6b89ed7fe714d7cbb70581a7700aacb7d8` |

Index version: `idx-c1dc6980912b`. Chunk size: 500. Embedding model name: `all-MiniLM-L6-v2`.

## 9. Evidence Verifier compatibility

`EvidenceRetriever` built and loaded this corpus. The saved index matches the corpus hash, chunk size, and model name. A later run can reuse that index only when those three still match.

Both candidates of a question use this same frozen file pair. The query does not contain the candidate answer. The verifier's 0.78 cosine gate leaves 166 of 185 HotpotQA questions without a supporting-title chunk above the gate (165 title hits below the gate, plus the one miss). Compatibility of the file format is shown. Compatibility with the verifier's relevance gate is not shown for most questions.

No official verifier attempts were recorded.

## 10. Missing evidence and unresolved issues

- One HotpotQA question is unresolved for retrieval: `HotpotQA:hotpot_5a84bda45542992a431d1a96`.
- 165 questions retrieve a supporting title below the verifier's 0.78 gate. Whether those chunks would pass the verifier's later topic gate was not run.
- Wikipedia URLs were not fetched. Publication dates are `UNKNOWN`.
- The embedding-model weight snapshot hash is `UNKNOWN`.
- GSM8K has no external evidence corpus. Arithmetic coverage is outside this artifact.
- Gold-answer strings remain inside the source paragraphs for 177 questions.
- The 13,083-article corpus still lacks the supporting-title sets. It was not expanded in place.
- No execution-source custody ZIP and no reviewed collection-adapter configuration were recovered. See `historical_evidence_recovery_v1.md`.

## 11. Corpus freeze recommendation

Do not freeze this corpus yet. The proposal status is `PROPOSAL_NOT_APPROVED`, approver null, `collection_authorized: false`, `final_test_authorized: false`.

A later approval would need a named approver and date, a decision on the 0.78 gate versus title coverage, a disposition of the one retrieval miss, and a pinned embedding-snapshot hash. Approval of this corpus would still not authorize verifier collection, policy fitting, or Final Test access.
