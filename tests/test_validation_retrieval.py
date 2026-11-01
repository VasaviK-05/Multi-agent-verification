
import pytest

from app.database import validation_repository
from app.database import verifier_repository


class FakeCursor:
    def __init__(self, row=None, rows=None):
        self.row = row
        self.rows = rows or []
        self.executed = []
        self.closed = False

    def execute(self, query, params=None):
        self.executed.append((query, params))

    def fetchone(self):
        return self.row

    def fetchall(self):
        return self.rows

    def close(self):
        self.closed = True


class FakeConnection:
    def __init__(self, cursor):
        self.fake_cursor = cursor
        self.closed = False

    def cursor(self):
        return self.fake_cursor

    def close(self):
        self.closed = True


def test_get_validation_returns_persisted_record(monkeypatch):
    cursor = FakeCursor(
        row=(
            "validation-123",
            42,
            "Question?",
            "Generated answer",
            "Context",
            "accepted",
            0.95,
            None,
            "medical",
            "medium",
            ["semantic"],
            None,
            0.9,
            None,
        )
    )
    connection = FakeConnection(cursor)

    monkeypatch.setattr(
        validation_repository,
        "get_connection",
        lambda: connection,
    )

    result = validation_repository.get_validation("validation-123")

    assert result["validation_id"] == "validation-123"
    assert result["domain"] == "medical"
    assert result["selected_verifiers"] == ["semantic"]
    assert cursor.executed[0][1] == ("validation-123",)
    assert cursor.closed
    assert connection.closed


def test_get_validation_returns_none_when_missing(monkeypatch):
    cursor = FakeCursor(row=None)
    connection = FakeConnection(cursor)

    monkeypatch.setattr(
        validation_repository,
        "get_connection",
        lambda: connection,
    )

    assert validation_repository.get_validation("missing") is None
    assert cursor.closed
    assert connection.closed


def test_get_verifier_outputs_returns_execution_order(monkeypatch):
    cursor = FakeCursor(
        rows=[
            (
                "result-1",
                "semantic",
                0.9,
                True,
                "Supported",
                {},
                None,
                1,
            ),
            (
                "result-2",
                "rule",
                0.2,
                False,
                "Contradicted",
                {},
                None,
                2,
            ),
        ]
    )
    connection = FakeConnection(cursor)

    monkeypatch.setattr(
        verifier_repository,
        "get_connection",
        lambda: connection,
    )

    results = verifier_repository.get_verifier_outputs("validation-123")

    assert len(results) == 2
    assert results[0]["verifier_name"] == "semantic"
    assert results[1]["verifier_name"] == "rule"
    assert cursor.executed[0][1] == ("validation-123",)
    assert "ORDER BY execution_order ASC" in cursor.executed[0][0]
    assert cursor.closed
    assert connection.closed


def test_get_verifier_outputs_returns_empty_list_when_missing(monkeypatch):
    cursor = FakeCursor(rows=[])
    connection = FakeConnection(cursor)

    monkeypatch.setattr(
        verifier_repository,
        "get_connection",
        lambda: connection,
    )

    assert verifier_repository.get_verifier_outputs("missing") == []
    assert cursor.closed
    assert connection.closed
