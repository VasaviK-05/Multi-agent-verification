"""Synthetic offline budget tests; no empirical calibration or provider execution."""
from dataclasses import replace, FrozenInstanceError
import json
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from app.selection.baseline_budget import (
    BaselineBudgetSnapshot, BudgetLedger, capture_baseline_budget_configuration,
    plan_with_budget, validate_baseline_calibration,
)
from app.selection.verifier_selector import VerifierSelector
from app.selection.baseline_resources import BaselineVerifierSelector
from app.selection.capabilities import CapabilityDescriptor
from app.models.schemas import ValidationRequest
from app.selection.models import VerifierUnavailable
from app.orchestration.validation_orchestrator import ValidationOrchestrator
from app.analysis.question_analyzer import QuestionAnalysis
from app.game.offline.calibration import calibrate
from tests.test_cost_calibration import request as synthetic_request
from tests.test_adaptive_pipeline import (
    offline_pipeline_boundaries, MetadataChecker, FixedAnalyzer, factual_metadata,
)


@pytest.fixture(autouse=True)
def offline(monkeypatch, offline_pipeline_boundaries):
    from app.utils.config import settings
    monkeypatch.setattr(settings, "BASELINE_BUDGET_CONFIG_PATH", "")


@pytest.fixture
def clock(monkeypatch):
    from app.game.offline import timing
    value = SimpleNamespace(seconds=0.)
    monkeypatch.setattr(timing, "time", SimpleNamespace(perf_counter=lambda: value.seconds))
    return value


class Checker(MetadataChecker):
    def __init__(self, name, clock, duration=1., error=None):
        super().__init__(name, score=1., metadata=factual_metadata())
        self.clock, self.duration, self.error = clock, duration, error

    def verify(self, *args):
        self.clock.seconds += self.duration / 1000
        if self.error is not None:
            self.calls += 1
            raise self.error
        return super().verify(*args)


def snapshot(names, budget, cost=1.):
    return BaselineBudgetSnapshot(status="configured", reason="SYNTHETIC_TEST_ONLY",
        limit_ms=budget, costs=tuple((n, cost) for n in names), calibration_id="SYNTHETIC")


def pipeline(checkers, provider, hard=False, **kwargs):
    selector = VerifierSelector(verifiers=checkers, lambda_cost=0, lambda_latency=0,
        lambda_suitability=0, capabilities={c.name: CapabilityDescriptor(("direct_fact",)) for c in checkers})
    return ValidationOrchestrator(question_analyzer=FixedAnalyzer(QuestionAnalysis(
        "general", "hard" if hard else "easy", .9 if hard else .1, verification_types=["direct_fact"])),
        verifier_selector=selector, baseline_budget_provider=provider, **kwargs)


def test_unconfigured_preserves_execution_and_reports_reason(clock):
    checkers = [Checker(n, clock) for n in ("a", "b", "later")]
    result = pipeline(checkers, lambda _: BaselineBudgetSnapshot()).validate(ValidationRequest(question="q", answer="a"))
    assert result.selected_verifiers == ["a", "b"] and checkers[-1].calls == 0
    assert result.final_status == "passed" and result.early_stop_reason == "approved_early_stop"
    audit = result.execution_audit["baseline_budget"]
    assert audit["status"] == "unconfigured" and audit["remaining_ms"] is None
    assert audit["reason"] == "baseline_budget_configuration_absent"


@pytest.mark.parametrize("budget,count,reason", [(1., 0, "budget_planning_infeasible"),
    (2., 2, "approved_early_stop"), (10., 2, "approved_early_stop")])
def test_explicit_budget_levels_admit_only_feasible_teams(clock, budget, count, reason):
    checkers = [Checker(n, clock) for n in ("a", "b", "later")]
    s = snapshot([c.name for c in checkers], budget)
    result = pipeline(checkers, lambda _: s).validate(ValidationRequest(question="q", answer="a"))
    assert sum(c.calls for c in checkers) == count
    assert result.early_stop_reason == reason
    assert result.execution_audit["baseline_budget"]["calibration_id"] == "SYNTHETIC"
    if not count:
        assert result.final_status == "uncertain"


def test_actual_time_exhaustion_blocks_remaining_dispatch_and_records_overrun(clock):
    checkers = [Checker(n, clock, duration=4.) for n in ("a", "b", "c")]
    s = snapshot([c.name for c in checkers], 6., cost=2.)
    result = pipeline(checkers, lambda _: s, hard=True).validate(ValidationRequest(question="q", answer="a"))
    assert [c.calls for c in checkers] == [1, 1, 0]
    assert result.early_stop_reason == "actual_budget_exhaustion" and result.final_status == "uncertain"
    audit = result.execution_audit["baseline_budget"]
    assert audit["actual_attempt_ms"] == pytest.approx(8.) and audit["remaining_ms"] == 0
    assert audit["actual_limit_exceeded"] and not audit["preemption_supported"]
    assert all(a["estimate_overrun"] for a in audit["attempts"])
    assert audit["skipped"][0]["verifier_name"] == "c"
    assert result.execution_audit["runtime_availability"]["c"] == "budget_not_admitted"


@pytest.mark.parametrize("error,status", [(RuntimeError("fixture"), "failure"),
    (TimeoutError("fixture"), "timeout"), (KeyboardInterrupt(), "interrupted")])
def test_exception_time_is_charged_and_original_exception_survives(clock, error, status):
    ledger = BudgetLedger(snapshot(("a",), 2.), "execution")
    with pytest.raises(type(error)) as raised:
        ledger.verify(Checker("a", clock, duration=3., error=error), "q", "a", None)
    assert raised.value is error
    assert ledger.actual_ms == pytest.approx(3.)
    assert ledger.attempts[0]["status"] == status
    assert not ledger.admit("a")


@pytest.mark.parametrize("cost", [None, -1., float("nan"), float("inf"), True, "1"])
def test_unknown_or_invalid_cost_never_bypasses_admission(clock, cost):
    run = pipeline([Checker(n, clock) for n in ("a", "b")], lambda _: BaselineBudgetSnapshot())
    plan = run.verifier_selector.plan(run._question_analyzer.analysis)
    s = replace(snapshot(("a", "b"), 10.), costs=(("a", 1.), ("b", cost)))
    assert not plan_with_budget(plan, s).feasible
    assert not BudgetLedger(s, "execution").admit("b")


def test_configuration_captured_once_before_analysis_and_cannot_mutate(clock):
    checkers = [Checker(n, clock) for n in ("a", "b")]
    s = snapshot(("a", "b"), 2.)
    provider = Mock(return_value=s)
    run = pipeline(checkers, provider)
    original = run._question_analyzer.analyze

    def analyze(question):
        provider.assert_called_once()
        provider.return_value = snapshot(("a", "b"), 0.)
        return original(question)

    run._question_analyzer.analyze = analyze
    result = run.validate(ValidationRequest(question="q", answer="a"))
    assert result.final_status == "passed"
    assert result.execution_audit["baseline_budget"]["limit_ms"] == 2.
    with pytest.raises(FrozenInstanceError):
        s.limit_ms = 0.


def test_lower_priority_team_can_fit_without_weakening_minimum_or_coverage(clock):
    run = pipeline([Checker(n, clock) for n in ("expensive", "cheap", "fallback")], lambda _: BaselineBudgetSnapshot())
    plan = run.verifier_selector.plan(run._question_analyzer.analysis)
    s = replace(snapshot(("expensive", "cheap", "fallback"), 2.), costs=(("expensive", 9.), ("cheap", 1.), ("fallback", 1.)))
    admitted = plan_with_budget(plan, s)
    assert admitted.initial_selected == ("cheap", "fallback")
    assert admitted.fallback == ("expensive",) and admitted.estimated_initial_ms == 2.


def test_setup_validation_recomputes_identity_and_rejects_changed_environment():
    a = calibrate(synthetic_request())  # In-memory synthetic fixture, never empirical output.
    setup = a.request.measurements.setup
    assert dict(validate_baseline_calibration(a, setup)) == {"a": 2., "b": 2.}
    with pytest.raises(ValueError, match="setup_mismatch"):
        validate_baseline_calibration(a, setup.model_copy(update={"environment": {"host": "different"}}))
    data = a.model_dump(mode="json")
    data["result"]["estimates"][0]["attempt_cost"] = 0.
    with pytest.raises(ValueError):
        validate_baseline_calibration(data, setup)


@pytest.mark.parametrize("levels,active", [({}, "small"), ({"small": -1}, "small"),
    ({"small": True}, "small"), ({"small": 2}, "missing")])
def test_invalid_server_levels_fail_unconfigured(tmp_path, monkeypatch, levels, active):
    from app.utils.config import settings
    path = tmp_path / "server.json"
    path.write_text(json.dumps(dict(version="baseline_budget_configuration_v1", levels_ms=levels,
        active_level=active, calibration_path="missing", index_receipt_path="missing",
        service_observation_path="missing")), encoding="utf-8")
    monkeypatch.setattr(settings, "BASELINE_BUDGET_CONFIG_PATH", str(path))
    result = capture_baseline_budget_configuration(VerifierSelector(verifiers=[]))
    assert result.status == "unconfigured" and "configuration" in result.reason


def test_historical_calibration_cannot_activate_or_contact_observer(tmp_path, monkeypatch):
    from app.utils.config import settings
    import app.benchmark.baseline_setup as module
    artifact = str(__import__('pathlib').Path('artifacts/research-v1-development-cost-calibration-v1/calibration.json').resolve())
    path = tmp_path / "server.json"
    path.write_text(json.dumps(dict(version="baseline_budget_configuration_v1", levels_ms={"small": 2.},
        active_level="small", calibration_path=artifact, index_receipt_path="missing",
        service_observation_path="missing")), encoding="utf-8")
    monkeypatch.setattr(settings, "BASELINE_BUDGET_CONFIG_PATH", str(path))
    observer = Mock(side_effect=AssertionError("historical costs must not trigger observations"))
    monkeypatch.setattr(module, "observe_baseline_setup", observer)
    s = capture_baseline_budget_configuration(BaselineVerifierSelector())
    assert s.status == "unconfigured" and s.reason == "calibration_not_baseline_empirical"
    observer.assert_not_called()


@pytest.mark.parametrize("error,status", [(TimeoutError("offline"), "timeout"),
    (RuntimeError("offline"), "failure"), (KeyboardInterrupt(), "interrupted")])
def test_failed_runtime_journal_receives_attempt_metrics_and_budget(clock, monkeypatch, error, status):
    import app.orchestration.validation_orchestrator as module
    conn = SimpleNamespace(commit=Mock(), rollback=Mock(), close=Mock())
    monkeypatch.setattr(module, "get_connection", lambda: conn)
    for n in ("create_validation_record", "begin_validation", "mark_execution_ready", "mark_verifier_attempt_started"):
        monkeypatch.setattr(module, n, Mock())
    monkeypatch.setattr(module, "mark_execution_running", lambda **kw: {"lease_token": "lease"})
    monkeypatch.setattr(module, "create_verifier_attempt", lambda **kw: {"attempt_id": kw["verifier_name"]})
    heartbeat = SimpleNamespace(assert_owned=Mock())
    heartbeat.start = lambda: heartbeat
    monkeypatch.setattr(module, "ExecutionLeaseHeartbeat", lambda **kw: heartbeat)
    failed, attempt = Mock(), Mock()
    monkeypatch.setattr(module, "mark_execution_failed", failed)
    monkeypatch.setattr(module, "mark_verifier_attempt_error", attempt)
    checkers = [Checker("a", clock, duration=3., error=error), Checker("b", clock)]
    with pytest.raises(type(error)) as raised:
        pipeline(checkers, lambda _: snapshot(("a", "b"), 5.), persist_execution=True).validate(
            ValidationRequest(question="q", answer="a"))
    assert raised.value is error and checkers[1].calls == 0
    assert attempt.call_args.kwargs["duration_ms"] == pytest.approx(3.)
    assert attempt.call_args.kwargs["cost_units"] == "ms"
    audit = failed.call_args.kwargs["failure_details"]["baseline_budget"]
    assert audit["attempts"][0]["status"] == status
    assert audit["remaining_ms"] == pytest.approx(2.)


def test_unavailable_attempt_consumes_time_then_admits_fallback(clock):
    checkers = [Checker("offline", clock, error=VerifierUnavailable("maintenance")),
                Checker("b", clock), Checker("fallback", clock)]
    result = pipeline(checkers, lambda _: snapshot(("offline", "b", "fallback"), 3.)).validate(
        ValidationRequest(question="q", answer="a"))
    assert [c.calls for c in checkers] == [1, 1, 1]
    assert result.selected_verifiers == ["b", "fallback"] and result.final_status == "passed"
    audit = result.execution_audit
    assert audit["attempted_verifiers"] == ["offline", "b", "fallback"]
    assert audit["unavailable_verifiers"] == [{"verifier": "offline", "reason": "maintenance"}]
    assert audit["baseline_budget"]["actual_attempt_ms"] == pytest.approx(3.)


@pytest.fixture
def mocked_server_configuration(tmp_path, monkeypatch):
    """Test server plumbing, not empirical evidence: artifact loader/observer mocked.

    Real identity/compatibility rejection is tested separately above. The bytes
    here deliberately are NOT a calibration artifact and never leave tmp_path.
    """
    from app.utils.config import settings
    import app.selection.baseline_budget as module
    import app.benchmark.baseline_setup as setup_module
    artifact_path = tmp_path / "not-an-artifact.fixture"
    artifact_path.write_bytes(b"mock loader input only")
    config = dict(version="baseline_budget_configuration_v1", levels_ms={"small": 2., "large": 10.},
        active_level="small", calibration_path=artifact_path.name, index_receipt_path="fixture",
        service_observation_path="fixture")
    path = tmp_path / "server.json"
    path.write_text(json.dumps(config), encoding="utf-8")
    monkeypatch.setattr(settings, "BASELINE_BUDGET_CONFIG_PATH", str(path))
    setup = SimpleNamespace(evidence_kind="empirical", environment={"initialization": setup_module.INITIALIZATION},
        fingerprint="f" * 64, resources=SimpleNamespace(require_candidates=Mock()))
    artifact = SimpleNamespace(request=SimpleNamespace(measurements=SimpleNamespace(setup=setup)),
                               calibration_id="MOCK_ONLY")
    monkeypatch.setattr(module.CalibrationArtifact, "model_validate_json", lambda raw: artifact)
    observer = Mock(return_value=setup)
    monkeypatch.setattr(setup_module, "observe_baseline_setup", observer)
    validator = Mock(return_value=tuple((n, 1.) for n in setup_module.NAMES))
    monkeypatch.setattr(module, "validate_baseline_calibration", validator)
    return SimpleNamespace(path=path, config=config, observer=observer, validator=validator)


def test_server_levels_reuse_immutable_calibration_reference(mocked_server_configuration):
    fixture = mocked_server_configuration
    first = capture_baseline_budget_configuration(BaselineVerifierSelector())
    fixture.config["active_level"] = "large"
    fixture.path.write_text(json.dumps(fixture.config), encoding="utf-8")
    second = capture_baseline_budget_configuration(BaselineVerifierSelector())
    assert first.status == second.status == "configured"
    assert (first.limit_ms, second.limit_ms) == (2., 10.)
    assert first.calibration_id == second.calibration_id == "MOCK_ONLY"
    assert first.calibration_sha256 == second.calibration_sha256
    assert first.configuration_id != second.configuration_id
    assert first.level == "small" and second.level == "large"
    assert fixture.observer.call_count == fixture.validator.call_count == 2


@pytest.mark.parametrize("kind", ["shared", "injected", "unreviewed_subclass"])
def test_only_reviewed_default_baseline_factory_can_bind_empirical_setup(mocked_server_configuration, kind):
    class UnreviewedSelector(BaselineVerifierSelector):
        pass
    selector = {"shared": lambda: VerifierSelector(),
                "injected": lambda: BaselineVerifierSelector(verifiers=[]),
                "unreviewed_subclass": lambda: UnreviewedSelector()}[kind]()
    result = capture_baseline_budget_configuration(selector)
    assert result.status == "unconfigured"
    assert result.reason == "baseline_custom_factory_not_reviewed"
    mocked_server_configuration.observer.assert_not_called()
    mocked_server_configuration.validator.assert_not_called()


def test_independent_observation_failure_is_unconfigured(mocked_server_configuration):
    fixture = mocked_server_configuration
    fixture.observer.side_effect = ValueError("private filesystem details must not escape")
    result = capture_baseline_budget_configuration(BaselineVerifierSelector())
    assert result.status == "unconfigured"
    assert result.reason == "baseline_budget_setup_observation_unavailable_or_invalid"
    fixture.validator.assert_not_called()


def test_preexisting_unobserved_instances_cannot_be_rebound(monkeypatch, clock):
    from app.selection import verifier_selector as module
    selector = BaselineVerifierSelector()
    monkeypatch.setattr(module, "_build_default_verifier", lambda name: Checker(name, clock))
    selector.resolve("rule")
    with pytest.raises(ValueError, match="unverified setup"):
        selector.bind_baseline_setup("new")
    fresh = BaselineVerifierSelector()
    fresh.bind_baseline_setup("observed")
    fresh.resolve("rule")
    fresh.bind_baseline_setup("observed")
    with pytest.raises(ValueError):
        fresh.bind_baseline_setup("changed")


def test_api_records_budget_and_ignores_client_budget(clock, monkeypatch, offline_pipeline_boundaries):
    from fastapi.testclient import TestClient
    from app.services.validation_service import ValidationService
    boundary = offline_pipeline_boundaries
    checkers = [Checker(n, clock) for n in ("a", "b", "later")]
    provider = Mock(return_value=snapshot(("a", "b", "later"), 2.))
    run = pipeline(checkers, provider)
    monkeypatch.setattr(boundary.routes, "_validation_service", ValidationService(run))
    with TestClient(boundary.app) as client:
        response = client.post("/validate", json={"question": "q", "answer": "a", "budget_ms": 0})
    assert response.status_code == 200
    data = response.json()
    audit = data["execution_audit"]["baseline_budget"]
    assert audit["limit_ms"] == 2. and audit["actual_attempt_ms"] == pytest.approx(2.)
    assert data["final_status"] == "passed" and checkers[-1].calls == 0
    provider.assert_called_once()
    persisted = boundary.persistence["update_audit"].call_args.kwargs["run_summary"]
    assert persisted["baseline_budget"] == audit


def test_game_never_reads_baseline_budget_and_preserves_frozen_execution():
    from tests.test_game_runtime import runtime_fixture
    run, checkers, manager, rng = runtime_fixture()
    provider = Mock(side_effect=AssertionError("Game must never consult baseline budgeting"))
    run._baseline_budget_provider = provider
    before = run._game_runtime.episode.context.model_dump_json()
    result = run.validate(ValidationRequest(question="fixture question", answer="fixture answer"))
    provider.assert_not_called()
    assert [c.calls for c in checkers] == [1, 1, 0]
    assert result.final_status == "passed" and rng.calls == 1
    assert result.execution_audit["termination"] == "complete_selected_team"
    assert "baseline_budget" not in result.execution_audit
    assert run._game_runtime.episode.context.model_dump_json() == before
