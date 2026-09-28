"""Isolated tests for DecisionEngine."""

from app.decision.decision_engine import (
    SCORE_HIGH,
    SCORE_LOW,
    DecisionEngine,
    log_odds_weight,
)
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


def test_log_odds_is_zero_at_one_half_and_negative_below():
    assert log_odds_weight(0.5) == 0.0
    assert log_odds_weight(0.2) < 0.0
    assert log_odds_weight(0.8) > 0.0
    assert abs(log_odds_weight(0.8) + log_odds_weight(0.2)) < 1e-12


def test_reputation_one_half_is_ignored_when_another_vote_is_informative():
    manager = ReputationManager()
    for _ in range(3):
        manager.update_reputation("semantic", "general", True)
    engine = DecisionEngine(reputation_manager=manager)
    status, score = engine.decide(
        [
            _result("semantic", 1.0, True),
            _result("rule", 1.0, False),
        ],
        domain="general",
    )
    assert abs(score - 1.0) < 1e-6
    assert status == "passed"


def test_reputation_below_one_half_inverts_a_pass():
    manager = ReputationManager(prior_alpha=1.0, prior_beta=4.0)
    assert manager.get_reputation("semantic", "general") == 0.2
    engine = DecisionEngine(reputation_manager=manager)
    status, score = engine.decide([_result("semantic", 1.0, True)], domain="general")
    assert abs(score - (-1.0)) < 1e-6
    assert status == "failed"


def test_reputation_below_one_half_inverts_a_reject():
    manager = ReputationManager(prior_alpha=1.0, prior_beta=4.0)
    engine = DecisionEngine(reputation_manager=manager)
    status, score = engine.decide([_result("semantic", 1.0, False)], domain="general")
    assert abs(score - 1.0) < 1e-6
    assert status == "passed"


def test_equal_opposite_votes_are_uncertain():
    manager = ReputationManager(prior_alpha=8.0, prior_beta=2.0)
    engine = DecisionEngine(reputation_manager=manager)
    status, score = engine.decide(
        [
            _result("semantic", 0.9, True),
            _result("rule", 0.9, False),
        ],
        domain="general",
    )
    assert abs(score) < 1e-6
    assert status == "uncertain"


def test_weighted_score_matches_the_log_odds_formula():
    manager = ReputationManager()
    for _ in range(3):
        manager.update_reputation("semantic", "general", True)
    manager.update_reputation("rule", "general", False)
    engine = DecisionEngine(reputation_manager=manager)
    results = [
        _result("semantic", 0.9, True),
        _result("rule", 0.4, False),
    ]
    weight_semantic = log_odds_weight(manager.get_reputation("semantic", "general"))
    weight_rule = log_odds_weight(manager.get_reputation("rule", "general"))
    numerator = weight_semantic * 0.9 * 1.0 + weight_rule * 0.4 * -1.0
    denominator = abs(weight_semantic) + abs(weight_rule)
    expected = round(numerator / denominator, 6)
    status, score = engine.decide(results, domain="general")
    assert score == expected
    assert SCORE_LOW <= score <= SCORE_HIGH
    assert status in {"passed", "failed", "uncertain"}


def test_decide_does_not_update_reputation():
    manager = ReputationManager()
    engine = DecisionEngine(reputation_manager=manager)
    engine.decide([_result("semantic", 0.9, True), _result("rule", 0.2, False)])
    assert manager.observation_count("semantic", "general") == 0
    assert manager.observation_count("rule", "general") == 0
