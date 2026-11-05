"""Synthetic execution plumbing tests, never native compatibility evidence."""
import random
from pathlib import Path
from types import SimpleNamespace
import pytest
from scripts.reconciliation import load_bundle
from app.game.models import content_id
from app.game.resource_provenance import ResourceManifest
from app.game.offline.reconciled_resources import ReconciledERObserver, project, instance_settings
from app.game.offline.reference_compatibility import reference_intermediate
from app.benchmark import project_adapter as a
from app.models.schemas import ValidationRequest
from app.selection.verifier_selector import VerifierSelector
from app.selection.capabilities import BUILTIN_CAPABILITIES
from tests.test_verifier_selector import StubVerifier

Q='What is the population of Cameroon, and what is that population plus 1000? Give both values.'
A='{"base":"29879337","derived":"29880337"}'


def test_frozen_bundle_and_unknown_routing():
    config,provider,policy=load_bundle()
    assert len(provider.snapshot())==3
    assert config.router().resolve('Explain quantum gravity.')[0]=='unsupported_category'
    assert policy.policy_id=='0192b98e50ab5dcbd40ca78a0d4a3ec3978dfe8086edcb615802c21024c83532'


def test_acceptance_selector_scopes_capability_registration():
    from scripts.reconciliation import selector_for
    pool=[StubVerifier('evidence'),StubVerifier('rule')]
    selector=selector_for(pool)
    assert set(selector._capabilities)=={'evidence','rule'}
    assert all(selector.resolve(v.name) is v for v in pool)


def test_opt_in_seam_keeps_observations_and_checks_post_drift():
    configuration,provider,policy=load_bundle()
    original=policy.contract.actual_resources
    observed=project(original)
    class TestObserver(ReconciledERObserver):
        def __init__(self, drift=False):self.count=0;self.drift=drift
        def snapshot_for(self,selector):
            self.count+=1
            if self.drift and self.count==2:
                data=observed.model_dump(mode='json');data['verifiers'][0]['resources'][0]['sha256']='f'*64
                return ResourceManifest.model_validate(data)
            return observed
        def authorize_component(self,policy_id,historical,actual):
            return dict(policy_id=policy_id,historical_manifest_id=historical.manifest_id,
                observed_manifest_id=actual.manifest_id)
    selector=VerifierSelector(verifiers=[StubVerifier('evidence'),StubVerifier('rule')],capabilities={
        k:BUILTIN_CAPABILITIES[k] for k in ('evidence','rule')})
    def run(observer):return configuration.router().run(selector,ValidationRequest(question=Q,answer=A),
        'synthetic-seam',provider=provider,rng=random.Random(1103),resource_observer=observer)
    rejected=run(SimpleNamespace(snapshot=lambda:observed))
    assert rejected.summary['attempts']==[]
    accepted=run(TestObserver())
    assert len(accepted.summary['attempts'])==2
    assert accepted.summary['resource_compatibility']['observed_manifest_id']==observed.manifest_id
    assert accepted.summary['historical_resource_manifest_id']==original.manifest_id
    assert accepted.summary['after_resource_manifest_id']==observed.manifest_id
    drifted=run(TestObserver(drift=True))
    assert drifted.public_status=='uncertain'
    assert 'resource_provenance_changed_during_execution' in drifted.summary['override_reasons']


def reference_case():
    _,provider,_=load_bundle()
    artifact=next(v for v in provider.snapshot() if 'semantic_comparison' in v.context.plan.requirements.requirements)
    from app.game.offline.reconciled_resources import OLD_CONFIGURATION
    config=a.AdapterConfiguration(**OLD_CONFIGURATION,embedding_snapshot=None,nli_snapshot=None,
        index_receipt=None,service_observation=None)
    service=a.ServiceObservation.model_validate(a.read_json(a.ROOT/'reconciliation/reference-service.json'))
    return artifact,config,service


def test_reference_uses_own_current_service(monkeypatch):
    artifact,config,service=reference_case()
    monkeypatch.setattr(a,'observe_service',lambda c:service)
    assert reference_intermediate(artifact,config).manifest_id!=artifact.contract.resource_manifest.manifest_id


@pytest.mark.parametrize('field,value',[('server_version','0.40.5'),('model_digest','sha256:'+'f'*64)])
def test_reference_service_and_model_mismatch(monkeypatch,field,value):
    artifact,config,service=reference_case()
    monkeypatch.setattr(a,'observe_service',lambda c:service.model_copy(update={field:value}))
    with pytest.raises(ValueError,match='live service/model'):reference_intermediate(artifact,config)


@pytest.mark.parametrize('field,value',[('n_samples',4),('temperature',.9),('timeout',61.)])
def test_reference_sampling_mismatch_rejects(monkeypatch,field,value):
    artifact,config,service=reference_case()
    monkeypatch.setattr(a,'observe_service',lambda c:pytest.fail('settings should reject before GET'))
    with pytest.raises(ValueError,match='settings differ'):
        reference_intermediate(artifact,config.model_copy(update={field:value}))


def test_constructor_and_runtime_cache_distinction():
    model=SimpleNamespace(named_parameters=lambda:[])
    class Double:
        def __init__(self,name):self.name=name;self.threshold=.5
        def verify(self,*args):raise AssertionError('no inference')
    evidence=Double('evidence');rule=Double('rule')
    evidence.retriever=SimpleNamespace(model=model,_document_frequency=None,_postings=None,_doc_lengths=[],_avgdl=0.)
    evidence.nli=SimpleNamespace(model=model)
    before=instance_settings([evidence,rule])
    rule._start=1.;evidence.retriever._avgdl=10.;evidence.retriever._postings={}
    assert instance_settings([evidence,rule])==before
    evidence.threshold=.9
    assert instance_settings([evidence,rule])!=before


def test_changed_reference_prompt_source_rejects(tmp_path,monkeypatch):
    artifact,config,_=reference_case()
    root=a.ROOT
    capsule=a.read_json(root/'reconciliation/reference-source.json')
    deps=a.read_json(root/'reconciliation/integration-dependencies.json')
    for path in set(capsule['target_files']) | set(deps['files']) | {
            'reconciliation/reference-source.json','reconciliation/reference-service.json','reconciliation/integration-dependencies.json'}:
        target=tmp_path/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((root/path).read_bytes())
    (tmp_path/'app/verifiers/self_consistency.py').write_bytes(b'changed prompt or sampler')
    monkeypatch.setattr(a,'ROOT',tmp_path)
    with pytest.raises(ValueError,match='unreviewed reference implementation'):
        reference_intermediate(artifact,config)


def test_reference_logical_serialization_does_not_excuse_other_resources(tmp_path,monkeypatch):
    import json
    from tests.test_reconciled_resources import assets
    from app.game.offline import reference_compatibility as ref
    config,intermediate,current,hashes,receipt=assets(tmp_path)
    # Make the physical/logical serialization difference explicit on every OS.
    # Native write_text newline conversion previously supplied it only on Windows.
    manifest_path=Path(config.index_dir)/'manifest.json'
    manifest_path.write_bytes(json.dumps(current,separators=(',',':')).encode('utf-8'))
    hashes['manifest.json']=a.file_digest(manifest_path)
    physical=intermediate.model_dump(mode='json')
    for verifier in physical['verifiers']:
        for resource in verifier['resources']:
            if resource['resource_id']=='evidence-index':resource['sha256']=content_id([hashes,receipt])
    intermediate=ResourceManifest.model_validate(physical)
    logical=content_id([a._current_index_hashes(hashes,current),receipt])
    data=intermediate.model_dump(mode='json')
    for v in data['verifiers']:
        for r in v['resources']:
            if r['resource_id']=='evidence-index':r['sha256']=logical
    report=dict(ready=True,observed_setup={'resources':data},_relocation_state=dict(
        stored=current,current=current,index_hashes=hashes,expected_receipt=receipt))
    observer=object.__new__(ref.ReferenceObserver)
    observer.pool=(SimpleNamespace(name='evidence'),)
    observer.settings=();observer.config=config
    observer.artifact=SimpleNamespace(artifact_id='synthetic-test',contract=SimpleNamespace(resource_manifest=intermediate))
    observer.native=SimpleNamespace(_attest_active_verifiers=lambda *args:True)
    monkeypatch.setattr(ref,'reference_settings',lambda pool:())
    monkeypatch.setattr(ref,'reference_intermediate',lambda *args:intermediate)
    monkeypatch.setattr(a,'inspect_setup',lambda c:report)
    selector=SimpleNamespace(resolve=lambda n:observer.pool[0])
    observed=observer.snapshot_for(selector)
    assert observer.last_proof['index_observation']['physical_index_id']!=logical
    assert observer.last_proof['observed_manifest_id']==observed.manifest_id
    data['verifiers'][0]['resources'][0]['sha256']='f'*64
    with pytest.raises(ValueError,match='non-serialization required resources'):
        observer.snapshot_for(selector)


def test_reference_proof_seam_executes_frozen_route_with_synthetic_reports(monkeypatch):
    from app.game.offline.reference_compatibility import ReferenceObserver
    artifact,config,service=reference_case()
    monkeypatch.setattr(a,'observe_service',lambda c:service)
    observed=reference_intermediate(artifact,config)
    class FixtureObserver(ReferenceObserver):
        def __init__(self):pass
        def snapshot_for(self,selector):return observed
        def authorize_artifact(self,actual,manifest):
            assert actual==artifact and manifest==observed
            return dict(artifact_id=artifact.artifact_id,observed_manifest_id=manifest.manifest_id)
    from scripts.reconciliation import selector_for
    selector=selector_for([StubVerifier(v.verifier_name) for v in artifact.context.plan.candidates])
    configuration,provider,_=load_bundle()
    question=next(q for q in configuration.allowlist if q.startswith('Paraphrase this reference: '))
    reference=question.partition(': ')[2]
    result=configuration.router().run(selector,ValidationRequest(question=question,answer=reference,context=reference),
        'synthetic-reference-seam',provider=provider,rng=random.Random(1103),resource_observer=FixtureObserver())
    assert result.summary['selection_status']=='selected'
    assert len(result.summary['attempts']) in {1,2}
    assert result.summary['reference_resource_compatibility']['artifact_id']==artifact.artifact_id
