"""Semantic verifier contract tests that run without a real embedding model."""

import numpy as np
import pytest

from app.models.schemas import VerificationResult
from app.verifiers.semantic_verifier import (
    JUDGMENT_CONTEXT_REASON,
    NO_CONTEXT_REASON,
    SemanticVerifier,
)


class FakeModel:
    """Returns fixed vectors so cosine similarity is controlled by the test."""

    def __init__(self, vectors: dict[str, list[float]]) -> None:
        self.vectors = vectors
        self.calls: list[list[str]] = []

    def encode(self, texts, **kwargs):
        self.calls.append(list(texts))
        return np.array([self.vectors[text] for text in texts], dtype=np.float32)


def _verifier(similarity_vectors: dict[str, list[float]], mode: str = "answer") -> SemanticVerifier:
    return SemanticVerifier(comparison_mode=mode, model=FakeModel(similarity_vectors))


def test_negative_similarity_is_clipped_and_raw_is_kept():
    verifier = _verifier({"opposite": [1.0, 0.0], "reference": [-1.0, 0.0]})

    result = verifier.verify("q", "opposite", "reference")

    assert isinstance(result, VerificationResult)
    assert result.score == 0.0
    assert result.metadata["raw_similarity"] == pytest.approx(-1.0)
    assert result.passed is False
    assert result.metadata["decision"] == "REJECT"
    assert "not a probability" in result.metadata["score_meaning"]


def test_three_way_decision_bands():
    cases = {
        "high": ([1.0, 0.0], "SUPPORT", True),
        "middle": ([0.4, np.sqrt(1 - 0.4**2)], "UNSURE", False),
        "low": ([0.1, np.sqrt(1 - 0.1**2)], "REJECT", False),
    }
    vectors = {"reference": [1.0, 0.0]}
    vectors.update({name: list(vec) for name, (vec, _, _) in cases.items()})
    verifier = _verifier(vectors)

    for name, (_, decision, passed) in cases.items():
        result = verifier.verify("q", name, "reference")
        assert result.metadata["decision"] == decision, name
        assert result.passed is passed, name
        assert result.metadata["support_threshold"] == SemanticVerifier.SUPPORT_THRESHOLD
        assert result.metadata["reject_threshold"] == SemanticVerifier.REJECT_THRESHOLD
        assert result.metadata["thresholds_calibrated"] is False


def test_low_similarity_reasoning_does_not_claim_falsity():
    verifier = _verifier({"low": [0.0, 1.0], "reference": [1.0, 0.0]})
    result = verifier.verify("q", "low", "reference")
    assert "not evidence of falsity" in result.reasoning


def test_both_texts_are_encoded_in_one_call():
    model = FakeModel({"a": [1.0, 0.0], "ref": [1.0, 0.0]})
    verifier = SemanticVerifier(comparison_mode="answer", model=model)
    verifier.verify("q", "a", "ref")
    assert model.calls == [["a", "ref"]]


def test_comparison_modes_change_the_compared_text():
    question, answer = "What is the capital of France?", "Paris"
    expected = {
        "question_answer": "What is the capital of France? Paris",
        "answer": "Paris",
        "claim": "The capital of France is Paris.",
    }
    for mode, text in expected.items():
        verifier = SemanticVerifier(comparison_mode=mode, model=FakeModel({text: [1.0], "ref": [1.0]}))
        result = verifier.verify(question, answer, "ref")
        assert result.metadata["compared_text"] == text
        assert result.metadata["comparison_method"] == f"{mode}_vs_context"


def test_unknown_comparison_mode_is_rejected():
    with pytest.raises(ValueError):
        SemanticVerifier(comparison_mode="nonsense", model=FakeModel({}))


def test_missing_context_abstains_with_the_contract_sentence():
    verifier = _verifier({})
    for context in (None, "", "   "):
        result = verifier.verify("q", "a", context)
        assert result.reasoning == NO_CONTEXT_REASON
        assert result.score == 0.0
        assert result.passed is False
        assert result.metadata["decision"] == "UNSURE"
        assert result.metadata["abstain_reason"] == "no_context"


def test_judgment_list_in_context_is_not_used_as_reference():
    model = FakeModel({})
    verifier = SemanticVerifier(comparison_mode="answer", model=model)

    result = verifier.verify("q", "a", "support,support,reject")

    assert result.reasoning == JUDGMENT_CONTEXT_REASON
    assert "No reference context" in result.reasoning
    assert result.metadata["abstain_reason"] == "context_was_judgment_list"
    assert model.calls == []
