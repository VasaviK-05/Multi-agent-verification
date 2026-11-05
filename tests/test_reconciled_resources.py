"""Resource/transition contract tests; temporary bytes are not live evidence."""
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from app.benchmark import project_adapter as a
from app.game.models import content_id
from app.game.resource_provenance import ResourceManifest
from app.game.offline.reconciled_resources import (source_transition, inspect_required,
    OLD_CONFIGURATION, POLICY_ID, project, ReconciledERObserver)
from app.game.offline.resource_relocation import ResourceRelocationBinding
from scripts.policy_package import load

ROOT = Path(__file__).resolve().parents[1]


def test_pinned_transition_and_singleton_rejection():
    _, provider, policy = load(ROOT / 'reconciliation/policies.json')
    capsule = a.read_json(ROOT / 'docs/policy-source-capsule-v2.json')
    config = a.AdapterConfiguration(**OLD_CONFIGURATION, embedding_snapshot=None, nli_snapshot=None,
        index_receipt=None, service_observation=None)
    historical, intermediate = source_transition(policy.policy_id, policy.contract.actual_resources, config, capsule)
    assert historical.manifest_id != intermediate.manifest_id
    for artifact in provider.snapshot()[:2]:
        with pytest.raises(ValueError, match='unapproved compound'):
            source_transition(artifact.policy.policy_id, artifact.contract.resource_manifest, config, capsule)
    with pytest.raises(ValueError, match='semantic configuration'):
        source_transition(POLICY_ID, historical, config.model_copy(update={'temperature': .9}), capsule)


def assets(tmp_path):
    # Minimal inspector fixtures; never loaded into an inference runtime.
    for name in ('embedding', 'nli'):
        directory = tmp_path / name; directory.mkdir()
        for file in ('config.json', 'tokenizer.json', 'modules.json'):
            (directory / file).write_text('{}')
        (directory / 'model.safetensors').write_bytes(b'unit-fixture')
    corpus = tmp_path / 'corpus.json'; corpus.write_text('{}')
    index = tmp_path / 'index'; index.mkdir()
    (index / 'faiss.index').write_bytes(b'vectors')
    (index / 'chunks.json').write_text('[]')
    sha = a.file_digest(corpus); version = 'sha256:' + sha
    manifest = dict(version=2, corpus_path=str(corpus.resolve()), corpus_size=corpus.stat().st_size,
        corpus_mtime=corpus.stat().st_mtime, corpus_sha256=sha, corpus_version=version, chunk_size=500,
        embedding_model='all-MiniLM-L6-v2', index_version='idx-' + hashlib.sha256(
            json.dumps([version,500,'all-MiniLM-L6-v2']).encode()).hexdigest()[:12])
    (index / 'manifest.json').write_text(json.dumps(manifest, indent=2))
    config = a.AdapterConfiguration(**{**OLD_CONFIGURATION, 'corpus_path':str(corpus), 'index_dir':str(index)},
        embedding_snapshot=str(tmp_path / 'embedding'), nli_snapshot=str(tmp_path / 'nli'),
        index_receipt=str(tmp_path / 'receipt.json'), service_observation=None)
    hashes = {n:a.file_digest(index/n) for n in ('faiss.index','chunks.json','manifest.json')}
    receipt = a.index_receipt(config,a.directory_digest(config.embedding_snapshot)['sha256'],sha,hashes)
    Path(config.index_receipt).write_text(json.dumps(receipt))
    # Build an independently expected fixture manifest using the same public hash specification.
    capsule = a.read_json(ROOT / 'docs/policy-source-capsule-v2.json')
    frozen = project(load(ROOT / 'reconciliation/policies.json')[2].contract.actual_resources).model_dump(mode='json')
    values = {'local-embedding-snapshot':a.directory_digest(config.embedding_snapshot)['sha256'],
        'local-nli-snapshot':a.directory_digest(config.nli_snapshot)['sha256'], 'evidence-corpus':sha,
        'evidence-index':content_id([hashes,receipt])}
    for v in frozen['verifiers']:
        for r in v['resources']:
            if r['kind']=='implementation':r['sha256']=capsule['implementation_transitions'][v['verifier_name']]['new']
            elif r['kind']=='configuration':r['sha256']=content_id(config.model_dump(exclude={
                'embedding_snapshot','nli_snapshot','index_receipt','service_observation'}))
            else:r['sha256']=values[r['resource_id']]
    return config, ResourceManifest.model_validate(frozen), manifest, hashes, receipt


def test_inspection_does_not_contact_ollama(tmp_path, monkeypatch):
    config, intermediate, *_ = assets(tmp_path)
    monkeypatch.setattr(a, 'observe_service', lambda *x: pytest.fail('unused service contacted'))
    observed, relocation, proof = inspect_required(config, intermediate)
    assert observed == intermediate and relocation is None and proof is None


@pytest.mark.parametrize('resource', ['corpus.json','index/faiss.index','embedding/model.safetensors','nli/tokenizer.json'])
def test_changed_required_bytes_reject(tmp_path, resource):
    config, intermediate, *_ = assets(tmp_path)
    (tmp_path / resource).write_bytes(b'changed')
    with pytest.raises(ValueError):inspect_required(config,intermediate)


@pytest.mark.parametrize('names',[('evidence','rule'),('evidence',)])
def test_relocation_composes_only_with_named_intermediate(tmp_path,names):
    config, intermediate, manifest, hashes, receipt = assets(tmp_path)
    intermediate=ResourceManifest(verifiers=tuple(v for v in intermediate.verifiers if v.verifier_name in names))
    index = Path(config.index_dir)
    stored = dict(manifest, corpus_path='C:\\original\\corpus.json', corpus_mtime=1.)
    (index/'manifest.json').write_text(json.dumps(stored,indent=2))
    hashes['manifest.json']=a.file_digest(index/'manifest.json')
    # Bind a different physical manifest's historical index, keeping actual logical current index distinct.
    data=intermediate.model_dump(mode='json')
    for v in data['verifiers']:
        for r in v['resources']:
            if r['resource_id']=='evidence-index':r['sha256']=content_id([hashes,receipt])
    binding_path=tmp_path/'binding.json'
    config=config.model_copy(update={'resource_relocation_binding':str(binding_path)})
    for v in data['verifiers']:
        for r in v['resources']:
            if r['kind']=='configuration':r['sha256']=content_id(config.model_dump(exclude={
                'embedding_snapshot','nli_snapshot','index_receipt','service_observation'}))
    intermediate=ResourceManifest.model_validate(data)
    logical=a._current_index_hashes(hashes,manifest)
    binding=ResourceRelocationBinding(version='verified_resource_relocation_v1',expected_resource_manifest_id=intermediate.manifest_id,
        historical_corpus_path=stored['corpus_path'],current_corpus_path=manifest['corpus_path'],
        historical_manifest_path='C:\\original\\index\\manifest.json',current_manifest_path=str((index/'manifest.json').resolve()),
        historical_corpus_mtime=1.,current_corpus_mtime=manifest['corpus_mtime'],corpus_sha256=manifest['corpus_sha256'],
        corpus_size=manifest['corpus_size'],faiss_sha256=hashes['faiss.index'],chunks_sha256=hashes['chunks.json'],
        manifest_sha256=hashes['manifest.json'],receipt_sha256=a.file_digest(Path(config.index_receipt)),receipt_fingerprint=content_id(receipt),
        embedding_model_sha256=a.directory_digest(config.embedding_snapshot)['sha256'],nli_model_sha256=a.directory_digest(config.nli_snapshot)['sha256'],
        semantic_configuration_sha256=next(r['sha256'] for v in data['verifiers'] for r in v['resources'] if r['kind']=='configuration'),
        manifest_version=2,chunk_size=500,embedding_model='all-MiniLM-L6-v2',index_version=manifest['index_version'],
        historical_index_fingerprint=content_id([hashes,receipt]),current_index_fingerprint=content_id([logical,receipt]))
    binding_path.write_text(binding.model_dump_json())
    observed,proof,load_proof=inspect_required(config,intermediate,names=names)
    assert proof['expected_resource_manifest_id']==intermediate.manifest_id
    assert observed.manifest_id!=intermediate.manifest_id and load_proof['binding_id']==binding.binding_id
    binding_path.write_text(binding.model_copy(update={'expected_resource_manifest_id':'f'*64}).model_dump_json())
    with pytest.raises(ValueError,match='different policy resource manifest'):inspect_required(config,intermediate,names=names)


def test_different_selected_objects_reject_before_observation():
    observer=object.__new__(ReconciledERObserver)
    observer.pool=(SimpleNamespace(name='evidence'),SimpleNamespace(name='rule'))
    with pytest.raises(ValueError,match='selected verifier instance'):
        observer.snapshot_for(SimpleNamespace(resolve=lambda n: object()))


def test_changed_relocation_dependency_source_rejected(tmp_path):
    from app.game.offline.reconciled_resources import check_dependencies
    inventory=a.read_json(ROOT/'reconciliation/integration-dependencies.json')
    (tmp_path/'reconciliation').mkdir()
    (tmp_path/'reconciliation/integration-dependencies.json').write_text(json.dumps(inventory))
    for path in inventory['files']:
        p=tmp_path/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/path).read_bytes())
    check_dependencies(tmp_path)
    (tmp_path/'app/game/offline/resource_relocation.py').write_bytes(b'unreviewed verifier change')
    with pytest.raises(ValueError,match='dependency source'):check_dependencies(tmp_path)
