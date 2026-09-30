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
    assert manager.is_cold_start("confidence", "technical")


def test_cold_start_is_per_domain_and_has_no_observations():
    manager = ReputationManager()
    assert manager.get_reputation("semantic", "general") == 0.5
    assert manager.is_cold_start("semantic", "general")
    assert manager.observation_count("semantic", "general") == 0
    manager.update_from_ground_truth("semantic", "medical", True, True)
    assert manager.is_cold_start("semantic", "general")
    assert not manager.is_cold_start("semantic", "medical")


def test_agreement_with_a_negative_label_raises_reputation():
    manager = ReputationManager()
    manager.update_from_ground_truth(
        "semantic",
        "medical",
        verifier_passed=False,
        answer_is_correct=False,
    )
    assert manager.get_reputation("semantic", "medical") > 0.5


def test_a_pass_on_a_wrong_answer_lowers_reputation():
    manager = ReputationManager()
    manager.update_from_ground_truth(
        "semantic",
        "medical",
        verifier_passed=True,
        answer_is_correct=False,
    )
    assert manager.get_reputation("semantic", "medical") < 0.5
    assert manager.is_cold_start("semantic", "general")


def test_prediction_source_does_not_learn():
    manager = ReputationManager()
    before = manager.get_reputation("semantic", "general")
    try:
        manager.update_reputation("semantic", "general", True, source="prediction")
        raised = False
    except ValueError:
        raised = True
    assert raised
    assert manager.get_reputation("semantic", "general") == before
    assert manager.observation_count("semantic", "general") == 0


def test_status_string_is_not_a_label():
    manager = ReputationManager()
    try:
        manager.update_from_ground_truth("semantic", "general", True, "passed")  # type: ignore[arg-type]
        raised = False
    except TypeError:
        raised = True
    assert raised
    assert manager.observation_count("semantic", "general") == 0
