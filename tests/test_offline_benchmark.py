"""Offline benchmark accounting. These tests use stubs, not a published score."""

import json

from app.analysis.question_analyzer import QuestionAnalysis, QuestionAnalyzer
from app.benchmark.offline_benchmark import (
    LabeledExample,
    examples_from_records,
    load_labeled_jsonl,
    main,
    run_benchmark,
)
from app.models.schemas import VerificationResult
from app.verifiers.base_verifier import BaseVerifier


class StubVerifier(BaseVerifier):
    def __init__(self, name: str, passed: bool = True, score: float = 0.5) -> None:
        self._name = name
        self.passed = passed
        self.score = score

    @property
    def name(self) -> str:
        return self._name

    def verify(
        self,
        question: str,
        answer: str,
        context: str | None = None,
    ) -> VerificationResult:
        return VerificationResult(
            verifier_name=self._name,
            score=self.score,
            passed=self.passed,
            reasoning="stub",
        )


def _stubs(score: float) -> list[StubVerifier]:
    return [
        StubVerifier(name, passed=True, score=score)
        for name in ("semantic", "evidence", "rule", "confidence")
    ]


class FixedAnalyzer(QuestionAnalyzer):
    def __init__(self, analysis: QuestionAnalysis) -> None:
        self.analysis = analysis

    def analyze(self, question: str) -> QuestionAnalysis:
        return self.analysis


def _assert_accounting(report) -> None:
    for item in report.methods:
        assert item.n_covered + item.n_abstentions == item.n_examples
        assert item.n_correct + item.n_incorrect == item.n_covered
        if item.n_covered == 0:
            assert item.accuracy is None
        else:
            assert item.accuracy == item.n_correct / item.n_covered
        if item.n_examples == 0:
            assert item.coverage is None
        else:
            assert item.coverage == item.n_covered / item.n_examples


def test_empty_input_does_not_invent_rates():
    report = run_benchmark([], verifiers=_stubs(0.5))
    _assert_accounting(report)
    for name in ("adaptive", "majority", "all_verifiers"):
        item = report.method(name)
        assert item.n_examples == 0
        assert item.accuracy is None
        assert item.coverage is None
        assert item.verifier_calls == 0
        assert item.latency_ms_total == 0.0
        assert item.mean_latency_ms is None
    payload = report.to_dict()
    assert "winner" not in payload
    blob = json.dumps(payload).lower()
    for banned in ("novel", "patent", "state-of-the-art"):
        assert banned not in blob


def test_early_stop_calls_fewer_verifiers_than_the_baselines():
    example = LabeledExample("q", "a", answer_is_correct=False)
    report = run_benchmark(
        [example],
        verifiers=_stubs(0.95),
        analyzer=FixedAnalyzer(QuestionAnalysis("medical", "easy", 0.34)),
        update_reputation=True,
    )
    _assert_accounting(report)
    adaptive = report.method("adaptive")
    majority = report.method("majority")
    full = report.method("all_verifiers")
    assert adaptive.verifier_calls == 2
    assert majority.verifier_calls == 4
    assert full.verifier_calls == 4
    assert adaptive.reputation_updates == 2
    assert majority.reputation_updates == 0
    assert full.reputation_updates == 4
    assert adaptive.n_incorrect == 1
    assert adaptive.accuracy == 0.0
    assert report.adaptive_reputation.get_reputation("rule", "medical") < 0.5
    assert report.adaptive_reputation.observation_count("semantic", "medical") == 1
    assert report.adaptive_reputation.is_cold_start("rule", "general")
    assert not report.all_verifiers_reputation.is_cold_start("semantic", "medical")
    assert report.adaptive_reputation is not report.all_verifiers_reputation
    assert adaptive.latency_ms_total >= 0.0
    assert isinstance(adaptive.mean_latency_ms, float)


def test_neutral_votes_abstain_and_majority_does_not():
    report = run_benchmark(
        [LabeledExample("q", "a", True)],
        verifiers=_stubs(0.5),
        analyzer=FixedAnalyzer(QuestionAnalysis("general", "easy", 0.1)),
        update_reputation=False,
    )
    _assert_accounting(report)
    adaptive = report.method("adaptive")
    majority = report.method("majority")
    full = report.method("all_verifiers")
    assert adaptive.verifier_calls == 4
    assert adaptive.n_abstentions == 1
    assert adaptive.accuracy is None
    assert adaptive.coverage == 0.0
    assert majority.n_correct == 1
    assert majority.accuracy == 1.0
    assert majority.coverage == 1.0
    assert full.n_abstentions == 1
    assert full.accuracy is None
    assert report.adaptive_reputation.is_cold_start("rule", "general")
    assert adaptive.reputation_updates == 0


def test_measured_latency_is_not_the_cost_table(monkeypatch):
    from itertools import count

    ticks = count()
    monkeypatch.setattr("app.benchmark.offline_benchmark.time.perf_counter",
                        lambda: next(ticks) * 0.125)
    profiles = {
        name: {"cost": 0.0, "latency": (index + 1) / 4}
        for index, name in enumerate(("semantic", "evidence", "rule", "confidence"))
    }
    report = run_benchmark(
        [LabeledExample("q", "a", True)],
        verifiers=_stubs(0.95),
        analyzer=FixedAnalyzer(QuestionAnalysis("general", "easy", 0.1)),
        verifier_profiles=profiles,
        update_reputation=False,
    )
    assert report.method("all_verifiers").latency_ms_total < 10_000
    assert report.method("adaptive").latency_ms_total < 10_000
    # Every timed stub takes 125 ms, regardless of its normalized estimate.
    assert report.method("adaptive").mean_latency_ms == 125.0
    assert report.method("all_verifiers").mean_latency_ms == 125.0
    assert report.method("adaptive").verifier_calls < report.method("all_verifiers").verifier_calls


def test_real_analyzer_still_selects_a_subset():
    from app.verifiers.rule_verifier import RuleVerifier

    report = run_benchmark(
        [LabeledExample("What is 2 + 2?", "4", True)],
        verifiers=[RuleVerifier(), StubVerifier("semantic", score=0.95),
                   StubVerifier("evidence", score=0.95), StubVerifier("confidence", score=0.95)],
        update_reputation=False,
    )
    assert report.method("adaptive").verifier_calls < report.method("all_verifiers").verifier_calls
    assert report.method("all_verifiers").verifier_calls == 4


def test_records_require_one_boolean_label():
    examples = examples_from_records(
        [{"question": "q", "answer": "a", "label": False, "context": "c"}]
    )
    assert examples[0].answer_is_correct is False
    assert examples[0].context == "c"
    try:
        examples_from_records([{"question": "q", "answer": "a", "answer_is_correct": "passed"}])
        raised = False
    except TypeError:
        raised = True
    assert raised
    try:
        examples_from_records(
            [{"question": "q", "answer": "a", "label": True, "answer_is_correct": True}]
        )
        raised = False
    except ValueError:
        raised = True
    assert raised


def test_jsonl_loader_skips_blank_lines(tmp_path):
    path = tmp_path / "labels.jsonl"
    path.write_text(
        '\n{"question": "q", "answer": "a", "answer_is_correct": true}\n\n',
        encoding="utf-8",
    )
    loaded = load_labeled_jsonl(path)
    assert len(loaded) == 1
    assert loaded[0].answer_is_correct is True
    report = run_benchmark(
        loaded,
        verifiers=_stubs(0.5),
        analyzer=FixedAnalyzer(QuestionAnalysis("general", "easy", 0.1)),
        update_reputation=False,
    )
    assert report.method("majority").n_correct == 1


def test_all_verifiers_skip_abstentions_and_learn_after_the_prediction():
    class AbstainingEvidence(StubVerifier):
        def __init__(self) -> None:
            super().__init__("evidence", passed=False, score=0.0)

        def verify(self, question: str, answer: str, context: str | None = None) -> VerificationResult:
            return VerificationResult(
                verifier_name="evidence",
                score=0.0,
                passed=False,
                reasoning="No evidence was retrieved.",
            )

    verifiers = [
        StubVerifier("semantic", passed=True, score=0.95),
        AbstainingEvidence(),
        StubVerifier("rule", passed=True, score=0.95),
        StubVerifier("confidence", passed=True, score=0.95),
    ]
    report = run_benchmark(
        [LabeledExample("q", "a", False), LabeledExample("q2", "a2", False)],
        verifiers=verifiers,
        analyzer=FixedAnalyzer(QuestionAnalysis("medical", "easy", 0.0)),
        update_reputation=True,
    )
    full = report.method("all_verifiers")
    assert full.reputation_updates == 6
    assert report.all_verifiers_reputation.is_cold_start("evidence", "medical")
    assert report.all_verifiers_reputation.observation_count("semantic", "medical") == 2
    assert report.adaptive_reputation is not report.all_verifiers_reputation
    assert report.adaptive_reputation.observation_count("evidence", "medical") == 0


def test_cli_requires_a_dataset():
    try:
        main([])
        raised = False
    except SystemExit:
        raised = True
    assert raised
