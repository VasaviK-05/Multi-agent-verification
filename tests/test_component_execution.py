"""Synthetic software fixtures only; no empirical compound performance claims."""
import json
import random
from pathlib import Path
from types import SimpleNamespace
import pytest

from app.game.component_binding import question_plan, bind_answer, BindingError
from app.game.component_execution import (ComponentContract, ComponentPolicy,
    enumerate_component_strategies, run_component_diagnostic, run_component_policy)
from app.game.question_routing import QuestionPolicyConfiguration, classify_question
from app.game.models import PlanningContext, PayoffMatrix
from app.game.policy import Policy, validate_policy
from app.game.solver import solve_minimax
from app.game.artifacts import DeploymentEpisode, InMemoryPolicyProvider
from app.game.task_conditioning import TaskSnapshotBinding
from app.models.schemas import VerificationResult
from app.selection.verifier_selector import VerifierSelector
from app.selection.capabilities import BUILTIN_CAPABILITIES
from app.verifiers.rule_verifier import RuleVerifier
from tests.test_verifier_selector import StubVerifier
from scripts.component_scenarios import diagnostic_contract

Q = 'What is the area of Bahrain, and what is that area plus 10 square kilometres? Give both values.'
REF = 'The area of Bahrain is 765 square kilometres.'
ROOT = Path(__file__).resolve().parents[1]


def bases():
    return {kind: json.loads((ROOT/f'artifacts/flexible-teams-v1/{kind}-minimum-1/context.json').read_text())
        for kind in ('factual', 'arithmetic')}


class SyntheticVerifier(StubVerifier):
    def __init__(self, name, calls, mode=None):
        super().__init__(name); self.calls = calls; self.mode = mode

    def verify(self, question, answer, context=None):
        self.calls.append((self.name, question, answer))
        if self.mode == 'failure':
            from app.game.execution import VerifierExecutionFailure
            raise VerifierExecutionFailure('synthetic failure')
        if self.name == 'rule':
            return RuleVerifier().verify(question, answer, context)
        passed = 'is 765 square' in answer if self.name == 'evidence' else True
        decision = 'SUPPORT' if passed else 'REJECT'
        label = 'entailment' if passed else 'contradiction'
        return VerificationResult(verifier_name=self.name, passed=passed, score=1.,
            reasoning='synthetic test fixture', metadata=dict(decision=decision,
                nli_label=label, unsure_reason=None,
                supporting=[{'nli_label':label}] if passed else [],
                contradicting=[] if passed else [{'nli_label':label}],
                claim_decisions=[{'decision':decision}]))


def setup(mode=None):
    calls = []
    verifiers = [SyntheticVerifier(n, calls, mode if n == 'evidence' else None)
        for n in ('confidence', 'evidence', 'rule', 'semantic')]
    contract = diagnostic_contract(Q, REF, bases(), verifiers)
    selector = VerifierSelector(verifiers=verifiers, capabilities=BUILTIN_CAPABILITIES)
    observer = SimpleNamespace(snapshot=lambda:contract.obligations[0].contract.resource_manifest)
    strategies = enumerate_component_strategies(contract)
    strategy = next(s for s in strategies if tuple(a.verifiers for _, a in s.components) == (('evidence',), ('rule',))
        and s.components[0][1].aggregation == 'reputation_weighted')
    return contract, strategy, selector, observer, calls


@pytest.mark.parametrize('base,derived,status', [('765','775','passed'), ('765','774','failed'),
    ('766','776','failed'), ('766','775','failed')])
def test_component_correctness_and_complete_execution(base, derived, status):
    c,s,selector,observer,calls = setup()
    run = run_component_diagnostic(c,s,selector,Q,json.dumps(dict(base=base,derived=derived)),REF,'test',resource_observer=observer)
    assert run.public_status == status
    assert len(calls) == 2
    assert calls[1][1] == f'What is {base} + 10?'
    assert run.summary['components'][1]['depends_on'] == ['base_fact']
    assert run.summary['contributors'] == ['evidence','rule']
    assert len({a['validation_id'] for a in run.summary['attempts']}) == 2
    assert all(a['report']['metadata']['binding_id'] == a['binding_id'] for a in run.summary['attempts'])
    assert run.summary['estimated_attempted_cost'] == s.estimated_cost


@pytest.mark.parametrize('answer', ['{}','{"base":"765"}', '{"base":"765","base":"766","derived":"776"}',
    '{"base":765,"derived":775}', '{"base":"NaN","derived":"775"}',
    '{"base":"765","derived":"775","extra":"x"}', '765 / 775',
    '{"base":"1e3","derived":"1010"}', '{"base":true,"derived":"775"}'])
def test_invalid_answer_has_no_dispatch(answer):
    c,s,selector,observer,calls = setup()
    run = run_component_diagnostic(c,s,selector,Q,answer,REF,'test',resource_observer=observer)
    assert run.public_status == 'uncertain' and not calls
    assert run.summary['termination'] == 'before_dispatch'


def test_unsupported_operation_and_units():
    for q in (Q.replace('plus','times'), Q.replace('square kilometres','people'), Q.replace('that area','that population'),
              Q.replace('Bahrain','Cuba'), Q.replace('plus 10','plus 20')):
        with pytest.raises(BindingError): question_plan(q)
        assert QuestionPolicyConfiguration().router().resolve(q,REF)[0] == 'unsupported_category'


def test_failure_resource_checks_and_unrelated_support():
    c,s,selector,observer,calls = setup('failure')
    run = run_component_diagnostic(c,s,selector,Q,'{"base":"765","derived":"775"}',REF,'test',resource_observer=observer)
    assert run.public_status == 'uncertain' and len(calls) == 2
    assert run.summary['attempts'][0]['state'] == 'failed'
    calls.clear()
    run = run_component_diagnostic(c,s,selector,Q,'{"base":"765","derived":"775"}',REF,'test',resource_observer=None)
    assert run.public_status == 'uncertain' and not calls


def test_repeated_verifier_cost_and_distinct_contributors():
    c,_,selector,observer,calls = setup()
    s = next(s for s in enumerate_component_strategies(c)
        if tuple(a.verifiers for _,a in s.components) == (('confidence','evidence'),('confidence','rule'))
        and s.components[0][1].aggregation == 'reputation_weighted')
    costs = dict(c.obligations[0].context.attempt_costs)
    arithmetic_costs = dict(c.obligations[1].context.attempt_costs)
    assert s.estimated_cost == pytest.approx(costs['evidence']+arithmetic_costs['rule']+costs['confidence']+arithmetic_costs['confidence'])
    assert len(s.verifiers) == 3
    run = run_component_diagnostic(c,s,selector,Q,'{"base":"765","derived":"775"}',REF,'test',resource_observer=observer)
    assert len(calls) == 4 and run.summary['contributor_count'] <= 3
    limited = ComponentContract(**{**c.model_dump(), 'budget':s.estimated_cost-.01})
    assert not any(t.components == s.components for t in enumerate_component_strategies(limited))


def synthetic_policy(c, target):
    strategies = enumerate_component_strategies(c)
    matrix = PayoffMatrix(compatibility_id=c.compatibility_id,
        strategy_ids=tuple(s.strategy_id for s in strategies), attack_ids=('synthetic_joint_failure',),
        values=tuple((0. if s == target else 1.,) for s in strategies))
    return ComponentPolicy(contract=c,matrix=matrix,solution=solve_minimax(matrix),
        evidence_kind='synthetic_test_fixture',joint_evidence_id='SYNTHETIC software fixture only')


@pytest.mark.parametrize('size',[2,3])
def test_joint_policy_sampling_and_category_registry(size):
    c,pair,selector,observer,calls = setup()
    target = pair if size == 2 else next(s for s in enumerate_component_strategies(c)
        if s.verifiers == ('confidence','evidence','rule'))
    policy = synthetic_policy(c,target)
    router = QuestionPolicyConfiguration(component_entries=((c.question_signature,c.budget,True,policy),)).router()
    request = SimpleNamespace(question=Q,answer='{"base":"765","derived":"775"}',context=REF)
    blocked = router.run(selector,request,'test',provider=InMemoryPolicyProvider(),rng=random.Random(0),resource_observer=observer)
    assert blocked.public_status == 'uncertain' and not calls
    run = router.run(selector,request,'test',provider=InMemoryPolicyProvider(),rng=random.Random(0),resource_observer=observer,allow_synthetic_for_tests=True)
    assert run.summary['selected_strategy_id'] == target.strategy_id
    assert len(run.summary['team']) == size
    assert run.summary['execution_mode'] == 'synthetic_policy_test'
    assert run.summary['selection_status'] == 'selected'


def test_policy_preflight_precedes_sampling_and_returns_component_reports():
    c, target, selector, _, calls = setup()
    policy = synthetic_policy(c, target)
    events = []
    expected = c.obligations[0].contract.resource_manifest
    observer = SimpleNamespace(snapshot=lambda: events.append('snapshot') or expected)

    class TrackingRng:
        def random(self):
            events.append('sample')
            return 0.0

    request = SimpleNamespace(question=Q, answer='{"base":"765","derived":"775"}', context=REF)
    run = QuestionPolicyConfiguration(component_entries=((c.question_signature,c.budget,True,policy),)).router().run(
        selector, request, 'test', provider=InMemoryPolicyProvider(), rng=TrackingRng(),
        resource_observer=observer, allow_synthetic_for_tests=True)
    assert run.summary['execution_mode'] == 'synthetic_policy_test'
    assert run.results and run.detail is None
    assert events[0] == 'snapshot' and events.index('snapshot') < events.index('sample')
    assert len(calls) == len(run.summary['attempts'])


def test_policy_resource_mismatch_does_not_sample_or_dispatch():
    c, target, selector, _, calls = setup()
    policy = synthetic_policy(c, target)
    events = []
    expected = c.obligations[0].contract.resource_manifest
    verifiers = list(expected.verifiers)
    resources = list(verifiers[0].resources)
    resources[0] = resources[0].model_copy(update={'sha256': 'f' * 64})
    verifiers[0] = verifiers[0].model_copy(update={'resources': tuple(resources)})
    changed = expected.model_copy(update={'verifiers': tuple(verifiers)})

    class TrackingRng:
        def random(self):
            events.append('sample')
            return 0.0

    request = SimpleNamespace(question=Q, answer='{"base":"765","derived":"775"}', context=REF)
    run = QuestionPolicyConfiguration(component_entries=((c.question_signature,c.budget,True,policy),)).router().run(
        selector, request, 'test', provider=InMemoryPolicyProvider(), rng=TrackingRng(),
        resource_observer=SimpleNamespace(snapshot=lambda: changed), allow_synthetic_for_tests=True)
    assert run.public_status == 'uncertain'
    assert run.summary['selection_status'] == 'resource_incompatible'
    assert not events and not calls


def test_real_atomic_routes_and_old_policy_identity():
    routes = []
    ids = []
    frozen=json.loads((ROOT/'artifacts/remaining-category-studies-v1/atomic-public-identities.json').read_text())
    for family in ('arithmetic','factual'):
        path = ROOT/f'artifacts/flexible-teams-v1/{family}-minimum-1'
        context = PlanningContext.model_validate_json((path/'context.json').read_text())
        contract = __import__('app.game.execution_contract',fromlist=['ExecutionContract']).ExecutionContract.model_validate_json((path/'contract.json').read_text())
        policy = Policy.model_validate_json((path/'policy.json').read_text())
        assert validate_policy(policy,context).policy_id == policy.policy_id
        expected=next(c for c in frozen['candidates'] if c['cohort']==family)
        assert policy.policy_id==expected['policy_id']
        assert context.compatibility_id==expected['context_id']
        binding = TaskSnapshotBinding.model_validate_json(context.task_conditioning_json)
        plan = context.plan
        sig=(binding.identity.task_id,plan.difficulty,plan.difficulty_score,plan.reference_available)
        episode=DeploymentEpisode(episode_id=family,context=context,contract=contract,execution_configuration_id=contract.execution_configuration_id)
        routes.append((sig,context.budget,True,episode,'')); ids.append(policy.policy_id)
        c,_,selector,observer,calls=setup()
        blocked=run_component_policy(policy,selector,Q,'{"base":"765","derived":"775"}',REF,'test',rng=random.Random(0),resource_observer=observer)
        assert blocked.public_status=='uncertain' and not calls
    router=QuestionPolicyConfiguration(atomic_routes=tuple(routes)).router()
    # Actual stored development questions provide compatible signature examples.
    for route in routes:
        assert router.tasks.resolve(route[0])[3] == route[3]
    assert ids[0] != ids[1]
    assert router.resolve(Q,REF)[0]=='missing_policy'
    assert classify_question('What is 765 + 10?',REF)[0]=='atomic'
    assert QuestionPolicyConfiguration(allowlist=frozenset()).router().resolve(Q,REF)[0]=='unsupported_category'


def test_resource_drift_and_bound_report_identity():
    c,s,selector,observer,calls=setup()
    snapshots=iter((c.obligations[0].contract.resource_manifest,{}))
    drift=SimpleNamespace(snapshot=lambda:next(snapshots))
    run=run_component_diagnostic(c,s,selector,Q,'{"base":"765","derived":"775"}',REF,'test',resource_observer=drift)
    assert len(calls)==2 and run.public_status=='uncertain'
    assert 'resource_provenance_changed_during_execution' in run.summary['override_reasons']
    evidence=selector.resolve('evidence'); original=evidence.verify
    def wrong_identity(*args):
        row=original(*args);row.metadata['validation_id']='another-request';return row
    evidence.verify=wrong_identity
    with pytest.raises(ValueError,match='validation_id differs'):
        run_component_diagnostic(c,s,selector,Q,'{"base":"765","derived":"775"}',REF,'test',resource_observer=observer)


def test_compound_provenance_is_not_an_atomic_or_fixture_relabel():
    c,s,_,_,_=setup()
    policy=synthetic_policy(c,s)
    with pytest.raises(ValueError,match='separately sealed joint'):
        ComponentPolicy(**{**policy.model_dump(),'evidence_kind':'empirical'})
    other=ComponentContract(**{**c.model_dump(),'minimum_distinct_contributors':2})
    assert c.compatibility_id!=other.compatibility_id
    assert {x.strategy_id for x in enumerate_component_strategies(c)}.isdisjoint(
        {x.strategy_id for x in enumerate_component_strategies(other)})


def test_missing_category_does_not_dispatch_or_use_answer():
    _,_,selector,observer,calls=setup()
    router=QuestionPolicyConfiguration().router()
    for answer in ('{"base":"765","derived":"775"}','{"base":"766","derived":"776"}'):
        request=SimpleNamespace(question=Q,answer=answer,context=REF)
        result=router.run(selector,request,'test',provider=InMemoryPolicyProvider(),rng=random.Random(0),resource_observer=observer)
        assert result.summary['selection_status']=='missing_policy'
    assert not calls


@pytest.mark.parametrize('abstain',[True,False])
def test_unavailable_component_coverage_cannot_be_certified_by_arithmetic(abstain):
    c,s,selector,observer,calls=setup()
    evidence=selector.resolve('evidence'); original=evidence.verify
    def incomplete(*args):
        row=original(*args)
        row.metadata={'decision':'UNSURE' if abstain else 'SUPPORT'}
        return row
    evidence.verify=incomplete
    result=run_component_diagnostic(c,s,selector,Q,'{"base":"765","derived":"775"}',REF,'test',resource_observer=observer)
    assert result.public_status=='uncertain' and len(calls)==2
    assert result.summary['components'][0]['unresolved']==['direct_fact']
    assert result.summary['components'][1]['public_status']=='passed'


def test_active_resource_observer_receives_actual_selector():
    c,s,selector,_,_=setup()
    seen=[]
    def snapshot_for(current):
        seen.append(current)
        return c.obligations[0].contract.resource_manifest
    observer=SimpleNamespace(snapshot_for=snapshot_for)
    result=run_component_diagnostic(c,s,selector,Q,'{"base":"765","derived":"775"}',REF,'test',resource_observer=observer)
    assert result.public_status=='passed' and seen==[selector,selector]
