
import os
from uuid import UUID, uuid4

import pytest
import psycopg2
from dotenv import load_dotenv

from database import get_connection
from app.game.models import content_id
from app.database.execution_journal_repository import (
    begin_validation,
    create_verifier_attempt,
    get_verifier_attempts,
    mark_execution_ready,
    mark_execution_running,
)
from app.game.component_binding import bind_answer, component_validation_id, question_plan


load_dotenv()


class AttemptCursor:
    def __init__(self):
        self.executed = []
        self.report_validation_id = None
        self.validation_id = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def execute(self, query, params=None):
        self.executed.append((query, params))
        self.validation_id = params[0]
        self.report_validation_id = params[5]

    def fetchone(self):
        from datetime import datetime, timezone
        return (
            uuid4(), self.validation_id, "call-key", 0, "evidence", "base_fact",
            self.report_validation_id, {}, "planned", datetime.now(timezone.utc),
        )


class AttemptConnection:
    def __init__(self):
        self.fake_cursor = AttemptCursor()

    def cursor(self):
        return self.fake_cursor


def assert_disposable_database(connection):
    with connection.cursor() as cursor:
        cursor.execute("SELECT current_database()")
        assert cursor.fetchone()[0] == "multi_agent_controlled_fixture_test", (
            "Refusing database writes outside multi_agent_controlled_fixture_test"
        )


@pytest.mark.parametrize("report_kind", ["uuid", "compound_sha256"])
def test_create_verifier_attempt_preserves_report_identity(report_kind):
    parent_validation_id = str(uuid4())
    if report_kind == "uuid":
        report_id = str(uuid4())
    else:
        plan = question_plan(
            "What is the area of Bahrain, and what is that area plus 10 square kilometres? Give both values."
        )
        bound = bind_answer(plan, '{"base":"765","derived":"775"}')
        report_id = component_validation_id(parent_validation_id, bound[0])
        assert len(report_id) == 64
        assert all(char in "0123456789abcdef" for char in report_id)

    connection = AttemptConnection()
    attempt = create_verifier_attempt(
        validation_id=parent_validation_id,
        call_key="call-key",
        execution_order=0,
        verifier_name="evidence",
        component_id="base_fact",
        report_validation_id=report_id,
        connection=connection,
    )

    assert connection.fake_cursor.executed[0][1][0] == parent_validation_id
    assert connection.fake_cursor.executed[0][1][5] == report_id
    assert attempt["validation_id"] == str(UUID(parent_validation_id))
    assert attempt["report_validation_id"] == report_id


def test_create_verifier_attempt_still_requires_parent_uuid():
    connection = AttemptConnection()
    with pytest.raises(ValueError):
        create_verifier_attempt(
            validation_id="not-a-uuid",
            call_key="call-key",
            execution_order=0,
            verifier_name="evidence",
            report_validation_id="a" * 64,
            connection=connection,
        )
    assert connection.fake_cursor.executed == []


def test_postgres_journal_round_trips_uuid_and_compound_report_ids():
    assert os.getenv("DB_NAME") == "multi_agent_controlled_fixture_test", (
        "Refusing to run outside multi_agent_controlled_fixture_test"
    )
    parent_validation_id = str(uuid4())
    plan = question_plan(
        "What is the area of Bahrain, and what is that area plus 10 square kilometres? Give both values."
    )
    bound = bind_answer(plan, '{"base":"765","derived":"775"}')
    report_ids = (
        str(uuid4()),
        component_validation_id(parent_validation_id, bound[0]),
        component_validation_id(parent_validation_id, bound[1]),
    )
    connection = get_connection()
    try:
        assert_disposable_database(connection)
    except Exception:
        connection.close()
        raise
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO validation_records (validation_id, question, generated_answer) "
                "VALUES (%s, %s, %s)",
                (parent_validation_id, "compound test", '{"base":"765","derived":"775"}'),
            )
        connection.commit()

        begin_validation(
            validation_id=parent_validation_id,
            execution_mode="game",
            request_payload={"question": "compound test"},
        )
        mark_execution_ready(
            validation_id=parent_validation_id,
            plan_payload={"test": "report identity round trip"},
        )
        running = mark_execution_running(
            validation_id=parent_validation_id,
            worker_id="controlled-report-id-test",
            lease_seconds=120,
        )
        for order, (component, report_id) in enumerate(
            zip((None, "base_fact", "derived_sum"), report_ids)
        ):
            create_verifier_attempt(
                validation_id=parent_validation_id,
                call_key=f"identity-test:{order}",
                execution_order=order,
                verifier_name="evidence" if component != "derived_sum" else "rule",
                component_id=component,
                report_validation_id=report_id,
                identity_binding={"component_id": component} if component else {},
                lease_token=running["lease_token"],
            )

        attempts = get_verifier_attempts(validation_id=parent_validation_id)
        assert [attempt["report_validation_id"] for attempt in attempts] == list(report_ids)
        assert all(attempt["validation_id"] == parent_validation_id for attempt in attempts)
        assert [attempt["component_id"] for attempt in attempts] == [None, "base_fact", "derived_sum"]
        assert len({attempt["attempt_id"] for attempt in attempts}) == 3
    finally:
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "DELETE FROM live_verifier_attempts WHERE validation_id = %s",
                    (parent_validation_id,),
                )
                cursor.execute(
                    "DELETE FROM validation_executions WHERE validation_id = %s",
                    (parent_validation_id,),
                )
                cursor.execute(
                    "DELETE FROM validation_records WHERE validation_id = %s",
                    (parent_validation_id,),
                )
            connection.commit()
        finally:
            connection.close()


def test_begin_validation_persists_execution():
    """
    Verify that begin_validation:
    1. Creates a validation execution.
    2. Stores the original request.
    3. Persists its canonical SHA-256 digest.
    4. Starts in the initializing state.
    """

    # Never allow this integration test to run against the real database.
    assert os.getenv("DB_NAME") == "multi_agent_controlled_fixture_test", (
        "Refusing to run outside multi_agent_controlled_fixture_test"
    )

    validation_id = str(uuid4())

    request_payload = {
        "question": "What is 2 + 2?",
        "answer": "4",
        "context": None,
    }

    conn = get_connection()
    try:
        assert_disposable_database(conn)
    except Exception:
        conn.close()
        raise

    try:
        # Create the parent validation record required by the FK.
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO validation_records (
                    validation_id,
                    question,
                    generated_answer
                )
                VALUES (%s, %s, %s)
                """,
                (
                    validation_id,
                    request_payload["question"],
                    request_payload["answer"],
                ),
            )

        conn.commit()

        # Exercise the actual repository function.
        result = begin_validation(
            validation_id=validation_id,
            execution_mode="game",
            request_payload=request_payload,
        )

        assert result["validation_id"] == validation_id
        assert result["execution_status"] == "initializing"
        assert result["execution_mode"] == "game"
        assert result["request_digest"] == content_id(request_payload)

        # Verify the persisted database record.
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    execution_status,
                    execution_mode,
                    request_payload,
                    request_digest
                FROM validation_executions
                WHERE validation_id = %s
                """,
                (validation_id,),
            )

            row = cursor.fetchone()

        assert row is not None
        assert row[0] == "initializing"
        assert row[1] == "game"
        assert row[2] == request_payload
        assert row[3] == content_id(request_payload)

    finally:
        # Remove test data without leaving records behind.
        conn.rollback()

        with conn.cursor() as cursor:
            cursor.execute(
                """
                DELETE FROM validation_executions
                WHERE validation_id = %s
                """,
                (validation_id,),
            )

            cursor.execute(
                """
                DELETE FROM validation_records
                WHERE validation_id = %s
                """,
                (validation_id,),
            )

        conn.commit()
        conn.close()


def test_begin_validation_rejects_duplicate_id():
    """A validation ID must not create two execution records."""

    assert os.getenv("DB_NAME") == "multi_agent_controlled_fixture_test", (
        "Refusing to run outside multi_agent_controlled_fixture_test"
    )

    validation_id = str(uuid4())

    request_payload = {
        "question": "Duplicate test",
        "answer": "Test answer",
    }

    conn = get_connection()
    try:
        assert_disposable_database(conn)
    except Exception:
        conn.close()
        raise

    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO validation_records (
                    validation_id,
                    question,
                    generated_answer
                )
                VALUES (%s, %s, %s)
                """,
                (
                    validation_id,
                    request_payload["question"],
                    request_payload["answer"],
                ),
            )

        conn.commit()

        begin_validation(
            validation_id=validation_id,
            execution_mode="game",
            request_payload=request_payload,
        )

        with pytest.raises(psycopg2.errors.UniqueViolation):
            begin_validation(
                validation_id=validation_id,
                execution_mode="game",
                request_payload=request_payload,
            )

    finally:
        conn.rollback()

        with conn.cursor() as cursor:
            cursor.execute(
                """
                DELETE FROM validation_executions
                WHERE validation_id = %s
                """,
                (validation_id,),
            )

            cursor.execute(
                """
                DELETE FROM validation_records
                WHERE validation_id = %s
                """,
                (validation_id,),
            )

        conn.commit()
        conn.close()
