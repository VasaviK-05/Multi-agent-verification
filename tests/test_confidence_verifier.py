from app.verifiers.confidence_verifier import (
    AUTO,
    INVALID_JUDGMENTS_REASON,
    NO_JUDGMENTS_REASON,
    PROVIDER_UNAVAILABLE_SOURCE,
    ConfidenceVerifier,
    parse_judgment_list,
)
from app.verifiers.self_consistency import JudgmentSourceError, SelfConsistencyJudge


class RecordingProvider:
    """Provider that records calls and optionally raises."""

    source_name = "fake_provider"

    def __init__(self, judgments=None, error=None):
        self.judgments = judgments or []
        self.error = error
        self.calls = []
        self.last_trace = {"n_samples": len(self.judgments), "samples": []}

    def __call__(self, question, answer):
        self.calls.append((question, answer))
        if self.error is not None:
            raise self.error
        return list(self.judgments)


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


def test_no_judgments_without_provider():
    verifier = ConfidenceVerifier(judgment_provider=None)

    result = verifier.verify(
        "Example question",
        "Example answer",
    )

    assert result.passed is False
    assert result.score == 0.0
    assert result.reasoning == NO_JUDGMENTS_REASON
    assert result.metadata["judgments"] == []
    assert result.metadata["judgment_source"] == "none"


def test_prose_context_is_not_a_judgment_list():
    verifier = ConfidenceVerifier(judgment_provider=None)

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


def test_prose_context_falls_through_to_provider():
    provider = RecordingProvider(["support", "support", "reject"])
    verifier = ConfidenceVerifier(judgment_provider=provider)

    result = verifier.verify(
        "What is the capital of France?",
        "Paris",
        "France is a country in Europe.",
    )

    assert provider.calls == [("What is the capital of France?", "Paris")]
    assert result.passed is True
    assert result.metadata["judgment_source"] == "fake_provider"
    assert result.metadata["n_samples"] == 3  # provider trace merged into metadata


def test_label_list_context_short_circuits_provider():
    provider = RecordingProvider(["reject", "reject", "reject"])
    verifier = ConfidenceVerifier(judgment_provider=provider)

    result = verifier.verify("q", "a", "support,support")

    assert provider.calls == []
    assert result.passed is True
    assert result.metadata["judgment_source"] == "context"


def test_provider_failure_abstains_with_hook_compatible_reasoning():
    provider = RecordingProvider(error=JudgmentSourceError("llama3.2:3b at http://localhost: refused"))
    verifier = ConfidenceVerifier(judgment_provider=provider)

    result = verifier.verify("q", "a")

    assert result.passed is False
    assert result.score == 0.0
    assert result.metadata["decision"] == "UNSURE"
    assert result.metadata["judgments"] == []  # decision-layer abstention hook
    assert result.reasoning.startswith(NO_JUDGMENTS_REASON)
    assert "refused" in result.reasoning
    assert result.metadata["judgment_source"] == PROVIDER_UNAVAILABLE_SOURCE
    assert result.metadata["error"].startswith("JudgmentSourceError")


def test_default_constructor_uses_self_consistency_judge_lazily():
    verifier = ConfidenceVerifier()
    assert verifier._provider_arg is AUTO
    assert verifier._provider is None  # nothing built until first use
    assert isinstance(verifier.judgment_provider, SelfConsistencyJudge)


def test_provider_returning_empty_list_abstains():
    verifier = ConfidenceVerifier(judgment_provider=RecordingProvider([]))
    result = verifier.verify("q", "a")
    assert result.passed is False
    assert result.reasoning == NO_JUDGMENTS_REASON
    assert result.metadata["judgments"] == []
    assert result.metadata["judgment_source"] == "fake_provider"


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
