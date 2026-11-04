import json
from pathlib import Path
from types import SimpleNamespace
import pytest
from scripts import scoped_er_adapter as scoped
from app.game.offline.calibration import MeasurementSetup
from app.game.resource_provenance import ResourceManifest

def setup():
    original=MeasurementSetup.model_validate_json(Path('artifacts/compound-study-36-v1/preparation/setup.json').read_text(encoding='utf-8'))
    projection=ResourceManifest(verifiers=tuple(v for v in original.resources.verifiers if v.verifier_name in {'evidence','rule'}))
    return original,original.model_copy(update={'resources':projection})

def test_unused_service_absence_does_not_disable_required_observation(monkeypatch):
    original,current=setup()
    monkeypatch.setattr(scoped,'observe_service',lambda *a:pytest.fail('unused Ollama contacted'))
    monkeypatch.setattr(scoped,'inspect_setup',lambda c:dict(ready=True,observed_setup=current.model_dump(mode='json'),observed_setup_fingerprint=current.fingerprint))
    pool=[SimpleNamespace(name=n) for n in ('evidence','rule')]
    monkeypatch.setattr(scoped,'construct_verifiers',lambda c:pool)
    native,observed,observer=scoped.create_scoped({},original.resources)
    assert observer.snapshot_for(SimpleNamespace(resolve=lambda n:next(v for v in native if v.name==n)))==current.resources
    with pytest.raises(ValueError,match='active instance'):observer.snapshot_for(SimpleNamespace(resolve=lambda n:object()))
    monkeypatch.setattr(scoped,'inspect_setup',lambda c:dict(ready=False))
    with pytest.raises(ValueError,match='drift'):observer.snapshot()

@pytest.mark.parametrize('kind',['implementation','configuration','model','corpus','index'])
def test_required_resource_delta_rejected(kind):
    original,current=setup();data=current.resources.model_dump(mode='json')
    row=next(r for v in data['verifiers'] for r in v['resources'] if r['kind']==kind);row['sha256']='f'*64
    with pytest.raises(ValueError,match='required E/R'):scoped.require_equivalent(original.resources,data)

def test_confidence_cannot_enter_er_scope():
    original,current=setup()
    with pytest.raises(ValueError):scoped.require_equivalent(original.resources,original.resources)
    assert any(r.kind=='service' for v in original.resources.verifiers if v.verifier_name=='confidence' for r in v.resources)

def test_recovery_permission_does_not_bypass_ambiguous_original_journal(tmp_path):
    from app.game.offline import collection as collector
    from app.game.offline.compound_journal import record_requests
    base=Path('artifacts/remaining-category-studies-v1/reference')
    req=collector.validate_recording_request(json.loads((base/'request.json').read_text(encoding='utf-8')))
    amendment=json.loads(Path('artifacts/remaining-category-studies-v1/recovery-audit/authorized-recovery-amendment.json').read_text(encoding='utf-8'))
    assert amendment['original_duration_ms'] is None
    assert amendment['replacement_identity']!=amendment['original_attempt_id']
    with pytest.raises(ValueError,match='ambiguous in-flight'):
        record_requests({'reference':req},req.expected_setup,[],None,tmp_path/'new',collector,resume_from=base/'training')
    assert not (tmp_path/'new').exists()
