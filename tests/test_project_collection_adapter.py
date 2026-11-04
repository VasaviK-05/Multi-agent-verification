"""Synthetic local bytes and mocked runtimes only; no empirical measurements."""
import hashlib
import json
import os
from pathlib import Path
import sys
import types

import pytest

from app.benchmark import project_adapter as adapter
from app.benchmark.prepare_collection import PreparationInput, attempt_counts, prepare
from app.benchmark.collect_costs import CollectionRequest
from app.game.models import content_id
from tests.test_cost_calibration import request as synthetic_calibration_request


def preparation():
    return PreparationInput(final_test_reservation=synthetic_calibration_request()['final_test_reservation'],
        permitted_datasets=(('history', 'history-v1'),), preparation_authorization='SYNTHETIC custodian permission',
        examples=tuple(dict(example_id='history', split_identity='history', question_id='history', run_id='run'+str(i),
            dataset_id='history-v1', role='history', purpose=p, question='history question',
            answer='fixture answer', context=None) for i, p in enumerate(('warmup', 'calibration'))))


@pytest.fixture
def configuration(tmp_path, monkeypatch):
    monkeypatch.setattr(adapter.importlib.metadata, 'version', lambda n: 'SYNTHETIC_VERSION')
    paths = []
    for name in ('embedding', 'nli'):
        path = tmp_path / name
        path.mkdir()
        for filename, text in (('config.json', '{}'), ('tokenizer.json', '{}'),
                               ('modules.json', '[]'), ('model.safetensors', 'SYNTHETIC_WEIGHTS')):
            (path / filename).write_text(text)
        paths.append(str(path))
    corpus = tmp_path / 'corpus.json'
    corpus.write_text('[{"id":1,"text":"SYNTHETIC corpus"}]')
    index_dir = tmp_path / 'index'
    index_dir.mkdir()
    (index_dir / 'faiss.index').write_bytes(b'SYNTHETIC_INDEX')
    (index_dir / 'chunks.json').write_text('[{"text":"SYNTHETIC chunk"}]')
    digest = adapter.file_digest(corpus)
    corpus_version = 'sha256:' + digest
    constants = adapter.source_constants('app/verifiers/evidence_retriever.py',
                                        {'EMBEDDING_MODEL', 'MANIFEST_VERSION'})
    model = constants['EMBEDDING_MODEL']
    manifest = dict(version=constants['MANIFEST_VERSION'], corpus_path=str(corpus.resolve()), corpus_size=corpus.stat().st_size,
        corpus_mtime=corpus.stat().st_mtime, corpus_sha256=digest, corpus_version=corpus_version,
        index_version='idx-' + hashlib.sha256(json.dumps([corpus_version, 500, model]).encode()).hexdigest()[:12],
        chunk_size=500, embedding_model=model)
    (index_dir / 'manifest.json').write_text(json.dumps(manifest))
    receipt = tmp_path / 'receipt.json'
    service = tmp_path / 'service.json'
    config = adapter.AdapterConfiguration(embedding_snapshot=paths[0], nli_snapshot=paths[1],
        corpus_path=str(corpus), index_dir=str(index_dir), index_receipt=str(receipt),
        service_observation=str(service))
    receipt.write_text(json.dumps(adapter.index_receipt(config, adapter.directory_digest(paths[0])['sha256'], digest,
        {n: adapter.file_digest(index_dir / n) for n in ('faiss.index', 'chunks.json')})))
    service.write_text(adapter.ServiceObservation(url=config.ollama_url, model=config.ollama_model,
        model_digest='sha256:'+'a'*64, server_version='SYNTHETIC_SERVER').model_dump_json())
    return config


def test_inspection_no_loads_network_generation_or_state_writes(configuration, monkeypatch):
    def forbidden(*a, **kw):
        pytest.fail('preflight attempted external action')
    monkeypatch.setattr(adapter, 'observe_service', forbidden)
    monkeypatch.setattr(adapter, 'construct_verifiers', forbidden)
    monkeypatch.setattr(adapter, 'prepare_index', forbidden)
    import requests
    import sqlite3
    monkeypatch.setattr(sqlite3, 'connect', forbidden)
    monkeypatch.setattr(requests.Session, 'request', forbidden)
    report = adapter.inspect_setup(configuration)
    assert report['ready'], report['blockers']
    assert report['provider_requests_performed'] == 0
    assert report['downloads_performed'] is False
    assert report['requirements']['pricing'] is None
    assert {v['verifier_name'] for v in report['observed_setup']['resources']['verifiers']} == {
        'semantic', 'evidence', 'rule', 'confidence'}
    assert report['observed_setup_fingerprint'] == adapter.inspect_setup(configuration)['observed_setup_fingerprint']
    request = prepare(configuration, preparation())
    assert request.factory == adapter.FACTORY
    assert request.examples == preparation().examples
    counts = attempt_counts(preparation(), configuration.n_samples)
    assert counts['intended_attempts'] == 8 and counts['warmup_attempts'] == 4
    assert counts['intended_generation_requests_if_all_reached'] == 10
    assert CollectionRequest.model_validate_json(request.model_dump_json()) == request


@pytest.mark.parametrize('problem', ['missing_model', 'weights', 'tokenizer', 'index', 'receipt', 'stale_manifest',
    'alias_only_manifest', 'legacy_version', 'changed_model', 'changed_corpus', 'service', 'service_mismatch', 'dependency'])
def test_missing_and_incompatible_resources_block(configuration, monkeypatch, problem):
    data = configuration.model_dump()
    if problem == 'missing_model':
        data['embedding_snapshot'] = None
    elif problem == 'weights':
        (Path(data['embedding_snapshot']) / 'model.safetensors').unlink()
    elif problem == 'tokenizer':
        (Path(data['nli_snapshot']) / 'tokenizer.json').unlink()
    elif problem == 'index':
        (Path(data['index_dir']) / 'faiss.index').unlink()
    elif problem == 'receipt':
        data['index_receipt'] = None
    elif problem in {'stale_manifest', 'alias_only_manifest', 'legacy_version'}:
        path = Path(data['index_dir']) / 'manifest.json'
        manifest = json.loads(path.read_text())
        if problem == 'stale_manifest':
            manifest['chunk_size'] = 999
        elif problem == 'legacy_version':
            manifest['version'] = 1
        else:
            del manifest['corpus_sha256']
        path.write_text(json.dumps(manifest))
    elif problem == 'changed_model':
        (Path(data['embedding_snapshot']) / 'model.safetensors').write_bytes(b'CHANGED_SYNTHETIC')
    elif problem == 'changed_corpus':
        Path(data['corpus_path']).write_text('[]')
    elif problem == 'service':
        data['service_observation'] = None
    elif problem == 'service_mismatch':
        data['ollama_model'] = 'different-model'
    elif problem == 'dependency':
        monkeypatch.setattr(adapter.importlib.metadata, 'version',
            lambda n: (_ for _ in ()).throw(adapter.importlib.metadata.PackageNotFoundError(n)))
    report = adapter.inspect_setup(data)
    assert not report['ready'] and report['blockers']
    assert report['observed_setup'] is None


@pytest.mark.parametrize('problem', ['final_role', 'final_group', 'final_content', 'related_group', 'duplicate_run',
    'cross_role', 'label', 'unpermitted', 'inconsistent_example'])
def test_preparation_roles_grouping_and_final_exclusion(problem):
    data = preparation().model_dump()
    row = data['examples'][1]
    if problem == 'final_role':
        row['role'] = 'final_test'
    elif problem == 'final_group':
        row['split_identity'] = 'final_test'
    elif problem == 'final_content':
        row.update(question='final_test question', answer='fixture answer')
    elif problem == 'related_group':
        row['split_identity'] = 'other'
    elif problem == 'duplicate_run':
        row['run_id'] = data['examples'][0]['run_id']
    elif problem == 'cross_role':
        data['permitted_datasets'] += (('development', 'development-v1'),)
        row.update(role='development', dataset_id='development-v1')
    elif problem == 'label':
        row['answer_is_correct'] = True
    elif problem == 'unpermitted':
        row['dataset_id'] = 'unapproved'
    else:
        row.update(question='different content', question_id='different-question')
    with pytest.raises(ValueError):
        PreparationInput.model_validate(data)


def test_actual_verifier_constructors_with_mocked_models(configuration, monkeypatch):
    calls = []
    embedding = types.SimpleNamespace(get_sentence_embedding_dimension=lambda: 384)
    def sentence_model(path, **kwargs):
        calls.append(('embedding', path, kwargs))
        return embedding
    nli = types.SimpleNamespace(model=types.SimpleNamespace(config=types.SimpleNamespace(
        id2label={0: 'contradiction', 1: 'entailment', 2: 'neutral'})))
    def load(path, **kwargs):
        calls.append(('nli', path, kwargs))
        return object()
    monkeypatch.setitem(sys.modules, 'sentence_transformers', types.SimpleNamespace(SentenceTransformer=sentence_model))
    monkeypatch.setitem(sys.modules, 'transformers', types.SimpleNamespace(
        AutoModelForSequenceClassification=types.SimpleNamespace(from_pretrained=load),
        AutoTokenizer=types.SimpleNamespace(from_pretrained=load), pipeline=lambda *a, **kw: nli))
    import app.verifiers.evidence_retriever as retrieval
    retriever = types.SimpleNamespace(index=types.SimpleNamespace(ntotal=1, d=384), chunks=[{}])
    monkeypatch.setattr(retrieval, 'EvidenceRetriever', lambda **kw: retriever)
    pool = adapter.construct_verifiers(configuration)
    assert [v.name for v in pool] == ['semantic', 'evidence', 'rule', 'confidence']
    assert pool[0].model is embedding
    assert pool[1].retriever is retriever and pool[1].nli is nli
    provider = pool[3].judgment_provider
    assert provider.n_samples == 5 and provider.labeler.nli is nli
    assert provider.sampler.url == configuration.ollama_url
    assert all(call[2]['local_files_only'] is True for call in calls)


def test_factory_checks_live_service_and_setup(configuration, monkeypatch, tmp_path):
    config_path = tmp_path / 'adapter.json'
    config_path.write_text(configuration.model_dump_json())
    monkeypatch.setenv('VERIFIER_COLLECTION_ADAPTER_CONFIG', str(config_path))
    observed = adapter.ServiceObservation.model_validate_json(Path(configuration.service_observation).read_text())
    monkeypatch.setattr(adapter, 'observe_service', lambda c: observed)
    pool = [types.SimpleNamespace(name=n) for n in ('semantic', 'evidence', 'rule', 'confidence')]
    monkeypatch.setattr(adapter, 'construct_verifiers', lambda c: pool)
    actual, setup = adapter.create_verifiers()
    assert actual is pool
    setup.resources.require_candidates(v.name for v in actual)
    monkeypatch.setattr(adapter, 'observe_service', lambda c: adapter.ServiceObservation(
        **{**observed.model_dump(), 'model_digest': 'sha256:'+'b'*64}))
    monkeypatch.setattr(adapter, 'construct_verifiers', lambda c: pytest.fail('must fail before model initialization'))
    with pytest.raises(ValueError, match='digest differs'):
        adapter.create_verifiers()


def test_preflight_cli_reports_counts_and_invalid_preparation(configuration, monkeypatch, tmp_path):
    config = tmp_path / 'adapter.json'
    config.write_text(configuration.model_dump_json())
    prep = tmp_path / 'preparation.json'
    prep.write_text(preparation().model_dump_json())
    monkeypatch.setattr(adapter, 'observe_service', lambda *a: pytest.fail('network'))
    output = tmp_path / 'preflight.json'
    assert adapter.main(['preflight', str(config), '--collection', str(prep), '--output', str(output)]) == 0
    assert json.loads(output.read_text())['counts']['intended_attempts'] == 8
    prep.write_text('{"examples":[{"role":"final_test"}]}')
    out2 = tmp_path / 'blocked.json'
    assert adapter.main(['preflight', str(config), '--collection', str(prep), '--output', str(out2)]) == 2
    assert json.loads(out2.read_text())['ready'] is False
    with pytest.raises(ValueError):
        adapter.AdapterConfiguration(**{**configuration.model_dump(), 'ollama_url': 'https://user:secret@provider/api/generate'})


def test_factory_fails_without_configuration(monkeypatch):
    monkeypatch.delenv('VERIFIER_COLLECTION_ADAPTER_CONFIG', raising=False)
    with pytest.raises(ValueError, match='VERIFIER_COLLECTION_ADAPTER_CONFIG'):
        adapter.create_verifiers()


def test_service_observation_uses_only_metadata_and_normalizes_real_digest(configuration, monkeypatch):
    import requests
    calls = []
    class Session:
        trust_env = True
        def get(self, url, **kw):
            calls.append(url)
            value = {'version': 'SYNTHETIC_SERVER'} if url.endswith('/version') else {
                'models': [{'name': configuration.ollama_model, 'digest': 'a'*64}]}
            return types.SimpleNamespace(raise_for_status=lambda: None, json=lambda: value)
        def close(self):
            assert self.trust_env is False
    monkeypatch.setattr(requests, 'Session', Session)
    actual = adapter.observe_service(configuration)
    assert actual.model_digest == 'sha256:'+'a'*64
    assert [url.rsplit('/', 1)[-1] for url in calls] == ['version', 'tags']


def test_explicit_index_preparation_uses_existing_builder(configuration, monkeypatch, tmp_path):
    import numpy as np
    root = tmp_path / 'offline-root'
    root.mkdir()
    monkeypatch.setattr(adapter, 'ROOT', root)
    config = adapter.AdapterConfiguration(**{**configuration.model_dump(), 'index_dir': str(root / 'build' / 'fresh-index')})
    calls = []
    class Model:
        def encode(self, texts, **kw):
            calls.append(len(texts))
            return np.array([[1., 0.] for text in texts], dtype=np.float32)
    monkeypatch.setitem(sys.modules, 'sentence_transformers', types.SimpleNamespace(SentenceTransformer=lambda *a, **kw: Model()))
    receipt = adapter.prepare_index(config)
    assert calls == [1]
    assert receipt['embedding_sha256'] == adapter.directory_digest(config.embedding_snapshot)['sha256']
    assert receipt['index_sha256'] == adapter.file_digest(Path(config.index_dir) / 'faiss.index')
    with pytest.raises(FileExistsError):
        adapter.prepare_index(config)


def test_resource_observer_rejects_changed_service(configuration, monkeypatch):
    report = adapter.inspect_setup(configuration)
    observed = adapter.ServiceObservation.model_validate(report['inventory']['service'])
    monkeypatch.setattr(adapter, 'observe_service', lambda c: observed)
    observer = adapter.ResourceObserver(configuration, report['observed_setup'])
    assert observer.snapshot().manifest_id == observer.setup.resources.manifest_id
    monkeypatch.setattr(adapter, 'observe_service', lambda c: adapter.ServiceObservation(
        **{**observed.model_dump(), 'server_version': 'CHANGED_SYNTHETIC'}))
    with pytest.raises(ValueError, match='identity changed'):
        observer.snapshot()


def _relocate_manifest_metadata(configuration):
    path = Path(configuration.index_dir) / 'manifest.json'
    manifest = json.loads(path.read_text())
    manifest['corpus_path'] = r'C:\historical\project\corpus.json'
    manifest['corpus_mtime'] = 1_600_000_000.0
    path.write_text(json.dumps(manifest, indent=2))
    return path


def _retriever_for_relocation(configuration, proof):
    from app.verifiers.evidence_retriever import EvidenceRetriever
    instance = EvidenceRetriever.__new__(EvidenceRetriever)
    instance.corpus_path = Path(configuration.corpus_path)
    instance.chunk_size = configuration.chunk_size
    instance.corpus_version = 'sha256:' + adapter.file_digest(instance.corpus_path)
    instance.index_version = 'idx-' + hashlib.sha256(json.dumps([
        instance.corpus_version, instance.chunk_size, instance.EMBEDDING_MODEL
    ]).encode()).hexdigest()[:12]
    instance.index_dir = Path(configuration.index_dir)
    instance.index_path = instance.index_dir / 'faiss.index'
    instance.chunks_path = instance.index_dir / 'chunks.json'
    instance.manifest_path = instance.index_dir / 'manifest.json'
    instance._relocation_proof = proof
    return instance


def test_verified_relocation_loads_existing_index_without_mutating_historical_manifest(configuration):
    manifest_path = _relocate_manifest_metadata(configuration)
    original = manifest_path.read_bytes()
    binding = adapter.create_relocation_binding(configuration)
    # Ordinary preflight remains strict unless the binding is explicitly passed.
    strict = adapter.inspect_setup(configuration)
    assert strict['ready'] is False
    assert any('stale/legacy' in item['reason'] for item in strict['blockers'])

    report = adapter.inspect_setup(configuration, relocation_binding=binding.model_dump(mode='json'))
    assert report['ready'], report['blockers']
    assert report['relocation_audit']['authorized_resource_ids'] == ['index:evidence-index']
    assert report['relocation_audit']['historical_corpus_path'] == r'C:\historical\project\corpus.json'
    assert report['relocation_audit']['current_corpus_path'] == str(Path(configuration.corpus_path).resolve())
    assert report['relocation_audit']['historical_corpus_mtime'] != report['relocation_audit']['current_corpus_mtime']
    setup = adapter.MeasurementSetup.model_validate(report['observed_setup'])
    assert json.loads(setup.environment['resource_relocation_audit']) == report['relocation_audit']
    retriever = _retriever_for_relocation(configuration, report['relocation_proof'])
    assert retriever._index_is_current() is True
    assert manifest_path.read_bytes() == original


@pytest.mark.parametrize('changed', ['corpus_same_size', 'faiss', 'chunks', 'missing_faiss'])
def test_verified_relocation_rejects_changed_or_missing_bytes_without_rebuild(configuration, changed):
    manifest_path = _relocate_manifest_metadata(configuration)
    binding = adapter.create_relocation_binding(configuration)
    report = adapter.inspect_setup(configuration, relocation_binding=binding.model_dump(mode='json'))
    instance = _retriever_for_relocation(configuration, report['relocation_proof'])
    original_manifest = manifest_path.read_bytes()
    if changed == 'corpus_same_size':
        corpus = Path(configuration.corpus_path)
        original = corpus.read_bytes()
        stat = corpus.stat()
        corpus.write_bytes(original.replace(b'SYNTHETIC', b'SAME_SIZE'))
        os.utime(corpus, ns=(stat.st_atime_ns, stat.st_mtime_ns))
        assert corpus.stat().st_size == stat.st_size
    elif changed == 'faiss':
        target = instance.index_path
        original = target.read_bytes()
        target.write_bytes(bytes([original[0] ^ 1]) + original[1:])
    elif changed == 'chunks':
        target = instance.chunks_path
        original = target.read_bytes()
        target.write_bytes(bytes([original[0] ^ 1]) + original[1:])
    else:
        instance.index_path.unlink()
    with pytest.raises(ValueError):
        instance._index_is_current()
    assert manifest_path.read_bytes() == original_manifest


def test_explicit_relocation_binding_generation_rejects_non_path_manifest_changes(configuration):
    manifest_path = _relocate_manifest_metadata(configuration)
    manifest = json.loads(manifest_path.read_text())
    manifest['chunk_size'] = 501
    manifest_path.write_text(json.dumps(manifest, indent=2))
    with pytest.raises(ValueError, match='differs beyond relocation'):
        adapter.create_relocation_binding(configuration)


def test_relocation_binding_cannot_be_created_when_no_relocation_exists(configuration):
    with pytest.raises(ValueError, match='no corpus path/mtime relocation'):
        adapter.create_relocation_binding(configuration)


def test_project_observer_and_runtime_factory_share_relocated_resource_identity(configuration, monkeypatch, tmp_path):
    from app.game.offline.recording_adapters import ProjectObserver
    manifest_path = _relocate_manifest_metadata(configuration)
    historical_manifest_bytes = manifest_path.read_bytes()
    binding = adapter.create_relocation_binding(configuration)
    binding_path = tmp_path / 'resource-relocation.json'
    binding_path.write_text(binding.model_dump_json())
    config_path = tmp_path / 'adapter.json'
    config_path.write_text(configuration.model_dump_json())
    monkeypatch.setenv('VERIFIER_COLLECTION_ADAPTER_CONFIG', str(config_path))
    monkeypatch.setenv('VERIFIER_RESOURCE_RELOCATION_BINDING', str(binding_path))
    report = adapter.inspect_setup(configuration, relocation_binding=binding)
    service = adapter.ServiceObservation.model_validate(report['inventory']['service'])
    monkeypatch.setattr(adapter, 'observe_service', lambda _config: service)
    observer = ProjectObserver()
    observed = observer.snapshot()
    assert observed == adapter.MeasurementSetup.model_validate(report['observed_setup']).resources
    assert manifest_path.read_bytes() == historical_manifest_bytes

    shared_embedding, shared_nli = object(), object()
    retriever = types.SimpleNamespace(corpus_path=adapter.local_path(configuration.corpus_path),
        index_dir=adapter.local_path(configuration.index_dir), chunk_size=configuration.chunk_size,
        model=shared_embedding)
    evidence = types.SimpleNamespace(name='evidence', retriever=retriever, nli=shared_nli)
    semantic = types.SimpleNamespace(name='semantic', model=shared_embedding)
    confidence = types.SimpleNamespace(name='confidence', judgment_provider=types.SimpleNamespace(
        labeler=types.SimpleNamespace(nli=shared_nli), n_samples=configuration.n_samples,
        sampler=types.SimpleNamespace(url=configuration.ollama_url, model=configuration.ollama_model,
            temperature=configuration.temperature, timeout=configuration.timeout)))
    selector = types.SimpleNamespace(_injected=[semantic, evidence, types.SimpleNamespace(name='rule'), confidence])
    assert observer.snapshot_for(selector) == observed
    retriever.index_dir = tmp_path / 'different-index'
    with pytest.raises(ValueError, match='paths/settings differ'):
        observer.snapshot_for(selector)


def test_configured_evidence_constructor_receives_verified_relocation_proof(configuration, monkeypatch):
    manifest_path = _relocate_manifest_metadata(configuration)
    historical_manifest_bytes = manifest_path.read_bytes()
    binding = adapter.create_relocation_binding(configuration)
    report = adapter.inspect_setup(configuration, relocation_binding=binding)
    calls = []
    embedding = types.SimpleNamespace(get_sentence_embedding_dimension=lambda: 384)
    def sentence_model(path, **kwargs):
        return embedding
    nli = types.SimpleNamespace(model=types.SimpleNamespace(config=types.SimpleNamespace(
        id2label={0: 'contradiction', 1: 'entailment', 2: 'neutral'})))
    def load(path, **kwargs):
        return object()
    monkeypatch.setitem(sys.modules, 'sentence_transformers', types.SimpleNamespace(SentenceTransformer=sentence_model))
    monkeypatch.setitem(sys.modules, 'transformers', types.SimpleNamespace(
        AutoModelForSequenceClassification=types.SimpleNamespace(from_pretrained=load),
        AutoTokenizer=types.SimpleNamespace(from_pretrained=load), pipeline=lambda *a, **kw: nli))
    import app.verifiers.evidence_retriever as retrieval
    loaded = types.SimpleNamespace(index=types.SimpleNamespace(ntotal=1, d=384), chunks=[{}])
    monkeypatch.setattr(retrieval, 'EvidenceRetriever', lambda **kwargs: (calls.append(kwargs) or loaded))
    pool = adapter.construct_verifiers(configuration, relocation_proof=report['relocation_proof'])
    assert pool[1].retriever is loaded
    assert calls[0]['corpus_path'] == str(adapter.local_path(configuration.corpus_path))
    assert calls[0]['index_dir'] == adapter.local_path(configuration.index_dir)
    assert calls[0]['relocation_proof']['binding_id'] == binding.binding_id
    assert manifest_path.read_bytes() == historical_manifest_bytes


def test_mock_attempts_feed_existing_calibration(configuration):
    from app.benchmark.collect_costs import collect
    from app.game.offline.calibration import MeasurementSetup, MeasurementInput, calibrate
    from app.models.schemas import VerificationResult
    request = prepare(configuration, preparation())
    setup = MeasurementSetup(**{**request.setup.model_dump(), 'evidence_kind': 'synthetic_test_fixture'})
    request = CollectionRequest(**{**request.model_dump(), 'setup': setup})
    class Verifier:
        def __init__(self, name):
            self.name = name
        def verify(self, *args):
            return VerificationResult(verifier_name=self.name, passed=True, score=1.)
    rows = []
    collect(request, [Verifier(n) for n in ('semantic', 'evidence', 'rule', 'confidence')], setup, rows)
    assert len(rows) == 8
    inputs = MeasurementInput(setup=setup, permitted_datasets=request.permitted_datasets,
        preparation_authorization=request.preparation_authorization, attempts=rows)
    artifact = calibrate(dict(measurements=inputs, final_test_reservation=request.final_test_reservation,
        required_verifiers=('semantic', 'evidence', 'rule', 'confidence'), include_warmups=False,
        freeze_record='SYNTHETIC freeze'))
    assert all(row['attempts'] == 1 for row in artifact.result['estimates'])
    assert len(artifact.result['exclusions']) == 4


def test_prepare_context_preserves_old_recording_categories():
    from tests.test_cost_calibration import integration
    from app.game.offline.prepare_calibrated_context import prepare_context
    from app.game.research.specification import PolicyBuildSpecification
    spec, calibration, contract, recording = integration()
    spec = PolicyBuildSpecification(**{**spec.model_dump(), 'contract': contract, 'recording': recording})
    original = spec.manifest.model_dump_json()
    result = prepare_context(spec, calibration, dict(budget_ms=20., resource_weight_per_ms=.002,
        expected_setup_fingerprint=calibration.request.measurements.setup.fingerprint))
    assert result['incompatible_recordings']
    assert result['recordings_rewritten'] is False
    assert spec.manifest.model_dump_json() == original


def test_initial_export_reuses_detached_reports_without_relabeling():
    from tests.test_cost_calibration import integration
    from tests.test_game_foundation import analysis
    from tests.test_game_offline import report
    from app.game.offline.collection import RecordingRequest, collect, measurement_input
    from app.game.offline.calibration import calibrate
    from app.game.offline.prepare_calibrated_context import prepare_collected_context
    from app.selection.capabilities import CapabilityDescriptor
    from app.verifiers.base_verifier import BaseVerifier
    spec, ignored, contract, recording = integration()
    setup = ignored.request.measurements.setup
    recorded_analysis = analysis()
    recorded_analysis.difficulty = spec.context.plan.difficulty
    recorded_analysis.difficulty_score = spec.context.plan.difficulty_score
    request = RecordingRequest(version='offline_recording_request_v1', intended_use='pilot', study_approval=None,
        preparation_authorization='SYNTHETIC permission', cache_contract='complete_team_independent_v1',
        randomness_control='SYNTHETIC deterministic mocks', execution_configuration_id=setup.resources.manifest_id,
        factory='SYNTHETIC:factory', expected_setup=setup, final_test_reservation=spec.manifest.final_test_reservation,
        permitted_datasets=(('history', 'history-v1'), ('development', 'development-v1')),
        candidates=tuple(dict(verifier_name=n, adapter='generic_v1', registered=True, capability_source='explicit',
            capabilities=CapabilityDescriptor(('arithmetic',))) for n in ('a', 'b')),
        examples=tuple(dict(example_id=p.role, split_identity=p.role, question_id=p.role, run_id=p.role,
            dataset_id=p.dataset_id, role=p.role, purpose='calibration', question=p.role+' question',
            answer='fixture answer', reference=None, analysis=recorded_analysis, label=dict(answer_is_correct=True,
                label_source='fixture-independent-label', label_method='independent_ground_truth',
                provenance='SYNTHETIC independent label')) for p in spec.manifest.partitions))
    class Verifier(BaseVerifier):
        def __init__(self, name):
            self._name = name
        @property
        def name(self):
            return self._name
        def verify(self, *args):
            return report(self.name, metadata={'decision': 'UNSURE'}) if args[0].startswith('history') else report(self.name)
    bundle = collect(request, [Verifier('a'), Verifier('b')], setup,
        types.SimpleNamespace(snapshot=lambda: setup.resources))
    before = bundle.model_dump_json()
    calibration = calibrate(dict(measurements=measurement_input(bundle), final_test_reservation=request.final_test_reservation,
        required_verifiers=('a', 'b'), include_warmups=False, freeze_record='SYNTHETIC freeze'))
    raw = spec.context.model_dump()
    del raw['attempt_costs']
    result = prepare_collected_context(dict(context=raw, contract=contract, recording=recording, attacks=spec.attacks), bundle, calibration,
        dict(budget_ms=20., resource_weight_per_ms=.002, expected_setup_fingerprint=setup.fingerprint))
    assert result['export_kind'] == 'initial_training_export_from_detached_reports'
    assert result['source_bundle_id'] == bundle.bundle_id
    assert all(e['planning_category'] == result['planning_category']
        for p in result['manifest']['partitions'] for e in p['examples'])
    assert bundle.model_dump_json() == before
