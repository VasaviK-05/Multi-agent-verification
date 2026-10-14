
from uuid import UUID

from fastapi.testclient import TestClient

from app.api import routes
from app.main import app
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
    monkeypatch.setattr(routes, "save_validation", fake_save_validation)
    monkeypatch.setattr(routes, "save_verifier_outputs", fake_save_verifier_outputs)
    monkeypatch.setattr(routes, "save_ground_truth", fake_save_ground_truth)

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
        "verifiers",
        "ground_truth",
    ]
    assert UUID(events[0][1]) == UUID(VALIDATION_ID)


def test_generate_and_validate_saves_ground_truth_after_validation(monkeypatch):
    events = []
    question_id = 456

    class FakeService:
        def validate(self, request):
            assert request.question_id == question_id
            return make_validation_response()

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
        "verifiers",
        "ground_truth",
    ]
    assert UUID(events[2][1]) == UUID(VALIDATION_ID)

def test_validate_does_not_save_ground_truth_if_validation_save_fails(monkeypatch):
    question_id = 789
    ground_truth_calls = []

    class FakeService:
        def validate(self, request):
            return make_validation_response()

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
