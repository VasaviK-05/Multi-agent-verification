"""scoped_er_resources_v1: owned adapter, native algorithms unchanged.
Inspector forked from the reviewed adapter: exact E/R resource construction,
index receipt and environment checks retained; unused service/Confidence removed.
Execute in the original native source checkout; no network is required.
"""
from app.benchmark.project_adapter import *

SCOPE_VERSION='scoped_er_resources_v1'

def require_equivalent(original,scoped):
    original=ResourceManifest.model_validate(original);scoped=ResourceManifest.model_validate(scoped)
    expected=ResourceManifest(verifiers=tuple(v for v in original.verifiers if v.verifier_name in {'evidence','rule'}))
    if {v.verifier_name for v in scoped.verifiers}!={'evidence','rule'} or scoped!=expected:
        raise ValueError('required E/R resources differ from frozen projection')
    return scoped

class ScopedObserver:
    def __init__(self,config,setup,pool):self.config=config;self.setup=setup;self.pool=tuple(pool)
    def snapshot(self):
        report=inspect_setup(self.config)
        if not report['ready'] or report['observed_setup_fingerprint']!=self.setup.fingerprint:
            raise ValueError('required E/R resource drift')
        return self.setup.resources
    def snapshot_for(self,selector):
        if any(selector.resolve(v.name) is not v for v in self.pool):raise ValueError('active instance differs from scoped factory')
        return self.snapshot()

def create_scoped(config,original_resources):
    before=inspect_setup(config)
    if not before['ready']:raise ValueError(before['blockers'])
    setup=MeasurementSetup.model_validate(before['observed_setup'])
    require_equivalent(original_resources,setup.resources)
    pool=construct_verifiers(config)
    observer=ScopedObserver(config,setup,pool);observer.snapshot()
    return pool,setup,observer
def inspect_setup(configuration):
    """Hash local resources and saved service metadata; no loads/downloads/requests."""
    config = AdapterConfiguration.model_validate(configuration)
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
            raise ValueError('index manifest is stale/legacy; explicit separate index preparation is required')
        return expected_receipt
    receipt = inspect('index_provenance', check_index)
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
        configuration = config.model_dump(exclude={'embedding_snapshot', 'nli_snapshot', 'index_receipt', 'service_observation'})
        rows = []
        for name in ('evidence', 'rule'):
            resources = [resource('implementation', name+'-implementation', source(shared + files[name])),
                resource('configuration', name+'-adapter-configuration', content_id(configuration))]
            if name == 'semantic':
                resources += [model]
            if name == 'evidence':
                resources += [model, nli_model, resource('corpus', 'evidence-corpus', corpus['sha256']),
                              resource('index', 'evidence-index', content_id([index, receipt]))]
            rows.append(dict(verifier_name=name, resources=resources))
        setup = MeasurementSetup(resources=ResourceManifest(verifiers=tuple(rows)), environment=hardware(),
            dependency_versions=versions, code_revision=subprocess.check_output(
                ['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
            application_source_digest=content_id([(p.relative_to(ROOT).as_posix(), file_digest(p))
                for p in sorted((ROOT / 'app').rglob('*.py'))]), evidence_kind='empirical')
    return dict(ready=not blockers, blockers=blockers, inventory=inventory, hardware=hardware(),
        ready_scope='scoped_er_resources_v1; no generation service dependency',
        observed_setup=None if setup is None else setup.model_dump(mode='json'),
        observed_setup_fingerprint=None if setup is None else setup.fingerprint,
        downloads_performed=False, provider_requests_performed=0,
        requirements=dict(downloads='none allowed; missing snapshots require separately authorized provisioning',
            external_service=None, model=None, pricing=None,
            factory_metadata_get_requests=0,
            pricing_reason='no approved monetary pricing inputs supplied',
            memory='CPU mode; model file sizes reported; peak RAM and service memory are not estimated'))

def construct_verifiers(config):
    """Supported constructors; only local files. No verify or generation calls."""
    from sentence_transformers import SentenceTransformer
    from transformers import AutoModelForSequenceClassification, AutoTokenizer, pipeline
    from app.verifiers.evidence_retriever import EvidenceRetriever
    from app.verifiers.evidence_verifier import EvidenceVerifier
    from app.verifiers.rule_verifier import RuleVerifier
    embedding = SentenceTransformer(str(local_path(config.embedding_snapshot)), device='cpu', local_files_only=True)
    tokenizer = AutoTokenizer.from_pretrained(str(local_path(config.nli_snapshot)), local_files_only=True)
    model = AutoModelForSequenceClassification.from_pretrained(str(local_path(config.nli_snapshot)), local_files_only=True)
    nli = pipeline('text-classification', model=model, tokenizer=tokenizer, top_k=None, device=-1)
    retriever = EvidenceRetriever(corpus_path=str(local_path(config.corpus_path)),
        chunk_size=config.chunk_size, index_dir=local_path(config.index_dir), model=embedding)
    if retriever.index.ntotal != len(retriever.chunks) or retriever.index.d != embedding.get_sentence_embedding_dimension():
        raise ValueError('loaded index dimensions/counts differ from embedding/chunks')
    return [EvidenceVerifier(corpus_path=str(local_path(config.corpus_path)),retriever=retriever,nli=nli),RuleVerifier()]
