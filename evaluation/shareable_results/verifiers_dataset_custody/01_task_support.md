# Task support

Source of the status words: `app/verifiers/task_compatibility.py`, copied by reference. The declarations are also reflected in `evidence/verifier_config.json`. This package does not change verifier behavior.

Status words:

- `VERIFIED`: the implementation decides that population for the matched case.
- `PARTIALLY_VERIFIED`: a real but limited path exists.
- `UNSUPPORTED`: a success result must not be treated as verification.
- `UNKNOWN`: the research configuration does not pin the inputs required to judge it.

Direct arithmetic is not a `research_v1` experimental population. `evaluation/docs/dataset_selection.md` and `evaluation/docs/candidate_answer_protocol.md` say there is no verified subset, annotation, or count. The rule path below is an implementation contract, not an approved dataset.

HotpotQA is not the `direct_facts` population. HotpotQA is a benchmark population. `direct_facts` is a separate contract for listed factual patterns.

## Population matrix

| Verifier | direct_arithmetic | gsm8k | direct_facts | hotpotqa | fever |
| --- | --- | --- | --- | --- | --- |
| semantic | UNSUPPORTED | PARTIALLY_VERIFIED | PARTIALLY_VERIFIED | PARTIALLY_VERIFIED | UNKNOWN |
| evidence | UNSUPPORTED | UNSUPPORTED | PARTIALLY_VERIFIED | PARTIALLY_VERIFIED | UNSUPPORTED |
| rule | VERIFIED | UNSUPPORTED | PARTIALLY_VERIFIED | UNSUPPORTED | UNSUPPORTED |
| confidence | PARTIALLY_VERIFIED | PARTIALLY_VERIFIED | UNKNOWN | UNKNOWN | UNKNOWN |

## Rule

Implementation: `app/verifiers/rule_verifier.py`. No model. The first matching regular expression selects a listed rule. An unmatched question is `unsupported`, which is an abstention, not a rejection.

Direct arithmetic is `VERIFIED` only when the matched rule name starts with `arithmetic_` and the caller labels the item `direct_arithmetic`. The check uses exact Decimal arithmetic on one explicit expression. `tests/test_research_readiness.py::test_rule_verifies_direct_arithmetic_and_refuses_word_problems` checks `What is 25 + 17?` against `42` (`passed` true, `REJECT` for `40`) and rejects a multi-step GSM8K word problem as `UNSUPPORTED`.

A GSM8K word problem that is not one explicit expression stays unsupported. If a single explicit expression is mislabeled as `gsm8k`, the arithmetic rule can still check that expression, and the contract says the GSM8K population remains unsupported. GSM8K word problems are not a direct-arithmetic subset.

Direct facts are `PARTIALLY_VERIFIED` only for listed factual patterns, including comparisons, adult status, and format questions. `tests/test_rule_verifier.py` covers factual pass and fail. The module states that this is not general factual verification. Structural format checks do not establish that an answer is the right answer.

Suitable for correctness only on a matched factual or arithmetic rule. Every other rule outcome is an abstention or a format check.

## Semantic

Implementation: `app/verifiers/semantic_verifier.py`. The score is cosine similarity, not factual correctness. Reference text is required. Empty context, missing context, and a judgment-label string are rejected. `test_semantic_requires_reference_and_is_not_correctness` covers HotpotQA with and without reference text, a judgment string on `direct_facts`, and `UNSUPPORTED` for direct arithmetic even when the context is `2 + 2 = 4`.

Thresholds in the config are support 0.5 and reject 0.3. `thresholds_calibrated` is false. A present reference produces `PARTIALLY_VERIFIED` and `score_is_correctness` false. This is a resemblance signal.

## Evidence

Implementation: `app/verifiers/evidence_verifier.py`. Retrieval coverage is not a correctness decision. Direct arithmetic, GSM8K, and FEVER are `UNSUPPORTED`. `direct_facts` and HotpotQA are `PARTIALLY_VERIFIED` only when a supporting hit is at cosine `>= 0.78`. Below that gate the contract returns `INSUFFICIENT_EVIDENCE` and `UNSURE`. A hit still has `passed` false and `score_is_correctness` false. Tests: `test_evidence_preserves_insufficient_evidence_and_refuses_fever_support`.

The canonical corpus does not by itself establish evidence verification. Corpus approval is still a proposal. See [02_verifier_versions_and_resources.md](02_verifier_versions_and_resources.md).

## Confidence

Implementation: `app/verifiers/confidence_verifier.py`. The score is an agreement fraction across generator samples. `test_confidence_is_not_correctness` requires `score_is_correctness` false. Direct arithmetic and GSM8K are `PARTIALLY_VERIFIED` only as numeric agreement. `direct_facts`, HotpotQA, and FEVER are `UNKNOWN` because no frozen generator snapshot is approved. The generator model hash is `UNKNOWN`.

Confidence is not a correctness verifier.

## Tests

`tests/test_research_readiness.py` covers the matrix, the arithmetic example, the word-problem refusal, semantic reference requirements, evidence insufficiency, and the confidence non-correctness claim. `tests/test_rule_verifier.py` covers the listed factual rules. This package did not rerun those tests.
