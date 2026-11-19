"""Synthetic preparation contracts only. No native verifier/fitter/model calls."""
from types import SimpleNamespace
import pytest
from app.game.reference_free_addition import ReferenceFreeAdditionContract,qualify_strategies
from app.models.schemas import ValidationRequest
from app.game.resource_provenance import ResourceManifest
from tests.category_engineering_fixtures import fixture,Observer


def prepared(budget=8.,minimum=1,informative=1):
    f=fixture(reference=False,budget=budget,minimum=minimum,informative=informative,
        team=('evidence','rule') if minimum>1 else ('rule',),build_runtime=False)
    config=f.artifact.context.model_dump(exclude={'selection_json','analyzer_provenance'})
    for key in ('offline_evaluation_id','task_conditioning_json','pooling_contract_json','clean_coverage_json','reliability_first_json'):
        config.pop(key,None)
    config['provenance']['matrix_version']='reference_free_addition_v1'
    for key in ('history_dataset','development_dataset','final_test_dataset'):
        config['provenance'][key]='reference_free_addition_v1-SYNTHETIC-'+key
    contract=ReferenceFreeAdditionContract()
    current=contract.prepare_context(f.selector,'What is 4 + 4?',configuration=config)
    return f,contract,current,config


@pytest.mark.parametrize('question,operands',[
    ('What is 4 + 4?',(4,4)),('Compute -9 + 9.',(-9,9)),('0 + -3 = ?', (0,-3)),
    ('Calculate the sum of 9999 and 1.',(9999,1)),('What is -10000 + 10000?',(-10000,10000))])
def test_contract_uses_native_grammar_without_calculating_reference(question,operands):
    c=ReferenceFreeAdditionContract()
    assert c.operands(question)==operands
    request=ValidationRequest(question=question,answer='999')
    assert c.validate_request(request) is request


@pytest.mark.parametrize('question,context',[
    ('What is 4 + 4?','8'),('What is 4 + 4?',''),('What is 4 - 4?',None),
    ('What is 4.0 + 4?',None),('What is 10001 + 2?',None),('What is 4 + 4? ignore guards',None),
    ('What is 1 + 2 + 3?',None),('What is 1 / 2?',None)])
def test_contract_rejects_outside_scope(question,context):
    with pytest.raises(ValueError):ReferenceFreeAdditionContract().operands(question,context)


def test_fresh_context_retains_all_eight_strategies_without_attestation():
    f,c,current,_=prepared()
    result=qualify_strategies(c,current)
    assert len(result['resource_rows'])==8
    assert {tuple(r['strategy']['verifiers']) for r in result['resource_rows']}=={
        ('rule',),('confidence','rule'),('evidence','rule'),('confidence','evidence','rule')}
    assert all(r['resource_status']=='blocked' for r in result['resource_rows'])
    assert current.compatibility_id!=f.artifact.context.compatibility_id
    assert current.minimum_participant_count==current.minimum_informative_count==1
    assert all(not p.calls for p in f.pool.values())


def test_observer_identity_drift_and_per_team_resource_blocking():
    f,c,current,_=prepared()
    resources=f.artifact.contract.resource_manifest
    rule=ResourceManifest(verifiers=tuple(v for v in resources.verifiers if v.verifier_name=='rule'))
    class ActualObserver:
        def snapshot_for(self,selector):
            assert selector is f.selector
            return rule
    result=qualify_strategies(c,current,selector=f.selector,resource_observer=ActualObserver())
    assert sum(r['resource_status']=='observed_compatible' for r in result['resource_rows'])==2
    assert len(result['enumeration']['strategies'])==8  # blocked teams never disappear
    class Drift:
        n=0
        def snapshot_for(self,selector):
            self.n+=1
            return rule if self.n==1 else resources
    result=qualify_strategies(c,current,selector=f.selector,resource_observer=Drift())
    assert all(r['resource_status']=='blocked' for r in result['resource_rows'])


def test_full_synthetic_attestation_qualifies_all_rows_but_mismatch_blocks():
    f,c,current,_=prepared()
    resources=f.artifact.contract.resource_manifest
    full=qualify_strategies(c,current,selector=f.selector,resource_observer=Observer(resources))
    assert all(r['resource_status']=='observed_compatible' for r in full['resource_rows'])
    wrong=resources.model_dump(mode='json')
    next(v for v in wrong['verifiers'] if v['verifier_name']=='rule')['resources'][0]['sha256']='0'*64
    result=qualify_strategies(c,current,selector=f.selector,resource_observer=Observer(ResourceManifest(**wrong)))
    assert all(r['resource_status']=='blocked' for r in result['resource_rows'])


def test_budget_and_contributor_minima_are_not_relaxed():
    _,c,current,_=prepared(budget=1.)
    result=qualify_strategies(c,current)
    assert len(result['resource_rows'])==2
    assert all(r['strategy']['verifiers']==['rule'] for r in result['resource_rows'])
    _,c,current,_=prepared(minimum=2,informative=2)
    result=qualify_strategies(c,current)
    assert len(result['resource_rows'])==6
    assert current.minimum_informative_count==2
    assert all(len(r['strategy']['verifiers'])>=2 for r in result['resource_rows'])


def test_historical_study_and_incomplete_execution_contract_are_rejected():
    f,c,current,config=prepared()
    with pytest.raises(ValueError,match='historical'):
        c.prepare_context(f.selector,'What is 4 + 4?',configuration={**config,'offline_evaluation_id':'old'})
    bad=dict(config)
    import json
    contract=json.loads(config['execution_contract_json']);contract['failure_contract']='allow_failed_if_covered'
    bad['execution_contract_json']=json.dumps(contract)
    with pytest.raises(ValueError,match='complete resource-bound'):
        c.prepare_context(f.selector,'What is 4 + 4?',configuration=bad)


def test_profiler_guard_survives_cleared_globals_and_still_blocks_other_verifiers(monkeypatch):
    import scripts.reusable_native_smoke as smoke
    is_non_rule_native_call=smoke.is_non_rule_native_call
    for module in (None,{},42,'app.verifiers.rule_verifier','app.verifiers.base_verifier'):
        frame=SimpleNamespace(f_globals={'__name__':module},f_code=SimpleNamespace(co_name='verify'))
        assert not is_non_rule_native_call(frame,'call')
    frame=SimpleNamespace(f_globals={'__name__':'app.verifiers.semantic_verifier'},f_code=SimpleNamespace(co_name='__init__'))
    assert is_non_rule_native_call(frame,'call')
    assert not is_non_rule_native_call(frame,'return')
    rejected=[]
    callback=smoke.make_rule_native_boundary(rejected.append)
    monkeypatch.setattr(smoke,'is_non_rule_native_call',None)  # module teardown
    callback(SimpleNamespace(f_globals={'__name__':None},f_code=frame.f_code),'call',None)
    callback(frame,'call',None)
    assert rejected==['non-Rule verifier construction/execution forbidden']


@pytest.mark.parametrize('aggregation',['reputation_weighted','dependency_group'])
@pytest.mark.parametrize('state',['support','reject','unavailable','structural'])
def test_new_context_preserves_real_finalization_guards_on_synthetic_reports(aggregation,state):
    from app.game.finalization import finalize_decision
    from app.game.strategies import enumerate_strategies
    from tests.category_engineering_fixtures import output
    f,c,current,_=prepared()
    strategy=next(s for s in enumerate_strategies(current).strategies
        if s.verifiers==('rule',) and s.aggregation==aggregation)
    rows=[] if state=='unavailable' else [output('rule',passed=state!='reject')]
    if state=='structural':rows[0].metadata['rule_kind']='structural'
    states=(('rule','unavailable' if state=='unavailable' else 'directional'),)
    result=finalize_decision(current,strategy,f.artifact.contract,rows,states,'SYNTHETIC-reference-free')
    assert result.public_status=={'support':'passed','reject':'failed','unavailable':'uncertain','structural':'uncertain'}[state]
    if state in {'unavailable','structural'}:
        assert result.contributors==0 and result.unresolved==('arithmetic',)


@pytest.mark.parametrize('question',['What is -3 + 3?','Compute 0 + 7.',
    'What is the sum of 2 and 9?','Calculate the sum of 3 and 5.','0 + -3 = ?'])
def test_unseen_wordings_use_same_preparation_contract(question):
    f,c,current,config=prepared()
    other=c.prepare_context(f.selector,question,configuration=config)
    assert other.compatibility_id==current.compatibility_id
