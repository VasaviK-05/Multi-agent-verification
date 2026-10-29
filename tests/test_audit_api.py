
from fastapi.testclient import TestClient

from unittest.mock import patch
from app.reputation.reputation_manager import ReputationManager

# Import-time service bootstrap is not a live PostgreSQL integration test.
# Restore the real loader immediately; individual repository tests keep their SQL.
with patch("app.orchestration.validation_orchestrator.load_reputation_manager_state",
           return_value=ReputationManager().export_state()):
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

    assert calls[0][1]["validation_id"] == FakeResult.validation_id

    update_call = calls[1]
    audit_data = update_call[2]

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
