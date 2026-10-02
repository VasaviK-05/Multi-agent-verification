"""Orchestrator wiring for selection, reputation, decision, and early stop."""

from app.analysis.question_analyzer import QuestionAnalysis, QuestionAnalyzer
from app.decision.decision_engine import DecisionEngine
from app.models.schemas import ValidationRequest, VerificationResult
from app.orchestration.validation_orchestrator import ValidationOrchestrator
from app.reputation.reputation_manager import ReputationManager
from app.selection.verifier_selector import VerifierSelector
from app.verifiers.base_verifier import BaseVerifier


class StubVerifier(BaseVerifier):
    def __init__(self, name: str, passed: bool = True, score: float = 0.5) -> None:
        self._name = name
        self.passed = passed
        self.score = score
        self.calls = 0

    @property
    def name(self) -> str:
        return self._name

    def verify(
        self,
        question: str,
        answer: str,
        context: str | None = None,
    ) -> VerificationResult:
        self.calls += 1
        return VerificationResult(
            verifier_name=self._name,
            score=self.score,
            passed=self.passed,
            reasoning="stub",
        )


def _named(score: float = 0.5) -> list[StubVerifier]:
    return [
        StubVerifier(name, passed=True, score=score)
        for name in ("semantic", "evidence", "rule", "confidence")
    ]


class FixedAnalyzer(QuestionAnalyzer):
    def __init__(self, analysis: QuestionAnalysis) -> None:
        self.analysis = analysis

    def analyze(self, question: str) -> QuestionAnalysis:
        return self.analysis


def test_default_orchestrator_shares_one_reputation_manager():
    orchestrator = ValidationOrchestrator()
    assert orchestrator.verifier_selector.reputation_manager is orchestrator.decision_engine.reputation_manager
    assert orchestrator.reputation_manager is orchestrator.decision_engine.reputation_manager


def test_divergent_reputation_managers_are_rejected():
    try:
        ValidationOrchestrator(
            verifier_selector=VerifierSelector(verifiers=[]),
            decision_engine=DecisionEngine(),
        )
        raised = False
    except ValueError:
        raised = True
    assert raised


def test_validate_does_not_learn_and_ground_truth_can_disagree_with_the_status():
    manager = ReputationManager()
    stubs = _named(score=0.9)
    analyzer = FixedAnalyzer(QuestionAnalysis("medical", "easy", 0.1))
    orchestrator = ValidationOrchestrator(
        question_analyzer=analyzer,
        verifier_selector=VerifierSelector(reputation_manager=manager, verifiers=stubs),
        decision_engine=DecisionEngine(reputation_manager=manager),
        reputation_manager=manager,
    )
    first = orchestrator.validate(ValidationRequest(question="q", answer="a"))
    assert first.results[0].verifier_name == "rule"
    assert first.final_status == "passed"
    assert manager.is_cold_start("rule", "medical")

    # The system said passed. The label says the answer is wrong, and the
    # verifier had agreed with the system, so a correct update lowers reputation.
    orchestrator.record_ground_truth(first.results, answer_is_correct=False)
    assert manager.get_reputation("rule", "medical") < 0.5
    assert manager.is_cold_start("rule", "general")

    second = orchestrator.validate(ValidationRequest(question="q", answer="a"))
    assert second.results[0].verifier_name == "semantic"

    analyzer.analysis = QuestionAnalysis("general", "easy", 0.1)
    third = orchestrator.validate(ValidationRequest(question="q", answer="a"))
    assert third.results[0].verifier_name == "rule"


def test_analyzer_domain_reaches_the_decision_engine():
    manager = ReputationManager()
    for _ in range(4):
        manager.update_reputation("semantic", "medical", False)
    stub = StubVerifier("semantic", passed=True, score=1.0)
    orchestrator = ValidationOrchestrator(
        question_analyzer=FixedAnalyzer(QuestionAnalysis("medical", "easy", 0.1)),
        verifier_selector=VerifierSelector(reputation_manager=manager, verifiers=[stub]),
        decision_engine=DecisionEngine(reputation_manager=manager),
        reputation_manager=manager,
    )
    response = orchestrator.validate(ValidationRequest(question="q", answer="a"))
    general = orchestrator.decision_engine.decide(response.results, domain="general")
    assert response.final_status == "failed"
    assert response.final_score < 0.0
    assert general[0] == "passed"
    assert manager.observation_count("semantic", "medical") == 4


def test_early_stop_runs_after_each_verifier_and_respects_the_minimum():
    stubs = _named(score=0.95)
    by_name = {stub.name: stub for stub in stubs}
    orchestrator = ValidationOrchestrator(
        question_analyzer=FixedAnalyzer(QuestionAnalysis("general", "easy", 0.34)),
        verifier_selector=VerifierSelector(verifiers=stubs),
    )
    response = orchestrator.validate(ValidationRequest(question="q", answer="a"))
    assert len(response.results) == 1
    assert by_name["rule"].calls == 1
    assert by_name["semantic"].calls == 0

    fresh = _named(score=0.95)
    fresh_by_name = {stub.name: stub for stub in fresh}
    held = ValidationOrchestrator(
        question_analyzer=FixedAnalyzer(QuestionAnalysis("general", "easy", 0.0)),
        verifier_selector=VerifierSelector(
            verifiers=fresh,
            difficulty_range={"easy": (2, 2), "medium": (2, 3), "hard": (3, 4)},
        ),
    )
    held_response = held.validate(ValidationRequest(question="q", answer="a"))
    assert len(held_response.results) == 2
    assert fresh_by_name["rule"].calls == 1
    assert fresh_by_name["semantic"].calls == 1
    assert fresh_by_name["evidence"].calls == 0


def test_low_confidence_and_hard_questions_keep_running():
    easy = _named(score=0.55)
    easy_by_name = {stub.name: stub for stub in easy}
    easy_run = ValidationOrchestrator(
        question_analyzer=FixedAnalyzer(QuestionAnalysis("general", "easy", 0.34)),
        verifier_selector=VerifierSelector(verifiers=easy),
    )
    easy_response = easy_run.validate(ValidationRequest(question="q", answer="a"))
    assert len(easy_response.results) == 2
    assert easy_by_name["rule"].calls == 1
    assert easy_by_name["semantic"].calls == 1

    hard = _named(score=0.99)
    hard_run = ValidationOrchestrator(
        question_analyzer=FixedAnalyzer(QuestionAnalysis("medical", "hard", 1.0)),
        verifier_selector=VerifierSelector(verifiers=hard),
    )
    hard_response = hard_run.validate(ValidationRequest(question="q", answer="a"))
    assert len(hard_response.results) == 4
    assert all(stub.calls == 1 for stub in hard)


def test_unsupported_rule_falls_back_and_is_not_a_reject():
    from app.verifiers.rule_verifier import RuleVerifier

    rule = RuleVerifier()
    semantic_abstains = _AbstainingStub(
        "semantic",
        reasoning="No reference context provided for semantic comparison.",
    )
    confidence = _AbstainingStub(
        "confidence",
        reasoning="No verification judgments were provided.",
        metadata={"method": "self_consistency", "judgments": []},
    )
    evidence = StubVerifier("evidence", passed=True, score=0.8)
    orchestrator = ValidationOrchestrator(
        verifier_selector=VerifierSelector(
            verifiers=[rule, semantic_abstains, confidence, evidence]
        ),
    )
    response = orchestrator.validate(
        ValidationRequest(question="What is the capital of France?", answer="Paris")
    )
    roles = [result.metadata["pipeline_role"] for result in response.results]
    assert [result.verifier_name for result in response.results] == [
        "rule",
        "semantic",
        "confidence",
        "evidence",
    ]
    assert roles == ["abstention", "abstention", "abstention", "vote"]
    assert response.results[0].metadata["rule"] == "unsupported"
    assert "not a pass or a reject" in response.results[0].metadata["pipeline_note"]
    assert "Consulted after" in response.results[-1].metadata["pipeline_note"]
    assert response.final_status == "passed"
    assert response.final_score > 0.55
    assert semantic_abstains.calls == 1
    assert confidence.calls == 1
    assert evidence.calls == 1

    manager = orchestrator.reputation_manager
    orchestrator.record_ground_truth(response.results, answer_is_correct=True)
    assert manager.is_cold_start("rule", "general")
    assert not manager.is_cold_start("evidence", "general")


def test_supported_rule_rejection_stops_with_a_fail():
    from app.verifiers.rule_verifier import RuleVerifier

    rule = RuleVerifier()
    semantic = StubVerifier("semantic", passed=True, score=0.95)
    orchestrator = ValidationOrchestrator(
        verifier_selector=VerifierSelector(verifiers=[rule, semantic]),
    )
    response = orchestrator.validate(ValidationRequest(question="What is 2+2?", answer="5"))
    assert len(response.results) == 1
    result = response.results[0]
    assert result.verifier_name == "rule"
    assert result.metadata["rule"] == "arithmetic_addition"
    assert result.metadata["pipeline_role"] == "vote"
    assert result.passed is False
    assert result.score == 0.0
    assert "deterministic" in result.metadata["pipeline_note"]
    assert "confidence 1" in result.metadata["pipeline_note"]
    assert response.final_status == "failed"
    assert response.final_score < -0.55
    assert semantic.calls == 0


def test_delayed_feedback_uses_the_original_validation_domain():
    class SwitchingAnalyzer(QuestionAnalyzer):
        def analyze(self, question: str) -> QuestionAnalysis:
            domain = "medical" if question == "A" else "technical"
            return QuestionAnalysis(domain, "easy", 0.0)

    stubs = _named(score=0.95)
    manager = ReputationManager()
    orchestrator = ValidationOrchestrator(
        question_analyzer=SwitchingAnalyzer(),
        verifier_selector=VerifierSelector(reputation_manager=manager, verifiers=stubs),
        decision_engine=DecisionEngine(reputation_manager=manager),
        reputation_manager=manager,
    )
    first = orchestrator.validate(ValidationRequest(question="A", answer="a"))
    assert manager.observation_count("rule", "medical") == 0
    second = orchestrator.validate(ValidationRequest(question="B", answer="b"))
    assert first.domain == "medical"
    assert second.domain == "technical"
    assert first.validation_id != second.validation_id
    applied = orchestrator.record_ground_truth(
        first.results,
        False,
        validation_id=first.validation_id,
    )
    assert applied == 1
    assert manager.observation_count("rule", "medical") == 1
    assert manager.is_cold_start("rule", "technical")
    replay = orchestrator.record_ground_truth(
        first.results,
        False,
        validation_id=first.validation_id,
    )
    assert replay == 0
    assert manager.observation_count("rule", "medical") == 1
    try:
        orchestrator.record_ground_truth(
            first.results,
            True,
            domain="technical",
            validation_id=first.validation_id,
        )
        raised = False
    except ValueError:
        raised = True
    assert raised
    assert manager.statistics("rule", "medical").failures == 1
    assert manager.is_cold_start("rule", "technical")


def test_snapshot_and_result_identity_protect_delayed_feedback():
    stubs = _named(score=0.95)
    manager = ReputationManager()
    orchestrator = ValidationOrchestrator(
        question_analyzer=FixedAnalyzer(QuestionAnalysis("medical", "easy", 0.0)),
        verifier_selector=VerifierSelector(reputation_manager=manager, verifiers=stubs),
        decision_engine=DecisionEngine(reputation_manager=manager),
        reputation_manager=manager,
    )
    first = orchestrator.validate(ValidationRequest(question="A", answer="a"))
    orchestrator._question_analyzer.analysis = QuestionAnalysis("technical", "easy", 0.0)
    second = orchestrator.validate(ValidationRequest(question="B", answer="b"))
    stored = orchestrator._contexts[first.validation_id].results[0]
    original_passed = stored.passed
    original_name = stored.verifier_name
    first.results[0].passed = not original_passed
    first.results[0].verifier_name = "renamed"
    first.results[0].metadata["rule"] = "unsupported"
    assert stored.passed is original_passed
    assert stored.verifier_name == original_name
    assert stored.metadata.get("rule") != "unsupported"
    viewed = orchestrator.validation_context(first.validation_id)
    viewed.results[0].metadata["rule"] = "unsupported"
    viewed.results[0].passed = not original_passed
    assert orchestrator._contexts[first.validation_id].results[0].metadata.get("rule") != "unsupported"
    assert manager.is_cold_start("rule", "medical")
    try:
        orchestrator.record_ground_truth(
            first.results,
            False,
            validation_id=first.validation_id,
        )
        raised = False
    except ValueError:
        raised = True
    assert raised
    assert manager.is_cold_start("rule", "medical")

    applied = orchestrator.record_ground_truth(second.results, True)
    assert applied == 1
    assert manager.observation_count("rule", "technical") == 1
    assert manager.is_cold_start("rule", "medical")
    clone = [result.model_copy(deep=True) for result in second.results]
    try:
        orchestrator.record_ground_truth(clone, True)
        raised = False
    except ValueError:
        raised = True
    assert raised
    assert manager.observation_count("rule", "technical") == 1
    assert orchestrator.record_ground_truth(clone, True, domain="general") == 1
    assert orchestrator.record_ground_truth(clone, True, domain="general") == 1
    assert manager.observation_count("rule", "general") == 2
    assert manager.observation_count("rule", "technical") == 1
    try:
        orchestrator.record_ground_truth(second.results, True, validation_id="missing")
        raised = False
    except ValueError:
        raised = True
    assert raised
    try:
        orchestrator.record_ground_truth(
            second.results,
            False,
            domain="medical",
            validation_id=second.validation_id,
        )
        raised = False
    except ValueError:
        raised = True
    assert raised
    assert orchestrator.record_ground_truth(
        second.results,
        True,
        validation_id=second.validation_id,
    ) == 0
    assert manager.observation_count("rule", "technical") == 1
    try:
        orchestrator.record_ground_truth(
            [first.results[0], second.results[0]],
            True,
        )
        raised = False
    except ValueError:
        raised = True
    assert raised


def test_mismatched_binding_slot_does_not_resolve_a_different_object():
    stubs = _named(score=0.95)
    manager = ReputationManager()
    orchestrator = ValidationOrchestrator(
        question_analyzer=FixedAnalyzer(QuestionAnalysis("medical", "easy", 0.0)),
        verifier_selector=VerifierSelector(reputation_manager=manager, verifiers=stubs),
        decision_engine=DecisionEngine(reputation_manager=manager),
        reputation_manager=manager,
    )
    response = orchestrator.validate(ValidationRequest(question="A", answer="a"))
    original = response.results[0]
    lookalike = original.model_copy(deep=True)
    orchestrator._result_binding[id(lookalike)] = (original, response.validation_id)
    viewed = orchestrator.validation_context(response.validation_id)
    retained, bound_id = orchestrator._result_binding[id(original)]
    assert retained is original
    assert bound_id == response.validation_id
    assert viewed.results[0] is not retained
    assert viewed.results[0] is not orchestrator._contexts[response.validation_id].results[0]
    try:
        orchestrator.record_ground_truth([lookalike], True)
        raised = False
    except ValueError:
        raised = True
    assert raised
    assert manager.observation_count("rule", "medical") == 0
    assert orchestrator.record_ground_truth(response.results, True) == 1
    assert manager.observation_count("rule", "medical") == 1


def test_verification_types_change_the_ranked_pipeline_order():
    stubs = _named(score=0.9)
    by_name = {stub.name: stub for stub in stubs}
    orchestrator = ValidationOrchestrator(
        question_analyzer=FixedAnalyzer(
            QuestionAnalysis(
                "general",
                "easy",
                0.0,
                verification_types=["evidence_retrieval"],
            )
        ),
        verifier_selector=VerifierSelector(verifiers=stubs),
    )
    response = orchestrator.validate(ValidationRequest(question="q", answer="a"))
    assert response.results[0].verifier_name == "evidence"
    assert by_name["evidence"].calls == 1
    assert by_name["rule"].calls == 0
    explained = orchestrator.verifier_selector.explain_ranking(orchestrator.last_analysis)
    assert explained[0].verifier_name == "evidence"
    assert explained[0].suitability_contribution > 0.0


def test_type_preferred_abstention_still_falls_through_to_the_next_ranked_verifier():
    evidence = _AbstainingStub(
        "evidence",
        reasoning="No supporting evidence was retrieved.",
    )
    rule = StubVerifier("rule", passed=True, score=0.9)
    semantic = StubVerifier("semantic", passed=True, score=0.9)
    confidence = StubVerifier("confidence", passed=True, score=0.9)
    orchestrator = ValidationOrchestrator(
        question_analyzer=FixedAnalyzer(
            QuestionAnalysis(
                "general",
                "easy",
                0.0,
                verification_types=["direct_fact"],
            )
        ),
        verifier_selector=VerifierSelector(
            verifiers=[semantic, evidence, rule, confidence]
        ),
    )
    response = orchestrator.validate(ValidationRequest(question="q", answer="a"))
    assert [result.verifier_name for result in response.results] == ["evidence", "rule"]
    assert response.results[0].metadata["pipeline_role"] == "abstention"
    assert response.results[1].metadata["pipeline_role"] == "vote"
    assert semantic.calls == 0
    assert confidence.calls == 0


def test_unrelated_rule_metadata_keeps_the_score_explanation():
    semantic = _RuleLabeledSemantic()
    orchestrator = ValidationOrchestrator(
        question_analyzer=FixedAnalyzer(QuestionAnalysis("general", "easy", 0.0)),
        verifier_selector=VerifierSelector(verifiers=[semantic]),
    )
    response = orchestrator.validate(ValidationRequest(question="A", answer="a"))
    result = response.results[0]
    note = result.metadata["pipeline_note"]
    assert result.verifier_name == "semantic"
    assert result.metadata["rule"] == "arithmetic_addition"
    assert "deterministic" not in note
    assert "0.4000" in note
    assert response.final_score == 0.4


class _RuleLabeledSemantic(StubVerifier):
    def __init__(self) -> None:
        super().__init__("semantic", passed=True, score=0.4)

    def verify(
        self,
        question: str,
        answer: str,
        context: str | None = None,
    ) -> VerificationResult:
        self.calls += 1
        return VerificationResult(
            verifier_name="semantic",
            score=0.4,
            passed=True,
            reasoning="compared",
            metadata={"rule": "arithmetic_addition"},
        )


def test_tied_confidence_is_not_a_vote_and_does_not_learn():
    confidence = _TiedConfidence()
    semantic = StubVerifier("semantic", passed=True, score=0.95)
    manager = ReputationManager()
    orchestrator = ValidationOrchestrator(
        question_analyzer=FixedAnalyzer(QuestionAnalysis("medical", "easy", 0.0)),
        verifier_selector=VerifierSelector(
            reputation_manager=manager,
            verifiers=[confidence, semantic],
            verifier_profiles={
                "confidence": {"cost": 0.0, "latency": 0.0},
                "semantic": {"cost": 1.0, "latency": 1.0},
            },
        ),
        decision_engine=DecisionEngine(reputation_manager=manager),
        reputation_manager=manager,
    )
    response = orchestrator.validate(ValidationRequest(question="A", answer="a"))
    assert [result.verifier_name for result in response.results] == ["confidence", "semantic"]
    assert response.results[0].metadata["pipeline_role"] == "abstention"
    assert "tied" in response.results[0].metadata["pipeline_note"]
    assert response.results[1].metadata["pipeline_role"] == "vote"
    applied = orchestrator.record_ground_truth(
        response.results,
        True,
        validation_id=response.validation_id,
    )
    assert applied == 1
    assert manager.observation_count("confidence", "medical") == 0
    assert manager.observation_count("semantic", "medical") == 1
    assert orchestrator.decision_engine.reputation_manager is manager


class _TiedConfidence(StubVerifier):
    def __init__(self) -> None:
        super().__init__("confidence", passed=True, score=1.0)

    def verify(
        self,
        question: str,
        answer: str,
        context: str | None = None,
    ) -> VerificationResult:
        self.calls += 1
        return VerificationResult(
            verifier_name="confidence",
            score=1.0,
            passed=True,
            reasoning="Majority judgment: support. Agreement: 1/2.",
            metadata={
                "judgments": ["support", "reject"],
                "majority_label": "support",
            },
        )


class _AbstainingStub(StubVerifier):
    def __init__(self, name: str, reasoning: str, metadata: dict | None = None) -> None:
        super().__init__(name, passed=False, score=0.0)
        self._reasoning = reasoning
        self._metadata = metadata or {}

    def verify(
        self,
        question: str,
        answer: str,
        context: str | None = None,
    ) -> VerificationResult:
        self.calls += 1
        return VerificationResult(
            verifier_name=self._name,
            score=0.0,
            passed=False,
            reasoning=self._reasoning,
            metadata=dict(self._metadata),
        )
