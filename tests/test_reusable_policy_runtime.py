"""Real frozen minimax artifact, fresh mock calls. No native/retained-report replay."""
from types import SimpleNamespace
import math
import pytest
from app.game.reusable_policy import ReusablePolicyScope, ReusablePolicyGameRuntime
from app.game.category_deployment import create_category_game_runtime
from app.game.deployment import FlexiblePolicyGameRuntime
from app.game.resource_provenance import ResourceManifest
from app.models.schemas import VerificationResult, ValidationRequest
from app.selection.verifier_selector import VerifierSelector
from app.selection.capabilities import BUILTIN_CAPABILITIES
from app.verifiers.base_verifier import BaseVerifier
from scripts.reconciliation import load_bundle


class FreshChecker(BaseVerifier):
    def __init__(self,name,calls):self._name,self.calls=name,calls
    @property
    def name(self):return self._name
    def verify(self,question,answer,context=None):
        self.calls.append((self.name,question,answer,context))
        if self.name!='rule':raise AssertionError('Frozen probability-one strategy changed')
        # Fixed test truths; no copied development report or Rule algorithm.
        expected={'What is 328 + 536?':'864','What is 4 + 4?':'8','Calculate 4 + 4.':'8'}
        passed=answer==expected[question]
        return VerificationResult(verifier_name='rule',passed=passed,score=float(passed),
            metadata=dict(decision='SUPPORT' if passed else 'REJECT',rule_kind='factual',rule='arithmetic_addition',
                mock_fresh_question=question,mock_fresh_answer=answer))


def setup(monkeypatch,draw=.5):
    configuration,provider,_=load_bundle();artifact=provider.snapshot()[0]; calls=[]
    selector=VerifierSelector(verifiers=[FreshChecker(c.verifier_name,calls) for c in artifact.context.plan.candidates],
        capabilities=BUILTIN_CAPABILITIES)
    observer=SimpleNamespace(snapshot_for=lambda actual:artifact.contract.resource_manifest)
    scope=ReusablePolicyScope(artifact_id=artifact.artifact_id,compatibility_id=artifact.context.compatibility_id,
        question_pattern=r'.+',maximum_question_chars=200,question_rules_version='explicit_task_questions_v1',
        review_basis='TEST ONLY: task/context compatibility; no new empirical certification')
    reuse=ReusablePolicyGameRuntime([artifact],[scope],rng=SimpleNamespace(random=lambda:draw),resource_observer=observer)
    # Real legacy router/dispatcher, with native construction seam mocked. Full
    # resource equality is checked by GameRuntime against explicit fixture data.
    import app.game.offline.singleton_compatibility as singleton
    legacy=object.__new__(FlexiblePolicyGameRuntime)
    legacy._configuration,legacy._provider=configuration,provider
    legacy._router=configuration.router();legacy._rng=SimpleNamespace(random=lambda:draw)
    legacy._bundle_id='TEST-ONLY';legacy._adapter_for=lambda route:object()
    monkeypatch.setattr(singleton,'create_singleton',lambda config,actual:(selector,observer))
    adapter=create_category_game_runtime(legacy,reuse)
    return SimpleNamespace(artifact=artifact,provider=provider,selector=selector,observer=observer,
        reuse=reuse,adapter=adapter,calls=calls,configuration=configuration)


@pytest.mark.parametrize('draw',[0.,.5,math.nextafter(1.,0.)])
def test_seen_and_unseen_use_identical_existing_fitted_policy_and_live_inputs(monkeypatch,draw):
    f=setup(monkeypatch,draw); artifact=f.artifact; before=artifact.model_dump_json()
    outcomes=[]
    for question,answer in [('What is 328 + 536?','864'),('What is 4 + 4?','8'),('What is 4 + 4?','9'),('Calculate 4 + 4.','8')]:
        request=ValidationRequest(question=question,answer=answer,context=answer)
        outcomes.append(f.adapter.run(f.selector,None,request,'SYNTHETIC-fresh'))
    assert 'What is 4 + 4?' not in f.configuration.allowlist
    assert all(r.summary['selection_status']=='selected' for r in outcomes)
    assert [r.public_status for r in outcomes]==['passed','passed','failed','passed']
    assert all(r.summary['policy_id']==artifact.policy.policy_id for r in outcomes)
    assert all(r.summary['artifact_id']==artifact.artifact_id for r in outcomes)
    assert all(r.summary['selected_strategy_id']==outcomes[0].summary['selected_strategy_id'] for r in outcomes)
    assert artifact.model_dump_json()==before
    assert f.reuse._provider.snapshot()[0].policy.version==artifact.policy.version
    assert f.reuse._provider.snapshot()[0].policy.solution.probabilities==artifact.policy.solution.probabilities
    assert f.calls==[('rule','What is 328 + 536?','864','864'),('rule','What is 4 + 4?','8','8'),
        ('rule','What is 4 + 4?','9','9'),('rule','Calculate 4 + 4.','8','8')]
    resolved,failed=f.reuse.resolve('Calculate 4 + 4.','8')
    assert failed is None and resolved[3].difficulty_score!=artifact.context.plan.difficulty_score
    assert outcomes[1].summary['fitted_compatibility_id']==artifact.context.compatibility_id
    assert all(r.summary['fallback_enabled'] is False and r.summary['early_stopping_enabled'] is False for r in outcomes)


@pytest.mark.parametrize('question,context',[('What is the capital of France?','Paris'),
    ('What is 4 + 4?',None),('What is 4 ** 4?','256'),
    ('What is 4 + 4?','support,reject')])
def test_genuinely_incompatible_obligations_reference_or_parser_rejected(monkeypatch,question,context):
    f=setup(monkeypatch)
    result=f.adapter.run(f.selector,None,ValidationRequest(question=question,answer='8',context=context),'SYNTHETIC')
    assert result.public_status=='uncertain'
    assert not f.calls


def test_resource_mismatch_rejected_without_cache_or_fallback(monkeypatch):
    f=setup(monkeypatch); data=f.artifact.contract.resource_manifest.model_dump()
    data['verifiers'][0]['resources'][0]['sha256']='f'*64
    f.reuse._observer=SimpleNamespace(snapshot_for=lambda actual:ResourceManifest(**data))
    result=f.adapter.run(f.selector,None,ValidationRequest(question='What is 4 + 4?',answer='8',context='8'),'SYNTHETIC')
    assert result.summary['selection_status']=='provenance_incompatible'
    assert not f.calls


def test_highest_existing_validate_api_boundary_uses_same_fitted_policy(monkeypatch):
    from unittest.mock import patch
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from app.reputation.reputation_manager import ReputationManager
    # Import-time service bootstrap is mocked; actual selected engine/service
    # below use the real existing implementation, with persistence disabled.
    with patch('app.orchestration.validation_orchestrator.load_reputation_manager_state',
               return_value=ReputationManager().export_state()):
        from app.api import routes
    from app.orchestration.validation_orchestrator import ValidationOrchestrator
    from app.services.validation_service import ValidationService
    f=setup(monkeypatch)
    orchestrator=ValidationOrchestrator(verifier_selector=f.selector,
        reputation_manager=f.selector.reputation_manager,execution_mode='game',game_runtime=f.adapter)
    monkeypatch.setattr(routes,'_validation_service',ValidationService(orchestrator=orchestrator))
    for name in ('update_validation_record','create_audit','save_verifier_outputs','update_audit'):
        monkeypatch.setattr(routes,name,lambda *args,**kwargs:None)
    app=FastAPI();app.include_router(routes.router)
    client=TestClient(app)
    records=[]
    for question,answer in [('What is 328 + 536?','864'),('What is 4 + 4?','8'),('What is 4 + 4?','9')]:
        response=client.post('/validate',json={'question':question,'answer':answer,'context':answer})
        assert response.status_code==200,response.text
        records.append(response.json())
    assert [r['final_status'] for r in records]==['passed','passed','failed']
    assert {r['execution_audit']['policy_id'] for r in records}=={f.artifact.policy.policy_id}
    assert {r['execution_audit']['artifact_id'] for r in records}=={f.artifact.artifact_id}
    assert records[1]['results'][0]['metadata']['mock_fresh_question']=='What is 4 + 4?'
    assert records[2]['results'][0]['metadata']['mock_fresh_answer']=='9'
    assert len(f.calls)==3


def test_reuse_never_invokes_fitting_or_greedy_selection(monkeypatch):
    import app.game.solver as solver
    import app.game.offline.evaluation as evaluation
    import app.game.policy as policy
    def forbidden(*args,**kwargs):raise AssertionError('Fitting/greedy replacement forbidden')
    monkeypatch.setattr(solver,'solve_minimax',forbidden)
    monkeypatch.setattr(evaluation,'fit_policy',forbidden)
    monkeypatch.setattr(policy,'build_policy',forbidden)
    f=setup(monkeypatch)
    monkeypatch.setattr(f.selector,'select',forbidden)
    result=f.adapter.run(f.selector,None,ValidationRequest(question='What is 4 + 4?',answer='8',context='8'),'SYNTHETIC')
    assert result.public_status=='passed'
    assert result.summary['policy_id']==f.artifact.policy.policy_id


@pytest.mark.parametrize('index,question,reference,draw',[
    (1,'What is the population of Denmark?','SYNTHETIC external fact reference',.5),
    (2,'Paraphrase this reference: Mira delivered twelve parcels to Noor.','Mira delivered twelve parcels to Noor.',0.),
    (2,'Paraphrase this reference: Mira delivered twelve parcels to Noor.','Mira delivered twelve parcels to Noor.',.9)])
def test_other_existing_task_policies_reuse_original_singleton_or_mixed_distribution(index,question,reference,draw):
    from tests.category_engineering_fixtures import output
    from app.game.task_conditioning import TaskSnapshotBinding
    _,provider,_=load_bundle(); artifact=provider.snapshot()[index]; before=artifact.model_dump_json();calls=[]
    class LiveMock(BaseVerifier):
        def __init__(self,name):self._name=name
        @property
        def name(self):return self._name
        def verify(self,q,a,context=None):
            calls.append((self.name,q,a,context));return output(self.name)
    selector=VerifierSelector(verifiers=[LiveMock(c.verifier_name) for c in artifact.context.plan.candidates],
        capabilities=BUILTIN_CAPABILITIES)
    identity=TaskSnapshotBinding.model_validate_json(artifact.context.task_conditioning_json).identity
    scope=ReusablePolicyScope(artifact_id=artifact.artifact_id,compatibility_id=artifact.context.compatibility_id,
        question_pattern=r'.+',maximum_question_chars=200,question_rules_version=identity.question_rules_version,
        review_basis='TEST ONLY: unchanged class/policy; no actual evidence or semantic accuracy claim')
    runtime=ReusablePolicyGameRuntime([artifact],[scope],rng=SimpleNamespace(random=lambda:draw),
        resource_observer=SimpleNamespace(snapshot_for=lambda selector:artifact.contract.resource_manifest))
    request=ValidationRequest(question=question,answer='SYNTHETIC freshly supplied answer',context=reference)
    result=runtime.run(selector,None,request,'SYNTHETIC-new-instance')
    assert result.summary['selection_status']=='selected'
    assert result.summary['policy_id']==artifact.policy.policy_id and result.summary['artifact_id']==artifact.artifact_id
    assert artifact.model_dump_json()==before
    assert runtime._provider.snapshot()[0].policy.solution.probabilities==artifact.policy.solution.probabilities
    assert [row[0] for row in calls]==result.summary['team']
    assert all(row[1:]==(question,request.answer,reference) for row in calls)
    if index==2 and draw==0.:
        assert result.summary['team']==['semantic'] and result.public_status=='uncertain'  # Frozen neutral reputation retained.
    if index==2 and draw==.9:
        assert result.summary['team']==['confidence','semantic']


def test_generate_and_validate_uses_each_fresh_mock_generated_answer_without_policy_change(monkeypatch):
    from unittest.mock import patch
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from app.reputation.reputation_manager import ReputationManager
    with patch('app.orchestration.validation_orchestrator.load_reputation_manager_state',
               return_value=ReputationManager().export_state()):
        from app.api import routes
    from app.orchestration.validation_orchestrator import ValidationOrchestrator
    from app.services.validation_service import ValidationService
    f=setup(monkeypatch)
    orchestrator=ValidationOrchestrator(verifier_selector=f.selector,
        reputation_manager=f.selector.reputation_manager,execution_mode='game',game_runtime=f.adapter)
    monkeypatch.setattr(routes,'_validation_service',ValidationService(orchestrator=orchestrator))
    for name in ('update_validation_record','create_audit','save_verifier_outputs','update_audit'):
        monkeypatch.setattr(routes,name,lambda *args,**kwargs:None)
    generated=[]; answers=iter(['864','8','9'])
    def mock_generate(question):
        answer=next(answers);generated.append((question,answer));return answer
    monkeypatch.setattr(routes,'generate_answer',mock_generate)
    # All database seams are inert mocks, never psycopg2 connections.
    writes=[]
    class Cursor:
        def execute(self,sql,values):writes.append(values)
        def fetchone(self):return (len(writes),)
        def close(self):pass
    connection=SimpleNamespace(cursor=lambda:Cursor(),commit=lambda:None,rollback=lambda:None,close=lambda:None)
    monkeypatch.setattr(routes,'get_connection',lambda:connection)
    app=FastAPI();app.include_router(routes.router);client=TestClient(app);responses=[]
    for question in ['What is 328 + 536?','What is 4 + 4?','What is 4 + 4?']:
        response=client.post('/generate-and-validate',json={'question':question,'context':'SYNTHETIC external reference'})
        assert response.status_code==200,response.text
        responses.append(response.json())
    assert [r['answer'] for r in responses]==['864','8','9']
    assert [r['validation']['final_status'] for r in responses]==['passed','passed','failed']
    assert {r['validation']['execution_audit']['policy_id'] for r in responses}=={f.artifact.policy.policy_id}
    assert [(q,a) for _,q,a,_ in f.calls]==generated
    assert writes==generated
    for record in responses[1:]:
        audit=record['validation']['execution_audit']
        assert audit['fitted_policy_version']==f.artifact.policy.version
        assert audit['fitted_strategy_probabilities']==[list(row) for row in f.artifact.policy.solution.probabilities]
