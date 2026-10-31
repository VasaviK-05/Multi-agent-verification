"""Synthetic task isolation, routing and collection resume invariants."""
from dataclasses import asdict
import json
from types import SimpleNamespace
import pytest
from app.analysis.task_analyzer import TaskQuestionAnalyzer
from app.game.task_conditioning import analysis_task, bind_task_history, validate_task_history, analysis_signature, TaskPolicyRouter
from app.game.models import PlanningContext
from app.decision.coverage import task_capabilities, factual_capabilities
from app.models.schemas import VerificationResult, ValidationRequest


def test_general_domain_does_not_define_the_task_reputation_key():
    analyzer=TaskQuestionAnalyzer()
    analyses=[analyzer.analyze(q) for q in ('What is 307 + 503?','What is the currency of France?','Paraphrase this reference: Alex carried a parcel to the library.')]
    assert all(a.domain=='general' and a.domain_status=='unknown' for a in analyses)
    assert len({analysis_task(a).task_id for a in analyses})==3
    assert [analysis_task(a).requirements for a in analyses]==[('arithmetic',),('direct_fact',),('semantic_comparison',)]
    with pytest.raises(ValueError):analysis_task(analyzer.analyze('Tell me a tale.'))


def test_task_binding_uses_only_its_exact_history_without_pooling():
    from tests.test_game_clean_coverage import source
    c,m,k,a,e=source();bound=bind_task_history(c,m)
    validate_task_history(bound,m)
    assert bound.reputation_snapshot_id==c.reputation_snapshot_id
    assert all(s.posterior_mean==.5 for s in bound.plan.reputation_statistics)
    assert bound.compatibility_id!=c.compatibility_id
    data=json.loads(bound.task_conditioning_json);data['history_partition_digest']='0'*64
    altered=PlanningContext(**{**bound.model_dump(),'task_conditioning_json':json.dumps(data)})
    with pytest.raises(ValueError):validate_task_history(altered,m)
    data=json.loads(bound.task_conditioning_json);data['identity']['requirements']=['semantic_comparison']
    with pytest.raises(ValueError):PlanningContext(**{**bound.model_dump(),'task_conditioning_json':json.dumps(data)})
    assert 'task_conditioning_json' not in c.model_dump()


def semantic_report():
    from app.verifiers.semantic_verifier import SemanticVerifier
    class Model:
        def encode(self,texts):return [[1.,0.],[.9,.435889894]]
    return SemanticVerifier(model=Model(),model_name='SYNTHETIC').verify('Paraphrase this reference: Alex carried a parcel.','A parcel was carried by Alex.','Alex carried a parcel.')


def test_semantic_measurement_is_scoped_comparison_not_fact_coverage():
    row=semantic_report()
    assert not factual_capabilities(row)
    assert task_capabilities(row,requirements=('semantic_comparison',),reference_available=True)=={'semantic_comparison'}
    assert not task_capabilities(row,requirements=('direct_fact',),reference_available=True)
    assert not task_capabilities(row,requirements=('semantic_comparison',),reference_available=False)
    for key in ('model','compared_text','comparison_method','raw_similarity'):
        broken=row.model_copy(deep=True);broken.metadata.pop(key)
        assert not task_capabilities(broken,requirements=('semantic_comparison',),reference_available=True)
    bare=VerificationResult(verifier_name='semantic',passed=True,score=1.,metadata={'decision':'SUPPORT'})
    assert not task_capabilities(bare,requirements=('semantic_comparison',),reference_available=True)


def test_unknown_infeasible_and_budget_routes_fail_without_dispatch():
    analyzer=TaskQuestionAnalyzer();a=analyzer.analyze('What is 307 + 503?')
    signature=analysis_signature(a,'810');router=TaskPolicyRouter(((signature,100.,True,None,'insufficient informative contributors'),))
    def run(a,request,**kw):return router.run(None,a,request,'synthetic',provider=None,rng=None,resource_observer=None,**kw)
    request=ValidationRequest(question='What is 307 + 503?',answer='810',context='810')
    assert run(a,request).summary['selection_status']=='task_infeasible'
    assert run(a,request,budget=99.).summary['selection_status']=='task_out_of_scope'
    unknown=analyzer.analyze('Tell me a tale.')
    assert run(unknown,request).summary['selection_status']=='task_unknown'


@pytest.mark.parametrize('failed',[False,True])
def test_resume_never_reexecutes_completed_or_failed_attempts(failed):
    from tests.test_game_collection import fixture
    from app.game.offline.collection import collect
    from app.game.execution import VerifierExecutionFailure
    request,pool,setup,observer,*_=fixture()
    if failed:pool[0].action=VerifierExecutionFailure('SYNTHETIC recorded failure')
    rows=[]
    def checkpoint(row):rows.append(row);raise KeyboardInterrupt()
    with pytest.raises(KeyboardInterrupt):collect(request,pool,setup,observer,sink=checkpoint)
    assert sum(len(p.calls) for p in pool)==1
    _,newpool,_,newobserver,*_=fixture()
    resumed=collect(request,newpool,setup,newobserver,completed=rows)
    assert resumed.attempts[0]==rows[0]
    assert sum(len(p.calls) for p in newpool)==3
    assert len({r.attempt_id for r in resumed.attempts})==4
    assert resumed.attempts[0].attempt.state==('failed' if failed else 'abstention')


def test_resume_rejects_setup_change_before_verifier_execution():
    from tests.test_game_collection import fixture
    from app.game.offline.collection import collect
    request,pool,setup,observer,*_=fixture()
    altered=setup.model_copy(update={'application_source_digest':'f'*64})
    with pytest.raises(ValueError,match='setup'):collect(request,pool,altered,observer)
    assert not any(p.calls for p in pool)


def test_cli_refuses_ambiguous_inflight_attempt_without_retry(tmp_path):
    from tests.test_game_collection import fixture
    from app.game.offline.collect import main
    request,pool,setup,observer,*_=fixture()
    prior=tmp_path/'prior';prior.mkdir()
    (prior/'request.json').write_text(request.model_dump_json())
    (prior/'observed-setup.json').write_text(setup.model_dump_json())
    (prior/'started.jsonl').write_text(json.dumps({'attempt_id':'SYNTHETIC started but unflushed'})+'\n')
    path=tmp_path/'input.json';path.write_text(request.model_dump_json())
    assert main(['collect',str(path),'--resume-from',str(prior),'--output-dir',str(tmp_path/'fresh')])==2
    assert not (tmp_path/'fresh').exists()


def test_source_numbers_do_not_round_large_published_values():
    from scripts.multitask_policy42 import source_number
    for value in (2381741,17098242,12345.125):assert float(source_number(value))==value
    for value in (True,0,-1,float('nan')):
        with pytest.raises(ValueError):source_number(value)


def test_task_episode_routes_through_existing_runtime_without_label_input():
    import random
    from tests.test_game_reliability_first import full_fixture
    from tests.test_game_foundation import analysis
    from app.game.offline.evaluation import bind_evaluation, construct_payoffs, export_artifact
    from app.game.offline.reliability import fit_reliability_first
    from app.game.execution_contract import ExecutionContract
    from app.game.artifacts import DeploymentEpisode, InMemoryPolicyProvider
    from tests.test_game_offline import report
    c,m,k,a,e,selector=full_fixture()
    context=bind_task_history(c,m)
    unbound=PlanningContext(**{**context.model_dump(),'offline_evaluation_id':None,'execution_contract_json':None})
    contract=ExecutionContract(**{**k.model_dump(),'version':'offline_public_decision_v4','coverage_version':'task_output_contract_v2'})
    context=bind_evaluation(unbound,m,contract,a)
    e=construct_payoffs(context,m,contract,a)
    bound,p=fit_reliability_first(context,m,contract,a,e)
    artifact=export_artifact(p,bound,m,contract,a,applicable_domain='general')
    episode=DeploymentEpisode(episode_id='task-synthetic',context=bound,contract=contract,execution_configuration_id=contract.execution_configuration_id)
    signature=analysis_signature(analysis(),None)
    router=TaskPolicyRouter(((signature,bound.budget,True,episode,''),))
    for verifier in selector._injected:verifier.verify=lambda *args,n=verifier.name,**kw:report(n)
    actual=router.run(selector,analysis(),ValidationRequest(question='synthetic',answer='synthetic'),'synthetic',
        provider=InMemoryPolicyProvider((artifact,)),rng=random.Random(42),resource_observer=SimpleNamespace(snapshot=lambda:contract.resource_manifest),
        allow_synthetic_for_tests=True)
    assert actual.summary['selection_status']=='selected' and actual.public_status=='passed'
    assert actual.summary['task_id']==signature[0]


def test_budget_cache_reuses_only_exact_semantics_and_records():
    from tests.test_game_clean_coverage import source
    from app.game.offline.records import TrainingManifest
    from app.game.offline.replay import category_id
    from app.game.offline.evaluation import bind_evaluation, construct_payoffs
    from app.game.offline.budget_sensitivity import restrict_budget_evaluation
    c,m,k,a,e=source()
    target=PlanningContext(**{**c.model_dump(),'budget':1.,'offline_evaluation_id':None,'execution_contract_json':None})
    data=m.model_dump()
    for p in data['partitions']:
        for example in p['examples']:example['planning_category']=category_id(target)
    manifest=TrainingManifest(**data);target=bind_evaluation(target,manifest,k,a)
    cached=restrict_budget_evaluation(c,m,target,manifest,k,a,e)
    fresh=construct_payoffs(target,manifest,k,a)
    assert cached==fresh
    bad=PlanningContext(**{**target.model_dump(),'loss_configuration':{**target.loss_configuration.model_dump(),'uncertain':.3}})
    with pytest.raises(ValueError,match='identical decision'):restrict_budget_evaluation(c,m,bad,manifest,k,a,e)


def test_task_history_dataset_must_match_declared_provenance():
    from tests.test_game_clean_coverage import source
    c,m,*_=source();bound=bind_task_history(c,m)
    data=json.loads(bound.task_conditioning_json);data['history_dataset_id']='other-task-history'
    with pytest.raises(ValueError,match='history dataset'):
        PlanningContext(**{**bound.model_dump(),'task_conditioning_json':json.dumps(data)})


def test_task_isolation_rejects_an_existing_domain_pool():
    from tests.test_game_completion import pooled
    members,(_,fitted,_)=pooled()
    domain,context,_=fitted[0]
    manifest=next(m.manifest for m in members if m.context.plan.domain==domain)
    with pytest.raises(ValueError,match='task-isolated'):
        bind_task_history(context,manifest)


def test_task_coverage_requires_task_binding_before_fitting():
    from tests.test_game_reliability_first import full_fixture
    from app.game.execution_contract import ExecutionContract
    from app.game.offline.evaluation import bind_evaluation
    c,m,k,a,*_=full_fixture()
    c=PlanningContext(**{**c.model_dump(),'offline_evaluation_id':None,'execution_contract_json':None})
    k=ExecutionContract(**{**k.model_dump(),'version':'offline_public_decision_v4','coverage_version':'task_output_contract_v2'})
    with pytest.raises(ValueError,match='task-aware'):
        bind_evaluation(c,m,k,a)


def test_public_finalizer_rejects_changed_coverage_semantics():
    from tests.test_game_reliability_first import full_fixture
    from tests.test_game_offline import report
    from app.game.execution_contract import ExecutionContract
    from app.game.offline.evaluation import bind_evaluation
    from app.game.strategies import enumerate_strategies
    from app.game.finalization import finalize_decision
    c,m,k,a,*_=full_fixture()
    c=bind_task_history(c,m)
    c=PlanningContext(**{**c.model_dump(),'offline_evaluation_id':None,'execution_contract_json':None})
    v4=ExecutionContract(**{**k.model_dump(),'version':'offline_public_decision_v4','coverage_version':'task_output_contract_v2'})
    c=bind_evaluation(c,m,v4,a);s=enumerate_strategies(c).strategies[0]
    rows=[report(n) for n in s.verifiers];states=tuple((n,'directional') for n in s.verifiers)
    assert finalize_decision(c,s,v4,rows,states,'synthetic').public_status=='passed'
    with pytest.raises(ValueError,match='bound execution semantics'):
        finalize_decision(c,s,k,rows,states,'synthetic')


def test_semantic_reference_check_matches_question_rule_case_and_whitespace():
    analyzer=TaskQuestionAnalyzer();question='  paraphrase this reference: Alex carried a parcel.  '
    a=analyzer.analyze(question);signature=analysis_signature(a,'Different source.')
    router=TaskPolicyRouter(((signature,1.,True,None,'synthetic'),))
    result=router.run(None,a,ValidationRequest(question=question,answer='A parcel.',context='Different source.'),
        'synthetic',provider=None,rng=None,resource_observer=None)
    assert result.summary['selection_status']=='task_reference_mismatch'
