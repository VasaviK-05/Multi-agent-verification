"""Isolated tests for VerifierSelector."""

from app.analysis.question_analyzer import QuestionAnalysis
from app.models.schemas import VerificationResult
from app.reputation.reputation_manager import ReputationManager
from app.selection.verifier_selector import (
    DEFAULT_DIFFICULTY_RANGE,
    VerifierSelector,
)
from app.verifiers.base_verifier import BaseVerifier


class StubVerifier(BaseVerifier):
    def __init__(self, name: str) -> None:
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    def verify(self, question: str, answer: str, context: str | None = None) -> VerificationResult:
        return VerificationResult(
            verifier_name=self._name,
            score=0.5,
            passed=True,
            reasoning="stub",
        )


def _stubs() -> list[StubVerifier]:
    return [StubVerifier(name) for name in ("semantic", "evidence", "rule", "confidence")]


def test_select_returns_base_verifiers():
    selector = VerifierSelector()
    selected = selector.select(
        QuestionAnalysis(domain="general", difficulty="easy", difficulty_score=0.1)
    )
    assert selected
    assert all(isinstance(v, BaseVerifier) for v in selected)


def test_hard_selects_more_than_easy():
    selector = VerifierSelector(verifiers=_stubs())
    easy = selector.select(
        QuestionAnalysis(domain="general", difficulty="easy", difficulty_score=0.1)
    )
    hard = selector.select(
        QuestionAnalysis(domain="general", difficulty="hard", difficulty_score=0.9)
    )
    assert len(easy) == DEFAULT_DIFFICULTY_RANGE["easy"][0]
    assert len(hard) == DEFAULT_DIFFICULTY_RANGE["hard"][1]
    assert len(hard) > len(easy)


def test_configured_range_endpoints_are_reachable():
    selector = VerifierSelector(verifiers=[])
    assert selector.target_count(QuestionAnalysis("general", "easy", 0.0)) == 1
    assert selector.target_count(QuestionAnalysis("general", "easy", 0.34)) == 2
    assert selector.target_count(QuestionAnalysis("general", "medium", 0.35)) == 2
    assert selector.target_count(QuestionAnalysis("general", "medium", 0.64)) == 3
    assert selector.target_count(QuestionAnalysis("general", "hard", 0.65)) == 3
    assert selector.target_count(QuestionAnalysis("general", "hard", 1.0)) == 4


def test_cost_and_latency_reduce_utility_at_equal_reputation():
    selector = VerifierSelector(verifiers=[])
    assert selector.utility("rule", "general") > selector.utility("evidence", "general")


def test_explicit_estimates_can_change_the_first_verifier():
    profiles = {
        "semantic": {"cost": 1.0, "latency": 1.0},
        "evidence": {"cost": 0.0, "latency": 0.0},
        "rule": {"cost": 1.0, "latency": 1.0},
        "confidence": {"cost": 1.0, "latency": 1.0},
    }
    selector = VerifierSelector(verifiers=_stubs(), verifier_profiles=profiles)
    selected = selector.select(QuestionAnalysis("general", "easy", 0.1))
    assert selected[0].name == "evidence"


def test_domain_reputation_outranks_a_cheaper_verifier():
    manager = ReputationManager()
    for _ in range(3):
        manager.update_reputation("evidence", "medical", True)
    selector = VerifierSelector(reputation_manager=manager, verifiers=_stubs())
    medical = selector.select(QuestionAnalysis("medical", "easy", 0.1))
    general = selector.select(QuestionAnalysis("general", "easy", 0.1))
    assert medical[0].name == "evidence"
    assert general[0].name == "rule"


def test_higher_reputation_ranks_first():
    manager = ReputationManager()
    manager.update_reputation("rule", "general", True)
    manager.update_reputation("rule", "general", True)
    manager.update_reputation("evidence", "general", False)
    selector = VerifierSelector(reputation_manager=manager)
    selected = selector.select(
        QuestionAnalysis(domain="general", difficulty="easy", difficulty_score=0.1)
    )
    assert selected[0].name == "rule"
