"""Reference-specific frozen full-roster contract; zero generation in binding checks."""
from pathlib import Path

from app.benchmark import project_adapter as adapter
from app.game.models import content_id
from app.game.resource_provenance import ResourceManifest
from app.game.offline.reconciled_resources import OLD_CONFIGURATION, semantic_configuration, instance_settings, check_dependencies

CAPSULE_ID = '8ae545bf6762dfcc1708be8ef41f347e9f8d2d94d0d05ad8a13782ed639579bc'


def reference_intermediate(artifact, config):
    check_dependencies()
    if artifact.artifact_id != 'ee32392c870fba30b08b4f7509af645019d9f8b92dc7c39bafeceb8207745c8f':
        raise ValueError('reference contract required; singleton contraction is not authorized')
    root = adapter.ROOT
    capsule = adapter.read_json(root / 'reconciliation/reference-source.json')
    if capsule.get('capsule_id') != CAPSULE_ID or content_id({k: v for k, v in capsule.items() if k != 'capsule_id'}) != CAPSULE_ID:
        raise ValueError('unreviewed reference source capsule')
    for path, digest in capsule['target_files'].items():
        if adapter.file_digest(root / path) != digest:
            raise ValueError('unreviewed reference implementation bytes: ' + path)
    service = adapter.ServiceObservation.model_validate(adapter.read_json(root / 'reconciliation/reference-service.json'))
    original = artifact.contract.resource_manifest
    # Service/model/prompt/sampling requirements come from THIS frozen artifact.
    confidence = next(v for v in original.verifiers if v.verifier_name == 'confidence')
    service_hash = next(r.sha256 for r in confidence.resources if r.kind == 'service')
    if service_hash != content_id(service.model_dump(mode='json')):
        raise ValueError('artifact does not bind the reviewed current-service reference contract')
    current = semantic_configuration(config)
    paths = {'corpus_path', 'index_dir', 'resource_relocation_binding'}
    if {k: v for k, v in current.items() if k not in paths} != {k: v for k, v in OLD_CONFIGURATION.items() if k not in paths}:
        raise ValueError('reference sampling/service/semantic settings differ')
    if adapter.observe_service(config) != service:
        raise ValueError('reference live service/model differs from its frozen contract')
    data = original.model_dump(mode='json')
    for verifier in data['verifiers']:
        for row in verifier['resources']:
            if row['kind'] == 'implementation':
                transition = capsule['transitions'][verifier['verifier_name']]
                if row['sha256'] != transition['old']:
                    raise ValueError('unreviewed reference historical implementation')
                row['sha256'] = transition['new']
            elif row['kind'] == 'configuration':
                if row['sha256'] != content_id(OLD_CONFIGURATION):
                    raise ValueError('unreviewed reference historical configuration')
                row['sha256'] = content_id(current)
    return ResourceManifest.model_validate(data)


def reference_settings(pool):
    from app.verifiers.self_consistency import SHORT_ANSWER_PROMPT
    by_name = {v.name: v for v in pool}
    provider = by_name['confidence'].judgment_provider
    sampler = provider.sampler
    return (instance_settings([by_name['evidence'], by_name['rule']]),
        id(by_name['semantic'].model), by_name['semantic'].comparison_mode,
        id(provider), id(provider.labeler), id(provider.labeler.nli), id(sampler),
        sampler.url, sampler.model, sampler.temperature, sampler.timeout, provider.n_samples,
        content_id(SHORT_ANSWER_PROMPT))


class ReferenceObserver:
    def __init__(self, artifact, config, pool):
        from app.game.offline.recording_adapters import ProjectObserver
        self.artifact, self.config, self.pool = artifact, config, tuple(pool)
        self.native = ProjectObserver(self.pool)
        self.settings = reference_settings(self.pool)
        self.last_proof = None

    def snapshot_for(self, selector):
        if any(selector.resolve(v.name) is not v for v in self.pool) or reference_settings(self.pool) != self.settings:
            raise ValueError('reference actual instances/settings drift')
        intermediate = reference_intermediate(self.artifact, self.config)
        # Do not use ProjectObserver's environment-based snapshot: retain this
        # observer's captured configuration and attest the actual selected pool.
        report = adapter.inspect_setup(self.config)
        if not report['ready']:
            raise ValueError(str(report['blockers']))
        self.native._attest_active_verifiers(self.pool, self.config, report)
        observed = ResourceManifest.model_validate(report['observed_setup']['resources'])
        state = report.get('_relocation_state', {})
        historical_index = next(r.sha256 for v in intermediate.verifiers for r in v.resources if r.resource_id=='evidence-index')
        if not state or content_id([state['index_hashes'],state['expected_receipt']]) != historical_index:
            raise ValueError('reference historical index/receipt bytes differ')
        relocation, index_observation = None, None
        if observed != intermediate:
            from app.game.offline.resource_relocation import verify_relocated_index
            state = report.get('_relocation_state', {})
            if state.get('stored') == state.get('current'):
                # The integration inspector always hashes a freshly serialized
                # logical manifest, even at the same location. Bind that exact
                # observation-only serialization to unchanged physical bytes.
                logical_index = content_id([adapter._current_index_hashes(state['index_hashes'],state['current']),state['expected_receipt']])
                data = intermediate.model_dump(mode='json')
                for verifier in data['verifiers']:
                    for row in verifier['resources']:
                        if row['resource_id']=='evidence-index':row['sha256']=logical_index
                if ResourceManifest.model_validate(data) != observed:
                    raise ValueError('reference non-serialization required resources differ')
                index_observation=dict(version='exact_index_observation_serialization_v1',
                    physical_index_id=historical_index,logical_index_id=logical_index,
                    physical_manifest_sha256=state['index_hashes']['manifest.json'],no_file_changes=True)
            elif 'binding' not in state:
                raise ValueError('reference required resources differ')
            else:
                relocation = verify_relocated_index(state['binding'], expected_manifest=intermediate,
                    observed_manifest=observed, stored_manifest=state['stored'], current_manifest=state['current'],
                    corpus_path=Path(state['corpus_path']), manifest_path=Path(state['manifest_path']),
                    corpus_sha256=state['corpus_sha256'], index_hashes=state['index_hashes'],
                    receipt_path=Path(state['receipt_path']), receipt=state['expected_receipt'], expected_receipt=state['expected_receipt'],
                    embedding_model_sha256=state['embedding_model_sha256'], nli_model_sha256=state['nli_model_sha256'],
                    semantic_configuration_sha256=state['semantic_configuration_sha256'])
        self.last_proof = dict(version='reference_source_resource_transition_v1', artifact_id=self.artifact.artifact_id,
            historical_manifest_id=self.artifact.contract.resource_manifest.manifest_id,
            intermediate_manifest_id=intermediate.manifest_id, observed_manifest_id=observed.manifest_id,
            reference_source_capsule_id=CAPSULE_ID, relocation=relocation,index_observation=index_observation,active_instances_checked=True)
        self.last_proof['proof_id'] = content_id(self.last_proof)
        return observed

    def authorize_artifact(self, artifact, observed):
        if artifact != self.artifact or self.last_proof is None or self.last_proof['observed_manifest_id'] != observed.manifest_id:
            raise ValueError('unbound reference artifact proof')
        return self.last_proof

    def snapshot(self):
        raise ValueError('reference proof requires actual selected instances')


def create_reference(configuration, artifact):
    config = adapter.AdapterConfiguration.model_validate(configuration)
    reference_intermediate(artifact, config)
    report = adapter.inspect_setup(config)
    if not report['ready']:
        raise ValueError(str(report['blockers']))
    proof = report.get('relocation_proof')
    pool = adapter.construct_verifiers(config, relocation_proof=proof)
    observer = ReferenceObserver(artifact, config, pool)
    from app.selection.verifier_selector import VerifierSelector
    from app.selection.capabilities import BUILTIN_CAPABILITIES
    selector = VerifierSelector(verifiers=pool, capabilities=BUILTIN_CAPABILITIES)
    observer.snapshot_for(selector)
    return pool, observer
