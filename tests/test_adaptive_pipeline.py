"""Orchestrator wiring for selection, reputation, decision, and early stop."""

import pytest
import itertools

from app.analysis.question_analyzer import QuestionAnalysis, QuestionAnalyzer
from app.decision.decision_engine import DecisionEngine
from app.decision.early_termination import AdaptiveEarlyTermination
from app.models.schemas import ValidationRequest, VerificationResult
from app.orchestration.validation_orchestrator import ValidationOrchestrator
from app.reputation.reputation_manager import ReputationManager
from app.selection.verifier_selector import VerifierSelector
from app.verifiers.base_verifier import BaseVerifier


@pytest.mark.parametrize("history", ["prior", "success", "failure", "balanced"])
def test_campaign_connected_small_pool_execution_and_feedback(history):
    """Exhaustive controlled votes; retained inversion is not accuracy evidence."""
    states = list(itertools.product(("SUPPORT", "REJECT", "UNSURE"), (0., .95)))
    for pair in itertools.product(states, repeat=2):
        manager = ReputationManager()
        for name in ("a", "b", "later"):
            for correct in {"prior": [], "success": [True], "failure": [False],
                            "balanced": [True, False]}[history]:
                manager.update_reputation(name, "general", correct)
        checkers = [MetadataChecker(name, direction != "REJECT", confidence,
                                   metadata={"decision": direction})
                    for name, (direction, confidence) in zip(("a", "b"), pair)]
        checkers.append(MetadataChecker("later"))
        run = connected(checkers, manager=manager)
        before = manager.export_state()
        response = run.validate(ValidationRequest(question="q", answer="a"))
        assert manager.export_state() == before, (history, pair)
        executed = [c.name for c in checkers if c.calls]
        assert [r.verifier_name for r in response.results] == executed, (history, pair)
        diagnostics = summary(response)
        assert diagnostics["numerical_decision"]["score"] == response.final_score
        positive = [(d, c) for d, c in pair if d != "UNSURE" and c > 0]
        if len(positive) < 2 or len({d for d, c in positive}) > 1:
            assert checkers[-1].calls == 1, (history, pair)
        counts = {c.name: manager.observation_count(c.name, "general") for c in checkers}
        # Ground truth is deliberately independent of the public decision.
        expected = sum(r.metadata["decision"] != "UNSURE" for r in response.results)
        assert run.record_ground_truth(response.results, False,
                                       validation_id=response.validation_id) == expected
        learned = manager.export_state()
        assert run.record_ground_truth(response.results, False,
                                       validation_id=response.validation_id) == 0
        assert manager.export_state() == learned
        with pytest.raises(ValueError):
            run.record_ground_truth(response.results, True, validation_id=response.validation_id)
        assert manager.export_state() == learned
        for checker in checkers:
            result = next((r for r in response.results if r.verifier_name == checker.name), None)
            increment = int(result is not None and result.metadata["decision"] != "UNSURE")
            assert manager.observation_count(checker.name, "general") == counts[checker.name] + increment


@pytest.mark.parametrize("mutation", ["bare", "neutral", "partial", "conflict", "rows", "claims"])
def test_campaign_malformed_factual_metadata_cannot_replace_coverage(mutation):
    metadata = factual_metadata()
    if mutation == "bare":
        metadata = {"decision": "SUPPORT"}
    elif mutation == "neutral":
        metadata["nli_label"] = "neutral"
    elif mutation == "partial":
        metadata["claim_decisions"].append({"claim": "another claim", "decision": "UNSURE"})
    elif mutation == "conflict":
        metadata["contradicting"] = [{"nli_label": "contradiction"}]
    elif mutation == "rows":
        metadata["supporting"] = {"nli_label": "entailment"}
    else:
        metadata["claim_decisions"] = [{"claim": "claim"}]
    run = connected([MetadataChecker("generic"), MetadataChecker("custom", metadata=metadata),
                     MetadataChecker("later")], hints=["direct_fact"],
                    mapping={"direct_fact": "custom"})
    response = run.validate(ValidationRequest(question="Who wrote Hamlet?", answer="Shakespeare"))
    assert len(response.results) == 3
    assert response.final_status == "uncertain" and response.final_score == .95
    assert summary(response)["coverage"]["direct_fact"]["directional"] == []


def test_campaign_actual_partial_evidence_continues_without_factual_coverage():
    """Actual evidence logic with controlled retrieval/NLI, not live accuracy."""
    from app.verifiers.evidence_verifier import EvidenceVerifier
    from tests.test_evidence_verifier import FakeRetriever, FakeNLI, chunk, ENTAILS
    evidence = EvidenceVerifier(retriever=FakeRetriever(by_query={
        "Seine": [chunk("Germany", "Berlin is on the Spree.", .10)],
        "capital of France": [chunk("France", "Paris is the capital of France.", .85)],
    }), nli=FakeNLI({"capital of France": ENTAILS}))
    run = connected([MetadataChecker("generic"), evidence, MetadataChecker("later")],
                    hints=["direct_fact"])
    response = run.validate(ValidationRequest(question="What is the capital of France?",
        answer="Paris is the capital of France. It lies on the Seine."))
    assert response.results[1].metadata["unsure_reason"] == "partial_support"
    assert len(response.results) == 3 and response.final_status == "uncertain"
    assert summary(response)["coverage"]["direct_fact"]["directional"] == []
    assert summary(response)["coverage"]["direct_fact"]["attempts"] == [
        {"verifier": "evidence", "state": "abstained"}]


@pytest.mark.parametrize("dissent_history", [[], [False]])
def test_campaign_raw_dissent_blocks_stop_despite_zero_or_inverted_weight(dissent_history):
    manager = ReputationManager()
    for name in ("a", "b"):
        manager.update_reputation(name, "general", True)
    for correct in dissent_history:
        manager.update_reputation("dissent", "general", correct)
    # Use equal resources and a custom suitability mapping to put the dissent
    # first. Reputation ranking remains intact; generic quorum alone is decisive.
    checkers = [MetadataChecker("dissent", False, 1), MetadataChecker("a", score=1),
                MetadataChecker("b", score=1), MetadataChecker("later", score=1)]
    selector = VerifierSelector(verifiers=checkers, reputation_manager=manager,
        lambda_cost=0, lambda_latency=0, lambda_suitability=1,
        type_mapping={"logical_rule": "dissent"})
    run = ValidationOrchestrator(question_analyzer=FixedAnalyzer(QuestionAnalysis(
        "general", "easy", .1, verification_types=["logical_rule"])),
        verifier_selector=selector, decision_engine=DecisionEngine(manager))
    response = run.validate(ValidationRequest(question="q", answer="a"))
    assert [r.verifier_name for r in response.results] == ["dissent", "a", "b", "later"]
    assert summary(response)["termination"] == "candidate_exhaustion"
    # Exhaustion deliberately retains decisive numerical status once minima hold.
    assert response.final_status == "passed" and response.final_score == 1


@pytest.mark.parametrize("band", ["easy", "medium"])
def test_campaign_custom_selector_minimum_is_binding_in_connected_run(band):
    manager = ReputationManager()
    checkers = [MetadataChecker(name, score=1) for name in ("a", "b", "c", "later")]
    selector = VerifierSelector(verifiers=checkers, reputation_manager=manager,
        lambda_cost=0, lambda_latency=0, lambda_suitability=0,
        difficulty_range={"easy": (3, 3), "medium": (3, 3), "hard": (3, 4)})
    run = ValidationOrchestrator(question_analyzer=FixedAnalyzer(QuestionAnalysis("general", band, .5)),
        verifier_selector=selector, decision_engine=DecisionEngine(manager))
    response = run.validate(ValidationRequest(question="q", answer="a"))
    assert [r.verifier_name for r in response.results] == ["a", "b", "c"]
    assert checkers[-1].calls == 0
    assert summary(response)["contributors"] == 3
    assert summary(response)["termination"] == "approved_early_stop"


@pytest.mark.parametrize("answer,passed,expected", [("4", True, "passed"), ("5", False, "failed")])
def test_campaign_actual_api_serializes_approved_rule_snapshot(monkeypatch, answer, passed, expected):
    """Real route/service/rule; other vote controlled, no live model or database."""
    from fastapi.testclient import TestClient
    from app.main import app
    from app.api import routes
    from app.services.validation_service import ValidationService
    from app.verifiers.rule_verifier import RuleVerifier
    run = connected([RuleVerifier(), MetadataChecker("generic", passed), MetadataChecker("later")],
                    hints=["arithmetic"])
    before = run.reputation_manager.export_state()
    monkeypatch.setattr(routes, "_validation_service", ValidationService(run))
    with TestClient(app) as client:
        response = client.post("/validate", json={"question": "What is 2 + 2?", "answer": answer})
    assert response.status_code == 200
    body = response.json()
    assert body["final_status"] == expected
    assert [r["verifier_name"] for r in body["results"]] == ["rule", "generic"]
    diagnostics = body["results"][-1]["metadata"]["multi_agent_verification.execution"]
    assert diagnostics["termination"] == "approved_early_stop"
    assert diagnostics["numerical_decision"]["score"] == body["final_score"]
    assert diagnostics["coverage"]["arithmetic"]["directional"] == ["rule"]
    assert run.reputation_manager.export_state() == before


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
    assert second.results[0].verifier_name == "evidence"

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
    assert response.final_status == "uncertain"
    assert orchestrator.validation_context(response.validation_id).decision.status == "failed"
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
    assert len(response.results) == 2
    assert by_name["rule"].calls == 1
    assert by_name["semantic"].calls == 1

    fresh = _named(score=0.95)
    fresh_by_name = {stub.name: stub for stub in fresh}
    held = ValidationOrchestrator(
        question_analyzer=FixedAnalyzer(QuestionAnalysis("general", "easy", 0.0)),
        verifier_selector=VerifierSelector(
            verifiers=fresh,
            difficulty_range={"easy": (3, 3), "medium": (2, 3), "hard": (3, 4)},
        ),
    )
    held_response = held.validate(ValidationRequest(question="q", answer="a"))
    assert len(held_response.results) == 3
    assert fresh_by_name["rule"].calls == 1
    assert fresh_by_name["semantic"].calls == 1
    assert fresh_by_name["evidence"].calls == 1


def test_orchestrator_uses_its_engine_and_keeps_the_stopped_decision():
    stubs = _named(score=0.95)
    by_name = {stub.name: stub for stub in stubs}
    manager = ReputationManager()
    engine = DecisionEngine(reputation_manager=manager)
    seen: dict = {}

    class RecordingStop(AdaptiveEarlyTermination):
        def should_terminate(self, results, analysis, min_verifiers=None, *, decision_engine=None):
            seen["engine"] = decision_engine
            seen["domain"] = analysis.domain
            return super().should_terminate(
                results,
                analysis,
                min_verifiers,
                decision_engine=decision_engine,
            )

    orchestrator = ValidationOrchestrator(
        question_analyzer=FixedAnalyzer(QuestionAnalysis("medical", "easy", 0.34)),
        verifier_selector=VerifierSelector(reputation_manager=manager, verifiers=stubs),
        decision_engine=engine,
        reputation_manager=manager,
        early_termination=RecordingStop(),
    )
    before = manager.export_state()
    response = orchestrator.validate(ValidationRequest(question="q", answer="a"))
    assert seen["engine"] is orchestrator.decision_engine
    assert seen["domain"] == "medical"
    assert by_name["rule"].calls == 1
    assert by_name["semantic"].calls == 1
    assert response.final_status == "passed"
    assert manager.export_state() == before
    applied = orchestrator.record_ground_truth(
        response.results,
        True,
        validation_id=response.validation_id,
    )
    assert applied == 2
    assert manager.observation_count("rule", "medical") == 1
    assert manager.observation_count("semantic", "medical") == 1
    assert manager.observation_count("evidence", "medical") == 0
    assert manager.observation_count("confidence", "medical") == 0


def test_response_uses_the_decision_from_before_a_reputation_change():
    stubs = _named(score=0.95)
    by_name = {stub.name: stub for stub in stubs}
    manager = ReputationManager()
    engine = DecisionEngine(reputation_manager=manager)
    seen: dict = {}

    class MutatingStop(AdaptiveEarlyTermination):
        def should_terminate(self, results, analysis, min_verifiers=None, *, decision_engine=None):
            seen["engine"] = decision_engine
            seen["domain"] = analysis.domain
            decision = super().should_terminate(
                results,
                analysis,
                min_verifiers,
                decision_engine=decision_engine,
            )
            if decision["terminate"]:
                seen["decision"] = decision["decision"]
                for _ in range(12):
                    manager.update_reputation("rule", "medical", False)
            return decision

    orchestrator = ValidationOrchestrator(
        question_analyzer=FixedAnalyzer(QuestionAnalysis("medical", "easy", 0.34)),
        verifier_selector=VerifierSelector(reputation_manager=manager, verifiers=stubs),
        decision_engine=engine,
        reputation_manager=manager,
        early_termination=MutatingStop(),
    )
    response = orchestrator.validate(ValidationRequest(question="q", answer="a"))
    captured = seen["decision"]
    assert orchestrator.validation_context(response.validation_id).decision is captured
    assert (response.final_status, response.final_score) == (captured.status, captured.score)
    revised_status, revised_score = engine.decide(response.results, domain="medical")
    assert (revised_status, revised_score) != (response.final_status, response.final_score)
    assert seen["engine"] is orchestrator.decision_engine
    assert seen["domain"] == "medical"
    assert by_name["rule"].calls == 1
    assert by_name["semantic"].calls == 1
    applied = orchestrator.record_ground_truth(
        response.results,
        True,
        validation_id=response.validation_id,
    )
    assert applied == 2
    assert manager.observation_count("rule", "medical") == 13
    assert manager.observation_count("semantic", "medical") == 1


def test_low_confidence_and_hard_questions_keep_running():
    easy = _named(score=0.55)
    easy_by_name = {stub.name: stub for stub in easy}
    easy_run = ValidationOrchestrator(
        question_analyzer=FixedAnalyzer(QuestionAnalysis("general", "easy", 0.34)),
        verifier_selector=VerifierSelector(verifiers=easy),
    )
    easy_response = easy_run.validate(ValidationRequest(question="q", answer="a"))
    assert len(easy_response.results) == 4
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
        "evidence",
        "rule",
        "semantic",
        "confidence",
    ]
    assert roles == ["vote", "abstention", "abstention", "abstention"]
    assert response.results[1].metadata["rule"] == "unsupported"
    assert "not a pass or a reject" in response.results[1].metadata["pipeline_note"]
    assert response.results[-1].metadata["pipeline_role"] == "abstention"
    assert response.final_status == "uncertain"
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
    semantic = StubVerifier("semantic", passed=False, score=0.95)
    orchestrator = ValidationOrchestrator(
        verifier_selector=VerifierSelector(verifiers=[rule, semantic, StubVerifier("confidence", score=0.95)]),
    )
    response = orchestrator.validate(ValidationRequest(question="What is 2+2?", answer="5"))
    assert len(response.results) == 2
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
    assert semantic.calls == 1


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
    assert applied == 2
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
    assert applied == 2
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
    assert orchestrator.record_ground_truth(clone, True, domain="general") == 2
    assert orchestrator.record_ground_truth(clone, True, domain="general") == 2
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
    assert orchestrator.record_ground_truth(response.results, True) == 2
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
    assert by_name["rule"].calls == 1
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
    assert [result.verifier_name for result in response.results] == ["evidence", "rule", "semantic", "confidence"]
    assert response.results[0].metadata["pipeline_role"] == "abstention"
    assert response.results[1].metadata["pipeline_role"] == "vote"
    assert semantic.calls == 1
    assert confidence.calls == 1
    assert response.final_status == "uncertain"


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


class MetadataChecker(StubVerifier):
    def __init__(self, name, passed=True, score=0.95, metadata=None):
        super().__init__(name, passed, score)
        self.metadata = metadata or {"decision": "SUPPORT" if passed else "REJECT"}

    def verify(self, question, answer, context=None):
        result = super().verify(question, answer, context)
        return result.model_copy(update={"metadata": dict(self.metadata)})


def factual_metadata(passed=True):
    decision = "SUPPORT" if passed else "REJECT"
    label = "entailment" if passed else "contradiction"
    return {
        "decision": decision, "nli_label": label, "unsure_reason": None,
        "claim_decisions": [{"claim": "Shakespeare wrote Hamlet", "decision": decision}],
        "supporting": [{"nli_label": label}] if passed else [],
        "contradicting": [] if passed else [{"nli_label": label}],
    }


def connected(checkers, *, hints=None, difficulty="easy", manager=None, mapping=None):
    manager = manager or ReputationManager()
    selector = VerifierSelector(
        verifiers=checkers, reputation_manager=manager, type_mapping=mapping,
        lambda_cost=0, lambda_latency=0, lambda_suitability=0,
    )
    return ValidationOrchestrator(
        question_analyzer=FixedAnalyzer(QuestionAnalysis(
            "general", difficulty, 0.1, verification_types=hints,
        )), verifier_selector=selector, decision_engine=DecisionEngine(manager),
    )


def summary(response):
    return response.results[-1].metadata["multi_agent_verification.execution"]


def test_low_reputation_factual_evidence_is_reached_and_preserved():
    manager = ReputationManager()
    for _ in range(3):
        manager.update_reputation("evidence", "general", False)
    evidence = MetadataChecker("evidence", False, 1, factual_metadata(False))
    run = connected([MetadataChecker("semantic"), MetadataChecker("confidence"), evidence],
                    hints=["direct_fact"], manager=manager)
    before = manager.export_state()
    response = run.validate(ValidationRequest(question="Who wrote Hamlet?", answer="Marlowe"))
    assert [r.verifier_name for r in response.results] == ["semantic", "confidence", "evidence"]
    assert summary(response)["coverage"]["direct_fact"]["directional"] == ["evidence"]
    assert summary(response)["contributors"] == 1
    assert response.final_status == "uncertain" and response.final_score == 1
    assert manager.export_state() == before
    assert run.record_ground_truth(response.results, False, validation_id=response.validation_id) == 3
    assert run.record_ground_truth(response.results, False, validation_id=response.validation_id) == 0
    assert manager.observation_count("evidence", "general") == 4


@pytest.mark.parametrize("metadata,score,state", [
    ({"decision": "UNSURE", "nli_label": "neutral", "unsure_reason": "conflict"}, 1, "abstained"),
    ({"decision": "SUPPORT"}, .95, "unproven"),
    (factual_metadata(), 0, "zero_confidence"),
])
def test_generic_agreement_cannot_replace_factual_coverage(metadata, score, state):
    checker = MetadataChecker("evidence", metadata.get("decision") != "UNSURE", score, metadata)
    run = connected([MetadataChecker("semantic"), MetadataChecker("confidence"), checker],
                    hints=["direct_fact"])
    response = run.validate(ValidationRequest(question="Who wrote Hamlet?", answer="Shakespeare"))
    assert len(response.results) == 3
    assert response.final_status == "uncertain" and response.final_score > .55
    coverage = summary(response)["coverage"]["direct_fact"]
    assert coverage["attempts"] == [{"verifier": "evidence", "state": state}]
    assert coverage["directional"] == []


@pytest.mark.parametrize("answer,passed", [("4", True), ("5", False), ("not a number", False)])
def test_actual_arithmetic_rule_contract_covers_valid_and_invalid_answers(answer, passed):
    from app.verifiers.rule_verifier import RuleVerifier
    run = connected([RuleVerifier(), MetadataChecker("semantic", passed), MetadataChecker("confidence")],
                    hints=["arithmetic"])
    response = run.validate(ValidationRequest(question="What is 2 + 2?", answer=answer))
    assert len(response.results) == 2
    rule = response.results[0]
    assert rule.score == (1 if passed else 0)
    assert rule.metadata["rule_kind"] == "factual"
    assert response.final_status == ("passed" if passed else "failed")
    assert summary(response)["coverage"]["arithmetic"]["directional"] == ["rule"]
    assert summary(response)["contributors"] == 2
    assert summary(response)["termination"] == "approved_early_stop"


@pytest.mark.parametrize("second_score,second_passed", [(1, False), (0, True)])
def test_disagreement_and_zero_confidence_continue_past_two_results(second_score, second_passed):
    run = connected([MetadataChecker("first", score=1),
                     MetadataChecker("second", second_passed, second_score),
                     MetadataChecker("third", score=.95)])
    response = run.validate(ValidationRequest(question="q", answer="a"))
    assert len(response.results) == 3
    if second_score == 0:
        assert summary(response)["contributors"] == 2
        assert response.results[1].passed and summary(response)["termination"] == "approved_early_stop"
    else:
        assert summary(response)["termination"] == "candidate_exhaustion"
        assert response.final_status == "uncertain"


def test_exhaustion_disagreement_does_not_override_numerically_decisive_status():
    run = connected([MetadataChecker("a", score=1), MetadataChecker("b", score=1),
                     MetadataChecker("c", False, .01)], difficulty="hard")
    response = run.validate(ValidationRequest(question="q", answer="a"))
    assert len(response.results) == 3
    assert response.final_status == "passed"
    assert summary(response)["termination"] == "candidate_exhaustion"


def test_actual_structural_rejection_is_not_a_contributor():
    from app.verifiers.rule_verifier import RuleVerifier
    run = connected([RuleVerifier(), MetadataChecker("semantic", False)])
    response = run.validate(ValidationRequest(question="Provide an email address.", answer="invalid"))
    assert response.results[0].metadata["rule_kind"] == "structural"
    assert response.results[0].passed is False
    assert summary(response)["contributors"] == 1
    assert summary(response)["numerical_decision"]["status"] == "failed"
    assert response.final_status == "uncertain" and response.final_score < -.55


@pytest.mark.parametrize("checkers,hints", [([], ["direct_fact"]),
    ([MetadataChecker("first"), MetadataChecker("second")], ["direct_fact"]),
    ([MetadataChecker("first")], [])])
def test_missing_coverage_or_contributors_guard_exhaustion(checkers, hints):
    run = connected(checkers, hints=hints)
    response = run.validate(ValidationRequest(question="q", answer="a"))
    assert response.final_status == "uncertain"
    captured = run.validation_context(response.validation_id)
    assert captured.run_summary["termination"] == "candidate_exhaustion"
    if hints:
        assert not captured.run_summary["coverage"]["direct_fact"]["available"]
    assert response.final_score == captured.decision.score
    if not checkers:
        assert response.results == [] and response.final_score == 0


@pytest.mark.parametrize("metadata,qualified", [(factual_metadata(), True), ({"decision": "SUPPORT"}, False)])
def test_custom_mapping_is_only_a_candidate_declaration(metadata, qualified):
    checker = MetadataChecker("custom", metadata=metadata)
    run = connected([MetadataChecker("generic"), checker, MetadataChecker("later")],
                    hints=["direct_fact"], mapping={"direct_fact": "custom"})
    response = run.validate(ValidationRequest(question="Who wrote Hamlet?", answer="Shakespeare"))
    assert len(response.results) == (2 if qualified else 3)
    assert response.final_status == ("passed" if qualified else "uncertain")
    assert summary(response)["coverage"]["direct_fact"]["available"]
    assert bool(summary(response)["coverage"]["direct_fact"]["directional"]) == qualified


def test_metadata_contract_can_qualify_custom_checker_without_mapping():
    run = connected([MetadataChecker("generic"), MetadataChecker("custom", metadata=factual_metadata()),
                     MetadataChecker("later")], hints=["direct_fact"])
    response = run.validate(ValidationRequest(question="q", answer="a"))
    assert len(response.results) == 2 and response.final_status == "passed"
    assert summary(response)["coverage"]["direct_fact"]["directional"] == ["custom"]


def test_run_summary_is_detached_and_reserved_collision_is_rejected():
    from app.orchestration.validation_orchestrator import RUN_SUMMARY_KEY
    run = connected([MetadataChecker("first"), MetadataChecker("second")])
    response = run.validate(ValidationRequest(question="q", answer="a"))
    original = run.validation_context(response.validation_id)
    summary(response)["contributors"] = 999
    assert run.validation_context(response.validation_id).run_summary["contributors"] == 2
    assert original.results[-1].metadata[RUN_SUMMARY_KEY]["contributors"] == 2
    collision = connected([MetadataChecker("first"), MetadataChecker("second", metadata={
        "decision": "SUPPORT", RUN_SUMMARY_KEY: {"owned": True}})])
    with pytest.raises(ValueError, match="reserved metadata"):
        collision.validate(ValidationRequest(question="q", answer="a"))


def test_unexpected_runtime_failure_remains_visible():
    class Broken(MetadataChecker):
        def verify(self, *args):
            raise RuntimeError("programming failure")
    run = connected([MetadataChecker("first"), Broken("broken"), MetadataChecker("later")])
    with pytest.raises(RuntimeError, match="programming failure"):
        run.validate(ValidationRequest(question="q", answer="a"))
    assert run._contexts == {}


def test_snapshot_contributor_helper_reads_no_reputations():
    manager = ReputationManager()
    engine = DecisionEngine(manager)
    results = [VerificationResult(verifier_name=name, score=.95, passed=True,
                                  metadata={"decision": "SUPPORT"}) for name in ["a", "b"]]
    detail = engine.decide_detailed(results, domain="general")
    manager.update_reputation("a", "general", False)
    assert AdaptiveEarlyTermination.contributor_count(detail, results) == 2
    with pytest.raises(ValueError, match="snapshot prefix"):
        AdaptiveEarlyTermination.contributor_count(detail, results[:1])


@pytest.mark.parametrize("probabilities,expected", [
    ({"entailment": .95, "neutral": .04, "contradiction": .01}, "passed"),
    ({"contradiction": .95, "neutral": .04, "entailment": .01}, "failed"),
    ({"neutral": .95, "entailment": .04, "contradiction": .01}, "uncertain"),
])
def test_actual_evidence_output_contract_is_consumed_without_models(probabilities, expected):
    from app.verifiers.evidence_verifier import EvidenceVerifier
    from tests.test_evidence_verifier import FakeRetriever, FakeNLI, chunk
    evidence = EvidenceVerifier(
        retriever=FakeRetriever([chunk("Hamlet", "Shakespeare wrote Hamlet.", .9)]),
        nli=FakeNLI({"Shakespeare": probabilities}),
    )
    run = connected([MetadataChecker("generic", expected != "failed"), evidence,
                     MetadataChecker("later", expected != "failed")], hints=["direct_fact"])
    response = run.validate(ValidationRequest(question="Who wrote Hamlet?", answer="Shakespeare"))
    assert response.final_status == expected
    assert len(response.results) == (3 if expected == "uncertain" else 2)
    assert bool(summary(response)["coverage"]["direct_fact"]["directional"]) == (expected != "uncertain")


def test_actual_conflicting_evidence_cannot_cover_factual_request():
    from app.verifiers.evidence_verifier import EvidenceVerifier
    from tests.test_evidence_verifier import FakeRetriever, FakeNLI, chunk, ENTAILS, CONTRADICTS
    evidence = EvidenceVerifier(
        retriever=FakeRetriever([chunk("Support", "Shakespeare wrote Hamlet.", .9),
                                chunk("Reject", "Marlowe wrote Hamlet.", .9, 1)]),
        nli=FakeNLI({"Shakespeare": ENTAILS, "Marlowe": CONTRADICTS}),
    )
    run = connected([MetadataChecker("generic"), evidence, MetadataChecker("later")], hints=["direct_fact"])
    response = run.validate(ValidationRequest(question="Who wrote Hamlet?", answer="Shakespeare"))
    assert len(response.results) == 3 and response.final_status == "uncertain"
    assert response.results[1].metadata["unsure_reason"] == "conflict"
    assert summary(response)["coverage"]["direct_fact"]["directional"] == []


def test_both_factual_capabilities_must_be_completed_separately():
    # Both capabilities are needed; completing one cannot terminate the run.
    from app.verifiers.rule_verifier import RuleVerifier
    run = connected([MetadataChecker("generic"), MetadataChecker("evidence", metadata=factual_metadata()),
                     RuleVerifier()], hints=["direct_fact", "arithmetic"])
    response = run.validate(ValidationRequest(question="What is 2 + 2?", answer="4"))
    assert len(response.results) == 3 and response.final_status == "passed"
    assert summary(response)["coverage"]["direct_fact"]["directional"] == ["evidence"]
    assert summary(response)["coverage"]["arithmetic"]["directional"] == ["rule"]


@pytest.mark.parametrize("rule", [["arithmetic_addition"], {"rule": "arithmetic_addition"}])
@pytest.mark.parametrize("mapped", [True, False])
def test_nonstring_rule_metadata_does_not_authorize_arithmetic_coverage(rule, mapped):
    checker = MetadataChecker("custom", metadata={
        "decision": "SUPPORT", "rule_kind": "factual", "rule": rule,
    })
    run = connected([MetadataChecker("generic"), checker, MetadataChecker("later")],
                    hints=["arithmetic"], mapping={"arithmetic": "custom"} if mapped else None)
    response = run.validate(ValidationRequest(question="What is 2 + 2?", answer="4"))
    assert len(response.results) == 3
    assert response.final_status == "uncertain" and response.final_score == .95
    coverage = summary(response)["coverage"]["arithmetic"]
    assert coverage["directional"] == []
    assert summary(response)["missing_coverage"] == ["arithmetic"]
    assert coverage["available"] is mapped
    assert coverage["attempts"] == ([{"verifier": "custom", "state": "unproven"}] if mapped else [])
    # Ancillary metadata does not change the valid directional vote or its score.
    vote = summary(response)["numerical_decision"]["votes"][1]
    assert vote["passed"] and not vote["abstained"]
    assert vote["confidence"] == .95 and vote["contribution"] == .95


@pytest.mark.parametrize("rule", [["arithmetic_addition"], {"rule": "arithmetic_addition"}])
def test_actual_arithmetic_rule_qualifies_after_malformed_generic_metadata(rule):
    from app.verifiers.rule_verifier import RuleVerifier
    generic = MetadataChecker("generic", metadata={"decision": "SUPPORT", "rule": rule})
    later = MetadataChecker("later")
    run = connected([generic, RuleVerifier(), later], hints=["arithmetic"])
    response = run.validate(ValidationRequest(question="What is 2 + 2?", answer="4"))
    assert [r.verifier_name for r in response.results] == ["generic", "rule"]
    assert response.final_status == "passed" and response.final_score == .975
    assert summary(response)["coverage"]["arithmetic"]["attempts"] == [
        {"verifier": "rule", "state": "directional"},
    ]
    assert summary(response)["coverage"]["arithmetic"]["directional"] == ["rule"]
    assert summary(response)["termination"] == "approved_early_stop"
    assert later.calls == 0
