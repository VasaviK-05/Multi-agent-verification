from app.verifiers.confidence_verifier import (
    INVALID_JUDGMENTS_REASON,
    NO_JUDGMENTS_REASON,
    ConfidenceVerifier,
    parse_judgment_list,
)


def test_full_agreement():
    verifier = ConfidenceVerifier()

    result = verifier.verify(
        "What is the capital of France?",
        "Paris",
        "support,support,support,support,support",
    )

    assert result.passed is True
    assert result.score == 1.0
    assert result.metadata["decision"] == "SUPPORT"
    assert result.metadata["judgment_source"] == "context"


def test_majority_support():
    verifier = ConfidenceVerifier()

    result = verifier.verify(
        "What is the capital of France?",
        "Paris",
        "support,support,support,reject,support",
    )

    assert result.passed is True
    assert result.score == 0.8
    assert result.metadata["judgment_counts"] == {"support": 4, "reject": 1}


def test_majority_reject():
    verifier = ConfidenceVerifier()

    result = verifier.verify(
        "What is the capital of France?",
        "London",
        "reject,reject,support,reject,reject",
    )

    assert result.passed is False
    assert result.score == 0.8
    assert result.metadata["decision"] == "REJECT"
    assert result.metadata["majority_label"] == "reject"


def test_equal_disagreement():
    verifier = ConfidenceVerifier()

    result = verifier.verify(
        "Example question",
        "Example answer",
        "support,reject",
    )

    assert result.score == 0.5
    assert result.passed is False
    assert result.metadata["majority_label"] == "tie"
    assert result.metadata["decision"] == "UNSURE"


def test_no_judgments():
    verifier = ConfidenceVerifier()

    result = verifier.verify(
        "Example question",
        "Example answer",
    )

    assert result.passed is False
    assert result.score == 0.0
    assert result.reasoning == NO_JUDGMENTS_REASON
    assert result.metadata["judgments"] == []


def test_prose_context_is_not_a_judgment_list():
    verifier = ConfidenceVerifier()

    result = verifier.verify(
        "What is the capital of France?",
        "Paris",
        "France is a country in Europe.",
    )

    assert result.passed is False
    assert result.score == 0.0
    assert result.reasoning == NO_JUDGMENTS_REASON
    assert result.metadata["judgments"] == []
    assert result.metadata["judgment_source"] == "none"


def test_invalid_labels_abstain_and_are_reported():
    verifier = ConfidenceVerifier()

    result = verifier.verify("q", "a", judgments=["support", "maybe", "Support"])

    assert result.passed is False
    assert result.score == 0.0
    assert result.reasoning == INVALID_JUDGMENTS_REASON
    assert result.metadata["majority_label"] == "invalid"
    assert result.metadata["invalid_judgments"] == ["maybe"]
    assert result.metadata["judgments"] == []


def test_invalid_label_list_in_context_is_reported_not_ignored():
    result = ConfidenceVerifier().verify("q", "a", "support,maybe")
    assert result.metadata["majority_label"] == "invalid"
    assert result.metadata["invalid_judgments"] == ["maybe"]


def test_unsure_majority_is_not_a_vote():
    result = ConfidenceVerifier().verify("q", "a", "unsure,unsure,support")
    assert result.passed is False
    assert result.metadata["majority_label"] == "unsure"
    assert result.metadata["decision"] == "UNSURE"


def test_explicit_judgments_take_priority_over_context():
    verifier = ConfidenceVerifier()
    result = verifier.verify("q", "a", "reject,reject", judgments=["support", "support", "support"])
    assert result.passed is True
    assert result.metadata["judgment_source"] == "argument"
    assert result.metadata["judgments"] == ["support", "support", "support"]


def test_provider_is_called_and_recorded():
    calls = []

    def provider(question: str, answer: str) -> list[str]:
        calls.append((question, answer))
        return ["reject", "reject", "support"]

    verifier = ConfidenceVerifier(judgment_provider=provider)
    result = verifier.verify("q", "a")

    assert calls == [("q", "a")]
    assert result.passed is False
    assert result.metadata["judgment_source"] == "provider"
    assert result.score == 2 / 3


def test_score_is_documented_as_agreement_not_accuracy():
    result = ConfidenceVerifier().verify("q", "a", "support,support")
    assert "not accuracy" in result.metadata["score_meaning"]


def test_parse_judgment_list():
    assert parse_judgment_list("support, Reject ,unsure") == ["support", "reject", "unsure"]
    assert parse_judgment_list("hello,support") is None
    assert parse_judgment_list("France is a country.") is None
    assert parse_judgment_list("") is None
    assert parse_judgment_list(None) is None
