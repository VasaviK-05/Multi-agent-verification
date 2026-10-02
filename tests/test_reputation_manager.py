"""Isolated tests for ReputationManager."""

import math

import pytest

from app.decision.decision_engine import DecisionEngine
from app.models.schemas import VerificationResult
from app.reputation.reputation_manager import FeedbackEvent, FeedbackReceipt, ReputationManager
from app.selection.verifier_selector import VerifierSelector
from app.verifiers.base_verifier import BaseVerifier


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


def _result(name: str, passed: bool, *, abstain: bool = False) -> VerificationResult:
    if abstain:
        return VerificationResult(
            verifier_name=name,
            score=0.0,
            passed=False,
            reasoning="No reference context provided for semantic comparison.",
            metadata={"rule": "unsupported"} if name == "rule" else None,
        )
    return VerificationResult(
        verifier_name=name,
        score=1.0 if passed else 0.2,
        passed=passed,
        reasoning="vote",
        metadata={"nli_label": "entailment" if passed else "contradiction"},
    )


def _event(validation_id: str, name: str, passed: bool, label: bool, domain: str = "medical") -> FeedbackEvent:
    return FeedbackEvent(
        validation_id=validation_id,
        domain=domain,
        answer_is_correct=label,
        results=(_result(name, passed),),
    )


def test_all_four_vote_and_label_combinations():
    manager = ReputationManager()
    cases = (
        ("pass-right", True, True, True),
        ("pass-wrong", True, False, False),
        ("reject-right", False, True, False),
        ("reject-wrong", False, False, True),
    )
    for validation_id, passed, label, succeeded in cases:
        manager.record_feedback(_event(validation_id, validation_id, passed, label))
        stats = manager.statistics(validation_id, "medical")
        assert stats.observation_count == 1
        assert stats.cold_start is False
        if succeeded:
            assert stats.successes == 1 and stats.failures == 0
            assert stats.posterior_mean > 0.5
        else:
            assert stats.successes == 0 and stats.failures == 1
            assert stats.posterior_mean < 0.5
        assert stats.posterior_variance == pytest.approx(
            stats.alpha * stats.beta / ((stats.alpha + stats.beta) ** 2 * (stats.alpha + stats.beta + 1))
        )


def test_counts_stay_exact_with_a_large_prior():
    manager = ReputationManager(prior_alpha=1e16, prior_beta=1.0)
    manager.update_reputation("rule", "general", True)
    stats = manager.statistics("rule", "general")
    assert stats.successes == 1
    assert stats.failures == 0
    assert stats.observation_count == 1
    assert stats.alpha == pytest.approx(1e16 + 1)
    assert manager.is_cold_start("rule", "technical")


def test_invalid_priors_identifiers_and_labels_do_not_learn():
    for kwargs in (
        {"prior_alpha": math.nan},
        {"prior_beta": math.inf},
        {"prior_alpha": 0},
        {"prior_alpha": -1},
        {"prior_alpha": True},
        {"prior_beta": "1"},
    ):
        with pytest.raises(ValueError):
            ReputationManager(**kwargs)
    manager = ReputationManager()
    with pytest.raises(ValueError):
        manager.get_reputation(" ", "general")
    with pytest.raises(ValueError):
        manager.update_reputation("rule", "", True)
    with pytest.raises(TypeError):
        manager.update_from_ground_truth("rule", "general", True, "passed")  # type: ignore[arg-type]
    assert manager.observation_count("rule", "general") == 0


def test_abstentions_and_missing_verifiers_add_no_observation():
    manager = ReputationManager()
    receipt = manager.record_feedback(
        FeedbackEvent(
            validation_id="run-1",
            domain="general",
            answer_is_correct=True,
            results=(
                _result("rule", True, abstain=True),
                _result("semantic", True),
            ),
        )
    )
    assert receipt.observations_applied == 1
    assert manager.is_cold_start("rule", "general")
    assert manager.observation_count("semantic", "general") == 1
    assert manager.is_cold_start("evidence", "general")


def test_duplicate_feedback_is_a_noop_and_conflict_does_not_change_state():
    manager = ReputationManager()
    event = _event("run-1", "semantic", True, True)
    assert manager.record_feedback(event).applied is True
    replay = manager.record_feedback(event)
    assert replay.applied is False
    assert replay.observations_applied == 0
    assert manager.observation_count("semantic", "medical") == 1
    conflict = FeedbackEvent(
        validation_id="run-1",
        domain="medical",
        answer_is_correct=False,
        results=event.results,
    )
    with pytest.raises(ValueError, match="correction"):
        manager.record_feedback(conflict)
    assert manager.statistics("semantic", "medical").successes == 1
    assert manager.statistics("semantic", "medical").failures == 0


def test_batch_is_atomic_and_duplicate_names_conflict():
    manager = ReputationManager()
    valid = _event("ok", "semantic", True, True)
    invalid = FeedbackEvent(
        validation_id="bad",
        domain="medical",
        answer_is_correct="passed",  # type: ignore[arg-type]
        results=valid.results,
    )
    with pytest.raises(TypeError):
        manager.record_feedback_batch((valid, invalid))
    assert manager.is_cold_start("semantic", "medical")
    duplicate = FeedbackEvent(
        validation_id="dup",
        domain="general",
        answer_is_correct=True,
        results=(_result("rule", True), _result("rule", False)),
    )
    with pytest.raises(ValueError, match="conflicting duplicate"):
        manager.record_feedback(duplicate)
    assert manager.observation_count("rule", "general") == 0


def test_export_restore_round_trip_and_malformed_restore_is_unchanged():
    manager = ReputationManager(prior_alpha=8.0, prior_beta=2.0)
    manager.record_feedback(_event("run-1", "evidence", False, False, domain="technical"))
    manager.update_reputation("rule", "general", False)
    payload = manager.export_state()
    restored = ReputationManager()
    restored.restore_state(payload)
    assert restored.prior_alpha == 8.0
    assert restored.prior_beta == 2.0
    assert restored.statistics("evidence", "technical") == manager.statistics("evidence", "technical")
    assert restored.observation_count("rule", "general") == 1
    replay = restored.record_feedback(_event("run-1", "evidence", False, False, domain="technical"))
    assert replay.applied is False
    assert restored.observation_count("evidence", "technical") == 1
    before = restored.export_state()
    broken = restored.export_state()
    broken["pairs"][0]["successes"] = -1
    with pytest.raises(ValueError):
        restored.restore_state(broken)
    broken = restored.export_state()
    broken["feedback"] = []
    broken["pairs"] = []
    broken["schema_version"] = 2
    with pytest.raises(ValueError):
        restored.restore_state(broken)
    assert restored.export_state() == before


def test_selector_and_decision_read_feedback_updates():
    manager = ReputationManager()
    manager.record_feedback(_event("run-1", "evidence", True, False, domain="medical"))

    class Stub(BaseVerifier):
        def __init__(self, name: str) -> None:
            self._name = name

        @property
        def name(self) -> str:
            return self._name

        def verify(self, question: str, answer: str, context: str | None = None) -> VerificationResult:
            return _result(self._name, True)

    selector = VerifierSelector(
        reputation_manager=manager,
        verifiers=[Stub(name) for name in ("semantic", "evidence", "rule", "confidence")],
    )
    from app.analysis.question_analyzer import QuestionAnalysis

    ranking = [item.verifier_name for item in selector.explain_ranking(QuestionAnalysis("medical", "easy", 0.1))]
    assert ranking[0] != "evidence"
    engine = DecisionEngine(reputation_manager=manager)
    status, score = engine.decide([_result("evidence", True)], domain="medical")
    assert status == "failed"
    assert score < 0
    assert manager.observation_count("evidence", "medical") == 1


def test_extreme_priors_stay_finite_and_unsafe_counts_do_not_restore():
    for prior in (1e308, 1e200, 1e-300):
        manager = ReputationManager(prior_alpha=prior, prior_beta=prior)
        stats = manager.statistics("rule", "general")
        assert stats.posterior_mean == pytest.approx(0.5)
        assert math.isfinite(stats.posterior_variance)
        assert manager.get_reputation("rule", "general") == 0.5
    normal = ReputationManager()
    normal.update_reputation("rule", "general", True)
    assert normal.statistics("rule", "general").posterior_variance == pytest.approx(1 / 18)
    before = normal.export_state()
    huge = normal.export_state()
    huge["pairs"][0]["successes"] = 10**400
    with pytest.raises(ValueError, match="represented safely"):
        normal.restore_state(huge)
    for version in (True, 1.0, "1", 2):
        broken = normal.export_state()
        broken["schema_version"] = version
        with pytest.raises(ValueError, match="schema_version"):
            normal.restore_state(broken)
    assert normal.export_state() == before


def test_concurrent_feedback_keeps_each_committed_event():
    import threading

    manager = ReputationManager()
    first = _event("one", "semantic", True, True)
    second = _event("two", "rule", False, False, domain="technical")
    barrier = threading.Barrier(2)

    def apply(event: FeedbackEvent) -> None:
        barrier.wait()
        manager.record_feedback(event)

    threads = [
        threading.Thread(target=apply, args=(first,)),
        threading.Thread(target=apply, args=(second,)),
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert manager.observation_count("semantic", "medical") == 1
    assert manager.observation_count("rule", "technical") == 1


def test_concurrent_replay_applies_once_and_conflict_preserves_state():
    import threading

    manager = ReputationManager()
    event = _event("run-1", "semantic", True, True)
    barrier = threading.Barrier(2)
    receipts: list[FeedbackReceipt] = []

    def replay() -> None:
        barrier.wait()
        receipts.append(manager.record_feedback(event))

    threads = [threading.Thread(target=replay), threading.Thread(target=replay)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert manager.observation_count("semantic", "medical") == 1
    assert sum(receipt.applied for receipt in receipts) == 1

    conflict = FeedbackEvent(
        validation_id="run-1",
        domain="medical",
        answer_is_correct=False,
        results=event.results,
    )
    extra = _event("run-2", "rule", True, True, domain="general")
    barrier = threading.Barrier(2)
    errors: list[BaseException] = []

    def send_conflict() -> None:
        barrier.wait()
        try:
            manager.record_feedback(conflict)
        except ValueError as exc:
            errors.append(exc)

    def send_extra() -> None:
        barrier.wait()
        manager.record_feedback(extra)

    threads = [
        threading.Thread(target=send_conflict),
        threading.Thread(target=send_extra),
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert errors
    assert manager.statistics("semantic", "medical").successes == 1
    assert manager.statistics("semantic", "medical").failures == 0
    assert manager.observation_count("rule", "general") == 1


def _state_at_exact_boundary() -> ReputationManager:
    manager = ReputationManager()
    payload = manager.export_state()
    payload["pairs"] = [
        {
            "verifier_name": "semantic",
            "domain": "general",
            "successes": 1,
            "failures": 0,
        },
        {
            "verifier_name": "rule",
            "domain": "general",
            "successes": 2**53,
            "failures": 0,
        },
    ]
    manager.restore_state(payload)
    return manager


def test_legacy_update_stops_at_the_representable_boundary():
    manager = _state_at_exact_boundary()
    before = manager.export_state()
    with pytest.raises(ValueError, match="represented safely"):
        manager.update_reputation("rule", "general", True)
    assert manager.export_state() == before
    manager.get_reputation("rule", "general")
    manager.update_reputation("semantic", "general", True)
    restored = ReputationManager()
    restored.restore_state(manager.export_state())
    assert restored.observation_count("rule", "general") == 2**53
    assert restored.observation_count("semantic", "general") == 2
    assert restored.get_reputation("semantic", "general") == manager.get_reputation(
        "semantic", "general"
    )


def test_unscoped_update_rolls_back_when_a_later_pair_is_not_representable():
    manager = _state_at_exact_boundary()
    before = manager.export_state()
    with pytest.raises(ValueError, match="represented safely"):
        manager.record_unscoped_ground_truth(
            "general",
            [_result("semantic", True), _result("rule", True)],
            True,
        )
    assert manager.export_state() == before
    assert manager.observation_count("semantic", "general") == 1
    assert manager.observation_count("rule", "general") == 2**53


def test_feedback_batch_does_not_consume_ids_when_a_later_pair_fails():
    manager = _state_at_exact_boundary()
    before = manager.export_state()
    with pytest.raises(ValueError, match="represented safely"):
        manager.record_feedback_batch(
            (
                _event("safe-id", "semantic", True, True, domain="general"),
                _event("blocked-id", "rule", True, True, domain="general"),
            )
        )
    assert manager.export_state() == before
    stored_ids = {item["validation_id"] for item in manager.export_state()["feedback"]}
    assert "safe-id" not in stored_ids
    assert "blocked-id" not in stored_ids
    assert manager.observation_count("semantic", "general") == 1
    assert manager.observation_count("rule", "general") == 2**53


def test_statistics_batch_is_one_locked_read():
    import threading

    manager = ReputationManager()
    manager.update_reputation("semantic", "general", True)
    entered = threading.Event()
    release = threading.Event()
    original = manager._statistics_unlocked
    errors: list[BaseException] = []

    def wrapped(verifier_name: str, domain: str):
        stats = original(verifier_name, domain)
        if verifier_name == "semantic":
            entered.set()
            if not release.wait(5):
                raise TimeoutError("batch reader was not released")
        return stats

    manager._statistics_unlocked = wrapped
    outcome: dict = {}

    def read() -> None:
        try:
            outcome["stats"] = manager.statistics_batch(
                (("semantic", "general"), ("rule", "general"))
            )
        except BaseException as exc:
            errors.append(exc)

    reader = threading.Thread(target=read)
    held = False
    try:
        reader.start()
        assert entered.wait(5)
        held = manager._lock.acquire(blocking=False)
        assert held is False
        release.set()
        reader.join(5)
        assert not reader.is_alive()
        assert errors == []
        snapshot = outcome["stats"]
        assert snapshot[0].successes == 1
        assert snapshot[1].observation_count == 0
        assert snapshot[0] is not manager.statistics("semantic", "general")
        held = manager._lock.acquire(blocking=False)
        assert held is True
        manager._lock.release()
        held = False
        manager.update_reputation("semantic", "general", True)
        assert snapshot[0].successes == 1
        assert manager.observation_count("semantic", "general") == 2
        before = manager.export_state()
        with pytest.raises(TypeError):
            manager.statistics_batch("semantic")  # type: ignore[arg-type]
        with pytest.raises(TypeError):
            manager.statistics_batch((("semantic",),))  # type: ignore[arg-type]
        with pytest.raises(ValueError):
            manager.statistics_batch((("", "general"),))
        assert manager.export_state() == before
    finally:
        release.set()
        if reader.is_alive():
            reader.join(5)
        if held:
            manager._lock.release()


def test_status_string_is_not_a_label():
    manager = ReputationManager()
    try:
        manager.update_from_ground_truth("semantic", "general", True, "passed")  # type: ignore[arg-type]
        raised = False
    except TypeError:
        raised = True
    assert raised
    assert manager.observation_count("semantic", "general") == 0
