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
