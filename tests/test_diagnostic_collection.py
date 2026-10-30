"""Synthetic diagnostics: no claims of labels, custody approval or calibrated costs."""
import pytest
import io
import sys
from types import SimpleNamespace

from tests.test_game_collection import fixture
from app.game.offline.collection import (DiagnosticRecordingRequest, RecordingRequest,
    RecordingBundle, collect, completeness, measurement_input, export_training)


def diagnostic():
    request, pool, setup, observer, context, attacks = fixture()
    data = request.model_dump(mode='json')
    data.update(version='offline_diagnostic_recording_v1', intended_use='smoke',
        study_approval=None, cache_contract='diagnostic_observation_only')
    data['final_test_reservation'].pop('custody_record')
    data['final_test_reservation']['version'] = 'diagnostic_exclusion_roster_v1'
    for example in data['examples']:
        example['label'] = None
    return DiagnosticRecordingRequest.model_validate(data), pool, setup, observer, context


def test_diagnostic_same_collection_without_label_or_custody_claims():
    request, pool, setup, observer, context = diagnostic()
    bundle = collect(request, pool, setup, observer)
    assert completeness(bundle)['executed_calls'] == 4
    assert all(a.measurement is not None and a.attempt.report is not None for a in bundle.attempts)
    assert all(e.label is None for e in bundle.request.examples)
    assert 'custody_record' not in bundle.request.final_test_reservation.model_dump()
    restored = RecordingBundle.model_validate_json(bundle.model_dump_json())
    assert isinstance(restored.request, DiagnosticRecordingRequest)
    with pytest.raises(ValueError, match='diagnostic-only'):
        measurement_input(restored)
    with pytest.raises(ValueError, match='smoke'):
        export_training(restored, context)


def test_study_contract_not_weakened_and_final_exclusion_retained():
    request, pool, setup, observer, context = diagnostic()
    data = request.model_dump(mode='json')
    with pytest.raises(ValueError):
        RecordingRequest.model_validate(data)
    data['examples'][0]['split_identity'] = data['final_test_reservation']['examples'][0]['split_identity']
    with pytest.raises(ValueError, match='final-test'):
        DiagnosticRecordingRequest.model_validate(data)


def test_diagnostic_cannot_supply_labels_or_study_approval():
    request, *_ = diagnostic()
    data = request.model_dump(mode='json')
    data['study_approval'] = 'pretend approved'
    with pytest.raises(ValueError):
        DiagnosticRecordingRequest.model_validate(data)
    data['study_approval'] = None
    data['examples'][0]['label'] = dict(answer_is_correct=True)
    with pytest.raises(ValueError):
        DiagnosticRecordingRequest.model_validate(data)


def test_network_limits_and_external_denial_without_actual_network():
    from scripts.run_factual_diagnostic import NetworkBudget
    audit = io.StringIO()
    budget = NetworkBudget('http://localhost:11434/api/generate', audit)
    calls = []
    def original(session, method, url, **kw):
        assert kw.get("allow_redirects") is False
        calls.append((method, url))
        return SimpleNamespace(status_code=200)
    for _ in range(30):
        budget.call(original, None, 'POST', 'http://localhost:11434/api/generate')
    with pytest.raises(RuntimeError, match='authorization'):
        budget.call(original, None, 'POST', 'http://localhost:11434/api/generate')
    for _ in range(100):
        budget.call(original, None, 'GET', 'http://localhost:11434/api/tags')
    with pytest.raises(RuntimeError):
        budget.call(original, None, 'GET', 'http://localhost:11434/api/version')
    with pytest.raises(RuntimeError):
        budget.call(original, None, 'POST', 'https://example.org/paid')
    assert len(calls) == 130
    assert budget.counts == dict(generation=30, metadata=100, blocked=3)


def test_existing_cli_diagnostic_collect_check_and_export_guard(tmp_path, monkeypatch):
    from app.game.offline.collect import main, load_bundle
    request, pool, setup, observer, context = diagnostic()
    data = request.model_dump(mode='json')
    data['factory'] = 'synthetic_diagnostic_factory:create'
    monkeypatch.setitem(sys.modules, 'synthetic_diagnostic_factory', SimpleNamespace(create=lambda: (pool, setup, observer)))
    import json
    path = tmp_path / 'request.json'
    path.write_text(json.dumps(data))
    output = tmp_path / 'recording'
    assert main(['validate', str(path)]) == 0
    assert main(['collect', str(path), '--output-dir', str(output)]) == 0
    assert main(['check', str(output)]) == 0
    assert isinstance(load_bundle(output).request, DiagnosticRecordingRequest)
    assert not (output / 'measurements.json').exists()
    report = json.loads((output / 'collection-report.json').read_text())
    assert 'diagnostic-only' in report['measurement_export_blocker']


@pytest.mark.parametrize('url', ['https://example.org/api/generate',
    'http://user:password@localhost:11434/api/generate', 'http://localhost:11434/api/generate?token=fixture'])
def test_network_budget_rejects_nonlocal_or_credentialed_configuration(url):
    from scripts.run_factual_diagnostic import NetworkBudget
    with pytest.raises(ValueError, match='loopback'):
        NetworkBudget(url, io.StringIO())
