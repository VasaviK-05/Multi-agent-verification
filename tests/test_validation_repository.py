
import os
from uuid import uuid4

import pytest
from dotenv import load_dotenv

from database import get_connection
from app.database.validation_repository import (
    create_validation_record,
    update_validation_record,
)

load_dotenv()


def _assert_test_database():
    assert os.getenv("DB_NAME") == "multi_agent_controlled_fixture_test", (
        "Refusing to run outside multi_agent_controlled_fixture_test"
    )


def test_create_and_update_validation_record():
    """Verify initial validation creation and final result updating."""

    _assert_test_database()

    validation_id = str(uuid4())
    conn = get_connection()

    try:
        # Create the initial parent validation record.
        create_validation_record(
            validation_id=validation_id,
            question_id=None,
            question="What is 2 + 2?",
            generated_answer="4",
            context=None,
            session_id=None,
        )

        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT final_status, final_score, question,
                       generated_answer, selected_verifiers
                FROM validation_records
                WHERE validation_id = %s
                """,
                (validation_id,),
            )
            row = cursor.fetchone()

        assert row is not None
        assert row[0] is None
        assert row[1] is None
        assert row[2] == "What is 2 + 2?"
        assert row[3] == "4"
        assert row[4] == []

        # Update the initial record with the final result.
        update_validation_record(
            validation_id=validation_id,
            question_id=None,
            question="What is 2 + 2?",
            generated_answer="4",
            context=None,
            final_status="approved",
            final_score=1.0,
            session_id=None,
            domain="mathematics",
            difficulty="easy",
            selected_verifiers=["verifier_a", "verifier_b"],
            early_stop_reason=None,
            signed_score=1.0,
        )

        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT final_status, final_score, domain,
                       difficulty, selected_verifiers, signed_score
                FROM validation_records
                WHERE validation_id = %s
                """,
                (validation_id,),
            )
            row = cursor.fetchone()

        assert row is not None
        assert row[0] == "approved"
        assert row[1] == 1.0
        assert row[2] == "mathematics"
        assert row[3] == "easy"
        assert row[4] == ["verifier_a", "verifier_b"]
        assert row[5] == 1.0

    finally:
        conn.rollback()

        with conn.cursor() as cursor:
            cursor.execute(
                """
                DELETE FROM validation_records
                WHERE validation_id = %s
                """,
                (validation_id,),
            )

        conn.commit()
        conn.close()


def test_update_validation_record_rejects_unknown_id():
    """Updating a nonexistent validation must fail."""

    _assert_test_database()

    with pytest.raises(ValueError, match="Validation record not found"):
        update_validation_record(
            validation_id=str(uuid4()),
            question_id=None,
            question="Test question",
            generated_answer="Test answer",
            context=None,
            final_status="approved",
            final_score=1.0,
            session_id=None,
        )
