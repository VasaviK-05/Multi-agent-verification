"""Shared abstention rules used by decision, feedback, and early stopping."""

from app.analysis.question_analyzer import QuestionAnalysis
from app.decision.early_termination import AdaptiveEarlyTermination
from app.decision.vote_normalization import is_abstention, vote_confidence
from app.models.schemas import VerificationResult
from app.reputation.reputation_manager import FeedbackEvent, ReputationManager


def _confidence(judgments: list[str], majority: str) -> VerificationResult:
    return VerificationResult(
        verifier_name="confidence",
        score=0.5,
        passed=majority == "support",
        reasoning=f"Majority judgment: {majority}. Agreement: 1/{len(judgments)}.",
        metadata={
            "method": "self_consistency",
            "judgments": judgments,
            "majority_label": majority,
            "agreement_count": 1,
            "total_judgments": len(judgments),
        },
    )


def test_confidence_ties_abstain_in_either_order():
    for judgments, majority in (
        (["support", "reject"], "support"),
        (["reject", "support"], "reject"),
    ):
        result = _confidence(judgments, majority)
        assert is_abstention(result) is True
        assert vote_confidence(result) == 0.0


def test_unique_confidence_majorities_keep_their_direction():
    support = _confidence(["support", "support", "reject"], "support")
    support = support.model_copy(update={"score": 2 / 3, "passed": True})
    reject = _confidence(["reject", "reject", "support"], "reject")
    reject = reject.model_copy(update={"score": 2 / 3, "passed": False})
    assert is_abstention(support) is False
    assert is_abstention(reject) is False
    assert vote_confidence(support) == support.score
    assert vote_confidence(reject) == reject.score
    assert support.passed is True
    assert reject.passed is False


def test_supported_rule_confidence_stays_on_the_rule_verifier():
    rejection = VerificationResult(
        verifier_name="rule",
        score=0.0,
        passed=False,
        reasoning="Expected 4; received 5.",
        metadata={"rule": "arithmetic_addition"},
    )
    assert is_abstention(rejection) is False
    assert vote_confidence(rejection) == 1.0
    unrelated = VerificationResult(
        verifier_name="semantic",
        score=0.4,
        passed=True,
        reasoning="compared",
        metadata={"rule": "arithmetic_addition"},
    )
    assert is_abstention(unrelated) is False
    assert vote_confidence(unrelated) == 0.4
    unsupported = VerificationResult(
        verifier_name="rule",
        score=0.0,
        passed=False,
        reasoning="No supported deterministic rule matched the question.",
        metadata={"rule": "unsupported"},
    )
    assert is_abstention(unsupported) is True


def test_tied_confidence_does_not_stop_early_or_add_an_observation():
    result = _confidence(["reject", "support"], "support")
    analysis = QuestionAnalysis("general", "easy", 0.0)
    decision = AdaptiveEarlyTermination().should_terminate([result], analysis, min_verifiers=1)
    assert decision["terminate"] is False
    manager = ReputationManager()
    event = FeedbackEvent(
        validation_id="tie-1",
        domain="general",
        answer_is_correct=True,
        results=(result,),
    )
    receipt = manager.record_feedback(event)
    assert receipt.observations_applied == 0
    assert manager.observation_count("confidence", "general") == 0
    assert manager.record_feedback(event).applied is False
    assert manager.observation_count("confidence", "general") == 0
