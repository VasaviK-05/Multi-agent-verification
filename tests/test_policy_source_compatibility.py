import hashlib
import json
import pytest
from app.game.offline.policy_source_compatibility import check_capsule, method_invariants


def seal(payload):
    return dict(payload, capsule_id=hashlib.sha256(json.dumps(payload, sort_keys=True,
        separators=(',', ':')).encode()).hexdigest())


def test_exact_transition_and_binding(tmp_path):
    (tmp_path / 'source.py').write_bytes(b'reviewed')
    c = seal(dict(version='reviewed_er_source_transition_v1', policy_id='policy',
        observed_manifest_id='observed', execution_authorized=False,
        target_files={'source.py': hashlib.sha256(b'reviewed').hexdigest()}))
    assert check_capsule(c, tmp_path, policy_id='policy', observed_manifest_id='observed')['source_review_verified']
    with pytest.raises(ValueError, match='binding differs'):
        check_capsule(c, tmp_path, policy_id='another', observed_manifest_id='observed')
    (tmp_path / 'source.py').write_bytes(b'future version')
    with pytest.raises(ValueError, match='unreviewed required source'):
        check_capsule(c, tmp_path, policy_id='policy', observed_manifest_id='observed')


def test_retrieval_algorithm_change_rejected():
    old = 'class Retriever:\n def retrieve(self): return 1\n def load(self): return 1\n'
    assert method_invariants(old, old.replace('load(self): return 1', 'load(self): return 2'), 'Retriever', {'load'}) == ['load']
    with pytest.raises(ValueError, match='verification semantics'):
        method_invariants(old, old.replace('retrieve(self): return 1', 'retrieve(self): return 2'), 'Retriever', {'load'})


def transition_case():
    from pathlib import Path
    from types import SimpleNamespace
    from app.game.models import content_id
    from app.game.resource_provenance import ResourceManifest
    root = Path(__file__).resolve().parents[1]
    capsule = json.loads((root / 'docs/policy-source-capsule-v2.json').read_text())
    # Contract doubles test the gate; they are not native compatibility evidence.
    config = dict(version='project_collection_adapter_v1', chunk_size=500,
        corpus_path='build\\multitask-policy42\\corpus.json', device='cpu',
        index_dir='build\\multitask-policy42\\index-v2', n_samples=5,
        ollama_model='llama3.2:3b', ollama_url='http://localhost:11434/api/generate',
        temperature=.8, timeout=60.)
    from app.game.offline.reconciled_resources import project
    bundle = json.loads((root / 'reconciliation/policies.json').read_text())
    expected = project(bundle['compound_policy']['contract']['actual_resources'])
    observed = expected.model_dump(mode='json')
    new = dict(config, resource_relocation_binding=None)
    for v in observed['verifiers']:
        for r in v['resources']:
            if r['kind'] == 'implementation': r['sha256'] = capsule['implementation_transitions'][v['verifier_name']]['new']
            if r['kind'] == 'configuration': r['sha256'] = content_id(new)
    pool = [SimpleNamespace(name=n) for n in ('evidence', 'rule')]
    selector = SimpleNamespace(resolve=lambda n: next(v for v in pool if v.name == n))
    return dict(capsule=capsule, root=root, policy_id=capsule['policy_id'], expected=expected,
        observed=observed, old_configuration=config, new_configuration=new, selector=selector, native_pool=pool)


def test_exact_nonrelocated_source_and_configuration_transition():
    from app.game.offline.policy_source_compatibility import verify_er_transition
    assert verify_er_transition(**transition_case())['active_instances_checked']


@pytest.mark.parametrize('kind', ['implementation', 'model', 'corpus', 'index', 'configuration'])
def test_nonpermitted_resource_changes_reject(kind):
    from app.game.offline.policy_source_compatibility import verify_er_transition
    case = transition_case()
    next(r for v in case['observed']['verifiers'] for r in v['resources'] if r['kind'] == kind)['sha256'] = 'f'*64
    with pytest.raises(ValueError): verify_er_transition(**case)


def test_active_instance_mismatch_rejects():
    from types import SimpleNamespace
    from app.game.offline.policy_source_compatibility import verify_er_transition
    case = transition_case(); case['selector'] = SimpleNamespace(resolve=lambda n: object())
    with pytest.raises(ValueError, match='active native objects'): verify_er_transition(**case)
