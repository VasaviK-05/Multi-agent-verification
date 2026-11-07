import json
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
    assert os.getenv("DB_NAME") == "multi_agent_controlled_fixture_test", (
        "Refusing to run outside multi_agent_controlled_fixture_test"
    )
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT current_database()")
            assert cursor.fetchone()[0] == "multi_agent_controlled_fixture_test", (
                "Refusing database writes outside multi_agent_controlled_fixture_test"
            )
    finally:
        connection.close()
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


def test_game_mode_persists_journal_and_links_selected_outputs(test_db, monkeypatch):
    from tests.test_game_runtime import runtime_fixture

    unpersisted, checkers, manager, _ = runtime_fixture()
    orchestrator = ValidationOrchestrator(
        question_analyzer=unpersisted._question_analyzer,
        verifier_selector=unpersisted.verifier_selector,
        reputation_manager=manager,
        execution_mode="game",
        game_runtime=unpersisted._game_runtime,
        persist_execution=True,
    )
    monkeypatch.setattr(
        routes, "_validation_service", ValidationService(orchestrator=orchestrator)
    )
    validation_id = None
    try:
        with TestClient(app) as client:
            response = client.post(
                "/validate",
                json={"question": "fixture question", "answer": "fixture answer"},
            )
            assert response.status_code == 200, response.text
            body = response.json()
            validation_id = str(UUID(body["validation_id"]))

        execution = get_execution(validation_id=validation_id)
        attempts = get_verifier_attempts(validation_id=validation_id)
        audit = get_audit(validation_id)
        validation = get_validation(validation_id)
        assert execution["execution_mode"] == "game"
        assert execution["execution_status"] == "completed"
        assert execution["plan_payload"]["strategy_id"] == body["execution_audit"]["selected_strategy_id"]
        assert validation is not None and audit["run_status"] == "completed"
        assert len(attempts) == len(body["execution_audit"]["team"])
        assert all(row["lifecycle_status"] == "completed" for row in attempts)
        assert all(row["report_validation_id"] == validation_id for row in attempts)
        assert {row["attempt_id"] for row in attempts} == {
            row["attempt_id"] for row in attempts if row["report"]
        }
        connection = get_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT attempt_id, verifier_name FROM verifier_outputs WHERE validation_id = %s",
                    (validation_id,),
                )
                output_links = cursor.fetchall()
        finally:
            connection.close()
        assert len(output_links) == len(body["results"])
        assert all(attempt_id for attempt_id, _ in output_links)
        assert {name for _, name in output_links} == set(body["execution_audit"]["team"])
        assert all(checker.calls == (1 if checker.name in body["execution_audit"]["team"] else 0)
                   for checker in checkers)
    finally:
        if validation_id is not None:
            cleanup_validation(validation_id)


@pytest.mark.parametrize("mode", ["abstention", "failure"])
def test_compound_component_journal_identity_and_finalization_persist(
    test_db, monkeypatch, mode
):
    from tests.test_component_execution import Q, REF, setup
    from app.game.component_execution import run_component_diagnostic
    from app.game.deployment import PrototypeGameRuntime

    contract, strategy, selector, observer, calls = setup(
        "failure" if mode == "failure" else None
    )
    if mode == "abstention":
        evidence = selector.resolve("evidence")
        original = evidence.verify
        def abstain(question, answer, context=None):
            row = original(question, answer, context)
            row.metadata = {"decision": "UNSURE", "unsure_reason": "controlled fixture"}
            return row
        evidence.verify = abstain

    class ComponentRouter:
        def run(self, actual_selector, analysis, request, validation_id, *,
                provider, rng, resource_observer, allow_synthetic_for_tests,
                execution_journal):
            return run_component_diagnostic(
                contract, strategy, actual_selector, request.question,
                request.answer, request.context, validation_id,
                resource_observer=observer, execution_journal=execution_journal,
            )

    runtime = object.__new__(PrototypeGameRuntime)
    runtime._router = ComponentRouter()
    runtime._provider = object()
    runtime._rng = object()
    orchestrator = ValidationOrchestrator(
        question_analyzer=FixedAnalyzer(), verifier_selector=selector,
        decision_engine=DecisionEngine(selector.reputation_manager),
        reputation_manager=selector.reputation_manager,
        execution_mode="game", game_runtime=runtime, persist_execution=True,
    )
    monkeypatch.setattr(
        routes, "_validation_service", ValidationService(orchestrator=orchestrator)
    )
    validation_id = None
    answer = json.dumps({"base": "765", "derived": "775"})
    try:
        with TestClient(app) as client:
            response = client.post("/validate", json={"question": Q, "answer": answer, "context": REF})
            assert response.status_code == 200, response.text
            body = response.json()
            validation_id = str(UUID(body["validation_id"]))

        attempts = get_verifier_attempts(validation_id=validation_id)
        execution = get_execution(validation_id=validation_id)
        audit = get_audit(validation_id)
        assert execution["execution_mode"] == "game"
        assert execution["execution_status"] == "completed"
        assert audit["run_status"] == "completed"
        assert len(attempts) == 2
        assert {row["component_id"] for row in attempts} == {"base_fact", "derived_sum"}
        assert all(row["identity_binding"]["binding_id"] for row in attempts)
        assert all(row["report_validation_id"] for row in attempts)
        by_component = {row["component_id"]: row for row in attempts}
        component_ids = {
            item["component_id"]: item["validation_id"]
            for item in body["execution_audit"]["components"]
        }
        assert set(component_ids) == {"base_fact", "derived_sum"}
        assert all(
            len(value) == 64 and all(char in "0123456789abcdef" for char in value)
            for value in component_ids.values()
        )
        assert {
            component: by_component[component]["report_validation_id"]
            for component in component_ids
        } == component_ids
        assert by_component["base_fact"]["lifecycle_status"] == (
            "completed" if mode == "abstention" else "execution_failed"
        )
        assert by_component["derived_sum"]["lifecycle_status"] == "completed"
        expected_base = "abstention" if mode == "abstention" else "failed"
        assert body["execution_audit"]["components"][0]["states"][0][1] == expected_base
        assert body["execution_audit"]["components"][1]["public_status"] == "passed"
        assert body["final_status"] == "uncertain"

        connection = get_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT attempt_id, verifier_name FROM verifier_outputs WHERE validation_id = %s",
                    (validation_id,),
                )
                output_links = cursor.fetchall()
        finally:
            connection.close()
        assert len(output_links) == len(body["results"])
        assert all(row[0] is not None for row in output_links)
        assert len(calls) == 2
    finally:
        if validation_id is not None:
            cleanup_validation(validation_id)
