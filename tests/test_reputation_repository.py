
import pytest

from app.database import reputation_repository as repository


class FakeCursor:
    def __init__(self, rows=None):
        self.rows = rows or []
        self.executed = []
        self.closed = False

    def execute(self, query, params=None):
        self.executed.append((query, params))

    def fetchall(self):
        return self.rows

    def fetchone(self):
        return self.rows[0] if self.rows else None

    def close(self):
        self.closed = True

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()


class FakeConnection:
    def __init__(self, rows=None):
        self.fake_cursor = FakeCursor(rows)
        self.commits = 0
        self.rollbacks = 0
        self.closed = False

    def cursor(self):
        return self.fake_cursor

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1

    def close(self):
        self.closed = True


def test_load_reputation_returns_database_rows(monkeypatch):
    connection = FakeConnection([
        ("semantic", "medical", 3.0, 2.0),
        ("rule", "general", 4.0, 1.0),
    ])
    monkeypatch.setattr(repository, "get_connection", lambda: connection)

    result = repository.load_reputation()

    assert result == [
        {
            "verifier_name": "semantic",
            "domain": "medical",
            "alpha": 3.0,
            "beta": 2.0,
        },
        {
            "verifier_name": "rule",
            "domain": "general",
            "alpha": 4.0,
            "beta": 1.0,
        },
    ]
    assert connection.closed
    assert connection.fake_cursor.closed


def test_save_reputation_upserts_and_commits(monkeypatch):
    connection = FakeConnection()
    monkeypatch.setattr(repository, "get_connection", lambda: connection)

    repository.save_reputation(
        verifier_name="semantic",
        domain="medical",
        alpha=3.0,
        beta=2.0,
    )

    query, params = connection.fake_cursor.executed[0]
    assert "INSERT INTO verifier_reputation" in query
    assert "ON CONFLICT (verifier_name, domain)" in query
    assert params == ("semantic", "medical", 3.0, 2.0)
    assert connection.commits == 1
    assert connection.rollbacks == 0
    assert connection.closed


def test_save_reputation_rolls_back_on_database_error(monkeypatch):
    connection = FakeConnection()

    def fail_execute(query, params=None):
        raise RuntimeError("database write failed")

    connection.fake_cursor.execute = fail_execute
    monkeypatch.setattr(repository, "get_connection", lambda: connection)

    with pytest.raises(RuntimeError, match="database write failed"):
        repository.save_reputation(
            verifier_name="semantic",
            domain="medical",
            alpha=3.0,
            beta=2.0,
        )

    assert connection.commits == 0
    assert connection.rollbacks == 1
    assert connection.closed


from app.models.schemas import VerificationResult
from app.reputation.reputation_manager import FeedbackEvent, ReputationManager


def test_build_reputation_state_reconstructs_feedback_without_double_counting(
    monkeypatch,
):
    result = VerificationResult(
        verifier_name="semantic",
        score=0.9,
        passed=True,
        metadata={"decision": "SUPPORT"},
    )

    event = {
        "validation_id": "validation-123",
        "domain": "medical",
        "answer_is_correct": True,
        "source": "ground_truth",
        "results": [
            {
                "verifier_name": "semantic",
                "score": 0.9,
                "passed": True,
                "reasoning": "Supports the answer",
                "metadata": {"decision": "SUPPORT"},
            }
        ],
    }

    monkeypatch.setattr(
        repository,
        "load_reputation_state",
        lambda: {
            "reputation": [
                {
                    "verifier_name": "semantic",
                    "domain": "medical",
                    "alpha": 2.0,
                    "beta": 1.0,
                }
            ],
            "feedback": [event],
        },
    )

    restored_state = repository.build_reputation_state()

    restored = ReputationManager()
    restored.restore_state(restored_state)

    stats = restored.statistics("semantic", "medical")

    assert stats.observation_count == 1
    assert stats.alpha == pytest.approx(2.0)
    assert stats.beta == pytest.approx(1.0)

    # Replaying the same feedback must not count it again.
    before = restored.export_state()
    receipt = restored.record_feedback(
        FeedbackEvent(
            validation_id="validation-123",
            domain="medical",
            answer_is_correct=True,
            results=(result,),
            source="ground_truth",
        )
    )

    assert receipt.observations_applied == 0
    assert restored.export_state() == before


def test_build_reputation_state_does_not_silently_claim_snapshot_was_restored(
    monkeypatch,
):
    monkeypatch.setattr(
        repository,
        "load_reputation_state",
        lambda: {
            "reputation": [
                {
                    "verifier_name": "semantic",
                    "domain": "medical",
                    "alpha": 8.0,
                    "beta": 2.0,
                }
            ],
            "feedback": [],
        },
    )

    state = repository.build_reputation_state()

    restored = ReputationManager()
    restored.restore_state(state)

    stats = restored.statistics("semantic", "medical")

    # With no feedback, reconstruction from history alone has no observations.
    # This documents the current limitation: the stored snapshot is ignored.
    assert stats.observation_count == 0
    assert stats.alpha == pytest.approx(1.0)
    assert stats.beta == pytest.approx(1.0)

def test_save_and_load_reputation_manager_state(monkeypatch):
    state = {
        "schema_version": 1,
        "prior_alpha": 1.0,
        "prior_beta": 1.0,
        "pairs": [
            {
                "verifier_name": "semantic",
                "domain": "medical",
                "successes": 2,
                "failures": 1,
            }
        ],
        "feedback": [
            {
                "validation_id": "validation-123",
                "domain": "medical",
                "answer_is_correct": True,
                "source": "ground_truth",
                "votes": [
                    {
                        "verifier_name": "semantic",
                        "passed": True,
                        "abstained": False,
                    }
                ],
            }
        ],
    }

    save_connection = FakeConnection()
    monkeypatch.setattr(
        repository, "get_connection", lambda: save_connection
    )

    repository.save_reputation_manager_state(state)

    save_query, save_params = save_connection.fake_cursor.executed[0]
    assert "INSERT INTO reputation_manager_state" in save_query
    assert save_params[0] == 1
    assert save_connection.commits == 1
    assert save_connection.closed

    load_connection = FakeConnection([(1, state)])
    monkeypatch.setattr(
        repository, "get_connection", lambda: load_connection
    )

    loaded = repository.load_reputation_manager_state()

    assert loaded == state
    assert load_connection.closed

def test_fresh_orchestrator_restores_saved_reputation_snapshot(monkeypatch):
    from app.orchestration import validation_orchestrator as orchestrator_module

    original = ReputationManager()
    original.record_feedback(
        FeedbackEvent(
            validation_id="saved-validation-1",
            domain="medical",
            answer_is_correct=True,
            results=(
                VerificationResult(
                    verifier_name="semantic",
                    score=0.9,
                    passed=True,
                    reasoning="Supports the answer",
                    metadata={},
                ),
            ),
            source="ground_truth",
        )
    )
    saved_state = original.export_state()

    monkeypatch.setattr(
        orchestrator_module,
        "load_reputation_manager_state",
        lambda: saved_state,
    )
    monkeypatch.setattr(
        orchestrator_module,
        "build_reputation_state",
        lambda: pytest.fail("Fallback should not be used when a snapshot exists"),
    )

    fresh = orchestrator_module.ValidationOrchestrator()

    assert fresh.reputation_manager.export_state() == saved_state


def test_save_reputation_state_and_rows_commits_atomically(monkeypatch):
    state = {
        "schema_version": 1,
        "prior_alpha": 1.0,
        "prior_beta": 1.0,
        "pairs": [
            {
                "verifier_name": "semantic",
                "domain": "medical",
                "successes": 2,
                "failures": 1,
            },
            {
                "verifier_name": "rule",
                "domain": "general",
                "successes": 3,
                "failures": 0,
            },
        ],
        "feedback": [],
    }

    connection = FakeConnection()
    monkeypatch.setattr(
        repository, "get_connection", lambda: connection
    )

    repository.save_reputation_state_and_rows(state)

    executed = connection.fake_cursor.executed

    # One snapshot write and one upsert per reputation pair.
    assert len(executed) == 3
    assert "INSERT INTO reputation_manager_state" in executed[0][0]
    assert "INSERT INTO verifier_reputation" in executed[1][0]
    assert "INSERT INTO verifier_reputation" in executed[2][0]

    # alpha = prior_alpha + successes; beta = prior_beta + failures.
    assert executed[1][1] == ("semantic", "medical", 3.0, 2.0)
    assert executed[2][1] == ("rule", "general", 4.0, 1.0)

    assert connection.commits == 1
    assert connection.rollbacks == 0
    assert connection.closed


def test_save_reputation_state_and_rows_rolls_back_on_failure(monkeypatch):
    state = {
        "schema_version": 1,
        "prior_alpha": 1.0,
        "prior_beta": 1.0,
        "pairs": [
            {
                "verifier_name": "semantic",
                "domain": "medical",
                "successes": 2,
                "failures": 1,
            }
        ],
        "feedback": [],
    }

    connection = FakeConnection()

    def fail_on_reputation_write(query, params=None):
        if "INSERT INTO verifier_reputation" in query:
            raise RuntimeError("reputation row write failed")
        connection.fake_cursor.executed.append((query, params))

    connection.fake_cursor.execute = fail_on_reputation_write
    monkeypatch.setattr(
        repository, "get_connection", lambda: connection
    )

    with pytest.raises(RuntimeError, match="reputation row write failed"):
        repository.save_reputation_state_and_rows(state)

    # The snapshot write happened, but the transaction must not commit.
    assert len(connection.fake_cursor.executed) == 1
    assert "INSERT INTO reputation_manager_state" in (
        connection.fake_cursor.executed[0][0]
    )
    assert connection.commits == 0
    assert connection.rollbacks == 1
    assert connection.closed