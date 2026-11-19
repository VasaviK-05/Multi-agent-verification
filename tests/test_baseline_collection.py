"""Controlled verifier/clock fixtures only; never a live collection command."""
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from app.benchmark.baseline_collection import (
    BaselineCollectionRequest, collect_baseline, measurement_input, main,
)
from app.benchmark.baseline_setup import INITIALIZATION, NAMES, observe_baseline_setup
from app.benchmark.prepare_collection import PreparationInput
from app.game.models import content_id
from app.game.offline.calibration import MeasurementSetup, MeasurementInput
from app.game.resource_provenance import ResourceManifest
from app.selection.capabilities import BUILTIN_CAPABILITIES
from app.selection.verifier_selector import VerifierSelector
from app.selection.baseline_resources import BaselineVerifierSelector
from tests.test_cost_calibration import request as synthetic_request
from tests.test_adaptive_pipeline import offline_pipeline_boundaries
from tests.test_baseline_budget import Checker, clock


@pytest.fixture(autouse=True)
def offline(offline_pipeline_boundaries):
    pass


def request_fixture():
    kinds = ("implementation", "configuration", "model", "corpus", "index", "prompt", "service")
    resources = ResourceManifest(verifiers=tuple(dict(verifier_name=n, resources=[
        dict(kind=k, resource_id=k, sha256="0" * 64) for k in kinds]) for n in NAMES))
    setup = MeasurementSetup(resources=resources, environment={"initialization": INITIALIZATION,
        "host": "SYNTHETIC_FIXTURE"}, dependency_versions={"python": "SYNTHETIC"},
        code_revision="a" * 40, application_source_digest="b" * 64, evidence_kind="synthetic_test_fixture")
    examples = [dict(example_id="example", split_identity="group", question_id="question",
        run_id="run" + str(i), dataset_id="history-v1", role="history", purpose="calibration",
        question="What is 2 + 2?", answer="4", context=reference)
        for i, reference in enumerate((None, "reference"))]
    # Context changes content; separate example and group identities accordingly.
    for i, e in enumerate(examples):
        e.update(example_id="example" + str(i), split_identity="group" + str(i), question_id="question" + str(i))
    prep = PreparationInput(final_test_reservation=synthetic_request()["final_test_reservation"],
        permitted_datasets=(("history", "history-v1"),), preparation_authorization="SYNTHETIC ONLY", examples=tuple(examples))
    return BaselineCollectionRequest(collection_authorized=True, expected_setup=setup, preparation=prep,
                                     index_receipt_path="SYNTHETIC", service_observation_path="SYNTHETIC")


def pool(monkeypatch, clock, error=None):
    import app.selection.verifier_selector as module
    built = []

    def factory(name):
        clock.seconds += 10.  # Simulate expensive construction, never slept.
        built.append(name)
        return Checker(name, clock, duration=2., error=error)

    monkeypatch.setattr(module, "_build_default_verifier", factory)
    return BaselineVerifierSelector(capabilities=BUILTIN_CAPABILITIES), built


def test_actual_selector_exclusion_lazy_construction_and_existing_measurement_export(monkeypatch, clock):
    request = request_fixture()
    selector, built = pool(monkeypatch, clock)
    rows, events = [], []
    collect_baseline(request, selector, lambda: request.expected_setup, rows, events)
    assert len(rows) == 7 and len(built) == 4
    assert len([a for a in rows if a["verifier_name"] == "semantic"]) == 1
    assert any(e["event"] == "excluded" and e["verifier_name"] == "semantic" for e in events)
    assert built == [e["verifier_name"] for e in events if e["event"] == "constructed"]
    assert all(a["duration_ms"] == pytest.approx(2.) for a in rows)
    result = measurement_input(request, rows, events)
    assert MeasurementInput.model_validate_json(result.model_dump_json()) == result
    assert result.setup == request.expected_setup and len(result.attempts) == 7
    assert all(a.verifier_fingerprint == content_id(next(v for v in result.setup.resources.verifiers
        if v.verifier_name == a.verifier_name).model_dump(mode="json")) for a in result.attempts)


@pytest.mark.parametrize("error,status", [(RuntimeError("fixture"), "failure"),
    (TimeoutError("fixture"), "timeout"), (KeyboardInterrupt(), "interrupted")])
def test_collection_retains_original_failure_and_stops_without_retry(monkeypatch, clock, error, status):
    request = request_fixture()
    selector, built = pool(monkeypatch, clock, error)
    rows, events = [], []
    with pytest.raises(type(error)) as raised:
        collect_baseline(request, selector, lambda: request.expected_setup, rows, events)
    assert raised.value is error and len(rows) == 1 and len(built) == 1
    assert rows[0]["status"] == status and rows[0]["duration_ms"] == pytest.approx(2.)
    assert len(measurement_input(request, rows, events).attempts) == 1


def test_observation_drift_never_exports_calibration_eligible_measurements(monkeypatch, clock):
    request = request_fixture()
    selector, _ = pool(monkeypatch, clock)
    changed = request.expected_setup.model_copy(update={"environment": {"host": "changed"}})
    observe = Mock(side_effect=[request.expected_setup, request.expected_setup, changed])
    rows, events = [], []
    with pytest.raises(ValueError, match="setup_changed"):
        collect_baseline(request, selector, observe, rows, events)
    assert len(rows) == 1
    with pytest.raises(ValueError, match="diagnostic_only"):
        measurement_input(request, rows, events)


def test_missing_receipt_fails_before_service_or_model_construction(tmp_path, monkeypatch):
    from app.benchmark import project_adapter
    from app.selection import baseline_resources
    monkeypatch.setattr(baseline_resources, "LOCAL_CONFIGURATION", tmp_path / "no-local-configuration")
    service = Mock(side_effect=AssertionError("no service requests permitted"))
    models = Mock(side_effect=AssertionError("no snapshot/model access needed"))
    monkeypatch.setattr(project_adapter, "observe_service", service)
    monkeypatch.setattr(project_adapter, "directory_digest", models)
    with pytest.raises(ValueError, match="index_build_receipt_unavailable"):
        observe_baseline_setup(index_receipt_path=tmp_path / "absent", service_observation_path=tmp_path / "absent")
    service.assert_not_called()
    models.assert_not_called()


def test_cli_cannot_collect_without_explicit_execute(tmp_path):
    with pytest.raises(SystemExit) as raised:
        main([str(tmp_path / "request"), "--output", str(tmp_path / "out"),
              "--audit-output", str(tmp_path / "audit")])
    assert raised.value.code == 2
    assert list(tmp_path.iterdir()) == []


def test_cli_constructs_reviewed_baseline_selector_without_running_verifiers(tmp_path, monkeypatch):
    import json
    import app.benchmark.baseline_collection as module
    from app.selection import baseline_resources

    # Synthetic CLI wiring fixture; no observer or native collection is executed.
    request = request_fixture()
    setup = request.expected_setup.model_copy(update={"evidence_kind": "empirical"})
    request = request.model_copy(update={"expected_setup": setup})
    source = tmp_path / "request.json"
    source.write_text(request.model_dump_json(), encoding="utf-8")
    monkeypatch.setattr(baseline_resources, "load_baseline_evidence_configuration", lambda: None)
    monkeypatch.setattr(module, "observe_baseline_setup", Mock(side_effect=AssertionError("no live observation")))
    collector = Mock()
    monkeypatch.setattr(module, "collect_baseline", collector)
    assert main([str(source), "--output", str(tmp_path / "measurements.json"),
                 "--audit-output", str(tmp_path / "audit.json"), "--execute"]) == 0
    selector = collector.call_args.args[1]
    assert type(selector) is BaselineVerifierSelector and selector.uses_default_factory
    assert selector.baseline_evidence_configuration is None
    assert (tmp_path / "measurements.json").read_text() == ""
    assert json.loads((tmp_path / "audit.json").read_text())["measurements_exported"] is False
    module.observe_baseline_setup.assert_not_called()


def test_preexisting_default_nli_cache_requires_observed_binding(monkeypatch):
    import app.benchmark.baseline_setup as module
    import app.verifiers.evidence_verifier as evidence
    monkeypatch.setattr(evidence, "default_nli_pipeline", SimpleNamespace(
        cache_info=lambda: SimpleNamespace(currsize=1)))
    monkeypatch.setattr(module, "_nli_binding", None)
    with pytest.raises(ValueError, match="unverified_provenance"):
        module._check_nli_cache("observed")
    monkeypatch.setattr(module, "_nli_binding", "observed")
    module._check_nli_cache("observed")
    with pytest.raises(ValueError):
        module._check_nli_cache("changed")
