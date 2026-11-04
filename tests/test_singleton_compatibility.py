"""Contract and retained-report metamorphic tests; never native acceptance."""
import json
import math
from pathlib import Path
from types import SimpleNamespace
import pytest

from app.benchmark import project_adapter as a
from app.game.offline import singleton_compatibility as single
from app.game.offline.reconciled_resources import OLD_CONFIGURATION
from app.game.resource_provenance import ResourceManifest
from app.game.models import capture_context
from app.game.frozen_planning import frozen_selector
from app.models.schemas import ValidationRequest, VerificationResult
from app.selection.verifier_selector import VerifierSelector
from app.selection.capabilities import BUILTIN_CAPABILITIES
from app.selection.models import VerifierUnavailable
from app.verifiers.base_verifier import BaseVerifier
from scripts.reconciliation import load_bundle

ROOT=Path(__file__).resolve().parents[1]


def config():
    return a.AdapterConfiguration(**OLD_CONFIGURATION,embedding_snapshot=None,nli_snapshot=None,index_receipt=None,service_observation=None)


class RetainedReport(BaseVerifier):
    def __init__(self,name,report,calls):self._name=name;self.report=report;self.calls=calls
    @property
    def name(self):return self._name
    def verify(self,*args):
        self.calls.append(self.name)
        if self.report is None:raise AssertionError('zero-probability candidate dispatched')
        return VerificationResult.model_validate_json(self.report)


@pytest.mark.parametrize('index',[0,1])
@pytest.mark.parametrize('draw',[0.,.5,math.nextafter(1.,0.)])
def test_full_plan_distribution_and_finalization_preserved(index,draw,monkeypatch):
    import app.selection.verifier_selector as selector_module
    monkeypatch.setattr(selector_module,'_build_default_verifier',lambda *args:pytest.fail('unused candidate constructed'))
    routes,provider,_=load_bundle();artifact=provider.snapshot()[index]
    item=a.read_json(ROOT/'artifacts/compound-study-36-v1/atomic-replay-inputs.json')[index]
    calls_full,calls_scoped=[],[]
    full=VerifierSelector(verifiers=[RetainedReport(v.verifier_name,item['report_json'] if v.verifier_name==item['selected'] else None,calls_full)
        for v in artifact.context.plan.candidates],capabilities=BUILTIN_CAPABILITIES)
    native=RetainedReport(item['selected'],item['report_json'],calls_scoped)
    scoped=single.SingletonSelector(native)
    # Test only the selected-object and execution seam; no live-resource claim.
    monkeypatch.setattr(single,'settings',lambda obj:(id(obj),obj.name))
    monkeypatch.setattr(single,'require_native',lambda *args:None)
    monkeypatch.setattr(single,'observe',lambda c,i,n:(i,None,None))
    observer=single.SingletonObserver(config(),artifact,native)
    _,_,resolved=routes.router().resolve(item['question'],item['reference'])
    analysis=resolved[1]
    values=artifact.context.model_dump(exclude={'selection_json','analyzer_provenance'})
    captured=capture_context(frozen_selector(scoped,artifact.context),analysis,context=item['reference'],**values)
    assert captured.compatibility_id==artifact.context.compatibility_id
    assert len(captured.plan.candidates)==4
    request=ValidationRequest(question=item['question'],answer=item['answer'],context=item['reference'])
    def run(selector,resource_observer):
        return routes.router().run(selector,request,'metamorphic',provider=provider,
            rng=SimpleNamespace(random=lambda:draw),resource_observer=resource_observer)
    old=run(full,SimpleNamespace(snapshot=lambda:artifact.contract.resource_manifest))
    new=run(scoped,observer)
    assert old.summary['selection_status']==new.summary['selection_status']=='selected'
    for field in ('policy_id','matrix_id','selected_strategy_id','team','aggregation','threshold',
        'reputation_snapshot_id','required','achieved','unresolved','contributors',
        'estimated_selected_cost','estimated_attempted_cost','numerical_decision','public_status','override_reasons'):
        assert old.summary[field]==new.summary[field],field
    assert calls_full==calls_scoped==[item['selected']]
    assert new.summary['singleton_resource_compatibility']['planning_candidates_preserved']
    assert new.summary['singleton_resource_compatibility']==new.summary['singleton_resource_compatibility_after']
    for unused in {'semantic','evidence','rule','confidence'}-{item['selected']}:
        with pytest.raises(VerifierUnavailable):scoped.resolve(unused)


def test_rule_requires_no_models_corpus_index_or_service(monkeypatch):
    _,provider,_=load_bundle();artifact=provider.snapshot()[0]
    monkeypatch.setattr(a,'directory_digest',lambda *x:pytest.fail('unused model inspected'))
    monkeypatch.setattr(a,'observe_service',lambda *x:pytest.fail('unused service contacted'))
    binding,_,intermediate=single.transition(artifact,config())
    observed,relocation,load=single.observe(config(),intermediate,binding['selected'])
    assert observed==intermediate and relocation is load is None


def test_unapproved_artifact_settings_and_code_reject(monkeypatch):
    _,provider,compound=load_bundle();artifact=provider.snapshot()[0]
    with pytest.raises(ValueError,match='unapproved singleton'):single.transfer_for(provider.snapshot()[2])
    with pytest.raises(ValueError,match='atomic PolicyArtifact'):single.transfer_for(compound)
    with pytest.raises(ValueError,match='configuration'):
        single.transition(artifact,config().model_copy(update={'temperature':.9}))
    original=a.file_digest
    monkeypatch.setattr(a,'file_digest',lambda p:'f'*64 if str(p).endswith('rule_verifier.py') else original(p))
    with pytest.raises(ValueError,match='implementation'):single.transition(artifact,config())


def test_instance_and_setting_drift_reject(monkeypatch):
    _,provider,_=load_bundle();native=RetainedReport('rule','{}',[])
    monkeypatch.setattr(single,'require_native',lambda *args:None)
    observer=single.SingletonObserver(config(),provider.snapshot()[0],native)
    with pytest.raises(ValueError,match='instance'):observer.snapshot_for(single.SingletonSelector(RetainedReport('rule','{}',[])))
    native.report='changed'
    with pytest.raises(ValueError,match='settings drift'):observer.snapshot_for(single.SingletonSelector(native))


def test_non_native_selected_object_rejected():
    _,provider,_=load_bundle()
    with pytest.raises(ValueError,match='reviewed native class'):
        single.SingletonObserver(config(),provider.snapshot()[0],RetainedReport('rule','{}',[]))


@pytest.mark.parametrize('path',['corpus.json','index/faiss.index','embedding/model.safetensors','nli/tokenizer.json'])
def test_evidence_required_resource_drift_rejects(tmp_path,path):
    from tests.test_reconciled_resources import assets
    c,intermediate,*_=assets(tmp_path)
    scoped=ResourceManifest(verifiers=tuple(v for v in intermediate.verifiers if v.verifier_name=='evidence'))
    assert single.observe(c,scoped,'evidence')[0]==scoped
    (tmp_path/path).write_bytes(b'changed')
    with pytest.raises(ValueError):single.observe(c,scoped,'evidence')
