
"""PostgreSQL repository for durable verifier execution and recovery."""

import json
import math
from contextlib import contextmanager
from typing import Any
from uuid import UUID, uuid4

from database import get_connection
from app.game.models import content_id


class ExecutionJournalError(Exception):
    """Base exception for execution journal operations."""


class ExecutionConflictError(ExecutionJournalError):
    """Raised when a requested state transition conflicts with persisted state."""


def _json(value: Any) -> str:
    """Serialize JSON safely, rejecting NaN and Infinity."""
    return json.dumps(value, allow_nan=False)


def _uuid(value: str | UUID) -> str:
    """Validate and normalize a UUID."""
    return str(UUID(str(value)))


@contextmanager
def _connection_scope(connection=None):
    """
    Reuse a caller-owned connection when supplied.

    Otherwise, open and manage a dedicated connection.
    Caller-owned connections are never committed, rolled back, or closed here.
    """
    owned = connection is None
    conn = connection if connection is not None else get_connection()

    try:
        yield conn
        if owned:
            conn.commit()
    except Exception:
        if owned:
            conn.rollback()
        raise
    finally:
        if owned:
            conn.close()


def begin_validation(
    *,
    validation_id: str,
    execution_mode: str,
    request_payload: dict,
    connection=None,
) -> dict:
    """Create a durable execution record before validation begins."""

    validation_id = _uuid(validation_id)

    if not isinstance(request_payload, dict):
        raise ValueError("request_payload must be a dictionary")

    if not isinstance(execution_mode, str) or not execution_mode.strip():
        raise ValueError("execution_mode must be a non-empty string")

    serialized = _json(request_payload)
    request_digest = content_id(request_payload)

    with _connection_scope(connection) as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO validation_executions (
                    validation_id,
                    execution_status,
                    execution_mode,
                    request_payload,
                    request_digest
                )
                VALUES (%s, 'initializing', %s, %s::jsonb, %s)
                RETURNING
                    validation_id,
                    execution_status,
                    execution_mode,
                    request_digest,
                    created_at
                """,
                (
                    validation_id,
                    execution_mode,
                    serialized,
                    request_digest,
                ),
            )

            row = cursor.fetchone()

    return {
        "validation_id": str(row[0]),
        "execution_status": row[1],
        "execution_mode": row[2],
        "request_digest": row[3],
        "created_at": row[4].isoformat(),
    }


def mark_execution_ready(
    *,
    validation_id: str,
    plan_payload: dict,
    analysis_snapshot: dict | None = None,
    connection=None,
) -> dict:
    """Persist the execution plan and transition initializing to ready."""

    validation_id = _uuid(validation_id)

    if not isinstance(plan_payload, dict):
        raise ValueError("plan_payload must be a dictionary")

    if analysis_snapshot is not None and not isinstance(
        analysis_snapshot, dict
    ):
        raise ValueError("analysis_snapshot must be a dictionary or None")

    serialized_plan = _json(plan_payload)
    plan_digest = content_id(plan_payload)
    serialized_analysis = (
        _json(analysis_snapshot)
        if analysis_snapshot is not None
        else None
    )

    with _connection_scope(connection) as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                UPDATE validation_executions
                SET
                    execution_status = 'ready',
                    plan_payload = %s::jsonb,
                    plan_digest = %s,
                    analysis_snapshot = %s::jsonb,
                    updated_at = NOW()
                WHERE validation_id = %s
                  AND execution_status = 'initializing'
                RETURNING
                    validation_id,
                    execution_status,
                    plan_digest,
                    updated_at
                """,
                (
                    serialized_plan,
                    plan_digest,
                    serialized_analysis,
                    validation_id,
                ),
            )

            row = cursor.fetchone()

            if row is None:
                cursor.execute(
                    """
                    SELECT execution_status
                    FROM validation_executions
                    WHERE validation_id = %s
                    """,
                    (validation_id,),
                )
                existing = cursor.fetchone()

                if existing is None:
                    raise ExecutionJournalError(
                        f"Unknown validation execution: {validation_id}"
                    )

                raise ExecutionConflictError(
                    f"Cannot mark execution ready from status "
                    f"{existing[0]!r}"
                )

    return {
        "validation_id": str(row[0]),
        "execution_status": row[1],
        "plan_digest": row[2],
        "updated_at": row[3].isoformat(),
    }



def mark_execution_running(
    *,
    validation_id: str,
    worker_id: str | None = None,
    lease_seconds: int = 60,
    connection=None,
) -> dict:
    """Acquire a lease while transitioning a ready execution to running."""

    validation_id = _uuid(validation_id)

    if (
        isinstance(lease_seconds, bool)
        or not isinstance(lease_seconds, int)
        or lease_seconds < 15
    ):
        raise ValueError("lease_seconds must be an integer >= 15")

    worker_id = worker_id or f"worker-{uuid4()}"

    if not isinstance(worker_id, str) or not worker_id.strip():
        raise ValueError("worker_id must be non-empty")

    lease_token = uuid4()

    with _connection_scope(connection) as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                UPDATE validation_executions
                SET
                    execution_status = 'running',
                    lease_token = %s,
                    worker_id = %s,
                    heartbeat_at = NOW(),
                    lease_expires_at =
                        NOW() + (%s * INTERVAL '1 second'),
                    updated_at = NOW()
                WHERE validation_id = %s
                  AND execution_status = 'ready'
                RETURNING
                    validation_id,
                    execution_status,
                    lease_token,
                    worker_id,
                    heartbeat_at,
                    lease_expires_at
                """,
                (
                    str(lease_token),
                    worker_id.strip(),
                    lease_seconds,
                    validation_id,
                ),
            )

            row = cursor.fetchone()

            if row is None:
                raise ExecutionConflictError(
                    "Execution could not acquire its running lease."
                )

    return {
        "validation_id": str(row[0]),
        "execution_status": row[1],
        "lease_token": str(row[2]),
        "worker_id": row[3],
        "heartbeat_at": row[4].isoformat(),
        "lease_expires_at": row[5].isoformat(),
    }


def renew_execution_lease(
    *,
    validation_id: str,
    lease_token: str,
    lease_seconds: int = 60,
    connection=None,
) -> bool:
    """Renew only a lease that is still valid and owned by this worker."""

    validation_id = _uuid(validation_id)
    lease_token = _uuid(lease_token)

    if (
        isinstance(lease_seconds, bool)
        or not isinstance(lease_seconds, int)
        or lease_seconds < 15
    ):
        raise ValueError("lease_seconds must be an integer >= 15")

    with _connection_scope(connection) as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                UPDATE validation_executions
                SET
                    heartbeat_at = NOW(),
                    lease_expires_at =
                        NOW() + (%s * INTERVAL '1 second'),
                    updated_at = NOW()
                WHERE validation_id = %s
                  AND execution_status = 'running'
                  AND lease_token = %s
                  AND lease_expires_at > NOW()
                RETURNING validation_id
                """,
                (lease_seconds, validation_id, lease_token),
            )

            return cursor.fetchone() is not None


def mark_execution_completed(
    *,
    validation_id: str,
    final_response: dict,
    lease_token: str | None = None,
    connection=None,
) -> dict:
    """Persist the final response and complete a running execution."""

    validation_id = _uuid(validation_id)

    if not isinstance(final_response, dict):
        raise ValueError("final_response must be a dictionary")

    if lease_token is not None:
        lease_token = _uuid(lease_token)

    serialized_response = _json(final_response)
    response_digest = content_id(final_response)

    with _connection_scope(connection) as conn:
        with conn.cursor() as cursor:
            if lease_token is not None:
                cursor.execute(
                    """
                    UPDATE validation_executions
                    SET
                        execution_status = 'completed',
                        final_response = %s::jsonb,
                        final_response_digest = %s,
                        completed_at = NOW(),
                        lease_token = NULL,
                        worker_id = NULL,
                        heartbeat_at = NULL,
                        lease_expires_at = NULL,
                        updated_at = NOW()
                    WHERE validation_id = %s
                      AND execution_status = 'running'
                      AND lease_token = %s
                      AND lease_expires_at > NOW()
                    RETURNING
                        validation_id,
                        execution_status,
                        final_response_digest,
                        completed_at
                    """,
                    (
                        serialized_response,
                        response_digest,
                        validation_id,
                        lease_token,
                    ),
                )
            else:
                cursor.execute(
                    """
                    UPDATE validation_executions
                    SET
                        execution_status = 'completed',
                        final_response = %s::jsonb,
                        final_response_digest = %s,
                        completed_at = NOW(),
                        lease_token = NULL,
                        worker_id = NULL,
                        heartbeat_at = NULL,
                        lease_expires_at = NULL,
                        updated_at = NOW()
                    WHERE validation_id = %s
                      AND execution_status = 'running'
                    RETURNING
                        validation_id,
                        execution_status,
                        final_response_digest,
                        completed_at
                    """,
                    (
                        serialized_response,
                        response_digest,
                        validation_id,
                    ),
                )

            row = cursor.fetchone()

            if row is None:
                raise ExecutionConflictError(
                    "Cannot complete execution: it is missing, "
                    "not running, or the lease is no longer owned."
                )

    return {
        "validation_id": str(row[0]),
        "execution_status": row[1],
        "final_response_digest": row[2],
        "completed_at": row[3].isoformat(),
    }


def mark_execution_failed(
    *,
    validation_id: str,
    failure_details: dict,
    lease_token: str | None = None,
    connection=None,
) -> dict:
    """Persist execution failure details and mark execution failed."""

    validation_id = _uuid(validation_id)

    if not isinstance(failure_details, dict):
        raise ValueError("failure_details must be a dictionary")

    if lease_token is not None:
        lease_token = _uuid(lease_token)

    serialized_details = _json(failure_details)

    with _connection_scope(connection) as conn:
        with conn.cursor() as cursor:
            if lease_token is not None:
                cursor.execute(
                    """
                    UPDATE validation_executions
                    SET
                        execution_status = 'failed',
                        failure_details = %s::jsonb,
                        lease_token = NULL,
                        worker_id = NULL,
                        heartbeat_at = NULL,
                        lease_expires_at = NULL,
                        updated_at = NOW()
                    WHERE validation_id = %s
                      AND execution_status = 'running'
                      AND lease_token = %s
                      AND lease_expires_at > NOW()
                    RETURNING
                        validation_id,
                        execution_status,
                        failure_details,
                        updated_at
                    """,
                    (
                        serialized_details,
                        validation_id,
                        lease_token,
                    ),
                )
            else:
                cursor.execute(
                    """
                    UPDATE validation_executions
                    SET
                        execution_status = 'failed',
                        failure_details = %s::jsonb,
                        lease_token = NULL,
                        worker_id = NULL,
                        heartbeat_at = NULL,
                        lease_expires_at = NULL,
                        updated_at = NOW()
                    WHERE validation_id = %s
                      AND execution_status IN (
                          'initializing', 'ready', 'running'
                      )
                    RETURNING
                        validation_id,
                        execution_status,
                        failure_details,
                        updated_at
                    """,
                    (serialized_details, validation_id),
                )

            row = cursor.fetchone()

            if row is None:
                raise ExecutionConflictError(
                    "Cannot fail execution: it is missing, "
                    "not in a valid state, or the lease is no longer owned."
                )

    return {
        "validation_id": str(row[0]),
        "execution_status": row[1],
        "failure_details": row[2],
        "updated_at": row[3].isoformat(),
    }


def mark_execution_blocked(
    *,
    validation_id: str,
    block_reason: str,
    connection=None,
) -> dict:
    """Persist a blocked execution and its reason."""

    validation_id = _uuid(validation_id)

    if not isinstance(block_reason, str) or not block_reason.strip():
        raise ValueError("block_reason must be a non-empty string")

    block_reason = block_reason.strip()

    with _connection_scope(connection) as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                UPDATE validation_executions
                SET
                    lease_token = NULL,
                    worker_id = NULL,
                    heartbeat_at = NULL,
                    lease_expires_at = NULL,
                    execution_status = 'blocked',
                    block_reason = %s,
                    updated_at = NOW()
                WHERE validation_id = %s
                  AND execution_status IN (
                      'initializing', 'ready', 'running'
                  )
                RETURNING
                    validation_id,
                    execution_status,
                    block_reason,
                    updated_at
                """,
                (block_reason, validation_id),
            )

            row = cursor.fetchone()

            if row is None:
                cursor.execute(
                    """
                    SELECT execution_status
                    FROM validation_executions
                    WHERE validation_id = %s
                    """,
                    (validation_id,),
                )
                existing = cursor.fetchone()

                if existing is None:
                    raise ExecutionJournalError(
                        f"Unknown validation execution: {validation_id}"
                    )

                raise ExecutionConflictError(
                    f"Cannot block execution from status "
                    f"{existing[0]!r}"
                )

    return {
        "validation_id": str(row[0]),
        "execution_status": row[1],
        "block_reason": row[2],
        "updated_at": row[3].isoformat(),
    }

def create_verifier_attempt(
    *,
    validation_id: str,
    call_key: str,
    execution_order: int,
    verifier_name: str,
    component_id: str | None = None,
    report_validation_id: str | None = None,
    lease_token: str | None = None,
    connection=None,
) -> dict:
    """Persist a planned verifier attempt."""

    validation_id = _uuid(validation_id)

    if not isinstance(call_key, str) or not call_key.strip():
        raise ValueError("call_key must be a non-empty string")

    if not isinstance(verifier_name, str) or not verifier_name.strip():
        raise ValueError("verifier_name must be a non-empty string")

    if isinstance(execution_order, bool) or not isinstance(execution_order, int):
        raise ValueError("execution_order must be an integer")

    if execution_order < 0:
        raise ValueError("execution_order must be non-negative")

    if component_id is not None and not isinstance(component_id, str):
        raise ValueError("component_id must be a string or None")

    if report_validation_id is not None:
        report_validation_id = _uuid(report_validation_id)

    if lease_token is not None:
        lease_token = _uuid(lease_token)

    with _connection_scope(connection) as conn:
        with conn.cursor() as cursor:
            if lease_token is not None:
                cursor.execute(
                    """
                    INSERT INTO live_verifier_attempts (
                        validation_id,
                        call_key,
                        execution_order,
                        verifier_name,
                        component_id,
                        report_validation_id,
                        lifecycle_status
                    )
                    SELECT
                        e.validation_id,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        'planned'
                    FROM validation_executions e
                    WHERE e.validation_id = %s
                      AND e.execution_status = 'running'
                      AND e.lease_token = %s
                      AND e.lease_expires_at > NOW()
                    RETURNING
                        attempt_id,
                        validation_id,
                        call_key,
                        execution_order,
                        verifier_name,
                        component_id,
                        report_validation_id,
                        lifecycle_status,
                        created_at
                    """,
                    (
                        call_key.strip(),
                        execution_order,
                        verifier_name.strip(),
                        component_id,
                        report_validation_id,
                        validation_id,
                        lease_token,
                    ),
                )
            else:
                cursor.execute(
                    """
                    INSERT INTO live_verifier_attempts (
                        validation_id,
                        call_key,
                        execution_order,
                        verifier_name,
                        component_id,
                        report_validation_id,
                        lifecycle_status
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, 'planned')
                    RETURNING
                        attempt_id,
                        validation_id,
                        call_key,
                        execution_order,
                        verifier_name,
                        component_id,
                        report_validation_id,
                        lifecycle_status,
                        created_at
                    """,
                    (
                        validation_id,
                        call_key.strip(),
                        execution_order,
                        verifier_name.strip(),
                        component_id,
                        report_validation_id,
                    ),
                )

            row = cursor.fetchone()

            if row is None:
                raise ExecutionConflictError(
                    "Cannot create verifier attempt: execution lease "
                    "is missing, expired, or no longer owned."
                )

    return {
        "attempt_id": str(row[0]),
        "validation_id": str(row[1]),
        "call_key": row[2],
        "execution_order": row[3],
        "verifier_name": row[4],
        "component_id": row[5],
        "report_validation_id": (
            str(row[6]) if row[6] is not None else None
        ),
        "lifecycle_status": row[7],
        "created_at": row[8].isoformat(),
    }


def _validate_attempt_metrics(
    duration_ms=None,
    estimated_cost=None,
    cost_units=None,
):
    """Validate optional execution metrics."""

    for name, value in (
        ("duration_ms", duration_ms),
        ("estimated_cost", estimated_cost),
    ):
        if value is not None:
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(value)
                or value < 0
            ):
                raise ValueError(
                    f"{name} must be a finite non-negative number"
                )

    if cost_units is not None:
        if not isinstance(cost_units, str) or not cost_units.strip():
            raise ValueError("cost_units must be a non-empty string")


def _attempt_result(row):
    """Convert a persisted attempt row into a dictionary."""

    return {
        "attempt_id": str(row[0]),
        "lifecycle_status": row[1],
        "outcome": row[2],
        "report": row[3],
        "report_digest": row[4],
        "error_type": row[5],
        "error_message": row[6],
        "started_at": row[7].isoformat() if row[7] else None,
        "completed_at": row[8].isoformat() if row[8] else None,
        "duration_ms": row[9],
        "estimated_cost": row[10],
        "cost_units": row[11],
        "updated_at": row[12].isoformat(),
    }


def _raise_attempt_transition_error(cursor, attempt_id, target_status):
    """Raise an appropriate error for a missing or invalid attempt."""

    cursor.execute(
        """
        SELECT lifecycle_status
        FROM live_verifier_attempts
        WHERE attempt_id = %s
        """,
        (attempt_id,),
    )

    existing = cursor.fetchone()

    if existing is None:
        raise ExecutionJournalError(
            f"Unknown verifier attempt: {attempt_id}"
        )

    raise ExecutionConflictError(
        f"Cannot transition verifier attempt from "
        f"{existing[0]!r} to {target_status!r}"
    )


def _transition_started_attempt(
    *,
    attempt_id,
    target_status,
    set_clause,
    parameters,
    lease_token=None,
    connection=None,
):
    """Apply a terminal transition to an already-started attempt."""

    attempt_id = _uuid(attempt_id)

    if lease_token is not None:
        lease_token = _uuid(lease_token)

    returning = """
        RETURNING
            attempt_id,
            lifecycle_status,
            outcome,
            report,
            report_digest,
            error_type,
            error_message,
            started_at,
            completed_at,
            duration_ms,
            estimated_cost,
            cost_units,
            updated_at
    """

    lease_condition = ""
    query_parameters = (*parameters, attempt_id)

    if lease_token is not None:
        lease_condition = """
            AND EXISTS (
                SELECT 1
                FROM validation_executions e
                WHERE e.validation_id =
                    live_verifier_attempts.validation_id
                  AND e.execution_status = 'running'
                  AND e.lease_token = %s
                  AND e.lease_expires_at > NOW()
            )
        """
        query_parameters = (*query_parameters, lease_token)

    with _connection_scope(connection) as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                f"""
                UPDATE live_verifier_attempts
                SET
                    {set_clause},
                    updated_at = NOW()
                WHERE attempt_id = %s
                  AND lifecycle_status = 'started'
                  {lease_condition}
                {returning}
                """,
                query_parameters,
            )

            row = cursor.fetchone()

            if row is None:
                _raise_attempt_transition_error(
                    cursor,
                    attempt_id,
                    target_status,
                )

                # Defensive: the helper above always raises.
                raise ExecutionConflictError(
                    "Verifier attempt transition was rejected."
                )

    return _attempt_result(row)


def mark_verifier_attempt_started(
    *,
    attempt_id: str,
    lease_token: str | None = None,
    connection=None,
) -> dict:
    """Mark a planned verifier attempt as started."""

    attempt_id = _uuid(attempt_id)

    if lease_token is not None:
        lease_token = _uuid(lease_token)

    lease_condition = ""
    parameters = [attempt_id]

    if lease_token is not None:
        lease_condition = """
            AND EXISTS (
                SELECT 1
                FROM validation_executions e
                WHERE e.validation_id =
                    live_verifier_attempts.validation_id
                  AND e.execution_status = 'running'
                  AND e.lease_token = %s
                  AND e.lease_expires_at > NOW()
            )
        """
        parameters.append(lease_token)

    with _connection_scope(connection) as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                f"""
                UPDATE live_verifier_attempts
                SET
                    lifecycle_status = 'started',
                    started_at = NOW(),
                    updated_at = NOW()
                WHERE attempt_id = %s
                  AND lifecycle_status = 'planned'
                  {lease_condition}
                RETURNING
                    attempt_id,
                    lifecycle_status,
                    outcome,
                    report,
                    report_digest,
                    error_type,
                    error_message,
                    started_at,
                    completed_at,
                    duration_ms,
                    estimated_cost,
                    cost_units,
                    updated_at
                """,
                tuple(parameters),
            )

            row = cursor.fetchone()

            if row is None:
                _raise_attempt_transition_error(
                    cursor,
                    attempt_id,
                    "started",
                )

                raise ExecutionConflictError(
                    "Verifier attempt could not be started."
                )

    return _attempt_result(row)


def mark_verifier_attempt_completed(
    *,
    attempt_id: str,
    report: dict,
    outcome: str,
    duration_ms=None,
    estimated_cost=None,
    cost_units=None,
    lease_token: str | None = None,
    connection=None,
) -> dict:
    """Persist a successful verifier report."""

    if not isinstance(report, dict):
        raise ValueError("report must be a dictionary")

    if outcome not in ("directional", "abstention"):
        raise ValueError(
            "outcome must be 'directional' or 'abstention'"
        )

    _validate_attempt_metrics(
        duration_ms,
        estimated_cost,
        cost_units,
    )

    serialized_report = _json(report)
    report_digest = content_id(report)

    return _transition_started_attempt(
        attempt_id=attempt_id,
        target_status="completed",
        set_clause="""
            lifecycle_status = 'completed',
            outcome = %s,
            report = %s::jsonb,
            report_digest = %s,
            completed_at = NOW(),
            duration_ms = %s,
            estimated_cost = %s,
            cost_units = %s
        """,
        parameters=(
            outcome,
            serialized_report,
            report_digest,
            duration_ms,
            estimated_cost,
            cost_units,
        ),
        lease_token=lease_token,
        connection=connection,
    )


def mark_verifier_attempt_failed(
    *,
    attempt_id: str,
    error_type: str,
    error_message: str,
    duration_ms=None,
    estimated_cost=None,
    cost_units=None,
    lease_token: str | None = None,
    connection=None,
) -> dict:
    """Persist a verifier execution failure."""

    if not isinstance(error_type, str) or not error_type.strip():
        raise ValueError("error_type must be non-empty")

    if not isinstance(error_message, str) or not error_message.strip():
        raise ValueError("error_message must be non-empty")

    _validate_attempt_metrics(
        duration_ms,
        estimated_cost,
        cost_units,
    )

    return _transition_started_attempt(
        attempt_id=attempt_id,
        target_status="execution_failed",
        set_clause="""
            lifecycle_status = 'execution_failed',
            outcome = 'failed',
            error_type = %s,
            error_message = %s,
            completed_at = NOW(),
            duration_ms = %s,
            estimated_cost = %s,
            cost_units = %s
        """,
        parameters=(
            error_type.strip(),
            error_message.strip(),
            duration_ms,
            estimated_cost,
            cost_units,
        ),
        lease_token=lease_token,
        connection=connection,
    )


def mark_verifier_attempt_unavailable(
    *,
    attempt_id: str,
    reason: str | None = None,
    duration_ms=None,
    estimated_cost=None,
    cost_units=None,
    lease_token: str | None = None,
    connection=None,
) -> dict:
    """Persist an unavailable verifier attempt."""

    if reason is not None:
        if not isinstance(reason, str) or not reason.strip():
            raise ValueError("reason must be a non-empty string")

    _validate_attempt_metrics(
        duration_ms,
        estimated_cost,
        cost_units,
    )

    return _transition_started_attempt(
        attempt_id=attempt_id,
        target_status="unavailable",
        set_clause="""
            lifecycle_status = 'unavailable',
            outcome = 'unavailable',
            error_message = %s,
            completed_at = NOW(),
            duration_ms = %s,
            estimated_cost = %s,
            cost_units = %s
        """,
        parameters=(
            reason.strip() if reason is not None else None,
            duration_ms,
            estimated_cost,
            cost_units,
        ),
        lease_token=lease_token,
        connection=connection,
    )


def mark_verifier_attempt_error(
    *,
    attempt_id: str,
    error_type: str,
    error_message: str,
    duration_ms=None,
    estimated_cost=None,
    cost_units=None,
    lease_token: str | None = None,
    connection=None,
) -> dict:
    """Persist a verifier attempt that ended in an error state."""

    if not isinstance(error_type, str) or not error_type.strip():
        raise ValueError("error_type must be non-empty")

    if not isinstance(error_message, str) or not error_message.strip():
        raise ValueError("error_message must be non-empty")

    _validate_attempt_metrics(
        duration_ms,
        estimated_cost,
        cost_units,
    )

    return _transition_started_attempt(
        attempt_id=attempt_id,
        target_status="error",
        set_clause="""
            lifecycle_status = 'error',
            outcome = 'error',
            error_type = %s,
            error_message = %s,
            completed_at = NOW(),
            duration_ms = %s,
            estimated_cost = %s,
            cost_units = %s
        """,
        parameters=(
            error_type.strip(),
            error_message.strip(),
            duration_ms,
            estimated_cost,
            cost_units,
        ),
        lease_token=lease_token,
        connection=connection,
    )


def mark_verifier_attempt_ambiguous(
    *,
    attempt_id: str,
    connection=None,
) -> dict:
    """Mark a started verifier attempt as ambiguous."""

    return _transition_started_attempt(
        attempt_id=attempt_id,
        target_status="ambiguous",
        set_clause="""
            lifecycle_status = 'ambiguous',
            outcome = NULL
        """,
        parameters=(),
        connection=connection,
    )


def _execution_result(row):
    """Convert an execution journal row into a dictionary."""

    return {
        "validation_id": str(row[0]),
        "execution_status": row[1],
        "execution_mode": row[2],
        "request_payload": row[3],
        "request_digest": row[4],
        "analysis_snapshot": row[5],
        "plan_payload": row[6],
        "plan_digest": row[7],
        "final_response": row[8],
        "final_response_digest": row[9],
        "failure_details": row[10],
        "block_reason": row[11],
        "created_at": row[12].isoformat() if row[12] else None,
        "updated_at": row[13].isoformat() if row[13] else None,
        "completed_at": row[14].isoformat() if row[14] else None,
    }


def get_execution(
    *,
    validation_id: str,
    connection=None,
) -> dict | None:
    """Retrieve a persisted execution journal by validation ID."""

    validation_id = _uuid(validation_id)

    with _connection_scope(connection) as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    validation_id,
                    execution_status,
                    execution_mode,
                    request_payload,
                    request_digest,
                    analysis_snapshot,
                    plan_payload,
                    plan_digest,
                    final_response,
                    final_response_digest,
                    failure_details,
                    block_reason,
                    created_at,
                    updated_at,
                    completed_at
                FROM validation_executions
                WHERE validation_id = %s
                """,
                (validation_id,),
            )

            row = cursor.fetchone()

    if row is None:
        return None

    return _execution_result(row)


def get_verifier_attempts(
    *,
    validation_id: str,
    connection=None,
) -> list[dict]:
    """Retrieve all verifier attempts in execution order."""

    validation_id = _uuid(validation_id)

    with _connection_scope(connection) as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    attempt_id,
                    validation_id,
                    call_key,
                    execution_order,
                    verifier_name,
                    component_id,
                    report_validation_id,
                    lifecycle_status,
                    outcome,
                    report,
                    report_digest,
                    error_type,
                    error_message,
                    started_at,
                    completed_at,
                    duration_ms,
                    estimated_cost,
                    cost_units,
                    identity_binding,
                    created_at,
                    updated_at
                FROM live_verifier_attempts
                WHERE validation_id = %s
                ORDER BY execution_order ASC, created_at ASC
                """,
                (validation_id,),
            )

            rows = cursor.fetchall()

    return [
        {
            "attempt_id": str(row[0]),
            "validation_id": str(row[1]),
            "call_key": row[2],
            "execution_order": row[3],
            "verifier_name": row[4],
            "component_id": row[5],
            "report_validation_id": (
                str(row[6]) if row[6] is not None else None
            ),
            "lifecycle_status": row[7],
            "outcome": row[8],
            "report": row[9],
            "report_digest": row[10],
            "error_type": row[11],
            "error_message": row[12],
            "started_at": row[13].isoformat() if row[13] else None,
            "completed_at": row[14].isoformat() if row[14] else None,
            "duration_ms": row[15],
            "estimated_cost": row[16],
            "cost_units": row[17],
            "identity_binding": row[18],
            "created_at": row[19].isoformat() if row[19] else None,
            "updated_at": row[20].isoformat() if row[20] else None,
        }
        for row in rows
    ]


def get_incomplete_executions(
    *,
    limit: int = 100,
    connection=None,
) -> list[dict]:
    """
    Retrieve non-terminal executions that may need recovery.

    Blocked executions are included for inspection, but should not
    automatically be resumed without checking their block reason.
    """

    if isinstance(limit, bool) or not isinstance(limit, int) or limit <= 0:
        raise ValueError("limit must be a positive integer")

    with _connection_scope(connection) as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    validation_id,
                    execution_status,
                    execution_mode,
                    request_payload,
                    request_digest,
                    analysis_snapshot,
                    plan_payload,
                    plan_digest,
                    final_response,
                    final_response_digest,
                    failure_details,
                    block_reason,
                    created_at,
                    updated_at,
                    completed_at
                FROM validation_executions
                WHERE execution_status IN (
                    'initializing',
                    'ready',
                    'running',
                    'blocked'
                )
                ORDER BY updated_at ASC, created_at ASC
                LIMIT %s
                """,
                (limit,),
            )

            rows = cursor.fetchall()

    return [_execution_result(row) for row in rows]
