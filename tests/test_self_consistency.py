import os
from decimal import Decimal

import pytest

from app.verifiers.confidence_verifier import ConfidenceVerifier
from app.verifiers.self_consistency import (
    NLI_TO_JUDGMENT,
    AgreementLabeler,
    JudgmentSourceError,
    OllamaSampler,
    SelfConsistencyJudge,
    extract_number,
    normalize_text,
)


class FakeSampler:
    model = "fake-model"
    temperature = 0.8

    def __init__(self, samples):
        self.samples = samples
        self.calls = []

    def __call__(self, question, n):
        self.calls.append((question, n))
        return list(self.samples)[:n]


class FakeNLI:
    """Returns a fixed label distribution keyed on the premise text."""

    def __init__(self, by_premise=None, default=("neutral", 0.9)):
        self.by_premise = by_premise or {}
        self.default = default
        self.calls = []

    def __call__(self, inputs):
        self.calls.append(inputs)
        label, score = self.default
        for needle, (needle_label, needle_score) in self.by_premise.items():
            if needle.lower() in inputs["text"].lower():
                label, score = needle_label, needle_score
                break
        rest = (1.0 - score) / 2
        return [
            {"label": label, "score": score},
            *[{"label": other, "score": rest} for other in NLI_TO_JUDGMENT if other != label],
        ]


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def test_normalize_text_drops_case_punctuation_and_articles():
    assert normalize_text("The capital is Paris.") == "capital is paris"
    assert normalize_text("  A  dog, an owl ") == "dog owl"


def test_extract_number_requires_exactly_one_number():
    assert extract_number("The answer is 4.") == Decimal("4")
    assert extract_number("1,024") == Decimal("1024")
    assert extract_number("0.30") == Decimal("0.3")
    assert extract_number("between 3 and 5") is None
    assert extract_number("Paris") is None


# ---------------------------------------------------------------------------
# labeler
# ---------------------------------------------------------------------------


def test_short_answer_string_match_does_not_call_nli():
    nli = FakeNLI()
    labeler = AgreementLabeler(nli=nli)
    row = labeler.label("Paris, France.", "What is the capital of France?", "Paris", "claim")
    assert row == {"label": "support", "method": "string_match"}
    assert nli.calls == []


def test_numeric_answers_compare_as_decimals():
    labeler = AgreementLabeler(nli=FakeNLI())
    assert labeler.label("The sum is 0.30", "q", "0.3", "c")["label"] == "support"
    assert labeler.label("It equals 5.", "q", "4", "c") == {"label": "reject", "method": "numeric"}


def test_empty_sample_is_unsure():
    labeler = AgreementLabeler(nli=FakeNLI())
    assert labeler.label("   ", "q", "Paris", "c")["label"] == "unsure"


def test_disagreeing_short_sample_goes_to_nli_with_declarative_premise():
    nli = FakeNLI(by_premise={"lyon": ("contradiction", 0.95)})
    labeler = AgreementLabeler(nli=nli)
    claim = "The capital of France is Paris."
    row = labeler.label("Lyon", "What is the capital of France?", "Paris", claim)
    assert row["label"] == "reject"
    assert row["method"] == "nli"
    assert row["premise"] == "The capital of France is Lyon."
    assert nli.calls[0] == {"text": "The capital of France is Lyon.", "text_pair": claim}


def test_long_sample_is_used_verbatim_as_premise_and_truncated():
    nli = FakeNLI(default=("entailment", 0.8))
    labeler = AgreementLabeler(nli=nli, max_premise_chars=40)
    long_sample = "William Shakespeare, the English playwright, wrote the tragedy Hamlet around 1600."
    row = labeler.label(long_sample, "Who wrote Hamlet?", "Shakespeare wrote Hamlet", "Shakespeare wrote Hamlet.")
    assert row["label"] == "support"
    assert row["premise"] == long_sample[:40]


def test_low_nli_confidence_is_unsure():
    labeler = AgreementLabeler(nli=FakeNLI(default=("contradiction", 0.4)), min_nli_score=0.5)
    row = labeler.label("Something long enough to skip matching here", "q", "a b c d e f g", "c")
    assert row["label"] == "unsure"
    assert row["nli"]["contradiction"] == pytest.approx(0.4)


# ---------------------------------------------------------------------------
# judge
# ---------------------------------------------------------------------------


def test_judge_returns_one_label_per_sample_and_records_trace():
    sampler = FakeSampler(["Paris", "Paris.", "paris, france", "Lyon", ""])
    nli = FakeNLI(by_premise={"lyon": ("contradiction", 0.97)})
    judge = SelfConsistencyJudge(sampler=sampler, labeler=AgreementLabeler(nli=nli), n_samples=5)

    labels = judge("What is the capital of France?", "Paris")

    assert labels == ["support", "support", "support", "reject", "unsure"]
    assert sampler.calls == [("What is the capital of France?", 5)]
    trace = judge.last_trace
    assert trace["n_samples"] == 5
    assert trace["claim"] == "The capital of France is Paris."
    assert trace["generator_model"] == "fake-model"
    assert [row["method"] for row in trace["samples"]] == [
        "string_match",
        "string_match",
        "string_match",
        "nli",
        "empty_sample",
    ]
    assert set(trace["latency_breakdown_ms"]) == {"sampling", "labeling"}


def test_judge_rejects_zero_samples():
    with pytest.raises(ValueError):
        SelfConsistencyJudge(sampler=FakeSampler([]), labeler=AgreementLabeler(nli=FakeNLI()), n_samples=0)


def test_confidence_verifier_end_to_end_with_fake_generator():
    sampler = FakeSampler(["Paris", "Paris", "Paris", "Lyon", "Paris"])
    nli = FakeNLI(by_premise={"lyon": ("contradiction", 0.97)})
    judge = SelfConsistencyJudge(sampler=sampler, labeler=AgreementLabeler(nli=nli), n_samples=5)
    verifier = ConfidenceVerifier(judgment_provider=judge)

    result = verifier.verify("What is the capital of France?", "Paris")

    assert result.passed is True
    assert result.metadata["decision"] == "SUPPORT"
    assert result.score == pytest.approx(0.8)
    assert result.metadata["judgment_source"] == "self_consistency"
    assert result.metadata["judgment_counts"] == {"support": 4, "reject": 1}
    assert [row["sample"] for row in result.metadata["samples"]] == sampler.samples
    assert result.metadata["generator_model"] == "fake-model"


def test_consistently_wrong_model_yields_support():
    """Agreement is stability, not truth: the verifier must report what the model says."""
    sampler = FakeSampler(["Lyon", "Lyon", "Lyon"])
    judge = SelfConsistencyJudge(sampler=sampler, labeler=AgreementLabeler(nli=FakeNLI()), n_samples=3)
    result = ConfidenceVerifier(judgment_provider=judge).verify("What is the capital of France?", "Lyon")
    assert result.passed is True
    assert result.score == 1.0
    assert "consistently wrong" in result.metadata["score_meaning"]


def test_sampler_failure_surfaces_as_abstention():
    class BrokenSampler:
        def __call__(self, question, n):
            raise JudgmentSourceError("connection refused")

    judge = SelfConsistencyJudge(sampler=BrokenSampler(), labeler=AgreementLabeler(nli=FakeNLI()))
    result = ConfidenceVerifier(judgment_provider=judge).verify("q", "a")
    assert result.passed is False
    assert result.metadata["judgments"] == []
    assert "connection refused" in result.reasoning


# ---------------------------------------------------------------------------
# Ollama sampler
# ---------------------------------------------------------------------------


def test_ollama_sampler_wraps_network_errors(monkeypatch):
    import requests

    def boom(*args, **kwargs):
        raise requests.ConnectionError("refused")

    monkeypatch.setattr(requests, "post", boom)
    sampler = OllamaSampler(url="http://127.0.0.1:1/api/generate", model="m")
    with pytest.raises(JudgmentSourceError) as excinfo:
        sampler("q", 2)
    assert "refused" in str(excinfo.value)


def test_ollama_sampler_sends_distinct_seeds_and_short_prompt(monkeypatch):
    import requests

    sent = []

    class Resp:
        def raise_for_status(self):
            return None

        def json(self):
            return {"response": " Paris \n"}

    def fake_post(url, json, timeout):
        sent.append(json)
        return Resp()

    monkeypatch.setattr(requests, "post", fake_post)
    sampler = OllamaSampler(url="http://x", model="m", temperature=0.7)
    samples = sampler("What is the capital of France?", 3)

    assert samples == ["Paris", "Paris", "Paris"]
    assert [body["options"]["seed"] for body in sent] == [0, 1, 2]
    assert all(body["options"]["temperature"] == 0.7 for body in sent)
    assert all("short, direct answer" in body["prompt"] for body in sent)
    assert all(body["stream"] is False for body in sent)


# ---------------------------------------------------------------------------
# real models (slow; the Ollama one is opt-in)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def real_labeler():
    pytest.importorskip("transformers")
    return AgreementLabeler()


def test_real_nli_separates_agreeing_and_disagreeing_regenerations(real_labeler):
    claim = "Hamlet was written by William Shakespeare."
    agree = real_labeler.label(
        "The tragedy Hamlet was written by the English playwright William Shakespeare.",
        "Who wrote Hamlet?",
        "William Shakespeare",
        claim,
    )
    disagree = real_labeler.label(
        "Hamlet was written by Charles Dickens, the Victorian novelist.",
        "Who wrote Hamlet?",
        "William Shakespeare",
        claim,
    )
    assert agree["label"] == "support"
    assert disagree["label"] == "reject"


def _ollama_available() -> bool:
    try:
        import requests

        url = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
        base = url.split("/api/")[0]
        return requests.get(f"{base}/api/tags", timeout=2).ok
    except Exception:
        return False


@pytest.mark.skipif(not _ollama_available(), reason="Ollama is not running")
def test_real_ollama_self_consistency_on_easy_fact():
    judge = SelfConsistencyJudge(n_samples=3)
    result = ConfidenceVerifier(judgment_provider=judge).verify("What is the capital of France?", "Paris")
    assert result.metadata["judgment_source"] == "self_consistency"
    assert result.metadata["total_judgments"] == 3
    assert result.metadata["decision"] in {"SUPPORT", "UNSURE", "REJECT"}
    assert len(result.metadata["samples"]) == 3
