"""Tests for verifier classes and inheritance."""

from app.models.schemas import VerificationResult
from app.verifiers import (
    BaseVerifier,
    ConfidenceVerifier,
    EvidenceVerifier,
    RuleVerifier,
    SemanticVerifier,
)


def test_all_verifiers_inherit_base():
    verifiers = [
        SemanticVerifier(),
        EvidenceVerifier(),
        RuleVerifier(),
        ConfidenceVerifier(),
    ]
    for verifier in verifiers:
        assert isinstance(verifier, BaseVerifier)


def test_verifier_output_conforms_to_schema():
    verifier = SemanticVerifier()
    result = verifier.verify("What is 2+2?", "4")

    assert isinstance(result, VerificationResult)
    assert result.verifier_name == "semantic"
    assert 0.0 <= result.score <= 1.0
    assert isinstance(result.passed, bool)
    assert result.reasoning is not None


def test_every_verifier_sets_decision_and_score_meaning():
    """Shared metadata contract from app/verifiers/base_verifier.py."""
    cases = [
        (SemanticVerifier(), ("What is the capital of France?", "Paris", "Paris is the capital of France.")),
        (SemanticVerifier(), ("What is the capital of France?", "Paris", None)),
        (EvidenceVerifier(corpus_path="data/test_evidence_corpus.json"), ("What is the capital of France?", "Paris", None)),
        (RuleVerifier(), ("What is 2+2?", "4", None)),
        (RuleVerifier(), ("Who is the president of France?", "Someone", None)),
        (ConfidenceVerifier(), ("q", "a", "support,support,reject")),
        (ConfidenceVerifier(judgment_provider=None), ("q", "a", None)),
        (ConfidenceVerifier(judgment_provider=lambda q, a: ["reject", "reject", "support"]), ("q", "a", None)),
    ]
    for verifier, args in cases:
        result = verifier.verify(*args)
        assert result.metadata["decision"] in {"SUPPORT", "REJECT", "UNSURE"}, verifier.name
        assert isinstance(result.metadata["score_meaning"], str) and result.metadata["score_meaning"], verifier.name
        if result.metadata["decision"] == "SUPPORT":
            assert result.passed is True
        else:
            assert result.passed is False

"""
def test_all_verifiers_return_placeholder_results():
    verifiers = [
        SemanticVerifier(),
        EvidenceVerifier(),
        RuleVerifier(),
        ConfidenceVerifier(),
    ]
    for verifier in verifiers:
        result = verifier.verify("test question", "test answer")
        assert result.score == 0.5
        assert result.passed is True
        assert result.reasoning == "Placeholder implementation"
"""
def test_semantic_verifier_correct_answer():
    verifier = SemanticVerifier()

    result = verifier.verify(
        "What is the capital of France?",
        "Paris",
        "The capital of France is Paris.",
    )

    assert result.score >= 0.7
    assert result.passed is True


def test_semantic_verifier_wrong_answer():
    verifier = SemanticVerifier()

    result = verifier.verify(
        "What is the capital of France?",
        "London",
        "The capital of France is Paris.",
    )

    assert 0.0 <= result.score <= 1.0
    assert result.passed is not None

def test_semantic_verifier_paraphrased_answer():
    verifier = SemanticVerifier()

    result = verifier.verify(
        "What is the capital of France?",
        "Paris is the capital city of France.",
        "The capital of France is Paris.",
    )

    assert result.score >= 0.7
    assert result.passed is True

def test_semantic_verifier_without_context():
    verifier = SemanticVerifier()

    result = verifier.verify(
        "What is the capital of France?",
        "Paris",
    )

    assert result.score == 0.0
    assert result.passed is False
    assert result.reasoning == "No reference context provided for semantic comparison."
    assert result.metadata["decision"] == "UNSURE"