"""Explicitly synthetic three-outcome and reference prerequisite contracts."""
import pytest
from app.game.finalization import finalize_decision
from app.game.strategies import enumerate_strategies
from tests.test_game_reliability_first import counts_fixture
from tests.test_game_offline import report

@pytest.mark.parametrize('aggregation',['reputation_weighted','dependency_group'])
@pytest.mark.parametrize('case,expected',[
    ('positive','passed'),('negative','failed'),('conflict','uncertain'),
    ('no_coverage','uncertain'),('abstention','uncertain'),('failed_execution','uncertain')])
def test_three_outcomes_preserve_protections(aggregation,case,expected):
    context,_,contract=counts_fixture()
    strategy=next(s for s in enumerate_strategies(context).strategies if s.verifiers==('a','b') and s.aggregation==aggregation)
    rows=[report(n,passed=case!='negative') for n in strategy.verifiers]
    states=(('a','directional'),('b','directional'))
    if case=='conflict':rows[1]=report('b',passed=False)
    if case=='no_coverage':rows=[report(n,metadata={'decision':'SUPPORT'}) for n in strategy.verifiers]
    if case=='abstention':
        rows[1]=report('b',passed=False,metadata={'decision':'UNSURE'});states=(('a','directional'),('b','abstention'))
    if case=='failed_execution':rows=rows[:1];states=(('a','directional'),('b','failed'))
    actual=finalize_decision(context,strategy,contract,rows,states,'SYNTHETIC three-outcome fixture')
    assert actual.public_status==expected

@pytest.mark.parametrize('reference',[None,'','   ','support,reject'])
def test_missing_reference_does_not_construct_or_execute_semantic(monkeypatch,reference):
    import app.selection.verifier_selector as module
    from tests.test_game_foundation import analysis
    from app.reputation.reputation_manager import ReputationManager
    from app.selection.capabilities import BUILTIN_CAPABILITIES
    from app.selection.capabilities import prerequisite_status
    from tests.test_verifier_selector import StubVerifier
    made=[]
    def factory(name):
        assert name!='semantic','Semantic constructor must not be reached'
        made.append(name);return StubVerifier(name)
    monkeypatch.setattr(module,'_build_default_verifier',factory)
    manager=ReputationManager();selector=module.VerifierSelector(reputation_manager=manager)
    before=manager.statistics('semantic','general')
    plan=selector.plan(analysis(),context=reference)
    assert not plan.reference_available
    semantic=next(c for c in plan.candidates if c.verifier_name=='semantic')
    assert not semantic.eligible and semantic.prerequisite_status=='missing_reference'
    assert prerequisite_status(BUILTIN_CAPABILITIES['evidence'],reference)[1] is None
    for name in (*plan.initial_selected,*plan.fallback):
        verifier=selector.resolve(name)
        verifier.verify('SYNTHETIC question','SYNTHETIC answer',reference)
    assert 'semantic' not in made and manager.statistics('semantic','general')==before

def test_nonblank_availability_is_not_a_suitability_classifier():
    from app.selection.capabilities import BUILTIN_CAPABILITIES,prerequisite_status
    # Unrelated prose is available; no claim that it is relevant or sufficient.
    assert prerequisite_status(BUILTIN_CAPABILITIES['semantic'],'The sea is blue.')[1] is None

@pytest.mark.parametrize('factory',['project_factory','arithmetic_factory'])
def test_eager_factory_rejected_before_any_constructor(tmp_path,monkeypatch,factory):
    from tests.test_game_collection import fixture
    from app.game.offline.collect import main
    import app.game.offline.recording_adapters as adapters
    request,*_=fixture();data=request.model_dump(mode='json')
    data['factory']='app.game.offline.recording_adapters:'+factory
    # Fixture already has no reference; labels remain independently synthetic.
    for e in data['examples']:e['reference']=None
    import json
    path=tmp_path/'request.json';path.write_text(json.dumps(data))
    monkeypatch.setattr(adapters,factory,lambda:pytest.fail('eager constructor reached'))
    output=tmp_path/'collection'
    assert main(['collect',str(path),'--output-dir',str(output)])==2
    assert not output.exists()

def test_unavailable_and_abstaining_history_are_not_negative_observations():
    from tests.test_game_offline import fixture,change_example,attempt
    from app.game.offline.records import history_reputation
    c,m,k,a=fixture(names=('a','semantic'))
    for state in ('abstention','unavailable','failed'):
        execution=m.partition('history').examples[0].validation_id
        attempts=tuple(x.model_copy(update={'execution_id':execution}) for x in (attempt('a'),attempt('semantic',state=state)))
        changed=change_example(m,'history',attempts=attempts)
        manager=history_reputation(changed,prior_alpha=1.,prior_beta=1.)
        stats=manager.statistics('semantic',c.plan.domain)
        assert stats.observation_count==0 and stats.posterior_mean==.5
