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
