"""Portable typed loading from a relocated bundle; no models or inference."""
import json
from pathlib import Path
import pytest
from scripts.policy_package import load, load_runtime_candidate
SOURCE=Path(__file__).resolve().parents[1]/'artifacts/remaining-category-studies-v1/minimal-policy-package-v1/policies.json'
def test_relocated_bundle_needs_no_original_artifact_paths(tmp_path,monkeypatch):
    bundle=tmp_path/'policies.json';bundle.write_bytes(SOURCE.read_bytes())
    monkeypatch.chdir(tmp_path)
    config,provider,compound=load(bundle)
    assert config.router().resolve('Explain quantum gravity.')[0]=='unsupported_category'
    assert compound.evidence_kind=='empirical'
    assert config.component_entries[0][3].policy_id==compound.policy_id
    assert config.allowlist and provider.snapshot()
def test_bundle_tampering_fails_before_registry_construction(tmp_path):
    data=json.loads(SOURCE.read_text(encoding='utf-8'));data['allowed_questions'].append('Unreviewed arbitrary question')
    target=tmp_path/'bad.json';target.write_text(json.dumps(data),encoding='utf-8')
    with pytest.raises(ValueError,match='digest differs'):load(target)

def test_offline_package_is_not_implicitly_deployable():
    published=Path(__file__).resolve().parents[1]/'artifacts/remaining-category-studies-v1/prototype-policy-package-v1/policies.json'
    with pytest.raises(ValueError,match='not deployment-active'):
        load_runtime_candidate(published)

def test_scoped_transfer_is_separate_and_binds_only_exact_projection():
    from app.game.resource_transfer import (
        authorize_scoped_observation, project_manifest, validate_compound_transfer,
    )
    published=Path(__file__).resolve().parents[1]/'artifacts/remaining-category-studies-v1/prototype-policy-package-v1/policies.json'
    config,provider,compound=load(published)
    transfer=json.loads(published.read_text(encoding='utf-8'))['compound_transfer']
    validate_compound_transfer(transfer,compound)
    full=compound.contract.actual_resources
    scoped=project_manifest(full)
    proof=authorize_scoped_observation(transfer,full,full,scoped)
    assert proof['scope']==['evidence','rule']
    rows=list(full.verifiers)
    confidence=next(i for i,row in enumerate(rows) if row.verifier_name=='confidence')
    resources=list(rows[confidence].resources)
    index=next(i for i,row in enumerate(resources) if row.kind=='service')
    resources[index]=resources[index].model_copy(update={'sha256':'f'*64})
    rows[confidence]=rows[confidence].model_copy(update={'resources':tuple(resources)})
    changed=full.model_copy(update={'verifiers':tuple(rows)})
    with pytest.raises(ValueError,match='separate verified relocation'):
        authorize_scoped_observation(transfer,full,changed,scoped)
