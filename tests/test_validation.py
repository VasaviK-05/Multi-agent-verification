"""Tests for the validation pipeline."""

from fastapi.testclient import TestClient

from app.reputation.reputation_manager import ReputationManager
import app.orchestration.validation_orchestrator as orchestrator_module

orchestrator_module.load_reputation_manager_state = lambda: None
orchestrator_module.build_reputation_state = (
    lambda: ReputationManager().export_state()
)

from app.main import app
from app.api import routes
from app.models.schemas import ValidationRequest
from app.orchestration.validation_orchestrator import ValidationOrchestrator

routes.save_validation = lambda **kwargs: None
routes.create_audit = lambda **kwargs: None
routes.save_verifier_outputs = lambda **kwargs: None
routes.update_audit = lambda *args, **kwargs: None


client = TestClient(app)


def _geography(answer: str) -> dict:
    response = client.post(
        "/validate",
        json={"question": "What is the capital of France?", "answer": answer},
    )
    assert response.status_code == 200
    data = response.json()
    rule_results = [
    result
    for result in data["results"]
    if result["verifier_name"] == "rule"
    ]

    if rule_results:
        rule = rule_results[0]
        assert rule["metadata"]["rule"] == "unsupported"
        assert rule["passed"] is False
        assert rule["score"] == 0
        assert rule["metadata"]["pipeline_role"] == "abstention"
        assert "not a pass or a reject" in rule["metadata"]["pipeline_note"]
        assert len(data["results"]) > 1
    votes = [
        result
        for result in data["results"]
        if result.get("metadata", {}).get("pipeline_role") == "vote"
    ]
    if not votes:
        assert data["final_status"] == "uncertain"
        assert data["final_score"] == 0.0
    else:
        assert data["final_status"] in {"passed", "failed", "uncertain"}
        if data["final_status"] == "failed":
            assert any(vote["passed"] is False for vote in votes)
        if data["final_status"] == "passed":
            assert any(vote["passed"] is True for vote in votes)
    return data


def test_validate_endpoint():
    paris = _geography("Paris")
    berlin = _geography("Berlin")
    assert paris["results"][0]["metadata"]["pipeline_note"]
    assert berlin["results"][0]["metadata"]["pipeline_note"]


def test_validate_with_context():
    payload = {
        "question": "What is the capital of France?",
        "answer": "Paris",
        "context": "France is a country in Europe.",
    }
    response = client.post("/validate", json=payload)
    assert response.status_code == 200
    data = response.json()

    rule_results = [
        result
        for result in data["results"]
        if result["verifier_name"] == "rule"
    ]

    assert rule_results, f"No rule verifier result found. Results: {data['results']}"

    rule = rule_results[0]
    assert rule["metadata"]["rule"] == "unsupported"
    assert rule["metadata"]["pipeline_role"] == "abstention"


def test_orchestrator_pipeline():
    orchestrator = ValidationOrchestrator()
    response = orchestrator.validate(
        ValidationRequest(question="What is 2+2?", answer="4")
    )

    rule_results = [
        result
        for result in response.results
        if result.verifier_name == "rule"
    ]

    assert rule_results, "Rule verifier result not found"
    result = rule_results[0]
    assert result.metadata["rule"] == "arithmetic_addition"
    assert result.passed is True
    assert result.metadata["pipeline_role"] == "vote"
    assert "confidence 1" in result.metadata["pipeline_note"]
    assert response.final_status == "passed"
    assert response.final_score > 0.55


def test_wrong_addition_is_a_rule_rejection():
    orchestrator = ValidationOrchestrator()
    response = orchestrator.validate(
        ValidationRequest(question="What is 2+2?", answer="5")
    )

    rule_results = [
        result
        for result in response.results
        if result.verifier_name == "rule"
    ]

    assert rule_results, "Rule verifier result not found"
    result = rule_results[0]
    assert result.metadata["rule"] == "arithmetic_addition"
    assert result.metadata["expected"] == 4
    assert result.metadata["actual"] == 5
    assert result.passed is False
    assert result.score == 0.0
    assert result.metadata["pipeline_role"] == "vote"
    assert response.final_status == "failed"
    assert response.final_score < -0.55
