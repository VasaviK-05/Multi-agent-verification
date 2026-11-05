"""Narrow server-boundary tests; no model construction, inference or persistence."""
from types import SimpleNamespace

from app.analysis.question_analyzer import QuestionAnalyzer
from app.game.deployment import FlexiblePolicyGameRuntime
from app.models.schemas import ValidationRequest, VerificationResult
from app.orchestration.validation_orchestrator import ValidationOrchestrator
from app.selection.verifier_selector import VerifierSelector


def test_flexible_component_dispatch_uses_factory_selector_and_observer(monkeypatch):
    runtime = object.__new__(FlexiblePolicyGameRuntime)
    compound = SimpleNamespace(policy_id="policy-id")
    runtime._compound = compound
    runtime._provider = SimpleNamespace(snapshot=lambda: ())
    runtime._bundle_id = "bundle-id"
    runtime._rng = object()
    runtime._adapter = object()
    runtime._adapter_for = lambda route_name: ("adapter", route_name)
    observer = SimpleNamespace(
        snapshot_for=lambda selector: SimpleNamespace(manifest_id="observed-manifest"),
        last_proof={"proof_id": "compatibility-proof"},
    )
    pool = [object(), object()]
    factory_selector = object()
    route = ("signature", 1.0, True, None, "component_dispatch")
    runtime._router = SimpleNamespace(
        resolve=lambda question, context: ("component", "signature", (route, object())),
        run=lambda selector, request, validation_id, **kwargs: SimpleNamespace(
            summary={"execution_mode": "component_policy", "policy_id": "policy-id"},
            public_status="uncertain", results=(), detail=None,
        ),
    )

    import app.game.offline.reconciled_resources as resources
    import scripts.reconciliation as reconciliation
    monkeypatch.setattr(resources, "create_scoped", lambda config, policy: (pool, observer))
    monkeypatch.setattr(reconciliation, "selector_for", lambda actual_pool: factory_selector)

    received = {}

    def run(selector, request, validation_id, **kwargs):
        received.update(selector=selector, observer=kwargs["resource_observer"],
                        provider=kwargs["provider"], rng=kwargs["rng"])
        return SimpleNamespace(
            summary={"execution_mode": "component_policy", "policy_id": "policy-id"},
            public_status="uncertain", results=(), detail=None,
        )

    runtime._router.run = run
    request = ValidationRequest(question="supported compound", answer="{}", context=None)
    result = runtime.run(object(), None, request, "validation-id")

    assert received["selector"] is factory_selector
    assert received["observer"] is observer
    assert received["provider"] is runtime._provider
    assert received["rng"] is runtime._rng
    assert result.summary["execution_mode"] == "flexible_game"
    assert result.summary["policy_bundle_id"] == "bundle-id"
    assert result.summary["validation_id"] == "validation-id"
    assert result.summary["pre_dispatch_resource_manifest_id"] == "observed-manifest"
    assert result.summary["pre_dispatch_compatibility_proof"]["proof_id"] == "compatibility-proof"


def test_flexible_preflight_failure_stops_before_router_sampling(monkeypatch):
    runtime = object.__new__(FlexiblePolicyGameRuntime)
    runtime._compound = SimpleNamespace(policy_id="policy-id")
    runtime._provider = SimpleNamespace(snapshot=lambda: ())
    runtime._bundle_id = "bundle-id"
    runtime._rng = object()
    runtime._adapter = object()
    runtime._adapter_for = lambda route_name: ("adapter", route_name)
    route = ("signature", 1.0, True, None, "component_dispatch")
    dispatched = []
    runtime._router = SimpleNamespace(
        resolve=lambda question, context: ("component", "signature", (route, object())),
        run=lambda *args, **kwargs: dispatched.append("run"),
    )

    import app.game.offline.reconciled_resources as resources
    import scripts.reconciliation as reconciliation

    observer = SimpleNamespace(
        snapshot_for=lambda selector: (_ for _ in ()).throw(ValueError("index changed")),
    )
    monkeypatch.setattr(resources, "create_scoped", lambda config, policy: ([object(), object()], observer))
    monkeypatch.setattr(reconciliation, "selector_for", lambda pool: object())

    result = runtime.run(
        object(), None,
        ValidationRequest(question="supported compound", answer="{}", context=None),
        "validation-id",
    )

    assert result.public_status == "uncertain"
    assert result.summary["selection_status"] == "resource_incompatible"
    assert "index changed" in result.summary["selection_reasons"][0]
    assert dispatched == []


def test_game_orchestrator_preserves_component_reports_without_reaggregation():
    report = VerificationResult(
        verifier_name="rule", score=0.0, passed=False,
        metadata={"component_id": "derived_sum", "binding_id": "binding"},
    )

    runtime = object.__new__(FlexiblePolicyGameRuntime)
    runtime.run = lambda selector, analysis, request, validation_id: SimpleNamespace(
        public_status="uncertain",
        summary={"execution_mode": "flexible_game", "attempts": [
            {"verifier_name": "rule", "report": report.model_dump(mode="json")},
        ]},
    )
    orchestrator = ValidationOrchestrator(
        question_analyzer=QuestionAnalyzer(mode="heuristic"),
        verifier_selector=VerifierSelector(verifiers=[]),
        execution_mode="game", game_runtime=runtime,
    )

    response = orchestrator.validate(ValidationRequest(
        question="supported compound", answer="{}", context=None,
    ))

    assert response.final_status == "uncertain"
    assert response.final_score is None
    assert [row.verifier_name for row in response.results] == ["rule"]
    assert response.execution_audit["attempts"][0]["report"]["metadata"]["component_id"] == "derived_sum"
