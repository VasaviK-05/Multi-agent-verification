"""Synthetic LP and public replay/runtime regression checks, not study evidence."""
import json
import pytest
from app.game.models import PayoffMatrix, SolverResult, canonical_json
from app.game.coverage_contract import CleanCoverageConstraint
from app.game.solver import solve_minimax, validate_solution
from app.game.offline.coverage import fit_clean_coverage
from app.game.offline.evaluation import construct_payoffs, export_artifact
from app.game.artifacts import PolicyArtifact, DeploymentEpisode, InMemoryPolicyProvider
from app.game.policy import validate_policy
from tests.test_game_foundation import matrix
from tests.test_game_offline import fixture


def covered_matrix(minimum=.5,qs=(0.,1.)):
    original=matrix(values=((.2,.2),(0.,.5)))
    constraint=CleanCoverageConstraint(version='finalized_clean_development_coverage_v1',minimum=minimum,
        strategy_coverage=tuple(zip(original.strategy_ids,qs)),parent_matrix_id=original.matrix_id,
        training_binding_id='a'*64,source_evaluation_id='b'*64)
    return PayoffMatrix(**{**original.model_dump(),'clean_coverage':constraint})


@pytest.mark.parametrize('target',[.25,.5,.75,1.])
def test_analytic_coverage_solution_and_dual(target):
    m=covered_matrix(target);s=solve_minimax(m)
    assert s.status=='optimal'
    assert dict(s.probabilities)==pytest.approx({'first':1-target,'second':target})
    assert s.game_value==pytest.approx(.2+.3*target)
    assert s.coverage_certificate.achieved==pytest.approx(target)
    assert s.coverage_certificate.multiplier==pytest.approx(.3)
    assert s.primal_dual_gap==pytest.approx(0.)
    assert validate_solution(m,SolverResult.model_validate_json(s.model_dump_json()))==s


def test_infeasible_target_is_not_relaxed_or_published():
    m=covered_matrix(.75,qs=(0.,.5))
    s=solve_minimax(m)
    assert s.status=='infeasible' and not s.probabilities
    with pytest.raises(ValueError):validate_solution(m,s)


@pytest.mark.parametrize('field',['multiplier','achieved','residual','probabilities','basis'])
def test_tampered_certificate_rejected(field):
    m=covered_matrix();s=solve_minimax(m);data=s.model_dump()
    if field in {'multiplier','achieved','residual'}:data['coverage_certificate'][field]+=.1
    elif field=='probabilities':data['probabilities']=(('first',1.),('second',0.))
    else:data['optimality_basis']='highs_status_0_and_recomputed_primal_dual_certificate'
    with pytest.raises(ValueError):validate_solution(m,SolverResult(**data))


def source():
    from tests.test_game_build import build_spec
    from app.game.offline.evaluation import bind_evaluation
    s,_=build_spec(names=('a','b'))
    c=bind_evaluation(s.context,s.manifest,s.contract,s.attacks)
    return c,s.manifest,s.contract,s.attacks,construct_payoffs(c,s.manifest,s.contract,s.attacks)


def test_variant_export_versions_history_and_legacy_identity():
    c,m,k,a,e=source()
    before=c.model_dump_json()
    bound,policy=fit_clean_coverage(c,m,k,a,e,minimum=.5)
    artifact=export_artifact(policy,bound,m,k,a,applicable_domain=c.plan.domain)
    loaded=PolicyArtifact.model_validate_json(artifact.model_dump_json())
    assert loaded.version=='deployable_game_policy_clean_coverage_v1'
    assert loaded.policy.version=='game_policy_clean_coverage_v1'
    assert bound.reputation_snapshot_id==c.reputation_snapshot_id and c.model_dump_json()==before
    assert bound.compatibility_id!=c.compatibility_id
    assert len(policy.strategies)==len(e.matrix.strategy_ids)
    assert InMemoryPolicyProvider((loaded,)).snapshot()[0]==loaded
    with pytest.raises(ValueError):validate_policy(policy,c)
    with pytest.raises(ValueError):PolicyArtifact(**{**loaded.model_dump(),'version':'deployable_game_policy_v1'})
    with pytest.raises(ValueError):DeploymentEpisode(episode_id='bad',context=bound,contract=k,execution_configuration_id='wrong')
    assert 'clean_coverage_json' not in c.model_dump()
    assert 'clean_coverage' not in e.matrix.model_dump()
    legacy=solve_minimax(e.matrix)
    assert 'coverage_certificate' not in legacy.model_dump()
    assert validate_solution(e.matrix,legacy)==legacy


def test_zero_target_preserves_optimal_objective_and_infeasible_no_contributors():
    c,m,k,a,e=source()
    bound,p=fit_clean_coverage(c,m,k,a,e,minimum=0.)
    assert p.solution.game_value==pytest.approx(solve_minimax(e.matrix).game_value)
    from app.game.offline.evaluation import bind_evaluation
    from app.game.offline.records import TrainingManifest
    from tests.test_game_offline import unbind, report
    data=m.model_dump()
    for part in data['partitions']:
        if part['role']=='development':
            for row in part['examples'][0]['attempts']:
                row.update(state='abstention',report_json=report(row['verifier_name'],metadata={'decision':'UNSURE'}).model_dump_json())
    m=TrainingManifest(**data);c=bind_evaluation(unbind(c),m,k,a)
    e=construct_payoffs(c,m,k,a)
    with pytest.raises(ValueError,match='coverage target'):
        fit_clean_coverage(c,m,k,a,e,minimum=.25)


def test_fitting_contract_cannot_accept_final_payload_and_coverage_is_not_a_guard_override():
    c,m,k,a=fixture(names=('a','b'))
    with pytest.raises(ValueError):fit_clean_coverage(c,m,k,a,construct_payoffs(c,m,k,a),minimum=.5)
    c,m,k,a,e=source()
    bound,p=fit_clean_coverage(c,m,k,a,e,minimum=.5)
    from app.game.offline.replay import replay
    from app.game.offline.attacks import enumerate_attacks
    suppressed=enumerate_attacks(bound.dependencies,a)[-1]
    result=replay(bound,p.strategies[0],suppressed,a,k,m.partition('development').examples[0])
    assert result.public_status=='uncertain'
    assert 'selected_execution_incomplete' in result.reasons
    assert 'missing_achieved_coverage' in result.reasons


def test_fitter_never_calls_heldout_payload_validation(monkeypatch):
    from app.game.offline.records import DatasetManifest, FinalTestReservation
    c,m,k,a,e=source()
    def forbidden(*args,**kw):raise AssertionError('held-out payload touched during coverage fitting')
    monkeypatch.setattr(DatasetManifest,'model_validate',forbidden)
    monkeypatch.setattr(FinalTestReservation,'validate_payload',forbidden)
    bound,p=fit_clean_coverage(c,m,k,a,e,minimum=.5)
    assert p.solution.coverage_certificate.achieved>=.5


@pytest.mark.parametrize('bad',[True,-.1,1.1,float('nan')])
def test_invalid_targets_rejected(bad):
    with pytest.raises(ValueError):covered_matrix(bad)


def test_constraint_axes_and_parent_payoff_binding_cannot_be_changed():
    c,m,k,a,e=source()
    bound,p=fit_clean_coverage(c,m,k,a,e,minimum=.5)
    data=p.model_dump()
    data['matrix']['values']=[list(row) for row in data['matrix']['values']]
    data['matrix']['values'][0][0]+=.1
    with pytest.raises(ValueError,match='original development payoffs'):
        validate_policy(data,bound)
    raw=p.matrix.model_dump();constraint=raw['clean_coverage']
    constraint['strategy_coverage']=tuple(reversed(constraint['strategy_coverage']))
    with pytest.raises(ValueError,match='axes'):PayoffMatrix(**raw)


@pytest.mark.parametrize('tamper',['truth','missing','duplicate','payoff','history','finalized_trace','missing_definitions'])
def test_bad_source_or_development_reputation_rejected(tamper):
    from app.game.offline.evaluation import Evaluation
    c,m,k,a,e=source();data=e.model_dump()
    if tamper=='truth':data['outcomes'][0]['answer_is_correct']=False
    elif tamper=='missing_definitions':data['matrix']['strategy_definitions']=()
    elif tamper=='finalized_trace':data['outcomes'][0]['numerical_score']-=.1
    elif tamper=='missing':data['outcomes']=data['outcomes'][1:]
    elif tamper=='duplicate':data['outcomes']=(*data['outcomes'],data['outcomes'][0])
    elif tamper=='payoff':
        rows=[list(row) for row in data['matrix']['values']];rows[0][0]+=.1;data['matrix']['values']=rows
    else:
        from dataclasses import asdict
        from app.game.models import PlanningContext
        from app.reputation.reputation_manager import ReputationManager
        # A self-consistent posterior learned from development must still fail
        # the independent history binding, not merely schema arithmetic checks.
        manager=ReputationManager(prior_alpha=1.,prior_beta=1.)
        raw=c.model_dump();plan=json.loads(raw['selection_json'])
        name=plan['reputation_statistics'][0]['verifier_name']
        manager.update_from_ground_truth(name,c.plan.domain,True,True)
        stats=manager.statistics_batch(((name,c.plan.domain),))[0]
        plan['reputation_statistics'][0]=asdict(stats)
        candidate=next(row for row in plan['candidates'] if row['verifier_name']==name)
        candidate.update(reputation=round(stats.posterior_mean,6),observation_count=stats.observation_count,cold_start=stats.cold_start)
        raw['selection_json']=canonical_json(plan)
        altered=PlanningContext(**raw)
        with pytest.raises(ValueError,match='snapshot is not established'):
            fit_clean_coverage(altered,m,k,a,e,minimum=.5)
        return
    with pytest.raises(ValueError):fit_clean_coverage(c,m,k,a,Evaluation(**data),minimum=.5)
