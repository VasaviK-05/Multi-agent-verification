import json
from uuid import uuid4

from database import get_connection


def save_verifier_outputs(
    validation_id: str,
    question_id: int,
    results: list,
):
    connection = None
    cursor = None

    try:
        connection = get_connection()
        cursor = connection.cursor()

        for execution_order, result in enumerate(results, start=1):
            cursor.execute(
                """
                INSERT INTO verifier_outputs (
                    verifier_result_id,
                    validation_id,
                    verifier_name,
                    score,
                    passed,
                    reasoning,
                    metadata,
                    latency_ms,
                    created_at,
                    execution_order,
                    question_id
                )
                VALUES (
                    %s, %s, %s, %s, %s,
                    %s, %s::jsonb, %s, NOW(), %s, %s
                )
                """,
                (
                    str(uuid4()),
                    validation_id,
                    result.verifier_name,
                    result.score,
                    result.passed,
                    result.reasoning,
                    json.dumps(result.metadata or {}),
                    None,
                    execution_order,
                    question_id,
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