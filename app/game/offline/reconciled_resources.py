"""Opt-in exact compound source/configuration/relocation observation.

Historical, source-transferred intermediate, and freshly observed manifests
remain distinct. No full-roster or singleton resource contraction is implied.
"""
import hashlib
import inspect
import json
from pathlib import Path

from app.benchmark import project_adapter as adapter
from app.game.models import content_id
from app.game.resource_provenance import ResourceManifest
from app.game.offline.policy_source_compatibility import check_capsule
from app.game.offline.resource_relocation import ResourceRelocationBinding, verify_relocated_index

POLICY_ID = '0192b98e50ab5dcbd40ca78a0d4a3ec3978dfe8086edcb615802c21024c83532'
SCOPE_ID = '310364dae8d9d6c001622d4bbe1866ca0646fb8f50c9c50a022e05f5353688c1'
CAPSULE_ID = 'd78864a6cceb0262408617c724c8789f93811f9b72aa87856abb57dc49d24993'
DEPENDENCIES_ID = '9bd64bb4876aa9108afff2ed23dde10fdc469013d44f5440338934c566962e9b'
OLD_CONFIGURATION = dict(version='project_collection_adapter_v1', chunk_size=500,
    corpus_path='build\\multitask-policy42\\corpus.json', device='cpu',
    index_dir='build\\multitask-policy42\\index-v2', n_samples=5,
    ollama_model='llama3.2:3b', ollama_url='http://localhost:11434/api/generate',
    temperature=.8, timeout=60.)


def project(manifest):
    value = ResourceManifest.model_validate(manifest)
    return ResourceManifest(verifiers=tuple(v for v in value.verifiers if v.verifier_name in {'evidence', 'rule'}))


def semantic_configuration(config):
    return config.model_dump(exclude={'embedding_snapshot', 'nli_snapshot', 'index_receipt', 'service_observation'})


def check_dependencies(root=None):
    root = Path(root or adapter.ROOT)
    record = adapter.read_json(root / 'reconciliation/integration-dependencies.json')
    if record.get('manifest_id') != DEPENDENCIES_ID or content_id({k:v for k,v in record.items() if k!='manifest_id'}) != DEPENDENCIES_ID:
        raise ValueError('unreviewed integration dependency inventory')
    for path, digest in record['files'].items():
        if adapter.file_digest(root / path) != digest:
            raise ValueError('unreviewed integration dependency source: ' + path)


def source_transition(policy_id, historical, config, capsule):
    check_dependencies()
    if policy_id != POLICY_ID or capsule.get('capsule_id') != CAPSULE_ID:
        raise ValueError('unapproved compound policy/source transition')
    check_capsule(capsule, adapter.ROOT, policy_id=policy_id,
                  observed_manifest_id=capsule['observed_manifest_id'])
    historical = project(historical)
    if historical.manifest_id != SCOPE_ID:
        raise ValueError('unapproved historical E/R resource scope')
    current = semantic_configuration(config)
    paths = {'corpus_path', 'index_dir', 'resource_relocation_binding'}
    if {k: v for k, v in current.items() if k not in paths} != {
            k: v for k, v in OLD_CONFIGURATION.items() if k not in paths}:
        raise ValueError('unreviewed semantic configuration change')
    data = historical.model_dump(mode='json')
    for verifier in data['verifiers']:
        name = verifier['verifier_name']
        for row in verifier['resources']:
            if row['kind'] == 'implementation':
                transition = capsule['implementation_transitions'][name]
                if row['sha256'] != transition['old']:
                    raise ValueError('unexpected historical implementation')
                row['sha256'] = transition['new']
            elif row['kind'] == 'configuration':
                if row['sha256'] != content_id(OLD_CONFIGURATION):
                    raise ValueError('unexpected historical configuration')
                row['sha256'] = content_id(current)
    return historical, ResourceManifest.model_validate(data)


def inspect_required(config, intermediate, *, prepare=False, names=('evidence', 'rule')):
    """Observe actual required bytes. No model construction or service calls."""
    if names not in {('evidence',), ('evidence', 'rule')} or {v.verifier_name for v in intermediate.verifiers} != set(names):
        raise ValueError('unexpected required resource scope')
    embedding = adapter.directory_digest(config.embedding_snapshot)
    nli = adapter.directory_digest(config.nli_snapshot)
    if not (adapter.local_path(config.embedding_snapshot) / 'modules.json').is_file():
        raise ValueError('embedding snapshot lacks modules.json')
    corpus_path = adapter.local_path(config.corpus_path)
    directory = adapter.local_path(config.index_dir)
    corpus = adapter.file_digest(corpus_path)
    index = {n: adapter.file_digest(directory / n) for n in ('faiss.index', 'chunks.json', 'manifest.json')}
    if not config.index_receipt:
        raise ValueError('required index receipt missing')
    receipt_path = adapter.local_path(config.index_receipt)
    receipt = adapter.read_json(receipt_path)
    expected_receipt = adapter.index_receipt(config, embedding['sha256'], corpus, index)
    if receipt != expected_receipt:
        raise ValueError('required corpus/model/index receipt mismatch')
    stored = adapter.read_json(directory / 'manifest.json')
    constants = adapter.source_constants('app/verifiers/evidence_retriever.py', {'EMBEDDING_MODEL', 'MANIFEST_VERSION'})
    version = 'sha256:' + corpus
    current = dict(version=constants['MANIFEST_VERSION'], corpus_path=str(corpus_path),
        corpus_size=corpus_path.stat().st_size, corpus_mtime=corpus_path.stat().st_mtime,
        corpus_sha256=corpus, corpus_version=version, chunk_size=config.chunk_size,
        embedding_model=constants['EMBEDDING_MODEL'], index_version='idx-' + hashlib.sha256(
            json.dumps([version, config.chunk_size, constants['EMBEDDING_MODEL']]).encode()).hexdigest()[:12])
    relocated = stored != current
    historical_index = next(r.sha256 for v in intermediate.verifiers for r in v.resources
                            if r.resource_id == 'evidence-index')
    if content_id([index, receipt]) != historical_index:
        raise ValueError('physical historical index/receipt bytes differ from intermediate contract')
    if relocated and not config.resource_relocation_binding:
        raise ValueError('relocation requires an explicit intermediate-bound proof')
    logical = adapter._current_index_hashes(index, current) if relocated else index
    shared = ['app/verifiers/base_verifier.py', 'app/models/schemas.py', 'app/benchmark/project_adapter.py']
    files = dict(evidence=['app/verifiers/evidence_verifier.py', 'app/verifiers/evidence_retriever.py',
                          'app/verifiers/claim_generator.py'], rule=['app/verifiers/rule_verifier.py'])
    # Construct from OBSERVED bytes, not the intermediate manifest.
    rows = []
    for name in names:
        resources = [dict(kind='implementation', resource_id=name+'-implementation',
            sha256=content_id([(p, adapter.file_digest(adapter.ROOT / p)) for p in shared + files[name]])),
            dict(kind='configuration', resource_id=name+'-adapter-configuration',
                 sha256=content_id(semantic_configuration(config)))]
        if name == 'evidence':
            resources += [dict(kind=k, resource_id=r, sha256=d) for k, r, d in (
                ('model', 'local-embedding-snapshot', embedding['sha256']),
                ('model', 'local-nli-snapshot', nli['sha256']), ('corpus', 'evidence-corpus', corpus),
                ('index', 'evidence-index', content_id([logical, receipt])))]
        rows.append(dict(verifier_name=name, resources=resources))
    observed = ResourceManifest(verifiers=tuple(rows))
    state = dict(stored_manifest=stored, current_manifest=current, corpus_path=corpus_path,
        manifest_path=directory / 'manifest.json', corpus_sha256=corpus, index_hashes=index,
        receipt_path=receipt_path, receipt=receipt, expected_receipt=expected_receipt,
        embedding_model_sha256=embedding['sha256'], nli_model_sha256=nli['sha256'],
        semantic_configuration_sha256=content_id(semantic_configuration(config)))
    relocation, load_proof = None, None
    if relocated:
        if prepare:
            differences = {k for k in set(stored) | set(current) if stored.get(k) != current.get(k)}
            if not differences or differences - {'corpus_path', 'corpus_mtime'} or set(stored) != set(current):
                raise ValueError('index differs beyond reviewed relocation fields')
            def nonindex(manifest):
                return {(v.verifier_name,r.kind,r.resource_id):r.sha256 for v in manifest.verifiers
                        for r in v.resources if r.resource_id != 'evidence-index'}
            if nonindex(intermediate) != nonindex(observed):
                raise ValueError('non-relocation required resource differs')
            return observed, None, state
        binding = ResourceRelocationBinding.model_validate(adapter.read_json(adapter.local_path(config.resource_relocation_binding)))
        relocation = verify_relocated_index(binding, expected_manifest=intermediate,
            observed_manifest=observed, **state)
        load_proof = dict(**relocation, binding=binding.model_dump(mode='json'),
            expected_resource_manifest=intermediate.model_dump(mode='json'),
            observed_resource_manifest=observed.model_dump(mode='json'),
            **{k: str(v) if isinstance(v, Path) else v for k, v in state.items()})
    elif observed != intermediate:
        raise ValueError('required resources differ from reviewed source-transferred manifest')
    elif config.resource_relocation_binding:
        raise ValueError('relocation binding supplied without a relocation')
    return observed, relocation, load_proof


def prepare_relocation(configuration, policy):
    """Create metadata only after proving exact historical bytes; never rebuild."""
    config = adapter.AdapterConfiguration.model_validate(configuration)
    capsule = adapter.read_json(adapter.ROOT / 'docs/policy-source-capsule-v2.json')
    _, intermediate = source_transition(policy.policy_id, policy.contract.actual_resources, config, capsule)
    observed, _, state = inspect_required(config, intermediate, prepare=True)
    if state is None or 'current_manifest' not in state:
        raise ValueError('no relocation exists to bind')
    return make_relocation_binding(config, intermediate, observed, state)


def make_relocation_binding(config, intermediate, observed, state):
    """Common existing byte-proof builder; scope remains explicit in intermediate."""
    stored, current = state['stored_manifest'], state['current_manifest']
    index = state['index_hashes']
    binding = ResourceRelocationBinding(version='verified_resource_relocation_v1',
        expected_resource_manifest_id=intermediate.manifest_id,
        historical_corpus_path=stored['corpus_path'], current_corpus_path=str(state['corpus_path']),
        historical_manifest_path=str(Path(stored['corpus_path']).parent /
            Path(OLD_CONFIGURATION['index_dir'].replace('\\','/')).name / 'manifest.json'),
        current_manifest_path=str(state['manifest_path']), historical_corpus_mtime=stored['corpus_mtime'],
        current_corpus_mtime=current['corpus_mtime'], corpus_sha256=state['corpus_sha256'], corpus_size=current['corpus_size'],
        faiss_sha256=index['faiss.index'], chunks_sha256=index['chunks.json'], manifest_sha256=index['manifest.json'],
        receipt_sha256=adapter.file_digest(state['receipt_path']), receipt_fingerprint=content_id(state['receipt']),
        embedding_model_sha256=state['embedding_model_sha256'],nli_model_sha256=state['nli_model_sha256'],
        semantic_configuration_sha256=state['semantic_configuration_sha256'], manifest_version=current['version'],
        chunk_size=current['chunk_size'],embedding_model=current['embedding_model'],index_version=current['index_version'],
        historical_index_fingerprint=next(r.sha256 for v in intermediate.verifiers for r in v.resources if r.resource_id=='evidence-index'),
        current_index_fingerprint=next(r.sha256 for v in observed.verifiers for r in v.resources if r.resource_id=='evidence-index'))
    proof = verify_relocated_index(binding, expected_manifest=intermediate, observed_manifest=observed, **state)
    return binding, proof


def instance_settings(pool):
    """Constructor values, executable identities and loaded model dependencies."""
    runtime = {'_start', '_document_frequency', '_postings', '_doc_lengths', '_avgdl'}
    rows = []
    for verifier in pool:
        for obj in (verifier, getattr(verifier, 'retriever', None), getattr(verifier, 'claim_generator', None)):
            if obj is None:
                continue
            values = []
            for key, value in sorted(vars(obj).items()):
                if key in runtime:
                    continue
                if type(value) in (str, int, float, bool, type(None)):
                    captured = value
                elif isinstance(value, dict) and all(type(v) in (str, int, float, bool, type(None)) for v in value.values()):
                    captured = content_id(value)
                else:
                    captured = id(value)
                values.append((key, captured))
            rows.append((id(obj), tuple(values)))
        rows.append((verifier.name, id(type(verifier).verify)))
    evidence = next(v for v in pool if v.name == 'evidence')
    for model in (evidence.retriever.model, evidence.nli.model):
        rows.append(tuple((name, id(param), param._version) for name, param in model.named_parameters()))
    return tuple(rows)


class ReconciledERObserver:
    def __init__(self, config, capsule, historical, intermediate, pool):
        self.config, self.capsule = config, capsule
        self.historical, self.intermediate, self.pool = historical, intermediate, tuple(pool)
        self.settings = instance_settings(self.pool)
        self.last_proof = None

    def snapshot_for(self, selector):
        if any(selector.resolve(v.name) is not v for v in self.pool):
            raise ValueError('actual selected verifier instance mismatch')
        if instance_settings(self.pool) != self.settings:
            raise ValueError('active constructor/model/dependency settings drift')
        source_transition(POLICY_ID, self.historical, self.config, self.capsule)
        observed, relocation, _ = inspect_required(self.config, self.intermediate)
        self.last_proof = dict(version='scoped_source_relocation_composition_v1', policy_id=POLICY_ID,
            capsule_id=CAPSULE_ID, historical_scope_id=self.historical.manifest_id,
            intermediate_manifest_id=self.intermediate.manifest_id, observed_manifest_id=observed.manifest_id,
            relocation=relocation, active_instances_checked=True,
            constructor_settings_id=content_id(self.settings), execution_scope=['evidence', 'rule'])
        self.last_proof['proof_id'] = content_id(self.last_proof)
        return observed

    def snapshot(self):
        raise ValueError('scoped compatibility requires snapshot_for(actual_selector)')

    def authorize_component(self, policy_id, historical_full, observed):
        if policy_id != POLICY_ID or project(historical_full) != self.historical or self.last_proof is None:
            raise ValueError('unapproved component policy or historical scope')
        if self.last_proof['observed_manifest_id'] != observed.manifest_id:
            raise ValueError('unbound observed manifest')
        return self.last_proof


def create_scoped(configuration, policy, *, capsule_path=None):
    """Only required local native objects; no Confidence imports/construction/GETs."""
    config = adapter.AdapterConfiguration.model_validate(configuration)
    capsule = adapter.read_json(capsule_path or adapter.ROOT / 'docs/policy-source-capsule-v2.json')
    if policy.policy_id != POLICY_ID:
        raise ValueError('unapproved policy; singleton contraction is not authorized')
    historical, intermediate = source_transition(policy.policy_id, policy.contract.actual_resources, config, capsule)
    before, _, load_proof = inspect_required(config, intermediate)
    from app.verifiers.rule_verifier import RuleVerifier
    pool = [construct_evidence(config, load_proof), RuleVerifier()]
    observer = ReconciledERObserver(config, capsule, historical, intermediate, pool)
    after, _, _ = inspect_required(config, intermediate)
    if after != before:
        raise ValueError('required resources changed during initialization')
    return pool, observer


def construct_evidence(config, load_proof=None):
    """Shared local-only native construction; no unused Confidence/service."""
    from sentence_transformers import SentenceTransformer
    from transformers import AutoModelForSequenceClassification, AutoTokenizer, pipeline
    from app.verifiers.evidence_retriever import EvidenceRetriever
    from app.verifiers.evidence_verifier import EvidenceVerifier
    from app.verifiers.rule_verifier import RuleVerifier
    embedding = SentenceTransformer(str(adapter.local_path(config.embedding_snapshot)), device='cpu', local_files_only=True)
    tokenizer = AutoTokenizer.from_pretrained(str(adapter.local_path(config.nli_snapshot)), local_files_only=True)
    model = AutoModelForSequenceClassification.from_pretrained(str(adapter.local_path(config.nli_snapshot)), local_files_only=True)
    nli = pipeline('text-classification', model=model, tokenizer=tokenizer, top_k=None, device=-1)
    retriever = EvidenceRetriever(corpus_path=str(adapter.local_path(config.corpus_path)), chunk_size=config.chunk_size,
        index_dir=adapter.local_path(config.index_dir), model=embedding, relocation_proof=load_proof)
    if retriever.index.ntotal != len(retriever.chunks) or retriever.index.d != embedding.get_sentence_embedding_dimension():
        raise ValueError('loaded index dimensions/counts differ')
    return EvidenceVerifier(corpus_path=str(adapter.local_path(config.corpus_path)), retriever=retriever, nli=nli)
