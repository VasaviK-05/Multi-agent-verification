"""Isolated tests for VerifierSelector."""

from app.analysis.question_analyzer import QuestionAnalysis
from app.reputation.reputation_manager import ReputationManager
from app.selection.verifier_selector import VerifierSelector
from app.verifiers.base_verifier import BaseVerifier


def test_select_returns_base_verifiers():
    selector = VerifierSelector()
    selected = selector.select(
        QuestionAnalysis(domain="general", difficulty="easy", difficulty_score=0.1)
    )
    assert selected
    assert all(isinstance(v, BaseVerifier) for v in selected)


def test_hard_selects_more_than_easy():
    selector = VerifierSelector()
    easy = selector.select(
        QuestionAnalysis(domain="general", difficulty="easy", difficulty_score=0.1)
    )
    hard = selector.select(
        QuestionAnalysis(domain="general", difficulty="hard", difficulty_score=0.9)
    )
    assert len(hard) > len(easy)


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
