
from fastapi.testclient import TestClient

from app.main import app
from app.api import feedback_routes
from app.orchestration.validation_orchestrator import ValidationOrchestrator
from app.reputation.reputation_manager import ReputationManager

client = TestClient(app)


def test_conflicting_feedback_returns_409(monkeypatch):
    def reject_conflicting_feedback(**kwargs):
        raise ValueError(
            "Conflicting feedback already exists for this validation."
        )

    monkeypatch.setattr(
        feedback_routes,
        "save_feedback",
        reject_conflicting_feedback,
    )

    response = client.post(
        "/feedback",
        json={
            "validation_id": "test-validation-conflict",
            "is_correct": False,
            "comment": None,
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "Conflicting feedback already exists for this validation."
    )


def test_conflicting_feedback_rolls_back_without_inserting(monkeypatch):
    from app.database import feedback_repository

    class FakeCursor:
        def __init__(self):
            self.insert_called = False
            self.closed = False

        def execute(self, query, params=None):
            if "SELECT id, validation_id" in query:
                return
            if "INSERT INTO feedback" in query:
                self.insert_called = True

        def fetchone(self):
            return (
                "existing-id",
                "test-validation-conflict",
                True,
                None,
                None,
            )

        def close(self):
            self.closed = True

    class FakeConnection:
        def __init__(self):
            self.fake_cursor = FakeCursor()
            self.rollback_called = False
            self.commit_called = False

        def cursor(self):
            return self.fake_cursor

        def rollback(self):
            self.rollback_called = True

        def commit(self):
            self.commit_called = True

        def close(self):
            pass

    fake_connection = FakeConnection()
    monkeypatch.setattr(
        feedback_repository,
        "get_connection",
        lambda: fake_connection,
    )

    import pytest

    with pytest.raises(ValueError, match="Conflicting feedback"):
        feedback_repository.save_feedback(
            validation_id="test-validation-conflict",
            is_correct=False,
        )

    assert fake_connection.rollback_called
    assert not fake_connection.commit_called
    assert not fake_connection.fake_cursor.insert_called

def test_persisted_feedback_works_without_in_memory_context(monkeypatch):
    from app.orchestration import validation_orchestrator as module

    validation_id = "test-persisted-feedback"

    monkeypatch.setattr(
        module,
        "get_validation",
        lambda _id: {"validation_id": validation_id, "domain": "general"},
    )

    monkeypatch.setattr(
        module,
        "get_verifier_outputs",
        lambda _id: [
            {
                "verifier_name": "test_verifier",
                "score": 0.9,
                "passed": True,
                "reasoning": "Test verification",
                "metadata": {},
            }
        ],
    )

    saved_states = []

    monkeypatch.setattr(
        module,
        "save_reputation_state_and_rows",
        lambda state: saved_states.append(state),
    )

    orchestrator = ValidationOrchestrator(
        reputation_manager=ReputationManager()
    )

    # Simulate a fresh process: no validation context exists in memory.
    assert orchestrator._contexts == {}

    # Prevent unrelated posterior database writes in this unit test.
    monkeypatch.setattr(
        orchestrator,
        "_flush_pending_posteriors",
        lambda: None,
    )

    first_result = orchestrator.record_persisted_ground_truth(
        validation_id=validation_id,
        answer_is_correct=True,
    )

    second_result = orchestrator.record_persisted_ground_truth(
        validation_id=validation_id,
        answer_is_correct=True,
    )

    assert first_result > 0
    assert second_result == 0
    assert len(saved_states) == 1

def test_persisted_feedback_retries_after_failed_reputation_save(monkeypatch):
    from app.orchestration import validation_orchestrator as module
    import pytest

    validation_id = "test-feedback-retry"

    monkeypatch.setattr(
        module,
        "get_validation",
        lambda _id: {"validation_id": validation_id, "domain": "general"},
    )

    monkeypatch.setattr(
        module,
        "get_verifier_outputs",
        lambda _id: [
            {
                "verifier_name": "test_verifier",
                "score": 0.9,
                "passed": True,
                "reasoning": "Test verification",
                "metadata": {},
            }
        ],
    )

    save_attempts = []

    def save_with_one_failure(state):
        save_attempts.append(state)

        if len(save_attempts) == 1:
            raise RuntimeError("Simulated database failure")

    monkeypatch.setattr(
        module,
        "save_reputation_state_and_rows",
        save_with_one_failure,
    )

    orchestrator = ValidationOrchestrator(
        reputation_manager=ReputationManager()
    )

    monkeypatch.setattr(
        orchestrator,
        "_flush_pending_posteriors",
        lambda: None,
    )

    with pytest.raises(RuntimeError, match="Simulated database failure"):
        orchestrator.record_persisted_ground_truth(
            validation_id=validation_id,
            answer_is_correct=True,
        )

    result = orchestrator.record_persisted_ground_truth(
        validation_id=validation_id,
        answer_is_correct=True,
    )

    assert result > 0
    assert len(save_attempts) == 2

    duplicate = orchestrator.record_persisted_ground_truth(
        validation_id=validation_id,
        answer_is_correct=True,
    )

    assert duplicate == 0
    assert len(save_attempts) == 2

def test_reconstructed_feedback_is_idempotent(monkeypatch):
    from app.orchestration import validation_orchestrator as module

    validation_id = "test-reconstructed-feedback"

    monkeypatch.setattr(
        module,
        "get_validation",
        lambda _id: {
            "validation_id": validation_id,
            "domain": "general",
        },
    )

    monkeypatch.setattr(
        module,
        "get_verifier_outputs",
        lambda _id: [
            {
                "verifier_name": "test_verifier",
                "score": 0.9,
                "passed": True,
                "reasoning": "Test verification",
                "metadata": {},
            }
        ],
    )

    saved_states = []

    monkeypatch.setattr(
        module,
        "save_reputation_state_and_rows",
        lambda state: saved_states.append(state),
    )

    manager = ReputationManager()
    orchestrator = ValidationOrchestrator(
        reputation_manager=manager
    )

    # Simulate feedback already reconstructed from PostgreSQL.
    manager.record_feedback(
        module.FeedbackEvent(
            validation_id=validation_id,
            domain="general",
            answer_is_correct=True,
            results=(
                module.VerificationResult(
                    verifier_name="test_verifier",
                    score=0.9,
                    passed=True,
                    reasoning="Test verification",
                    metadata={},
                ),
            ),
            source="ground_truth",
        )
    )

    monkeypatch.setattr(
        orchestrator,
        "_flush_pending_posteriors",
        lambda: None,
    )

    result = orchestrator.record_persisted_ground_truth(
        validation_id=validation_id,
        answer_is_correct=True,
    )

    assert result == 0
    assert saved_states == []
    assert manager.observation_count("test_verifier", "general") == 1