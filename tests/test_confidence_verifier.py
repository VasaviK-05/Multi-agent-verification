from app.verifiers.confidence_verifier import ConfidenceVerifier


def test_full_agreement():
    verifier = ConfidenceVerifier()

    result = verifier.verify(
        "What is the capital of France?",
        "Paris",
        "support,support,support,support,support",
    )

    assert result.passed is True
    assert result.score == 1.0


def test_majority_support():
    verifier = ConfidenceVerifier()

    result = verifier.verify(
        "What is the capital of France?",
        "Paris",
        "support,support,support,reject,support",
    )

    assert result.passed is True
    assert result.score == 0.8


def test_majority_reject():
    verifier = ConfidenceVerifier()

    result = verifier.verify(
        "What is the capital of France?",
        "London",
        "reject,reject,support,reject,reject",
    )

    assert result.passed is False
    assert result.score == 0.8


def test_equal_disagreement():
    verifier = ConfidenceVerifier()

    result = verifier.verify(
        "Example question",
        "Example answer",
        "support,reject",
    )

    assert result.score == 0.5


def test_no_judgments():
    verifier = ConfidenceVerifier()

    result = verifier.verify(
        "Example question",
        "Example answer",
    )

    assert result.passed is False
    assert result.score == 0.0