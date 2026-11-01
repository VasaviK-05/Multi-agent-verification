from datetime import datetime, timezone
from uuid import uuid4

import pytest

from app.ground_truth import storage


VALIDATION_ID = uuid4()
GROUND_TRUTH_ID = uuid4()
QUESTION_ID = 123
LABEL = "Paris"
SOURCE = "Wikidata"
LABELED_AT = datetime.now(timezone.utc)


def make_record():
    return (
        GROUND_TRUTH_ID,
        VALIDATION_ID,
        QUESTION_ID,
        LABEL,
        SOURCE,
        LABELED_AT,
    )


class FakeCursor:
    def __init__(self, rows):
        self.rows = list(rows)
        self.executed = []
        self.closed = False

    def execute(self, query, params=None):
        self.executed.append((query, params))

    def fetchone(self):
        if self.rows:
            return self.rows.pop(0)
        return None

    def close(self):
        self.closed = True


class FakeConnection:
    def __init__(self, rows):
        self.fake_cursor = FakeCursor(rows)
        self.committed = False
        self.rolled_back = False
        self.closed = False

    def cursor(self):
        return self.fake_cursor

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True

    def close(self):
        self.closed = True


def test_first_save_inserts_ground_truth(monkeypatch):
    connection = FakeConnection([make_record()])

    monkeypatch.setattr(
        storage,
        "get_connection",
        lambda: connection,
    )

    result = storage.save_ground_truth(
        validation_id=VALIDATION_ID,
        question_id=QUESTION_ID,
        label=LABEL,
        source=SOURCE,
    )

    assert result.ground_truth_id == GROUND_TRUTH_ID
    assert result.validation_id == VALIDATION_ID
    assert result.question_id == QUESTION_ID
    assert result.label == LABEL
    assert result.source == SOURCE

    assert connection.committed is True
    assert connection.rolled_back is False

    assert len(connection.fake_cursor.executed) == 1

    query = connection.fake_cursor.executed[0][0]

    assert "INSERT INTO ground_truth_labels" in query
    assert "ON CONFLICT (validation_id) DO NOTHING" in query


def test_identical_retry_returns_existing_record(monkeypatch):
    connection = FakeConnection([
        None,
        make_record(),
    ])

    monkeypatch.setattr(
        storage,
        "get_connection",
        lambda: connection,
    )

    result = storage.save_ground_truth(
        validation_id=VALIDATION_ID,
        question_id=QUESTION_ID,
        label=LABEL,
        source=SOURCE,
    )

    assert result.ground_truth_id == GROUND_TRUTH_ID
    assert result.validation_id == VALIDATION_ID
    assert result.label == LABEL
    assert result.source == SOURCE

    assert connection.committed is True
    assert connection.rolled_back is False

    assert len(connection.fake_cursor.executed) == 2

    assert "INSERT INTO ground_truth_labels" in (
        connection.fake_cursor.executed[0][0]
    )

    assert "SELECT" in connection.fake_cursor.executed[1][0]


def test_conflicting_label_raises_error(monkeypatch):
    existing_record = (
        GROUND_TRUTH_ID,
        VALIDATION_ID,
        QUESTION_ID,
        "London",
        SOURCE,
        LABELED_AT,
    )

    connection = FakeConnection([
        None,
        existing_record,
    ])

    monkeypatch.setattr(
        storage,
        "get_connection",
        lambda: connection,
    )

    with pytest.raises(
        ValueError,
        match="Conflicting ground-truth data",
    ):
        storage.save_ground_truth(
            validation_id=VALIDATION_ID,
            question_id=QUESTION_ID,
            label=LABEL,
            source=SOURCE,
        )

    assert connection.rolled_back is True
    assert connection.committed is False


def test_conflicting_source_raises_error(monkeypatch):
    existing_record = (
        GROUND_TRUTH_ID,
        VALIDATION_ID,
        QUESTION_ID,
        LABEL,
        "DifferentSource",
        LABELED_AT,
    )

    connection = FakeConnection([
        None,
        existing_record,
    ])

    monkeypatch.setattr(
        storage,
        "get_connection",
        lambda: connection,
    )

    with pytest.raises(
        ValueError,
        match="Conflicting ground-truth data",
    ):
        storage.save_ground_truth(
            validation_id=VALIDATION_ID,
            question_id=QUESTION_ID,
            label=LABEL,
            source=SOURCE,
        )

    assert connection.rolled_back is True
    assert connection.committed is False


def test_missing_existing_record_raises_error(monkeypatch):
    connection = FakeConnection([
        None,
        None,
    ])

    monkeypatch.setattr(
        storage,
        "get_connection",
        lambda: connection,
    )

    with pytest.raises(
        RuntimeError,
        match="could not be retrieved",
    ):
        storage.save_ground_truth(
            validation_id=VALIDATION_ID,
            question_id=QUESTION_ID,
            label=LABEL,
            source=SOURCE,
        )

    assert connection.rolled_back is True