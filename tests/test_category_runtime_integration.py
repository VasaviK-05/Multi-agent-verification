"""Full engine synthetic tests; no native verify/model/provider/fit calls."""
from dataclasses import replace
from types import SimpleNamespace
import pytest
from app.game.category_runtime import CategoryBinding, CategoryGameRuntime
from app.game.execution import VerifierExecutionFailure
from app.game.artifacts import InMemoryPolicyProvider
from app.game.models import content_id
from app.selection.models import VerifierUnavailable
from tests.category_engineering_fixtures import fixture, output, NAMES


def run(f, **changes):
    return f.runtime.run(f.selector,None,f.request.model_copy(update=changes),'SYNTHETIC-game')


@pytest.mark.parametrize('requirements,team,reference,assessment',[
    (('arithmetic',),('rule',),False,False),
    (('direct_fact',),('evidence',),False,False),
    (('semantic_comparison',),('semantic',),True,False),
    (('consistency',),('confidence',),False,True)])
@pytest.mark.parametrize('passed',[True,False])
def test_all_four_complete_paths_with_unseen_candidates(requirements,team,reference,assessment,passed):
    f=fixture(requirements=requirements,team=team,reference=reference,assessment=assessment)
    f.pool[team[0]].behavior=output(team[0],passed)
    before=f.selector.reputation_manager.export_state()
    result=run(f, answer='8' if passed else '9')
    assert result.summary['selection_status']=='selected'
    assert result.public_status==('passed' if passed else 'failed')
    assert set(result.summary['achieved']) >= set(requirements)
    assert result.summary['contributors']==1
    assert result.summary['termination']=='complete_selected_team'
    assert result.summary['early_stopping_enabled'] is False
    assert result.summary['fallback_enabled'] is False
    assert f.rng.calls==1 and f.observer.calls==2
    assert sum(len(v.calls) for v in f.pool.values())==1
    assert f.selector.reputation_manager.export_state()==before


@pytest.mark.parametrize('team',[('rule',),('confidence','rule'),('confidence','evidence','rule'),NAMES])
@pytest.mark.parametrize('aggregation',['reputation_weighted','dependency_group'])
def test_one_to_four_complete_teams_and_both_aggregations(team,aggregation):
    f=fixture(team=team,reference=True,aggregation=aggregation)
    result=run(f)
    assert result.public_status=='passed'
    assert result.summary['team']==list(team)
    assert result.summary['attempted_verifiers']==list(team)
    assert result.summary['aggregation']==aggregation
    assert sum(len(v.calls) for v in f.pool.values())==len(team)
    if aggregation=='dependency_group':
        assert len(result.detail.groups)==1  # All names share an unresolved dependency.


@pytest.mark.parametrize('case',['unsupported','missing_reference','wrong_reference','label_context'])
def test_prerequisite_or_grammar_failures_do_not_sample_or_dispatch(case):
    f=fixture(requirements=('semantic_comparison',),team=('semantic',),reference=True)
    changes=dict(question='Explain gravity.') if case=='unsupported' else dict(context=None) if case=='missing_reference' else dict(context='different') if case=='wrong_reference' else dict(context='support,reject')
    result=run(f,**changes)
    assert result.public_status=='uncertain'
    assert f.rng.calls==0
    assert not any(v.calls for v in f.pool.values())


def test_wrong_format_remains_eligible_and_is_decided_by_report():
    f=fixture(); f.pool['rule'].behavior=output('rule',False)
    a=run(f,answer='not a number')
    assert a.public_status=='failed' and f.rng.calls==1
    assert f.pool['rule'].calls[0][1]=='not a number'


def test_ambiguous_category_match_has_no_execution():
    f=fixture(); f.runtime._bindings=f.runtime._bindings*2
    result=run(f)
    assert result.public_status=='uncertain' and f.rng.calls==0


def test_missing_policy_is_not_a_fallback():
    f=fixture(); f.runtime._provider=InMemoryPolicyProvider()
    result=run(f)
    assert result.summary['selection_status']=='missing_policy'
    assert not any(v.calls for v in f.pool.values())


def test_incompatible_policy_and_reputation_snapshot_reject_before_sampling():
    f=fixture(); different=fixture(neutral=True)
    f.runtime._provider=InMemoryPolicyProvider([different.artifact])
    result=run(f)
    assert result.summary['selection_status']=='incompatible'
    assert f.rng.calls==0
    # Live feedback must never silently replace the frozen snapshot.
    f=fixture(); old=f.artifact.context.reputation_snapshot_id
    f.selector.reputation_manager.update_reputation('rule','general',False)
    result=run(f)
    assert result.summary['reputation_snapshot_id']==old
    assert result.public_status=='passed'


def test_resource_drift_before_dispatch_is_incompatible():
    f=fixture(); data=f.observer.resources.model_dump()
    data['verifiers'][0]['resources'][0]['sha256']='f'*64
    f.observer.resources=type(f.observer.resources)(**data)
    result=run(f)
    assert result.summary['selection_status']=='provenance_incompatible' and f.rng.calls==0


@pytest.mark.parametrize('failure',[VerifierUnavailable('SYNTHETIC unavailable'),VerifierExecutionFailure('SYNTHETIC timeout')])
def test_failed_member_does_not_stop_selected_team_or_append_fallback(failure):
    f=fixture(team=('confidence','rule'),informative=2)
    f.pool['confidence'].behavior=failure
    result=run(f)
    assert result.public_status=='uncertain'
    assert result.summary['attempted_verifiers']==['confidence','rule']
    assert len(f.pool['rule'].calls)==1
    assert 'selected_execution_incomplete' in result.summary['override_reasons']
    assert not f.pool['evidence'].calls and not f.pool['semantic'].calls


@pytest.mark.parametrize('aggregation',['reputation_weighted','dependency_group'])
def test_minimum_informative_count_not_fixed_by_good_coverage(aggregation):
    f=fixture(neutral=True,aggregation=aggregation)
    result=run(f)
    assert result.public_status=='uncertain' and result.summary['contributors']==0
    assert result.summary['achieved']==['arithmetic']
    assert 'minimum_contributors' in result.summary['override_reasons']


@pytest.mark.parametrize('name,requirements,reference,assessment',[
    ('evidence',('direct_fact',),False,False),('semantic',('semantic_comparison',),True,False),
    ('confidence',('consistency',),False,True)])
def test_abstention_never_establishes_coverage(name,requirements,reference,assessment):
    f=fixture(requirements=requirements,team=(name,),reference=reference,assessment=assessment)
    f.pool[name].behavior=f.pool[name].behavior.model_copy(update={'passed':False,'score':0.,'metadata':{'decision':'UNSURE'}})
    result=run(f)
    assert result.public_status=='uncertain' and not result.summary['achieved']


@pytest.mark.parametrize('change',['n_samples','samples','judgment_source','score'])
def test_malformed_consistency_does_not_count_influence_or_coverage(change):
    f=fixture(requirements=('consistency',),team=('confidence',),assessment=True)
    row=f.pool['confidence'].behavior
    if change=='score':row.score=0.
    elif change=='judgment_source':row.metadata[change]='context'
    else:row.metadata.pop(change)
    result=run(f)
    assert result.public_status=='uncertain'
    assert result.summary['contributors']==0 and not result.summary['achieved']


@pytest.mark.parametrize('challenge',['numbers','negation','entities','relationships'])
def test_semantic_contradiction_mock_limit_is_not_routing_failure(challenge):
    f=fixture(requirements=('semantic_comparison',),team=('semantic',),reference=True)
    # Deliberately high-similarity SUPPORT fixture on a known contradiction.
    # The unchanged verifier may fail to distinguish this; no learned detector.
    result=run(f,answer='SYNTHETIC contradiction: '+challenge)
    assert result.summary['selection_status']=='selected'
    assert result.public_status=='passed'
    assert result.summary['achieved']==['semantic_comparison']
    assert 'direct_fact' not in result.summary['achieved']


def test_synthetic_artifact_cannot_enter_default_runtime():
    f=fixture()
    with pytest.raises(ValueError,match='empirical'):
        CategoryGameRuntime([CategoryBinding(f.reviewed,f.artifact)],reports=f.reports,
            rng=f.rng,resource_observer=f.observer)


def test_insufficient_budget_and_no_feasible_team_are_not_relaxed():
    with pytest.raises(ValueError,match='no feasible'):
        fixture(budget=0.)
    with pytest.raises(StopIteration):
        fixture(team=('confidence','rule'),budget=1.)


def test_old_v4_does_not_gain_consistency_coverage_or_new_serialized_fields():
    from app.game.finalization import finalize_decision
    f=fixture(requirements=('consistency',),team=('confidence',),assessment=False,build_runtime=False)
    result=finalize_decision(f.artifact.context,f.selected,f.artifact.contract,
        [output('confidence')],(('confidence','directional'),),'SYNTHETIC-old')
    assert result.public_status=='uncertain' and result.unresolved==('consistency',)
    assert 'consistency_assessment' not in f.artifact.contract.model_dump(mode='json')


def test_contract_cannot_be_downgraded_or_unbound():
    from app.game.execution_contract import ExecutionContract
    from app.game.finalization import finalize_decision
    f=fixture(requirements=('consistency',),team=('confidence',),assessment=True)
    data=f.artifact.contract.model_dump()
    for changes in ({'version':'offline_public_decision_v4'}, {'consistency_assessment':None},
                    {'coverage_version':'task_output_contract_v2'}):
        with pytest.raises(ValueError):ExecutionContract(**(data|changes))
    other=fixture().artifact.contract
    with pytest.raises(ValueError,match='bound execution'):
        finalize_decision(f.artifact.context,f.selected,other,[output('confidence')],
            (('confidence','directional'),),'SYNTHETIC')


@pytest.mark.parametrize('aggregation',['reputation_weighted','dependency_group'])
def test_completed_consistency_with_shared_dependency_preserves_contributor_minimum(aggregation):
    f=fixture(requirements=('consistency',),team=('confidence','rule'),assessment=True,
        minimum=2,informative=2,aggregation=aggregation)
    result=run(f)
    assert result.public_status=='passed' and result.summary['contributors']==2
    assert 'consistency' in result.summary['achieved']
    if aggregation=='dependency_group':assert len(result.detail.groups)==1
    f.pool['rule'].behavior=output('rule').model_copy(update={'passed':False,'score':0.,'metadata':{'decision':'UNSURE'}})
    result=run(f)
    assert result.public_status=='uncertain' and result.summary['contributors']==1
    assert 'minimum_contributors' in result.summary['override_reasons']


def test_category_adapter_is_accepted_by_unchanged_orchestrator():
    from app.game.category_deployment import create_category_game_runtime
    from app.game.deployment import FlexiblePolicyGameRuntime
    from app.orchestration.validation_orchestrator import ValidationOrchestrator
    f=fixture()
    legacy=object.__new__(FlexiblePolicyGameRuntime)
    legacy._configuration=SimpleNamespace(allowlist=frozenset({'old registered question'}))
    legacy.run=lambda *args,**kwargs: (_ for _ in ()).throw(AssertionError('Wrong exact route'))
    with pytest.raises(ValueError,match='synthetic'):
        create_category_game_runtime(legacy,f.runtime)
    adapter=create_category_game_runtime(legacy,f.runtime,allow_synthetic_for_tests=True)
    orchestrator=ValidationOrchestrator(verifier_selector=f.selector,
        reputation_manager=f.selector.reputation_manager,execution_mode='game',game_runtime=adapter)
    response=orchestrator.validate(f.request)
    assert response.final_status=='passed'
    assert response.execution_audit['selected_strategy_id']==f.selected.strategy_id
    assert response.execution_audit['early_stopping_enabled'] is False


def test_execution_journal_is_forwarded_without_extra_calls_or_database():
    from app.game.category_deployment import create_category_game_runtime
    from app.game.deployment import FlexiblePolicyGameRuntime
    f=fixture(requirements=('consistency',),team=('confidence',),assessment=True)
    events=[]
    class Journal:
        def set_plan(self,plan):events.append(('plan',plan))
        def start_attempt(self,**kwargs):events.append(('start',kwargs));return {'attempt_id':'SYNTHETIC-attempt'}
        def complete_attempt(self,attempt,**kwargs):events.append(('complete',kwargs))
    legacy=object.__new__(FlexiblePolicyGameRuntime)
    legacy._configuration=SimpleNamespace(allowlist=frozenset({'old'}))
    adapter=create_category_game_runtime(legacy,f.runtime,allow_synthetic_for_tests=True)
    result=adapter.run(f.selector,None,f.request,'SYNTHETIC',execution_journal=Journal())
    assert result.public_status=='passed'
    assert [e[0] for e in events]==['plan','start','complete']
    assert result.summary['attempts'][0]['journal_attempt_id']=='SYNTHETIC-attempt'
