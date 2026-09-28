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
