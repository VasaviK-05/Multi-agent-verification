"""Tests for health endpoint and module imports."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_modules_import():
    import app.analysis
    import app.api
    import app.decision
    import app.feedback
    import app.models
    import app.orchestration
    import app.reputation
    import app.selection
    import app.services
    import app.verifiers

    assert app is not None
