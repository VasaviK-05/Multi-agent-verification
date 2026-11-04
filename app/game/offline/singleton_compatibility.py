"""Exact frozen singleton execution closure; the four-candidate plan is retained.

This is a separate transfer from compound execution. Only probability-one Rule
or Evidence artifacts listed in the immutable transfer can use it. Unselected
names remain planning metadata but can never be resolved by this selector.
"""
from pathlib import Path
import inspect

from app.benchmark import project_adapter as a
from app.game.models import content_id
from app.game.resource_provenance import ResourceManifest
from app.game.offline.reconciled_resources import (
    OLD_CONFIGURATION, semantic_configuration, check_dependencies, inspect_required,
    instance_settings, construct_evidence)
from app.selection.verifier_selector import VerifierSelector
from app.selection.capabilities import BUILTIN_CAPABILITIES
from app.selection.models import VerifierUnavailable

TRANSFER_ID = 'ddbb12d1a91ee520887ee0462e81a57ea34109b821487b8cc045a90b268eec87'


def transfer_for(artifact):
    from app.game.artifacts import PolicyArtifact
    if not isinstance(artifact,PolicyArtifact):raise ValueError('frozen atomic PolicyArtifact required')
    value = a.read_json(a.ROOT / 'reconciliation/singleton-transfer-v1.json')
    if value.get('transfer_id') != TRANSFER_ID or content_id({k:v for k,v in value.items() if k!='transfer_id'}) != TRANSFER_ID:
        raise ValueError('unreviewed singleton transfer')
    binding = next((b for b in value['bindings'] if b['artifact_id']==artifact.artifact_id),None)
    if binding is None:
        raise ValueError('unapproved singleton artifact')
    probabilities = tuple((sid,p) for sid,p in artifact.policy.solution.probabilities if p!=0)
    if probabilities != ((binding['strategy_id'],1.),):
        raise ValueError('singleton strategy support/probabilities differ')
    strategy = next(s for s in artifact.policy.strategies if s.strategy_id==binding['strategy_id'])
    if strategy.verifiers!=(binding['selected'],) or strategy.aggregation!=binding['aggregation']:
        raise ValueError('singleton strategy/aggregation differs')
    if {c.verifier_name for c in artifact.context.plan.candidates}!={'semantic','evidence','rule','confidence'}:
        raise ValueError('original planning candidate contract must remain intact')
    return value,binding


def transition(artifact, config):
    value,binding = transfer_for(artifact)
    check_dependencies()
    for path,digest in value['target_files'].items():
        if a.file_digest(a.ROOT/path)!=digest:
            raise ValueError('unreviewed required singleton implementation: '+path)
    current=semantic_configuration(config)
    paths={'corpus_path','index_dir','resource_relocation_binding'}
    if {k:v for k,v in current.items() if k not in paths}!={k:v for k,v in OLD_CONFIGURATION.items() if k not in paths}:
        raise ValueError('unreviewed singleton configuration')
    original=artifact.contract.resource_manifest
    historical=ResourceManifest(verifiers=tuple(v for v in original.verifiers if v.verifier_name==binding['selected']))
    if historical.manifest_id!=binding['historical_scope_id']:
        raise ValueError('singleton historical resource identity differs')
    data=historical.model_dump(mode='json')
    for verifier in data['verifiers']:
        for row in verifier['resources']:
            if row['kind']=='implementation':
                source=value['implementation_transitions'][binding['selected']]
                if row['sha256']!=source['old']:raise ValueError('singleton historical implementation differs')
                row['sha256']=source['new']
            elif row['kind']=='configuration':
                if row['sha256']!=content_id(OLD_CONFIGURATION):raise ValueError('singleton historical settings differ')
                row['sha256']=content_id(current)
    return binding,historical,ResourceManifest.model_validate(data)


def observe(config, intermediate, selected):
    if selected=='evidence':
        return inspect_required(config,intermediate,names=('evidence',))
    if selected!='rule':raise ValueError('unsupported singleton closure')
    if config.resource_relocation_binding:
        raise ValueError('Rule has no index relocation dependency')
    files=['app/verifiers/base_verifier.py','app/models/schemas.py','app/benchmark/project_adapter.py','app/verifiers/rule_verifier.py']
    observed=ResourceManifest(verifiers=(dict(verifier_name='rule',resources=(
        dict(kind='implementation',resource_id='rule-implementation',sha256=content_id([(p,a.file_digest(a.ROOT/p)) for p in files])),
        dict(kind='configuration',resource_id='rule-adapter-configuration',sha256=content_id(semantic_configuration(config))))),))
    if observed!=intermediate:raise ValueError('required Rule resources differ')
    return observed,None,None


class SingletonSelector(VerifierSelector):
    """Plan with the original roster; resolve only the certified singleton."""
    def __init__(self, native):
        super().__init__(capabilities=BUILTIN_CAPABILITIES)
        self._approved_name=native.name
        self._cache[native.name]=native

    def resolve(self,name):
        if name!=self._approved_name:
            raise VerifierUnavailable('unused singleton planning candidate cannot be constructed/dispatched: '+name)
        return self._cache[name]


def settings(native):
    if native.name=='evidence':return instance_settings((native,))
    values=tuple(sorted((k,v if type(v) in (str,int,float,bool,type(None)) else id(v))
        for k,v in vars(native).items() if k!='_start'))
    return (id(native),id(type(native).verify),values)


def require_native(native,config,selected):
    from app.verifiers.rule_verifier import RuleVerifier
    from app.verifiers.evidence_verifier import EvidenceVerifier
    expected=RuleVerifier if selected=='rule' else EvidenceVerifier
    if type(native) is not expected:raise ValueError('selected singleton is not the reviewed native class')
    if selected=='evidence':
        signature=inspect.signature(EvidenceVerifier.__init__)
        for name in ('top_k','min_retrieval_score','retrieval_margin','min_nli_score','min_topic_coverage',
                     'topic_margin','max_premise_windows','max_premise_chars'):
            if getattr(native,name)!=signature.parameters[name].default:
                raise ValueError('native Evidence constructor differs: '+name)
        retriever=native.retriever
        if (Path(retriever.corpus_path).resolve()!=a.local_path(config.corpus_path) or
            Path(retriever.index_dir).resolve()!=a.local_path(config.index_dir) or retriever.chunk_size!=config.chunk_size):
            raise ValueError('native Evidence retrieval settings differ')


class SingletonObserver:
    def __init__(self,config,artifact,native):
        self.config,self.artifact,self.native=config,artifact,native
        self.binding,self.historical,self.intermediate=transition(artifact,config)
        require_native(native,config,self.binding['selected'])
        self.settings=settings(native)
        self.last_proof=None

    def snapshot_for(self,selector):
        try:
            bound=isinstance(selector,SingletonSelector) and selector.resolve(self.binding['selected']) is self.native
        except (VerifierUnavailable,KeyError,AttributeError):bound=False
        if not bound:
            raise ValueError('actual selected singleton instance differs')
        require_native(self.native,self.config,self.binding['selected'])
        if settings(self.native)!=self.settings:raise ValueError('singleton constructor/model settings drift')
        _,historical,intermediate=transition(self.artifact,self.config)
        if historical!=self.historical or intermediate!=self.intermediate:raise ValueError('singleton transition drift')
        actual,relocation,_=observe(self.config,self.intermediate,self.binding['selected'])
        self.last_proof=dict(version='verified_frozen_singleton_execution_v1',transfer_id=TRANSFER_ID,
            artifact_id=self.artifact.artifact_id,original_full_manifest_id=self.artifact.contract.resource_manifest.manifest_id,
            historical_scope_id=self.historical.manifest_id,intermediate_manifest_id=self.intermediate.manifest_id,
            observed_manifest_id=actual.manifest_id,original_context_id=self.artifact.context.compatibility_id,
            strategy_id=self.binding['strategy_id'],aggregation=self.binding['aggregation'],
            native_selected=[self.binding['selected']],planning_candidates_preserved=True,
            active_instances_checked=True,constructor_settings_id=content_id(self.settings),relocation=relocation)
        self.last_proof['proof_id']=content_id(self.last_proof)
        return actual

    def authorize_artifact(self,artifact,actual):
        if artifact!=self.artifact or self.last_proof is None or actual.manifest_id!=self.last_proof['observed_manifest_id']:
            raise ValueError('unbound singleton artifact/resource proof')
        transfer_for(artifact)
        return self.last_proof

    def snapshot(self):raise ValueError('singleton proof requires actual selected instance')


def create_singleton(configuration,artifact):
    config=a.AdapterConfiguration.model_validate(configuration)
    binding,_,intermediate=transition(artifact,config)
    before,_,load_proof=observe(config,intermediate,binding['selected'])
    if binding['selected']=='rule':
        from app.verifiers.rule_verifier import RuleVerifier
        native=RuleVerifier()
    else:native=construct_evidence(config,load_proof)
    observer=SingletonObserver(config,artifact,native)
    selector=SingletonSelector(native)
    if observer.snapshot_for(selector)!=before:raise ValueError('singleton resources changed during initialization')
    return selector,observer


def prepare_singleton_relocation(configuration,artifact):
    """Metadata-only preparation for this factual artifact's exact E scope."""
    config=a.AdapterConfiguration.model_validate(configuration)
    binding,_,intermediate=transition(artifact,config)
    if binding['selected']!='evidence':raise ValueError('Rule has no relocation dependency')
    actual,_,state=inspect_required(config,intermediate,prepare=True,names=('evidence',))
    if state is None:raise ValueError('no relocation exists')
    from app.game.offline.reconciled_resources import make_relocation_binding
    return make_relocation_binding(config,intermediate,actual,state)
