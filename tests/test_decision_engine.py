"""Isolated tests for DecisionEngine."""

import dataclasses
import math
import itertools

import pytest

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
    assert score < -0.55


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


def test_supported_rule_rejection_is_strong_negative_evidence():
    engine = DecisionEngine()
    status, score = engine.decide(
        [
            VerificationResult(
                verifier_name="rule",
                score=0.0,
                passed=False,
                reasoning="Expected 4; received 5.",
                metadata={"rule": "arithmetic_addition", "expected": 4, "actual": 5},
            )
        ]
    )
    assert status == "failed"
    assert abs(score - (-1.0)) < 1e-6


def test_unsupported_rule_is_not_a_rejection():
    engine = DecisionEngine()
    status, score = engine.decide(
        [
            VerificationResult(
                verifier_name="rule",
                score=0.0,
                passed=False,
                reasoning="No supported deterministic rule matched the question.",
                metadata={"rule": "unsupported"},
            )
        ]
    )
    assert status == "uncertain"
    assert score == 0.0


def test_decide_does_not_update_reputation():
    manager = ReputationManager()
    engine = DecisionEngine(reputation_manager=manager)
    engine.decide([_result("semantic", 0.9, True), _result("rule", 0.2, False)])
    assert manager.observation_count("semantic", "general") == 0
    assert manager.observation_count("rule", "general") == 0


def _past_threshold(threshold: float, *, positive: bool) -> float:
    """A float that crosses ``threshold`` but rounds back onto it."""
    direction = 1.0 if positive else -1.0
    value = math.nextafter(threshold, direction)
    while not (
        (value > threshold if positive else value < threshold)
        and round(value, 6) == threshold
    ):
        value = math.nextafter(value, direction)
    return value


def test_duplicate_names_are_rejected_including_an_abstention():
    engine = DecisionEngine()
    abstention = VerificationResult(
        verifier_name="rule",
        score=0.0,
        passed=False,
        reasoning="No supported deterministic rule matched the question.",
        metadata={"rule": "unsupported"},
    )
    vote = VerificationResult(
        verifier_name="rule",
        score=0.0,
        passed=False,
        reasoning="Expected 4; received 5.",
        metadata={"rule": "arithmetic_addition"},
    )
    with pytest.raises(ValueError, match="duplicate verifier name"):
        engine.decide([abstention, vote])


def test_blank_identifiers_and_domains_are_rejected():
    with pytest.raises(ValueError, match="domain"):
        DecisionEngine(default_domain=" ")
    engine = DecisionEngine(default_domain="medical")
    with pytest.raises(ValueError, match="domain"):
        engine.decide([_result("semantic", 1.0, True)], domain="")
    with pytest.raises(ValueError, match="verifier_name"):
        engine.decide([_result("  ", 1.0, True)], domain="medical")
    status, score = engine.decide([_result("semantic", 1.0, True)])
    assert status == "passed"
    assert score == 1.0


def test_invalid_scores_reputations_eps_and_thresholds_are_rejected():
    engine = DecisionEngine()
    for score in (float("nan"), float("inf"), -0.1, 1.1, True):
        broken = VerificationResult.model_construct(
            verifier_name="semantic",
            score=score,
            passed=True,
            reasoning="test",
            metadata=None,
        )
        with pytest.raises((TypeError, ValueError)):
            engine.decide([broken])
    for reputation in (float("nan"), float("inf"), -0.01, 1.01, True):
        with pytest.raises((TypeError, ValueError)):
            log_odds_weight(reputation)
    for eps in (0.0, 0.5, 1.0, float("nan"), True):
        with pytest.raises((TypeError, ValueError)):
            log_odds_weight(0.8, eps)
    for threshold in (0.0, 1.0, float("nan"), True):
        with pytest.raises((TypeError, ValueError)):
            DecisionEngine(threshold=threshold)
    assert math.isfinite(log_odds_weight(0.0))
    assert math.isfinite(log_odds_weight(1.0))
    assert log_odds_weight(0.0) < 0.0
    assert log_odds_weight(1.0) > 0.0
    assert log_odds_weight(0.0) == log_odds_weight(1e-6)
    for reputation in (0.0, 1.0):
        with pytest.raises(ValueError, match="strictly below 1"):
            log_odds_weight(reputation, 1e-17)
    low = log_odds_weight(0.0, 1e-10)
    high = log_odds_weight(1.0, 1e-10)
    assert math.isfinite(low) and low < 0.0
    assert math.isfinite(high) and high > 0.0


def test_all_abstentions_are_uncertain_and_domains_stay_separate():
    engine = DecisionEngine()
    status, score = engine.decide(
        [
            VerificationResult(
                verifier_name="semantic",
                score=0.0,
                passed=False,
                reasoning="No reference context provided for semantic comparison.",
            )
        ]
    )
    assert status == "uncertain"
    assert score == 0.0
    manager = ReputationManager(prior_alpha=1.0, prior_beta=4.0)
    for _ in range(6):
        manager.update_reputation("semantic", "medical", True)
    engine = DecisionEngine(reputation_manager=manager, default_domain="general")
    medical_status, medical_score = engine.decide(
        [_result("semantic", 1.0, True)],
        domain="medical",
    )
    general_status, general_score = engine.decide([_result("semantic", 1.0, True)])
    assert medical_status == "passed"
    assert medical_score == 1.0
    assert general_status == "failed"
    assert general_score == -1.0


def test_thresholds_use_the_unrounded_score():
    engine = DecisionEngine()
    status, score = engine.decide([_result("semantic", 0.55, True)])
    assert status == "uncertain"
    assert score == 0.55
    above = _past_threshold(0.55, positive=True)
    status, score = engine.decide([_result("semantic", above, True)])
    assert status == "passed"
    assert score == 0.55
    below = math.nextafter(0.55, 0.0)
    status, score = engine.decide([_result("semantic", below, True)])
    assert status == "uncertain"
    assert score <= 0.55
    status, score = engine.decide([_result("semantic", 0.55, False)])
    assert status == "uncertain"
    assert score == -0.55
    below_negative = _past_threshold(-0.55, positive=False)
    status, score = engine.decide([_result("semantic", abs(below_negative), False)])
    assert status == "failed"
    assert score == -0.55
    custom = DecisionEngine(threshold=0.9)
    status, score = custom.decide([_result("semantic", 0.8, True)])
    assert status == "uncertain"
    assert score == 0.8
    loose = DecisionEngine(threshold=0.2)
    status, score = loose.decide([_result("semantic", 0.8, True)])
    assert status == "passed"
    assert score == 0.8


def test_detailed_decision_matches_decide_and_does_not_mutate_state():
    manager = ReputationManager()
    manager.update_reputation("semantic", "medical", True)
    before = manager.export_state()
    calls: list[tuple[tuple[str, str], ...]] = []
    original = manager.statistics_batch

    def spy(pairs):
        calls.append(tuple(pairs))
        return original(pairs)

    manager.statistics_batch = spy
    engine = DecisionEngine(reputation_manager=manager)
    results = [_result("semantic", 0.9, True), _result("rule", 0.4, False)]
    status, score = engine.decide(results, domain="medical")
    detail = engine.decide_detailed(results, domain="medical")
    assert (detail.status, detail.score) == (status, score)
    assert detail.score == round(detail.raw_score, 6)
    if detail.status == "passed":
        assert detail.raw_score > detail.threshold
    elif detail.status == "failed":
        assert detail.raw_score < -detail.threshold
    else:
        assert abs(detail.raw_score) <= detail.threshold
    assert detail.aggregation == "log_odds"
    assert [vote.verifier_name for vote in detail.votes] == ["semantic", "rule"]
    assert len(calls) == 2
    assert calls[0] == (("semantic", "medical"), ("rule", "medical"))
    assert calls[1] == calls[0]
    with pytest.raises(dataclasses.FrozenInstanceError):
        detail.status = "failed"  # type: ignore[misc]
    assert manager.export_state() == before


def test_unrelated_rule_metadata_does_not_force_confidence_one():
    engine = DecisionEngine()
    status, score = engine.decide(
        [
            VerificationResult(
                verifier_name="semantic",
                score=0.4,
                passed=True,
                reasoning="compared",
                metadata={"rule": "arithmetic_addition"},
            )
        ]
    )
    assert status == "uncertain"
    assert score == 0.4


def _directional(name: str, score: float, passed: bool) -> VerificationResult:
    return VerificationResult(
        verifier_name=name, score=score, passed=passed,
        metadata={"decision": "SUPPORT" if passed else "REJECT"},
    )


@pytest.mark.parametrize("history", ["prior", "success", "failure", "balanced", "mixed"])
def test_campaign_exhaustive_abstention_and_zero_confidence_invariants(history):
    """Retained weights are policies, not calibrated correctness estimates."""
    manager = ReputationManager()
    for name in ("a", "b"):
        observations = {"prior": [], "success": [True], "failure": [False],
                        "balanced": [True, False],
                        "mixed": [name == "a"]}[history]
        for correct in observations:
            manager.update_reputation(name, "general", correct)
    engine = DecisionEngine(manager)
    # 36 two-vote combinations per history, including both confidence endpoints.
    states = list(itertools.product(("SUPPORT", "REJECT", "UNSURE"), (0., 1.)))
    for pair in itertools.product(states, repeat=2):
        results = [VerificationResult(verifier_name=name, passed=direction != "REJECT",
                    score=confidence, metadata={"decision": direction})
                   for name, (direction, confidence) in zip(("a", "b"), pair)]
        detail = engine.decide_detailed(results, domain="general")
        extra = VerificationResult(verifier_name="unused", score=1., passed=True,
                                   metadata={"decision": "UNSURE"})
        extended = engine.decide_detailed(results + [extra], domain="general")
        assert (extended.status, extended.score, extended.aggregation) == (
            detail.status, detail.score, detail.aggregation), (history, pair)
        assert -1 <= detail.score <= 1, (history, pair)
        assert all(v.confidence == v.contribution == 0
                   for v in detail.votes if v.abstained or v.confidence == 0)
        active = [r for r in results if r.metadata["decision"] != "UNSURE" and r.score > 0]
        if active:
            reduced = engine.decide_detailed(active, domain="general")
            assert (reduced.status, reduced.score, reduced.aggregation) == (
                detail.status, detail.score, detail.aggregation), (history, pair)
        else:
            assert detail.status == "uncertain" and detail.score == 0, (history, pair)


@pytest.mark.parametrize("learned", [False, True])
def test_zero_confidence_does_not_dilute_either_aggregation_mode(learned):
    manager = ReputationManager()
    if learned:
        for name in ("semantic", "evidence"):
            manager.update_reputation(name, "general", True)
    before = manager.export_state()
    detail = DecisionEngine(manager).decide_detailed([
        _directional("semantic", 0.9, True), _directional("evidence", 0.0, False),
    ])
    assert detail.aggregation == ("log_odds" if learned else "equal_weight")
    assert detail.raw_score == pytest.approx(0.9)
    assert detail.status == "passed"
    zero = detail.votes[1]
    assert zero.passed is False and zero.abstained is False
    assert zero.confidence == zero.contribution == 0.0
    assert manager.export_state() == before


def test_learned_zero_confidence_does_not_disable_prior_fallback():
    manager = ReputationManager()
    manager.update_reputation("evidence", "general", True)
    calls = []
    original = manager.statistics_batch

    def snapshot(pairs):
        calls.append(tuple(pairs))
        return original(pairs)

    manager.statistics_batch = snapshot
    detail = DecisionEngine(manager).decide_detailed([
        _directional("semantic", 0.9, True), _directional("evidence", 0.0, False),
    ])
    assert calls == [(("semantic", "general"), ("evidence", "general"))]
    assert detail.votes[1].weight > 0.0
    assert detail.votes[1].contribution == 0.0
    assert detail.aggregation == "equal_weight"
    assert (detail.status, detail.score) == ("passed", 0.9)


@pytest.mark.parametrize("with_abstention", [False, True])
def test_all_zero_confidence_directions_are_not_relabelled_as_abstentions(with_abstention):
    results = [_directional("semantic", 0.0, True), _directional("evidence", 0.0, False)]
    if with_abstention:
        results.append(VerificationResult(
            verifier_name="rule", score=1.0, passed=True,
            metadata={"decision": "UNSURE", "rule": "email_regex"},
        ))
    detail = DecisionEngine().decide_detailed(results)
    assert (detail.status, detail.score, detail.raw_score) == ("uncertain", 0.0, 0.0)
    assert detail.aggregation == "zero_confidence"
    assert [vote.passed for vote in detail.votes[:2]] == [True, False]
    assert all(not vote.abstained for vote in detail.votes[:2])
    assert all(vote.confidence == vote.contribution == 0.0 for vote in detail.votes)
    if with_abstention:
        assert detail.votes[2].abstained is True
    from app.analysis.question_analyzer import QuestionAnalysis
    from app.decision.early_termination import AdaptiveEarlyTermination

    assert not AdaptiveEarlyTermination().should_terminate(
        results, QuestionAnalysis("general", "easy", 0.0)
    )["terminate"]


@pytest.mark.parametrize("update,error", [
    ({"metadata": {"decision": None}}, "metadata.decision"),
    ({"metadata": {"decision": "SUPPORT"}}, "requires passed=True"),
    ({"verifier_name": " "}, "verifier_name"),
    ({"passed": "false"}, "boolean"),
])
def test_zero_confidence_results_are_validated_before_exclusion(update, error):
    invalid = _directional("evidence", 0.0, False).model_copy(update=update)
    manager = ReputationManager()
    before = manager.export_state()
    with pytest.raises((TypeError, ValueError), match=error):
        DecisionEngine(manager).decide([_directional("semantic", 0.9, True), invalid])
    assert manager.export_state() == before


def test_duplicate_zero_confidence_identities_are_still_rejected():
    zero = _directional("semantic", 0.0, True)
    with pytest.raises(ValueError, match="duplicate verifier name"):
        DecisionEngine().decide([zero, zero])


def test_factual_rule_zero_stored_score_remains_in_scoring_pool():
    result = VerificationResult(
        verifier_name="rule", score=0.0, passed=False,
        metadata={"decision": "REJECT", "rule": "arithmetic_addition"},
    )
    detail = DecisionEngine().decide_detailed([result, _directional("semantic", 0.0, True)])
    assert (detail.status, detail.score) == ("failed", -1.0)
    assert detail.votes[0].confidence == 1.0
    assert detail.votes[0].contribution == -1.0
    assert detail.votes[0].abstained is False


@pytest.mark.parametrize("succeeded,expected", [(True, 0.9), (False, -0.9)])
def test_current_policy_one_observation_dominates_opposing_untouched_votes(succeeded, expected):
    """Retained sparse-data policy, not evidence of empirical reliability."""
    manager = ReputationManager()
    manager.update_reputation("semantic", "general", succeeded)
    detail = DecisionEngine(manager).decide_detailed([
        _directional("semantic", 0.9, True),
        _directional("evidence", 0.9, False),
        _directional("confidence", 0.9, False),
    ])
    assert detail.aggregation == "log_odds"
    assert detail.raw_score == pytest.approx(expected)
    assert detail.status == ("passed" if succeeded else "failed")
    assert all(vote.weight == vote.contribution == 0.0 for vote in detail.votes[1:])


def test_mixed_abstentions_do_not_change_log_odds_score():
    manager = ReputationManager(8.0, 2.0)
    directional = [_directional("semantic", 0.9, True), _directional("confidence", 0.7, False)]
    abstentions = [VerificationResult(
        verifier_name=name, score=1.0, passed=True,
        metadata={"decision": "UNSURE"},
    ) for name in ("rule", "evidence")]
    engine = DecisionEngine(manager)
    expected = engine.decide_detailed(directional)
    detail = engine.decide_detailed(directional + abstentions)
    assert detail.aggregation == "log_odds"
    assert detail.raw_score == pytest.approx(0.1)
    assert (detail.status, detail.score) == (expected.status, expected.score)
    assert all(vote.abstained and vote.contribution == 0.0 for vote in detail.votes[2:])


def test_current_policy_experienced_balanced_reputations_use_equal_weight_fallback():
    """Observation count does not change this retained weighting policy."""
    manager = ReputationManager()
    for name in ("semantic", "evidence"):
        for succeeded in (True, False) * 4:
            manager.update_reputation(name, "general", succeeded)
        assert manager.observation_count(name, "general") == 8
    detail = DecisionEngine(manager).decide_detailed([
        _directional("semantic", 0.9, True), _directional("evidence", 0.7, False),
    ])
    assert detail.aggregation == "equal_weight"
    assert detail.raw_score == pytest.approx(0.1)
    assert all(vote.reputation == 0.5 and vote.weight == 0.0 for vote in detail.votes)


@pytest.mark.parametrize("successes,failures", [(500001, 500000), (500000, 500001)])
def test_current_policy_near_half_reputation_rounding_can_trigger_fallback(successes, failures):
    """Retained six-decimal precision, not a calibrated observation cutoff."""
    manager = ReputationManager()
    state = manager.export_state()
    state["pairs"] = [{
        "verifier_name": "semantic", "domain": "general",
        "successes": successes, "failures": failures,
    }]
    manager.restore_state(state)
    assert manager.statistics("semantic", "general").posterior_mean != 0.5
    detail = DecisionEngine(manager).decide_detailed([
        _directional("semantic", 0.9, True), _directional("evidence", 0.7, False),
    ])
    assert detail.votes[0].reputation == 0.5
    assert detail.votes[0].weight == 0.0
    assert detail.aggregation == "equal_weight"
    assert detail.raw_score == pytest.approx(0.1)
