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
    def snapshot(self):
        # Reuse the current project owner's local-resource and service observers.
        from app.benchmark.project_adapter import AdapterConfiguration, inspect_setup, observe_service
        from app.game.offline.calibration import read_json
        configuration = AdapterConfiguration.model_validate(read_json(os.environ['VERIFIER_COLLECTION_ADAPTER_CONFIG']))
        report = inspect_setup(configuration)
        if not report['ready']:
            raise ValueError(json.dumps(report['blockers']))
        if observe_service(configuration).model_dump(mode='json') != report['inventory']['service']:
            raise ValueError('live service differs from declared resource observation')
        return MeasurementSetup.model_validate(report['observed_setup']).resources


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
