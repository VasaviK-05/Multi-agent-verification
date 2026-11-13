# Evidence corpus readiness

Status: `PROPOSAL_NOT_APPROVED`. The corpus is not frozen and collection is not authorized.

## Canonical resource

File `evaluation/artifacts/person1/development_evidence_corpus_v1/corpus.json`, SHA-256 `f76c6ce19661e2fdae44f87f126825d8efc4b3edb3fa1b381d0130c7f82e5e2b`, 1,844 articles, index `idx-c1dc6980912b`. The index manifest stores that corpus hash. `evaluation/scripts/evaluate_evidence_corpus.py` recomputes the corpus and index hashes and summarizes `coverage_new_corpus.jsonl`. It does not load the retriever.

## Coverage

The recorded coverage file has 185 HotpotQA questions and 187 GSM8K questions, matching the approved roster. GSM8K is not an evidence task. FEVER sentences are not in the source, so FEVER retrieval coverage is not established. Historical title checks against `articles_13083.json` found no FEVER title coverage.

The coverage file, recomputed by count only, has 184 HotpotQA rows with a supporting title retrieved and 1 retrieval miss. It also marks 20 HotpotQA questions with any retrieved chunk at cosine 0.78 or higher. The preparation report's stricter count, a supporting title that itself clears 0.78, remains 19 and is not a separate column in that file. A retrieval hit is not relevance, sufficiency, or correctness. Below-gate and missing evidence stay uncertain. No document was added to change those counts.

## Rebuild

`evaluation/data_preparation/development_evidence_corpus.py` refuses to overwrite the corpus. Rebuilding the index by instantiating `EvidenceRetriever` can rewrite `manifest.json` when the path or mtime differs. That rewrite is not part of this readiness check.

Limitations that remain on the approval package: the 0.78 gate, the one miss, unknown embedding weights, derived Wikipedia URLs, and gold-answer strings that already occur inside 177 source paragraphs.
