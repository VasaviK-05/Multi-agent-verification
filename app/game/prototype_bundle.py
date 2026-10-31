"""Versioned, path-safe offline prototype loading; no inference or activation."""
from dataclasses import asdict,dataclass
import hashlib
import json
from pathlib import Path,PurePosixPath
import re
from typing import Literal
from pydantic import Field,model_validator
from app.game.dependencies import FrozenModel
from app.game.models import content_id
from app.game.artifacts import PolicyArtifact,DeploymentEpisode,InMemoryPolicyProvider
from app.game.task_conditioning import TaskSnapshotBinding,TaskPolicyRouter

class BundleFile(FrozenModel):
    path:str
    sha256:str=Field(pattern=r'^[0-9a-f]{64}$')
    @model_validator(mode='after')
    def relative(self):
        p=PurePosixPath(self.path)
        if (not self.path or '\\' in self.path or ':' in self.path or p.is_absolute()
            or '..' in p.parts or '.' in p.parts or str(p)!=self.path):raise ValueError('unsafe bundle path')
        return self

class PrototypeEntry(FrozenModel):
    task:Literal['arithmetic','factual']
    experimental:bool
    artifact_path:str
    episode_path:str
    reputation_path:str
    costs_path:str
    resources_path:str
    metrics_path:str
    artifact_id:str
    compatibility_id:str
    task_id:str
    reputation_snapshot_id:str
    execution_configuration_id:str
    calibration_id:str
    expected_clean_coverage:float
    reference_required:Literal[True]=True
    # Metadata only. It bounds this prototype, not estimated correctness.
    allowed_question_ids:tuple[str,...]=Field(min_length=1)

class PrototypeManifest(FrozenModel):
    version:Literal['bounded_task_policy_bundle_v1']
    approval:str
    entries:tuple[PrototypeEntry,...]=Field(min_length=1)
    files:tuple[BundleFile,...]=Field(min_length=1)
    unsupported_tasks:tuple[Literal['semantic_comparison'],...]=('semantic_comparison',)
    scope:Literal['prepared_history_development_questions_v1']='prepared_history_development_questions_v1'
    @model_validator(mode='after')
    def unique(self):
        if len({e.task for e in self.entries})!=len(self.entries):raise ValueError('duplicate task')
        paths=[f.path for f in self.files]
        if len(set(paths))!=len(paths):raise ValueError('duplicate file')
        for e in self.entries:
            refs=(e.artifact_path,e.episode_path,e.reputation_path,e.costs_path,e.resources_path,e.metrics_path)
            if any(p not in paths for p in refs):raise ValueError('unlisted entry reference')
            if any(not re.fullmatch('[0-9a-f]{64}',q) for q in e.allowed_question_ids):raise ValueError('invalid question identity')
        return self
    @property
    def bundle_id(self):return content_id(self.model_dump(mode='json'))

def safe_payload(data):
    """Reject private paths/secrets rather than redacting content-addressed bytes."""
    text=data.decode('utf-8')
    if re.search(r'(?<![A-Za-z0-9])[A-Za-z]:[\\/]|/(?:Users|home)/|Bearer\s+\S+|sk-[A-Za-z0-9]{20,}',text):
        raise ValueError('bundle payload contains private path or credential pattern')

@dataclass(frozen=True)
class LoadedPrototype:
    manifest:PrototypeManifest
    artifacts:tuple[PolicyArtifact,...]
    episodes:tuple[DeploymentEpisode,...]
    def provider(self):return InMemoryPolicyProvider(self.artifacts)
    def router(self):
        routes=[]
        for episode in self.episodes:
            c=episode.context;b=TaskSnapshotBinding.model_validate_json(c.task_conditioning_json)
            routes.append(((b.identity.task_id,c.plan.difficulty,c.plan.difficulty_score,c.plan.reference_available),c.budget,True,episode,''))
        return PrototypeRouter(TaskPolicyRouter(routes),self.manifest)

class PrototypeRouter:
    """Bound existing task routing to the package's declared question metadata."""
    def __init__(self,router,manifest):self.router,self.manifest=router,manifest
    def run(self,selector,analysis,request,validation_id,**kwargs):
        from app.game.task_conditioning import analysis_task
        from app.game.execution import GameRun
        from app.decision.decision_engine import DecisionDetail
        try:task=analysis_task(analysis).task_id
        except ValueError:task=None
        entry=next((e for e in self.manifest.entries if e.task_id==task),None)
        if entry and content_id(request.question) not in entry.allowed_question_ids:
            return GameRun((),DecisionDetail(analysis.domain,'unknown',0.,0.,.55,'unknown',()),'uncertain',
                dict(selection_status='study_scope_mismatch',public_status='uncertain',selection_reasons=['outside declared prototype question scope']))
        return self.router.run(selector,analysis,request,validation_id,**kwargs)

def load_prototype(directory,*,allow_synthetic_for_tests=False):
    """Load only manifest-listed relative files, check hashes and bound identities."""
    base=Path(directory).resolve()
    raw_manifest=(base/'manifest.json').read_bytes();safe_payload(raw_manifest)
    manifest=PrototypeManifest.model_validate_json(raw_manifest)
    if {p.relative_to(base).as_posix() for p in base.rglob('*') if p.is_file()}!={f.path for f in manifest.files}|{'manifest.json'}:
        raise ValueError('unlisted or missing bundle files')
    payloads={}
    for f in manifest.files:
        path=(base/f.path).resolve()
        if not path.is_relative_to(base):raise ValueError('bundle path escapes root')
        raw=path.read_bytes();safe_payload(raw)
        if hashlib.sha256(raw).hexdigest()!=f.sha256:raise ValueError('bundle file digest mismatch: '+f.path)
        payloads[f.path]=raw
    def read(path):return json.loads(payloads[path])
    artifacts=[];episodes=[]
    for e in manifest.entries:
        a=PolicyArtifact.model_validate_json(payloads[e.artifact_path])
        if a.policy.provenance.evidence_kind!='empirical' and not allow_synthetic_for_tests:
            raise ValueError('synthetic policy requires explicit test-only permission')
        episode=DeploymentEpisode.model_validate_json(payloads[e.episode_path])
        c=a.context;binding=TaskSnapshotBinding.model_validate_json(c.task_conditioning_json)
        if binding.identity.requirements!=(('arithmetic',) if e.task=='arithmetic' else ('direct_fact',)):
            raise ValueError('declared task differs from artifact requirements')
        if e.task=='factual' and not e.experimental:raise ValueError('factual prototype must be experimental')
        if (a.artifact_id!=e.artifact_id or c.compatibility_id!=e.compatibility_id or binding.identity.task_id!=e.task_id
            or c.reputation_snapshot_id!=e.reputation_snapshot_id or a.execution_configuration_id!=e.execution_configuration_id
            or episode.context!=c or episode.contract!=a.contract or not c.plan.reference_available):raise ValueError('entry/episode/artifact identity mismatch')
        if read(e.reputation_path)!=[asdict(s) for s in c.plan.reputation_statistics]:raise ValueError('frozen reputation differs')
        costs=read(e.costs_path)
        if (costs['calibration_id']!=e.calibration_id or costs['budget']!=c.budget
            or costs['attempt_costs']!=[list(v) for v in c.attempt_costs] or costs['units']!=c.cost_units):raise ValueError('cost summary differs')
        if read(e.resources_path)!=a.contract.resource_manifest.model_dump(mode='json'):raise ValueError('resource expectations differ')
        coverage=json.loads(c.clean_coverage_json)
        if coverage['minimum']!=e.expected_clean_coverage:raise ValueError('coverage configuration differs')
        metrics=read(e.metrics_path)
        if metrics['artifact_id']!=a.artifact_id:raise ValueError('metrics artifact differs')
        probabilities=dict(a.policy.solution.probabilities)
        if metrics['all_strategies']!=[dict(**s.model_dump(mode='json'),probability=probabilities[s.strategy_id]) for s in a.policy.strategies]:
            raise ValueError('metrics strategy probabilities differ from unmodified policy')
        artifacts.append(a);episodes.append(episode)
    return LoadedPrototype(manifest,tuple(artifacts),tuple(episodes))
