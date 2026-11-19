"""Fresh artifact integration with recorded observation and fake runtime clocks.

These tests never perform a new setup observation or live verifier call. Local
campaign evidence is optional in other checkouts; it must validate when present.
"""
from dataclasses import FrozenInstanceError, replace
import hashlib
import json
from pathlib import Path
from unittest.mock import Mock

import pytest

from app.analysis.question_analyzer import QuestionAnalysis, QuestionAnalyzer
from app.benchmark.baseline_collection import BaselineCollectionRequest
from app.game.offline.calibration import CalibrationArtifact, MeasurementSetup
from app.models.schemas import ValidationRequest
from app.orchestration.validation_orchestrator import ValidationOrchestrator
from app.selection.baseline_budget import (
    BudgetLedger, capture_baseline_budget_configuration, plan_with_budget,
    validate_baseline_calibration,
)
from app.selection.capabilities import BUILTIN_CAPABILITIES
from app.selection.baseline_resources import BaselineVerifierSelector
from tests.test_adaptive_pipeline import FixedAnalyzer, offline_pipeline_boundaries
from tests.test_baseline_budget import Checker, clock


CAMPAIGN = Path(__file__).resolve().parents[1] / "build/baseline-development-20261118T172504Z-3f872bd0"
CALIBRATION_ID = "638db686358e8e905c9f2f00abd06f1bb98174e5700996f57ab371539d9882ea"
INPUT_DIGEST = "3a0162a7e3712b67aa76e5e834abcdece77f36324d328605f409c8cf0435c2f3"
SETUP_ID = "a5205440b39757b3eb0116fbe48a8356e729c6d9ac08398fb48529648ccebd88"
ARTIFACT_SHA = "219ad4b9a9783a55bfc209905f0e2d56566f585fb6287e10b6e2d2ad7248e848"


@pytest.fixture(autouse=True)
def offline(monkeypatch, offline_pipeline_boundaries):
    import app.selection.verifier_selector as selector_module
    from app.utils.config import settings

    monkeypatch.setattr(settings, "BASELINE_BUDGET_CONFIG_PATH", "")
    monkeypatch.setattr(selector_module, "_build_default_verifier",
                        Mock(side_effect=AssertionError("no real verifier construction")))


@pytest.fixture(scope="module")
def evidence():
    if not (CAMPAIGN / "calibration.json").is_file():
        pytest.skip("local fresh Development campaign evidence is not distributed")
    raw = (CAMPAIGN / "calibration.json").read_bytes()
    assert hashlib.sha256(raw).hexdigest() == ARTIFACT_SHA
    artifact = CalibrationArtifact.model_validate_json(raw)
    # Separate, previously captured observation, not an artifact-supplied oracle.
    readiness = json.loads((CAMPAIGN / "readiness-approved.json").read_text())
    observed = MeasurementSetup.model_validate(readiness["actual_setup"])
    assert artifact.calibration_id == CALIBRATION_ID
    assert artifact.input_digest == INPUT_DIGEST
    assert observed.fingerprint == SETUP_ID
    assert artifact.method == "mean_attempt_wall_time_ms_v1" and artifact.cost_units == "ms"
    assert len(artifact.request.measurements.attempts) == 427
    assert artifact.request.include_warmups is False
    assert len(artifact.result["exclusions"]) == 7
    assert dict(validate_baseline_calibration(artifact, observed))
    request = BaselineCollectionRequest.model_validate_json((CAMPAIGN / "collection-request.json").read_bytes())
    return artifact, observed, request


@pytest.fixture
def server(tmp_path, monkeypatch, evidence):
    from app.benchmark import baseline_setup
    from app.selection.baseline_resources import load_baseline_evidence_configuration
    from app.utils.config import settings

    artifact, observed, request = evidence
    config = dict(version="baseline_budget_configuration_v1",
                  levels_ms={"low": 100., "medium": 1000., "high": 30000.}, active_level="high",
                  calibration_path=str(CAMPAIGN / "calibration.json"),
                  index_receipt_path=request.index_receipt_path,
                  service_observation_path=request.service_observation_path)
    path = tmp_path / "server-budget.json"
    path.write_text(json.dumps(config), encoding="utf-8")
    monkeypatch.setattr(settings, "BASELINE_BUDGET_CONFIG_PATH", str(path))
    # Recorded-setup simulation only: this is not an observation of repaired source.
    observer = Mock(return_value=observed)
    monkeypatch.setattr(baseline_setup, "observe_baseline_setup", observer)
    selector = BaselineVerifierSelector(capabilities=BUILTIN_CAPABILITIES)
    selector.configure_baseline_evidence(load_baseline_evidence_configuration())
    return path, config, selector, observer


def test_fresh_artifact_contract_and_frozen_identity(evidence):
    artifact, observed, _ = evidence
    assert artifact.request.measurements.setup == observed
    assert artifact.request.measurements.setup.evidence_kind == "empirical"
    assert observed.environment["torch_num_threads"] == "1"
    assert observed.environment["torch_num_interop_threads"] == "1"


def test_historical_campaign_cannot_activate_against_repaired_source(server, evidence):
    from app.benchmark.project_adapter import file_digest
    from app.game.models import content_id

    _, recorded, _ = evidence
    root = Path(__file__).resolve().parents[1]
    current_digest = content_id([(p.relative_to(root).as_posix(), file_digest(p))
                                 for p in sorted((root / "app").rglob("*.py"))])
    assert current_digest != recorded.application_source_digest
    observed = recorded.model_copy(update={"application_source_digest": current_digest})
    with pytest.raises(ValueError, match="setup_mismatch"):
        validate_baseline_calibration(evidence[0], observed)
    _, _, selector, observer = server
    observer.return_value = observed
    snapshot = capture_baseline_budget_configuration(selector)
    assert snapshot.status == "unconfigured"
    assert snapshot.reason == "baseline_budget_compatibility_unavailable_or_invalid"
    assert snapshot.costs == () and snapshot.limit_ms is None


@pytest.mark.parametrize("level,limit,feasible_count", [("low", 100., 0), ("medium", 1000., 60), ("high", 30000., 120)])
def test_real_config_loader_and_roster_admission(server, evidence, level, limit, feasible_count):
    path, config, selector, observer = server
    config["active_level"] = level
    path.write_text(json.dumps(config), encoding="utf-8")
    snap = capture_baseline_budget_configuration(selector)
    assert snap.status == "configured" and snap.limit_ms == limit and snap.level == level
    assert snap.calibration_id == CALIBRATION_ID and snap.calibration_sha256 == ARTIFACT_SHA
    assert snap.setup_fingerprint == SETUP_ID
    observer.assert_called_once()
    analyzer = QuestionAnalyzer(mode="heuristic")
    admitted = 0
    for example in evidence[2].preparation.examples:
        if example.purpose == "warmup":
            continue
        plan = selector.plan(analyzer.analyze(example.question), example.context)
        result = plan_with_budget(plan, snap)
        if not example.context:
            assert not next(c for c in plan.candidates if c.verifier_name == "semantic").eligible
            assert "semantic" not in result.initial_selected + result.fallback
        if result.feasible:
            admitted += 1
            assert len(result.initial_selected) >= plan.minimum_count
            assert result.estimated_initial_ms == pytest.approx(sum(dict(snap.costs)[n] for n in result.initial_selected))
            assert result.estimated_initial_ms <= limit
            ranked = plan.initial_selected + plan.fallback
            assert tuple(sorted(result.initial_selected, key=ranked.index)) == result.initial_selected
            coverage = set().union(*(set(c.expected_capabilities) for c in plan.candidates if c.verifier_name in result.initial_selected))
            assert set(plan.requirements.requirements) <= coverage
            if level == "medium":
                assert result.initial_selected == ("rule", "semantic")
        else:
            assert result.initial_selected == () and result.fallback == ()
    assert admitted == feasible_count


def test_server_snapshot_cannot_change_during_request(server):
    path, config, selector, _ = server
    snap = capture_baseline_budget_configuration(selector)
    config["active_level"] = "low"
    path.write_text(json.dumps(config), encoding="utf-8")
    assert snap.limit_ms == 30000.
    assert capture_baseline_budget_configuration(selector).limit_ms == 100.
    with pytest.raises(FrozenInstanceError):
        snap.limit_ms = 100.


@pytest.mark.parametrize("field", ["source", "revision", "threads", "dependencies", "model", "corpus", "index"])
def test_incompatible_independent_observation_fails_unconfigured(server, evidence, field):
    _, _, selector, observer = server
    data = evidence[1].model_dump(mode="json")
    if field == "source":
        data["application_source_digest"] = "0" * 64
    elif field == "revision":
        data["code_revision"] = "0" * 40
    elif field == "threads":
        data["environment"]["torch_num_threads"] = "2"
    elif field == "dependencies":
        data["dependency_versions"]["torch"] = "different"
    else:
        resource = next(row for v in data["resources"]["verifiers"] for row in v["resources"] if row["kind"] == field)
        # Shared models appear in several verifier rows. Change the complete
        # shared identity so the observation remains structurally valid.
        identity = resource["resource_id"]
        for verifier in data["resources"]["verifiers"]:
            for row in verifier["resources"]:
                if row["resource_id"] == identity:
                    row["sha256"] = "0" * 64
    observer.return_value = MeasurementSetup.model_validate(data)
    snap = capture_baseline_budget_configuration(selector)
    assert snap.status == "unconfigured"
    assert snap.reason == "baseline_budget_compatibility_unavailable_or_invalid"
    assert snap.costs == () and snap.limit_ms is None


@pytest.mark.parametrize("problem", ["missing", "malformed", "tampered"])
def test_unusable_artifact_is_not_an_admission_cost(server, tmp_path, problem):
    path, config, selector, observer = server
    artifact = tmp_path / "invalid.json"
    if problem == "malformed":
        artifact.write_text("not JSON", encoding="utf-8")
    elif problem == "tampered":
        data = json.loads((CAMPAIGN / "calibration.json").read_text())
        data["result"]["estimates"][0]["attempt_cost"] = 0.
        artifact.write_text(json.dumps(data), encoding="utf-8")
    config["calibration_path"] = str(artifact)
    path.write_text(json.dumps(config), encoding="utf-8")
    snap = capture_baseline_budget_configuration(selector)
    assert snap.status == "unconfigured" and snap.costs == ()
    assert snap.reason == "baseline_budget_calibration_unavailable_or_invalid"
    observer.assert_not_called()


@pytest.mark.parametrize("limit,expected_calls,actual,exceeded", [(100., [], 0., False), (30000., ["evidence", "rule"], 28000., False), (30000., ["evidence"], 31000., True)])
def test_runtime_uses_empirical_config_and_blocks_dispatch(server, clock, monkeypatch, limit, expected_calls, actual, exceeded):
    path, config, selector, observer = server
    config["active_level"] = "low" if limit == 100. else "high"
    path.write_text(json.dumps(config), encoding="utf-8")
    durations = {"rule": 18000., "evidence": 31000. if actual == 31000. else 10000., "confidence": 1000.}
    calls = []
    def resolve(name):
        calls.append(name)
        # Simulated construction time must never enter the attempt ledger.
        clock.seconds += 99.
        return Checker(name, clock, duration=durations[name])
    monkeypatch.setattr(selector, "resolve", resolve)
    run = ValidationOrchestrator(question_analyzer=FixedAnalyzer(QuestionAnalysis(
        "general", "hard", .9, verification_types=["direct_fact"])), verifier_selector=selector)
    result = run.validate(ValidationRequest(question="offline fixture", answer="unchanged answer"))
    observer.assert_called_once()
    assert calls == expected_calls
    audit = result.execution_audit["baseline_budget"]
    assert audit["calibration_id"] == CALIBRATION_ID and audit["setup_fingerprint"] == SETUP_ID
    assert audit["actual_attempt_ms"] == pytest.approx(actual)
    assert audit["remaining_ms"] == pytest.approx(max(0., limit - actual))
    assert audit["actual_limit_exceeded"] == exceeded and audit["preemption_supported"] is False
    assert result.early_stop_reason == ("budget_planning_infeasible" if limit == 100. else "actual_budget_exhaustion")
    if actual:
        assert audit["attempts"][0]["estimate_overrun"] is True
        assert audit["skipped"]
        assert audit["skipped"][0]["reason"] == (
            "actual_budget_exhausted" if exceeded else "remaining_budget_insufficient")


@pytest.mark.parametrize("error,status,duration", [(RuntimeError("offline"), "failure", 500.), (TimeoutError("offline"), "timeout", 1000.), (KeyboardInterrupt(), "interrupted", 1500.)])
def test_empirical_ledger_charges_exception_duration(server, clock, error, status, duration):
    _, _, selector, _ = server
    snap = replace(capture_baseline_budget_configuration(selector), limit_ms=1000.)
    ledger = BudgetLedger(snap, "offline-exception-fixture")
    assert ledger.admit("rule")
    with pytest.raises(type(error)) as raised:
        ledger.verify(Checker("rule", clock, duration=duration, error=error), "q", "a", None)
    assert raised.value is error
    assert ledger.actual_ms == pytest.approx(duration)
    assert ledger.attempts[0]["status"] == status
    assert ledger.remaining_ms == pytest.approx(max(0., 1000. - duration))
    assert not ledger.admit("evidence")


def test_unknown_cost_cannot_dispatch_with_empirical_snapshot(server):
    _, _, selector, _ = server
    ledger = BudgetLedger(capture_baseline_budget_configuration(selector), "offline-unknown")
    assert not ledger.admit("unregistered-verifier")
    assert ledger.skipped[0]["reason"] == "unknown_empirical_cost"
