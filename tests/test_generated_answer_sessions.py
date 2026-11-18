"""Offline session persistence regression tests; no PostgreSQL or services."""
import sqlite3
from types import SimpleNamespace
from unittest.mock import Mock
import pytest
from tests.test_api_compound_generation import api, configuration, no_network, QUESTION, ANSWER
from app.database import session_repository

SESSION = "11111111-1111-4111-8111-111111111111"

@pytest.mark.parametrize("question,expected", [(QUESTION, ANSWER), ("Explain quantum gravity.", "Generic answer")])
def test_generation_associates_session_once(api, question, expected):
    response = api.client.post("/generate-answer", json={"question": question, "session_id": SESSION})
    assert response.status_code == 200
    assert response.json()["answer"] == expected
    assert len(api.statements) == 2
    assert "FROM sessions" in api.statements[0][0]
    assert api.statements[1][1] == (question, expected, SESSION)
    api.connection.commit.assert_called_once()
    assert not api.service.calls and not api.audits


def test_generation_without_session_is_backward_compatible(api):
    response = api.client.post("/generate-answer", json={"question": QUESTION})
    assert response.status_code == 200
    assert len(api.statements) == 1
    assert api.statements[0][1] == (QUESTION, ANSWER, None)
    api.connection.commit.assert_called_once()


def test_nonexistent_session_rolls_back_without_answer_insert(api):
    cursor = api.connection.cursor()
    cursor.fetchone = lambda: None
    response = api.client.post("/generate-answer", json={"question": QUESTION, "session_id": SESSION})
    assert response.status_code == 404
    assert len(api.statements) == 1 and "FROM sessions" in api.statements[0][0]
    api.connection.rollback.assert_called_once()
    api.connection.commit.assert_not_called()
    assert not api.audits and not api.service.calls


def test_malformed_session_rejected_before_generation(api):
    response = api.client.post("/generate-answer", json={"question": QUESTION, "session_id": "invalid"})
    assert response.status_code == 422
    api.connect.assert_not_called()
    api.llm.assert_not_called()


def test_answer_insert_failure_rolls_back(api):
    cursor = api.connection.cursor()
    cursor.execute = Mock(side_effect=[None, RuntimeError("private database details")])
    response = api.client.post("/generate-answer", json={"question": QUESTION, "session_id": SESSION})
    assert response.status_code == 500
    assert response.json()["detail"]["code"] == "ANSWER_PERSISTENCE_FAILED"
    assert "private" not in response.text
    api.connection.rollback.assert_called_once()
    api.connection.commit.assert_not_called()


@pytest.fixture
def history_db(monkeypatch):
    # Execute the repository query with only PostgreSQL cast/placeholder syntax
    # translated. This tests joins/order/deduplication, not PostgreSQL migration.
    db = sqlite3.connect(":memory:")
    db.executescript("""
      CREATE TABLE questions_answers(id INTEGER PRIMARY KEY, question TEXT, answer TEXT, created_at TEXT, session_id TEXT);
      CREATE TABLE validation_records(validation_id TEXT,question_id INTEGER,question TEXT,generated_answer TEXT,final_status TEXT,final_score REAL,domain TEXT,created_at TEXT,session_id TEXT);
    """)
    class Cursor:
        def __init__(self): self.cursor = db.cursor()
        def execute(self, sql, params):
            for cast in ("::double precision", "::uuid", "::text"):
                sql = sql.replace(cast, "")
            self.cursor.execute(sql.replace("%s", "?"), params)
        def fetchall(self): return self.cursor.fetchall()
        def close(self): self.cursor.close()
    monkeypatch.setattr(session_repository, "get_connection", lambda: SimpleNamespace(cursor=Cursor, close=lambda: None))
    yield db
    db.close()


def test_generated_history_survives_reload_and_is_not_validated(history_db):
    history_db.execute("INSERT INTO questions_answers VALUES(1,?,?,?,?)", (QUESTION, ANSWER, "2026-11-18T10:00:00", SESSION))
    first = session_repository.get_session_questions(SESSION)
    restored = session_repository.get_session_questions(SESSION)
    assert first == restored
    assert restored[0]["generated_answer"] == ANSWER
    assert restored[0]["question_id"] == 1
    assert restored[0]["history_state"] == "generated_only"
    assert restored[0]["validation_id"] is None
    assert restored[0]["final_status"] is None and restored[0]["final_score"] is None
    assert session_repository.get_session_questions("other-session") == []


def test_validation_replaces_generated_history_without_duplicate(history_db):
    history_db.execute("INSERT INTO questions_answers VALUES(1,?,?,?,?)", (QUESTION, ANSWER, "2026-11-18T10:00:00", SESSION))
    history_db.execute("INSERT INTO validation_records VALUES(?,?,?,?,?,?,?,?,?)", ("validation-1",1,QUESTION,ANSWER,"uncertain",0.0,"numeric_fact","2026-11-18T10:01:00",SESSION))
    rows = session_repository.get_session_questions(SESSION)
    assert len(rows) == 1
    assert rows[0]["validation_id"] == "validation-1"
    assert rows[0]["history_state"] == "validation_record"
    assert rows[0]["final_status"] == "uncertain"


def test_legacy_history_and_order_are_preserved(history_db):
    history_db.execute("INSERT INTO validation_records VALUES(?,?,?,?,?,?,?,?,?)", ("legacy",None,"older","old answer","passed",1.0,"general","2026-11-17T10:00:00",SESSION))
    history_db.execute("INSERT INTO questions_answers VALUES(2,?,?,?,?)", ("newer","generic unchanged","2026-11-18T10:00:00",SESSION))
    rows = session_repository.get_session_questions(SESSION)
    assert [r["question"] for r in rows] == ["older", "newer"]
    assert rows[0]["final_status"] == "passed" and rows[0]["final_score"] == 1.0
    assert rows[1]["generated_answer"] == "generic unchanged"
