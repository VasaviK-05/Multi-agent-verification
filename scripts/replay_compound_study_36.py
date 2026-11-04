"""Portable owned-router acceptance replay. No model inference or activation.

Uses sealed empirical policies, actual retained reports and recorded resource
observations. Replay is not active-instance attestation in a live API.
"""
import argparse
import hashlib
import json
from pathlib import Path
import random
from types import SimpleNamespace
from app.game.artifacts import PolicyArtifact,artifact_version
from app.game.models import PlanningContext
from app.game.policy import Policy
from app.game.execution_contract import ExecutionContract
from app.game.component_execution import ComponentPolicy
from app.game.question_routing import QuestionPolicyConfiguration,configuration_from_atomic_artifacts
from app.game.resource_provenance import ResourceManifest
from app.models.schemas import VerificationResult
from app.selection.verifier_selector import VerifierSelector
from app.selection.capabilities import BUILTIN_CAPABILITIES
from app.verifiers.base_verifier import BaseVerifier


def read(path):return json.loads(Path(path).read_text(encoding='utf-8'))


class RecordedVerifier(BaseVerifier):
    def __init__(self,name,calls,expected):self._name=name;self.calls=calls;self.expected=expected
    @property
    def name(self):return self._name
    def verify(self,question,answer,context=None):
        if self.name not in self.expected:raise AssertionError('unrecorded verifier requested')
        item=self.expected[self.name]
        if (question,answer,context)!=(item['question'],item['answer'],item['reference']):raise AssertionError('replay input differs from actual recorded invocation')
        self.calls.append(dict(name=self.name,question=question,answer=answer,reference=context))
        if item['report_json'] is None:
            from app.game.execution import VerifierExecutionFailure
            from app.selection.models import VerifierUnavailable
            if item.get('execution_state')=='unavailable':raise VerifierUnavailable('retained unavailable outcome; no retry')
            raise VerifierExecutionFailure('retained failed outcome; no retry')
        return VerificationResult.model_validate_json(item['report_json'])


def execute(router,provider,question,answer,reference,validation_id,expected,resources,*,invalid_resources=False):
    calls=[]
    selector=VerifierSelector(verifiers=[RecordedVerifier(n,calls,expected) for n in BUILTIN_CAPABILITIES],capabilities=BUILTIN_CAPABILITIES)
    observed=ResourceManifest.model_validate(resources)
    if invalid_resources:
        data=observed.model_dump(mode='json');data['verifiers'][0]['resources'][0]['sha256']='f'*64
        observed=ResourceManifest.model_validate(data)
    result=router.run(selector,SimpleNamespace(question=question,answer=answer,context=reference),validation_id,
        provider=provider,rng=random.Random(1102),resource_observer=SimpleNamespace(snapshot=lambda:observed))
    summary=result.summary
    for call in summary.get('attempts',[]):
        if 'elapsed_ms' in call:call['replay_elapsed_ms']=call.pop('elapsed_ms')
    return dict(question=question,answer=answer,public_status=result.public_status,summary=summary,
        replay_calls=calls,new_live_verifier_calls=0,resource_mode='retained observation replay; not live attestation')


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--study-root',type=Path,default=Path('artifacts/compound-study-36-v1'))
    p.add_argument('--source-root',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    repo=Path(__file__).resolve().parents[1];study=a.study_root
    policy_path=study/'candidate/policy.json';compound=ComponentPolicy.model_validate(read(policy_path)) if policy_path.exists() else None
    packaged=study/'atomic-replay-inputs.json'
    if packaged.exists():inputs=read(packaged)
    else:
        if a.source_root is None:raise ValueError('first packaging requires the retained source root')
        inputs=[]
        for family,name in (('arithmetic','rule'),('factual','evidence')):
            path=a.source_root/family/'training-manifest.json';data=read(path)
            e=next(p for p in data['partitions'] if p['role']=='history')['examples'][0]
            report=next(row for row in e['attempts'] if row['verifier_name']==name)
            resources=ResourceManifest(verifiers=tuple(json.loads(row['observed_resources_json']) for row in e['attempts']))
            inputs.append(dict(family=family,question=e['question'],answer=e['answer'],reference=e['reference'],
                validation_id=e['validation_id'],selected=name,report_json=report['report_json'],
                resources=resources.model_dump(mode='json'),source_manifest_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                source_example_id=e['example_id'],source_role='history'))
        packaged.write_text(json.dumps(inputs,indent=2),encoding='utf-8')
    artifacts=[]
    for item in inputs:
        folder=repo/f"artifacts/flexible-teams-v1/{item['family']}-minimum-1"
        c=PlanningContext.model_validate(read(folder/'context.json'));k=ExecutionContract.model_validate(read(folder/'contract.json'))
        policy=Policy.model_validate(read(folder/'policy.json'))
        artifacts.append(PolicyArtifact(version=artifact_version(c,policy),policy=policy,context=c,contract=k,
            execution_configuration_id=k.execution_configuration_id,applicable_domain=c.plan.domain))
    base,provider=configuration_from_atomic_artifacts(artifacts)
    examples=read(study/'examples.json');allowed={e['question'] for rows in examples.values() for e in rows}|{e['question'] for e in inputs}
    negatives={'What is the area of Bahrain, and what is that area times 10 square kilometres? Give both values.'}
    allowed|=negatives
    entries=((compound.contract.question_signature,compound.contract.budget,True,compound),) if compound else ()
    config=QuestionPolicyConfiguration(atomic_routes=base.atomic_routes,component_entries=entries,allowlist=frozenset(allowed),
        component_catalog_json=compound.contract.descriptor_catalog_json if compound else json.dumps(read(study/'catalog.json')))
    router=config.router();outcomes=[]
    for item in inputs:
        expected={item['selected']:dict(question=item['question'],answer=item['answer'],reference=item['reference'],report_json=item['report_json'])}
        outcome=execute(router,provider,item['question'],item['answer'],item['reference'],item['validation_id'],expected,item['resources'])
        assert outcome['summary']['team']==[item['selected']]
        outcomes.append(dict(category=item['family'],**outcome))
    if compound and (study/'test/joint.json').exists():
        test=read(study/'test/joint.json');bundles=dict(test['bundles'])
        group=examples['final_test'][0]['group_id']
        resources=read(study/'test/resources-after.json')
        for e in (row for row in examples['final_test'] if row['group_id']==group):
            expected={}
            for cid,name in (('base_fact','evidence'),('derived_sum','rule')):
                row=next(r for r in bundles[cid]['attempts'] if r['example_id']==e['example_id']+'-'+cid and r['candidate']==name)
                request=next(r for r in bundles[cid]['request']['examples'] if r['example_id']==row['example_id'])
                expected[name]=dict(question=request['question'],answer=request['answer'],reference=request['reference'],
                    report_json=row['attempt']['report_json'],execution_state=row['attempt']['state'])
            outcome=execute(router,provider,e['question'],e['answer'],None,e['example_id'],expected,resources)
            assert outcome['summary']['team']==['evidence','rule'] and len(outcome['replay_calls'])==2
            outcomes.append(dict(category='compound',variant=e['variant'],independent_label=e['label'],**outcome))
        missing=QuestionPolicyConfiguration(atomic_routes=base.atomic_routes,component_catalog_json=compound.contract.descriptor_catalog_json,
            allowlist=frozenset(allowed)).router().resolve(e['question'])[0]
        resource_failure=execute(router,provider,e['question'],e['answer'],None,e['example_id'],expected,resources,invalid_resources=True)
    else:
        missing=router.resolve(examples['development'][0]['question'])[0]
        first=inputs[0]
        expected={first['selected']:dict(question=first['question'],answer=first['answer'],reference=first['reference'],report_json=first['report_json'])}
        resource_failure=execute(router,provider,first['question'],first['answer'],first['reference'],first['validation_id'],
            expected,first['resources'],invalid_resources=True)
    unsupported=router.resolve(next(iter(negatives)))[0]
    a.output.mkdir(parents=True,exist_ok=False)
    (a.output/'routing.json').write_text(json.dumps(dict(outcomes=outcomes,missing_policy=missing,unsupported_question=unsupported,
        incompatible_resource_fixture=resource_failure,actual_policy_team_sizes=sorted({len(o['summary']['team']) for o in outcomes}),
        real_policy_selection_of_three=False,activation=False,scope='explicit offline study allowlist; deployed prototype allowlist unchanged',
        all_categories_live_in_one_installation_demonstrated=False,new_live_calls=0),indent=2),encoding='utf-8')
    print([(o['category'],o['summary']['team'],o['public_status']) for o in outcomes],flush=True)


if __name__=='__main__':main()
