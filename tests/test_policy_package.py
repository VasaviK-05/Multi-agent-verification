"""Portable typed loading from a relocated bundle; no models or inference."""
import json
from pathlib import Path
import pytest
from scripts.policy_package import load
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
