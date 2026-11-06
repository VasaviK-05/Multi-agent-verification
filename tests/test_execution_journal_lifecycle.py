
import os
from uuid import uuid4

import psycopg2

import pytest
from dotenv import load_dotenv

from database import get_connection
from app.database.execution_journal_repository import (
    begin_validation,
    mark_execution_ready,
    mark_execution_running,
    mark_execution_completed,
    mark_execution_failed,
    mark_execution_blocked,
    ExecutionConflictError,
    create_verifier_attempt,
    mark_verifier_attempt_started,
    mark_verifier_attempt_completed,
    mark_verifier_attempt_failed,
    mark_verifier_attempt_unavailable,
    mark_verifier_attempt_error,
    mark_verifier_attempt_ambiguous,
    get_execution,
    get_verifier_attempts,
    get_incomplete_executions,
)

load_dotenv()


def test_mark_execution_ready_persists_plan():
    assert os.getenv("DB_NAME") == "capstone_recovery_test", (
        "Refusing to run outside capstone_recovery_test"
    )

    validation_id = str(uuid4())
    request = {"question": "What is 2 + 2?", "answer": "4"}
    plan = {"selected_verifiers": ["verifier_a", "verifier_b"]}

    conn = get_connection()

    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO validation_records (
                    validation_id, question, generated_answer
                )
                VALUES (%s, %s, %s)
                """,
                (validation_id, request["question"], request["answer"]),
            )
        conn.commit()

        begin_validation(
            validation_id=validation_id,
            execution_mode="baseline",
            request_payload=request,
        )

        result = mark_execution_ready(
            validation_id=validation_id,
            plan_payload=plan,
            analysis_snapshot={"domain": "mathematics"},
        )

        assert result["execution_status"] == "ready"
        assert result["plan_digest"]

        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT execution_status, plan_payload, plan_digest,
                       analysis_snapshot
                FROM validation_executions
                WHERE validation_id = %s
                """,
                (validation_id,),
            )
            row = cursor.fetchone()

        assert row[0] == "ready"
        assert row[1] == plan
        assert row[2] == result["plan_digest"]
        assert row[3] == {"domain": "mathematics"}

        with pytest.raises(ExecutionConflictError):
            mark_execution_ready(
                validation_id=validation_id,
                plan_payload=plan,
            )

    finally:
        conn.rollback()
        with conn.cursor() as cursor:
            cursor.execute(
                "DELETE FROM validation_executions WHERE validation_id = %s",
                (validation_id,),
            )
            cursor.execute(
                "DELETE FROM validation_records WHERE validation_id = %s",
                (validation_id,),
            )
        conn.commit()
        conn.close()


def test_mark_execution_running_persists_status():
    assert os.getenv("DB_NAME") == "capstone_recovery_test", (
        "Refusing to run outside capstone_recovery_test"
    )

    validation_id = str(uuid4())
    conn = get_connection()

    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO validation_records (
                    validation_id, question, generated_answer
                )
                VALUES (%s, %s, %s)
                """,
                (validation_id, "Test question", "Test answer"),
            )
        conn.commit()

        begin_validation(
            validation_id=validation_id,
            execution_mode="baseline",
            request_payload={"question": "Test question"},
        )

        mark_execution_ready(
            validation_id=validation_id,
            plan_payload={"selected_verifiers": ["verifier_a"]},
        )

        result = mark_execution_running(validation_id=validation_id)

        assert result["execution_status"] == "running"

        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT execution_status
                FROM validation_executions
                WHERE validation_id = %s
                """,
                (validation_id,),
            )
            row = cursor.fetchone()

        assert row[0] == "running"

        with pytest.raises(ExecutionConflictError):
            mark_execution_running(validation_id=validation_id)

    finally:
        conn.rollback()
        with conn.cursor() as cursor:
            cursor.execute(
                "DELETE FROM validation_executions WHERE validation_id = %s",
                (validation_id,),
            )
            cursor.execute(
                "DELETE FROM validation_records WHERE validation_id = %s",
                (validation_id,),
            )
        conn.commit()
        conn.close()


def test_mark_execution_completed_persists_response():
    assert os.getenv("DB_NAME") == "capstone_recovery_test", (
        "Refusing to run outside capstone_recovery_test"
    )

    validation_id = str(uuid4())
    final_response = {
        "final_status": "approved",
        "final_score": 0.95,
        "answer": "The answer is 4.",
    }

    conn = get_connection()

    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO validation_records (
                    validation_id, question, generated_answer
                )
                VALUES (%s, %s, %s)
                """,
                (validation_id, "What is 2 + 2?", "4"),
            )
        conn.commit()

        begin_validation(
            validation_id=validation_id,
            execution_mode="baseline",
            request_payload={"question": "What is 2 + 2?"},
        )

        mark_execution_ready(
            validation_id=validation_id,
            plan_payload={"selected_verifiers": ["verifier_a"]},
        )

        mark_execution_running(validation_id=validation_id)

        result = mark_execution_completed(
            validation_id=validation_id,
            final_response=final_response,
        )

        assert result["execution_status"] == "completed"
        assert result["final_response_digest"]

        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    execution_status,
                    final_response,
                    final_response_digest,
                    completed_at
                FROM validation_executions
                WHERE validation_id = %s
                """,
                (validation_id,),
            )
            row = cursor.fetchone()

        assert row[0] == "completed"
        assert row[1] == final_response
        assert row[2] == result["final_response_digest"]
        assert row[3] is not None

        with pytest.raises(ExecutionConflictError):
            mark_execution_completed(
                validation_id=validation_id,
                final_response=final_response,
            )

    finally:
        conn.rollback()

        with conn.cursor() as cursor:
            cursor.execute(
                "DELETE FROM validation_executions WHERE validation_id = %s",
                (validation_id,),
            )
            cursor.execute(
                "DELETE FROM validation_records WHERE validation_id = %s",
                (validation_id,),
            )

        conn.commit()
        conn.close()

def test_mark_execution_failed_persists_failure():
    assert os.getenv("DB_NAME") == "capstone_recovery_test", (
        "Refusing to run outside capstone_recovery_test"
    )

    validation_id = str(uuid4())
    failure = {
        "stage": "verifier_execution",
        "reason": "Verifier timed out",
    }

    conn = get_connection()

    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO validation_records (
                    validation_id, question, generated_answer
                )
                VALUES (%s, %s, %s)
                """,
                (validation_id, "Test question", "Test answer"),
            )
        conn.commit()

        begin_validation(
            validation_id=validation_id,
            execution_mode="baseline",
            request_payload={"question": "Test question"},
        )

        mark_execution_ready(
            validation_id=validation_id,
            plan_payload={"selected_verifiers": ["verifier_a"]},
        )

        mark_execution_running(validation_id=validation_id)

        result = mark_execution_failed(
            validation_id=validation_id,
            failure_details=failure,
        )

        assert result["execution_status"] == "failed"
        assert result["failure_details"] == failure

        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT execution_status, failure_details
                FROM validation_executions
                WHERE validation_id = %s
                """,
                (validation_id,),
            )
            row = cursor.fetchone()

        assert row[0] == "failed"
        assert row[1] == failure

        with pytest.raises(ExecutionConflictError):
            mark_execution_failed(
                validation_id=validation_id,
                failure_details=failure,
            )

    finally:
        conn.rollback()

        with conn.cursor() as cursor:
            cursor.execute(
                "DELETE FROM validation_executions WHERE validation_id = %s",
                (validation_id,),
            )
            cursor.execute(
                "DELETE FROM validation_records WHERE validation_id = %s",
                (validation_id,),
            )

        conn.commit()
        conn.close()

def test_mark_execution_blocked_persists_reason():
    assert os.getenv("DB_NAME") == "capstone_recovery_test", (
        "Refusing to run outside capstone_recovery_test"
    )

    validation_id = str(uuid4())
    reason = "Required evidence is unavailable"

    conn = get_connection()

    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO validation_records (
                    validation_id, question, generated_answer
                )
                VALUES (%s, %s, %s)
                """,
                (validation_id, "Test question", "Test answer"),
            )
        conn.commit()

        begin_validation(
            validation_id=validation_id,
            execution_mode="baseline",
            request_payload={"question": "Test question"},
        )

        result = mark_execution_blocked(
            validation_id=validation_id,
            block_reason=reason,
        )

        assert result["execution_status"] == "blocked"
        assert result["block_reason"] == reason

        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT execution_status, block_reason
                FROM validation_executions
                WHERE validation_id = %s
                """,
                (validation_id,),
            )
            row = cursor.fetchone()

        assert row[0] == "blocked"
        assert row[1] == reason

        with pytest.raises(ExecutionConflictError):
            mark_execution_blocked(
                validation_id=validation_id,
                block_reason=reason,
            )

    finally:
        conn.rollback()

        with conn.cursor() as cursor:
            cursor.execute(
                "DELETE FROM validation_executions WHERE validation_id = %s",
                (validation_id,),
            )
            cursor.execute(
                "DELETE FROM validation_records WHERE validation_id = %s",
                (validation_id,),
            )

        conn.commit()
        conn.close()

def test_create_verifier_attempt_persists_planned_attempt():
    assert os.getenv("DB_NAME") == "capstone_recovery_test", (
        "Refusing to run outside capstone_recovery_test"
    )

    validation_id = str(uuid4())
    conn = get_connection()

    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO validation_records (
                    validation_id, question, generated_answer
                )
                VALUES (%s, %s, %s)
                """,
                (validation_id, "Test question", "Test answer"),
            )
        conn.commit()

        begin_validation(
            validation_id=validation_id,
            execution_mode="baseline",
            request_payload={"question": "Test question"},
        )

        mark_execution_ready(
            validation_id=validation_id,
            plan_payload={"selected_verifiers": ["verifier_a"]},
        )

        result = create_verifier_attempt(
            validation_id=validation_id,
            call_key="verifier_a_call_1",
            execution_order=0,
            verifier_name="verifier_a",
            component_id="component_a",
        )

        assert result["lifecycle_status"] == "planned"
        assert result["call_key"] == "verifier_a_call_1"
        assert result["execution_order"] == 0
        assert result["verifier_name"] == "verifier_a"
        assert result["attempt_id"]

        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    lifecycle_status,
                    outcome,
                    started_at,
                    completed_at,
                    report
                FROM live_verifier_attempts
                WHERE attempt_id = %s
                """,
                (result["attempt_id"],),
            )
            row = cursor.fetchone()

        assert row[0] == "planned"
        assert row[1] is None
        assert row[2] is None
        assert row[3] is None
        assert row[4] is None

    finally:
        conn.rollback()

        with conn.cursor() as cursor:
            cursor.execute(
                """
                DELETE FROM live_verifier_attempts
                WHERE validation_id = %s
                """,
                (validation_id,),
            )
            cursor.execute(
                """
                DELETE FROM validation_executions
                WHERE validation_id = %s
                """,
                (validation_id,),
            )
            cursor.execute(
                """
                DELETE FROM validation_records
                WHERE validation_id = %s
                """,
                (validation_id,),
            )

        conn.commit()
        conn.close()


@pytest.fixture
def planned_attempt():
    assert os.getenv("DB_NAME") == "capstone_recovery_test", (
        "Refusing to run outside capstone_recovery_test"
    )

    validation_id = str(uuid4())
    conn = get_connection()

    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO validation_records (
                    validation_id, question, generated_answer
                )
                VALUES (%s, %s, %s)
                """,
                (validation_id, "Test question", "Test answer"),
            )
        conn.commit()

        begin_validation(
            validation_id=validation_id,
            execution_mode="baseline",
            request_payload={"question": "Test question"},
        )

        mark_execution_ready(
            validation_id=validation_id,
            plan_payload={"selected_verifiers": ["verifier_a"]},
        )

        attempt = create_verifier_attempt(
            validation_id=validation_id,
            call_key="verifier_a_call_1",
            execution_order=0,
            verifier_name="verifier_a",
        )

        yield {
            "validation_id": validation_id,
            "attempt_id": attempt["attempt_id"],
            "conn": conn,
        }

    finally:
        conn.rollback()

        with conn.cursor() as cursor:
            cursor.execute(
                "DELETE FROM live_verifier_attempts WHERE validation_id = %s",
                (validation_id,),
            )
            cursor.execute(
                "DELETE FROM validation_executions WHERE validation_id = %s",
                (validation_id,),
            )
            cursor.execute(
                "DELETE FROM validation_records WHERE validation_id = %s",
                (validation_id,),
            )

        conn.commit()
        conn.close()


def test_mark_verifier_attempt_started(planned_attempt):
    attempt_id = planned_attempt["attempt_id"]

    result = mark_verifier_attempt_started(
        attempt_id=attempt_id,
    )

    assert result["lifecycle_status"] == "started"
    assert result["started_at"] is not None
    assert result["completed_at"] is None

    with pytest.raises(ExecutionConflictError):
        mark_verifier_attempt_started(attempt_id=attempt_id)


def test_mark_verifier_attempt_completed(planned_attempt):
    attempt_id = planned_attempt["attempt_id"]

    mark_verifier_attempt_started(attempt_id=attempt_id)

    report = {
        "verifier": "verifier_a",
        "result": "supported",
    }

    result = mark_verifier_attempt_completed(
        attempt_id=attempt_id,
        report=report,
        outcome="directional",
        duration_ms=120,
        estimated_cost=0.02,
        cost_units="USD",
    )

    assert result["lifecycle_status"] == "completed"
    assert result["outcome"] == "directional"
    assert result["report"] == report
    assert result["report_digest"]
    assert result["started_at"] is not None
    assert result["completed_at"] is not None
    assert result["duration_ms"] == 120
    assert result["estimated_cost"] == 0.02

    with pytest.raises(ExecutionConflictError):
        mark_verifier_attempt_completed(
            attempt_id=attempt_id,
            report=report,
            outcome="directional",
        )


def test_mark_verifier_attempt_failed(planned_attempt):
    attempt_id = planned_attempt["attempt_id"]

    mark_verifier_attempt_started(attempt_id=attempt_id)

    result = mark_verifier_attempt_failed(
        attempt_id=attempt_id,
        error_type="TimeoutError",
        error_message="Verifier timed out",
        duration_ms=500,
    )

    assert result["lifecycle_status"] == "execution_failed"
    assert result["outcome"] == "failed"
    assert result["error_type"] == "TimeoutError"
    assert result["error_message"] == "Verifier timed out"
    assert result["completed_at"] is not None

    with pytest.raises(ExecutionConflictError):
        mark_verifier_attempt_failed(
            attempt_id=attempt_id,
            error_type="TimeoutError",
            error_message="Repeated failure",
        )


def test_mark_verifier_attempt_unavailable(planned_attempt):
    attempt_id = planned_attempt["attempt_id"]

    mark_verifier_attempt_started(attempt_id=attempt_id)

    result = mark_verifier_attempt_unavailable(
        attempt_id=attempt_id,
        reason="Verifier service unavailable",
    )

    assert result["lifecycle_status"] == "unavailable"
    assert result["outcome"] == "unavailable"
    assert result["error_message"] == "Verifier service unavailable"
    assert result["completed_at"] is not None

    with pytest.raises(ExecutionConflictError):
        mark_verifier_attempt_unavailable(
            attempt_id=attempt_id,
            reason="Repeated unavailable state",
        )


def test_mark_verifier_attempt_error(planned_attempt):
    attempt_id = planned_attempt["attempt_id"]

    mark_verifier_attempt_started(attempt_id=attempt_id)

    result = mark_verifier_attempt_error(
        attempt_id=attempt_id,
        error_type="RuntimeError",
        error_message="Unexpected verifier error",
    )

    assert result["lifecycle_status"] == "error"
    assert result["outcome"] == "error"
    assert result["error_type"] == "RuntimeError"
    assert result["error_message"] == "Unexpected verifier error"
    assert result["completed_at"] is not None

    with pytest.raises(ExecutionConflictError):
        mark_verifier_attempt_error(
            attempt_id=attempt_id,
            error_type="RuntimeError",
            error_message="Repeated error",
        )


def test_mark_verifier_attempt_ambiguous(planned_attempt):
    attempt_id = planned_attempt["attempt_id"]

    mark_verifier_attempt_started(attempt_id=attempt_id)

    result = mark_verifier_attempt_ambiguous(
        attempt_id=attempt_id,
    )

    assert result["lifecycle_status"] == "ambiguous"
    assert result["outcome"] is None
    assert result["started_at"] is not None
    assert result["completed_at"] is None

    with pytest.raises(ExecutionConflictError):
        mark_verifier_attempt_ambiguous(
            attempt_id=attempt_id,
        )


def test_get_execution_retrieves_persisted_journal(planned_attempt):
    validation_id = planned_attempt["validation_id"]

    result = get_execution(validation_id=validation_id)

    assert result is not None
    assert result["validation_id"] == validation_id
    assert result["execution_status"] == "ready"
    assert result["execution_mode"] == "baseline"
    assert result["request_payload"] == {
        "question": "Test question"
    }
    assert result["plan_payload"] == {
        "selected_verifiers": ["verifier_a"]
    }
    assert result["plan_digest"]


def test_get_verifier_attempts_returns_execution_order(planned_attempt):
    validation_id = planned_attempt["validation_id"]

    first = planned_attempt["attempt_id"]

    second = create_verifier_attempt(
        validation_id=validation_id,
        call_key="verifier_b_call_1",
        execution_order=1,
        verifier_name="verifier_b",
    )

    results = get_verifier_attempts(
        validation_id=validation_id
    )

    assert len(results) == 2
    assert results[0]["attempt_id"] == first
    assert results[0]["execution_order"] == 0
    assert results[1]["attempt_id"] == second["attempt_id"]
    assert results[1]["execution_order"] == 1


def test_get_incomplete_executions_returns_nonterminal_records(
    planned_attempt,
):
    validation_id = planned_attempt["validation_id"]

    results = get_incomplete_executions(limit=100)

    matching = [
        item for item in results
        if item["validation_id"] == validation_id
    ]

    assert len(matching) == 1
    assert matching[0]["execution_status"] == "ready"

    with pytest.raises(ValueError):
        get_incomplete_executions(limit=0)
