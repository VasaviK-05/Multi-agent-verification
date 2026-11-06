import os
from uuid import UUID

import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient

from app.analysis.models import QuestionAnalysis
from app.api import routes

from database import get_connection
from app.database.execution_journal_repository import (
    get_execution,
    get_verifier_attempts,
)
from app.database.audit_repository import get_audit
from app.database.validation_repository import get_validation
from app.main import app
from app.orchestration.validation_orchestrator import ValidationOrchestrator
from app.selection.verifier_selector import VerifierSelector
from app.services.validation_service import ValidationService
from app.decision.decision_engine import DecisionEngine
from app.reputation.reputation_manager import ReputationManager
from app.verifiers.base_verifier import BaseVerifier
from app.models.schemas import VerificationResult


load_dotenv()


class FixedAnalyzer:
    def analyze(self, question):
        return QuestionAnalysis(
            domain="general",
            difficulty="easy",
            difficulty_score=0.1,
            verification_types=[],
        )


class StubVerifier(BaseVerifier):
    def __init__(self, name):
        self._name = name

    @property
    def name(self):
        return self._name

    def verify(self, question, answer, context=None):
        return VerificationResult(
            verifier_name=self._name,
            score=0.8,
            passed=True,
            reasoning="Deterministic integration-test result",
        )


@pytest.fixture
def test_db():
    assert os.getenv("DB_NAME") == "capstone_recovery_test", (
        "Refusing to run outside capstone_recovery_test"
    )
    yield


def cleanup_validation(validation_id):
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "DELETE FROM verifier_outputs WHERE validation_id = %s",
                (validation_id,),
            )
            cursor.execute(
                "DELETE FROM ground_truth_labels WHERE validation_id = %s",
                (validation_id,),
            )
            cursor.execute(
                "DELETE FROM validation_audits WHERE validation_id = %s",
                (validation_id,),
            )
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
        connection.commit()
    finally:
        connection.close()


def test_validate_persists_records_and_survives_restart(test_db, monkeypatch):
    manager = ReputationManager()

    verifiers = [
        StubVerifier("semantic"),
        StubVerifier("rule"),
        StubVerifier("evidence"),
        StubVerifier("consistency"),
    ]

    selector = VerifierSelector(
        verifiers=verifiers,
        reputation_manager=manager,
        lambda_cost=0,
        lambda_latency=0,
        lambda_suitability=0,
    )

    orchestrator = ValidationOrchestrator(
        question_analyzer=FixedAnalyzer(),
        verifier_selector=selector,
        decision_engine=DecisionEngine(manager),
        reputation_manager=manager,
        persist_execution=True,
    )

    monkeypatch.setattr(
        routes,
        "_validation_service",
        ValidationService(orchestrator=orchestrator),
    )

    validation_id = None

    try:
        with TestClient(app) as client:
            response = client.post(
                "/validate",
                json={
                    "question": "What is the purpose of a database index?",
                    "answer": "A database index improves data retrieval efficiency.",
                },
            )

            assert response.status_code == 200, response.text

            body = response.json()
            validation_id = str(UUID(body["validation_id"]))

        execution = get_execution(validation_id=validation_id)
        attempts = get_verifier_attempts(validation_id=validation_id)
        validation = get_validation(validation_id)
        audit = get_audit(validation_id)

        assert execution is not None
        assert execution["execution_status"] == "completed"
        assert execution["final_response"] is not None

        assert len(attempts) >= 2
        assert all(
            attempt["lifecycle_status"] == "completed"
            for attempt in attempts
        )

        assert validation is not None
        assert audit is not None
        assert audit["run_status"] == "completed"

        # Confirm route-level verifier output rows were persisted.
        connection = get_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT COUNT(*)
                    FROM verifier_outputs
                    WHERE validation_id = %s
                    """,
                    (validation_id,),
                )
                output_count = cursor.fetchone()[0]
        finally:
            connection.close()

        assert output_count == len(body["results"])

        # A second application startup must not block completed work.
        with TestClient(app):
            execution_after_restart = get_execution(validation_id=validation_id)
            attempts_after_restart = get_verifier_attempts(validation_id=validation_id)

        assert execution_after_restart["execution_status"] == "completed"
        assert all(
            attempt["lifecycle_status"] == "completed"
            for attempt in attempts_after_restart
        )

    finally:
        if validation_id is not None:
            cleanup_validation(validation_id)

def test_generate_and_validate_persists_attempt_links(test_db, monkeypatch):
    manager = ReputationManager()

    verifiers = [
        StubVerifier("semantic"),
        StubVerifier("rule"),
        StubVerifier("evidence"),
        StubVerifier("consistency"),
    ]

    selector = VerifierSelector(
        verifiers=verifiers,
        reputation_manager=manager,
        lambda_cost=0,
        lambda_latency=0,
        lambda_suitability=0,
    )

    orchestrator = ValidationOrchestrator(
        question_analyzer=FixedAnalyzer(),
        verifier_selector=selector,
        decision_engine=DecisionEngine(manager),
        reputation_manager=manager,
        persist_execution=True,
    )

    monkeypatch.setattr(
        routes,
        "_validation_service",
        ValidationService(orchestrator=orchestrator),
    )
    monkeypatch.setattr(
        routes,
        "generate_answer",
        lambda question: "A database index improves retrieval efficiency.",
    )

    validation_id = None

    try:
        with TestClient(app) as client:
            response = client.post(
                "/generate-and-validate",
                json={
                    "question": "What is a database index?",
                    "context": "Database fundamentals",
                },
            )

            assert response.status_code == 200, response.text
            body = response.json()
            validation_id = str(UUID(body["validation"]["validation_id"]))

        attempts = get_verifier_attempts(validation_id=validation_id)
        assert attempts
        assert all(
            attempt["lifecycle_status"] == "completed"
            for attempt in attempts
        )

        connection = get_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT
                        vo.verifier_name,
                        vo.attempt_id,
                        va.verifier_name,
                        va.validation_id
                    FROM verifier_outputs vo
                    LEFT JOIN live_verifier_attempts va
                        ON vo.attempt_id = va.attempt_id
                    WHERE vo.validation_id = %s
                    ORDER BY vo.execution_order
                    """,
                    (validation_id,),
                )
                output_rows = cursor.fetchall()
        finally:
            connection.close()

        assert len(output_rows) == len(body["validation"]["results"])
        assert all(row[1] is not None for row in output_rows)
        assert all(row[2] == row[0] for row in output_rows)
        assert all(str(row[3]) == validation_id for row in output_rows)

    finally:
        if validation_id is not None:
            cleanup_validation(validation_id)