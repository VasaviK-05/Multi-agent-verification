
from uuid import UUID

from fastapi.testclient import TestClient

from unittest.mock import patch
from app.reputation.reputation_manager import ReputationManager

# Import-time service bootstrap is not a live PostgreSQL integration test.
# Restore the real loader immediately; individual repository tests keep their SQL.
with patch("app.orchestration.validation_orchestrator.load_reputation_manager_state",
           return_value=ReputationManager().export_state()):
    from app.main import app
    from app.api import routes
from app.models.schemas import GroundTruthEvaluation, ValidationResponse


VALIDATION_ID = "11111111-1111-4111-8111-111111111111"
GROUND_TRUTH = GroundTruthEvaluation(
    label="Paris",
    source="test",
    answer_is_correct=True,
)


def make_validation_response():
    return ValidationResponse(
        results=[],
        final_status="passed",
        final_score=1.0,
        validation_id=VALIDATION_ID,
        ground_truth=GROUND_TRUTH,
    )


def test_validate_saves_ground_truth_after_validation(monkeypatch):
    events = []
    question_id = 123

    class FakeService:
        def validate(self, request):
            return make_validation_response()

        def get_validation_context(self, validation_id):
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
    monkeypatch.setattr(routes, "_validation_service", FakeService())

    def fake_save_validation(**kwargs):
        events.append(("validation", kwargs["validation_id"]))

    def fake_save_verifier_outputs(**kwargs):
        events.append(("verifiers", kwargs["validation_id"]))

    def fake_save_ground_truth(**kwargs):
        events.append(("ground_truth", kwargs["validation_id"]))
        assert kwargs["question_id"] == question_id
        assert kwargs["label"] == "Paris"
        assert kwargs["source"] == "test"

    monkeypatch.setattr(routes, "save_validation", fake_save_validation)
    monkeypatch.setattr(routes, "save_verifier_outputs", fake_save_verifier_outputs)
    monkeypatch.setattr(routes, "save_ground_truth", fake_save_ground_truth)
    monkeypatch.setattr(
        routes,
        "create_audit",
        lambda **kwargs: events.append(("audit_create", kwargs["validation_id"])),
    )
    monkeypatch.setattr(
        routes,
        "update_audit",
        lambda validation_id, **kwargs: events.append(
            ("audit_update", validation_id, kwargs)
        ),
    )

    with TestClient(app) as client:
        response = client.post(
            "/validate",
            json={
                "question": "What is the capital of France?",
                "answer": "Paris",
                "question_id": question_id,
            },
        )

    assert response.status_code == 200
    assert [event[0] for event in events] == [
        "validation",
        "audit_create",
        "verifiers",
        "ground_truth",
        "audit_update",
    ]
    assert UUID(events[0][1]) == UUID(VALIDATION_ID)


def test_generate_and_validate_saves_ground_truth_after_validation(monkeypatch):
    events = []
    question_id = 456

    class FakeService:
        def validate(self, request):
            assert request.question_id == question_id
            return make_validation_response()

        def get_validation_context(self, validation_id):
            assert validation_id == VALIDATION_ID

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

    class FakeCursor:
        def execute(self, query, params):
            events.append(("question_insert", params))

        def fetchone(self):
            return (question_id,)

        def close(self):
            pass

    class FakeConnection:
        def cursor(self):
            return FakeCursor()

        def commit(self):
            events.append(("question_commit", None))

        def rollback(self):
            pass

        def close(self):
            pass

    def fake_save_validation(**kwargs):
        events.append(("validation", kwargs["validation_id"]))

    def fake_save_verifier_outputs(**kwargs):
        events.append(("verifiers", kwargs["validation_id"]))

    def fake_save_ground_truth(**kwargs):
        events.append(("ground_truth", kwargs["validation_id"]))
        assert kwargs["question_id"] == question_id
        assert kwargs["label"] == "Paris"
        assert kwargs["source"] == "test"

    monkeypatch.setattr(routes, "_validation_service", FakeService())
    monkeypatch.setattr(routes, "generate_answer", lambda question: "Paris")
    monkeypatch.setattr(routes, "get_connection", FakeConnection)
    monkeypatch.setattr(routes, "save_validation", fake_save_validation)
    monkeypatch.setattr(routes, "save_verifier_outputs", fake_save_verifier_outputs)
    monkeypatch.setattr(routes, "save_ground_truth", fake_save_ground_truth)
    monkeypatch.setattr(
        routes,
        "create_audit",
        lambda **kwargs: events.append(
            ("audit_create", kwargs["validation_id"])
        ),
    )
    monkeypatch.setattr(
        routes,
        "update_audit",
        lambda validation_id, **kwargs: events.append(
            ("audit_update", validation_id, kwargs)
        ),
    )

    with TestClient(app) as client:
        response = client.post(
            "/generate-and-validate",
            json={"question": "What is the capital of France?"},
        )

    assert response.status_code == 200
    assert [event[0] for event in events] == [
        "question_insert",
        "question_commit",
        "validation",
        "audit_create",
        "verifiers",
        "ground_truth",
        "audit_update",
    ]
    assert UUID(events[2][1]) == UUID(VALIDATION_ID)

    audit_update = events[-1]
    assert audit_update[2]["run_status"] == "completed"
    assert audit_update[2]["coverage_outcomes"]["coverage"] == {}

def test_validate_does_not_save_ground_truth_if_validation_save_fails(monkeypatch):
    question_id = 789
    ground_truth_calls = []

    class FakeService:
        def validate(self, request):
            return make_validation_response()

        def get_validation_context(self, validation_id):
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

    def fail_save_validation(**kwargs):
        raise RuntimeError("validation persistence failed")

    monkeypatch.setattr(routes, "_validation_service", FakeService())
    monkeypatch.setattr(routes, "save_validation", fail_save_validation)
    monkeypatch.setattr(
        routes,
        "save_ground_truth",
        lambda **kwargs: ground_truth_calls.append(kwargs),
    )

    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.post(
            "/validate",
            json={
                "question": "What is the capital of France?",
                "answer": "Paris",
                "question_id": question_id,
            },
        )

    assert response.status_code == 500
    assert ground_truth_calls == []
