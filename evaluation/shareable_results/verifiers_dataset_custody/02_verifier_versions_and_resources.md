# Verifier versions, hashes, and resources

Values are taken from `evidence/verifier_config.json`, `evidence/environment_manifest.json`, and `evidence/evidence_corpus_manifest.json`. Source hashes below were recomputed from the current Python files and match the config. Model-weight hashes were not recomputed, because none is recorded.

The verifier config status is `DECLARED_PENDING_APPROVAL`. `approved` is false. There is no approver and no approval date. A matching source hash is an implementation fingerprint, not an approved release pin.

## Source hashes and model-weight hashes

| Verifier | Implementation | Source SHA-256 | Model or generator name | Weight or digest |
| --- | --- | --- | --- | --- |
| semantic | `app.verifiers.semantic_verifier.SemanticVerifier` | `c72cf7a6f34a66d16e36e360286ab6085000e1594e86dd1e124480aa43086bd8` | `all-MiniLM-L6-v2` | `UNKNOWN` |
| evidence | `app.verifiers.evidence_verifier.EvidenceVerifier` | `b76f25a8416f0c515e279feba26e1b94ad716ad50c3e4170b58d5a97c1c7755c` | NLI `cross-encoder/nli-deberta-v3-small`; embeddings `all-MiniLM-L6-v2` | `UNKNOWN` |
| rule | `app.verifiers.rule_verifier.RuleVerifier` | `bf9d212d6f179e786241559a2ce974a69dcdfa74d3d8f5c59fd8cab2c4b61715` | none | not applicable |
| confidence | `app.verifiers.confidence_verifier.ConfidenceVerifier` | `e05617149ea32f4f6136cc9ac8512296075acd285005d7d99670e4ab750ed94f` | `llama3.2:3b` | `UNKNOWN` |

The rule version hash is the same value as the rule source hash. There is no separate rule prompt.

## Semantic requirements

- Reference text is required.
- Support threshold 0.5. Reject threshold 0.3. `thresholds_calibrated` is false.
- Score meaning: cosine similarity, not factual correctness.
- Model revision beyond the name `all-MiniLM-L6-v2` is not recorded. The weight snapshot hash is `UNKNOWN`.

## Evidence resources

- Retrieval gate used by the task contract: cosine `0.78`.
- Config `min_retrieval_score` 0.45. `min_nli_score` 0.5.
- `insufficient_evidence_decision` is `UNSURE`.
- `prompt_hash` is `UNKNOWN`. The config describes the prompt identity as question text only for template claims, and says claim text is not added to the first retrieval query. No prompt file is hashed in this package.
- Chunk size: 500 words.

Corpus manifest status: `PROPOSAL_NOT_APPROVED`. `approved` is false.

| Field | Value |
| --- | --- |
| Version | `development_evidence_corpus_v1` |
| Corpus path | `evaluation/artifacts/person1/development_evidence_corpus_v1/corpus.json` |
| Corpus SHA-256 | `f76c6ce19661e2fdae44f87f126825d8efc4b3edb3fa1b381d0130c7f82e5e2b` |
| Articles | 1844 |
| Index id | `idx-c1dc6980912b` |
| Index manifest SHA-256 | `2a7ce5a45101e26c73bd4a8c3255d4c743166b24e9339f4d8f5fe983a9ab8521` |
| Chunks SHA-256 | `1d207b208905a3ce3a85c4c567ecc5cc8b24106d43964ebda046a7da51963bc7` |
| FAISS index SHA-256 | `037e4923b2c69c86b5f7fb83c8589c6b89ed7fe714d7cbb70581a7700aacb7d8` |
| Embedding model | `all-MiniLM-L6-v2` |
| Embedding-weight snapshot | `UNKNOWN` |
| Source | HotpotQA reference paragraphs for the 185 eligible Development questions. GSM8K solutions and FEVER sentences were not added. |

The index-manifest SHA-256 matches the current file `evaluation/artifacts/person1/development_evidence_corpus_v1/evidence_index/corpus/manifest.json`. That index manifest records the same corpus hash, index id, chunk size 500, and embedding model. It does not record a frozen flag.

## Confidence resources

| Field | Value |
| --- | --- |
| Generator | `llama3.2:3b` |
| Generator digest | `UNKNOWN` |
| Research-collection generator | `UNKNOWN` |
| Prompt SHA-256 | `4dbe792282a6f23c12621441fed52b72b9c94a6cd0d8fdfd015d9878a00ef9f7` |
| Samples | 5 |
| Temperature | 0.8 |
| Timeout | 60 seconds |
| Endpoint | `http://localhost:11434/api/generate` |
| Score meaning | Agreement fraction, not correctness |

The prompt hash is recorded only in `verifier_config.json`. This repository copy does not include a prompt file that reproduces it. The hash is not a claim that a prompt file was found.

## Environment

`evidence/environment_manifest.json` is `OBSERVED_NOT_APPROVED`.

Observed: Python 3.12.1, `Windows-11-10.0.26300-SP0`, sentence-transformers 6.0.1, transformers 5.17.0, torch 2.14.0, faiss-cpu 1.15.1, numpy 2.5.3.

`UNKNOWN`: hardware model, GPU, Ollama version, model-weight snapshot hashes. `code_revision_approved` is false. These package versions are an observation, not a signed freeze.
