"""Minimal data-only policy bundle; loading never opens model/private source paths."""
import argparse,json
from pathlib import Path
from app.game.artifacts import PolicyArtifact
from app.game.component_execution import ComponentPolicy
from app.game.question_routing import QuestionPolicyConfiguration,configuration_from_atomic_artifacts
from app.analysis.reference_study_analyzer import VERSION
from app.game.models import content_id
def load(path):
    value=json.loads(Path(path).read_text(encoding='utf-8'))
    if value['version']!='supported_policy_bundle_v1':raise ValueError('unsupported policy package')
    payload={k:v for k,v in value.items() if k!='bundle_id'}
    if value['bundle_id']!=content_id(payload):raise ValueError('policy bundle digest differs')
    atomic=tuple(PolicyArtifact.model_validate(v) for v in value['atomic_artifacts'])
    compound=ComponentPolicy.model_validate(value['compound_policy'])
    base,provider=configuration_from_atomic_artifacts(atomic)
    config=QuestionPolicyConfiguration(atomic_routes=base.atomic_routes,
        component_entries=((compound.contract.question_signature,compound.contract.budget,True,compound),),
        allowlist=frozenset(value['allowed_questions']),reference_question_version=VERSION)
    return config,provider,compound

def load_runtime_candidate(path, *, repository_root=None):
    """Load a package only when its publisher has marked it deployment-active.

    Typed loading and a valid digest are not deployment authorization. The
    current published package is intentionally inactive and remains so.
    """
    value=json.loads(Path(path).read_text(encoding='utf-8'))
    config,provider,compound=load(path)
    if value.get('deployment_active') is not True:
        raise ValueError('policy package is published for offline evaluation and is not deployment-active')
    from app.game.resource_transfer import validate_compound_transfer
    transfer=value.get('compound_transfer')
    if transfer is None:
        raise ValueError('deployment-active package is missing its required compound transfer proof')
    transfer=validate_compound_transfer(transfer,compound,repository_root=repository_root)
    return config,provider,compound,transfer,value['bundle_id']
def build(repo,output):
    from scripts.replay_remaining_policies import load_registry
    config,_,compound,atomic=load_registry(repo)
    current=repo/'artifacts/remaining-category-studies-v1/reference-50-v1'
    summary=json.loads((current/'fit/summary.json').read_text(encoding='utf-8'))
    value=dict(version='supported_policy_bundle_v1',atomic_artifacts=[v.model_dump(mode='json') for v in atomic],
        compound_policy=compound.model_dump(mode='json'),allowed_questions=sorted(config.allowlist),
        reference_status=summary['status'],deployment_active=False,
        compound_transfer=json.loads((repo/'artifacts/remaining-category-studies-v1/scoped-er-v1/transfer.json').read_text(encoding='utf-8')),
        limitations='Explicit offline scope. Historical identity strings preserved; live resources/instance compatibility checked separately. No API activation.')
    value['bundle_id']=content_id(value);output.mkdir(parents=True,exist_ok=False)
    path=output/'policies.json';path.write_text(json.dumps(value,indent=2),encoding='utf-8')
    load(path)
    (output/'README.txt').write_text('From repository baseline with existing dependencies: from scripts.policy_package import load; configuration, provider, compound = load("policies.json"). No model/service/private source paths are opened. Use explicit owned registry/observer integration; this is not API activation. Full supporting inventory is outside this minimal bundle.\n',encoding='utf-8')
    print('MINIMAL_POLICY_PACKAGE',value['bundle_id'],flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--repo',type=Path,default=Path(__file__).resolve().parents[1]);p.add_argument('--output',type=Path,required=True);a=p.parse_args();build(a.repo,a.output)
