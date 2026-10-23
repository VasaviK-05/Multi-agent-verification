
import pytest

from app.database import audit_repository as repository
from datetime import datetime, timezone


VALIDATION_ID = "11111111-1111-4111-8111-111111111111"


class FakeCursor:
    def __init__(self, rows=None):
        self.rows = rows or []
        self.executed = []
        self.closed = False

    def execute(self, query, params=None):
        self.executed.append((query, params))

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


def test_create_audit_inserts_started_record(monkeypatch):
    connection = FakeConnection([
        (
            "audit-1",
            VALIDATION_ID,
            "started",
            datetime.now(timezone.utc),
        )
    ])
    monkeypatch.setattr(repository, "get_connection", lambda: connection)

    result = repository.create_audit(
        validation_id=VALIDATION_ID,
        question_id=123,
        policy_version="v1",
        selected_strategy="reputation_weighted_vote",
    )

    query, params = connection.fake_cursor.executed[0]

    assert "INSERT INTO validation_audits" in query
    assert "'started'" in query
    assert params[0] == VALIDATION_ID
    assert params[1] == 123
    assert params[3] == "v1"
    assert params[4] == "reputation_weighted_vote"
    assert result["run_status"] == "started"
    assert connection.commits == 1
    assert connection.rollbacks == 0
    assert connection.closed
    assert connection.fake_cursor.closed


def test_create_audit_rolls_back_on_error(monkeypatch):
    connection = FakeConnection()

    def fail_execute(query, params=None):
        raise RuntimeError("database write failed")

    connection.fake_cursor.execute = fail_execute
    monkeypatch.setattr(repository, "get_connection", lambda: connection)

    with pytest.raises(RuntimeError, match="database write failed"):
        repository.create_audit(validation_id=VALIDATION_ID)

    assert connection.commits == 0
    assert connection.rollbacks == 1
    assert connection.closed


def test_update_audit_marks_run_completed(monkeypatch):
    connection = FakeConnection([("audit-1",)])
    monkeypatch.setattr(repository, "get_connection", lambda: connection)

    repository.update_audit(
        VALIDATION_ID,
        run_status="completed",
        selected_verifiers=[],
        decision_summary={"status": "unknown"},
        coverage_outcomes={},
    )

    query, params = connection.fake_cursor.executed[0]

    assert "UPDATE validation_audits" in query
    assert params[0] == "completed"
    assert params[-1] == VALIDATION_ID
    assert connection.commits == 1
    assert connection.rollbacks == 0
    assert connection.closed


def test_update_audit_allows_empty_verifier_results(monkeypatch):
    connection = FakeConnection([("audit-1",)])
    monkeypatch.setattr(repository, "get_connection", lambda: connection)

    repository.update_audit(
        VALIDATION_ID,
        run_status="completed",
        selected_verifiers=[],
        ranking_explanations=[],
        decision_summary={"status": "unknown"},
        failure_details=[],
    )

    _, params = connection.fake_cursor.executed[0]

    assert params[1] == "[]"
    assert params[2] == "[]"
    assert params[3] == '{"status": "unknown"}'
    assert params[6] == "[]"
    assert connection.commits == 1


def test_update_audit_rejects_missing_audit(monkeypatch):
    connection = FakeConnection()
    monkeypatch.setattr(repository, "get_connection", lambda: connection)

    with pytest.raises(ValueError, match="No audit exists"):
        repository.update_audit(
            VALIDATION_ID,
            run_status="failed",
        )

    assert connection.commits == 0
    assert connection.rollbacks == 1
    assert connection.closed


def test_update_audit_rejects_invalid_status():
    with pytest.raises(ValueError, match="run_status"):
        repository.update_audit(
            VALIDATION_ID,
            run_status="unknown",
        )

def test_get_audit_returns_record(monkeypatch):
    started_at = datetime.now(timezone.utc)
    connection = FakeConnection([
        (
            "audit-1",
            VALIDATION_ID,
            123,
            None,  # session_id
            "completed",
            started_at,
            started_at,  # completed_at
            "v1",
            "reputation_weighted_vote",
            {},  # execution_contract
            {"verifier_a": 0.9},  # reputation_snapshot
            None,  # reputation_snapshot_id
            ["verifier_a"],
            [{"verifier": "verifier_a", "utility": 0.9}],
            {"status": "accepted"},
            {"direct_fact": True},
            {"total_ms": 120},
            [],  # failure_details
            started_at,  # created_at
            started_at,  # updated_at
        )
    ])
    monkeypatch.setattr(repository, "get_connection", lambda: connection)

    result = repository.get_audit(VALIDATION_ID)

    assert result is not None
    assert result["validation_id"] == VALIDATION_ID
    assert result["run_status"] == "completed"
    assert result["policy_version"] == "v1"
    assert result["selected_verifiers"] == ["verifier_a"]
    assert result["decision_summary"] == {"status": "accepted"}
    assert result["started_at"] == started_at.isoformat()
    assert connection.commits == 0
    assert connection.closed
    assert connection.fake_cursor.closed


def test_get_audit_returns_none_when_missing(monkeypatch):
    connection = FakeConnection()
    monkeypatch.setattr(repository, "get_connection", lambda: connection)

    result = repository.get_audit(VALIDATION_ID)

    assert result is None
    assert connection.closed
    assert connection.fake_cursor.closed
