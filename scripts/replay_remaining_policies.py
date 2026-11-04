"""Portable typed loading, explicit registry and empirical report replay. No inference.

python -m scripts.replay_remaining_policies --output <new-directory>
Only repository-relative policy/report files are opened. Historical identity
strings remain intact; no local model paths need exist to load/replay.
"""
import argparse,json
from pathlib import Path
from app.game.artifacts import PolicyArtifact,artifact_version
from app.game.models import PlanningContext
from app.game.policy import Policy
from app.game.execution_contract import ExecutionContract
from app.game.component_execution import ComponentPolicy
from app.game.question_routing import QuestionPolicyConfiguration,configuration_from_atomic_artifacts
from app.analysis.reference_study_analyzer import VERSION
from scripts.replay_compound_study_36 import execute
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def load_registry(repo):
    artifacts=[]
    for family in ('arithmetic','factual'):
        folder=repo/f'artifacts/flexible-teams-v1/{family}-minimum-1'
        context=PlanningContext.model_validate(read(folder/'context.json'));contract=ExecutionContract.model_validate(read(folder/'contract.json'))
        policy=Policy.model_validate(read(folder/'policy.json'))
        artifacts.append(PolicyArtifact(version=artifact_version(context,policy),policy=policy,context=context,contract=contract,
            execution_configuration_id=contract.execution_configuration_id,applicable_domain=context.plan.domain))
    new=repo/'artifacts/remaining-category-studies-v1'
    reference=new/'reference-50-v1/fit/policy.json'
    if reference.exists():artifacts.append(PolicyArtifact.model_validate(read(reference)))
    base,provider=configuration_from_atomic_artifacts(artifacts)
    compound=ComponentPolicy.model_validate(read(new/'compound-85/candidate/policy.json'))
    old=repo/'artifacts/compound-study-36-v1';examples=read(old/'examples.json');atomic=read(old/'atomic-replay-inputs.json')
    refs=read(new/'reference/groups.json')
    negative='What is the area of Bahrain, and what is that area times 10 square kilometres? Give both values.'
    allowed={e['question'] for rows in examples.values() for e in rows}|{e['question'] for e in atomic}|{g['question'] for g in refs}|{negative}
    config=QuestionPolicyConfiguration(atomic_routes=base.atomic_routes,
        component_entries=((compound.contract.question_signature,compound.contract.budget,True,compound),),
        allowlist=frozenset(allowed),reference_question_version=VERSION)
    return config,provider,compound,artifacts
def main():
    p=argparse.ArgumentParser();p.add_argument('--repo',type=Path,default=Path(__file__).resolve().parents[1]);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    config,provider,compound,artifacts=load_registry(a.repo);router=config.router();outcomes=[]
    old=a.repo/'artifacts/compound-study-36-v1';new=a.repo/'artifacts/remaining-category-studies-v1'
    for item in read(old/'atomic-replay-inputs.json'):
        expected={item['selected']:dict(question=item['question'],answer=item['answer'],reference=item['reference'],report_json=item['report_json'])}
        outcome=execute(router,provider,item['question'],item['answer'],item['reference'],item['validation_id'],expected,item['resources'])
        assert outcome['summary']['team']==[item['selected']]
        outcomes.append(dict(category=item['family'],**outcome))
    heldout=(new/'compound-85/test/joint.json').exists()
    recording=new/'compound-85/test' if heldout else old/'development'
    test=read(recording/'joint.json');bundles=dict(test['bundles']);resources=read(recording/'resources-after.json')
    examples=read(old/'examples.json')['final_test' if heldout else 'development'];group=examples[0]['group_id']
    for e in (row for row in examples if row['group_id']==group):
        expected={}
        for cid,name in (('base_fact','evidence'),('derived_sum','rule')):
            row=next(r for r in bundles[cid]['attempts'] if r['example_id']==e['example_id']+'-'+cid and r['candidate']==name)
            request=next(r for r in bundles[cid]['request']['examples'] if r['example_id']==row['example_id'])
            expected[name]=dict(question=request['question'],answer=request['answer'],reference=request['reference'],report_json=row['attempt']['report_json'],execution_state=row['attempt']['state'])
        outcome=execute(router,provider,e['question'],e['answer'],None,e['example_id'],expected,resources)
        assert outcome['summary']['team']==['evidence','rule'] and len(outcome['replay_calls'])==2
        assert outcome['summary']['selection_status']=='selected'
        outcomes.append(dict(category='compound',variant=e['variant'],independent_label=e['label'],**outcome))
    incompatible=execute(router,provider,e['question'],e['answer'],None,e['example_id'],expected,resources,invalid_resources=True)
    reference_artifact=new/'reference-50-v1/fit/policy.json'
    if reference_artifact.exists():
        bundle=read(new/'reference-50-v1/training/reference/bundle.json')
        item=next(row for row in bundle['request']['examples'] if row['role']=='history')
        expected={row['candidate']:dict(question=item['question'],answer=item['answer'],reference=item['reference'],
            report_json=row['attempt']['report_json'],execution_state=row['attempt']['state']) for row in bundle['attempts'] if row['run_id']==item['run_id']}
        outcome=execute(router,provider,item['question'],item['answer'],item['reference'],item['run_id'],expected,bundle['observed_setup']['resources'])
        outcomes.append(dict(category='reference',source_partition='history',**outcome))
    missing=QuestionPolicyConfiguration(atomic_routes=config.atomic_routes,allowlist=config.allowlist,component_catalog_json=compound.contract.descriptor_catalog_json).router().resolve(e['question'])[0]
    ref=read(new/'reference/groups.json')[0]
    result=dict(outcomes=outcomes,reference_route=router.resolve(ref['question'],ref['reference'])[0],
        missing_component_policy=missing,unknown_category=router.resolve('Explain quantum gravity.')[0],
        incompatible_resource_fixture=incompatible,actual_policy_team_sizes=sorted({len(o['summary']['team']) for o in outcomes}),
        real_triple_policy=any(len(o['summary'].get('team',[]))==3 for o in outcomes),new_live_calls=0,deployment_active=False,
        policies=[dict(artifact_id=x.artifact_id,policy_id=x.policy.policy_id,context_id=x.context.compatibility_id,matrix_id=x.policy.matrix.matrix_id,resource_id=x.execution_configuration_id) for x in artifacts],
        compound=dict(policy_id=compound.policy_id,contract_id=compound.contract.compatibility_id,matrix_id=compound.matrix.matrix_id,resource_id=compound.contract.actual_resources.manifest_id),
        compound_replay_partition='final_test' if heldout else 'development',
        limitation='Retained observation replay, not held-out evaluation, live API or active-instance attestation.')
    a.output.mkdir(parents=True,exist_ok=False);(a.output/'routing.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print([(o['category'],o['summary']['team'],o['public_status']) for o in outcomes],flush=True)
if __name__=='__main__':main()
