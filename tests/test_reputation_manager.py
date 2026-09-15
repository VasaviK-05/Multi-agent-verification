"""Isolated tests for ReputationManager."""

from app.reputation.reputation_manager import ReputationManager


def test_prior_reputation_is_one_half():
    manager = ReputationManager()
    assert manager.get_reputation("semantic", "general") == 0.5


def test_success_increases_reputation():
    manager = ReputationManager()
    before = manager.get_reputation("semantic", "general")
    manager.update_reputation("semantic", "general", True)
    after = manager.get_reputation("semantic", "general")
    assert after > before


def test_failure_decreases_reputation():
    manager = ReputationManager()
    before = manager.get_reputation("evidence", "medical")
    manager.update_reputation("evidence", "medical", False)
    after = manager.get_reputation("evidence", "medical")
    assert after < before


def test_domains_are_independent():
    manager = ReputationManager()
    manager.update_reputation("rule", "medical", True)
    assert manager.get_reputation("rule", "medical") > manager.get_reputation(
        "rule", "general"
    )


def test_configurable_priors():
    manager = ReputationManager(prior_alpha=8.0, prior_beta=2.0)
    assert manager.get_reputation("confidence", "technical") == 0.8
