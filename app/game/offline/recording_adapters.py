"""Resource-observing bridges for existing adapters, plus a rule-only smoke CLI."""
import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import subprocess
import time

from app.game.models import content_id
from app.game.offline.calibration import MeasurementSetup
from app.game.resource_provenance import ResourceManifest

ROOT = Path(__file__).resolve().parents[3]


class ArithmeticObserver:
    """Narrow real rule/semantic setup; no corpus, index, NLI or service claims."""
    def __init__(self, configuration):
        if set(configuration) != {'embedding_snapshot', 'torch_num_threads'}:
            raise ValueError('arithmetic adapter requires embedding_snapshot and torch_num_threads only')
        if type(configuration['torch_num_threads']) is not int or configuration['torch_num_threads'] < 1:
            raise ValueError('torch_num_threads must be an explicit positive integer')
        self.configuration = configuration

    def snapshot(self):
        from app.benchmark.project_adapter import directory_digest, file_digest, local_path
        from app.verifiers.semantic_verifier import SemanticVerifier
        model = directory_digest(self.configuration['embedding_snapshot'])
        path = local_path(self.configuration['embedding_snapshot'])
        if not (path / 'modules.json').is_file():
            raise ValueError('local SentenceTransformer snapshot lacks modules.json')
        rule = RuleObserver().snapshot().verifiers[0].model_dump(mode='json')
        shared = dict(kind='configuration', resource_id='arithmetic-local-runtime',
                      sha256=content_id(self.configuration))
        rule['resources'].append(shared)
        files = ('app/verifiers/semantic_verifier.py', 'app/verifiers/base_verifier.py',
                 'app/verifiers/claim_generator.py', 'app/verifiers/confidence_verifier.py',
                 'app/models/schemas.py', 'app/game/offline/recording_adapters.py')
        semantic = dict(verifier_name='semantic', resources=[shared,
            dict(kind='implementation', resource_id='semantic-source',
                 sha256=content_id([(p, file_digest(ROOT / p)) for p in files])),
            dict(kind='configuration', resource_id='semantic-constructor',
                 sha256=content_id(dict(model_name=str(path),
                     comparison_mode=SemanticVerifier.DEFAULT_COMPARISON_MODE))),
            dict(kind='model', resource_id='local-embedding-snapshot', sha256=model['sha256'])])
        return ResourceManifest(verifiers=(rule, semantic))


def arithmetic_factory():
    """Use installed embedding bytes and unchanged project verifier constructors."""
    from app.game.offline.calibration import read_json
    from app.benchmark.project_adapter import hardware, local_path, PACKAGES
    path = os.environ.get('VERIFIER_ARITHMETIC_ADAPTER_CONFIG')
    if not path:
        raise ValueError('set VERIFIER_ARITHMETIC_ADAPTER_CONFIG to the explicit narrow adapter configuration')
    configuration = read_json(path)
    observer = ArithmeticObserver(configuration)
    before = observer.snapshot()
    import torch
    from sentence_transformers import SentenceTransformer
    from app.verifiers.rule_verifier import RuleVerifier
    from app.verifiers.semantic_verifier import SemanticVerifier
    torch.set_num_threads(configuration['torch_num_threads'])
    embedding = SentenceTransformer(str(local_path(configuration['embedding_snapshot'])),
                                   device='cpu', local_files_only=True)
    pool = [RuleVerifier(), SemanticVerifier(model=embedding,
        model_name=str(local_path(configuration['embedding_snapshot'])))]
    after = observer.snapshot()
    if after != before:
        raise ValueError('resources changed during arithmetic adapter initialization')
    environment = hardware()
    environment.update(initialization='eager local embedding; excluded from measured attempt time',
        torch_intraop_threads=str(torch.get_num_threads()),
        collection_scope='rule and semantic only; no NLI/index/corpus/provider')
    versions = {name: importlib.metadata.version(name) for name in PACKAGES}
    setup = MeasurementSetup(resources=after, environment=environment, dependency_versions=versions,
        code_revision=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        application_source_digest=content_id([(p.relative_to(ROOT).as_posix(),
            hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted((ROOT / 'app').rglob('*.py'))]),
        evidence_kind='empirical')
    return pool, setup, observer


class RuleObserver:
    """Observe actual source bytes and the existing no-argument rule configuration."""
    def snapshot(self):
        files = ('app/verifiers/rule_verifier.py', 'app/verifiers/base_verifier.py',
                 'app/models/schemas.py', 'app/game/offline/recording_adapters.py')
        hashes = [(p, hashlib.sha256((ROOT / p).read_bytes()).hexdigest()) for p in files]
        return ResourceManifest(verifiers=(dict(verifier_name='rule', resources=(
            dict(kind='implementation', resource_id='rule-source', sha256=content_id(hashes)),
            dict(kind='configuration', resource_id='rule-constructor',
                 sha256=content_id(dict(constructor='RuleVerifier()', source_hashes=hashes))),)),))


def rule_factory():
    from app.verifiers.rule_verifier import RuleVerifier
    observer = RuleObserver()
    setup = MeasurementSetup(resources=observer.snapshot(), environment=dict(os=platform.platform(),
        python=platform.python_version(), execution='sequential CPU; no model/provider'),
        dependency_versions={'pydantic': importlib.metadata.version('pydantic')},
        code_revision=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        application_source_digest=content_id([(p.relative_to(ROOT).as_posix(),
            hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted((ROOT / 'app').rglob('*.py'))]),
        evidence_kind='empirical')
    return [RuleVerifier()], setup, observer


class ProjectObserver:
    def __init__(self):
        self._relocation_state = None

    def snapshot(self):
        # Reuse the current project owner's local-resource and service observers.
        from app.benchmark.project_adapter import AdapterConfiguration, inspect_setup, observe_service
        from app.game.offline.calibration import read_json
        configuration = AdapterConfiguration.model_validate(read_json(os.environ['VERIFIER_COLLECTION_ADAPTER_CONFIG']))
        report = inspect_setup(configuration)
        self._relocation_state = None
        if report['ready']:
            if observe_service(configuration).model_dump(mode='json') != report['inventory']['service']:
                raise ValueError('live service differs from declared resource observation')
            from app.game.resource_provenance import ResourceManifest
            return ResourceManifest.model_validate(report['observed_setup']['resources'])

        binding_path = os.environ.get('VERIFIER_RESOURCE_RELOCATION_BINDING')
        allowed_blocker = {
            'resource': 'index_provenance',
            'reason': 'index manifest is stale/legacy; explicit separate index preparation is required',
            'owner': 'resource/collection owner',
        }
        if not binding_path or report['blockers'] != [allowed_blocker]:
            raise ValueError(json.dumps(report['blockers']))

        from app.benchmark.project_adapter import (
            content_id, file_digest, index_receipt,
            local_path, source_constants,
        )
        from app.game.offline.resource_relocation import ResourceRelocationBinding
        from app.game.resource_provenance import ResourceManifest

        binding = ResourceRelocationBinding.model_validate(read_json(binding_path))
        base = local_path(configuration.index_dir)
        corpus_path = local_path(configuration.corpus_path)
        manifest_path = base / 'manifest.json'
        receipt_path = local_path(configuration.index_receipt)
        stored_manifest = read_json(manifest_path)
        inventory = report['inventory']
        index_hashes = inventory['index']
        corpus_sha = inventory['corpus']['sha256']
        receipt = read_json(receipt_path)
        expected_receipt = index_receipt(configuration, inventory['embedding_snapshot']['sha256'], corpus_sha, index_hashes)
        if receipt != expected_receipt:
            raise ValueError('index receipt differs from observed corpus, vectors, chunks, or embedding')

        constants = source_constants('app/verifiers/evidence_retriever.py', {'EMBEDDING_MODEL', 'MANIFEST_VERSION'})
        stat = corpus_path.stat()
        corpus_version = 'sha256:' + corpus_sha
        current_manifest = dict(version=constants['MANIFEST_VERSION'], corpus_path=str(corpus_path),
            corpus_size=stat.st_size, corpus_mtime=stat.st_mtime, corpus_sha256=corpus_sha,
            corpus_version=corpus_version, chunk_size=configuration.chunk_size,
            embedding_model=constants['EMBEDDING_MODEL'], index_version='idx-' + hashlib.sha256(
                json.dumps([corpus_version, configuration.chunk_size, constants['EMBEDDING_MODEL']]).encode()).hexdigest()[:12])

        source = lambda names: content_id([(name, file_digest(ROOT / name)) for name in names])
        shared = ['app/verifiers/base_verifier.py', 'app/models/schemas.py', 'app/benchmark/project_adapter.py']
        verifier_files = {
            'semantic': ['app/verifiers/semantic_verifier.py', 'app/verifiers/claim_generator.py', 'app/verifiers/confidence_verifier.py'],
            'evidence': ['app/verifiers/evidence_verifier.py', 'app/verifiers/evidence_retriever.py', 'app/verifiers/claim_generator.py'],
            'rule': ['app/verifiers/rule_verifier.py'],
            'confidence': ['app/verifiers/confidence_verifier.py', 'app/verifiers/self_consistency.py', 'app/verifiers/evidence_verifier.py', 'app/verifiers/claim_generator.py'],
        }
        prompt = source_constants('app/verifiers/self_consistency.py', {'SHORT_ANSWER_PROMPT'})['SHORT_ANSWER_PROMPT']
        semantic_configuration = configuration.model_dump(exclude={'embedding_snapshot', 'nli_snapshot', 'index_receipt', 'service_observation'})
        def resource(kind, name, digest):
            return dict(kind=kind, resource_id=name, sha256=digest)
        embedding = resource('model', 'local-embedding-snapshot', inventory['embedding_snapshot']['sha256'])
        nli = resource('model', 'local-nli-snapshot', inventory['nli_snapshot']['sha256'])
        rows = []
        for name in ('semantic', 'evidence', 'rule', 'confidence'):
            resources = [resource('implementation', name+'-implementation', source(shared + verifier_files[name])),
                resource('configuration', name+'-adapter-configuration', content_id(semantic_configuration))]
            if name == 'semantic':
                resources.append(embedding)
            elif name == 'evidence':
                resources += [embedding, nli, resource('corpus', 'evidence-corpus', corpus_sha),
                    resource('index', 'evidence-index', content_id([index_hashes, receipt]))]
            elif name == 'confidence':
                service = inventory['service']
                resources += [nli, resource('model', 'ollama-model', service['model_digest'][7:]),
                    resource('prompt', 'self-consistency-short-answer', content_id(prompt)),
                    resource('service', 'ollama-service', content_id(service))]
            rows.append(dict(verifier_name=name, resources=resources))
        resources = ResourceManifest(verifiers=tuple(rows))
        if observe_service(configuration).model_dump(mode='json') != inventory['service']:
            raise ValueError('live service differs from declared resource observation')
        self._relocation_state = dict(binding=binding, stored_manifest=stored_manifest,
            current_manifest=current_manifest, corpus_path=corpus_path, manifest_path=manifest_path,
            corpus_sha256=corpus_sha, index_hashes=index_hashes, receipt_path=receipt_path,
            receipt=receipt, expected_receipt=expected_receipt,
            embedding_model_sha256=inventory['embedding_snapshot']['sha256'],
            nli_model_sha256=inventory['nli_snapshot']['sha256'],
            semantic_configuration_sha256=content_id(semantic_configuration),
            resources=resources)
        return resources

    def authorize_relocation(self, expected, observed):
        if self._relocation_state is None:
            raise ValueError('no explicit verified relocation binding was used')
        from app.game.offline.resource_relocation import verify_relocated_index
        state = self._relocation_state
        if observed != state['resources']:
            raise ValueError('observed resource manifest changed after relocation verification')
        return verify_relocated_index(state['binding'], expected_manifest=expected,
            observed_manifest=observed, stored_manifest=state['stored_manifest'],
            current_manifest=state['current_manifest'], corpus_path=state['corpus_path'],
            manifest_path=state['manifest_path'], corpus_sha256=state['corpus_sha256'],
            index_hashes=state['index_hashes'], receipt_path=state['receipt_path'],
            receipt=state['receipt'], expected_receipt=state['expected_receipt'],
            embedding_model_sha256=state['embedding_model_sha256'],
            nli_model_sha256=state['nli_model_sha256'],
            semantic_configuration_sha256=state['semantic_configuration_sha256'])


def project_factory():
    from app.benchmark.project_adapter import create_verifiers
    verifiers, setup = create_verifiers()
    return verifiers, setup, ProjectObserver()


def main(argv=None):
    parser = argparse.ArgumentParser(description='Ad hoc real rule-adapter smoke only; no study labels or split claims')
    parser.add_argument('--question', required=True)
    parser.add_argument('--answer', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    # Reserve output before calling an adapter. This command does not accept files
    # of examples or final outcomes and cannot produce a TrainingManifest.
    with args.output.open('x', encoding='utf-8') as handle:
        verifiers, setup, observer = rule_factory()
        before = observer.snapshot()
        started = time.perf_counter()
        report = verifiers[0].verify(args.question, args.answer)
        duration = (time.perf_counter()-started)*1000.
        after = observer.snapshot()
        json.dump(dict(intended_use='smoke', independently_labelled=False, suitable_for_fitting=False,
            question=args.question, answer=args.answer, report=report.model_dump(mode='json'),
            duration_ms=duration, observed_setup=setup.model_dump(mode='json'),
            resources_unchanged=before == after, policy_created=False), handle, indent=2)
    return 0 if before == after else 2


if __name__ == '__main__':
    raise SystemExit(main())
