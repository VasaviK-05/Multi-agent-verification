"""Shared abstention rules used by decision, feedback, and early stopping."""

import pytest

from app.analysis.question_analyzer import QuestionAnalysis
from app.decision.decision_engine import DecisionEngine
from app.decision.early_termination import AdaptiveEarlyTermination
from app.decision.vote_normalization import is_abstention, signed_mass, vote_confidence
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


def _explicit(name, decision, passed, **metadata):
    return VerificationResult(
        verifier_name=name, score=0.9, passed=passed, reasoning="Reported result.",
        metadata={**metadata, "decision": decision},
    )


@pytest.mark.parametrize("name", ["rule", "semantic", "evidence", "confidence", "custom"])
@pytest.mark.parametrize("passed", [False, True])
def test_unsure_is_shared_abstention_without_legacy_hints(name, passed):
    result = _explicit(name, "UNSURE", passed)
    assert is_abstention(result)
    assert vote_confidence(result) == 0
    assert signed_mass(result) is None
    detail = DecisionEngine().decide_detailed([result])
    assert detail.status == "uncertain"
    assert detail.raw_score == 0
    assert detail.votes[0].abstained
    assert detail.votes[0].contribution == 0
    assert not AdaptiveEarlyTermination().should_terminate(
        [result], QuestionAnalysis("general", "easy", 0.0), min_verifiers=1
    )["terminate"]
    manager = ReputationManager()
    assert manager.record_unscoped_ground_truth("general", [result], True) == 0
    receipt = manager.record_feedback(FeedbackEvent("unsure", "general", True, (result,)))
    assert receipt.observations_applied == 0
    assert manager.observation_count(name, "general") == 0


def test_successful_structural_unsure_preserves_reporting_and_does_not_dilute_votes():
    structural = _explicit("rule", "UNSURE", True, rule="email_regex")
    support = _explicit("semantic", "SUPPORT", True)
    detail = DecisionEngine().decide_detailed([structural, support])
    assert structural.passed is True
    assert structural.score == 0.9
    assert detail.raw_score == 0.9
    assert detail.votes[0].passed is True
    assert detail.votes[0].confidence == 0
    stopper = AdaptiveEarlyTermination()
    analysis = QuestionAnalysis("general", "medium", 0.5)
    assert not stopper.should_terminate([structural, support], analysis)["terminate"]
    second = _explicit("confidence", "SUPPORT", True)
    assert stopper.should_terminate([structural, support, second], analysis)["terminate"]
    manager = ReputationManager()
    assert manager.record_feedback(FeedbackEvent(
        "mixed", "general", True, (structural, support, second)
    )).observations_applied == 2
    assert manager.observation_count("rule", "general") == 0


def test_actual_rule_outputs_preserve_structural_reporting_and_factual_rejection():
    from app.verifiers.rule_verifier import RuleVerifier

    verifier = RuleVerifier()
    structural = verifier.verify("Provide an email address.", "user@example.com")
    assert structural.metadata["decision"] == "UNSURE"
    assert structural.passed is True
    assert structural.score == 1
    assert signed_mass(structural) is None
    factual = verifier.verify("What is 2 + 2?", "5")
    assert factual.metadata["decision"] == "REJECT"
    assert factual.passed is False
    assert factual.score == 0
    assert signed_mass(factual) == -1


@pytest.mark.parametrize("name", ["rule", "semantic", "evidence", "confidence", "custom"])
@pytest.mark.parametrize("decision,passed,sign", [("SUPPORT", True, 1), ("REJECT", False, -1)])
def test_explicit_direction_overrides_legacy_abstention_hints(name, decision, passed, sign):
    result = _explicit(name, decision, passed, rule="unsupported", nli_label="neutral",
                       judgments=[], majority_label="unsure")
    result.reasoning = "No reference context; No verification judgments"
    assert not is_abstention(result)
    assert vote_confidence(result) == 0.9
    assert signed_mass(result) == sign * 0.9
    assert DecisionEngine().decide([result]) == ("passed" if passed else "failed", sign * 0.9)


@pytest.mark.parametrize("decision,passed", [
    (None, False), ("", False), ("support", True), (" SUPPORT", True),
    ("OTHER", False), (0, False), (True, True), ([], False), ({}, False),
    ("SUPPORT", False), ("REJECT", True),
])
def test_invalid_decisions_fail_all_consumers_without_partial_learning(decision, passed):
    invalid = _explicit("evidence", decision, passed)
    valid = _explicit("semantic", "SUPPORT", True)
    for normalize in (is_abstention, vote_confidence, signed_mass):
        with pytest.raises(ValueError, match=r"metadata\.decision"):
            normalize(invalid)
    with pytest.raises(ValueError, match=r"metadata\.decision"):
        DecisionEngine().decide([valid, invalid])
    with pytest.raises(ValueError, match=r"metadata\.decision"):
        AdaptiveEarlyTermination().should_terminate(
            [valid, invalid], QuestionAnalysis("general", "easy", 0.0)
        )
    manager = ReputationManager()
    manager.record_feedback(FeedbackEvent("seed", "general", True, (valid,)))
    before = manager.export_state()
    with pytest.raises(ValueError, match=r"metadata\.decision"):
        manager.record_feedback(FeedbackEvent("bad", "general", True, (valid, invalid)))
    assert manager.export_state() == before
    with pytest.raises(ValueError, match=r"metadata\.decision"):
        manager.record_unscoped_ground_truth("general", [valid, invalid], True)
    assert manager.export_state() == before


@pytest.mark.parametrize("explicit", [False, True])
def test_factual_rule_zero_score_is_confident_rejection_across_consumers(explicit):
    metadata = {"rule": "arithmetic_addition"}
    if explicit:
        metadata["decision"] = "REJECT"
    result = VerificationResult(verifier_name="rule", score=0, passed=False, metadata=metadata)
    assert not is_abstention(result)
    assert vote_confidence(result) == 1
    assert signed_mass(result) == -1
    assert DecisionEngine().decide([result]) == ("failed", -1)
    assert not AdaptiveEarlyTermination().should_terminate(
        [result], QuestionAnalysis("general", "easy", 0.0)
    )["terminate"]
    agreeing_rejection = VerificationResult(
        verifier_name="semantic", score=1, passed=False,
        metadata={"decision": "REJECT"},
    )
    assert AdaptiveEarlyTermination().should_terminate(
        [result, agreeing_rejection], QuestionAnalysis("general", "easy", 0.0)
    )["terminate"]
    manager = ReputationManager()
    assert manager.record_feedback(FeedbackEvent("factual", "general", False, (result,))).observations_applied == 1
    assert manager.statistics("rule", "general").successes == 1


@pytest.mark.parametrize("name,passed,score,metadata,reasoning,abstained", [
    ("semantic", False, 0, None, "No reference context provided", True),
    ("semantic", False, 0.8, None, "Compared", False),
    ("evidence", False, 0.8, {"nli_label": "neutral"}, "Reported", True),
    ("evidence", False, 0.8, {"nli_label": "contradiction"}, "Reported", False),
    ("confidence", False, 0, {"judgments": []}, "Reported", True),
    ("rule", True, 1, {"rule": "email_regex"}, "Reported", True),
])
def test_absent_decision_retains_legacy_interpretation(name, passed, score, metadata, reasoning, abstained):
    result = VerificationResult(verifier_name=name, passed=passed, score=score,
                                metadata=metadata, reasoning=reasoning)
    assert is_abstention(result) is abstained
    assert vote_confidence(result) == (0 if abstained else score)
