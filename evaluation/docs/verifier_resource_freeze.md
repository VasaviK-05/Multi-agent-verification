# Verifier and resource configuration

Status: `DECLARED_PENDING_APPROVAL`. Nothing in this note is a signed freeze.

## Canonical evidence resource

The research corpus is the file `evaluation/artifacts/person1/development_evidence_corpus_v1/corpus.json`, SHA-256 `f76c6ce19661e2fdae44f87f126825d8efc4b3edb3fa1b381d0130c7f82e5e2b`, index `idx-c1dc6980912b`. `.env` and `.env.example` point `EVIDENCE_CORPUS_PATH` at that file. If the variable is still a directory that contains `corpus.json`, `default_corpus_path()` resolves the file.

`data/evidence_corpus.json` and `data/articles_13083.json` remain historical corpora. They are not the research resource.

Do not construct `EvidenceRetriever` against the canonical corpus to refresh its manifest. A path or mtime difference rewrites `manifest.json` even when the semantic index keys match.

## What is declared

`evaluation/config/research_v1/verifier_config.json` records implementation source hashes, model names, the uncalibrated thresholds, the confidence prompt hash, and the rule list. Model-weight snapshot hashes are `UNKNOWN`. The confidence research generator is `UNKNOWN` even though the code default is `llama3.2:3b`.

`evaluation/config/research_v1/environment_manifest.json` records the Python and package versions observed while preparing this package. Hardware, GPU, and Ollama version are `UNKNOWN`. The observation is not an approved machine freeze.

## Failure groups

`structural_shared_resource_v1` does not put all four verifiers in one group. Rule is alone. Semantic and evidence share `all-MiniLM-L6-v2`. Evidence and confidence share `cross-encoder/nli-deberta-v3-small`. Confidence also depends on the generator. No paired failure recording exists, so these groups are not a measured correlation. The configuration remains `PROVISIONAL` and unapproved.

Timeouts other than the confidence default of 60 seconds are null. The resource budget and random seed are null pending approval. Failures are recorded and are not imputed.
