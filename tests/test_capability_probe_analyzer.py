from dataclasses import asdict
import pytest
from app.analysis.task_analyzer import TaskQuestionAnalyzer
from app.analysis.capability_probe_analyzer import CapabilityProbeAnalyzer,question_profile,VERSION,COMPONENT_CONTRACT
from app.selection.requirements import requirement_inputs
from app.game.task_conditioning import analysis_task


@pytest.mark.parametrize('q',['What is 307 + 503?','What is the currency of Cuba?','Paraphrase this reference: Nora carried a box.'])
def test_existing_atomic_analysis_is_unchanged(q):
    assert asdict(CapabilityProbeAnalyzer().analyze(q))==asdict(TaskQuestionAnalyzer().analyze(q))


def test_rule_supported_wording_is_an_explicit_new_category():
    q='What is the difference between 25 and 17?'
    assert not requirement_inputs(TaskQuestionAnalyzer().analyze(q)).requirements_known
    a=CapabilityProbeAnalyzer().analyze(q)
    assert requirement_inputs(a).requirements==('arithmetic',)
    assert a.research_context.scoring_version==VERSION
    assert question_profile(q).input_supported
    assert analysis_task(a).question_rules_version==VERSION


def test_mixed_question_cannot_be_downgraded_to_only_a_fact():
    q='What is the population of Belgium, and what is that population plus 1000? Give both values.'
    assert requirement_inputs(TaskQuestionAnalyzer().analyze(q)).requirements==('direct_fact',)
    a=CapabilityProbeAnalyzer().analyze(q);r=requirement_inputs(a)
    assert set(r.requirements)=={'direct_fact','arithmetic'}
    assert r.unsupported==(COMPONENT_CONTRACT,)
    with pytest.raises(ValueError,match='supported known'):analysis_task(a)


def test_and_in_a_standalone_sum_does_not_make_it_compound():
    q='What is the sum of 25 and 17?'
    assert question_profile(q).category=='existing_atomic_or_unknown'
    assert asdict(CapabilityProbeAnalyzer().analyze(q))==asdict(TaskQuestionAnalyzer().analyze(q))


def test_capability_union_does_not_bypass_missing_component_contract():
    from tests.test_game_foundation import make_context
    from tests.test_verifier_selector import StubVerifier
    from app.selection.capabilities import CapabilityDescriptor
    from app.selection.verifier_selector import VerifierSelector
    from app.game.models import capture_context
    from app.game.strategies import enumerate_strategies
    caps={'rule':CapabilityDescriptor(('arithmetic',)),'evidence':CapabilityDescriptor(('direct_fact',))}
    c=make_context(names=('rule','evidence'),labels=('arithmetic','direct_fact'),capabilities=caps)
    selector=VerifierSelector(verifiers=[StubVerifier(n) for n in caps],capabilities=caps)
    a=CapabilityProbeAnalyzer().analyze('What is the area of Bahrain, and what is that area plus 10 square kilometres? Give both values.')
    context=capture_context(selector,a,context='The area of Bahrain is 765 square kilometres.',**c.model_dump(exclude={'selection_json','analyzer_provenance'}))
    result=enumerate_strategies(context)
    assert result.status=='no_feasible_strategy'
    assert any('unsupported_requirements' in r.reasons for r in result.rejected)


def test_new_mixed_profile_never_reaches_policy_provider():
    from app.game.task_conditioning import TaskPolicyRouter
    from app.models.schemas import ValidationRequest
    q='What is the population of Belgium, and what is that population plus 1000? Give both values.'
    a=CapabilityProbeAnalyzer().analyze(q)
    class Never:
        def snapshot(self):raise AssertionError('must not dispatch')
    result=TaskPolicyRouter(()).run(None,a,ValidationRequest(question=q,answer='two values',context='fixed reference'), 'synthetic',provider=Never(),rng=None,resource_observer=None)
    assert result.summary['selection_status']=='task_unknown'
