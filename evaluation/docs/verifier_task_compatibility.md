# Verifier task compatibility

Status: declared by `app/verifiers/task_compatibility.py` and `evaluation/config/research_v1/verifier_config.json`. This declaration is not a research-lead approval. A verifier that returns a score has not thereby verified the answer.

| Verifier | Direct arithmetic | GSM8K | Direct facts | HotpotQA | FEVER |
|---|---|---|---|---|---|
| Semantic | UNSUPPORTED | PARTIALLY VERIFIED | PARTIALLY VERIFIED | PARTIALLY VERIFIED | UNKNOWN |
| Evidence | UNSUPPORTED | UNSUPPORTED | PARTIALLY VERIFIED | PARTIALLY VERIFIED | UNSUPPORTED |
| Rule | VERIFIED | UNSUPPORTED | PARTIALLY VERIFIED | UNSUPPORTED | UNSUPPORTED |
| Confidence | PARTIALLY VERIFIED | PARTIALLY VERIFIED | UNKNOWN | UNKNOWN | UNKNOWN |

## Contracts

Rule verification checks one explicit arithmetic expression with exact decimal arithmetic. `What is 25 + 17?` can be verified. A GSM8K word problem that is not that single expression returns `UNSUPPORTED`, decision `UNSURE`, and `passed` false. A plausible number is not treated as verified. Direct facts are limited to the listed patterns, such as the adult-status rule. HotpotQA and FEVER have no rule.

Semantic verification abstains without reference text. Judgment labels in `context` are not a reference. Cosine similarity is resemblance, not factual correctness. Thresholds 0.5 and 0.3 are uncalibrated. Arithmetic correctness is outside this verifier.

Evidence verification uses the canonical corpus file named in `evaluation/config/research_v1/resource_config.json`. GSM8K solutions and FEVER sentences were not added, so those populations are unsupported. A HotpotQA retrieval hit at cosine 0.78 is a coverage event, not a correctness verdict. Missing or below-gate evidence stays `UNSURE`. No supporting document is fabricated.

Confidence counts agreement among `support`, `reject`, and `unsure` judgments. The default generator is `llama3.2:3b` with five samples, temperature 0.8, and a 60-second timeout. The research collection record still leaves the generator snapshot `UNKNOWN`. Agreement is not correctness.

Unsupported populations are downgraded by `enforce_task_support` so a `SUPPORT` flag cannot survive.
