
from fastapi.testclient import TestClient

from unittest.mock import patch
from app.reputation.reputation_manager import ReputationManager


# Import-time service bootstrap is not a live PostgreSQL integration test.
# Restore the real loader immediately; individual repository tests keep their SQL.
with patch(
    "app.orchestration.validation_orchestrator.load_reputation_manager_state",
    return_value=ReputationManager().export_state(),
):
    from app.main import app
    from app.api import routes


client = TestClient(app)


def test_validate_creates_and_updates_audit(monkeypatch):
    calls = []

    class FakeResult:
        validation_id = "11111111-1111-4111-8111-111111111111"
        final_status = "accepted"
        final_score = 0.9
        session_id = None
        domain = "general"
        difficulty = "easy"
        selected_verifiers = ["verifier_a"]
        early_stop_reason = None
        signed_score = 0.9
        ground_truth = None
        results = []

        execution_audit = {
            "selected_strategy_id": "strategy_test",
            "execution_contract": {"threshold": 0.75},
            "reputation_snapshot_id": "22222222-2222-4222-8222-222222222222",
            "selection_plan": {"policy_version": "policy_v1"},
            "attempts": [
                {
                    "verifier_name": "verifier_a",
                    "estimated_attempt_cost": 12.5,
                }
            ],
            "estimated_selected_cost": 12.5,
            "estimated_attempted_cost": 12.5,

            # Existing audit summary fields
            "coverage": {},
            "missing_coverage": [],
            "termination": "candidate_exhaustion",
            "last_stopping_assessment": None,
            "minimum_contributors": 1,
            "contributors": 1,
            "numerical_decision": {},
        }

    class FakeValidationService:
        def validate(self, request):
            return FakeResult()

        def get_validation_context(self, validation_id):
            assert validation_id == FakeResult.validation_id

            return type(
                "FakeContext",
                (),
                {
                    "run_summary": FakeResult.execution_audit
                },
            )()

    monkeypatch.setattr(
        routes, "_validation_service", FakeValidationService()
    )
    monkeypatch.setattr(
        routes, "save_validation", lambda **kwargs: None
    )
    monkeypatch.setattr(
        routes, "save_verifier_outputs", lambda **kwargs: None
    )
    monkeypatch.setattr(
        routes,
        "create_audit",
        lambda **kwargs: calls.append(("create", kwargs)),
    )
    monkeypatch.setattr(
        routes,
        "update_audit",
        lambda *args, **kwargs: calls.append(("update", args, kwargs)),
    )

    response = client.post(
        "/validate",
        json={
            "question": "Test question",
            "answer": "Test answer",
        },
    )

    assert response.status_code == 200
    assert [call[0] for call in calls] == ["create", "update"]

    # Verify audit creation
    created = calls[0][1]

    assert created["validation_id"] == FakeResult.validation_id
    assert created["selected_strategy"] == "strategy_test"
    assert created["execution_contract"] == {"threshold": 0.75}
    assert created["reputation_snapshot_id"] == (
        "22222222-2222-4222-8222-222222222222"
    )
    assert created["selection_plan"] == {"policy_version": "policy_v1"}
    assert created["run_summary"] == FakeResult.execution_audit

    # Verify persisted game cost estimates
    updated = calls[1][2]
    costs = updated["execution_costs"]

    assert costs["game_estimated_attempt_costs"] == {
        "verifier_a": 12.5
    }
    assert costs["game_estimated_selected_cost"] == 12.5
    assert costs["game_estimated_attempted_cost"] == 12.5

    # Verify audit completion
    audit_data = updated

    assert audit_data["run_status"] == "completed"
    assert audit_data["selected_verifiers"] == ["verifier_a"]

    assert audit_data["coverage_outcomes"]["coverage"] == {}
    assert audit_data["coverage_outcomes"]["missing_coverage"] == []

    assert (
        audit_data["decision_summary"]["termination"]
        == "candidate_exhaustion"
    )
    assert audit_data["decision_summary"]["numerical_decision"] == {}


def test_validate_marks_audit_failed_when_verifier_persistence_fails(
    monkeypatch,
):
    calls = []

    class FakeResult:
        validation_id = "11111111-1111-4111-8111-111111111111"
        final_status = "passed"
        final_score = 1.0
        session_id = None
        domain = "general"
        difficulty = "easy"
        selected_verifiers = ["verifier_a"]
        early_stop_reason = None
        signed_score = 1.0
        ground_truth = None
        results = []

    class FakeValidationService:
        def validate(self, request):
            return FakeResult()

        def get_validation_context(self, validation_id):
            assert validation_id == FakeResult.validation_id

            return type(
                "FakeContext",
                (),
                {
                    "run_summary": {
                        "coverage": {},
                        "missing_coverage": [],
                        "termination": "candidate_exhaustion",
                        "last_stopping_assessment": None,
                        "minimum_contributors": 1,
                        "contributors": 1,
                        "numerical_decision": {},
                    }
                },
            )()

    def fail_saving_verifiers(**kwargs):
        raise RuntimeError("verifier persistence failed")

    monkeypatch.setattr(
        routes, "_validation_service", FakeValidationService()
    )
    monkeypatch.setattr(
        routes, "save_validation", lambda **kwargs: None
    )
    monkeypatch.setattr(
        routes, "save_verifier_outputs", fail_saving_verifiers
    )
    monkeypatch.setattr(
        routes,
        "create_audit",
        lambda **kwargs: calls.append(("create", kwargs)),
    )
    monkeypatch.setattr(
        routes,
        "update_audit",
        lambda *args, **kwargs: calls.append(("update", args, kwargs)),
    )

    with TestClient(app, raise_server_exceptions=False) as test_client:
        response = test_client.post(
            "/validate",
            json={
                "question": "Test question",
                "answer": "Test answer",
            },
        )

    assert response.status_code == 500
    assert [call[0] for call in calls] == ["create", "update"]

    update_call = calls[-1]
    audit_data = update_call[2]

    assert audit_data["run_status"] == "failed"
    assert audit_data["failure_details"][0]["stage"] == "persistence"


def test_generate_and_validate_creates_and_updates_audit(monkeypatch):
    calls = []

    class FakeCursor:
        def execute(self, query, params=None):
            self.query = query

        def fetchone(self):
            return (101,)

        def close(self):
            pass

    class FakeConnection:
        def cursor(self):
            return FakeCursor()

        def commit(self):
            pass

        def rollback(self):
            pass

        def close(self):
            pass

    class FakeResult:
        validation_id = "33333333-3333-4333-8333-333333333333"
        final_status = "accepted"
        final_score = 0.95
        session_id = None
        domain = "general"
        difficulty = "easy"
        selected_verifiers = ["verifier_a"]
        early_stop_reason = None
        signed_score = 0.95
        ground_truth = None
        results = []

        execution_audit = {
            "selected_strategy_id": "strategy_generate",
            "execution_contract": {"threshold": 0.8},
            "reputation_snapshot_id": "44444444-4444-4444-8444-444444444444",
            "selection_plan": {"policy_version": "policy_v2"},
            "attempts": [
                {
                    "verifier_name": "verifier_a",
                    "estimated_attempt_cost": 15.0,
                }
            ],
            "estimated_selected_cost": 15.0,
            "estimated_attempted_cost": 15.0,
            "coverage": {},
            "missing_coverage": [],
            "termination": "complete_selected_team",
            "last_stopping_assessment": None,
            "minimum_contributors": 1,
            "contributors": 1,
            "numerical_decision": {},
        }

    class FakeValidationService:
        def validate(self, request):
            assert request.question_id == 101
            return FakeResult()

        def get_validation_context(self, validation_id):
            assert validation_id == FakeResult.validation_id

            return type(
                "FakeContext",
                (),
                {"run_summary": FakeResult.execution_audit},
            )()

    monkeypatch.setattr(routes, "generate_answer", lambda question: "Generated test answer")
    monkeypatch.setattr(routes, "get_connection", lambda: FakeConnection())
    monkeypatch.setattr(routes, "_validation_service", FakeValidationService())
    monkeypatch.setattr(routes, "save_validation", lambda **kwargs: None)
    monkeypatch.setattr(routes, "save_verifier_outputs", lambda **kwargs: None)
    monkeypatch.setattr(
        routes,
        "create_audit",
        lambda **kwargs: calls.append(("create", kwargs)),
    )
    monkeypatch.setattr(
        routes,
        "update_audit",
        lambda *args, **kwargs: calls.append(("update", args, kwargs)),
    )

    response = client.post(
        "/generate-and-validate",
        json={
            "question": "Test generated question",
            "context": "Test context",
        },
    )

    assert response.status_code == 200
    assert [call[0] for call in calls] == ["create", "update"]

    # Verify audit creation
    created = calls[0][1]

    assert created["validation_id"] == FakeResult.validation_id
    assert created["question_id"] == 101
    assert created["selected_strategy"] == "strategy_generate"
    assert created["execution_contract"] == {"threshold": 0.8}
    assert created["reputation_snapshot_id"] == (
        "44444444-4444-4444-8444-444444444444"
    )
    assert created["selection_plan"] == {"policy_version": "policy_v2"}
    assert created["run_summary"] == FakeResult.execution_audit

    # Verify game cost estimates
    updated = calls[1][2]
    costs = updated["execution_costs"]

    assert costs["game_estimated_attempt_costs"] == {
        "verifier_a": 15.0
    }
    assert costs["game_estimated_selected_cost"] == 15.0
    assert costs["game_estimated_attempted_cost"] == 15.0

    # Verify audit completion
    assert updated["run_status"] == "completed"
    assert updated["selected_verifiers"] == ["verifier_a"]


def test_generate_and_validate_returns_error_when_audit_creation_fails(monkeypatch):
    calls = []

    class FakeCursor:
        def execute(self, query, params=None):
            pass

        def fetchone(self):
            return (101,)

        def close(self):
            pass

    class FakeConnection:
        def cursor(self):
            return FakeCursor()

        def commit(self):
            pass

        def rollback(self):
            pass

        def close(self):
            pass

    class FakeResult:
        validation_id = "55555555-5555-4555-8555-555555555555"
        final_status = "accepted"
        final_score = 0.95
        session_id = None
        domain = "general"
        difficulty = "easy"
        selected_verifiers = ["verifier_a"]
        early_stop_reason = None
        signed_score = 0.95
        ground_truth = None
        results = []
        execution_audit = {}

    class FakeValidationService:
        def validate(self, request):
            assert request.question_id == 101
            return FakeResult()

    def fail_create_audit(**kwargs):
        calls.append("create_audit")
        raise RuntimeError("audit creation failed")

    monkeypatch.setattr(
        routes, "generate_answer",
        lambda question: "Generated test answer",
    )
    monkeypatch.setattr(routes, "get_connection", lambda: FakeConnection())
    monkeypatch.setattr(
        routes, "_validation_service", FakeValidationService()
    )
    monkeypatch.setattr(
        routes, "save_validation",
        lambda **kwargs: calls.append("save_validation"),
    )
    monkeypatch.setattr(
        routes, "create_audit", fail_create_audit
    )
    monkeypatch.setattr(
        routes, "save_verifier_outputs",
        lambda **kwargs: calls.append("save_verifier_outputs"),
    )

    with TestClient(app, raise_server_exceptions=False) as test_client:
        response = test_client.post(
            "/generate-and-validate",
            json={
                "question": "Test generated question",
                "context": "Test context",
            },
        )

    assert response.status_code == 503
    assert calls == ["save_validation", "create_audit"]
    assert "save_verifier_outputs" not in calls


def test_validate_returns_error_when_audit_creation_fails(monkeypatch):
    calls = []

    class FakeResult:
        validation_id = "11111111-1111-4111-8111-111111111111"
        final_status = "accepted"
        final_score = 0.9
        session_id = None
        domain = "general"
        difficulty = "easy"
        selected_verifiers = ["verifier_a"]
        early_stop_reason = None
        signed_score = 0.9
        ground_truth = None
        results = []
        execution_audit = {}

    class FakeValidationService:
        def validate(self, request):
            return FakeResult()

    def fail_create_audit(**kwargs):
        calls.append("create_audit")
        raise RuntimeError("audit creation failed")

    monkeypatch.setattr(
        routes, "_validation_service", FakeValidationService()
    )
    monkeypatch.setattr(
        routes,
        "save_validation",
        lambda **kwargs: calls.append("save_validation"),
    )
    monkeypatch.setattr(
        routes,
        "create_audit",
        fail_create_audit,
    )
    monkeypatch.setattr(
        routes,
        "save_verifier_outputs",
        lambda **kwargs: calls.append("save_verifier_outputs"),
    )

    with TestClient(app, raise_server_exceptions=False) as test_client:
        response = test_client.post(
            "/validate",
            json={
                "question": "Test question",
                "answer": "Test answer",
            },
        )

    assert response.status_code == 500
    assert calls == ["save_validation", "create_audit"]
    assert response.text == "Internal Server Error"



def test_validate_handles_audit_completion_failure(monkeypatch):
    calls = []

    class FakeResult:
        validation_id = "11111111-1111-4111-8111-111111111111"
        final_status = "accepted"
        final_score = 0.9
        session_id = None
        domain = "general"
        difficulty = "easy"
        selected_verifiers = ["verifier_a"]
        early_stop_reason = None
        signed_score = 0.9
        ground_truth = None
        results = []
        execution_audit = {}

    class FakeValidationService:
        def validate(self, request):
            return FakeResult()

        def get_validation_context(self, validation_id):
            return type(
                "FakeContext",
                (),
                {"run_summary": {}},
            )()

    def fail_completion(validation_id, **kwargs):
        status = kwargs["run_status"]
        calls.append(status)

        if status == "completed":
            raise RuntimeError("audit completion failed")

    monkeypatch.setattr(
        routes, "_validation_service", FakeValidationService()
    )
    monkeypatch.setattr(
        routes, "save_validation", lambda **kwargs: None
    )
    monkeypatch.setattr(
        routes, "save_verifier_outputs", lambda **kwargs: None
    )
    monkeypatch.setattr(
        routes, "create_audit",
        lambda **kwargs: calls.append("created")
    )
    monkeypatch.setattr(
        routes, "update_audit", fail_completion
    )

    with TestClient(app, raise_server_exceptions=False) as test_client:
        response = test_client.post(
            "/validate",
            json={
                "question": "Test question",
                "answer": "Test answer",
            },
        )

    assert response.status_code == 500
    assert calls == ["created", "completed", "failed"]
