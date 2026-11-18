"""In-process API tests: fake service/bootstrap, fake DB, no lifespan or network."""
from copy import deepcopy
from contextlib import contextmanager
import sys
import importlib
from types import SimpleNamespace
from unittest.mock import Mock, patch

from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
import pytest
import requests

from app.game.deployment import FlexiblePolicyGameRuntime
from app.game.question_routing import (
    UnsupportedCompoundSyntaxError, QuestionClassificationError, classify_question,
)
from app.models.schemas import ValidationResponse
from app.services import compound_generation as compound
from app.services import answer_generation as generation
from app.services.validation_service import ValidationService

QUESTION = "What is the population of Cameroon, and what is that population plus 1000? Give both values."
ANSWER = '{"base":"29879337","derived":"29880337"}'


@pytest.fixture(scope="module")
def configuration():
    return compound.load_bundle()[0]


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    monkeypatch.setattr(requests.sessions.Session, "request", Mock(side_effect=AssertionError("No network permitted")))


class FakeService:
    def __init__(self, configuration):
        self.configuration = configuration
        self.calls = []
        self.summary = {"termination": "fixture", "team": ["evidence", "rule"]}
        self._orchestrator = SimpleNamespace(get_attempt_id_for_result=lambda result: None)

    def get_generation_policy_configuration(self):
        return self.configuration

    def validate(self, request):
        self.calls.append(request)
        return ValidationResponse(results=[], final_status="uncertain",
            validation_id="11111111-1111-4111-8111-111111111111", execution_audit=self.summary)

    def get_validation_context(self, validation_id):
        return SimpleNamespace(run_summary=self.summary)


@contextmanager
def isolated_routes(service):
    """Guard eager package imports and restore package/module/service state."""
    missing = object()
    app_package = sys.modules["app"]
    previous_package = sys.modules.get("app.api", missing)
    previous_app_attribute = getattr(app_package, "api", missing)
    previous = sys.modules.get("app.api.routes", missing)
    attributes = {name: getattr(previous_package, name, missing) for name in ("routes", "router")}
    try:
        # app.api.__init__ eagerly imports routes: both guards MUST precede it.
        with patch("psycopg2.connect", side_effect=AssertionError("No database access permitted")):
            with patch("app.services.validation_service.ValidationService", return_value=service):
                package = importlib.import_module("app.api")
                routes = importlib.import_module("app.api.routes")
            if previous is missing:
                routes.ValidationService = ValidationService
            with patch.object(routes, "_validation_service", service):
                yield routes
    finally:
        if previous is missing:
            sys.modules.pop("app.api.routes", None)
        else:
            sys.modules["app.api.routes"] = previous
        if previous_package is missing:
            sys.modules.pop("app.api", None)
        else:
            sys.modules["app.api"] = previous_package
            for name, value in attributes.items():
                if value is missing:
                    previous_package.__dict__.pop(name, None)
                else:
                    setattr(previous_package, name, value)
        if previous_app_attribute is missing:
            app_package.__dict__.pop("api", None)
        else:
            app_package.api = previous_app_attribute


@pytest.fixture
def api(monkeypatch, configuration):
    service = FakeService(configuration)
    with isolated_routes(service) as routes:
        statements, audits, updates = [], [], []
        cursor = SimpleNamespace(execute=lambda sql, values: statements.append((sql, values)),
            fetchone=lambda: (101,), close=Mock())
        connection = SimpleNamespace(cursor=lambda: cursor, commit=Mock(), rollback=Mock(), close=Mock())
        connect = Mock(return_value=connection)
        monkeypatch.setattr(routes, "get_connection", connect)
        monkeypatch.setattr(routes, "update_validation_record", lambda **kwargs: None)
        monkeypatch.setattr(routes, "create_audit", lambda **kwargs: audits.append(deepcopy(kwargs)))
        monkeypatch.setattr(routes, "update_audit", lambda *args, **kwargs: updates.append(deepcopy(kwargs)))
        monkeypatch.setattr(routes, "save_verifier_outputs", lambda **kwargs: None)
        monkeypatch.setattr(routes, "save_ground_truth", lambda **kwargs: None)
        llm = Mock(return_value="Generic answer")
        monkeypatch.setattr(generation.llm_service, "generate_answer", llm)
        # A supplied active snapshot must never cause another package load.
        monkeypatch.setattr(compound, "load_bundle", Mock(side_effect=AssertionError("Independent package reload")))
        adapter = importlib.import_module("app.benchmark.project_adapter")
        for name in ("construct_verifiers", "create_verifiers", "inspect_setup"):
            monkeypatch.setattr(adapter, name, Mock(side_effect=AssertionError("No verifier resources permitted")))
        application = FastAPI()
        application.include_router(routes.router)
        with TestClient(application) as client:
            yield SimpleNamespace(client=client, routes=routes, service=service,
                statements=statements, audits=audits, updates=updates, connection=connection,
                connect=connect, llm=llm)


@pytest.mark.parametrize("endpoint", ["/generate-answer", "/generate-and-validate"])
def test_compound_dispatch_answer_provenance_and_single_persistence(api, endpoint, monkeypatch):
    real = api.routes.dispatch_generation
    spy = Mock(wraps=real)
    monkeypatch.setattr(api.routes, "dispatch_generation", spy)
    response = api.client.post(endpoint, json={"question": QUESTION})
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["question_id"] == 101 and data["question"] == QUESTION
    assert data["status"] == "success" and data["answer"] == ANSWER
    assert data["generation_method"] == "source_grounded_deterministic_v1"
    provenance = data["generation_provenance"]
    assert provenance["source_manifest_id"] == api.service.configuration.router().catalog.source_manifest_id
    assert provenance["source_verified"] and provenance["arithmetic_validated"] and provenance["binder_accepted"]
    assert provenance["descriptor"]["source_id"] == "CM"
    assert len(provenance["source_hashes"]) == 3
    assert len(api.statements) == 1 and api.statements[0][1] == ((QUESTION, ANSWER, None) if endpoint == "/generate-answer" else (QUESTION, ANSWER))
    api.connection.commit.assert_called_once()
    spy.assert_called_once_with(QUESTION, validation_service=api.service)
    api.llm.assert_not_called()
    if endpoint.endswith("and-validate"):
        assert len(api.service.calls) == 1 and api.service.calls[0].answer == ANSWER
        initial = api.audits[0]["run_summary"]["generation"]
        completed = api.updates[0]["run_summary"]["generation"]
        assert initial == completed == {"generation_method": data["generation_method"], "generation_provenance": provenance}
        assert "generation" not in api.service.summary
    else:
        assert not api.service.calls and not api.audits


@pytest.mark.parametrize("endpoint", ["/generate-answer", "/generate-and-validate"])
@pytest.mark.parametrize("question", ["What is the capital of France?", "Explain quantum gravity.",
    "What is the capital of Trinidad and Tobago?", "Explain cats and dogs.",
    "What is the population of Trinidad and Tobago?"])
def test_generic_compatibility(api, endpoint, question):
    response = api.client.post(endpoint, json={"question": question})
    assert response.status_code == 200
    assert response.json()["answer"] == "Generic answer"
    assert response.json()["generation_method"] == "llm"
    api.llm.assert_called_once_with(question)
    assert len(api.statements) == 1


ERRORS = [
    (compound.UnsupportedRegistrationError, 422, "COMPOUND_REGISTRATION_UNSUPPORTED"),
    (compound.SourceUnavailableError, 503, "COMPOUND_SOURCE_UNAVAILABLE"),
    (compound.SourceIntegrityError, 500, "COMPOUND_SOURCE_INTEGRITY_MISMATCH"),
    (compound.FactLookupError, 500, "COMPOUND_SOURCE_FACT_NOT_UNIQUE"),
    (compound.ArithmeticFailure, 500, "COMPOUND_ARITHMETIC_FAILED"),
    (compound.ContractBindingError, 500, "COMPOUND_CONTRACT_BINDING_FAILED"),
    (compound.ConfigurationLoadingError, 500, "GENERATION_CONFIGURATION_INVALID"),
    (RuntimeError, 500, "GENERATION_INTERNAL_ERROR"),
]


@pytest.mark.parametrize("endpoint", ["/generate-answer", "/generate-and-validate"])
@pytest.mark.parametrize("error,status,code", ERRORS)
def test_generation_failure_has_no_fallback_or_side_effects(api, monkeypatch, endpoint, error, status, code):
    monkeypatch.setattr(generation, "generate_compound_answer", Mock(side_effect=error("secret C:/private/source stack")))
    response = api.client.post(endpoint, json={"question": QUESTION})
    assert response.status_code == status
    assert response.json()["detail"]["code"] == code
    assert response.json()["detail"]["stage"] == "generation"
    assert "secret" not in response.text and "C:/private" not in response.text
    api.llm.assert_not_called()
    api.connect.assert_not_called()
    assert not api.statements and not api.service.calls and not api.audits and not api.updates


@pytest.mark.parametrize("endpoint", ["/generate-answer", "/generate-and-validate"])
def test_unsupported_compound_syntax_never_falls_back(api, endpoint):
    response = api.client.post(endpoint, json={"question": QUESTION.replace("plus", "times")})
    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "COMPOUND_REGISTRATION_UNSUPPORTED"
    api.llm.assert_not_called()
    api.connect.assert_not_called()


def test_existing_routing_messages_and_exception_types(configuration):
    with pytest.raises(UnsupportedCompoundSyntaxError) as error:
        classify_question(QUESTION.replace("plus", "times"), component_catalog=configuration.router().catalog)
    assert str(error.value) == "unsupported_category: no declared component template"
    with pytest.raises(QuestionClassificationError) as error:
        classify_question("Explain quantum gravity.")
    assert str(error.value) == "unsupported_category: task routing requires supported known question requirements"
    router = configuration.router()
    assert router.resolve(QUESTION.replace("plus", "times"))[0] == "unsupported_category"


def test_active_snapshot_identity_and_mismatch_rejection(configuration):
    runtime = object.__new__(FlexiblePolicyGameRuntime)
    runtime._configuration = configuration
    runtime._router = configuration.router()
    service = ValidationService(orchestrator=object())
    service._generation_runtime = runtime
    service._generation_configuration = configuration
    assert service.get_generation_policy_configuration() is configuration
    runtime._router = SimpleNamespace(configuration=object())
    with pytest.raises(compound.ConfigurationLoadingError):
        generation.dispatch_generation(QUESTION, validation_service=service)


def test_unsuitable_runtime_fails_closed():
    service = ValidationService(orchestrator=object())
    with pytest.raises(compound.ConfigurationLoadingError):
        generation.dispatch_generation(QUESTION, validation_service=service)


def test_mismatched_configuration_returns_structured_error(api, monkeypatch):
    monkeypatch.setattr(api.service, "get_generation_policy_configuration", lambda: object())
    response = api.client.post("/generate-answer", json={"question": QUESTION})
    assert response.status_code == 500
    assert response.json()["detail"]["code"] == "GENERATION_CONFIGURATION_INVALID"
    api.connect.assert_not_called()
    api.llm.assert_not_called()


@pytest.mark.parametrize("endpoint", ["/generate-answer", "/generate-and-validate"])
def test_http_exception_preserved(api, endpoint, monkeypatch):
    monkeypatch.setattr(api.routes, "dispatch_generation", Mock(side_effect=HTTPException(409, "existing error")))
    response = api.client.post(endpoint, json={"question": QUESTION})
    assert response.status_code == 409 and response.json()["detail"] == "existing error"
    api.connect.assert_not_called()


@pytest.mark.parametrize("endpoint", ["/generate-answer", "/generate-and-validate"])
def test_database_failure_not_misclassified_as_generation(api, endpoint, monkeypatch):
    monkeypatch.setattr(api.routes, "get_connection", Mock(side_effect=RuntimeError("secret database path")))
    response = api.client.post(endpoint, json={"question": QUESTION})
    assert response.status_code == 500
    assert response.json()["detail"]["stage"] == "persistence"
    assert "secret" not in response.text and not api.service.calls


def test_validation_failure_not_misclassified_as_generation(api, monkeypatch):
    monkeypatch.setattr(api.service, "validate", Mock(side_effect=RuntimeError("secret validation path")))
    response = api.client.post("/generate-and-validate", json={"question": QUESTION})
    assert response.status_code == 500
    assert response.json()["detail"]["stage"] == "validation"
    assert len(api.statements) == 1 and not api.audits
    assert "secret" not in response.text


@pytest.mark.parametrize("error,status", [(UnsupportedCompoundSyntaxError, 422), (QuestionClassificationError, 200)])
def test_routing_uses_exception_types_not_messages(api, monkeypatch, error, status):
    monkeypatch.setattr(compound, "classify_generation_question", Mock(side_effect=error("entirely different text")))
    response = api.client.post("/generate-answer", json={"question": "Explain quantum gravity."})
    assert response.status_code == status
    if status == 422:
        api.llm.assert_not_called()
        api.connect.assert_not_called()
    else:
        api.llm.assert_called_once()


def test_client_cannot_select_policy_or_provenance(api):
    response = api.client.post("/generate-answer", json={"question": QUESTION,
        "policy_id": "untrusted", "generation_provenance": {"source_manifest_id": "untrusted"}})
    assert response.status_code == 200
    assert response.json()["generation_provenance"]["source_manifest_id"] != "untrusted"


def test_service_captures_constructed_runtime_snapshot(configuration, monkeypatch):
    module = importlib.import_module("app.services.validation_service")
    deployment = importlib.import_module("app.game.deployment")
    runtime = object.__new__(FlexiblePolicyGameRuntime)
    runtime._configuration = configuration
    runtime._router = configuration.router()
    monkeypatch.setattr(module.settings, "EXECUTION_MODE", "game")
    monkeypatch.setattr(deployment, "create_game_runtime", lambda: runtime)
    monkeypatch.setattr(module, "ValidationOrchestrator", Mock())
    monkeypatch.setattr("app.selection.verifier_selector.VerifierSelector", Mock())
    monkeypatch.setattr("app.analysis.question_analyzer.QuestionAnalyzer", Mock())
    service = ValidationService()
    assert service.get_generation_policy_configuration() is runtime.get_policy_configuration() is configuration
    runtime._configuration = object()
    runtime._router = SimpleNamespace(configuration=runtime._configuration)
    with pytest.raises(compound.ConfigurationLoadingError):
        service.get_generation_policy_configuration()


@pytest.mark.parametrize("mode", ["baseline", "prototype", "injected", "invalid"])
@pytest.mark.parametrize("question", ["What is the capital of Trinidad and Tobago?", "Explain cats and dogs."])
def test_ordinary_generation_without_flexible_snapshot(api, monkeypatch, mode, question):
    if mode == "invalid":
        getter = Mock(side_effect=compound.ConfigurationLoadingError("private error"))
    else:
        getter = Mock(return_value=None)
    monkeypatch.setattr(api.service, "get_generation_policy_configuration", getter)
    response = api.client.post("/generate-answer", json={"question": question})
    assert response.status_code == 200
    assert response.json()["answer"] == "Generic answer"
    api.llm.assert_called_once_with(question)


@pytest.mark.parametrize("question", [QUESTION, QUESTION.replace("plus", "times")])
@pytest.mark.parametrize("invalid", [False, True])
def test_compound_never_falls_back_without_snapshot(api, monkeypatch, question, invalid):
    getter = Mock(side_effect=compound.ConfigurationLoadingError("private")) if invalid else Mock(return_value=None)
    monkeypatch.setattr(api.service, "get_generation_policy_configuration", getter)
    response = api.client.post("/generate-and-validate", json={"question": question})
    assert response.status_code == 500
    assert response.json()["detail"]["code"] == "GENERATION_CONFIGURATION_INVALID"
    api.llm.assert_not_called()
    api.connect.assert_not_called()
    assert not api.service.calls and not api.audits


@pytest.mark.parametrize("branch", ["reference", "standalone", "ordinary"])
def test_all_atomic_signature_failures_are_typed(monkeypatch, branch):
    routing = importlib.import_module("app.game.question_routing")
    def fail(*args):
        raise ValueError("original classification failure")
    monkeypatch.setattr(routing, "analysis_signature", fail)
    kwargs = {}
    if branch == "reference":
        question = "Paraphrase this reference: Seven lanterns hang above the marina."
        kwargs["reference_question_version"] = importlib.import_module("app.analysis.reference_study_analyzer").VERSION
        expected = "original classification failure"
    elif branch == "standalone":
        question = QUESTION.replace("plus", "times")
        from app.analysis.task_analyzer import TaskQuestionAnalyzer
        arithmetic = TaskQuestionAnalyzer().analyze("What is 1 + 1?")
        monkeypatch.setattr(routing.CapabilityProbeAnalyzer, "analyze", lambda *args: arithmetic)
        expected = "original classification failure"
    else:
        question = "What is the capital of France?"
        expected = "unsupported_category: original classification failure"
    with pytest.raises(QuestionClassificationError) as error:
        routing.classify_question(question, **kwargs)
    assert str(error.value) == expected


def test_route_import_and_service_state_restored(configuration):
    missing = object()
    package = sys.modules.get("app.api", missing)
    before_package = package
    before_module = sys.modules.get("app.api.routes", missing)
    before_attribute = getattr(package, "routes", missing)
    original_service = getattr(before_module, "_validation_service", missing)
    for _ in range(2):
        fake = FakeService(configuration)
        with isolated_routes(fake) as routes:
            assert routes.ValidationService is ValidationService
            assert routes._validation_service is fake
        assert sys.modules.get("app.api.routes", missing) is before_module
        assert sys.modules.get("app.api", missing) is before_package
        assert getattr(package, "routes", missing) is before_attribute
        if before_module is not missing:
            assert before_module._validation_service is original_service


def test_existing_module_constructor_and_service_are_preserved(configuration):
    first = FakeService(configuration)
    second = FakeService(configuration)
    with isolated_routes(first) as existing:
        constructor = existing.ValidationService
        with isolated_routes(second) as nested:
            assert nested is existing and nested._validation_service is second
        assert existing._validation_service is first
        assert existing.ValidationService is constructor


@pytest.mark.parametrize("mode", ["baseline", "prototype", "injected"])
def test_real_service_accessors_preserve_ordinary_generation_without_activation(monkeypatch, mode):
    module = importlib.import_module("app.services.validation_service")
    deployment = importlib.import_module("app.game.deployment")
    monkeypatch.setattr(module, "ValidationOrchestrator", Mock())
    if mode == "injected":
        service = ValidationService(orchestrator=object())
    elif mode == "baseline":
        monkeypatch.setattr(module.settings, "EXECUTION_MODE", "baseline")
        service = ValidationService()
    else:
        monkeypatch.setattr(module.settings, "EXECUTION_MODE", "game")
        runtime = object.__new__(deployment.PrototypeGameRuntime)
        monkeypatch.setattr(deployment, "create_game_runtime", lambda: runtime)
        monkeypatch.setattr("app.benchmark.project_adapter.create_verifiers", lambda: ([], None))
        monkeypatch.setattr("app.selection.verifier_selector.VerifierSelector", Mock())
        service = ValidationService()
    assert service.get_generation_policy_configuration() is None
    expected = "Exact unchanged generic string."
    llm = Mock(return_value=expected)
    monkeypatch.setattr(generation.llm_service, "generate_answer", llm)
    monkeypatch.setattr(compound, "load_bundle", Mock(side_effect=AssertionError("No independent registry load")))
    result = generation.dispatch_generation("What is the capital of Trinidad and Tobago?", validation_service=service)
    assert result.answer == expected
    llm.assert_called_once()
    with pytest.raises(compound.ConfigurationLoadingError):
        generation.dispatch_generation(QUESTION, validation_service=service)
    llm.assert_called_once()


POSSESSIVE_COMPOUND_VARIANTS = [
    "What is the population of Cameroon, and what is its population plus 1000? Give both values.",
    "What is the population of Cameroon, and what is Cameroon's population plus 1000? Give both values.",
    "What is the population of Cameroon, and what is Cameroon\u2019s population plus 1000? Give both values.",
    "What is the population of Cameroon, and what is the country's population plus 1000? Give both values.",
    "What is the population of Cameroon, and what is the population of Cameroon plus 1000? Give both values.",
    "What is the population of Cameroon, and what is their population plus 1000? Give both values.",
    "What is the population of Cameroon, and what is its population times 1000? Give both values.",
    "What is the population of Cameroon, and what is its population plus one thousand? Give both values.",
    "What is the area of Bahrain, and what is its area plus 10 square kilometres? Give both values.",
]


@pytest.mark.parametrize("question", POSSESSIVE_COMPOUND_VARIANTS)
@pytest.mark.parametrize("snapshot", ["active", "missing", "invalid"])
@pytest.mark.parametrize("endpoint", ["/generate-answer", "/generate-and-validate"])
def test_explicit_compound_variants_never_reach_generic(api, monkeypatch, question, snapshot, endpoint):
    assert question not in api.service.configuration.allowlist
    if snapshot == "missing":
        monkeypatch.setattr(api.service, "get_generation_policy_configuration", lambda: None)
    elif snapshot == "invalid":
        monkeypatch.setattr(api.service, "get_generation_policy_configuration",
            Mock(side_effect=compound.ConfigurationLoadingError("private configuration detail")))
    response = api.client.post(endpoint, json={"question": question})
    assert response.status_code == (422 if snapshot == "active" else 500)
    assert response.json()["detail"]["code"] == (
        "COMPOUND_REGISTRATION_UNSUPPORTED" if snapshot == "active" else "GENERATION_CONFIGURATION_INVALID")
    api.llm.assert_not_called()
    api.connect.assert_not_called()
    assert not api.statements and not api.service.calls and not api.audits


@pytest.mark.parametrize("question", POSSESSIVE_COMPOUND_VARIANTS)
def test_generation_recognition_does_not_authorize_validation(configuration, question):
    from app.game.question_routing import classify_generation_question
    router = configuration.router()
    with pytest.raises(UnsupportedCompoundSyntaxError):
        classify_generation_question(question, component_catalog=router.catalog)
    # No dispatch, model construction or verifier execution: lookup only.
    assert question not in configuration.allowlist
    assert router.resolve(question, None) == (
        "unsupported_category", "question outside explicit allowlist", None)
    # Without an allowlist, preserve the base classifier's rejection too.
    with pytest.raises(UnsupportedCompoundSyntaxError) as error:
        classify_question(question, component_catalog=router.catalog)
    assert str(error.value) == "unsupported_category: no declared component template"


@pytest.mark.parametrize("question", ["What is the capital of Trinidad and Tobago?",
    "Explain cats and dogs.", "What is the population of Trinidad and Tobago?",
    "What is the population of Cameroon, and what is its area?",
    "Explain why population and area are both useful."])
@pytest.mark.parametrize("snapshot", [True, False])
def test_generation_guard_requires_fact_derived_operation_structure(api, monkeypatch, question, snapshot):
    if not snapshot:
        monkeypatch.setattr(api.service, "get_generation_policy_configuration", lambda: None)
    response = api.client.post("/generate-answer", json={"question": question})
    assert response.status_code == 200
    assert response.json()["answer"] == "Generic answer"
    api.llm.assert_called_once_with(question)


def test_registered_compound_still_uses_original_signature_and_route(configuration):
    from app.game.question_routing import classify_generation_question
    router = configuration.router()
    expected = configuration.component_entries[0][3].contract.question_signature
    assert classify_question(QUESTION, component_catalog=router.catalog)[:2] == ("component", expected)
    assert classify_generation_question(QUESTION, component_catalog=router.catalog)[:2] == ("component", expected)
    assert router.resolve(QUESTION, None)[0] == "component"
    # Restore the base validation guard rather than widening direct-fact routes.
    with pytest.raises(UnsupportedCompoundSyntaxError):
        classify_question("What is the capital of Trinidad and Tobago?", component_catalog=router.catalog)
    assert router.resolve("What is the capital of Trinidad and Tobago?", None)[2] is None
