"""Offline ownership/dispatch proofs; no database, model, or service calls."""
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

import pytest

from app.models.schemas import ValidationRequest
from app.orchestration import validation_orchestrator as module
from app.selection.baseline_budget import BaselineBudgetSnapshot
from app.selection.capabilities import CapabilityDescriptor
from app.selection.verifier_selector import VerifierSelector
from tests.test_adaptive_pipeline import (
    offline_pipeline_boundaries, FixedAnalyzer, MetadataChecker, factual_metadata,
)
from app.analysis.models import QuestionAnalysis
from tests.test_game_runtime import runtime_fixture
from app.game.execution import GameRun


@pytest.fixture(autouse=True)
def offline(offline_pipeline_boundaries, monkeypatch):
    import psycopg2
    from app.utils.config import settings
    monkeypatch.setattr(settings, "BASELINE_BUDGET_CONFIG_PATH", "")
    monkeypatch.setattr(module, "get_connection", Mock(side_effect=AssertionError("no real database")))
    monkeypatch.setattr(psycopg2, "connect", Mock(side_effect=AssertionError("no real database")))


@pytest.fixture
def persistence(monkeypatch):
    connection = SimpleNamespace(commit=Mock(), rollback=Mock(), close=Mock())
    monkeypatch.setattr(module, "get_connection", Mock(return_value=connection))
    names = ("create_validation_record", "begin_validation", "mark_execution_ready",
             "mark_execution_running", "update_execution_plan", "mark_execution_completed",
             "mark_execution_failed", "create_verifier_attempt", "mark_verifier_attempt_started",
             "mark_verifier_attempt_completed", "mark_verifier_attempt_error",
             "mark_verifier_attempt_failed", "mark_verifier_attempt_unavailable")
    mocks = {name: Mock() for name in names}
    mocks["mark_execution_running"].return_value = {"lease_token": "original-game-lease"}
    mocks["create_verifier_attempt"].side_effect = lambda **kw: {"attempt_id": str(uuid4())}
    for name, mock in mocks.items():
        monkeypatch.setattr(module, name, mock)
    heartbeat = SimpleNamespace(start=Mock(), stop=Mock(), assert_owned=Mock())
    heartbeat.start.return_value = heartbeat
    mocks["heartbeat_factory"] = Mock(return_value=heartbeat)
    monkeypatch.setattr(module, "ExecutionLeaseHeartbeat", mocks["heartbeat_factory"])
    return SimpleNamespace(mocks=mocks, heartbeat=heartbeat, connection=connection)


def baseline(persist=False, *, capability="direct_fact", reference=False, count=2, budget=None):
    checks = [MetadataChecker(name, score=1., metadata=factual_metadata())
              for name in ("a", "b")[:count]]
    selector = VerifierSelector(verifiers=checks,
        capabilities={c.name: CapabilityDescriptor((capability,), requires_reference=reference) for c in checks})
    provider = Mock(return_value=budget or BaselineBudgetSnapshot())
    run = module.ValidationOrchestrator(
        question_analyzer=FixedAnalyzer(QuestionAnalysis("general", "easy", .1,
                                                       verification_types=["direct_fact"])),
        verifier_selector=selector, persist_execution=persist, baseline_budget_provider=provider)
    return run, checks, provider


def game_failure(monkeypatch, baseline_run, *, status="no_feasible_strategy", persist=False,
                 extra=None, start=False, error=None):
    game, game_checks, _, _ = runtime_fixture()
    game._persist_execution = persist
    factory = Mock(return_value=baseline_run)
    monkeypatch.setattr(game, "_new_fallback_baseline", factory)
    def run(runtime, selector, analysis, request, validation_id, *, execution_journal):
        if start:
            execution_journal.start_attempt(verifier_name="a")
        if error:
            raise error
        return GameRun((), None, "uncertain", {
            "selection_status": status, "selection_reasons": ["no team"], **(extra or {})})
    monkeypatch.setattr(type(game._game_runtime), "run", run)
    return game, factory


REQUEST = ValidationRequest(question="What is the population?", answer="42", context="Population: 42.")


def test_direct_baseline_owns_one_lifecycle(persistence):
    run, checks, provider = baseline(True)
    result = run.validate(REQUEST)
    for name in ("create_validation_record", "begin_validation", "mark_execution_ready",
                 "mark_execution_running", "mark_execution_completed", "heartbeat_factory"):
        persistence.mocks[name].assert_called_once()
    assert [c.calls for c in checks] == [1, 1]
    assert result.validation_id == persistence.mocks["begin_validation"].call_args.kwargs["validation_id"]
    provider.assert_called_once_with(run.verifier_selector)


@pytest.mark.parametrize("persist", [False, True])
@pytest.mark.parametrize("status", ["no_feasible_strategy", "game_policy_missing", "game_policy_incompatible", "missing_policy"])
def test_fallback_reuses_identity_and_active_owner(monkeypatch, persistence, persist, status):
    base, checks, provider = baseline(persist)
    game, factory = game_failure(monkeypatch, base, status=status, persist=persist)
    response = game.validate(REQUEST)
    audit = response.execution_audit
    assert audit["requested_mode"] == "game" and audit["executed_mode"] == "baseline"
    assert audit["fallback_triggered"] and not audit["game_verifier_execution_started"]
    assert audit["fallback_decision"] == "accepted"
    assert audit["baseline_preparation_status"] == "completed"
    assert audit["game_failure_reason"] == ["no team"]
    assert audit["baseline_budget"]["status"] == "unconfigured"
    assert audit["baseline_execution_details"]["final_decision"] == response.final_status
    assert [c.calls for c in checks] == [1, 1]
    factory.assert_called_once()
    provider.assert_called_once()
    if persist:
        for name in ("create_validation_record", "begin_validation", "mark_execution_running",
                     "mark_execution_ready", "mark_execution_completed", "heartbeat_factory"):
            persistence.mocks[name].assert_called_once()
        assert persistence.mocks["begin_validation"].call_args.kwargs["validation_id"] == response.validation_id
        persistence.heartbeat.stop.assert_called_once()
        for name in ("update_execution_plan", "create_verifier_attempt", "mark_verifier_attempt_started",
                     "mark_verifier_attempt_completed", "mark_execution_completed"):
            for call in persistence.mocks[name].call_args_list:
                assert call.kwargs["lease_token"] == "original-game-lease"
        assert persistence.mocks["create_verifier_attempt"].call_count == 2
        persistence.mocks["mark_execution_failed"].assert_not_called()


@pytest.mark.parametrize("status", ["selected", "task_reference_mismatch", "unsupported_category", "resource_incompatible"])
def test_noneligible_game_outcomes_never_construct_baseline(monkeypatch, status):
    base, checks, _ = baseline()
    game, factory = game_failure(monkeypatch, base, status=status)
    result = game.validate(REQUEST)
    assert result.final_status == "uncertain"
    factory.assert_not_called()
    assert not any(c.calls for c in checks)


@pytest.mark.parametrize("error", [None, RuntimeError("after dispatch")])
@pytest.mark.parametrize("persist", [False, True])
def test_started_is_monotonic_and_disables_fallback(monkeypatch, persistence, error, persist):
    base, checks, _ = baseline(persist)
    game, factory = game_failure(monkeypatch, base, persist=persist, start=True, error=error)
    if error:
        with pytest.raises(RuntimeError, match="after dispatch"):
            game.validate(REQUEST)
        if persist:
            detail = persistence.mocks["mark_execution_failed"].call_args.kwargs["failure_details"]
            assert detail["baseline_eligibility"] is False
            assert detail["baseline_preparation_status"] == "not_started"
            assert detail["game_failure_stage"] == "execution"
            assert detail["game_failure_reason"] == ["after dispatch"]
    else:
        response = game.validate(REQUEST)
        assert response.execution_audit["game_verifier_execution_started"] is True
    factory.assert_not_called()
    assert not any(c.calls for c in checks)


@pytest.mark.parametrize("kind,expected", [
    ("unknown", "baseline_coverage_unproven"),
    ("unsupported", "baseline_coverage_unproven"),
    ("contributors", "baseline_insufficient_contributors"),
    ("prerequisite", "baseline_coverage_unproven"),
    ("budget_invalid", "baseline_budget_configuration_invalid"),
    ("budget_infeasible", "baseline_budget_feasibility_unproven"),
])
def test_rejected_fallback_preserves_original_diagnostics(monkeypatch, persistence, kind, expected):
    base, checks, _ = baseline(True, count=1 if kind == "contributors" else 2,
        capability="arithmetic" if kind == "unsupported" else "direct_fact",
        reference=kind == "prerequisite")
    request = REQUEST.model_copy(update={"context": None}) if kind == "prerequisite" else REQUEST
    if kind == "unknown":
        base._question_analyzer = FixedAnalyzer(QuestionAnalysis("general", "easy", .1))
    if kind == "budget_invalid":
        from app.utils.config import settings
        monkeypatch.setattr(settings, "BASELINE_BUDGET_CONFIG_PATH", "explicit-invalid.json")
    if kind == "budget_infeasible":
        base._baseline_budget_provider.return_value = BaselineBudgetSnapshot(
            status="configured", limit_ms=0., costs=(("a", 10.), ("b", 10.)))
    game, _ = game_failure(monkeypatch, base, persist=True)
    response = game.validate(request)
    assert response.execution_audit["fallback_rejection_reason"] == expected
    assert response.execution_audit["game_execution_details"]["selection_status"] == "no_feasible_strategy"
    assert not response.execution_audit["fallback_triggered"]
    assert not any(c.calls for c in checks)
    persistence.mocks["mark_execution_completed"].assert_called_once()
    persistence.mocks["create_verifier_attempt"].assert_not_called()


def test_flexible_missing_policy_is_not_artifact_failure(monkeypatch):
    base, _, _ = baseline()
    game, factory = game_failure(monkeypatch, base, status="missing_policy", extra={"policy_category": "missing_policy"})
    game.validate(REQUEST)
    factory.assert_not_called()


def test_baseline_exception_keeps_original_failure_in_failed_journal(monkeypatch, persistence):
    base, checks, _ = baseline(True)
    checks[0].verify = Mock(side_effect=RuntimeError("baseline failed"))
    game, _ = game_failure(monkeypatch, base, persist=True)
    with pytest.raises(RuntimeError, match="baseline failed"):
        game.validate(REQUEST)
    persistence.mocks["mark_execution_completed"].assert_not_called()
    failed = persistence.mocks["mark_execution_failed"].call_args.kwargs["failure_details"]
    assert failed["game_execution_details"]["selection_status"] == "no_feasible_strategy"
    persistence.heartbeat.stop.assert_called_once()


def test_lease_loss_prevents_handoff_dispatch(monkeypatch, persistence):
    base, checks, _ = baseline(True)
    game, _ = game_failure(monkeypatch, base, persist=True)
    persistence.heartbeat.assert_owned.side_effect = RuntimeError("lease lost")
    with pytest.raises(RuntimeError, match="lease lost"):
        game.validate(REQUEST)
    assert not any(c.calls for c in checks)
    persistence.mocks["mark_execution_running"].assert_called_once()


def test_missing_reference_rejected_before_baseline_preparation(monkeypatch):
    base, _, _ = baseline()
    game, factory = game_failure(monkeypatch, base)
    response = game.validate(ValidationRequest(question="Paraphrase this reference: A.", answer="A."))
    assert response.execution_audit["fallback_rejection_reason"] == "request_prerequisite_unsatisfied"
    factory.assert_not_called()


@pytest.mark.parametrize("message,status", [
    ("Configured flexible policy package does not exist: absent-package.json", "game_policy_missing"),
    ("frozen policy bundle bytes differ", "game_policy_incompatible"),
])
def test_service_classified_initialization_failure_reaches_handoff(monkeypatch, message, status):
    from app.services import validation_service
    from app.game import deployment
    from app.utils.config import settings
    monkeypatch.setattr(settings, "EXECUTION_MODE", "game")
    monkeypatch.setattr(settings, "GAME_FLEXIBLE_POLICY_PACKAGE_PATH", "absent-package.json")
    monkeypatch.setattr(settings, "GAME_POLICY_BUNDLE_PATH", "")
    monkeypatch.setattr(settings, "GAME_POLICY_ARTIFACT_PATH", "")
    error = FileNotFoundError(message) if status == "game_policy_missing" else ValueError(message)
    monkeypatch.setattr(deployment, "create_game_runtime", Mock(side_effect=error))
    base, checks, _ = baseline()
    service = validation_service.ValidationService()
    monkeypatch.setattr(service._orchestrator, "_new_fallback_baseline", lambda: base)
    response = service.validate(REQUEST)
    audit = response.execution_audit
    assert audit["executed_mode"] == "baseline"
    assert audit["game_execution_details"]["initialization_failure"]["error_type"] == type(error).__name__
    assert audit["fallback_reason"] == status
    assert [c.calls for c in checks] == [1, 1]


def test_invalid_evidence_is_rejected_without_dispatch(monkeypatch):
    from app.selection import baseline_resources
    base, checks, _ = baseline()
    # Use the reviewed subclass with injected instances, retaining their identity.
    base._verifier_selector = baseline_resources.BaselineVerifierSelector(verifiers=checks,
        capabilities={c.name: CapabilityDescriptor(("direct_fact",)) for c in checks})
    base._verifier_selector.configure_baseline_evidence(SimpleNamespace(configuration_id="selected"))
    plan = base._verifier_selector.plan(QuestionAnalysis("general", "easy", .1,
        verification_types=["direct_fact"]), REQUEST.context)
    from dataclasses import replace
    monkeypatch.setattr(base._verifier_selector, "plan", lambda *args: replace(plan, fallback=("evidence",)))
    validate = Mock(side_effect=ValueError("index hash differs"))
    monkeypatch.setattr(baseline_resources, "validate_baseline_evidence", validate)
    game, _ = game_failure(monkeypatch, base)
    result = game.validate(REQUEST)
    assert result.execution_audit["fallback_rejection_reason"] == "baseline_resources_incompatible"
    validate.assert_called_once()
    assert not any(c.calls for c in checks)


def test_compatible_budget_is_captured_once_and_charges_attempts(monkeypatch):
    budget = BaselineBudgetSnapshot(status="configured", limit_ms=1000., costs=(("a", 1.), ("b", 1.)))
    base, checks, provider = baseline(budget=budget)
    game, _ = game_failure(monkeypatch, base)
    result = game.validate(REQUEST)
    observed = result.execution_audit["baseline_budget"]
    assert observed["status"] == "configured" and observed["limit_ms"] == 1000.
    assert len(observed["attempts"]) == 2
    assert observed["actual_attempt_ms"] == sum(a["duration_ms"] for a in observed["attempts"])
    assert observed["remaining_ms"] == max(0., 1000. - observed["actual_attempt_ms"])
    provider.assert_called_once()


def test_api_returns_fallback_audit_without_schema_changes(monkeypatch, offline_pipeline_boundaries):
    from fastapi.testclient import TestClient
    from app.services.validation_service import ValidationService
    base, checks, _ = baseline()
    game, _ = game_failure(monkeypatch, base)
    monkeypatch.setattr(offline_pipeline_boundaries.routes, "_validation_service", ValidationService(game))
    client = TestClient(offline_pipeline_boundaries.app)
    response = client.post("/validate", json=REQUEST.model_dump())
    assert response.status_code == 200
    payload = response.json()
    assert payload["execution_audit"]["executed_mode"] == "baseline"
    assert len(payload["results"]) == 2


def test_finalization_error_records_failure_once_under_original_lease(monkeypatch, persistence):
    base, checks, _ = baseline(True)
    base._automatic_ground_truth.evaluate = Mock(side_effect=RuntimeError("finalization failed"))
    game, _ = game_failure(monkeypatch, base, persist=True)
    with pytest.raises(RuntimeError, match="finalization failed"):
        game.validate(REQUEST)
    persistence.mocks["mark_execution_completed"].assert_not_called()
    persistence.mocks["mark_execution_failed"].assert_called_once()
    failed = persistence.mocks["mark_execution_failed"].call_args.kwargs
    assert failed["lease_token"] == "original-game-lease"
    assert failed["failure_details"]["game_execution_details"]["selection_status"] == "no_feasible_strategy"
    persistence.heartbeat.stop.assert_called_once()


def test_preparation_and_planning_are_not_repeated(monkeypatch):
    base, checks, provider = baseline()
    base._question_analyzer.analyze = Mock(wraps=base._question_analyzer.analyze)
    base._verifier_selector.plan = Mock(wraps=base._verifier_selector.plan)
    game, _ = game_failure(monkeypatch, base)
    game.validate(REQUEST)
    base._question_analyzer.analyze.assert_called_once_with(REQUEST.question)
    base._verifier_selector.plan.assert_called_once()
    provider.assert_called_once()


@pytest.mark.parametrize("persist", [False, True])
@pytest.mark.parametrize("mode", [None, "failure"])
def test_actual_component_dispatch_sets_observer_before_verify(monkeypatch, persistence, persist, mode):
    from tests.test_component_execution import setup, Q, REF
    from app.game.component_execution import run_component_diagnostic
    contract, strategy, selector, resource_observer, calls = setup(mode)
    game, _, _, _ = runtime_fixture()
    game._persist_execution = persist
    forbidden = Mock(side_effect=AssertionError("component execution cannot fallback"))
    monkeypatch.setattr(game, "_new_fallback_baseline", forbidden)
    boundary = {}
    evidence = selector.resolve("evidence")
    original = evidence.verify
    def verify(*args):
        assert boundary["observer"].started is True
        return original(*args)
    monkeypatch.setattr(evidence, "verify", verify)
    def run(runtime, actual_selector, analysis, request, validation_id, *, execution_journal):
        boundary["observer"] = execution_journal
        return run_component_diagnostic(contract, strategy, selector, request.question,
            request.answer, request.context, validation_id,
            resource_observer=resource_observer, execution_journal=execution_journal)
    monkeypatch.setattr(type(game._game_runtime), "run", run)
    response = game.validate(ValidationRequest(question=Q, answer='{"base":"765","derived":"775"}', context=REF))
    assert response.execution_audit["game_verifier_execution_started"] is True
    assert not response.execution_audit["fallback_triggered"]
    assert len(calls) == 2
    forbidden.assert_not_called()


def include_mock_evidence(monkeypatch, base):
    """Reach the resource guard without constructing any Evidence verifier."""
    from dataclasses import replace
    original = base.verifier_selector.plan
    monkeypatch.setattr(base.verifier_selector, "plan", lambda *args: replace(
        original(*args), fallback=("evidence",)))
    monkeypatch.setattr(base.verifier_selector, "baseline_evidence_configuration",
                        SimpleNamespace(configuration_id="mock-selected"), raising=False)


@pytest.mark.parametrize("persist", [False, True])
@pytest.mark.parametrize("signal_type", [KeyboardInterrupt, SystemExit])
@pytest.mark.parametrize("phase", ["selector_construction", "analysis", "selection_planning",
    "resource_validation", "budget_capture", "budget_admission", "execution", "finalization"])
def test_interruption_owns_entire_fallback_lifecycle(monkeypatch, persistence, persist, signal_type, phase):
    import traceback
    from app.selection import baseline_resources
    base, checks, _ = baseline(persist)
    game, factory = game_failure(monkeypatch, base, persist=persist)
    signal = signal_type("original interruption")
    def interrupt(*args, **kwargs):
        raise signal
    if phase == "selector_construction":
        factory.side_effect = interrupt
    elif phase == "analysis":
        monkeypatch.setattr(base._question_analyzer, "analyze", interrupt)
    elif phase == "selection_planning":
        monkeypatch.setattr(base.verifier_selector, "plan", interrupt)
    elif phase == "resource_validation":
        include_mock_evidence(monkeypatch, base)
        monkeypatch.setattr(baseline_resources, "validate_baseline_evidence", interrupt)
    elif phase == "budget_capture":
        base._baseline_budget_provider.side_effect = interrupt
    elif phase == "budget_admission":
        monkeypatch.setattr(module, "plan_with_budget", interrupt)
    elif phase == "execution":
        monkeypatch.setattr(checks[0], "verify", interrupt)
    else:
        monkeypatch.setattr(base._automatic_ground_truth, "evaluate", interrupt)
    with pytest.raises(signal_type) as captured:
        game.validate(REQUEST)
    assert captured.value is signal
    assert traceback.extract_tb(captured.value.__traceback__)[-1].name == "interrupt"
    assert all(c.calls == 0 for c in checks) if phase != "finalization" else all(c.calls == 1 for c in checks)
    if persist:
        persistence.heartbeat.stop.assert_called_once()
        for name in ("create_validation_record", "begin_validation", "mark_execution_running", "mark_execution_failed"):
            persistence.mocks[name].assert_called_once()
        persistence.mocks["mark_execution_completed"].assert_not_called()
        failed = persistence.mocks["mark_execution_failed"].call_args.kwargs
        assert failed["lease_token"] == "original-game-lease"
        detail = failed["failure_details"]
        assert detail["game_failure_reason"] == ["no team"]
        assert detail["fallback_decision"] == "interrupted"
        assert detail["baseline_failure"]["error_type"] == signal_type.__name__
        ids = {persistence.mocks[n].call_args.kwargs["validation_id"] for n in (
            "create_validation_record", "begin_validation", "mark_execution_failed")}
        assert len(ids) == 1
        if phase not in {"execution", "finalization"}:
            persistence.mocks["create_verifier_attempt"].assert_not_called()
            assert detail["baseline_preparation_status"] == "interrupted"
            assert detail["baseline_preparation_stage"] == phase
    else:
        persistence.heartbeat.stop.assert_not_called()
        persistence.mocks["mark_execution_failed"].assert_not_called()


@pytest.mark.parametrize("cleanup_failure", ["failure_write", "attempt_write", "heartbeat_stop"])
def test_cleanup_error_never_masks_original_interruption(monkeypatch, persistence, cleanup_failure):
    base, checks, _ = baseline(True)
    game, _ = game_failure(monkeypatch, base, persist=True)
    signal = KeyboardInterrupt("keep this signal")
    def interrupt(*args):
        raise signal
    monkeypatch.setattr(checks[0], "verify", interrupt)
    if cleanup_failure == "failure_write":
        persistence.mocks["mark_execution_failed"].side_effect = RuntimeError("write unavailable")
    elif cleanup_failure == "attempt_write":
        persistence.mocks["mark_verifier_attempt_error"].side_effect = RuntimeError("attempt write unavailable")
    else:
        persistence.heartbeat.stop.side_effect = RuntimeError("stop failed")
    with pytest.raises(KeyboardInterrupt) as captured:
        game.validate(REQUEST)
    assert captured.value is signal
    persistence.heartbeat.stop.assert_called_once()
    persistence.mocks["mark_execution_completed"].assert_not_called()
    persistence.mocks["mark_execution_running"].assert_called_once()
    persistence.mocks["mark_execution_failed"].assert_called_once()


class ControlledInterruption(BaseException):
    pass


def test_other_baseexception_during_construction_is_not_swallowed(monkeypatch, persistence):
    base, _, _ = baseline(True)
    game, factory = game_failure(monkeypatch, base, persist=True)
    signal = ControlledInterruption("stop")
    factory.side_effect = signal
    with pytest.raises(ControlledInterruption) as captured:
        game.validate(REQUEST)
    assert captured.value is signal
    persistence.heartbeat.stop.assert_called_once()
    persistence.mocks["mark_execution_failed"].assert_called_once()


def test_preparation_interruption_does_not_fail_an_execution_after_lease_loss(monkeypatch, persistence):
    base, _, _ = baseline(True)
    game, factory = game_failure(monkeypatch, base, persist=True)
    signal = KeyboardInterrupt("original signal")
    factory.side_effect = signal
    persistence.heartbeat.assert_owned.side_effect = RuntimeError("lease belongs to another owner")
    with pytest.raises(KeyboardInterrupt) as captured:
        game.validate(REQUEST)
    assert captured.value is signal
    persistence.mocks["mark_execution_failed"].assert_not_called()
    persistence.mocks["mark_execution_completed"].assert_not_called()
    persistence.mocks["mark_execution_running"].assert_called_once()
    persistence.heartbeat.stop.assert_called_once()


@pytest.mark.parametrize("signal_type", [KeyboardInterrupt, SystemExit])
def test_interrupted_terminal_write_is_not_finalized_again(monkeypatch, persistence, signal_type):
    base, _, _ = baseline(True)
    game, _ = game_failure(monkeypatch, base, persist=True)
    signal = signal_type("completion outcome unknown")
    persistence.mocks["mark_execution_completed"].side_effect = signal
    with pytest.raises(signal_type) as captured:
        game.validate(REQUEST)
    assert captured.value is signal
    persistence.mocks["mark_execution_completed"].assert_called_once()
    persistence.mocks["mark_execution_failed"].assert_not_called()
    persistence.heartbeat.stop.assert_called_once()


@pytest.mark.parametrize("kind,stage,preparation", [
    ("resource_incompatible", "resource_preflight", "not_started"),
    ("flexible_missing_policy", "routing", "not_started"),
    ("missing_context", "strategy_selection", "not_started"),
    ("unsupported", "strategy_selection", "rejected"),
    ("invalid_evidence", "strategy_selection", "rejected"),
    ("invalid_budget", "strategy_selection", "rejected"),
    ("unknown", "strategy_selection", "rejected"),
    ("uncovered", "strategy_selection", "rejected"),
])
def test_all_rejections_have_complete_separate_audits(monkeypatch, persistence, kind, stage, preparation):
    from app.selection import baseline_resources
    base, checks, _ = baseline(True, capability="arithmetic" if kind == "uncovered" else "direct_fact")
    status = "resource_incompatible" if kind == "resource_incompatible" else (
        "missing_policy" if kind == "flexible_missing_policy" else "no_feasible_strategy")
    game, factory = game_failure(monkeypatch, base, status=status, persist=True,
        extra={"policy_category": "missing_policy"} if kind == "flexible_missing_policy" else None)
    request = REQUEST
    if kind == "missing_context":
        request = ValidationRequest(question="Paraphrase this reference: A.", answer="A.")
    elif kind in {"unsupported", "unknown"}:
        base._question_analyzer = FixedAnalyzer(QuestionAnalysis("general", "easy", .1,
            verification_types=["not_supported"] if kind == "unsupported" else []))
    elif kind == "invalid_evidence":
        include_mock_evidence(monkeypatch, base)
        monkeypatch.setattr(baseline_resources, "validate_baseline_evidence", Mock(side_effect=ValueError("bad receipt")))
    elif kind == "invalid_budget":
        from app.utils.config import settings
        monkeypatch.setattr(settings, "BASELINE_BUDGET_CONFIG_PATH", "explicit-invalid.json")
    result = game.validate(request)
    audit = result.execution_audit
    assert audit["requested_mode"] == audit["executed_mode"] == "game"
    assert audit["game_failure_stage"] == stage
    assert audit["game_failure_status"] == status
    assert audit["game_failure_reason"] == ["no team"]
    assert audit["game_execution_details"]["selection_reasons"] == ["no team"]
    assert audit["baseline_eligibility"] is False and audit["fallback_triggered"] is False
    assert audit["fallback_decision"] == "rejected"
    assert audit["fallback_rejection_reason"] != "no team"
    assert audit["baseline_preparation_status"] == preparation
    assert audit["game_verifier_execution_started"] is False
    if preparation == "not_started":
        factory.assert_not_called()
        assert "baseline_selection" not in audit and "baseline_budget" not in audit
    if kind == "invalid_evidence":
        assert audit["baseline_resource_validation"] == "failed"
    assert not any(c.calls for c in checks)
    persistence.heartbeat.stop.assert_called_once()
    persistence.mocks["mark_execution_failed"].assert_not_called()
    persistence.mocks["mark_execution_completed"].assert_called_once()
    stored = persistence.mocks["mark_execution_completed"].call_args.kwargs["final_response"]["execution_audit"]
    assert stored == audit


@pytest.mark.parametrize("error_type", [RuntimeError, KeyboardInterrupt, SystemExit, ControlledInterruption])
def test_final_response_serialization_failure_records_one_failure(monkeypatch, persistence, error_type):
    import traceback
    base, checks, _ = baseline(True)
    game, _ = game_failure(monkeypatch, base, persist=True)
    error = error_type("response serialization failed")
    def serialize(response, **kwargs):
        raise error
    monkeypatch.setattr(module.ValidationResponse, "model_dump", serialize)
    with pytest.raises(error_type) as captured:
        game.validate(REQUEST)
    assert captured.value is error
    assert traceback.extract_tb(error.__traceback__)[-1].name == "serialize"
    persistence.mocks["mark_execution_completed"].assert_not_called()
    persistence.mocks["mark_execution_failed"].assert_called_once()
    persistence.heartbeat.stop.assert_called_once()
    failed = persistence.mocks["mark_execution_failed"].call_args.kwargs
    assert failed["lease_token"] == "original-game-lease"
    assert failed["failure_details"]["error_type"] == error_type.__name__
    assert failed["failure_details"]["game_failure_reason"] == ["no team"]
    for name in ("create_validation_record", "begin_validation", "mark_execution_running"):
        persistence.mocks[name].assert_called_once()
        assert persistence.mocks[name].call_args.kwargs["validation_id"] == failed["validation_id"]
    assert [c.calls for c in checks] == [1, 1]


@pytest.mark.parametrize("outcome", ["success", "runtime_error", "keyboard_interrupt", "system_exit"])
def test_terminal_completion_serialization_order_and_no_second_write(monkeypatch, persistence, outcome):
    base, checks, _ = baseline(True)
    game, _ = game_failure(monkeypatch, base, persist=True)
    events, context = [], {}
    original_execute = base._execute_baseline
    original_dump = module.ValidationResponse.model_dump
    def execute(*args, **kwargs):
        context["lifecycle"] = kwargs["lifecycle"]
        return original_execute(*args, **kwargs)
    def serialize(response, **kwargs):
        assert context["lifecycle"].terminalization_attempted is False
        events.append("serialized")
        return original_dump(response, **kwargs)
    error = {"runtime_error": RuntimeError("completion outcome unknown"),
             "keyboard_interrupt": KeyboardInterrupt("completion outcome unknown"),
             "system_exit": SystemExit("completion outcome unknown")}.get(outcome)
    def complete(**kwargs):
        assert context["lifecycle"].terminalization_attempted is True
        assert isinstance(kwargs["final_response"], dict)
        events.append("completion")
        if error is not None:
            raise error
    monkeypatch.setattr(base, "_execute_baseline", execute)
    monkeypatch.setattr(module.ValidationResponse, "model_dump", serialize)
    persistence.mocks["mark_execution_completed"].side_effect = complete
    if error is None:
        result = game.validate(REQUEST)
        assert result.validation_id == persistence.mocks["mark_execution_completed"].call_args.kwargs["validation_id"]
    else:
        with pytest.raises(type(error)) as captured:
            game.validate(REQUEST)
        assert captured.value is error
    assert events == ["serialized", "completion"]
    persistence.mocks["mark_execution_completed"].assert_called_once()
    persistence.mocks["mark_execution_failed"].assert_not_called()
    persistence.heartbeat.stop.assert_called_once()
    for name in ("create_validation_record", "begin_validation", "mark_execution_running"):
        persistence.mocks[name].assert_called_once()
    assert [c.calls for c in checks] == [1, 1]


@pytest.mark.parametrize("error_type", [RuntimeError, KeyboardInterrupt])
def test_final_response_serialization_lease_loss_blocks_failure_write(monkeypatch, persistence, error_type):
    base, checks, _ = baseline(True)
    game, _ = game_failure(monkeypatch, base, persist=True)
    error = error_type("serialization failed after lease loss")
    def serialize(response, **kwargs):
        persistence.heartbeat.assert_owned.side_effect = RuntimeError("lease no longer owned")
        raise error
    monkeypatch.setattr(module.ValidationResponse, "model_dump", serialize)
    with pytest.raises(error_type) as captured:
        game.validate(REQUEST)
    assert captured.value is error
    persistence.mocks["mark_execution_completed"].assert_not_called()
    persistence.mocks["mark_execution_failed"].assert_not_called()
    persistence.heartbeat.stop.assert_called_once()
    persistence.mocks["mark_execution_running"].assert_called_once()
    assert [c.calls for c in checks] == [1, 1]


@pytest.mark.parametrize("cleanup_failure", ["failure_write", "heartbeat_stop"])
def test_final_response_serialization_cleanup_preserves_interruption(monkeypatch, persistence, cleanup_failure):
    base, checks, _ = baseline(True)
    game, _ = game_failure(monkeypatch, base, persist=True)
    error = KeyboardInterrupt("original serialization interruption")
    monkeypatch.setattr(module.ValidationResponse, "model_dump", Mock(side_effect=error))
    if cleanup_failure == "failure_write":
        persistence.mocks["mark_execution_failed"].side_effect = RuntimeError("failure write unavailable")
    else:
        persistence.heartbeat.stop.side_effect = RuntimeError("cleanup unavailable")
    with pytest.raises(KeyboardInterrupt) as captured:
        game.validate(REQUEST)
    assert captured.value is error
    persistence.mocks["mark_execution_completed"].assert_not_called()
    persistence.mocks["mark_execution_failed"].assert_called_once()
    persistence.heartbeat.stop.assert_called_once()
    assert [c.calls for c in checks] == [1, 1]
