"""Explicit local-only collection adapter; inspection never imports model runtimes."""
import argparse
import ast
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import subprocess
from typing import Literal
from urllib.parse import urlsplit

from pydantic import Field, StrictFloat, StrictInt, ValidationError, model_validator

from app.game.dependencies import FrozenModel
from app.game.models import content_id
from app.game.offline.calibration import MeasurementSetup, Text, read_json
from app.game.resource_provenance import ResourceManifest

ROOT = Path(__file__).resolve().parents[2]
FACTORY = 'app.benchmark.project_adapter:create_verifiers'
PACKAGES = ('numpy', 'pydantic', 'sentence-transformers', 'transformers', 'torch',
            'faiss-cpu', 'requests', 'safetensors', 'tokenizers')


class AdapterConfiguration(FrozenModel):
    version: Literal['project_collection_adapter_v1'] = 'project_collection_adapter_v1'
    embedding_snapshot: Text | None
    nli_snapshot: Text | None
    corpus_path: Text
    index_dir: Text
    index_receipt: Text | None
    service_observation: Text | None
    resource_relocation_binding: Text | None = None
    ollama_url: Text = 'http://localhost:11434/api/generate'
    ollama_model: Text = 'llama3.2:3b'
    n_samples: StrictInt = Field(default=5, ge=1)
    temperature: StrictFloat = Field(default=.8, gt=0)
    timeout: StrictFloat = Field(default=60., gt=0)
    chunk_size: StrictInt = Field(default=500, ge=1)
    device: Literal['cpu'] = 'cpu'

    @model_validator(mode='after')
    def local_service(self):
        url = urlsplit(self.ollama_url)
        if (url.scheme != 'http' or url.hostname not in {'localhost', '127.0.0.1', '::1'}
                or url.username or url.password or url.query or url.fragment or url.path != '/api/generate'):
            raise ValueError('adapter requires credential-free loopback Ollama /api/generate URL')
        return self


def local_path(value):
    path = Path(value)
    return path.resolve() if path.is_absolute() else (ROOT / path).resolve()


def file_digest(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def directory_digest(path):
    """Fingerprint actual local weights/tokenizer/config bytes, not a hub alias."""
    if path is None:
        raise ValueError('local model snapshot path is required')
    path = local_path(path)
    if not path.is_dir():
        raise ValueError('model snapshot directory unavailable')
    files = sorted(p for p in path.rglob('*') if p.is_file())
    if not files or not (path / 'config.json').is_file():
        raise ValueError('snapshot lacks config.json')
    if not any(p.suffix in {'.safetensors', '.bin'} for p in files):
        raise ValueError('snapshot lacks local model weights')
    if not any(p.name in {'tokenizer.json', 'vocab.txt', 'spm.model', 'sentencepiece.bpe.model'} for p in files):
        raise ValueError('snapshot lacks local tokenizer')
    return dict(sha256=content_id([(p.relative_to(path).as_posix(), file_digest(p)) for p in files]),
                files=len(files), bytes=sum(p.stat().st_size for p in files))


def index_receipt(config, embedding_digest, corpus_digest, files):
    return dict(version='observed_index_build_v1', embedding_sha256=embedding_digest,
        corpus_sha256=corpus_digest, chunk_size=config.chunk_size,
        index_sha256=files['faiss.index'], chunks_sha256=files['chunks.json'])


def prepare_index(config):
    """Explicit potentially costly embedding job. Never called by preflight/factory."""
    config = AdapterConfiguration.model_validate(config)
    embedding = directory_digest(config.embedding_snapshot)
    before_corpus = file_digest(local_path(config.corpus_path))
    target = local_path(config.index_dir)
    if not target.is_relative_to(ROOT / 'build'):
        raise ValueError('prepare-index requires a fresh directory under repository build/')
    target.mkdir(parents=True, exist_ok=False)
    from sentence_transformers import SentenceTransformer
    from app.verifiers.evidence_retriever import EvidenceRetriever
    model = SentenceTransformer(str(local_path(config.embedding_snapshot)), device='cpu', local_files_only=True)
    retriever = EvidenceRetriever(corpus_path=str(local_path(config.corpus_path)), chunk_size=config.chunk_size,
        index_dir=target, model=model)
    if (directory_digest(config.embedding_snapshot) != embedding or
            file_digest(local_path(config.corpus_path)) != before_corpus):
        raise ValueError('model/corpus changed during index build; no receipt produced')
    if retriever.index.ntotal != len(retriever.chunks):
        raise ValueError('index/chunk counts differ')
    return index_receipt(config, embedding['sha256'], before_corpus,
        {n: file_digest(target / n) for n in ('faiss.index', 'chunks.json')})


def source_constants(relative, names):
    """Read literal defaults without importing heavyweight verifier modules."""
    tree = ast.parse((ROOT / relative).read_text(encoding='utf-8'))
    result = {}
    for statement in ast.walk(tree):
        if isinstance(statement, ast.Assign):
            for target in statement.targets:
                if isinstance(target, ast.Name) and target.id in names:
                    try:
                        result[target.id] = ast.literal_eval(statement.value)
                    except ValueError:
                        pass
    return result


def hardware():
    result = dict(os=platform.platform(), architecture=platform.machine(),
        host_fingerprint=content_id(platform.node()),
        processor=platform.processor() or 'unavailable', logical_cpus=str(os.cpu_count()),
        device='cpu', concurrency='sequential', runtime=platform.python_version(),
        initialization='eager shared embedding and NLI; excluded from attempt timer',
        thread_settings=json.dumps({k: os.environ.get(k, 'runtime default') for k in
            ('OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'OPENBLAS_NUM_THREADS')}, sort_keys=True))
    if os.name == 'nt':
        import ctypes
        class Memory(ctypes.Structure):
            _fields_ = [('length', ctypes.c_ulong), ('load', ctypes.c_ulong)] + [
                (n, ctypes.c_ulonglong) for n in ('total', 'available', 'page', 'availpage', 'virtual', 'availvirtual', 'extended')]
        memory = Memory()
        memory.length = ctypes.sizeof(memory)
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(memory)):
            result['physical_memory_bytes'] = str(memory.total)
    elif hasattr(os, 'sysconf'):
        try:
            result['physical_memory_bytes'] = str(os.sysconf('SC_PAGE_SIZE') * os.sysconf('SC_PHYS_PAGES'))
        except (OSError, ValueError):
            pass
    return result


class ServiceObservation(FrozenModel):
    version: Literal['ollama_metadata_observation_v1'] = 'ollama_metadata_observation_v1'
    url: Text
    model: Text
    model_digest: Text = Field(pattern=r'^sha256:[0-9a-f]{64}$')
    server_version: Text
    # No timestamps: same observed service content yields the same setup identity.


def observe_service(config):
    """Explicit metadata-only command/factory check. Never called by preflight."""
    import requests
    config = AdapterConfiguration.model_validate(config)
    base = config.ollama_url.rsplit('/api/generate', 1)[0]
    session = requests.Session()
    session.trust_env = False  # loopback inspection must not inherit proxy secrets
    try:
        version = session.get(base + '/api/version', timeout=5)
        version.raise_for_status()
        tags = session.get(base + '/api/tags', timeout=5)
        tags.raise_for_status()
        names = {config.ollama_model, config.ollama_model + ':latest'}
        matches = [m for m in tags.json()['models'] if m.get('name') in names or m.get('model') in names]
        if len(matches) != 1:
            raise ValueError('Ollama tag unavailable or ambiguous; no pull is performed')
        digest = matches[0]['digest']
        if isinstance(digest, str) and not digest.startswith('sha256:'):
            digest = 'sha256:' + digest
        return ServiceObservation(url=config.ollama_url, model=config.ollama_model,
            model_digest=digest, server_version=version.json()['version'])
    finally:
        session.close()


def _load_relocation_binding(value):
    if value is None:
        return None
    from app.game.offline.resource_relocation import ResourceRelocationBinding
    if isinstance(value, (str, Path)):
        value = read_json(local_path(value))
    return ResourceRelocationBinding.model_validate(value)


def _current_index_hashes(index_hashes, current_manifest):
    """Hashes used for the relocated logical index, without writing a manifest."""
    result = dict(index_hashes)
    result['manifest.json'] = hashlib.sha256(json.dumps(current_manifest, indent=2).encode('utf-8')).hexdigest()
    return result


def _evidence_index_fingerprint(index_hashes, receipt, current_manifest=None):
    hashes = index_hashes if current_manifest is None else _current_index_hashes(index_hashes, current_manifest)
    return content_id([hashes, receipt])


def inspect_setup(configuration, *, relocation_binding=None, _prepare_relocation_binding=False):
    """Hash local resources and saved service metadata; no loads/downloads/requests."""
    config = AdapterConfiguration.model_validate(configuration)
    binding_source = relocation_binding
    if binding_source is None and not _prepare_relocation_binding:
        binding_source = config.resource_relocation_binding or os.environ.get('VERIFIER_RESOURCE_RELOCATION_BINDING')
    binding = _load_relocation_binding(binding_source)
    if binding is not None and _prepare_relocation_binding:
        raise ValueError('supply either a relocation binding or prepare one, not both')
    blockers, inventory = [], {}
    def inspect(key, function):
        try:
            inventory[key] = function()
            return inventory[key]
        except (OSError, ValueError, KeyError, TypeError) as exc:
            blockers.append(dict(resource=key, reason=str(exc), owner='resource/collection owner'))
            return None
    def model_snapshot(path, embedding=False):
        if not path:
            raise ValueError('supply an existing local snapshot path; no download is performed')
        result = directory_digest(path)
        if embedding and not (local_path(path) / 'modules.json').is_file():
            raise ValueError('embedding snapshot lacks SentenceTransformer modules.json')
        return result
    embedding = inspect('embedding_snapshot', lambda: model_snapshot(config.embedding_snapshot, embedding=True))
    nli = inspect('nli_snapshot', lambda: model_snapshot(config.nli_snapshot))
    corpus = inspect('corpus', lambda: dict(sha256=file_digest(local_path(config.corpus_path)),
                                           bytes=local_path(config.corpus_path).stat().st_size))
    index_dir = local_path(config.index_dir)
    index = inspect('index', lambda: {n: file_digest(index_dir / n) for n in
                                      ('faiss.index', 'chunks.json', 'manifest.json')})
    constants = source_constants('app/verifiers/evidence_retriever.py', {'EMBEDDING_MODEL', 'MANIFEST_VERSION'})
    def check_index():
        if not corpus or not index or not embedding:
            raise ValueError('cannot validate index before corpus, vectors and embedding snapshot are available')
        if not config.index_receipt:
            raise ValueError('missing index build receipt linking actual embedding bytes to vectors; alias-only manifest is insufficient')
        receipt = read_json(local_path(config.index_receipt))
        expected_receipt = index_receipt(config, embedding['sha256'], corpus['sha256'], index)
        if receipt != expected_receipt:
            raise ValueError('index build receipt differs from observed files/configuration')
        stored = read_json(index_dir / 'manifest.json')
        # Require the complete manifest, so EvidenceRetriever cannot silently
        # upgrade/rewrite it or rebuild the index in a collection factory.
        stat = local_path(config.corpus_path).stat()
        corpus_version = 'sha256:' + corpus['sha256']
        current = dict(version=constants['MANIFEST_VERSION'], corpus_path=str(local_path(config.corpus_path)),
            corpus_size=stat.st_size, corpus_mtime=stat.st_mtime, corpus_sha256=corpus['sha256'],
            corpus_version=corpus_version, chunk_size=config.chunk_size, embedding_model=constants['EMBEDDING_MODEL'],
            index_version='idx-' + hashlib.sha256(json.dumps([corpus_version, config.chunk_size,
                constants['EMBEDDING_MODEL']]).encode()).hexdigest()[:12])
        if stored != current:
            differences = {key for key in set(stored) | set(current) if stored.get(key) != current.get(key)}
            if not _prepare_relocation_binding and binding is None:
                raise ValueError('index manifest is stale/legacy; explicit separate index preparation is required')
            if differences != {'corpus_path', 'corpus_mtime'}:
                raise ValueError('index manifest differs beyond relocation path/mtime: ' + ', '.join(sorted(differences)))
            if stored.get('version') != current.get('version'):
                raise ValueError('unsupported legacy index manifest version')
        relocation_state.update(stored=stored, current=current, corpus_path=str(local_path(config.corpus_path)),
            manifest_path=str(index_dir / 'manifest.json'), receipt_path=str(local_path(config.index_receipt)),
            expected_receipt=expected_receipt, index_hashes=index, corpus_sha256=corpus['sha256'])
        return expected_receipt
    relocation_state = {}
    receipt = inspect('index_provenance', check_index)
    def service_metadata():
        if not config.service_observation:
            raise ValueError('missing saved Ollama metadata; run observe-service explicitly (no generation)')
        value = ServiceObservation.model_validate(read_json(local_path(config.service_observation)))
        if (value.url, value.model) != (config.ollama_url, config.ollama_model):
            raise ValueError('saved service observation URL/model mismatch')
        return value.model_dump(mode='json')
    service = inspect('service', service_metadata)
    versions = {}
    for name in PACKAGES:
        try:
            versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            blockers.append(dict(resource=name, reason='dependency not installed', owner='environment owner'))
    versions['python'] = platform.python_version()
    try:
        versions['sentencepiece'] = importlib.metadata.version('sentencepiece')
    except importlib.metadata.PackageNotFoundError:
        versions['sentencepiece'] = 'not installed; local tokenizer.json avoids conversion'
    setup = None
    relocation_audit = None
    relocation_proof = None
    if not blockers:
        source = lambda files: content_id([(n, file_digest(ROOT / n)) for n in files])
        shared = ['app/verifiers/base_verifier.py', 'app/models/schemas.py', 'app/benchmark/project_adapter.py']
        files = dict(semantic=['app/verifiers/semantic_verifier.py', 'app/verifiers/claim_generator.py',
                               'app/verifiers/confidence_verifier.py'],
            evidence=['app/verifiers/evidence_verifier.py', 'app/verifiers/evidence_retriever.py', 'app/verifiers/claim_generator.py'],
            rule=['app/verifiers/rule_verifier.py'],
            confidence=['app/verifiers/confidence_verifier.py', 'app/verifiers/self_consistency.py',
                        'app/verifiers/evidence_verifier.py', 'app/verifiers/claim_generator.py'])
        def resource(kind, name, digest):
            return dict(kind=kind, resource_id=name, sha256=digest)
        model = resource('model', 'local-embedding-snapshot', embedding['sha256'])
        nli_model = resource('model', 'local-nli-snapshot', nli['sha256'])
        prompt = source_constants('app/verifiers/self_consistency.py', {'SHORT_ANSWER_PROMPT'})['SHORT_ANSWER_PROMPT']
        configuration = config.model_dump(exclude={'embedding_snapshot', 'nli_snapshot', 'index_receipt', 'service_observation'})
        rows = []
        for name in ('semantic', 'evidence', 'rule', 'confidence'):
            resources = [resource('implementation', name+'-implementation', source(shared + files[name])),
                resource('configuration', name+'-adapter-configuration', content_id(configuration))]
            if name == 'semantic':
                resources += [model]
            if name == 'evidence':
                current_manifest = relocation_state.get('current')
                resources += [model, nli_model, resource('corpus', 'evidence-corpus', corpus['sha256']),
                              resource('index', 'evidence-index', _evidence_index_fingerprint(index, receipt, current_manifest))]
            if name == 'confidence':
                resources += [nli_model, resource('model', 'ollama-model', service['model_digest'][7:]),
                    resource('prompt', 'self-consistency-short-answer', content_id(prompt)),
                    resource('service', 'ollama-service', content_id(service))]
            rows.append(dict(verifier_name=name, resources=resources))
        resources_manifest = ResourceManifest(verifiers=tuple(rows))
        if relocation_state and relocation_state.get('stored') != relocation_state.get('current'):
            if _prepare_relocation_binding:
                pass
            else:
                expected_data = resources_manifest.model_dump(mode='json')
                for verifier in expected_data['verifiers']:
                    if verifier['verifier_name'] == 'evidence':
                        for row in verifier['resources']:
                            if row['resource_id'] == 'evidence-index':
                                row['sha256'] = binding.historical_index_fingerprint
                expected_manifest = ResourceManifest.model_validate(expected_data)
                semantic_configuration = config.model_dump(exclude={'embedding_snapshot', 'nli_snapshot', 'index_receipt', 'service_observation'})
                from app.game.offline.resource_relocation import verify_relocated_index
                relocation_audit = verify_relocated_index(binding, expected_manifest=expected_manifest,
                    observed_manifest=resources_manifest, stored_manifest=relocation_state['stored'],
                    current_manifest=relocation_state['current'], corpus_path=Path(relocation_state['corpus_path']),
                    manifest_path=Path(relocation_state['manifest_path']), corpus_sha256=relocation_state['corpus_sha256'],
                    index_hashes=relocation_state['index_hashes'], receipt_path=Path(relocation_state['receipt_path']),
                    receipt=receipt, expected_receipt=relocation_state['expected_receipt'],
                    embedding_model_sha256=embedding['sha256'], nli_model_sha256=nli['sha256'],
                    semantic_configuration_sha256=content_id(semantic_configuration))
                relocation_proof = dict(**relocation_audit, binding=binding.model_dump(mode='json'),
                    corpus_sha256=relocation_state['corpus_sha256'],
                    expected_resource_manifest=expected_manifest.model_dump(mode='json'),
                    observed_resource_manifest=resources_manifest.model_dump(mode='json'),
                    stored_manifest=relocation_state['stored'],
                    current_manifest=relocation_state['current'],
                    index_hashes=relocation_state['index_hashes'],
                    receipt_path=relocation_state['receipt_path'],
                    receipt=relocation_state['expected_receipt'],
                    expected_receipt=relocation_state['expected_receipt'],
                    corpus_path=relocation_state['corpus_path'],
                    manifest_path=relocation_state['manifest_path'],
                    embedding_model_sha256=embedding['sha256'], nli_model_sha256=nli['sha256'],
                    semantic_configuration_sha256=content_id(semantic_configuration))
                relocation_state.update(binding=binding, resources=resources_manifest,
                    embedding_model_sha256=embedding['sha256'], nli_model_sha256=nli['sha256'],
                    semantic_configuration_sha256=content_id(semantic_configuration),
                    relocation_audit=relocation_audit)
        environment = hardware()
        if relocation_audit is not None:
            environment['resource_relocation_audit'] = json.dumps(relocation_audit, sort_keys=True, separators=(',', ':'))
        setup = MeasurementSetup(resources=resources_manifest, environment=environment,
            dependency_versions=versions, code_revision=subprocess.check_output(
                ['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
            application_source_digest=content_id([(p.relative_to(ROOT).as_posix(), file_digest(p))
                for p in sorted((ROOT / 'app').rglob('*.py'))]), evidence_kind='empirical')
    report = dict(ready=not blockers, blockers=blockers, inventory=inventory, hardware=hardware(),
        ready_scope='local inputs only; saved service observation is revalidated live by factory',
        observed_setup=None if setup is None else setup.model_dump(mode='json'),
        observed_setup_fingerprint=None if setup is None else setup.fingerprint,
        relocation_audit=relocation_audit,
        relocation_proof=relocation_proof,
        downloads_performed=False, provider_requests_performed=0,
        requirements=dict(downloads='none allowed; missing snapshots require separately authorized provisioning',
            external_service=config.ollama_url, model=config.ollama_model, pricing=None,
            factory_metadata_get_requests=4,
            pricing_reason='no approved monetary pricing inputs supplied',
            memory='CPU mode; model file sizes reported; peak RAM and service memory are not estimated'))
    if relocation_state:
        report['_relocation_state'] = relocation_state
    return report


def create_relocation_binding(configuration):
    """Create a fresh, auditable path/mtime-only binding for a new artifact setup."""
    config = AdapterConfiguration.model_validate(configuration)
    report = inspect_setup(config, _prepare_relocation_binding=True)
    if not report['ready'] or report['observed_setup'] is None:
        raise ValueError(json.dumps(report['blockers']))
    state = report['_relocation_state']
    if state['stored'] == state['current']:
        raise ValueError('no corpus path/mtime relocation exists to bind')
    current = MeasurementSetup.model_validate(report['observed_setup']).resources
    historical_fp = _evidence_index_fingerprint(state['index_hashes'], state['expected_receipt'])
    current_fp = next(r.sha256 for v in current.verifiers if v.verifier_name == 'evidence'
                      for r in v.resources if r.resource_id == 'evidence-index')
    if historical_fp == current_fp:
        raise ValueError('relocation did not change the logical evidence-index identity')
    expected_data = current.model_dump(mode='json')
    for verifier in expected_data['verifiers']:
        if verifier['verifier_name'] == 'evidence':
            for row in verifier['resources']:
                if row['resource_id'] == 'evidence-index':
                    row['sha256'] = historical_fp
    expected = ResourceManifest.model_validate(expected_data)
    from app.game.offline.resource_relocation import ResourceRelocationBinding
    stored, manifest = state['stored'], state['current']
    index = state['index_hashes']
    receipt = state['expected_receipt']
    semantic_configuration = config.model_dump(exclude={'embedding_snapshot', 'nli_snapshot', 'index_receipt', 'service_observation'})
    historical_manifest_path = str(Path(stored['corpus_path']).parent / Path(config.index_dir).name / 'manifest.json')
    return ResourceRelocationBinding(version='verified_resource_relocation_v1',
        expected_resource_manifest_id=expected.manifest_id,
        historical_corpus_path=stored['corpus_path'], current_corpus_path=str(state['corpus_path']),
        historical_manifest_path=historical_manifest_path,
        current_manifest_path=str(state['manifest_path']),
        historical_corpus_mtime=stored['corpus_mtime'], current_corpus_mtime=manifest['corpus_mtime'],
        corpus_sha256=state['corpus_sha256'], corpus_size=manifest['corpus_size'],
        faiss_sha256=index['faiss.index'], chunks_sha256=index['chunks.json'], manifest_sha256=index['manifest.json'],
        receipt_sha256=file_digest(state['receipt_path']), receipt_fingerprint=content_id(receipt),
        embedding_model_sha256=report['inventory']['embedding_snapshot']['sha256'],
        nli_model_sha256=report['inventory']['nli_snapshot']['sha256'],
        semantic_configuration_sha256=content_id(semantic_configuration),
        manifest_version=manifest['version'], chunk_size=manifest['chunk_size'],
        embedding_model=manifest['embedding_model'], index_version=manifest['index_version'],
        historical_index_fingerprint=historical_fp, current_index_fingerprint=current_fp)


def create_verifiers():
    """Zero-argument factory used by the existing collector, configured explicitly."""
    path = os.environ.get('VERIFIER_COLLECTION_ADAPTER_CONFIG')
    if not path:
        raise ValueError('set VERIFIER_COLLECTION_ADAPTER_CONFIG to the reviewed adapter configuration')
    config = AdapterConfiguration.model_validate(read_json(path))
    report = inspect_setup(config)
    if not report['ready']:
        raise ValueError(json.dumps(report['blockers']))
    saved = ServiceObservation.model_validate(report['inventory']['service'])
    if observe_service(config) != saved:
        raise ValueError('live Ollama version/model digest differs from reviewed observation')
    proof = report.get('relocation_proof')
    pool = construct_verifiers(config) if proof is None else construct_verifiers(config, relocation_proof=proof)
    expected = MeasurementSetup.model_validate(report['observed_setup'])
    expected.resources.require_candidates(v.name for v in pool)
    if len({v.name for v in pool}) != len(pool):
        raise ValueError('adapter constructed duplicate verifier identities')
    if observe_service(config) != saved:
        raise ValueError('live Ollama version/model changed during verifier initialization')
    after = inspect_setup(config)
    if after['observed_setup_fingerprint'] != report['observed_setup_fingerprint']:
        raise ValueError('resources changed during verifier initialization')
    return pool, MeasurementSetup.model_validate(after['observed_setup'])


class ResourceObserver:
    """Optional observer for the existing detached recording producer."""
    def __init__(self, configuration, setup):
        self.configuration = AdapterConfiguration.model_validate(configuration)
        self.setup = MeasurementSetup.model_validate(setup)

    def snapshot(self):
        report = inspect_setup(self.configuration)
        if report['observed_setup_fingerprint'] != self.setup.fingerprint:
            raise ValueError('local resources/environment changed since factory initialization')
        saved = ServiceObservation.model_validate(report['inventory']['service'])
        if observe_service(self.configuration) != saved:
            raise ValueError('live service/model identity changed during recording')
        return self.setup.resources


def create_recording_verifiers():
    """Three-value adapter for the separate recording producer; pair factory unchanged."""
    pool, setup = create_verifiers()
    config = AdapterConfiguration.model_validate(read_json(os.environ['VERIFIER_COLLECTION_ADAPTER_CONFIG']))
    return pool, setup, ResourceObserver(config, setup)


def construct_verifiers(config, *, relocation_proof=None):
    """Supported constructors; only local files. No verify or generation calls."""
    from sentence_transformers import SentenceTransformer
    from transformers import AutoModelForSequenceClassification, AutoTokenizer, pipeline
    from app.verifiers.semantic_verifier import SemanticVerifier
    from app.verifiers.evidence_retriever import EvidenceRetriever
    from app.verifiers.evidence_verifier import EvidenceVerifier
    from app.verifiers.rule_verifier import RuleVerifier
    from app.verifiers.confidence_verifier import ConfidenceVerifier
    from app.verifiers.self_consistency import OllamaSampler, AgreementLabeler, SelfConsistencyJudge
    embedding = SentenceTransformer(str(local_path(config.embedding_snapshot)), device='cpu', local_files_only=True)
    tokenizer = AutoTokenizer.from_pretrained(str(local_path(config.nli_snapshot)), local_files_only=True)
    model = AutoModelForSequenceClassification.from_pretrained(str(local_path(config.nli_snapshot)), local_files_only=True)
    nli = pipeline('text-classification', model=model, tokenizer=tokenizer, top_k=None, device=-1)
    retriever = EvidenceRetriever(corpus_path=str(local_path(config.corpus_path)),
        chunk_size=config.chunk_size, index_dir=local_path(config.index_dir), model=embedding,
        relocation_proof=relocation_proof)
    if retriever.index.ntotal != len(retriever.chunks) or retriever.index.d != embedding.get_sentence_embedding_dimension():
        raise ValueError('loaded index dimensions/counts differ from embedding/chunks')
    provider = SelfConsistencyJudge(sampler=OllamaSampler(url=config.ollama_url, model=config.ollama_model,
        temperature=config.temperature, timeout=config.timeout), labeler=AgreementLabeler(nli=nli), n_samples=config.n_samples)
    return [SemanticVerifier(model=embedding), EvidenceVerifier(corpus_path=str(local_path(config.corpus_path)),
            retriever=retriever, nli=nli),
            RuleVerifier(), ConfidenceVerifier(judgment_provider=provider)]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('preflight', 'observe-service', 'prepare-index'))
    parser.add_argument('configuration', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--collection', type=Path)
    args = parser.parse_args(argv)
    result = None
    try:
        if args.output.exists():
            raise FileExistsError('output already exists; use a fresh path')
        config = AdapterConfiguration.model_validate(read_json(args.configuration))
        if args.command == 'observe-service':
            result = observe_service(config).model_dump(mode='json')
        elif args.command == 'prepare-index':
            result = prepare_index(config)
        else:
            result = inspect_setup(config)
            result['counts'] = None
            if args.collection:
                from app.benchmark.prepare_collection import PreparationInput, attempt_counts
                try:
                    preparation = PreparationInput.model_validate(read_json(args.collection))
                    result['counts'] = attempt_counts(preparation, config.n_samples)
                except (ValueError, OSError) as exc:
                    result['ready'] = False
                    result['blockers'].append(dict(resource='preparation', reason=error_reason(exc), owner='dataset custodian'))
            else:
                result['ready'] = False
                result['blockers'].append(dict(resource='preparation', reason='no approved preparation input supplied', owner='dataset custodian'))
        with args.output.open('x', encoding='utf-8') as handle:
            json.dump(result, handle, sort_keys=True, indent=2, allow_nan=False)
        return 0 if result.get('ready', True) else 2
    except (ValueError, OSError) as exc:
        print(json.dumps(dict(ready=False, blocker=error_reason(exc))))
        return 2


def error_reason(exc):
    if isinstance(exc, ValidationError):
        return json.dumps([dict(location=e['loc'], message=e['msg'])
                           for e in exc.errors(include_input=False, include_url=False)])
    return str(exc)


if __name__ == '__main__':
    raise SystemExit(main())
