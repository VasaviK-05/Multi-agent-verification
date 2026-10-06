from uuid import uuid4

from database import get_connection


def save_feedback(
    validation_id: str,
    is_correct: bool,
    comment: str | None = None,
):
    feedback_id = uuid4()

    connection = None
    cursor = None

    try:
        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO feedback (
                id,
                validation_id,
                is_correct,
                comment,
                created_at
            )
            VALUES (%s, %s, %s, %s, NOW())
            RETURNING id, validation_id, is_correct, comment, created_at
            """,
            (
                str(feedback_id),
                validation_id,
                is_correct,
                comment,
            ),
        )

        row = cursor.fetchone()
        connection.commit()

        return {
            "id": row[0],
            "validation_id": row[1],
            "is_correct": row[2],
            "comment": row[3],
            "created_at": row[4],
        }

    except Exception:
        if connection:
            connection.rollback()
        raise

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()