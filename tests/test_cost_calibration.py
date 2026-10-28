"""Synthetic fixtures only; durations below are not empirical measurements."""
import json

import pytest

from app.game.models import PlanningContext, content_id
from app.game.offline.calibration import (MeasurementSetup, MeasurementInput, CalibrationArtifact,
    calibrate, apply_calibration, main)
from app.game.resource_provenance import ResourceManifest


def request():
    resources = ResourceManifest(verifiers=tuple(dict(verifier_name=n, resources=tuple(
        dict(resource_id=n+'-'+kind, kind=kind, sha256=content_id([n, kind]))
        for kind in ('implementation', 'configuration'))) for n in ('a', 'b')))
    setup = MeasurementSetup(resources=resources, environment={'host': 'SYNTHETIC'},
        dependency_versions={'python': 'SYNTHETIC'}, code_revision='a'*40,
        application_source_digest='b'*64, evidence_kind='synthetic_test_fixture')
    rows = []
    for n in ('a', 'b'):
        resource = next(v for v in resources.verifiers if v.verifier_name == n)
        for i, (duration, status, purpose) in enumerate(((1., 'returned', 'calibration'),
                (3., 'failure', 'calibration'), (100., 'timeout', 'warmup'))):
            rows.append(dict(run_id='run'+str(i), example_id='history', split_identity='history',
                question_id='history', content_identity=content_id(['history question', 'fixture answer', None]),
                dataset_id='history-v1', role='history', verifier_name=n, duration_ms=duration,
                status=status, purpose=purpose, setup_fingerprint=setup.fingerprint,
                verifier_fingerprint=content_id(resource.model_dump(mode='json'))))
    return dict(measurements=dict(setup=setup, permitted_datasets=(('history', 'history-v1'),),
        preparation_authorization='SYNTHETIC preparation permission', attempts=rows),
        final_test_reservation=dict(version='final_test_reservation_v1', role='final_test', dataset_id='test-v1',
            custody_record='SYNTHETIC external witness only', examples=(dict(example_id='final_test',
                split_identity='final_test', question_id='final_test', validation_id='final_test',
                content_identity=content_id(['final_test question', 'fixture answer', None])),)),
        required_verifiers=('a', 'b'), include_warmups=False, freeze_record='SYNTHETIC freeze')


def test_mean_counts_warmups_reproducibility_and_tampering():
    payload = request()
    first = calibrate(payload)
    assert first == calibrate(json.loads(first.request.model_dump_json()))
    for row in first.result['estimates']:
        assert row == dict(verifier_name=row['verifier_name'], attempt_cost=2., attempts=2,
            failures=1, mean_ms=2., median_ms=2., p95_nearest_rank_ms=3.)
    assert len(first.result['exclusions']) == 2
    payload['include_warmups'] = True
    assert calibrate(payload).result['estimates'][0]['attempt_cost'] == pytest.approx(104/3)
    data = first.model_dump()
    data['result']['estimates'][0]['attempt_cost'] = 0.
    with pytest.raises(ValueError, match='digest'):
        CalibrationArtifact.model_validate(data)


def test_same_run_cannot_change_example_or_purpose_between_verifiers():
    for field, value in [('example_id', 'different-example'), ('purpose', 'warmup')]:
        data = request()
        data['measurements']['attempts'][3][field] = value
        with pytest.raises(ValueError, match='run identity'):
            MeasurementInput.model_validate(data['measurements'])


@pytest.mark.parametrize('duration', [-1., float('nan'), float('inf'), True, '3', None])
def test_invalid_durations(duration):
    data = request()
    data['measurements']['attempts'][0]['duration_ms'] = duration
    with pytest.raises(ValueError):
        calibrate(data)


@pytest.mark.parametrize('change', ['missing', 'duplicate', 'environment', 'verifier', 'final_test', 'unpermitted', 'version'])
def test_invalid_measurements(change):
    data = request()
    rows = data['measurements']['attempts']
    if change == 'missing':
        data['required_verifiers'] += ('absent',)
    elif change == 'duplicate':
        rows.append(rows[0])
    elif change == 'environment':
        rows[0]['setup_fingerprint'] = 'other'
    elif change == 'verifier':
        rows[0]['verifier_fingerprint'] = 'other'
    elif change == 'final_test':
        rows[0]['role'] = 'final_test'
    elif change == 'version':
        rows[0]['version'] = 'unsupported'
    else:
        rows[0]['dataset_id'] = 'other'
    with pytest.raises(ValueError):
        calibrate(data)


@pytest.mark.parametrize('error,status', [(None, 'returned'), (ValueError('original'), 'failure'),
    (TimeoutError('original'), 'timeout'), (KeyboardInterrupt(), 'interrupted')])
def test_wrapper_preserves_return_exception_and_identity(monkeypatch, error, status):
    from app.benchmark.offline_benchmark import _TimedVerifier
    from app.verifiers.base_verifier import BaseVerifier
    import app.benchmark.offline_benchmark as benchmark
    value = object()
    class Verifier(BaseVerifier):
        name = 'a'
        def verify(self, *args):
            if error is not None:
                raise error
            return value
    ticks = iter((10., 10.025))
    monkeypatch.setattr(benchmark.time, 'perf_counter', lambda: next(ticks))
    durations, rows = [], []
    wrapper = _TimedVerifier(Verifier(), durations, measurements=rows, measurement_metadata={'run_id': 'r'})
    if error is None:
        assert wrapper.verify('q', 'a') is value
    else:
        with pytest.raises(type(error)) as caught:
            wrapper.verify('q', 'a')
        assert caught.value is error
    assert len(rows) == len(durations) == 1
    assert rows[0]['verifier_name'] == 'a' and rows[0]['status'] == status
    assert rows[0]['duration_ms'] == pytest.approx(25.)


def integration():
    from tests.test_game_build import build_spec
    from app.game.execution_contract import ExecutionContract
    from app.game.research.specification import RecordingConfiguration
    spec, _ = build_spec(names=('a', 'b'))
    artifact = calibrate(request())
    resources = artifact.request.measurements.setup.resources
    contract = ExecutionContract(**{**spec.contract.model_dump(), 'version': 'offline_public_decision_v2',
        'resource_manifest': resources, 'execution_configuration_id': resources.manifest_id})
    recording = RecordingConfiguration(**{**spec.recording.model_dump(),
        'execution_configuration_id': resources.manifest_id})
    return spec, artifact, contract, recording


def test_context_loading_units_identity_and_separation():
    spec, artifact, contract, recording = integration()
    kwargs = dict(manifest=spec.manifest, contract=contract, recording=recording,
        budget_ms=20., resource_weight_per_ms=.002,
        expected_setup_fingerprint=artifact.request.measurements.setup.fingerprint)
    calibrated = apply_calibration(spec.context, artifact, **kwargs)
    assert calibrated.attempt_costs == (('a', 2.), ('b', 2.))
    assert calibrated.cost_units == calibrated.loss_configuration.cost_units == 'ms'
    assert calibrated.compatibility_id != spec.context.compatibility_id
    assert spec.context.cost_units != 'ms'
    with pytest.raises(ValueError):
        PlanningContext(**{**calibrated.model_dump(), 'cost_units': 'money'})
    with pytest.raises(ValueError, match='configuration'):
        apply_calibration(spec.context, artifact, **{**kwargs, 'contract': spec.contract})
    with pytest.raises(ValueError, match='setup fingerprint'):
        apply_calibration(spec.context, artifact, **{**kwargs, 'expected_setup_fingerprint': 'other'})
    with pytest.raises(ValueError):
        apply_calibration(spec.context, artifact, **{**kwargs, 'budget_ms': float('nan')})
    data = artifact.request.model_dump()
    for a in data['measurements']['attempts']:
        a['split_identity'] = spec.manifest.final_test_reservation.examples[0].split_identity
    with pytest.raises(ValueError, match='final-test'):
        apply_calibration(spec.context, calibrate(data), **kwargs)


def test_builder_uses_calibration_without_state_writes(monkeypatch):
    from app.game.offline.build import build
    from app.game.offline.replay import category_id
    from app.game.research.specification import PolicyBuildSpecification
    from app.game.models import canonical_json
    import app.orchestration.validation_orchestrator as orchestration
    monkeypatch.setattr(orchestration, 'save_reputation', lambda **kw: pytest.fail('state write'))
    spec, artifact, contract, recording = integration()
    context = apply_calibration(spec.context, artifact, manifest=spec.manifest,
        contract=contract, recording=recording, budget_ms=20., resource_weight_per_ms=.002,
        expected_setup_fingerprint=artifact.request.measurements.setup.fingerprint)
    data = spec.model_dump()
    data.update(context=context, contract=contract, recording=recording)
    # Recording producer explicitly supplies the new category and observations.
    for part in data['manifest']['partitions']:
        for e in part['examples']:
            e.update(planning_category=category_id(context), execution_configuration_id=contract.execution_configuration_id)
            for a in e['attempts']:
                resource = next(v for v in contract.resource_manifest.verifiers if v.verifier_name == a['verifier_name'])
                a.update(configuration_id=contract.execution_configuration_id,
                    observed_resources_json=canonical_json(resource.model_dump(mode='json')))
    spec = PolicyBuildSpecification.model_validate(data)
    policy, report = build(spec, actual_code_revision=spec.code_revision, calibration=artifact,
        budget_ms=20., resource_weight_per_ms=.002,
        expected_setup_fingerprint=artifact.request.measurements.setup.fingerprint)
    assert policy.context.attempt_costs == context.attempt_costs
    assert len(policy.policy.strategies) == 6
    assert report['calibration']['calibration_id'] == artifact.calibration_id
    raw = spec.model_dump(mode='json')
    for field in ('attempt_costs', 'budget', 'cost_units'):
        del raw['context'][field]
    del raw['context']['loss_configuration']['resource_weight']
    second, _ = build(raw, actual_code_revision=spec.code_revision, calibration=artifact,
        budget_ms=20., resource_weight_per_ms=.002,
        expected_setup_fingerprint=artifact.request.measurements.setup.fingerprint)
    assert second.artifact_id == policy.artifact_id
    changed_request = artifact.request.model_dump()
    for a in changed_request['measurements']['attempts']:
        a['duration_ms'] *= 2
    changed = calibrate(changed_request)
    changed_context = apply_calibration(spec.context, changed, manifest=spec.manifest,
        contract=contract, recording=recording, budget_ms=20., resource_weight_per_ms=.002,
        expected_setup_fingerprint=changed.request.measurements.setup.fingerprint)
    for part in raw['manifest']['partitions']:
        for example in part['examples']:
            example['planning_category'] = category_id(changed_context)
    different, _ = build(raw, actual_code_revision=spec.code_revision, calibration=changed,
        budget_ms=20., resource_weight_per_ms=.002,
        expected_setup_fingerprint=changed.request.measurements.setup.fingerprint)
    assert different.policy.policy_id != policy.policy.policy_id
    assert different.policy.matrix.matrix_id != policy.policy.matrix.matrix_id
    with pytest.raises(ValueError, match='explicit'):
        build(spec, actual_code_revision=spec.code_revision, calibration=artifact)


def test_cli_rejects_incomplete_template(tmp_path):
    output = tmp_path / 'calibration.json'
    assert main(['docs/verifier_cost_calibration.template.json', '--output', str(output)]) == 2
    assert not output.exists()


def test_collection_preserves_failed_attempt_and_never_run(tmp_path, monkeypatch):
    import sys
    import types
    from app.benchmark.collect_costs import CollectionRequest, main as collect_main
    from app.verifiers.base_verifier import BaseVerifier
    payload = request()
    class Verifier(BaseVerifier):
        def __init__(self, name):
            self._name = name
        @property
        def name(self):
            return self._name
        def verify(self, *args):
            if self.name == 'a':
                raise TimeoutError('preserved timeout')
            pytest.fail('b was never run')
    setup = payload['measurements']['setup']
    fake = types.ModuleType('synthetic_cost_factory')
    fake.make = lambda: ([Verifier('a'), Verifier('b')], setup)
    monkeypatch.setitem(sys.modules, fake.__name__, fake)
    collection = CollectionRequest(setup=setup, final_test_reservation=payload['final_test_reservation'],
        permitted_datasets=(('history', 'history-v1'),), preparation_authorization='SYNTHETIC permission',
        factory='synthetic_cost_factory:make', examples=(dict(example_id='history', split_identity='history',
            question_id='history', run_id='run', dataset_id='history-v1', role='history', purpose='calibration',
            question='history question', answer='fixture answer', context=None),))
    config, output = tmp_path / 'collect.json', tmp_path / 'attempts.json'
    config.write_text(collection.model_dump_json())
    with pytest.raises(TimeoutError, match='preserved timeout'):
        collect_main([str(config), '--output', str(output)])
    measured = MeasurementInput.model_validate_json(output.read_text())
    assert len(measured.attempts) == 1
    assert measured.attempts[0].verifier_name == 'a'
    assert measured.attempts[0].status == 'timeout'
    assert measured.attempts[0].duration_ms >= 0.
    with pytest.raises(ValueError, match='missing required'):
        calibrate({**payload, 'measurements': measured})
    data = collection.model_dump()
    data['examples'][0]['split_identity'] = 'final_test'
    with pytest.raises(ValueError, match='final-test collection'):
        CollectionRequest.model_validate(data)
