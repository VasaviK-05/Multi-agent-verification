import json

from database import get_connection


def save_validation(
    validation_id: str,
    question_id: int,
    question: str,
    generated_answer: str,
    context: str | None,
    final_status: str,
    final_score: float | None,
    session_id: str | None,
    domain: str | None = None,
    difficulty: str | None = None,
    selected_verifiers: list[str] | None = None,
    early_stop_reason: str | None = None,
    signed_score: float | None = None,
):

    connection = None
    cursor = None

    try:
        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO validation_records (
                validation_id,
                question_id,
                question,
                generated_answer,
                context,
                final_status,
                final_score,
                session_id,
                domain,
                difficulty,
                selected_verifiers,
                early_stop_reason,
                signed_score,
                created_at
            )
            VALUES (
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s,
                %s::jsonb, %s, %s, NOW()
            )
            """,
            (
                validation_id,
                question_id,
                question,
                generated_answer,
                context,
                final_status,
                final_score,
                session_id,
                domain,
                difficulty,
                json.dumps(selected_verifiers or []),
                early_stop_reason,
                signed_score,
            ),
        )

        connection.commit()

    except Exception:
        if connection:
            connection.rollback()
        raise

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


def get_validation(validation_id: str) -> dict | None:
    """Retrieve a persisted validation record by ID."""
    connection = None
    cursor = None

    try:
        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                validation_id,
                question_id,
                question,
                generated_answer,
                context,
                final_status,
                final_score,
                session_id,
                domain,
                difficulty,
                selected_verifiers,
                early_stop_reason,
                signed_score,
                created_at
            FROM validation_records
            WHERE validation_id = %s
            """,
            (validation_id,),
        )

        row = cursor.fetchone()

        if row is None:
            return None

        return {
            "validation_id": str(row[0]),
            "question_id": row[1],
            "question": row[2],
            "generated_answer": row[3],
            "context": row[4],
            "final_status": row[5],
            "final_score": row[6],
            "session_id": str(row[7]) if row[7] else None,
            "domain": row[8],
            "difficulty": row[9],
            "selected_verifiers": row[10] or [],
            "early_stop_reason": row[11],
            "signed_score": row[12],
            "created_at": row[13],
        }

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


def create_validation_record(
    validation_id: str,
    question_id: int | None,
    question: str,
    generated_answer: str,
    context: str | None,
    session_id: str | None,
    connection=None,
):
    """Create the parent validation record before execution starts."""

    owns_connection = connection is None
    cursor = None

    try:
        if owns_connection:
            connection = get_connection()

        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO validation_records (
                validation_id,
                question_id,
                question,
                generated_answer,
                context,
                final_status,
                final_score,
                session_id,
                selected_verifiers,
                created_at
            )
            VALUES (%s, %s, %s, %s, %s, NULL, NULL, %s, %s::jsonb, NOW())
            """,
            (
                validation_id,
                question_id,
                question,
                generated_answer,
                context,
                session_id,
                json.dumps([]),
            ),
        )

        if owns_connection:
            connection.commit()

    except Exception:
        if owns_connection and connection:
            connection.rollback()
        raise

    finally:
        if cursor:
            cursor.close()
        if owns_connection and connection:
            connection.close()


def update_validation_record(
    validation_id: str,
    question_id: int | None,
    question: str,
    generated_answer: str,
    context: str | None,
    final_status: str,
    final_score: float | None,
    session_id: str | None,
    domain: str | None = None,
    difficulty: str | None = None,
    selected_verifiers: list[str] | None = None,
    early_stop_reason: str | None = None,
    signed_score: float | None = None,
):
    """Update an existing validation record with its final result."""

    connection = None
    cursor = None

    try:
        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            UPDATE validation_records
            SET
                question_id = %s,
                question = %s,
                generated_answer = %s,
                context = %s,
                final_status = %s,
                final_score = %s,
                session_id = %s,
                domain = %s,
                difficulty = %s,
                selected_verifiers = %s::jsonb,
                early_stop_reason = %s,
                signed_score = %s
            WHERE validation_id = %s
            """,
            (
                question_id,
                question,
                generated_answer,
                context,
                final_status,
                final_score,
                session_id,
                domain,
                difficulty,
                json.dumps(selected_verifiers or []),
                early_stop_reason,
                signed_score,
                validation_id,
            ),
        )

        if cursor.rowcount != 1:
            raise ValueError(
                f"Validation record not found: {validation_id}"
            )

        connection.commit()

    except Exception:
        if connection:
            connection.rollback()
        raise

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
