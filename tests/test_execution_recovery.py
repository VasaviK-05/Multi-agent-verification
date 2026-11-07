import os
from uuid import uuid4

import pytest
from dotenv import load_dotenv

from unittest.mock import patch

from database import get_connection

from app.database.execution_journal_repository import (
    begin_validation,
    mark_execution_ready,
    mark_execution_running,
    create_verifier_attempt,
    mark_verifier_attempt_started,
    mark_verifier_attempt_completed,
    get_execution,
    get_verifier_attempts,
    mark_execution_blocked,
)

from app.database.execution_recovery import (
    inspect_and_recover_incomplete_executions,
)
from fastapi.testclient import TestClient
from app.main import app

load_dotenv()


def expire_execution_lease(validation_id: str) -> None:
    """Simulate a crashed worker by expiring its lease."""
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE validation_executions
                SET lease_expires_at = NOW() - INTERVAL '1 second',
                    updated_at = NOW()
                WHERE validation_id = %s
                  AND execution_status = 'running'
                """,
                (validation_id,),
            )

        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


@pytest.fixture
def recovery_validation():
    assert os.getenv("DB_NAME") == "multi_agent_controlled_fixture_test", (
        "Refusing to run outside multi_agent_controlled_fixture_test"
    )

    validation_id = str(uuid4())
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO validation_records (
                    validation_id, question, generated_answer
                )
                VALUES (%s, %s, %s)
                """,
                (
                    validation_id,
                    "Recovery test question",
                    "Recovery test answer",
                ),
            )

        connection.commit()

        yield validation_id

    finally:
        with connection.cursor() as cursor:
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

        connection.commit()
        connection.close()

def test_recovery_marks_started_attempt_ambiguous(
    recovery_validation,
):
    validation_id = recovery_validation

    begin_validation(
        validation_id=validation_id,
        execution_mode="baseline",
        request_payload={
            "question": "Recovery test question",
            "answer": "Recovery test answer",
        },
    )

    mark_execution_ready(
        validation_id=validation_id,
        plan_payload={"selected_verifiers": ["verifier_a"]},
    )

    mark_execution_running(validation_id=validation_id)

    attempt = create_verifier_attempt(
        validation_id=validation_id,
        call_key="1:verifier_a",
        execution_order=1,
        verifier_name="verifier_a",
    )

    mark_verifier_attempt_started(
        attempt_id=attempt["attempt_id"]
    )

    expire_execution_lease(validation_id)
    results = inspect_and_recover_incomplete_executions()

    recovered = next(
        item for item in results
        if item["validation_id"] == validation_id
    )

    assert recovered["action"] == "blocked_for_inspection"
    assert attempt["attempt_id"] in recovered[
        "attempts_marked_ambiguous"
    ]

    execution = get_execution(validation_id=validation_id)
    attempts = get_verifier_attempts(validation_id=validation_id)

    assert execution["execution_status"] == "blocked"
    assert attempts[0]["lifecycle_status"] == "ambiguous"

def test_recovery_preserves_completed_attempt(
    recovery_validation,
):
    validation_id = recovery_validation

    begin_validation(
        validation_id=validation_id,
        execution_mode="baseline",
        request_payload={"question": "Test", "answer": "Test"},
    )

    mark_execution_ready(
        validation_id=validation_id,
        plan_payload={"selected_verifiers": ["verifier_a"]},
    )

    mark_execution_running(validation_id=validation_id)

    attempt = create_verifier_attempt(
        validation_id=validation_id,
        call_key="1:verifier_a",
        execution_order=1,
        verifier_name="verifier_a",
    )

    mark_verifier_attempt_started(
        attempt_id=attempt["attempt_id"]
    )

    mark_verifier_attempt_completed(
        attempt_id=attempt["attempt_id"],
        report={"verdict": "supported"},
        outcome="directional",
    )

    expire_execution_lease(validation_id)
    inspect_and_recover_incomplete_executions()

    attempts = get_verifier_attempts(validation_id=validation_id)

    assert attempts[0]["lifecycle_status"] == "completed"
    assert attempts[0]["report"] == {"verdict": "supported"}

    execution = get_execution(validation_id=validation_id)
    assert execution["execution_status"] == "blocked"

def test_recovery_skips_already_blocked_execution(
    recovery_validation,
):
    validation_id = recovery_validation

    begin_validation(
        validation_id=validation_id,
        execution_mode="baseline",
        request_payload={"question": "Test", "answer": "Test"},
    )

    mark_execution_ready(
        validation_id=validation_id,
        plan_payload={"selected_verifiers": []},
    )

    mark_execution_running(validation_id=validation_id)

    mark_execution_blocked(
        validation_id=validation_id,
        block_reason="Previously blocked for inspection.",
    )

    results = inspect_and_recover_incomplete_executions()

    recovered = next(
        item for item in results
        if item["validation_id"] == validation_id
    )

    assert recovered["action"] == "already_blocked"
    assert recovered["attempts_marked_ambiguous"] == []

    execution = get_execution(validation_id=validation_id)
    assert execution["block_reason"] == (
        "Previously blocked for inspection."
    )

def test_recovery_rolls_back_attempt_if_execution_block_fails(
    recovery_validation,
):
    validation_id = recovery_validation

    begin_validation(
        validation_id=validation_id,
        execution_mode="baseline",
        request_payload={"question": "Test", "answer": "Test"},
    )

    mark_execution_ready(
        validation_id=validation_id,
        plan_payload={"selected_verifiers": ["verifier_a"]},
    )

    mark_execution_running(validation_id=validation_id)

    attempt = create_verifier_attempt(
        validation_id=validation_id,
        call_key="1:verifier_a",
        execution_order=1,
        verifier_name="verifier_a",
    )

    mark_verifier_attempt_started(
        attempt_id=attempt["attempt_id"]
    )

    expire_execution_lease(validation_id)
    with patch(
        "app.database.execution_recovery.mark_execution_blocked",
        side_effect=RuntimeError("Simulated recovery failure"),
    ):
        with pytest.raises(RuntimeError):
            inspect_and_recover_incomplete_executions()

    attempts = get_verifier_attempts(validation_id=validation_id)
    execution = get_execution(validation_id=validation_id)

    assert attempts[0]["lifecycle_status"] == "started"
    assert execution["execution_status"] == "running"

def test_fastapi_startup_recovers_interrupted_execution(
    recovery_validation,
):
    validation_id = recovery_validation

    begin_validation(
        validation_id=validation_id,
        execution_mode="baseline",
        request_payload={"question": "Simulated crash test"},
    )

    mark_execution_ready(
        validation_id=validation_id,
        plan_payload={"selected_verifiers": ["verifier_a"]},
    )

    mark_execution_running(validation_id=validation_id)

    attempt = create_verifier_attempt(
        validation_id=validation_id,
        call_key="1:verifier_a",
        execution_order=1,
        verifier_name="verifier_a",
    )

    attempt_id = attempt["attempt_id"]

    mark_verifier_attempt_started(attempt_id=attempt_id)

    # Simulate application startup after a crash.
    expire_execution_lease(validation_id)
    with TestClient(app):
        pass

    execution = get_execution(validation_id=validation_id)
    attempts = get_verifier_attempts(validation_id=validation_id)

    assert execution["execution_status"] == "blocked"

    recovered_attempt = next(
        item for item in attempts
        if item["attempt_id"] == attempt_id
    )

    assert recovered_attempt["lifecycle_status"] == "ambiguous"
