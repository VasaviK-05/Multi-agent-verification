# Development evidence corpus approval checklist

Status: `PROPOSAL_NOT_APPROVED`. This checklist does not freeze or approve `development_evidence_corpus_v1`. Collection is not authorized. The corpus files were not modified.

Package: `evaluation/config/experiments/experiment3_corpus_approval_package.json`.

## What the corpus is

1,844 articles were prepared from the 185 eligible HotpotQA questions. GSM8K has 187 eligible questions and does not use this factual corpus: arithmetic, no external evidence required. The working-tree corpus was restored from the Git blob and again hashes to `f76c6ce19661e2fdae44f87f126825d8efc4b3edb3fa1b381d0130c7f82e5e2b`. The restoration record is `evaluation/docs/experiment3_corpus_provenance_reconciliation.md`. This checklist does not approve or freeze the corpus. Index metadata from the preparation report: `idx-c1dc6980912b`, chunk size 500, embedding model name `all-MiniLM-L6-v2`. The weight-snapshot hash is `UNKNOWN`.

## Coverage and limits

Supporting titles are present for 185 of 185 HotpotQA questions. Retrieval from the question text returned a supporting title for 184. One miss remains: `HotpotQA:hotpot_5a84bda45542992a431d1a96`. Only 19 questions also clear cosine 0.78. Gold-answer strings of length at least 4 occur in the question's own paragraphs for 177 questions. The corpus is not leakage-free.

## Implications for Experiment 3

Evidence Verifier runs that use this corpus must record this version and index. A retrieval miss and the 0.78 gap mean missing evidence is an outcome, not a reason to retune the index on Development labels. GSM8K evidence calls are not answered by these articles. The existing 13,083-article and 500-article corpora do not contain the supporting-title sets and were not replaced.

## Research-lead checklist

| Item | State |
|---|---|
| Corpus identity and hash | Restored. Working-tree SHA-256 matches the preparation record. Not approved. |
| Index identity | Recorded; weight snapshot `UNKNOWN` |
| Retrieval miss disposition | Unresolved |
| Gold-string overlap | Disclosed, not cleared |
| Freeze | Not approved |
| Use in collection | Not authorized |

Approval requires a later record with an approver and a date. This file is not that record.
