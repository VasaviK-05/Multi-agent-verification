"""Synthetic diagnostics: no claims of labels, custody approval or calibrated costs."""
import pytest
import io
import json
import sys
from dataclasses import asdict
from types import SimpleNamespace

from tests.test_game_collection import fixture
from app.game.offline.collection import (DiagnosticRecordingRequest, RecordingRequest,
    Experiment4DiagnosticRecordingRequest, Experiment4DiagnosticAttemptMeasurement,
    CollectedAttempt, RecordingBundle, collect, completeness, collection_plan,
    attempt_identity, measurement_input, export_training, validate_recording_request)
from app.game.offline.calibration import AttemptMeasurement
from app.game.offline.records import Attempt
from app.decision.coverage import factual_capabilities
from app.game.models import canonical_json, content_id
from app.models.schemas import VerificationResult


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


def experiment4_request_data():
    from app.selection.capabilities import BUILTIN_CAPABILITIES
    from app.game.offline.calibration import MeasurementSetup
    from app.game.resource_provenance import ResourceManifest
    request, *_ = diagnostic()
    data = request.model_dump(mode='json')
    data.update(version='offline_experiment4_diagnostic_v1', intended_use='smoke',
        study_approval=None, cache_contract='diagnostic_observation_only')
    data.update(eligibility_manifest_id='synthetic-eligibility-v1',
        eligibility_manifest_sha256='a' * 64, eligibility_manifest_file_sha256='b' * 64,
        eligibility_candidate_roster_sha256='c' * 64, eligibility_group_assignments_sha256='d' * 64,
        development_source_manifest_sha256='e' * 64, development_candidates_sha256='f' * 64,
        development_verifier_inputs_sha256='1' * 64, selected_subset_sha256='2' * 64,
        collection_authorized=False, collection_authorization=None,
        maximum_examples=4, maximum_attempt_slots=16)
    data['permitted_datasets'] = [['development', 'development-v1']]
    data['candidates'] = [dict(verifier_name=name, adapter=name + '_v1', registered=True,
        capability_source='builtin', capabilities=asdict(BUILTIN_CAPABILITIES[name]))
        for name in ('confidence', 'evidence', 'rule', 'semantic')]
    resources = ResourceManifest(verifiers=tuple(dict(verifier_name=name, resources=tuple(
        dict(kind=kind, resource_id=f'{name}-{kind}', sha256='a' * 64)
        for kind in ('implementation', 'configuration', 'model', 'corpus', 'index', 'prompt', 'service')))
        for name in ('confidence', 'evidence', 'rule', 'semantic')))
    setup = MeasurementSetup(resources=resources, environment={'host': 'SYNTHETIC'},
        dependency_versions={'python': 'SYNTHETIC'}, code_revision='a' * 40,
        application_source_digest='b' * 64, evidence_kind='synthetic_test_fixture')
    data['expected_setup'] = setup.model_dump(mode='json')
    data['execution_configuration_id'] = resources.manifest_id
    data['examples'] = [data['examples'][1]]
    data['examples'][0].update(role='development', purpose='diagnostic', label=None,
        example_id='candidate-1', source_candidate_id='source-candidate-1', benchmark='GSM8K',
        run_id='run-1', split_identity='pair-1', question_id='question-1')
    data['examples'].append(dict(data['examples'][0], example_id='candidate-2',
        source_candidate_id='source-candidate-2', run_id='run-2'))
    return data


def test_diagnostic_same_collection_without_label_or_custody_claims():
    request, pool, setup, observer, context = diagnostic()
    bundle = collect(request, pool, setup, observer)
    assert completeness(bundle)['executed_calls'] == 4
    assert all(a.measurement is not None and a.attempt.report is not None for a in bundle.attempts)
    assert all(type(a.measurement) is AttemptMeasurement for a in bundle.attempts)
    assert all(a.measurement.purpose == 'calibration' for a in bundle.attempts)
    assert all(e.label is None for e in bundle.request.examples)
    assert 'custody_record' not in bundle.request.final_test_reservation.model_dump()
    restored = RecordingBundle.model_validate_json(bundle.model_dump_json())
    assert isinstance(restored.request, DiagnosticRecordingRequest)
    assert all(type(a.measurement) is AttemptMeasurement for a in restored.attempts)
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


def test_experiment4_diagnostic_request_enforces_development_roster_and_bounds():
    from app.game.offline.calibration import MeasurementSetup
    data = experiment4_request_data()
    setup = MeasurementSetup.model_validate(data['expected_setup'])

    valid = validate_recording_request(data)
    assert isinstance(valid, Experiment4DiagnosticRecordingRequest)
    assert valid.maximum_examples == 4
    assert valid.maximum_attempt_slots == 16
    assert valid.collection_authorized is False
    bundle = RecordingBundle(request=valid, observed_setup=setup, attempts=())
    restored = RecordingBundle.model_validate_json(bundle.model_dump_json())
    assert isinstance(restored.request, Experiment4DiagnosticRecordingRequest)

    preflight_data = dict(data, factory=None, execution_configuration_id=None,
        expected_setup=None, final_test_reservation=None)
    preflight = validate_recording_request(preflight_data)
    assert isinstance(preflight, Experiment4DiagnosticRecordingRequest)
    assert preflight.collection_authorized is False
    with pytest.raises(ValueError, match='not authorized'):
        collect(preflight, [], None, None)
    wrongly_authorized = dict(preflight_data, collection_authorized=True,
        collection_authorization='test-reference', factory='app.game.offline.recording_adapters:project_factory')
    with pytest.raises(ValueError, match='reservation/exclusion roster is required'):
        validate_recording_request(wrongly_authorized)

    oversized = dict(data, examples=[dict(data['examples'][0], example_id=f'e-{i}', run_id=f'r-{i}')
        for i in range(5)])
    with pytest.raises(ValueError, match='maximum examples'):
        Experiment4DiagnosticRecordingRequest.model_validate(oversized)

    cross_split = dict(data, examples=[dict(data['examples'][0], role='history')])
    with pytest.raises(ValueError):
        Experiment4DiagnosticRecordingRequest.model_validate(cross_split)


def test_experiment4_specific_measurement_and_bundle_round_trip_synthetically():
    from app.game.offline.calibration import MeasurementSetup

    data = experiment4_request_data()
    request = validate_recording_request(data)
    setup = MeasurementSetup.model_validate(data['expected_setup'])
    assert isinstance(request, Experiment4DiagnosticRecordingRequest)
    assert request.collection_authorized is False
    assert all(example.purpose == 'diagnostic' for example in request.examples)

    example = request.examples[0]
    candidate = next(c for c in request.candidates if c.verifier_name == 'confidence')
    resources = next(v for v in setup.resources.verifiers if v.verifier_name == candidate.verifier_name)
    measurement = Experiment4DiagnosticAttemptMeasurement(
        run_id=example.run_id,
        example_id=example.example_id,
        split_identity=example.split_identity,
        question_id=example.question_id,
        content_identity=example.content_identity,
        dataset_id=example.dataset_id,
        role=example.role,
        purpose='diagnostic',
        verifier_name=candidate.verifier_name,
        setup_fingerprint=setup.fingerprint,
        verifier_fingerprint=content_id(resources.model_dump(mode='json')),
        duration_ms=1.25,
        status='returned',
    )
    restored_measurement = Experiment4DiagnosticAttemptMeasurement.model_validate_json(
        measurement.model_dump_json())
    assert restored_measurement == measurement
    assert restored_measurement.purpose == 'diagnostic'

    report = VerificationResult(
        verifier_name=candidate.verifier_name,
        passed=True,
        score=1.0,
        metadata={'decision': 'SUPPORT', 'rule_kind': 'factual', 'rule': 'synthetic'},
    )
    attempt = Attempt(
        verifier_name=candidate.verifier_name,
        state='directional',
        report_json=report.model_dump_json(),
        execution_id=example.run_id,
        configuration_id=request.execution_configuration_id,
        report_provenance='synthetic-test-provenance',
        adapter=candidate.adapter,
        observed_resources_json=resources.model_dump_json(),
    )
    row = CollectedAttempt(
        attempt_id=attempt_identity(request, example, candidate),
        example_id=example.example_id,
        run_id=example.run_id,
        candidate=candidate.verifier_name,
        planning_json=canonical_json(collection_plan(request, example)),
        attempt=attempt,
        executed=True,
        duration_ms=measurement.duration_ms,
        timing_status=measurement.status,
        measurement=measurement,
        after_resources_json=resources.model_dump_json(),
        returned_payload_json=report.model_dump_json(),
        achieved_capabilities=tuple(sorted(factual_capabilities(report))),
    )
    # This is a model-only synthetic bundle fixture; no collection or verifier
    # dispatch occurred, and the request remains unauthorized.
    bundle = RecordingBundle(request=request, observed_setup=setup, attempts=(row,))
    restored_bundle = RecordingBundle.model_validate_json(bundle.model_dump_json())
    assert restored_bundle.request.collection_authorized is False
    assert isinstance(restored_bundle.request, Experiment4DiagnosticRecordingRequest)
    assert isinstance(restored_bundle.attempts[0].measurement,
        Experiment4DiagnosticAttemptMeasurement)
    assert restored_bundle.attempts[0].measurement.purpose == 'diagnostic'


def test_experiment4_unauthorized_cli_stops_before_factory_initialization(tmp_path, monkeypatch, capsys):
    from app.game.offline.collect import main

    data = experiment4_request_data()
    data['factory'] = 'synthetic_e4_factory:create'
    data['collection_authorized'] = False
    data['collection_authorization'] = None
    request_path = tmp_path / 'request.json'
    request_path.write_text(json.dumps(data), encoding='utf-8')
    monkeypatch.setitem(sys.modules, 'synthetic_e4_factory', SimpleNamespace(
        create=lambda: pytest.fail('factory must not initialize for unauthorized request')))
    output_dir = tmp_path / 'recording'

    assert main(['validate', str(request_path)]) == 0
    assert json.loads(capsys.readouterr().out)['factory_initialized'] is False
    assert main(['collect', str(request_path), '--output-dir', str(output_dir)]) == 2
    assert 'not authorized' in capsys.readouterr().out
    assert not output_dir.exists()


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
