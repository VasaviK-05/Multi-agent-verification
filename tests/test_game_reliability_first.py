"""Synthetic semantics and two-stage numerical certificates, no empirical claims."""
import json
import pytest
from app.game.execution_contract import ExecutionContract
from app.game.resource_provenance import ResourceManifest
from app.game.models import PayoffMatrix, Strategy, SolverResult, content_id
from app.game.coverage_contract import CleanCoverageConstraint
from app.game.reliability_contract import ReliabilityFirst
from app.game.finalization import finalize_decision
from app.game.strategies import enumerate_strategies
from app.game.solver import solve_minimax, validate_solution
from app.reputation.reputation_manager import ReputationManager
from app.selection.capabilities import CapabilityDescriptor
from app.selection.verifier_selector import VerifierSelector
from tests.test_verifier_selector import StubVerifier
from tests.test_game_foundation import make_context
from tests.test_game_offline import report


def counts_fixture(names=('a','b','semantic'),*,missing_reference=False,negative=False):
    manager=ReputationManager(prior_alpha=1.,prior_beta=1.)
    for name in names:
        if name!='semantic':manager.update_from_ground_truth(name,'general',True,not negative)
    caps={n:CapabilityDescriptor(('arithmetic',),requires_reference=(missing_reference and n=='semantic')) for n in names}
    selector=VerifierSelector(verifiers=[StubVerifier(n) for n in names],reputation_manager=manager,
        difficulty_range={'easy':(2,2),'hard':(2,2)},capabilities=caps)
    context=make_context(source=selector,minimum=2)
    resources=ResourceManifest(verifiers=tuple(dict(verifier_name=n,resources=tuple(dict(kind=k,resource_id=n+'-'+k,sha256='a'*64)
        for k in (('implementation','configuration','model') if n=='semantic' else ('implementation','configuration')))) for n in names))
    base=dict(coverage_version='factual_output_contract_v1',threshold=.55,failure_contract='all_selected_returned',
        execution_configuration_id=resources.manifest_id,resource_manifest=resources,history_prior_alpha=1.,history_prior_beta=1.)
    old=ExecutionContract(version='offline_public_decision_v2',contributor_version='baseline_log_odds_active_group_v1',**base)
    new=ExecutionContract(version='offline_public_decision_v3',contributor_version='informative_history_influence_v1',**base)
    return context,old,new


@pytest.mark.parametrize('aggregation',['reputation_weighted','dependency_group'])
def test_zero_reliability_cannot_satisfy_new_minimum(aggregation):
    context,old,new=counts_fixture()
    s=next(s for s in enumerate_strategies(context).strategies if s.verifiers==('a','semantic') and s.aggregation==aggregation)
    rows=[report(n) for n in s.verifiers];states=tuple((n,'directional') for n in s.verifiers)
    current=finalize_decision(context,s,new,rows,states,'synthetic')
    legacy=finalize_decision(context,s,old,rows,states,'synthetic')
    assert current.contributors==1 and current.public_status=='uncertain' and 'minimum_contributors' in current.reasons
    assert legacy.contributors==(2 if aggregation=='dependency_group' else 1)


@pytest.mark.parametrize('aggregation',['reputation_weighted','dependency_group'])
def test_informative_reports_consistent_and_guards_remain(aggregation):
    context,old,new=counts_fixture()
    s=next(s for s in enumerate_strategies(context).strategies if s.verifiers==('a','b') and s.aggregation==aggregation)
    states=tuple((n,'directional') for n in s.verifiers)
    valid=finalize_decision(context,s,new,[report(n) for n in s.verifiers],states,'synthetic')
    assert valid.contributors==2 and valid.public_status=='passed'
    uncovered=finalize_decision(context,s,new,[report(n,metadata={'decision':'SUPPORT'}) for n in s.verifiers],states,'synthetic')
    assert uncovered.contributors==2 and uncovered.public_status=='uncertain' and 'missing_achieved_coverage' in uncovered.reasons
    failed=finalize_decision(context,s,new,[report('a')],(('a','directional'),('b','failed')),'synthetic')
    assert failed.public_status=='uncertain' and 'selected_execution_incomplete' in failed.reasons
    zero=finalize_decision(context,s,new,[report('a',strength=0.),report('b')],states,'synthetic')
    assert zero.contributors==1


def test_prerequisite_and_negative_reputation_are_not_counted():
    context,old,new=counts_fixture(missing_reference=True)
    assert all('semantic' not in s.verifiers for s in enumerate_strategies(context).strategies)
    context,old,new=counts_fixture(negative=True)
    for s in enumerate_strategies(context).strategies:
        states=tuple((n,'directional') for n in s.verifiers)
        assert finalize_decision(context,s,new,[report(n) for n in s.verifiers],states,'synthetic').contributors==0


@pytest.mark.parametrize('aggregation',['reputation_weighted','dependency_group'])
def test_reliable_rejections_have_positive_influence_and_count(aggregation):
    c,old,new=counts_fixture()
    strategy=next(s for s in enumerate_strategies(c).strategies if s.verifiers==('a','b') and s.aggregation==aggregation)
    result=finalize_decision(c,strategy,new,[report(n,passed=False) for n in strategy.verifiers],
        tuple((n,'directional') for n in strategy.verifiers),'synthetic')
    assert result.contributors==2 and result.public_status=='failed'


@pytest.mark.parametrize('aggregation',['reputation_weighted','dependency_group'])
def test_structural_rule_is_not_an_informative_contributor(aggregation):
    c,old,new=counts_fixture(names=('a','rule'))
    s=next(s for s in enumerate_strategies(c).strategies if s.aggregation==aggregation)
    rows=[report('a'),report('rule',metadata={'decision':'SUPPORT','rule_kind':'structural','rule':'structural'})]
    result=finalize_decision(c,s,new,rows,(('a','directional'),('rule','directional')),'synthetic')
    assert result.contributors==1 and result.public_status=='uncertain'


def lex_matrix(*,minimum=.9,coverage=(1.,1.)):
    strategies=tuple(Strategy(strategy_id=content_id([(name,),'reputation_weighted']),verifiers=(name,),
        aggregation='reputation_weighted',estimated_cost=cost) for name,cost in [('cheap',1.),('reliable',100.)])
    base=PayoffMatrix(strategy_ids=tuple(s.strategy_id for s in strategies),strategy_definitions=strategies,
        attack_ids=('attack',),values=((.9,),(10.1,)),compatibility_id='synthetic')
    q=CleanCoverageConstraint(version='finalized_clean_development_coverage_v1',minimum=minimum,
        strategy_coverage=tuple(zip(base.strategy_ids,coverage)),parent_matrix_id=base.matrix_id,training_binding_id='a'*64,source_evaluation_id='b'*64)
    covered=PayoffMatrix(**{**base.model_dump(),'clean_coverage':q})
    objective=ReliabilityFirst(version='validation_then_attempt_cost_v1',epsilon=1e-8,cost_tolerance=1e-8,
        parent_matrix_id=covered.matrix_id,validation_values=((.8,),(.1,)))
    return PayoffMatrix(**{**covered.model_dump(),'reliability_first':objective})


def test_expensive_lower_loss_defeats_cheap_unreliable_with_both_coverage_feasible():
    matrix=lex_matrix();solution=solve_minimax(matrix)
    assert solution.status=='optimal',solution.message
    assert solution.probabilities[1][1]>=1-1e-8/.7-1e-12
    a=SolverResult.model_validate_json(solution.reliability_certificate.stage_a_json)
    assert a.game_value==pytest.approx(.1)
    assert solution.game_value<=.1+1e-8+1e-12
    assert solution.reliability_certificate.expected_cost>99.999
    assert validate_solution(matrix,SolverResult.model_validate_json(solution.model_dump_json()))==solution
    old=solve_minimax(PayoffMatrix(**{**matrix.model_dump(),'reliability_first':None}))
    assert old.probabilities[0][1]==1. # Same hard coverage, old objective chooses cheap errors.


def test_stage_b_cannot_buy_cost_by_exceeding_stage_a_cap():
    m=lex_matrix();s=solve_minimax(m);data=s.model_dump()
    data['probabilities']=((m.strategy_ids[0],.01),(m.strategy_ids[1],.99))
    with pytest.raises(ValueError,match='Stage A reliability cap'):validate_solution(m,SolverResult(**data))


@pytest.mark.parametrize('field',['cap','dual','cost','stage_a','basis'])
def test_lexicographic_certificate_tampering_rejected(field):
    m=lex_matrix();s=solve_minimax(m);data=s.model_dump();certificate=data['reliability_certificate']
    if field=='cap':certificate['reliability_cap']+=.1
    elif field=='dual':certificate['attack_multipliers']=(('attack',0.),)
    elif field=='cost':certificate['expected_cost']-=1.
    elif field=='basis':data['optimality_basis']='unverified'
    else:
        stage=json.loads(certificate['stage_a_json']);stage['game_value']+=.1;certificate['stage_a_json']=json.dumps(stage)
    with pytest.raises(ValueError):validate_solution(m,SolverResult(**data))


def test_infeasible_ninety_percent_never_relaxed():
    s=solve_minimax(lex_matrix(coverage=(.5,.8)))
    assert s.status=='infeasible' and not s.probabilities and s.reliability_certificate is None


def test_execution_version_cannot_silently_change_legacy_semantics():
    c,old,new=counts_fixture()
    with pytest.raises(ValueError):ExecutionContract(**{**old.model_dump(),'contributor_version':new.contributor_version})
    with pytest.raises(ValueError):ExecutionContract(**{**new.model_dump(),'contributor_version':old.contributor_version})


def full_fixture():
    """Synthetic independently labelled training-only records with positive history."""
    from tests.test_game_build import build_spec
    from tests.test_game_foundation import analysis
    from app.game.offline.records import TrainingManifest, history_reputation
    from app.game.models import capture_context
    from app.game.offline.replay import category_id
    from app.game.offline.evaluation import bind_evaluation, construct_payoffs
    s,_=build_spec(names=('a','b'));data=s.manifest.model_dump()
    resources=ResourceManifest(verifiers=tuple(dict(verifier_name=n,resources=tuple(dict(
        kind=k,resource_id=n+'-'+k,sha256='a'*64) for k in ('implementation','configuration'))) for n in ('a','b')))
    for partition in data['partitions']:
        for e in partition['examples']:
            e['execution_configuration_id']=resources.manifest_id
            for attempt in e['attempts']:
                attempt.update(configuration_id=resources.manifest_id,state='directional',report_json=report(attempt['verifier_name']).model_dump_json(),
                    observed_resources_json=next(r for r in resources.verifiers if r.verifier_name==attempt['verifier_name']).model_dump_json())
    manifest=TrainingManifest(**data);manager=history_reputation(manifest,prior_alpha=1.,prior_beta=1.)
    selector=VerifierSelector(verifiers=[StubVerifier(n) for n in ('a','b')],reputation_manager=manager,
        difficulty_range={'easy':(2,2),'hard':(2,2)},capabilities={n:CapabilityDescriptor(('arithmetic',)) for n in ('a','b')})
    config=s.context.model_dump();config.pop('selection_json');config.pop('analyzer_provenance')
    context=capture_context(selector,analysis(),**config)
    data=manifest.model_dump()
    for partition in data['partitions']:
        for e in partition['examples']:e['planning_category']=category_id(context)
    manifest=TrainingManifest(**data)
    contract=ExecutionContract(**{**s.contract.model_dump(),'version':'offline_public_decision_v3',
        'contributor_version':'informative_history_influence_v1','resource_manifest':resources,'execution_configuration_id':resources.manifest_id})
    context=bind_evaluation(context,manifest,contract,s.attacks)
    return context,manifest,contract,s.attacks,construct_payoffs(context,manifest,contract,s.attacks),selector


def test_full_export_reload_versions_and_runtime_parity_no_heldout_parser(monkeypatch):
    import random
    from app.game.offline.reliability import fit_reliability_first
    from app.game.offline.evaluation import export_artifact
    from app.game.offline.records import DatasetManifest, FinalTestReservation
    from app.game.artifacts import PolicyArtifact, InMemoryPolicyProvider, DeploymentEpisode
    from app.game.execution import GameRuntime
    from app.game.offline.replay import replay
    from app.game.offline.attacks import enumerate_attacks
    from app.models.schemas import ValidationRequest
    from tests.test_game_foundation import analysis
    from app.game.policy import validate_policy
    c,m,k,a,e,selector=full_fixture()
    def forbidden(*args,**kw):raise AssertionError('held-out parser accessed')
    monkeypatch.setattr(DatasetManifest,'model_validate',forbidden)
    monkeypatch.setattr(FinalTestReservation,'validate_payload',forbidden)
    bound,policy=fit_reliability_first(c,m,k,a,e)
    artifact=export_artifact(policy,bound,m,k,a,applicable_domain=bound.plan.domain)
    loaded=PolicyArtifact.model_validate_json(artifact.model_dump_json())
    assert loaded.version=='deployable_game_policy_reliability_first_v1'
    assert loaded.context.reputation_snapshot_id==c.reputation_snapshot_id
    with pytest.raises(ValueError):PolicyArtifact(**{**loaded.model_dump(),'version':'deployable_game_policy_v1'})
    with pytest.raises(ValueError):validate_policy(policy,c)
    class Observer:
        def snapshot(self):return k.resource_manifest
    dev=m.partition('development').examples[0]
    for verifier in selector._injected:
        verifier.verify=lambda *args, n=verifier.name,**kw:report(n)
    runtime=GameRuntime(InMemoryPolicyProvider((loaded,)),DeploymentEpisode(episode_id='synthetic',context=bound,contract=k,
        execution_configuration_id=k.execution_configuration_id),random.Random(42),allow_synthetic_for_tests=True,resource_observer=Observer())
    actual=runtime.run(selector,analysis(),ValidationRequest(question=dev.question,answer=dev.answer),dev.validation_id)
    strategy=next(s for s in policy.strategies if s.strategy_id==actual.summary['selected_strategy_id'])
    expected=replay(bound,strategy,enumerate_attacks(bound.dependencies,a)[0],a,k,dev)
    assert actual.summary['selection_status']=='selected' and actual.public_status==expected.public_status=='passed'
    assert actual.summary['contributors']==expected.contributors==2


def test_self_consistent_development_learned_reputation_still_rejected():
    from dataclasses import asdict
    from app.game.models import PlanningContext, canonical_json
    from app.game.offline.reliability import fit_reliability_first
    c,m,k,a,e,selector=full_fixture()
    raw=c.model_dump();plan=json.loads(raw['selection_json']);manager=ReputationManager(prior_alpha=1.,prior_beta=1.)
    manager.update_from_ground_truth('a','general',True,True);manager.update_from_ground_truth('a','general',True,True)
    stats=manager.statistics_batch((('a','general'),))[0]
    plan['reputation_statistics'][0]=asdict(stats)
    row=next(x for x in plan['candidates'] if x['verifier_name']=='a')
    row.update(reputation=round(stats.posterior_mean,6),observation_count=2,cold_start=False)
    altered=PlanningContext(**{**raw,'selection_json':canonical_json(plan)})
    with pytest.raises(ValueError,match='snapshot is not established'):fit_reliability_first(altered,m,k,a,e)


def test_bound_context_cannot_silently_use_other_contributor_semantics():
    c,m,k,a,e,selector=full_fixture()
    old=ExecutionContract(**{**k.model_dump(),'version':'offline_public_decision_v2','contributor_version':'baseline_log_odds_active_group_v1'})
    strategy=enumerate_strategies(c).strategies[0]
    with pytest.raises(ValueError,match='bound execution semantics'):
        finalize_decision(c,strategy,old,[report(n) for n in strategy.verifiers],
            tuple((n,'directional') for n in strategy.verifiers),'synthetic')
