"""Isolated tests for AdaptiveEarlyTermination."""

from app.analysis.question_analyzer import QuestionAnalysis
from app.decision.early_termination import AdaptiveEarlyTermination
from app.models.schemas import VerificationResult


def _result(passed: bool, score: float) -> VerificationResult:
    return VerificationResult(
        verifier_name="semantic",
        score=score,
        passed=passed,
        reasoning="test",
    )


def test_easy_agreement_can_stop():
    stopper = AdaptiveEarlyTermination()
    analysis = QuestionAnalysis(domain="general", difficulty="easy", difficulty_score=0.2)
    results = [_result(True, 0.9), _result(True, 0.88)]
    decision = stopper.should_terminate(results, analysis)
    assert decision["terminate"] is True


def test_hard_question_does_not_stop_early():
    stopper = AdaptiveEarlyTermination()
    analysis = QuestionAnalysis(domain="medical", difficulty="hard", difficulty_score=0.8)
    results = [_result(True, 0.9)]
    decision = stopper.should_terminate(results, analysis)
    assert decision["terminate"] is False


def test_disagreement_continues():
    stopper = AdaptiveEarlyTermination()
    analysis = QuestionAnalysis(domain="general", difficulty="medium", difficulty_score=0.5)
    results = [_result(True, 0.8), _result(False, 0.8)]
    decision = stopper.should_terminate(results, analysis)
    assert decision["terminate"] is False
    assert "disagreement" in decision["reason"]


def test_hard_question_continues_after_the_minimum_is_met():
    stopper = AdaptiveEarlyTermination()
    analysis = QuestionAnalysis(domain="medical", difficulty="hard", difficulty_score=0.9)
    results = [_result(True, 0.95), _result(True, 0.95), _result(True, 0.95)]
    decision = stopper.should_terminate(results, analysis)
    assert decision["terminate"] is False
    assert "hard" in decision["reason"]


def test_medium_does_not_stop_before_the_minimum():
    stopper = AdaptiveEarlyTermination()
    analysis = QuestionAnalysis(domain="general", difficulty="medium", difficulty_score=0.5)
    decision = stopper.should_terminate([_result(True, 0.99)], analysis)
    assert decision["terminate"] is False
    assert "minimum" in decision["reason"]


def test_easy_low_confidence_continues():
    stopper = AdaptiveEarlyTermination()
    analysis = QuestionAnalysis(domain="general", difficulty="easy", difficulty_score=0.2)
    decision = stopper.should_terminate([_result(True, 0.6), _result(True, 0.6)], analysis)
    assert decision["terminate"] is False
    assert "insufficient" in decision["reason"]


def test_explicit_minimum_blocks_an_otherwise_ready_stop():
    stopper = AdaptiveEarlyTermination()
    analysis = QuestionAnalysis(domain="general", difficulty="easy", difficulty_score=0.2)
    ready = stopper.should_terminate([_result(True, 0.95)], analysis)
    blocked = stopper.should_terminate([_result(True, 0.95)], analysis, min_verifiers=2)
    assert ready["terminate"] is True
    assert blocked["terminate"] is False


def test_unsupported_rule_does_not_stop_early():
    stopper = AdaptiveEarlyTermination()
    analysis = QuestionAnalysis(domain="general", difficulty="easy", difficulty_score=0.2)
    unsupported = VerificationResult(
        verifier_name="rule",
        score=0.0,
        passed=False,
        reasoning="No supported deterministic rule matched the question.",
        metadata={"rule": "unsupported"},
    )
    decision = stopper.should_terminate([unsupported], analysis)
    assert decision["terminate"] is False
    assert "informative" in decision["reason"]


def test_supported_rule_rejection_can_stop_on_easy():
    stopper = AdaptiveEarlyTermination()
    analysis = QuestionAnalysis(domain="general", difficulty="easy", difficulty_score=0.2)
    rejection = VerificationResult(
        verifier_name="rule",
        score=0.0,
        passed=False,
        reasoning="Expected 4; received 5.",
        metadata={"rule": "arithmetic_addition", "expected": 4, "actual": 5},
    )
    decision = stopper.should_terminate([rejection], analysis)
    assert decision["terminate"] is True


def test_default_minima_match_the_selector_ranges():
    from app.decision.early_termination import MIN_VERIFIERS_BY_DIFFICULTY
    from app.selection.verifier_selector import DEFAULT_DIFFICULTY_RANGE

    for band, (minimum, _maximum) in DEFAULT_DIFFICULTY_RANGE.items():
        assert MIN_VERIFIERS_BY_DIFFICULTY[band] == minimum
