"""Only new resource-binding seam; no native construction, inference or DB."""
from types import SimpleNamespace
import pytest
from app.game.reusable_deployment import FactoryBoundReusablePolicyRuntime, compose_factory_bound_reuse
from app.selection.verifier_selector import VerifierSelector
from app.models.schemas import ValidationRequest
from tests.test_reusable_policy_runtime import setup


def test_inert_service_selector_is_replaced_by_request_local_reviewed_binding(monkeypatch):
    f=setup(monkeypatch);scope=f.reuse._entries[0][0];factory_calls=[]
    def factory(artifact):factory_calls.append(artifact.artifact_id);return f.selector,f.observer
    bound=FactoryBoundReusablePolicyRuntime([f.artifact],[scope],rng=f.reuse._rng,
        resource_factories={f.artifact.artifact_id:factory})
    assert factory_calls==[]
    result=bound.run(VerifierSelector(verifiers=[]),None,
        ValidationRequest(question='What is 4 + 4?',answer='8',context='8'),'TEST-live-binding')
    assert result.public_status=='passed' and len(factory_calls)==1
    assert result.summary['policy_id']==f.artifact.policy.policy_id
    assert result.summary['runtime_resource_binding']=='reviewed_factory_bound_reuse_v1'
    assert f.calls==[('rule','What is 4 + 4?','8','8')]


def test_incompatible_input_never_constructs_resources(monkeypatch):
    f=setup(monkeypatch);scope=f.reuse._entries[0][0]
    def forbidden(artifact):raise AssertionError('unsupported input reached resource factory')
    bound=FactoryBoundReusablePolicyRuntime([f.artifact],[scope],rng=f.reuse._rng,
        resource_factories={f.artifact.artifact_id:forbidden})
    result=bound.run(None,None,ValidationRequest(question='Explain gravity.',answer='x'),'TEST')
    assert result.public_status=='uncertain' and not f.calls


def test_resource_preflight_failure_is_not_a_fallback(monkeypatch):
    f=setup(monkeypatch);scope=f.reuse._entries[0][0]
    def missing(artifact):raise ValueError('required native resources absent')
    bound=FactoryBoundReusablePolicyRuntime([f.artifact],[scope],rng=f.reuse._rng,
        resource_factories={f.artifact.artifact_id:missing})
    result=bound.run(None,None,ValidationRequest(question='What is 4 + 4?',answer='8',context='8'),'TEST')
    assert result.summary['selection_status']=='resource_incompatible' and not f.calls


def test_composition_works_through_actual_service_empty_selector_path(monkeypatch):
    from app.services.validation_service import ValidationService
    import app.game.deployment as deployment
    from app.utils.config import settings
    f=setup(monkeypatch);legacy=f.adapter._dispatcher._legacy;scope=f.reuse._entries[0][0]
    adapter=compose_factory_bound_reuse(legacy,[f.artifact],[scope],rng=f.reuse._rng)
    monkeypatch.setattr(deployment,'create_game_runtime',lambda:adapter)
    monkeypatch.setattr(settings,'EXECUTION_MODE','game')
    service=ValidationService(persist_execution=False)
    assert service._orchestrator._verifier_selector._injected == []
    result=service.validate(ValidationRequest(question='What is 4 + 4?',answer='9',context='8'))
    assert result.final_status=='failed' and result.execution_audit['policy_id']==f.artifact.policy.policy_id
