
from fastapi.testclient import TestClient

from app.main import app
from app.api import feedback_routes

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
