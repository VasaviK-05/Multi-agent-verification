"""Isolated tests for AdaptiveEarlyTermination."""

import math

import pytest

from app.analysis.question_analyzer import QuestionAnalysis
from app.decision.decision_engine import DecisionEngine
from app.decision.early_termination import AdaptiveEarlyTermination
from app.models.schemas import VerificationResult
from app.reputation.reputation_manager import ReputationManager


def _vote(name: str, passed: bool, score: float) -> VerificationResult:
    return VerificationResult(
        verifier_name=name,
        score=score,
        passed=passed,
        reasoning="test",
    )


def _easy(score: float = 0.2) -> QuestionAnalysis:
    return QuestionAnalysis(domain="general", difficulty="easy", difficulty_score=score)


def _pair(passed: bool, score: float) -> list[VerificationResult]:
    return [_vote("semantic", passed, score), _vote("evidence", passed, score)]


def test_easy_agreement_can_stop():
    stopper = AdaptiveEarlyTermination()
    decision = stopper.should_terminate(
        [_vote("semantic", True, 0.9), _vote("evidence", True, 0.88)],
        _easy(),
    )
    assert decision["terminate"] is True
    assert decision["decision"].status == "passed"
    assert decision["decision"].score > 0.55


def test_hard_question_does_not_stop_early():
    stopper = AdaptiveEarlyTermination()
    analysis = QuestionAnalysis(domain="medical", difficulty="hard", difficulty_score=0.8)
    decision = stopper.should_terminate([_vote("semantic", True, 0.9)], analysis)
    assert decision["terminate"] is False
    assert "minimum" in decision["reason"]


def test_disagreement_continues():
    stopper = AdaptiveEarlyTermination()
    analysis = QuestionAnalysis(domain="general", difficulty="medium", difficulty_score=0.5)
    decision = stopper.should_terminate(
        [_vote("semantic", True, 0.8), _vote("evidence", False, 0.8)],
        analysis,
    )
    assert decision["terminate"] is False
    assert "disagreement" in decision["reason"]


def test_hard_question_continues_after_the_minimum_is_met():
    stopper = AdaptiveEarlyTermination()
    analysis = QuestionAnalysis(domain="medical", difficulty="hard", difficulty_score=0.9)
    decision = stopper.should_terminate(
        [
            _vote("semantic", True, 0.95),
            _vote("evidence", True, 0.95),
            _vote("rule", True, 0.95),
        ],
        analysis,
    )
    assert decision["terminate"] is False
    assert "hard" in decision["reason"]
    assert "decision" not in decision


def test_medium_does_not_stop_before_the_minimum():
    stopper = AdaptiveEarlyTermination()
    analysis = QuestionAnalysis(domain="general", difficulty="medium", difficulty_score=0.5)
    decision = stopper.should_terminate([_vote("semantic", True, 0.99)], analysis)
    assert decision["terminate"] is False
    assert "minimum" in decision["reason"]


def test_easy_low_confidence_continues():
    stopper = AdaptiveEarlyTermination()
    decision = stopper.should_terminate(
        [_vote("semantic", True, 0.6), _vote("evidence", True, 0.6)],
        _easy(),
    )
    assert decision["terminate"] is False
    assert "insufficient" in decision["reason"]


def test_explicit_minimum_blocks_an_otherwise_ready_stop():
    stopper = AdaptiveEarlyTermination()
    ready = stopper.should_terminate(_pair(True, 0.95), _easy())
    blocked = stopper.should_terminate(
        _pair(True, 0.95),
        _easy(),
        min_verifiers=3,
    )
    assert ready["terminate"] is True
    assert blocked["terminate"] is False
    assert "minimum" in blocked["reason"]


def test_unsupported_rule_does_not_stop_early():
    stopper = AdaptiveEarlyTermination()
    unsupported = VerificationResult(
        verifier_name="rule",
        score=0.0,
        passed=False,
        reasoning="No supported deterministic rule matched the question.",
        metadata={"rule": "unsupported"},
    )
    decision = stopper.should_terminate([unsupported], _easy())
    assert decision["terminate"] is False
    assert "usable" in decision["reason"]


def test_supported_rule_rejection_can_stop_on_easy():
    stopper = AdaptiveEarlyTermination()
    rejection = VerificationResult(
        verifier_name="rule",
        score=0.0,
        passed=False,
        reasoning="Expected 4; received 5.",
        metadata={"rule": "arithmetic_addition", "expected": 4, "actual": 5},
    )
    decision = stopper.should_terminate([rejection, _vote("semantic", False, 1.0)], _easy())
    assert decision["terminate"] is True
    assert decision["decision"].status == "failed"
    assert decision["decision"].score == -1.0


def test_tied_confidence_judgments_do_not_stop_early():
    stopper = AdaptiveEarlyTermination()
    tied = VerificationResult(
        verifier_name="confidence",
        score=1.0,
        passed=True,
        reasoning="Majority judgment: support. Agreement: 1/2.",
        metadata={
            "judgments": ["support", "reject"],
            "majority_label": "support",
        },
    )
    decision = stopper.should_terminate([tied], _easy(), min_verifiers=1)
    assert decision["terminate"] is False
    assert "usable" in decision["reason"]


def test_empty_and_abstentions_do_not_stop():
    stopper = AdaptiveEarlyTermination()
    empty = stopper.should_terminate([], _easy())
    assert empty["terminate"] is False
    assert "usable" in empty["reason"]
    neutral = VerificationResult(
        verifier_name="evidence",
        score=0.4,
        passed=False,
        reasoning="The retrieved evidence is neutral.",
        metadata={"nli_label": "neutral"},
    )
    missing = VerificationResult(
        verifier_name="semantic",
        score=0.0,
        passed=False,
        reasoning="No reference context provided for semantic comparison.",
    )
    decision = stopper.should_terminate([neutral, missing], _easy())
    assert decision["terminate"] is False
    assert "usable" in decision["reason"]


def test_duplicate_names_and_invalid_settings_are_rejected():
    stopper = AdaptiveEarlyTermination()
    with pytest.raises(ValueError, match="duplicate"):
        stopper.should_terminate(
            [_vote("semantic", True, 0.9), _vote("semantic", False, 0.2)],
            _easy(),
        )
    abstention = VerificationResult(
        verifier_name="rule",
        score=0.0,
        passed=False,
        reasoning="No supported deterministic rule matched the question.",
        metadata={"rule": "unsupported"},
    )
    with pytest.raises(ValueError, match="duplicate"):
        stopper.should_terminate([abstention, abstention.model_copy()], _easy())
    broken = VerificationResult.model_construct(
        verifier_name="semantic",
        score=float("nan"),
        passed=True,
        reasoning="test",
        metadata=None,
    )
    with pytest.raises(ValueError, match="score"):
        stopper.should_terminate([broken], _easy())
    with pytest.raises(ValueError, match="domain"):
        stopper.should_terminate(
            [_vote("semantic", True, 0.9)],
            QuestionAnalysis(domain=" ", difficulty="easy", difficulty_score=0.0),
        )
    with pytest.raises(ValueError, match="difficulty"):
        stopper.should_terminate(
            [_vote("semantic", True, 0.9)],
            QuestionAnalysis(domain="general", difficulty="extreme", difficulty_score=0.0),
        )
    for minimum in (True, 0, -1, 1.5):
        with pytest.raises(ValueError, match="min_verifiers"):
            stopper.should_terminate(
                [_vote("semantic", True, 0.9)],
                _easy(),
                min_verifiers=minimum,  # type: ignore[arg-type]
            )
def test_cold_start_and_reputation_weights():
    stopper = AdaptiveEarlyTermination()
    cold = stopper.should_terminate(_pair(True, 0.9), _easy())
    assert cold["terminate"] is True
    assert cold["decision"].aggregation == "equal_weight"

    positive = ReputationManager()
    for _ in range(6):
        positive.update_reputation("semantic", "general", True)
        positive.update_reputation("evidence", "general", True)
    engine = DecisionEngine(reputation_manager=positive)
    followed = stopper.should_terminate(
        _pair(True, 0.9),
        _easy(),
        decision_engine=engine,
    )
    assert followed["terminate"] is True
    assert followed["decision"].status == "passed"

    negative = ReputationManager(prior_alpha=1.0, prior_beta=8.0)
    inverted = stopper.should_terminate(
        _pair(True, 1.0),
        _easy(),
        decision_engine=DecisionEngine(reputation_manager=negative),
    )
    assert inverted["terminate"] is True
    assert inverted["decision"].status == "failed"

    mixed = ReputationManager(prior_alpha=1.0, prior_beta=8.0)
    for _ in range(8):
        mixed.update_reputation("semantic", "general", True)
    asymmetric = stopper.should_terminate(
        [_vote("semantic", True, 1.0), _vote("evidence", True, 1.0)],
        _easy(),
        decision_engine=DecisionEngine(reputation_manager=mixed),
    )
    assert asymmetric["terminate"] is False
    assert "disagreement" in asymmetric["reason"]

    zero_weight = ReputationManager()
    for _ in range(6):
        zero_weight.update_reputation("semantic", "general", True)
    medium = QuestionAnalysis(domain="general", difficulty="medium", difficulty_score=0.5)
    ignored = stopper.should_terminate(
        [_vote("semantic", True, 1.0), _vote("rule", True, 1.0)],
        medium,
        decision_engine=DecisionEngine(reputation_manager=zero_weight),
    )
    assert ignored["terminate"] is False
    assert "minimum" in ignored["reason"]


def test_equal_opposite_weights_cancel_and_do_not_stop():
    manager = ReputationManager()
    for _ in range(3):
        manager.update_reputation("semantic", "general", True)
        manager.update_reputation("evidence", "general", False)
    assert manager.get_reputation("semantic", "general") == 0.8
    assert manager.get_reputation("evidence", "general") == 0.2
    engine = DecisionEngine(reputation_manager=manager)
    votes = [_vote("semantic", True, 1.0), _vote("evidence", True, 1.0)]
    detail = engine.decide_detailed(votes, domain="general")
    assert detail.status == "uncertain"
    assert detail.raw_score == pytest.approx(0.0)
    decision = AdaptiveEarlyTermination().should_terminate(
        votes,
        QuestionAnalysis(domain="general", difficulty="medium", difficulty_score=0.5),
        decision_engine=engine,
    )
    assert decision["terminate"] is False


def test_effective_agreement_after_inversion_is_vetoed_by_original_disagreement():
    manager = ReputationManager(prior_alpha=1.0, prior_beta=8.0)
    for _ in range(8):
        manager.update_reputation("semantic", "general", True)
    decision = AdaptiveEarlyTermination().should_terminate(
        [_vote("semantic", True, 1.0), _vote("evidence", False, 1.0)],
        _easy(),
        decision_engine=DecisionEngine(reputation_manager=manager),
    )
    assert decision["terminate"] is False
    assert "original directional disagreement" in decision["reason"]


def _medium() -> QuestionAnalysis:
    return QuestionAnalysis(domain="general", difficulty="medium", difficulty_score=0.5)


def test_exact_policy_boundaries_and_custom_threshold():
    stopper = AdaptiveEarlyTermination()
    exact = stopper.should_terminate(_pair(True, 0.75), _easy())
    assert exact["terminate"] is True
    assert exact["decision"].status == "passed"
    rejected = stopper.should_terminate(_pair(False, 0.75), _easy())
    assert rejected["terminate"] is True
    assert rejected["decision"].status == "failed"
    below = math.nextafter(0.75, 0.0)
    missed = stopper.should_terminate(_pair(True, below), _easy())
    assert missed["terminate"] is False
    assert "insufficient" in missed["reason"]
    missed_reject = stopper.should_terminate(_pair(False, below), _easy())
    assert missed_reject["terminate"] is False
    assert "insufficient" in missed_reject["reason"]

    margin_stopper = AdaptiveEarlyTermination(easy_confidence=0.0, easy_margin=0.60)
    at_margin = margin_stopper.should_terminate(_pair(True, 0.60), _easy())
    assert at_margin["terminate"] is True
    assert at_margin["decision"].status == "passed"
    at_margin_reject = margin_stopper.should_terminate(_pair(False, 0.60), _easy())
    assert at_margin_reject["terminate"] is True
    assert at_margin_reject["decision"].status == "failed"
    under_margin = math.nextafter(0.60, 0.0)
    short = margin_stopper.should_terminate(_pair(True, under_margin), _easy())
    assert short["terminate"] is False
    short_reject = margin_stopper.should_terminate(
        _pair(False, under_margin),
        _easy(),
    )
    assert short_reject["terminate"] is False

    medium_exact = stopper.should_terminate(
        [_vote("semantic", True, 0.80), _vote("evidence", True, 0.80)],
        _medium(),
    )
    assert medium_exact["terminate"] is True
    assert medium_exact["decision"].status == "passed"
    medium_reject = stopper.should_terminate(
        [_vote("semantic", False, 0.80), _vote("evidence", False, 0.80)],
        _medium(),
    )
    assert medium_reject["terminate"] is True
    assert medium_reject["decision"].status == "failed"
    medium_below = math.nextafter(0.80, 0.0)
    medium_missed = stopper.should_terminate(
        [_vote("semantic", True, medium_below), _vote("evidence", True, medium_below)],
        _medium(),
    )
    assert medium_missed["terminate"] is False
    assert "insufficient" in medium_missed["reason"]
    medium_missed_reject = stopper.should_terminate(
        [_vote("semantic", False, medium_below), _vote("evidence", False, medium_below)],
        _medium(),
    )
    assert medium_missed_reject["terminate"] is False
    assert "insufficient" in medium_missed_reject["reason"]

    medium_margin = AdaptiveEarlyTermination(medium_confidence=0.0, medium_margin=0.70)
    medium_at_margin = medium_margin.should_terminate(
        [_vote("semantic", True, 0.70), _vote("evidence", True, 0.70)],
        _medium(),
    )
    assert medium_at_margin["terminate"] is True
    assert medium_at_margin["decision"].status == "passed"
    medium_at_margin_reject = medium_margin.should_terminate(
        [_vote("semantic", False, 0.70), _vote("evidence", False, 0.70)],
        _medium(),
    )
    assert medium_at_margin_reject["terminate"] is True
    assert medium_at_margin_reject["decision"].status == "failed"
    medium_under = math.nextafter(0.70, 0.0)
    medium_short = medium_margin.should_terminate(
        [_vote("semantic", True, medium_under), _vote("evidence", True, medium_under)],
        _medium(),
    )
    assert medium_short["terminate"] is False
    medium_short_reject = medium_margin.should_terminate(
        [_vote("semantic", False, medium_under), _vote("evidence", False, medium_under)],
        _medium(),
    )
    assert medium_short_reject["terminate"] is False

    strict = DecisionEngine(threshold=0.9)
    blocked = stopper.should_terminate(
        _pair(True, 0.8),
        _easy(),
        decision_engine=strict,
    )
    assert blocked["terminate"] is False
    assert "uncertain" in blocked["reason"]


@pytest.mark.parametrize(
    "field",
    ("easy_confidence", "easy_margin", "medium_confidence", "medium_margin"),
)
@pytest.mark.parametrize(
    "value",
    (True, False, float("nan"), float("inf"), float("-inf"), -0.1, 1.1),
)
def test_invalid_policy_values_are_rejected(field: str, value: object):
    with pytest.raises((TypeError, ValueError)):
        AdaptiveEarlyTermination(**{field: value})


def test_zero_confidence_does_not_count_toward_the_minimum():
    stopper = AdaptiveEarlyTermination()
    analysis = QuestionAnalysis(domain="general", difficulty="medium", difficulty_score=0.5)
    decision = stopper.should_terminate(
        [_vote("semantic", True, 0.0), _vote("evidence", True, 0.95)],
        analysis,
    )
    assert decision["terminate"] is False
    assert "minimum" in decision["reason"]


def test_default_minima_match_the_selector_ranges():
    from app.decision.early_termination import MIN_VERIFIERS_BY_DIFFICULTY
    from app.selection.verifier_selector import DEFAULT_DIFFICULTY_RANGE

    for band, (minimum, _maximum) in DEFAULT_DIFFICULTY_RANGE.items():
        assert MIN_VERIFIERS_BY_DIFFICULTY[band] == minimum


@pytest.mark.parametrize("difficulty", ["easy", "medium"])
@pytest.mark.parametrize("minimum", [None, 1, 2])
def test_one_strong_vote_cannot_bypass_the_safety_floor(difficulty, minimum):
    analysis = QuestionAnalysis("general", difficulty, 0.2 if difficulty == "easy" else 0.5)
    decision = AdaptiveEarlyTermination().should_terminate(
        [_vote("semantic", True, 1.0)], analysis, min_verifiers=minimum)
    assert decision["terminate"] is False
    assert "minimum 2" in decision["reason"]


def test_actual_structural_rejection_does_not_supply_a_second_contributor():
    from app.verifiers.rule_verifier import RuleVerifier

    structural = RuleVerifier().verify("Return the answer as JSON.", "not json")
    assert structural.metadata["rule_kind"] == "structural"
    assert structural.metadata["decision"] == "REJECT"
    votes = [structural, _vote("semantic", False, 1.0)]
    engine = DecisionEngine()
    before = engine.decide_detailed(votes)
    stop = AdaptiveEarlyTermination().should_terminate(votes, _easy(), decision_engine=engine)
    assert stop["terminate"] is False
    assert "minimum" in stop["reason"]
    assert before.status == "failed" and before.score == -1.0
    assert engine.decide_detailed(votes) == before


@pytest.mark.parametrize("kind,rule,stops", [
    ("structural", "new_format_rule", False),
    (None, "json_structure", False),
    ("factual", "format_validity", True),
    ("factual", "arithmetic_addition", True),
])
def test_rule_kind_is_preferred_and_legacy_fallback_is_narrow(kind, rule, stops):
    result = _vote("rule", False, 0).model_copy(update={
        "metadata": {"decision": "REJECT", "rule_kind": kind, "rule": rule}})
    decision = AdaptiveEarlyTermination().should_terminate(
        [result, _vote("semantic", False, 1)], _easy())
    assert decision["terminate"] is stops


def test_structural_dissent_does_not_enter_agreement_or_confidence_average():
    from app.verifiers.rule_verifier import RuleVerifier

    structural = RuleVerifier().verify("Return the answer as JSON.", "not json")
    # Its numerical rejection remains, but cannot veto factual stopping agreement.
    manager = ReputationManager()
    for name in ("semantic", "evidence"):
        manager.update_reputation(name, "general", True)
    stop = AdaptiveEarlyTermination().should_terminate(
        _pair(True, 0.75) + [structural], _easy(), decision_engine=DecisionEngine(manager))
    assert stop["terminate"] is True
    assert stop["decision"].score == 0.75


def test_actual_factual_zero_score_rejection_remains_eligible():
    from app.verifiers.rule_verifier import RuleVerifier

    result = RuleVerifier().verify("What is 2 + 2?", "5")
    assert result.score == 0 and result.metadata["rule_kind"] == "factual"
    stop = AdaptiveEarlyTermination().should_terminate(
        [result, _vote("semantic", False, 1)], _easy())
    assert stop["terminate"] is True
    assert stop["decision"].votes[0].confidence == 1
    assert stop["decision"].score == -1


@pytest.mark.parametrize("passed", [True, False])
@pytest.mark.parametrize("decision,score", [("UNSURE", 1), (None, 0)])
def test_noncontributing_directions_do_not_affect_counts_agreement_or_average(passed, decision, score):
    result = _vote("confidence", passed, score)
    if decision:
        result.metadata = {"decision": decision}
    stop = AdaptiveEarlyTermination().should_terminate([_vote("semantic", True, 0.75), result], _easy())
    assert stop["terminate"] is False
    stop = AdaptiveEarlyTermination().should_terminate(_pair(True, 0.75) + [result], _easy())
    assert stop["terminate"] is True
    assert stop["decision"].score == 0.75


def test_zero_weight_raw_dissent_vetoes_a_decisive_agreeing_weighted_prefix():
    manager = ReputationManager()
    for name in ("semantic", "evidence"):
        manager.update_reputation(name, "general", True)
    votes = _pair(True, 0.95) + [_vote("confidence", False, 1)]
    engine = DecisionEngine(manager)
    detail = engine.decide_detailed(votes)
    assert detail.status == "passed" and detail.votes[-1].weight == 0
    stop = AdaptiveEarlyTermination().should_terminate(votes, _easy(), decision_engine=engine)
    assert stop["terminate"] is False
    assert "original directional disagreement" in stop["reason"]


@pytest.mark.parametrize("score", [True, False, None, "0.2", float("nan"), float("inf"), -float("inf")])
def test_invalid_analysis_scores_fail_before_decision_evaluation(score):
    class UnusedEngine:
        def decide_detailed(self, *args, **kwargs):
            pytest.fail("invalid analysis must fail before decision evaluation")
    with pytest.raises(ValueError, match="difficulty_score must be a finite number"):
        AdaptiveEarlyTermination().should_terminate(_pair(True, 1), _easy(score), decision_engine=UnusedEngine())


def test_accepted_stop_uses_one_immutable_snapshot_despite_later_learning():
    manager = ReputationManager()
    class RecordingEngine(DecisionEngine):
        calls = 0
        captured = None
        def decide_detailed(self, results, domain=None):
            self.calls += 1
            self.captured = super().decide_detailed(results, domain)
            for name in ("semantic", "evidence"):
                manager.update_reputation(name, "general", False)
            return self.captured
    engine = RecordingEngine(manager)
    votes = _pair(True, 0.9)
    stop = AdaptiveEarlyTermination().should_terminate(votes, _easy(), decision_engine=engine)
    assert stop["terminate"] is True and engine.calls == 1
    assert stop["decision"] is engine.captured
    assert stop["decision"].score == 0.9
    assert DecisionEngine(manager).decide_detailed(votes).status == "failed"
