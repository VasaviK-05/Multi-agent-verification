
import os
from uuid import uuid4

import pytest
import psycopg2
from dotenv import load_dotenv

from database import get_connection
from app.game.models import content_id
from app.database.execution_journal_repository import begin_validation


load_dotenv()


def test_begin_validation_persists_execution():
    """
    Verify that begin_validation:
    1. Creates a validation execution.
    2. Stores the original request.
    3. Persists its canonical SHA-256 digest.
    4. Starts in the initializing state.
    """

    # Never allow this integration test to run against the real database.
    assert os.getenv("DB_NAME") == "capstone_recovery_test", (
        "Refusing to run outside capstone_recovery_test"
    )

    validation_id = str(uuid4())

    request_payload = {
        "question": "What is 2 + 2?",
        "answer": "4",
        "context": None,
    }

    conn = get_connection()

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

    assert os.getenv("DB_NAME") == "capstone_recovery_test", (
        "Refusing to run outside capstone_recovery_test"
    )

    validation_id = str(uuid4())

    request_payload = {
        "question": "Duplicate test",
        "answer": "Test answer",
    }

    conn = get_connection()

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
