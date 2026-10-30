"""Synthetic regression of the pilot's versioned contributor and finalization contracts."""
import pytest
from app.game.finalization import finalize_decision
from app.game.strategies import enumerate_strategies
from tests.test_dependency_aggregation import captured, report
from tests.test_game_offline import fixture


def setup(counts=None):
    snapshot,_=captured(counts or {'rule':(40,0),'semantic':(20,20)},names=('rule','semantic'))
    _,_,contract,_=fixture()
    return snapshot.context, contract


def finish(context,contract,aggregation,rows,states=None):
    strategy=next(s for s in enumerate_strategies(context).strategies if s.aggregation==aggregation)
    return finalize_decision(context,strategy,contract,rows,states or tuple((n,'directional') for n in strategy.verifiers),'synthetic')


@pytest.mark.parametrize('correct',[True,False])
def test_neutral_reputation_is_not_a_second_log_odds_contributor(correct):
    context,contract=setup()
    rows=[report('rule',1 if correct else 0,decision='SUPPORT' if correct else 'REJECT',rule_kind='factual',rule='arithmetic_addition'),report('semantic',.8)]
    rep=finish(context,contract,'reputation_weighted',rows)
    group=finish(context,contract,'dependency_group',rows)
    assert rep.detail.raw_score==pytest.approx(1 if correct else -1)
    assert rep.detail.status==('passed' if correct else 'failed')
    assert rep.public_status=='uncertain' and rep.reasons==('minimum_contributors',)
    assert rep.contributors==1 and rep.unresolved==()
    assert group.public_status==('passed' if correct else 'failed')
    assert group.contributors==2 and group.reasons==()


@pytest.mark.parametrize('aggregation',['reputation_weighted','dependency_group'])
def test_informative_two_contributor_case_is_decisive(aggregation):
    context,contract=setup({'rule':(40,0),'semantic':(30,10)})
    rows=[report('rule',1,rule_kind='factual',rule='arithmetic_addition'),report('semantic',.8)]
    assert finish(context,contract,aggregation,rows).public_status=='passed'


@pytest.mark.parametrize('aggregation',['reputation_weighted','dependency_group'])
@pytest.mark.parametrize('problem',['coverage','failed','unavailable','abstention'])
def test_real_protections_still_force_uncertainty(aggregation,problem):
    context,contract=setup({'rule':(40,0),'semantic':(30,10)})
    rows=[report('rule',1,rule_kind='factual',rule='arithmetic_addition'),report('semantic',.8)]
    strategy=next(s for s in enumerate_strategies(context).strategies if s.aggregation==aggregation)
    states={n:'directional' for n in strategy.verifiers}
    if problem=='coverage': rows[0]=report('rule',1,rule_kind='structural',rule='format')
    elif problem=='abstention':
        rows[1]=report('semantic',0,decision='UNSURE'); states['semantic']='abstention'
    else:
        rows=rows[:1]; states['semantic']=problem
    result=finish(context,contract,aggregation,rows,tuple((n,states[n]) for n in strategy.verifiers))
    assert result.public_status=='uncertain'
    assert ('missing_achieved_coverage' if problem=='coverage' else 'minimum_contributors') in result.reasons
    if problem in {'failed','unavailable'}: assert 'selected_execution_incomplete' in result.reasons
