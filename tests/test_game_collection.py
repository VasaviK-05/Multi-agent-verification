"""Synthetic adapters and labelled fixtures only, never empirical study evidence."""
from dataclasses import asdict
import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest

from app.game.models import PlanningContext, content_id
from app.game.offline.collection import (RecordingRequest, RecordingBundle, collect,
    completeness, measurement_input, export_training)
from app.game.offline.collect import main, load_bundle
from app.game.offline.calibration import MeasurementSetup, calibrate
from app.game.offline.attacks import AttackSpecification
from app.game.offline.evaluation import bind_evaluation, fit_policy, export_artifact
from app.game.offline.replay import ReplayContract
from app.game.resource_provenance import ResourceManifest
from app.game.execution import VerifierExecutionFailure
from app.selection.capabilities import CapabilityDescriptor
from app.selection.models import VerifierUnavailable
from app.models.schemas import VerificationResult
from app.verifiers.base_verifier import BaseVerifier
from tests.test_game_foundation import make_context, analysis


def test_measurement_export_rechecks_stored_resource_observations():
    request, pool, setup, observer, *_ = fixture()
    bundle = collect(request, pool, setup, observer)
    for field in ('after_resources_json',):
        data = bundle.model_dump(mode='json')
        data['attempts'][0][field] = '{}'
        tampered = RecordingBundle.model_validate(data)
        with pytest.raises(ValueError, match='resource observations'):
            measurement_input(tampered)


class Checker(BaseVerifier):
    def __init__(self, name, action=None):
        self._name, self.action, self.calls = name, action, []

    @property
    def name(self):
        return self._name

    def verify(self, question, answer, context=None):
        self.calls.append((question, answer, context))
        if isinstance(self.action, BaseException):
            raise self.action
        if self.action is not None:
            return self.action
        return VerificationResult(verifier_name=self.name, passed=True, score=1.,
            metadata={'decision': 'UNSURE' if question.startswith('history') else 'SUPPORT',
                      'rule_kind': 'factual', 'rule': 'arithmetic_addition', 'original_nested': {'kept': [1,2]}})


class Observer:
    def __init__(self, resources):
        self.resources, self.calls = resources, 0

    def snapshot(self):
        self.calls += 1
        return self.resources


def fixture(names=('a','b'), capabilities=None):
    context = make_context(names=names, capabilities=capabilities)
    attacks = AttackSpecification(version='report_corruption_v1', suppression='unavailable')
    context = PlanningContext(**{**context.model_dump(), 'provenance': {
        **context.provenance.model_dump(), 'attack_specification': attacks.specification_id}})
    resources = ResourceManifest(verifiers=tuple(dict(verifier_name=n, resources=tuple(
        dict(kind=k, resource_id=n+'-'+k, sha256=content_id(['SYNTHETIC',n,k]))
        for k in ('implementation','configuration'))) for n in names))
    setup = MeasurementSetup(resources=resources, environment={'host':'SYNTHETIC'},
        dependency_versions={'python':'SYNTHETIC'}, code_revision='a'*40,
        application_source_digest='b'*64, evidence_kind='synthetic_test_fixture')
    a = analysis()
    a.difficulty, a.difficulty_score = 'hard', .8
    examples = [dict(example_id=role, split_identity=role, question_id=role,
        run_id=role, dataset_id=role+'-v1', role=role, purpose='calibration',
        question=role+' question', answer='SYNTHETIC answer', reference=None, analysis=asdict(a),
        label=dict(answer_is_correct=True, label_source='fixture-independent-label',
            label_method='independent_ground_truth', provenance='SYNTHETIC independent fixture labels'))
        for role in ('history','development')]
    candidates = [dict(verifier_name=c.verifier_name, adapter='generic_v1', registered=c.registered,
        capability_source='explicit', capabilities=dict(expected_capabilities=c.expected_capabilities,
            requires_reference=c.requires_reference, readiness=c.configured_readiness,
            unavailable_reason=c.exclusion_reason if c.configured_readiness == 'unavailable' else None,
            limitations=c.limitations)) for c in context.plan.candidates]
    request = RecordingRequest(version='offline_recording_request_v1', intended_use='pilot', study_approval=None,
        preparation_authorization='SYNTHETIC custodian preparation permission', cache_contract='complete_team_independent_v1',
        randomness_control='SYNTHETIC deterministic adapters; no generation',
        execution_configuration_id=resources.manifest_id, expected_setup=setup,
        factory='synthetic_recording_factory:create', candidates=candidates, examples=examples,
        permitted_datasets=(('history','history-v1'),('development','development-v1')),
        final_test_reservation=dict(version='final_test_reservation_v1', role='final_test', dataset_id='test-v1',
            custody_record='SYNTHETIC external witness', examples=(dict(example_id='reserved', split_identity='reserved',
                question_id='reserved', validation_id='reserved', content_identity='f'*64),)))
    return request, [Checker(n) for n in names], setup, Observer(resources), context, attacks


def test_complete_export_reload_replay_and_calibration():
    request, pool, setup, observer, context, attacks = fixture()
    bundle = collect(request, pool, setup, observer)
    assert completeness(bundle)['complete']
    restored = RecordingBundle.model_validate_json(bundle.model_dump_json())
    assert restored.bundle_id == bundle.bundle_id
    measurements = measurement_input(restored)
    calibration = calibrate(dict(measurements=measurements, final_test_reservation=request.final_test_reservation,
        required_verifiers=('a','b'), include_warmups=False, freeze_record='SYNTHETIC freeze'))
    assert all(e['attempts'] == 2 for e in calibration.result['estimates'])
    manifest = export_training(restored, context)
    assert {p.role for p in manifest.partitions} == {'history','development'}
    assert all(len(p.examples[0].attempts) == 2 for p in manifest.partitions)
    assert all(len(c.calls) == 2 for c in pool)
    assert all(c.calls[0] == ('history question','SYNTHETIC answer',None) for c in pool)
    contract = ReplayContract(version='offline_public_decision_v2', coverage_version='factual_output_contract_v1',
        contributor_version='baseline_log_odds_active_group_v1', threshold=.55,
        failure_contract='all_selected_returned', history_prior_alpha=1., history_prior_beta=1.,
        execution_configuration_id=setup.resources.manifest_id, resource_manifest=setup.resources)
    bound = bind_evaluation(context, manifest, contract, attacks)
    policy, evaluation = fit_policy(bound, manifest, contract, attacks)
    artifact = export_artifact(policy, bound, manifest, contract, attacks, applicable_domain='general')
    assert artifact.policy.matrix == evaluation.matrix
    assert any(row.achieved_capabilities == ('arithmetic',) for row in bundle.attempts)
    assert json.loads(bundle.attempts[-1].attempt.report_json)['metadata']['original_nested'] == {'kept':[1,2]}


def test_stable_links_exclude_incidental_durations():
    request, pool, setup, observer, _, _ = fixture()
    first = collect(request, pool, setup, observer)
    second = collect(request, pool, setup, observer)
    assert [a.attempt_id for a in first.attempts] == [a.attempt_id for a in second.attempts]
    data = first.model_dump()
    data['attempts'][0]['measurement']['run_id'] = 'tampered'
    with pytest.raises(ValueError, match='link mismatch'):
        RecordingBundle.model_validate(data)


@pytest.mark.parametrize('error,state,status,complete', [
    (VerifierUnavailable('offline'),'unavailable','failure',True),
    (VerifierExecutionFailure('declared failure'),'failed','failure',True),
    (TimeoutError('adapter deadline'),'failed','timeout',True),
    (RuntimeError('unexpected defect'),'failed','failure',False)])
def test_failures_retained_without_dropping_or_stopping(error,state,status,complete):
    request, pool, setup, observer, _, _ = fixture()
    pool[0].action = error
    bundle = collect(request, pool, setup, observer)
    assert len(bundle.attempts) == 4 and len(pool[1].calls) == 2
    assert bundle.attempts[0].attempt.state == state
    assert bundle.attempts[0].measurement.status == status
    assert bundle.attempts[0].attempt.report_json is None
    assert completeness(bundle)['complete'] == complete
    assert measurement_input(bundle).attempts[0].duration_ms >= 0.


def test_prerequisites_unavailable_and_abstention_are_distinct():
    caps = {'a':CapabilityDescriptor(('arithmetic',)),
            'b':CapabilityDescriptor(('arithmetic',),requires_reference=True),
            'c':CapabilityDescriptor(('arithmetic',),readiness='unavailable',unavailable_reason='not installed')}
    request, pool, setup, observer, _, _ = fixture(names=('a','b','c'),capabilities=caps)
    bundle = collect(request,pool,setup,observer)
    assert completeness(bundle)['complete']
    assert bundle.attempts[0].attempt.state == 'abstention'
    for row in (bundle.attempts[1],bundle.attempts[2]):
        assert row.attempt.state == 'unavailable' and not row.executed
        assert row.duration_ms is None and row.measurement is None
    assert not pool[1].calls and not pool[2].calls
    assert len(measurement_input(bundle).attempts) == 2
    with pytest.raises(ValueError, match='missing required-verifier measurements'):
        calibrate(dict(measurements=measurement_input(bundle), final_test_reservation=request.final_test_reservation,
            required_verifiers=('a','b','c'),include_warmups=False,freeze_record='SYNTHETIC freeze'))


def test_interrupt_and_malformed_report_are_explicit_incomplete_outcomes():
    request,pool,setup,observer,_,_ = fixture()
    pool[0].action = KeyboardInterrupt()
    bundle = collect(request,pool,setup,observer)
    assert not completeness(bundle)['complete'] and not pool[1].calls
    assert bundle.attempts[0].measurement.status == 'interrupted'
    assert all(a.attempt.state == 'missing' for a in bundle.attempts)
    request,pool,setup,observer,_,_ = fixture()
    pool[0].action = {'verifier_name':'wrong','passed':True,'score':.5}
    bundle = collect(request,pool,setup,observer)
    assert not completeness(bundle)['complete']
    assert json.loads(bundle.attempts[0].returned_payload_json)['verifier_name'] == 'wrong'
    assert bundle.attempts[0].attempt.state == 'missing'


def test_unknown_and_changed_resources_are_never_invented():
    request,pool,setup,observer,context,_ = fixture()
    unknown = collect(request,pool,setup,None)
    assert all(a.attempt.report_json for a in unknown.attempts)
    assert all(a.attempt.observed_resources_json is None for a in unknown.attempts)
    assert not completeness(unknown)['complete']
    with pytest.raises(ValueError, match='verified setup'):
        measurement_input(unknown)
    with pytest.raises(ValueError, match='incomplete'):
        export_training(unknown,context)
    class Drifting(Observer):
        def snapshot(self):
            value = super().snapshot()
            if self.calls == 2:
                data = value.model_dump()
                data['verifiers'][0]['resources'][0]['sha256'] = 'c'*64
                return ResourceManifest.model_validate(data)
            return value
    changed = collect(request,pool,setup,Drifting(setup.resources))
    assert not completeness(changed)['complete']
    assert changed.attempts[0].attempt.report_json and changed.attempts[0].measurement is None
    assert changed.attempts[0].after_resources_json is not None  # retain genuine changed observation
    assert changed.attempts[0].timing_status == 'returned'


def test_post_observation_candidate_and_actual_timing_status_checked():
    request,pool,setup,observer,_,_ = fixture()
    bundle=collect(request,pool,setup,observer)
    data=bundle.model_dump()
    data['attempts'][0]['measurement']['status']='failure'
    with pytest.raises(ValueError,match='link mismatch'):
        RecordingBundle.model_validate(data)
    data=bundle.model_dump()
    data['attempts'][0]['after_resources_json']=setup.resources.verifiers[1].model_dump_json()
    assert not completeness(RecordingBundle.model_validate(data))['complete']


@pytest.mark.parametrize('change',['label','label_provenance','same_group','same_question','reserved','final_payload'])
def test_invalid_inputs_reject_before_factory_execution(change,tmp_path,monkeypatch):
    request,_,_,_,_,_ = fixture()
    data = request.model_dump(mode='json')
    if change == 'label':
        del data['examples'][0]['label']
    elif change == 'label_provenance':
        data['examples'][0]['label']['provenance'] = ''
    elif change in {'same_group','same_question'}:
        key = 'split_identity' if change == 'same_group' else 'question_id'
        data['examples'][1][key] = data['examples'][0][key]
    elif change == 'reserved':
        data['final_test_reservation']['examples'][0]['example_id'] = data['examples'][0]['example_id']
    else:
        data['final_test_outcomes'] = str(tmp_path/'NEVER_OPEN.json')
    monkeypatch.setattr('importlib.import_module',lambda *a:pytest.fail('invalid request initialized factory'))
    path = tmp_path/'request.json'
    path.write_text(json.dumps(data))
    assert main(['collect',str(path),'--output-dir',str(tmp_path/'out')]) == 2
    assert not (tmp_path/'out').exists()


def test_cli_journal_recovery_and_export(tmp_path,monkeypatch):
    request,pool,setup,observer,context,_ = fixture()
    monkeypatch.setitem(sys.modules,'synthetic_recording_factory',SimpleNamespace(create=lambda:(pool,setup,observer)))
    path = tmp_path/'request.json'
    path.write_text(request.model_dump_json())
    out = tmp_path/'collected'
    assert main(['validate',str(path)]) == 0 and not pool[0].calls
    assert main(['collect',str(path),'--output-dir',str(out)]) == 0
    bundle = load_bundle(out)
    assert bundle.bundle_id == load_bundle(out/'recordings.json').bundle_id
    assert main(['check',str(out)]) == 0
    assert (out/'measurements.json').exists()
    ctx = tmp_path/'context.json'
    ctx.write_text(context.model_dump_json())
    assert main(['export',str(out),'--context',str(ctx),'--output',str(tmp_path/'training.json')]) == 0
    journal = out/'attempts.jsonl'
    journal.write_text(journal.read_text().splitlines()[0]+'\n')
    assert main(['check',str(out)]) == 2  # recover the partial journal, never hide gaps behind final JSON


def test_valid_collection_never_reads_released_final_payload(tmp_path,monkeypatch):
    from app.game.offline.records import FinalTestReservation
    request,pool,setup,observer,_,_=fixture()
    protected=tmp_path/'reserved-final-outcomes.json'
    protected.write_text('FORBIDDEN OUTCOMES')
    original=Path.open
    def guarded(path,*args,**kwargs):
        if path == protected:
            pytest.fail('fitter/collector opened reserved outcomes')
        return original(path,*args,**kwargs)
    monkeypatch.setattr(Path,'open',guarded)
    monkeypatch.setattr(FinalTestReservation,'validate_payload',lambda *a:pytest.fail('final payload validated'))
    monkeypatch.setitem(sys.modules,'synthetic_recording_factory',SimpleNamespace(create=lambda:(pool,setup,observer)))
    path=tmp_path/'request.json'
    path.write_text(request.model_dump_json())
    assert main(['collect',str(path),'--output-dir',str(tmp_path/'out')]) == 0


def test_unapproved_study_and_incompatible_export_are_rejected():
    request,pool,setup,observer,context,_=fixture()
    data=request.model_dump()
    data['intended_use']='study'
    with pytest.raises(ValueError,match='study approval'):
        RecordingRequest.model_validate(data)
    bundle=collect(request,pool,setup,observer)
    selection=json.loads(context.selection_json)
    selection['candidates'][0]['expected_capabilities']=[]
    from app.game.models import canonical_json
    wrong=PlanningContext(**{**context.model_dump(),'selection_json':canonical_json(selection)})
    with pytest.raises(ValueError,match='eligibility/capabilities'):
        export_training(bundle,wrong)


def test_smoke_cannot_be_promoted_and_fit_settings_not_required():
    request,pool,setup,observer,context,_ = fixture()
    data = request.model_dump()
    data['intended_use']='smoke'
    smoke=RecordingRequest.model_validate(data)
    assert not {'budget','loss_configuration','threshold','history_prior_alpha'} & set(type(smoke).model_fields)
    with pytest.raises(ValueError,match='smoke'):
        export_training(collect(smoke,pool,setup,observer),context)


def test_fresh_collector_import_and_collection_has_no_db_api_or_reputation_io():
    script = r'''
import importlib.abc, sys
class Guard(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname == 'database' or fullname.startswith(('app.database','app.api','app.orchestration')):
            raise AssertionError('persistence/API import: '+fullname)
sys.meta_path.insert(0,Guard())
from tests.test_game_collection import fixture
from app.game.offline.collection import collect, completeness
request,pool,setup,observer,_,_=fixture()
assert completeness(collect(request,pool,setup,observer))['complete']
'''
    result=subprocess.run([sys.executable,'-c',script],capture_output=True,text=True)
    assert result.returncode == 0,result.stderr


def test_project_bridge_uses_existing_factory_and_live_observers(tmp_path,monkeypatch):
    import app.benchmark.project_adapter as project
    from app.game.offline.recording_adapters import project_factory
    request,pool,setup,_,_,_=fixture()
    config=tmp_path/'adapter.json'
    config.write_text(json.dumps(dict(embedding_snapshot=None,nli_snapshot=None,corpus_path='unused',
        index_dir='unused',index_receipt=None,service_observation=None)))
    monkeypatch.setenv('VERIFIER_COLLECTION_ADAPTER_CONFIG',str(config))
    monkeypatch.setattr(project,'create_verifiers',lambda:(pool,setup))
    observed={'version':'SYNTHETIC service observation'}
    monkeypatch.setattr(project,'inspect_setup',lambda c:dict(ready=True,blockers=[],
        observed_setup=setup.model_dump(mode='json'),inventory={'service':observed}))
    monkeypatch.setattr(project,'observe_service',lambda c:SimpleNamespace(model_dump=lambda **kw:observed))
    supplied,actual,observer=project_factory()
    assert supplied == pool and actual == setup and observer.snapshot() == setup.resources
    monkeypatch.setattr(project,'observe_service',lambda c:SimpleNamespace(model_dump=lambda **kw:{'changed':True}))
    with pytest.raises(ValueError,match='live service differs'):
        observer.snapshot()
