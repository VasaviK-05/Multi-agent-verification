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