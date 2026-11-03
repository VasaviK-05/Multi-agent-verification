"""Opt-in team minima preserve legacy contracts and full-team finalization."""
import pytest
from app.game.execution_contract import ExecutionContract, TeamRequirements
from app.game.models import PlanningContext
from app.game.finalization import finalize_decision
from app.game.strategies import enumerate_strategies
from tests.test_game_reliability_first import counts_fixture
from tests.test_game_offline import report


def configured(selected=1, informative=1, **kwargs):
    c, old, k = counts_fixture(**kwargs)
    k=ExecutionContract(**{**k.model_dump(), 'team_requirements':TeamRequirements(minimum_selected=selected,minimum_informative=informative)})
    return PlanningContext(**{**c.model_dump(),'execution_contract_json':k.model_dump_json()}), k


@pytest.mark.parametrize('aggregation',['reputation_weighted','dependency_group'])
def test_singleton_and_separate_minima(aggregation):
    c,k=configured()
    s=next(s for s in enumerate_strategies(c).strategies if s.verifiers==('a',) and s.aggregation==aggregation)
    def run(rows,states=(('a','directional'),)):
        return finalize_decision(c,s,k,rows,states,'synthetic')
    assert run([report('a')]).public_status=='passed'
    assert run([report('a',passed=False)]).public_status=='failed'
    assert 'decision_threshold' in run([report('a',strength=.3)]).reasons
    assert run([], (('a','unavailable'),)).public_status=='uncertain'
    abstain=run([report('a',metadata={'decision':'UNSURE'})],(('a','abstention'),))
    assert abstain.contributors==0 and abstain.public_status=='uncertain'
    assert 'missing_achieved_coverage' in run([report('a',metadata={'decision':'SUPPORT'})]).reasons
    c2,k2=configured(informative=2)
    assert finalize_decision(c2,s,k2,[report('a')],(('a','directional'),),'synthetic').public_status=='uncertain'
    neutral=next(s for s in enumerate_strategies(c).strategies if s.verifiers==('semantic',) and s.aggregation==aggregation)
    r=finalize_decision(c,neutral,k,[report('semantic')],(('semantic','directional'),),'synthetic')
    assert r.contributors==0 and r.public_status=='uncertain'


def test_enumeration_budget_prerequisites_and_legacy_identity():
    legacy,old,new=counts_fixture()
    assert 'team_requirements' not in new.model_dump()
    assert all(len(s.verifiers)>=2 for s in enumerate_strategies(legacy).strategies)
    c,k=configured(names=('a','b','c','d'))
    assert {len(s.verifiers) for s in enumerate_strategies(c).strategies}=={1,2,3,4}
    limited=PlanningContext(**{**c.model_dump(),'budget':0.})
    assert any('budget' in r.reasons for r in enumerate_strategies(limited).rejected)
    c,k=configured(missing_reference=True)
    assert all('semantic' not in s.verifiers for s in enumerate_strategies(c).strategies)
    assert ('semantic','reference context is absent') in enumerate_strategies(c).exclusions
    s=enumerate_strategies(c).strategies[0]
    with pytest.raises(ValueError,match='contract differs'):
        finalize_decision(c,s,new,[],tuple((n,'unavailable') for n in s.verifiers),'synthetic')
    with pytest.raises(ValueError): TeamRequirements(minimum_selected=True,minimum_informative=1)


def test_conflicting_team_does_not_automatically_accept():
    c,k=configured()
    s=next(s for s in enumerate_strategies(c).strategies if s.verifiers==('a','b') and s.aggregation=='reputation_weighted')
    r=finalize_decision(c,s,k,[report('a'),report('b',passed=False)],(('a','directional'),('b','directional')),'synthetic')
    assert r.public_status=='uncertain' and 'decision_threshold' in r.reasons


def test_capability_exclusions_and_contract_identities():
    import json
    c,k=configured()
    data=c.model_dump();plan=json.loads(data['selection_json'])
    plan['candidates'][0]['expected_capabilities']=[]
    data['selection_json']=json.dumps(plan)
    altered=PlanningContext(**data)
    assert any('expected_coverage' in r.reasons for r in enumerate_strategies(altered).rejected)
    two,k2=configured(selected=2,informative=2)
    assert c.compatibility_id!=two.compatibility_id
    from app.game.offline.replay import category_id
    assert category_id(c)==category_id(two) # Same full-roster recordings, distinct policies.
    with pytest.raises(ValueError,match='must be bound'):
        legacy,_,_=counts_fixture()
        s=enumerate_strategies(legacy).strategies[0]
        finalize_decision(legacy,s,k,[],tuple((n,'unavailable') for n in s.verifiers),'synthetic')


def test_explicit_minimum_does_not_enable_prefix_finalization():
    c,k=configured()
    s=next(s for s in enumerate_strategies(c).strategies if s.verifiers==('a','b') and s.aggregation=='reputation_weighted')
    with pytest.raises(ValueError,match='complete selected team'):
        finalize_decision(c,s,k,[report('a')],(('a','directional'),),'synthetic')
    r=finalize_decision(c,s,k,[report('a')],(('a','directional'),('b','failed')),'synthetic')
    assert r.public_status=='uncertain' and 'selected_execution_incomplete' in r.reasons


def test_non_game_stopping_floor_remains_separate():
    from app.decision.early_termination import AdaptiveEarlyTermination
    from app.decision.decision_engine import DecisionEngine
    from app.reputation.reputation_manager import ReputationManager
    from tests.test_game_foundation import analysis
    manager=ReputationManager()
    manager.update_from_ground_truth('a','general',True,True)
    assessment=AdaptiveEarlyTermination().should_terminate([report('a')],analysis(),min_verifiers=1,decision_engine=DecisionEngine(manager))
    assert not assessment['terminate'] and 'minimum 2' in assessment['reason']
