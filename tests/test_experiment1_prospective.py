"""Deterministic synthetic integration contracts; no empirical collection or fitting."""
from copy import deepcopy
import hashlib
import json

import pytest

from app.game.models import content_id
from app.game.offline.collection import Candidate
from app.game.offline.records import Partition, TrainingManifest
from app.game.research.comparison import FrozenComparison, prepare_comparison
from app.game.research.experiment1.manifest import AtomicEntry, atomic_bindings, reporting_environment
from app.game.research.experiment1.prospective.models import (
    Manifest, Cohort, Population, Member, LabelProvenance, Evidence, Choices,
    Statistics, Approval, FinalRelease, Authorizations, load_authenticated,
)
from app.game.research.experiment1.prospective.readiness import readiness
from app.game.research.experiment1.prospective.reporting import report_development, report_final
from app.game.research.experiment1.prospective.__main__ import main
from app.game.offline.replay import category_id
from tests.test_experiment1_comparison import latest_fixture
from tests.test_game_build import build_spec

FP = 'a' * 64


@pytest.fixture(scope='module')
def prepared():
    # Existing fixture fits tiny SYNTHETIC matrices only. No historical file is loaded.
    spec, development, artifact = latest_fixture()
    spec = type(spec).model_validate({**spec.model_dump(), 'study_id': 'SYNTHETIC-prospective:arithmetic',
        'uncertainty': dict(method='paired_split_identity_cluster_percentile_v1', resamples=20,
                            confidence_level=.95, seed=31)})
    frozen = prepare_comparison(spec, development, artifact, freeze_record='SYNTHETIC prospective freeze', actual_code_revision=spec.code_revision)
    entry = AtomicEntry(cohort='arithmetic', specification=spec, comparison=frozen, bindings=atomic_bindings(spec, frozen))
    _, original_final = build_spec(names=('a', 'b'))
    final_data = original_final.model_dump()
    for e in final_data['examples']:
        e['execution_configuration_id'] = spec.contract.execution_configuration_id
        e['planning_category'] = category_id(spec.context)
        for a in e['attempts']:
            a['configuration_id'] = spec.contract.execution_configuration_id
            a['observed_resources_json'] = next(v for v in spec.contract.resource_manifest.verifiers if v.verifier_name == a['verifier_name']).model_dump_json()
    final = Partition.model_validate(final_data)
    members = []
    for p in (*spec.manifest.partitions, final):
        for e in p.examples:
            members.append(Member(example_id=e.example_id, group_id=e.split_identity, question_id=e.question_id,
                content_id=e.content_identity, validation_id=e.validation_id, role=p.role, reference_sha256=None,
                label=LabelProvenance(producer_protocol='SYNTHETIC independent oracle',method=e.label_method, basis='independent_ground_truth', source=e.label_source,
                    record='SYNTHETIC independent oracle', human_verified=False)))
    candidates = tuple(Candidate(verifier_name=p.verifier_name, adapter='generic_v1', registered=p.registered,
        capability_source='explicit', capabilities=dict(expected_capabilities=p.expected_capabilities,
            requires_reference=p.requires_reference, readiness=p.configured_readiness, limitations=p.limitations))
        for p in spec.context.plan.candidates)
    matrix = artifact.policy.matrix
    choices = Choices(minimum_selected=1, minimum_informative=1, development_coverage_floor=matrix.clean_coverage.minimum,
        budget=spec.context.budget, resource_coefficient=spec.context.loss_configuration.resource_weight,
        cost_units=spec.context.cost_units, attempt_costs=spec.context.attempt_costs,
        history_prior_alpha=spec.contract.history_prior_alpha, history_prior_beta=spec.contract.history_prior_beta,
        failure_contract=spec.contract.failure_contract, optimizer_tolerance=spec.optimizer_tolerance,
        validation_epsilon=matrix.reliability_first.epsilon, cost_tolerance=matrix.reliability_first.cost_tolerance,
        objective='validation_then_attempt_cost_v1')
    c = Cohort(name='arithmetic', population_kind='bounded_arithmetic', source_benchmark='SYNTHETIC',
        population=Population(dataset_ids=tuple((p.role,p.dataset_id) for p in (*spec.manifest.partitions, final)),
            source_sha256='b'*64, grouping_record='SYNTHETIC whole related groups', members=tuple(members)),
        resources=spec.contract.resource_manifest, candidates=candidates, reference_contract='SYNTHETIC explicit no-reference scope',
        dependencies=spec.context.dependencies, attacks=spec.attacks, choices=choices, training=spec.manifest, frozen=entry)
    manifest = Manifest(study_id='SYNTHETIC-prospective', evidence_kind='synthetic_test_fixture', source_commit=spec.code_revision, source_fingerprint=FP,
        reporting_environment=reporting_environment(), statistics=Statistics(resamples=20,seed=31),
        cohorts=(c, Cohort(name='factual')))
    subject = manifest.collection_id('arithmetic')
    evidence = tuple(Evidence(kind=kind, subject_id=subject, artifact_sha256='c'*64, authority='SYNTHETIC owner', record='SYNTHETIC reviewed evidence')
        for kind in ('labels','task_support','eligibility','reference','resources','collector','custody','calibration'))
    c = Cohort.model_validate({**c.model_dump(), 'evidence': evidence, 'final_exposure': 'untouched_reserved'})
    manifest = Manifest.model_validate({**manifest.model_dump(), 'cohorts': (c, manifest.cohort('factual'))})
    return manifest, final


def auth_for(m, *, release=None):
    return Authorizations(approvals=(
        Approval(scope='collection', subject_id=m.collection_id('arithmetic'), authority='SYNTHETIC authority', decision_record='SYNTHETIC collection decision'),
        Approval(scope='protocol', subject_id=m.protocol_id, authority='SYNTHETIC authority', decision_record='SYNTHETIC protocol decision'),
        Approval(scope='fitting', subject_id=m.fitting_id('arithmetic'), authority='SYNTHETIC authority', decision_record='SYNTHETIC fitting decision')),
        releases=() if release is None else (release,))


def check(m, auth=None, **kwargs):
    return readiness(m, actual_commit=kwargs.get('commit',m.source_commit), actual_source_fingerprint=kwargs.get('fingerprint',FP), authorizations=auth or auth_for(m))


def stage(r, name, cohort='arithmetic'):
    return next(x for x in r['cohorts'] if x['cohort']==cohort)['stages'][name]


def mutate(m, update):
    data=m.model_dump();update(data);return Manifest.model_validate(data)


def test_five_stages_ready_independently_and_read_only(prepared, monkeypatch):
    m,_=prepared;before=m.model_dump_json()
    import app.game.research.experiment1.runner as runner
    import app.game.research.comparison as comparisons
    import app.game.solver as solver
    def forbidden(*a,**kw):raise AssertionError('metadata checker replayed, fitted or released')
    monkeypatch.setattr(runner,'replay',forbidden)
    monkeypatch.setattr(comparisons,'prepare_comparison',forbidden)
    monkeypatch.setattr(solver,'linprog',forbidden)
    monkeypatch.setattr(type(m.cohort('arithmetic').training.final_test_reservation),'validate_payload',forbidden)
    r=check(m)
    assert stage(r,'policy_fitting')['ready'],stage(r,'policy_fitting')['blockers']
    assert stage(r,'final_test_authorization_review')['ready'],stage(r,'final_test_authorization_review')['blockers']
    assert not stage(r,'final_test_scoring')['ready']
    assert not r['stages']['policy_fitting']['ready']  # Factual remains a distinct unresolved cohort.
    assert not r['final_payloads_read'] and r['inference_calls']==r['optimization_calls']==0
    assert m.model_dump_json()==before


def test_collection_does_not_require_fitting_only_decisions(prepared):
    m,_=prepared
    changed=mutate(m,lambda d:d['cohorts'][0].update(choices={},training=None,frozen=None))
    r=check(changed)
    assert stage(r,'history_development_collection')['ready']
    assert not stage(r,'policy_fitting')['ready']
    assert all(b['owner'] and b['expected_artifact'] and b['identity_check'] for b in stage(r,'policy_fitting')['blockers'])


@pytest.mark.parametrize('field',['budget','resource_coefficient','development_coverage_floor','minimum_informative'])
def test_no_scientific_defaults_or_silent_objective_changes(prepared,field):
    m,_=prepared
    changed=mutate(m,lambda d:d['cohorts'][0]['choices'].update({field:None}))
    assert not stage(check(changed),'policy_fitting')['ready']


@pytest.mark.parametrize('kind',['resources','calibration','collector','custody'])
def test_stale_evidence_and_source_mismatch(prepared,kind):
    m,_=prepared
    def update(d):
        next(e for e in d['cohorts'][0]['evidence'] if e['kind']==kind)['subject_id']='f'*64
    changed=mutate(m,update)
    assert not stage(check(changed),'final_test_authorization_review')['ready']
    assert not stage(check(m,fingerprint='f'*64),'policy_fitting')['ready']
    assert not stage(check(m,commit='0'*40),'policy_fitting')['ready']


def test_provisional_labels_cannot_masquerade_as_human_or_independent(prepared):
    m,_=prepared
    with pytest.raises(ValueError,match='cast'):
        LabelProvenance(producer_protocol='SYNTHETIC independent oracle',method='independent_ground_truth',basis='synthetic_transformation',source='producer',record='record',human_verified=False)
    with pytest.raises(ValueError,match='human'):
        LabelProvenance(producer_protocol='SYNTHETIC independent oracle',method='independent_human',basis='human_adjudication',source='producer',record='record',human_verified=False)
    changed=mutate(m,lambda d:d['cohorts'][0]['population']['members'][0]['label'].update(method='provisional_automated',basis='synthetic_transformation'))
    assert not stage(check(changed),'history_development_collection')['ready']


@pytest.mark.parametrize('benchmark',['GSM8K','HotpotQA'])
def test_unsupported_population_not_relabelled(prepared,benchmark):
    m,_=prepared
    changed=mutate(m,lambda d:d['cohorts'][0].update(source_benchmark=benchmark))
    assert any(b['code']=='unsupported_population' for b in stage(check(changed),'history_development_collection')['blockers'])


def test_group_split_and_quarantine_isolation(prepared):
    m,_=prepared
    with pytest.raises(ValueError,match='overlap'):
        mutate(m,lambda d:d['cohorts'][0]['population']['members'][0].update(group_id=d['cohorts'][0]['population']['members'][-1]['group_id']))
    member=m.cohort('arithmetic').population.members[0]
    with pytest.raises(ValueError,match='quarantined'):
        mutate(m,lambda d:d['cohorts'][0]['population'].update(excluded=[dict(example_id='excluded',group_id=member.group_id,reason='quarantine',source_record='producer',quarantine_group=True)]))
    changed=mutate(m,lambda d:d['cohorts'][0]['population'].update(excluded=[dict(example_id='excluded',group_id='excluded-group',reason='quarantine',source_record='producer',quarantine_group=True)]))
    assert changed.cohort('arithmetic').population.excluded[0].example_id=='excluded'


def test_authenticated_loader_rejects_duplicates_retrospective_and_bad_hash(prepared,tmp_path):
    m,_=prepared;p=tmp_path/'manifest.json';raw=m.model_dump_json().encode();p.write_bytes(raw)
    assert load_authenticated(p,hashlib.sha256(raw).hexdigest())==m
    with pytest.raises(ValueError,match='SHA-256'):load_authenticated(p,'0'*64)
    p.write_text('{"version":"prospective_experiment1_v1","version":"other"}')
    with pytest.raises(ValueError,match='duplicate'):load_authenticated(p,hashlib.sha256(p.read_bytes()).hexdigest())
    p.write_text('{"version":"retrospective_experiment1_v1"}')
    with pytest.raises(ValueError):load_authenticated(p,hashlib.sha256(p.read_bytes()).hexdigest())


def test_missing_and_incompatible_frozen_policy_block_reporting(prepared):
    m,_=prepared
    changed=mutate(m,lambda d:d['cohorts'][0].update(frozen=None))
    with pytest.raises(ValueError,match='frozen_comparison_missing'):
        report_development(changed,'arithmetic',actual_commit=m.source_commit,actual_source_fingerprint=FP,authorizations=auth_for(changed))
    changed=mutate(m,lambda d:d['cohorts'][0]['choices'].update(budget=999.))
    assert any(b['code']=='objective_or_cost_contract_mismatch' for b in stage(check(changed),'final_test_authorization_review')['blockers'])


def test_development_adapter_preserves_mixtures_and_coverage_compliance(prepared):
    m,_=prepared
    r=report_development(m,'arithmetic',actual_commit=m.source_commit,actual_source_fingerprint=FP,authorizations=auth_for(m))
    assert r['metrics'][0]['probabilities']==m.cohort('arithmetic').frozen.comparison.policies[0].probabilities
    assert len(r['publication_rows'])==sum(len(p['attacks']) for p in r['metrics'])
    assert 'decision_validation' in r['metric_semantics']['worst_case_expected_loss']
    assert any(not p['development_coverage']['satisfies'] for p in r['metrics'])
    assert not r['fairness']['uniform_reweighted']
    assert r['uncertainty']['intervals']==[]  # Only one independent synthetic group.


def test_final_gate_precedes_even_the_loader_and_payload_hash(prepared):
    m,final=prepared;called=[]
    def loader():called.append(True);return final.model_dump_json().encode()
    with pytest.raises(ValueError,match='final_release'):
        report_final(m,'arithmetic',actual_commit=m.source_commit,actual_source_fingerprint=FP,authorizations=auth_for(m),payload_loader=loader)
    assert not called
    release=FinalRelease(manifest_id=m.manifest_id,cohort='arithmetic',reservation_id=m.cohort('arithmetic').training.final_test_reservation.reservation_id,payload_sha256=hashlib.sha256(loader()).hexdigest(),authority='SYNTHETIC custodian',decision_record='SYNTHETIC release')
    r=report_final(m,'arithmetic',actual_commit=m.source_commit,actual_source_fingerprint=FP,authorizations=auth_for(m,release=release),payload_loader=loader)
    assert r['role']=='final_test' and r['policy_id']==m.cohort('arithmetic').frozen.comparison.full_artifact.policy.policy_id
    with pytest.raises(ValueError,match='SHA-256'):
        report_final(m,'arithmetic',actual_commit=m.source_commit,actual_source_fingerprint=FP,authorizations=auth_for(m,release=release),payload_loader=lambda:b'changed')
    stale=FinalRelease(**{**release.model_dump(),'manifest_id':'0'*64})
    with pytest.raises(ValueError,match='final_release'):
        report_final(m,'arithmetic',actual_commit=m.source_commit,actual_source_fingerprint=FP,authorizations=auth_for(m,release=stale),payload_loader=lambda:pytest.fail('stale release opened payload'))


@pytest.mark.parametrize('problem',['reference','incomplete','failed_as_abstention','resources','label'])
def test_released_payload_integrity(prepared,problem):
    m,final=prepared;d=final.model_dump();e=d['examples'][0]
    if problem=='reference':e['reference']='unequal reference'
    if problem=='incomplete':e['attempts']=e['attempts'][:1]
    if problem=='failed_as_abstention':e['attempts'][0].update(state='abstention',report_json=None)
    if problem=='resources':e['attempts'][0]['observed_resources_json']=None
    if problem=='label':e['label_source']='not-approved'
    raw=json.dumps(d).encode()
    release=FinalRelease(manifest_id=m.manifest_id,cohort='arithmetic',reservation_id=m.cohort('arithmetic').training.final_test_reservation.reservation_id,payload_sha256=hashlib.sha256(raw).hexdigest(),authority='SYNTHETIC',decision_record='SYNTHETIC')
    with pytest.raises(ValueError):
        report_final(m,'arithmetic',actual_commit=m.source_commit,actual_source_fingerprint=FP,authorizations=auth_for(m,release=release),payload_loader=lambda:raw)


def test_cli_has_no_execution_commands_and_requires_trusted_hash(tmp_path,capsys):
    m=Manifest(study_id='draft',evidence_kind='empirical',cohorts=(Cohort(name='arithmetic'),Cohort(name='factual')))
    p=tmp_path/'draft.json';p.write_text(m.model_dump_json());digest=hashlib.sha256(p.read_bytes()).hexdigest()
    assert main(['readiness',str(p),'--sha256',digest])==2
    r=json.loads(capsys.readouterr().out);assert r['stages']['protocol_review']['ready'] and not r['final_payloads_read']
    for command in ('score','fit','collect'):
        with pytest.raises(SystemExit):main([command,str(p)])
    assert main(['schema'])==0
    assert json.loads(capsys.readouterr().out)['properties']['version']['const']=='prospective_experiment1_v1'


def test_fitting_authorization_binds_actual_training_not_just_protocol(prepared):
    m,_=prepared
    changed=mutate(m,lambda d:(d['cohorts'][0].update(frozen=None),d['cohorts'][0]['training']['partitions'][0]['examples'][0].update(answer_is_correct=False)))
    assert changed.protocol_id==m.protocol_id
    assert changed.fitting_id('arithmetic')!=m.fitting_id('arithmetic')
    r=check(changed,auth_for(m))
    assert any(b['code']=='fitting_authorization_missing' for b in stage(r,'policy_fitting')['blockers'])


def test_training_completeness_reference_and_failed_outcomes(prepared):
    m,_=prepared
    def changed_training(update):
        def apply(d):
            d['cohorts'][0]['frozen']=None
            update(d['cohorts'][0]['training']['partitions'][0]['examples'][0])
        return mutate(m,apply)
    incomplete=changed_training(lambda e:e['attempts'][0].update(state='missing',report_json=None))
    assert any(b['code']=='incomplete_recordings' for b in stage(check(incomplete),'policy_fitting')['blockers'])
    failed=changed_training(lambda e:e['attempts'][0].update(state='failed',report_json=None))
    assert stage(check(failed),'policy_fitting')['ready']  # Complete terminal failure, not informative success.
    assert failed.cohort('arithmetic').training.partitions[0].examples[0].attempts[0].state=='failed'
    reference=changed_training(lambda e:e.update(reference='different caller reference'))
    assert any(b['code']=='input_or_label_provenance_mismatch' for b in stage(check(reference),'policy_fitting')['blockers'])


def test_cross_cohort_groups_and_wrong_task_are_not_allowed(prepared):
    m,_=prepared
    def duplicate(d):
        other=deepcopy(d['cohorts'][0]);other.update(name='factual',frozen=None)
        other['population']['dataset_ids']=[(role,'factual-'+name) for role,name in other['population']['dataset_ids']]
        d['cohorts']=(d['cohorts'][0],other)
    with pytest.raises(ValueError,match='cross-cohort'):
        mutate(m,duplicate)
    wrong=mutate(m,lambda d:d['cohorts'][0].update(population_kind='grounded_direct_fact'))
    assert not stage(check(wrong),'policy_fitting')['ready']


def test_comparison_tampering_cannot_change_uniform_or_full_probabilities(prepared):
    m,_=prepared
    for method in ('uniform','full_minimax'):
        d=m.model_dump()
        policies=d['cohorts'][0]['frozen']['comparison']['policies']
        p=next(p for p in policies if p['method']==method)
        p['probabilities']=[(s,float(i==0)) for i,(s,_) in enumerate(p['probabilities'])]
        if method=='full_minimax':
            p['probabilities']=[(s,1./len(p['probabilities'])) for s,_ in p['probabilities']]
        with pytest.raises(ValueError):Manifest.model_validate(d)


def test_historical_policy_and_retrospective_envelopes_not_accepted(prepared,monkeypatch):
    from app.game.research.experiment1.prospective.models import HISTORICAL_POLICIES
    m,_=prepared
    assert len(HISTORICAL_POLICIES)==4
    d=m.model_dump();d['version']='retrospective_experiment1_v1'
    with pytest.raises(ValueError):Manifest.model_validate(d)
    d=m.model_dump();d['cohorts'][0]['training']['partitions']=(*d['cohorts'][0]['training']['partitions'],dict(role='final_test',dataset_id='forbidden',examples=[]))
    with pytest.raises(ValueError,match='final-test outcomes'):Manifest.model_validate(d)
    # Exercise the guard without reading or rewriting any real historical policy.
    import app.game.research.experiment1.prospective.models as models
    synthetic_id=m.cohort('arithmetic').frozen.comparison.full_artifact.policy.policy_id
    monkeypatch.setattr(models,'HISTORICAL_POLICIES',HISTORICAL_POLICIES | {synthetic_id})
    with pytest.raises(ValueError,match='historical fitted'):
        Manifest.model_validate(m.model_dump())


def test_shared_metrics_analytic_mixture_zero_coverage_and_paired_groups():
    from tests.test_experiment1_reporting import cube_fixture
    from app.game.research.experiment1.metrics import point_report,bootstrap_report,Statistics as MetricStatistics
    cube=cube_fixture(groups=3,tiny=True)
    points=point_report(cube)
    full=points[0]
    assert full['probabilities'][0][1]==1e-10
    clean=full['attacks'][0]['metrics']
    assert clean['decision_coverage']==pytest.approx(1e-10)
    assert clean['validation_loss']==pytest.approx(.2*(1.-1e-10))
    assert clean['total_loss']==pytest.approx(clean['validation_loss']+.1*clean['estimated_attempt_cost'])
    suppressed=next(a['metrics'] for a in full['attacks'] if a['attack_kind']=='suppression')
    assert suppressed['decision_coverage']==0. and suppressed['selective_risk'] is None
    config=MetricStatistics(resamples=30,seed=9)
    assert bootstrap_report(cube,config)==bootstrap_report(cube,config)
    assert bootstrap_report(cube,config)['groups']==3


def test_metadata_loader_rejects_reserved_path_before_read(tmp_path,monkeypatch):
    from pathlib import Path
    def forbidden(*a,**k):pytest.fail('reserved payload was opened')
    monkeypatch.setattr(Path,'read_bytes',forbidden)
    with pytest.raises(ValueError,match='reserved'):
        load_authenticated(tmp_path/'final-partition.json','a'*64)


def test_synthetic_records_cannot_authenticate_empirical_study(prepared):
    m,_=prepared
    changed=mutate(m,lambda d:d.update(evidence_kind='empirical'))
    assert any(b['code']=='evidence_kind_mismatch' for b in stage(check(changed),'policy_fitting')['blockers'])


@pytest.mark.parametrize('change,code',[
    ('costs','cost_roster_mismatch'),('dependencies','dependency_roster_mismatch'),('references','mixed_reference_profiles')])
def test_fitting_rejects_unrepresentable_planning_inputs(prepared,change,code):
    m,_=prepared
    def update(d):
        c=d['cohorts'][0];c['frozen']=None
        if change=='costs':c['choices']['attempt_costs']=[('extra',1.)]
        elif change=='dependencies':c['dependencies']={'version':'incomplete','unresolved':['a']}
        else:c['population']['members'][0]['reference_sha256']='a'*64
    altered=mutate(m,update)
    assert any(b['code']==code for b in stage(check(altered),'policy_fitting')['blockers'])


def test_factual_adapter_accepts_a_separate_grounded_synthetic_game():
    """One-verifier fabricated software fixture; no EvidenceVerifier.verify call."""
    from app.game.models import capture_context
    from app.game.execution_contract import ExecutionContract
    from app.game.resource_provenance import VerifierResources,ResourceManifest
    from app.game.research.evidence_validation import EvidenceValidation,EXPECTED
    from app.game.offline.records import FinalTestReservation,ReservedExample,history_reputation
    from app.game.offline.evaluation import bind_evaluation,construct_payoffs,export_artifact
    from app.game.offline.reliability import prepare_reliability_first
    from app.game.policy import build_policy
    from app.game.task_conditioning import bind_task_history
    from app.game.research.specification import PolicyBuildSpecification
    from app.selection.verifier_selector import VerifierSelector
    from app.selection.capabilities import BUILTIN_CAPABILITIES
    from tests.test_verifier_selector import StubVerifier
    from tests.test_game_foundation import analysis
    from tests.test_game_research import study
    from tests.test_game_offline import report
    original=study(labels=('direct_fact',),names=('evidence',))
    observation=VerifierResources(verifier_name='evidence',resources=tuple(dict(kind=k,resource_id='SYNTHETIC-'+k,sha256='a'*64) for k in ('implementation','configuration','model','corpus','index')))
    resources=ResourceManifest(verifiers=(observation,))
    def row(decision,conflict=False):
        label='entailment' if decision=='SUPPORT' else 'contradiction'
        meta=dict(decision=decision,nli_label=label,supporting=[dict(nli_label=label)] if decision=='SUPPORT' else [],contradicting=[dict(nli_label=label)] if decision=='REJECT' else [],claim_decisions=[dict(decision=decision)],unsure_reason=None if decision!='UNSURE' else 'conflict' if conflict else 'neutral')
        return report('evidence',passed=decision=='SUPPORT',strength=0. if decision=='UNSURE' else 1.,metadata=meta)
    proof=EvidenceValidation(version='evidence_public_contract_validation_v2',before=observation,after=observation,
        probes=tuple(dict(case_id=key,report_json=row(decision,key=='controlled_conflict').model_dump_json()) for key,(decision,_) in EXPECTED.items()))
    parts=[]
    for p in original.manifest.partitions:
        data=p.model_dump()
        for e in data['examples']:
            e['execution_configuration_id']=resources.manifest_id
            e['attempts'][0].update(state='directional',adapter='evidence_v1',report_json=row('SUPPORT').model_dump_json(),configuration_id=resources.manifest_id,observed_resources_json=observation.model_dump_json())
        parts.append(Partition.model_validate(data))
    final=next(p for p in parts if p.role=='final_test')
    training=TrainingManifest(version='game_training_manifest_v1',evidence_kind='synthetic_test_fixture',partitions=tuple(p for p in parts if p.role!='final_test'),final_test_reservation=FinalTestReservation(version='final_test_reservation_v1',role='final_test',dataset_id=final.dataset_id,custody_record='SYNTHETIC',examples=tuple(ReservedExample.from_example(e) for e in final.examples)))
    manager=history_reputation(training,prior_alpha=1.,prior_beta=1.)
    selector=VerifierSelector(verifiers=[StubVerifier('evidence')],reputation_manager=manager,capabilities={'evidence':BUILTIN_CAPABILITIES['evidence']},difficulty_range={'easy':(1,1),'hard':(1,1)})
    config=original.context.model_dump();config.pop('selection_json');config.pop('analyzer_provenance');config.update(offline_evaluation_id=None,execution_contract_json=None)
    context=capture_context(selector,analysis(('direct_fact',)),**config)
    contract=ExecutionContract(**{**original.contract.model_dump(),'version':'offline_public_decision_v4','coverage_version':'task_output_contract_v2','contributor_version':'informative_history_influence_v1','execution_configuration_id':resources.manifest_id,'resource_manifest':resources,'team_requirements':dict(minimum_selected=1,minimum_informative=1)})
    data=training.model_dump()
    for p in data['partitions']:
        for e in p['examples']:e['planning_category']=category_id(context)
    training=TrainingManifest.model_validate(data)
    context=bind_evaluation(bind_task_history(context,training),training,contract,original.attacks)
    dev=construct_payoffs(context,training,contract,original.attacks)
    context,matrix=prepare_reliability_first(context,training,contract,original.attacks,dev,minimum=.9)
    policy=build_policy(context,matrix)  # Tiny SYNTHETIC fixture only.
    artifact=export_artifact(policy,context,training,contract,original.attacks,applicable_domain='general')
    spec=PolicyBuildSpecification.model_validate({**original.model_dump(),'version':'offline_policy_build_v1','study_id':'SYNTHETIC-factual:factual','scientific_scope':'SYNTHETIC grounded direct-fact software fixture','manifest':training,'context':context,'contract':contract,'recording':{**original.recording.model_dump(),'execution_configuration_id':resources.manifest_id,'evidence_validation':proof},'uncertainty':dict(method='paired_split_identity_cluster_percentile_v1',resamples=20,confidence_level=.95,seed=31)})
    frozen=prepare_comparison(spec,dev,artifact,freeze_record='SYNTHETIC factual freeze',actual_code_revision=spec.code_revision)
    entry=AtomicEntry(cohort='factual',specification=spec,comparison=frozen,bindings=atomic_bindings(spec,frozen))
    label=LabelProvenance(producer_protocol='SYNTHETIC independent oracle',method='independent_ground_truth',basis='independent_ground_truth',source='fixture-independent-label',record='SYNTHETIC oracle',human_verified=False)
    population=Population(dataset_ids=tuple((p.role,p.dataset_id) for p in parts),source_sha256='a'*64,grouping_record='SYNTHETIC groups',members=tuple(Member(example_id=e.example_id,group_id=e.split_identity,question_id=e.question_id,content_id=e.content_identity,validation_id=e.validation_id,role=p.role,reference_sha256=None,label=label) for p in parts for e in p.examples))
    choices=Choices(minimum_selected=1,minimum_informative=1,development_coverage_floor=.9,budget=context.budget,resource_coefficient=context.loss_configuration.resource_weight,cost_units=context.cost_units,attempt_costs=context.attempt_costs,history_prior_alpha=1.,history_prior_beta=1.,failure_contract=contract.failure_contract,optimizer_tolerance=spec.optimizer_tolerance,validation_epsilon=matrix.reliability_first.epsilon,cost_tolerance=matrix.reliability_first.cost_tolerance,objective='validation_then_attempt_cost_v1')
    c=Cohort(name='factual',population_kind='grounded_direct_fact',source_benchmark='SYNTHETIC',population=population,resources=resources,candidates=(Candidate(verifier_name='evidence',adapter='evidence_v1',registered=True,capability_source='builtin',capabilities=BUILTIN_CAPABILITIES['evidence']),),reference_contract='SYNTHETIC no caller reference',dependencies=context.dependencies,attacks=spec.attacks,choices=choices,training=training,frozen=entry)
    m=Manifest(study_id='SYNTHETIC-factual',evidence_kind='synthetic_test_fixture',source_commit=spec.code_revision,source_fingerprint=FP,reporting_environment=reporting_environment(),statistics=Statistics(resamples=20,seed=31),cohorts=(Cohort(name='arithmetic'),c))
    evidence=tuple(Evidence(kind=k,subject_id=m.collection_id('factual'),artifact_sha256='c'*64,authority='SYNTHETIC owner',record='SYNTHETIC') for k in ('labels','task_support','eligibility','reference','resources','collector','calibration','custody'))
    c=Cohort.model_validate({**c.model_dump(),'evidence':evidence,'final_exposure':'untouched_reserved'});m=Manifest.model_validate({**m.model_dump(),'cohorts':(m.cohort('arithmetic'),c)})
    auth=Authorizations(approvals=tuple(Approval(scope=scope,subject_id=identity,authority='SYNTHETIC',decision_record='SYNTHETIC') for scope,identity in [('collection',m.collection_id('factual')),('protocol',m.protocol_id),('fitting',m.fitting_id('factual'))]))
    status=check(m,auth)
    assert stage(status,'final_test_authorization_review','factual')['ready'],stage(status,'final_test_authorization_review','factual')['blockers']
    result=report_development(m,'factual',actual_commit=m.source_commit,actual_source_fingerprint=FP,authorizations=auth)
    assert result['cohort']=='factual' and result['metrics'][0]['attacks'][0]['metrics']['decision_coverage']==1.


@pytest.mark.parametrize('placeholder',['PENDING_NO_INDEPENDENT_CUSTODIAN','UNRESOLVED','TODO approve'])
def test_pending_authority_cannot_be_promoted_to_approval(placeholder):
    with pytest.raises(ValueError,match='placeholder'):
        Approval(scope='collection',subject_id='a'*64,authority=placeholder,decision_record='review')


def test_pending_reservation_is_not_an_independent_final_seal(prepared):
    m,_=prepared
    changed=mutate(m,lambda d:(d['cohorts'][0].update(frozen=None),d['cohorts'][0]['training']['final_test_reservation'].update(custody_record='PENDING_NO_INDEPENDENT_CUSTODIAN:guard')))
    assert any(b['code']=='unresolved_custody_record' for b in stage(check(changed),'final_test_authorization_review')['blockers'])


def test_group_only_exclusions_preserved_without_fabricated_candidate_ids(prepared):
    m,_=prepared
    excluded=[dict(example_id=None,group_id=g,reason='no independently labelled candidate',source_record='producer group summary',quarantine_group=True) for g in ('excluded-one','excluded-two')]
    changed=mutate(m,lambda d:d['cohorts'][0]['population'].update(excluded=excluded))
    assert all(e.example_id is None for e in changed.cohort('arithmetic').population.excluded)
    assert changed.manifest_id!=m.manifest_id


@pytest.mark.parametrize('exposure',[None,'independence_unverified','previously_exposed'])
def test_untouched_final_population_requires_explicit_review(prepared,exposure):
    m,_=prepared
    changed=mutate(m,lambda d:d['cohorts'][0].update(final_exposure=exposure))
    assert changed.protocol_id==m.protocol_id  # An evidence update, not a new fitting design.
    assert any(b['code']=='final_exposure_unverified' for b in stage(check(changed),'final_test_authorization_review')['blockers'])


def test_verified_correct_producer_class_is_not_independent_adjudication(prepared):
    m,_=prepared
    changed=mutate(m,lambda d:d['cohorts'][0]['population']['members'][0]['label'].update(producer_protocol='provisional_automated_labeling_v1'))
    assert any(b['code']=='independent_label_review_missing' for b in stage(check(changed),'history_development_collection')['blockers'])
