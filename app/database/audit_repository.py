"""PostgreSQL repository for validation-level audit records."""

import json
from typing import Any
from uuid import UUID

from database import get_connection


def _json(value: Any) -> str:
    """Serialize JSON-compatible values without accepting NaN or Infinity."""
    return json.dumps(value, allow_nan=False)


def create_audit(
    *,
    validation_id: str,
    question_id: int | None = None,
    session_id: str | None = None,
    policy_version: str | None = None,
    selected_strategy: str | None = None,
    execution_contract: dict | None = None,
    reputation_snapshot: dict | None = None,
    reputation_snapshot_id: str | None = None,
    selection_plan: dict | None = None,
    run_summary: dict | None = None,
) -> dict:
    """Create an audit for an existing validation record."""
    conn = get_connection()

    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO validation_audits (
                    validation_id,
                    question_id,
                    session_id,
                    run_status,
                    policy_version,
                    selected_strategy,
                    execution_contract,
                    reputation_snapshot,
                    reputation_snapshot_id,
                    selection_plan,
                    run_summary
                )
                VALUES (
                    %s, %s, %s, 'started', %s, %s,
                    %s::jsonb, %s::jsonb, %s,
                    %s::jsonb, %s::jsonb
                )
                RETURNING audit_id, validation_id, run_status, started_at
                """,
                (
                    str(UUID(validation_id)),
                    question_id,
                    str(UUID(session_id)) if session_id else None,
                    policy_version,
                    selected_strategy,
                    _json(execution_contract or {}),
                    _json(reputation_snapshot)
                    if reputation_snapshot is not None
                    else None,
                    str(UUID(reputation_snapshot_id))
                    if reputation_snapshot_id
                    else None,
                    _json(selection_plan or {}),
                    _json(run_summary or {}),
                ),
            )
            row = cursor.fetchone()

        conn.commit()
        return {
            "audit_id": str(row[0]),
            "validation_id": str(row[1]),
            "run_status": row[2],
            "started_at": row[3].isoformat(),
        }
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def update_audit(
    validation_id: str,
    *,
    run_status: str,
    selected_verifiers: list[str] | None = None,
    ranking_explanations: list[dict] | None = None,
    decision_summary: dict | None = None,
    coverage_outcomes: dict | None = None,
    execution_costs: dict | None = None,
    failure_details: list[dict] | None = None,
    selection_plan: dict | None = None,
    run_summary: dict | None = None,
) -> None:
    """Update the audit when the validation finishes or fails."""
    if run_status not in {"completed", "failed", "partial"}:
        raise ValueError("run_status must be completed, failed, or partial")

    conn = get_connection()

    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                UPDATE validation_audits
                SET run_status = %s,
                    completed_at = NOW(),
                    updated_at = NOW(),
                    selected_verifiers = %s::jsonb,
                    ranking_explanations = %s::jsonb,
                    decision_summary = %s::jsonb,
                    coverage_outcomes = %s::jsonb,
                    execution_costs = %s::jsonb,
                    failure_details = %s::jsonb,
                    selection_plan = COALESCE(%s::jsonb, selection_plan),
                    run_summary = COALESCE(%s::jsonb, run_summary)
                WHERE validation_id = %s
                RETURNING audit_id
                """,
                (
                    run_status,
                    _json(selected_verifiers or []),
                    _json(ranking_explanations or []),
                    _json(decision_summary or {}),
                    _json(coverage_outcomes or {}),
                    _json(execution_costs or {}),
                    _json(failure_details or []),
                    _json(selection_plan) if selection_plan is not None else None,
                    _json(run_summary) if run_summary is not None else None,
                    str(UUID(validation_id)),
                ),
            )
            row = cursor.fetchone()
            if row is None:
                raise ValueError(
                    f"No audit exists for validation {validation_id!r}"
                )

        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_audit(validation_id: str) -> dict | None:
    """Retrieve a persisted audit by validation ID."""
    conn = get_connection()

    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT audit_id, validation_id, question_id, session_id,
                       run_status, started_at, completed_at, policy_version,
                       selected_strategy, execution_contract,
                       reputation_snapshot, reputation_snapshot_id,
                       selection_plan, run_summary,
                       selected_verifiers, ranking_explanations,
                       decision_summary, coverage_outcomes, execution_costs,
                       failure_details, created_at, updated_at
                FROM validation_audits
                WHERE validation_id = %s
                """,
                (str(UUID(validation_id)),),
            )
            row = cursor.fetchone()

        if row is None:
            return None

        names = (
            "audit_id", "validation_id", "question_id", "session_id",
            "run_status", "started_at", "completed_at", "policy_version",
            "selected_strategy", "execution_contract", "reputation_snapshot",
            "reputation_snapshot_id", "selection_plan", "run_summary",
            "selected_verifiers", "ranking_explanations",
            "decision_summary", "coverage_outcomes", "execution_costs",
            "failure_details", "created_at", "updated_at",
        )
        result = dict(zip(names, row))

        for key in (
            "audit_id",
            "validation_id",
            "session_id",
            "reputation_snapshot_id",
        ):
            if result[key] is not None:
                result[key] = str(result[key])

        for key in (
            "started_at",
            "completed_at",
            "created_at",
            "updated_at",
        ):
            if result[key] is not None:
                result[key] = result[key].isoformat()

        return result
    finally:
        conn.close()