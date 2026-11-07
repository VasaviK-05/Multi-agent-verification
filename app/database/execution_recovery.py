
"""Recovery of incomplete or abandoned validation executions."""

from database import get_connection

from app.database.execution_journal_repository import (
    mark_execution_blocked,
)


def inspect_and_recover_incomplete_executions(
    limit: int = 100,
    grace_period_seconds: int = 120,
) -> list[dict]:
    """
    Recover stale executions and report executions already blocked.

    Running executions are recoverable only when their lease is
    missing or expired. Initializing and ready executions are
    recoverable only after the grace period.
    """

    if isinstance(limit, bool) or not isinstance(limit, int) or limit <= 0:
        raise ValueError("limit must be a positive integer")

    if (
        isinstance(grace_period_seconds, bool)
        or not isinstance(grace_period_seconds, int)
        or grace_period_seconds <= 0
    ):
        raise ValueError("grace_period_seconds must be a positive integer")

    connection = get_connection()
    recovery_results = []

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT validation_id, execution_status
                FROM validation_executions
                WHERE
                    (
                        execution_status IN ('initializing', 'ready')
                        AND updated_at <=
                            NOW() - (%s * INTERVAL '1 second')
                    )
                    OR (
                        execution_status = 'running'
                        AND (
                            lease_expires_at IS NULL
                            OR lease_expires_at <= NOW()
                        )
                    )
                    OR execution_status = 'blocked'
                ORDER BY updated_at ASC, created_at ASC
                LIMIT %s
                FOR UPDATE SKIP LOCKED
                """,
                (grace_period_seconds, limit),
            )

            executions = cursor.fetchall()

            for validation_id, status in executions:
                validation_id = str(validation_id)

                if status == "blocked":
                    recovery_results.append(
                        {
                            "validation_id": validation_id,
                            "action": "already_blocked",
                            "attempts_marked_ambiguous": [],
                        }
                    )
                    continue

                cursor.execute(
                    """
                    UPDATE live_verifier_attempts
                    SET lifecycle_status = 'ambiguous',
                        outcome = NULL,
                        updated_at = NOW()
                    WHERE validation_id = %s
                      AND lifecycle_status = 'started'
                    RETURNING attempt_id
                    """,
                    (validation_id,),
                )

                ambiguous = [
                    str(row[0]) for row in cursor.fetchall()
                ]

                reason = (
                    "Stale execution detected. "
                    f"Previous status: {status}. "
                    "Execution requires manual inspection. "
                    f"Started attempts marked ambiguous: {len(ambiguous)}."
                )

                mark_execution_blocked(
                    validation_id=validation_id,
                    block_reason=reason,
                    connection=connection,
                )

                recovery_results.append(
                    {
                        "validation_id": validation_id,
                        "action": "blocked_for_inspection",
                        "attempts_marked_ambiguous": ambiguous,
                    }
                )

        connection.commit()
        return recovery_results

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()
