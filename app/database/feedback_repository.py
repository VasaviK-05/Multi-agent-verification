from uuid import uuid4

from database import get_connection


def save_feedback(
    validation_id: str,
    is_correct: bool,
    comment: str | None = None,
):
    connection = None
    cursor = None

    try:
        connection = get_connection()
        cursor = connection.cursor()

        # Check whether feedback already exists for this validation.
        cursor.execute(
            """
            SELECT id, validation_id, is_correct, comment, created_at
            FROM feedback
            WHERE validation_id = %s
            """,
            (validation_id,),
        )

        existing = cursor.fetchone()

        if existing:
            existing_feedback = {
                "id": existing[0],
                "validation_id": existing[1],
                "is_correct": existing[2],
                "comment": existing[3],
                "created_at": existing[4],
            }

            # Same feedback = safe retry.
            if existing[2] == is_correct:
                connection.commit()
                return existing_feedback

            # Different feedback = conflict.
            raise ValueError(
                "Conflicting feedback already exists for this validation."
            )

        # No existing feedback: create it.
        feedback_id = uuid4()

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