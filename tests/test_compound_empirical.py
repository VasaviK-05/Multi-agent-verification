"""48-source software fixtures. No empirical reports, models or policy evidence."""
from decimal import Decimal
import json
from pathlib import Path
from types import SimpleNamespace
import pytest
from app.game.component_sources import source_manifest,question_plan,bind_answer,SourceManifest
from app.game.component_binding import question_plan as legacy_plan,BindingError
from app.game.offline.compound import (prepare,Study,SourceCapacityError,requests,collect_partition,
    Training,JointRecordings,build_contract,fit,export_candidate,load_candidate,evaluate_frozen)
from app.game.models import LossConfiguration,content_id
from app.game.dependencies import DependencyRegistry
from app.game.offline.calibration import MeasurementSetup
from app.game.resource_provenance import ResourceManifest
from app.game.component_execution import enumerate_component_strategies,ComponentPolicy
from app.models.schemas import VerificationResult
from app.verifiers.base_verifier import BaseVerifier


def synthetic_sources(count=48,*,shared_value=False):
    corpus=[];countries=[];lines=[]
    for i in range(count):
        iso=chr(65+i//26)+chr(65+i%26);entity='Entity '+iso.title()
        measure='area' if i%2==0 else 'population';value=1000 if shared_value else 1000+i;unit=' square kilometres' if measure=='area' else ''
        corpus.append(dict(id=iso,title=iso,text=f'The {measure} of {entity} is {value}{unit}.',url=f'https://www.geonames.org/countries/{iso}/'))
        countries.append(dict(cca2=iso,name={'common':entity},area=value))
        lines.append('\t'.join((iso,iso+'X','000',iso,entity,'Capital',str(value),str(value))))
    return source_manifest(json.dumps(corpus).encode(),('\n'.join(lines)).encode(),json.dumps(countries).encode(),evidence_kind='synthetic_test_fixture')


def scenario(count=48):
    sources=synthetic_sources(count)
    loss=LossConfiguration(version='SYNTHETIC-loss',false_accept=1.,false_reject=1.,uncertain=.2,resource_weight=.00001,cost_units='ms')
    deps=DependencyRegistry(version='shared-unknown-SYNTHETIC',unresolved=('evidence','rule'))
    study=prepare(sources,loss,deps,'SYNTHETIC SOFTWARE TEST; NOT EMPIRICAL AUTHORIZATION',excluded_entities=())
    resources=ResourceManifest(verifiers=tuple(dict(verifier_name=n,resources=tuple(
        dict(kind=k,resource_id=n+'-'+k,sha256=sources.corpus_sha256 if k=='corpus' else content_id(['SYNTHETIC',n,k]))
        for k in ({'evidence':('implementation','configuration','model','corpus','index'),
            'rule':('implementation','configuration'),'semantic':('implementation','configuration','model'),
            'confidence':('implementation','configuration','model','prompt','service')}[n])))
            for n in ('evidence','rule','semantic','confidence')))
    setup=MeasurementSetup(resources=resources,environment={'host':'SYNTHETIC'},dependency_versions={'python':'SYNTHETIC'},code_revision='a'*40,
        application_source_digest='b'*64,evidence_kind='synthetic_test_fixture')
    return study,setup


class Fake(BaseVerifier):
    def __init__(self,name,study):self._name=name;self.study=study;self.calls=[]
    @property
    def name(self):return self._name
    def verify(self,q,a,context=None):
        import re
        self.calls.append((q,a))
        if self.name=='rule':
            match=re.fullmatch(r'What is (-?\d+(?:\.\d+)?) \+ (-?\d+(?:\.\d+)?)\?',q)
            passed=Decimal(a)==Decimal(match[1])+Decimal(match[2]);metadata=dict(rule_kind='factual',rule='arithmetic_addition')
        else:
            fact=next(f for f in self.study.sources.facts if q==f'What is the {f.descriptor.measure} of {f.descriptor.entity}?')
            passed=f' is {fact.value}' in a
            label='entailment' if passed else 'contradiction'
            metadata=dict(nli_label=label,unsure_reason=None,supporting=[{'nli_label':label}] if passed else [],
                contradicting=[] if passed else [{'nli_label':label}],claim_decisions=[{'decision':'SUPPORT' if passed else 'REJECT'}])
        metadata['decision']='SUPPORT' if passed else 'REJECT'
        return VerificationResult(verifier_name=self.name,passed=passed,score=1.,metadata=metadata,reasoning='SYNTHETIC software fixture')


@pytest.fixture(scope='module')
def recorded(tmp_path_factory):
    path=tmp_path_factory.mktemp('compound-software-fixture');study,setup=scenario()
    pool=[Fake(n,study) for n in ('evidence','rule')];observer=SimpleNamespace(snapshot=lambda:setup.resources)
    history=collect_partition(study,setup,'history',pool,observer,path/'history')
    development=collect_partition(study,setup,'development',pool,observer,path/'development')
    training=Training(study=study,setup=setup,history=history,development=development)
    return path,training,pool,observer


def test_source_count_gate_and_no_shrunken_design():
    with pytest.raises(SourceCapacityError,match='available=36'):scenario(36)
    study,_=scenario()
    d=study.model_dump();d['groups'][0]['role']='development'
    with pytest.raises(ValueError,match='16 in each'):Study(**d)
    d=study.model_dump();d['groups'][1]['source_id']=d['groups'][0]['source_id']
    with pytest.raises(ValueError,match='entity leakage'):Study(**d)


def test_post_development_configuration_changes_only_coverage(recorded,tmp_path):
    from app.game.component_execution import CompoundFittingConfiguration
    from app.game.offline.compound import construct_payoffs
    _,training,_,_=recorded
    config=CompoundFittingConfiguration(original_study_id=training.study.study_id,authorization='SYNTHETIC explicit post-development amendment')
    original=fit(training);revised=fit(training,fitting_configuration=config)
    assert 'fitting_configuration' not in original['contract'].model_dump(mode='json')
    assert original['matrix'].clean_coverage.minimum==.9
    assert revised['matrix'].clean_coverage.minimum==.85
    assert original['matrix'].values==revised['matrix'].values
    assert original['contract'].obligations==revised['contract'].obligations
    assert original['contract'].budget==revised['contract'].budget
    assert original['contract'].compatibility_id!=revised['contract'].compatibility_id
    assert construct_payoffs(training,contract=revised['contract'])[1]==revised['matrix']
    frozen=export_candidate(training,revised,tmp_path/'candidate')
    assert load_candidate(tmp_path/'candidate')==frozen
    with pytest.raises(ValueError):CompoundFittingConfiguration(minimum_clean_coverage=.84,original_study_id=training.study.study_id,authorization='invalid')
    with pytest.raises(ValueError):fit(training,fitting_configuration=config.model_copy(update={'original_study_id':'wrong-study'}))


def test_explicit_36_group_amendment_preserves_48_default():
    from app.game.offline.compound import PartitionSizes
    original,_=scenario()
    sizes=PartitionSizes(version='amended_36_v1',history=12,development=12,final_test=12)
    revised=prepare(synthetic_sources(36),original.loss,original.dependencies,'SYNTHETIC explicit amendment',
        excluded_entities=(),partition_sizes=sizes)
    assert revised.version=='grouped_compound_study_v3' and revised.sizes.total==36
    assert len(revised.groups)==36 and all(sum(g.role==r for g in revised.groups)==12 for r in ('history','development','final_test'))
    assert 'partition_sizes' not in original.model_dump() and original.sizes.total==48
    with pytest.raises(SourceCapacityError):prepare(synthetic_sources(36),original.loss,original.dependencies,'SYNTHETIC',excluded_entities=())
    with pytest.raises(ValueError):PartitionSizes(version='amended_36_v1',history=16,development=12,final_test=12)


def test_metadata_bound_includes_unexecuted_resource_roster_slots():
    from app.game.offline.compound_journal import metadata_ceiling
    study,setup=scenario()
    prepared=requests(study,setup,'history')
    assert metadata_ceiling(prepared)==1312
    assert sum(len(r.examples)*sum(c.registered for c in r.candidates) for r in prepared.values())==128


def test_source_values_and_binding():
    m=synthetic_sources();d=m.model_dump();d['facts'][0]['value']='9999'
    with pytest.raises(ValueError,match='independent base'):SourceManifest(**d)
    catalog=m.catalog;q='What is the area of Entity Aa, and what is that area plus 0.25 square kilometres? Give both values.'
    p=question_plan(q,catalog);b=bind_answer(p,'{"base":"1001.5","derived":"1001.75"}')
    assert b[1].question=='What is 1001.5 + 0.25?' and b[1].depends_on==('base_fact',)
    with pytest.raises(BindingError):legacy_plan(q)
    for bad in ('{}','{"base":"1","base":"2","derived":"3"}','{"base":1,"derived":"3"}'):
        with pytest.raises(BindingError):bind_answer(p,bad)
    with pytest.raises(BindingError):question_plan(q.replace('plus','times'),catalog)


def test_empirical_custody_cannot_be_a_fixture_header_relabel():
    study,_=scenario();data=study.model_dump();data['sources']['evidence_kind']='empirical'
    with pytest.raises(ValueError,match='actual raw material files'):Study(**data)


def test_entity_names_cannot_hide_identical_component_leakage():
    study,_=scenario()
    with pytest.raises(ValueError,match='component input leakage'):
        prepare(synthetic_sources(shared_value=True),study.loss,study.dependencies,'SYNTHETIC',excluded_entities=())


def test_requests_and_resources(recorded):
    _,t,_,_=recorded
    assert sum(a.executed for j in (t.history,t.development) for _,b in j.bundles for a in b.attempts)==256
    with pytest.raises(ValueError,match='frozen candidate'):requests(t.study,t.setup,'final_test')
    d=t.development.model_dump();d['role']='final_test'
    with pytest.raises(ValueError):Training(study=t.study,setup=t.setup,history=t.history,development=JointRecordings(**d))
    d=t.development.model_dump(mode='json');d['bundles'][0][1]['attempts'].pop()
    with pytest.raises(ValueError,match='completeness'):Training(study=t.study,setup=t.setup,history=t.history,development=JointRecordings(**d))


def test_resume_does_not_repeat_completed_or_ambiguous_attempts(recorded,tmp_path):
    import shutil
    path,t,pool,observer=recorded;before=sum(len(v.calls) for v in pool)
    resumed=collect_partition(t.study,t.setup,'history',pool,observer,tmp_path/'resumed',resume_from=path/'history')
    assert resumed==t.history and sum(len(v.calls) for v in pool)==before
    shutil.copytree(path/'history',tmp_path/'ambiguous')
    with (tmp_path/'ambiguous/derived_sum/started.jsonl').open('a') as handle:
        handle.write(json.dumps(dict(attempt_id='ambiguous-new-call'))+'\n')
    with pytest.raises(ValueError,match='ambiguous in-flight'):
        collect_partition(t.study,t.setup,'history',pool,observer,tmp_path/'blocked-resume',resume_from=tmp_path/'ambiguous')
    assert sum(len(v.calls) for v in pool)==before


def test_report_payload_and_component_identity_are_checked(recorded):
    _,t,_,_=recorded
    d=t.development.model_dump(mode='json')
    active=next(a for a in d['bundles'][0][1]['attempts'] if a['executed'])
    active['returned_payload_json']='{}'
    with pytest.raises(ValueError,match='retained actual returned payload'):
        Training(study=t.study,setup=t.setup,history=t.history,development=JointRecordings(**d))


def test_declared_coverage_infeasibility_is_preserved(recorded):
    from app.decision.vote_normalization import is_abstention
    _,t,_,_=recorded;d=t.development.model_dump(mode='json')
    for _,bundle in d['bundles']:
        for a in bundle['attempts']:
            if not a['executed']:continue
            row=VerificationResult.model_validate_json(a['attempt']['report_json'])
            row.metadata={**row.metadata,'decision':'UNSURE'}
            a['attempt'].update(state='abstention',report_json=row.model_dump_json())
            a.update(returned_payload_json=row.model_dump_json(),achieved_capabilities=[])
    # Explicitly synthetic alternate fixture, not a change to any empirical report.
    training=Training(study=t.study,setup=t.setup,history=t.history,development=JointRecordings(**d))
    result=fit(training)
    assert result['policy'] is None and result['solution'].status=='infeasible'
    assert result['matrix'].clean_coverage.minimum==.9


def test_history_cost_fit_export_reload_test_and_routing(recorded):
    import random
    from app.game.question_routing import QuestionPolicyConfiguration
    from app.game.offline.compound import examples
    from app.selection.verifier_selector import VerifierSelector
    from app.selection.capabilities import BUILTIN_CAPABILITIES
    from app.game.artifacts import InMemoryPolicyProvider
    path,t,pool,observer=recorded
    result=fit(t)
    assert result['status']=='optimal'
    assert {s.verifiers for s in enumerate_component_strategies(result['contract'])}=={('evidence','rule')}
    assert len(result['policy'].matrix.strategy_ids)==2
    assert result['matrix'].clean_coverage.minimum==.9
    costs={}
    for name in ('evidence','rule'):
        calls=[a for j in (t.history,t.development) for _,b in j.bundles for a in b.attempts if a.candidate==name and a.executed]
        costs[name]=sum(a.duration_ms for a in calls)/len(calls)
    assert result['contract'].budget==pytest.approx(sum(costs.values()))
    assert result['contract'].actual_resources==t.setup.resources
    scoped=result['contract'].obligations[0].contract.resource_manifest
    assert scoped.manifest_id!=t.setup.resources.manifest_id
    for entry in scoped.verifiers:t.setup.resources.require_observation(entry)
    counts={o.component_id:{r.verifier_name:r for r in o.context.plan.reputation_statistics} for o in result['contract'].obligations}
    assert counts['base_fact']['evidence'].observation_count==32  # duplicated base bindings are not extra history evidence
    assert counts['derived_sum']['rule'].observation_count==64
    assert result['policy'].evidence_kind=='synthetic_test_fixture' and result['policy'].joint_development is None
    frozen=export_candidate(t,result,path/'export')
    reloaded=load_candidate(path/'export');assert reloaded.freeze_id==frozen.freeze_id
    with pytest.raises(ValueError,match='actual frozen candidate'):
        collect_partition(t.study,t.setup,'final_test',pool,observer,path/'unfrozen-test',freeze_id='0'*64)
    test=collect_partition(t.study,t.setup,'final_test',pool,observer,path/'test',frozen=frozen)
    report=evaluate_frozen(reloaded,test)
    assert report['actual_test_calls']==128 and report['actual_upstream_failures']==0
    assert report['strategic_team_selection_advantage_established'] is False
    clean=next(v for k,v in report['attacks'].items() if k.startswith('clean:'))
    assert clean['policy']['coverage']==1 and clean['policy']['false_accepts']==0
    assert clean['policy']['decision_loss']==clean['development_best_fixed']['decision_loss']==0
    e=examples(t.study,'final_test')[0];c=frozen.policy.contract
    router=QuestionPolicyConfiguration(component_entries=((c.question_signature,c.budget,True,frozen.policy),)).router()
    selector=VerifierSelector(verifiers=pool,capabilities={v.name:BUILTIN_CAPABILITIES[v.name] for v in pool})
    run=router.run(selector,SimpleNamespace(question=e['question'],answer=e['answer'],context=None),'fixture-routing',
        provider=InMemoryPolicyProvider(),rng=random.Random(0),resource_observer=observer,allow_synthetic_for_tests=True)
    assert run.public_status=='passed' and run.summary['team']==['evidence','rule']
    assert run.summary['evidence_kind']=='synthetic_test_fixture'
    for measure in ('area','population'):
        from app.game.component_sources import question_plan
        alternate=next(row for row in examples(t.study,'final_test') if row['variant']=='wrong_base'
            and question_plan(row['question'],t.study.sources.catalog).measure==measure)
        outcome=router.run(selector,SimpleNamespace(question=alternate['question'],answer=alternate['answer'],context=None),
            'fixture-wrong-base-'+measure,provider=InMemoryPolicyProvider(),rng=random.Random(0),resource_observer=observer,
            allow_synthetic_for_tests=True)
        assert outcome.public_status=='failed' and outcome.summary['components'][1]['public_status']=='passed'
    (path/'export/policy.json').write_text('{}')
    with pytest.raises(ValueError,match='inventory'):load_candidate(path/'export')
