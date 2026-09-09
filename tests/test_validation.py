"""Tests for the validation pipeline."""

from fastapi.testclient import TestClient

from app.main import app
from app.models.schemas import ValidationRequest
from app.orchestration.validation_orchestrator import ValidationOrchestrator

client = TestClient(app)


def test_validate_endpoint():
    payload = {
        "question": "What is the capital of France?",
        "answer": "Paris",
    }
    response = client.post("/validate", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert "results" in data
    assert "final_status" in data
    assert len(data["results"]) == 4
    assert data["final_status"] == "passed"
    assert data["final_score"] == 0.5


def test_validate_with_context():
    payload = {
        "question": "What is the capital of France?",
        "answer": "Paris",
        "context": "France is a country in Europe.",
    }
    response = client.post("/validate", json=payload)
    assert response.status_code == 200


def test_orchestrator_pipeline():
    orchestrator = ValidationOrchestrator()
    request = ValidationRequest(
        question="What is 2+2?",
        answer="4",
    )
    response = orchestrator.validate(request)

    assert len(response.results) == 4
    assert response.final_status == "passed"
    assert response.final_score == 0.5
