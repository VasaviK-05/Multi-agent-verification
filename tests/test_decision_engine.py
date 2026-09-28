"""Isolated tests for DecisionEngine."""

from app.decision.decision_engine import DecisionEngine
from app.models.schemas import VerificationResult
from app.reputation.reputation_manager import ReputationManager


def _result(name: str, score: float, passed: bool) -> VerificationResult:
    return VerificationResult(
        verifier_name=name,
        score=score,
        passed=passed,
        reasoning="test",
    )


def test_empty_results_are_unknown():
    status, score = DecisionEngine().decide([])
    assert status == "unknown"
    assert score == 0.0


def test_strong_agreement_passes():
    manager = ReputationManager(prior_alpha=8.0, prior_beta=2.0)
    engine = DecisionEngine(reputation_manager=manager)
    results = [
        _result("semantic", 0.9, True),
        _result("rule", 0.85, True),
    ]
    status, score = engine.decide(results, domain="general")
    assert status == "passed"
    assert score > 0.55


def test_strong_disagreement_can_fail():
    manager = ReputationManager(prior_alpha=8.0, prior_beta=2.0)
    engine = DecisionEngine(reputation_manager=manager)
    results = [
        _result("semantic", 0.9, False),
        _result("rule", 0.85, False),
    ]
    status, score = engine.decide(results, domain="general")
    assert status == "failed"
    assert score < 0.45


def test_mid_score_is_uncertain_with_neutral_prior():
    engine = DecisionEngine()
    results = [
        _result("semantic", 0.5, True),
        _result("evidence", 0.5, True),
    ]
    status, score = engine.decide(results)
    assert status == "uncertain"
    assert abs(score - 0.5) < 1e-6
