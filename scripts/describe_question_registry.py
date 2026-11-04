"""Read-only real-policy routing demonstration; no inference or refitting."""
import hashlib
import json
from pathlib import Path
from app.game.artifacts import PolicyArtifact,artifact_version
from app.game.models import PlanningContext
from app.game.policy import Policy
from app.game.execution_contract import ExecutionContract
from app.game.question_routing import configuration_from_atomic_artifacts


def main():
    root=Path(__file__).resolve().parents[1]
    target=root/'artifacts/question-conditioned-components-v1'
    read=lambda p:json.loads(p.read_text(encoding='utf-8'))
    artifacts=[];inputs=[];source_facts=[]
    for family in ('arithmetic','factual'):
        directory=root/f'artifacts/flexible-teams-v1/{family}-minimum-1'
        context=PlanningContext.model_validate(read(directory/'context.json'))
        contract=ExecutionContract.model_validate(read(directory/'contract.json'))
        policy=Policy.model_validate(read(directory/'policy.json'))
        artifact=PolicyArtifact(version=artifact_version(context,policy),context=context,contract=contract,
            policy=policy,execution_configuration_id=contract.execution_configuration_id,applicable_domain=context.plan.domain)
        artifacts.append(artifact)
        manifest=root.parent/'multitask-policy42'/family/'training-manifest.json'
        examples=[e for p in read(manifest)['partitions'] for e in p['examples'] if p['role']=='history']
        # History questions demonstrate routing without consulting answers/outcomes.
        question=examples[0]
        inputs.append(dict(family=family,question=question['question'],reference=question['reference'],
            artifact_version=artifact.version,
            context_path=str(directory/'context.json'),contract_path=str(directory/'contract.json'),
            policy_path=str(directory/'policy.json'),
            artifact_id=artifact.artifact_id,policy_id=policy.policy_id,
            context_id=context.compatibility_id,
            distribution=[dict(team=list(s.verifiers),aggregation=s.aggregation,probability=dict(policy.solution.probabilities)[s.strategy_id])
                for s in policy.strategies if dict(policy.solution.probabilities)[s.strategy_id]>0]))
        if family=='factual':
            for e in examples:
                if e['example_id'] in {'BE-correct','BH-correct'}:
                    source_facts.append(dict(source_manifest=str(manifest),manifest_sha256=hashlib.sha256(manifest.read_bytes()).hexdigest(),
                        example_id=e['example_id'],split='history',question=e['question'],answer=e['answer'],
                        label_source=e['label_source'],label_method=e['label_method']))
    configuration,provider=configuration_from_atomic_artifacts(artifacts)
    router=configuration.router()
    for item in inputs:
        kind,signature,resolved=router.resolve(item['question'],item['reference'])
        assert kind=='atomic' and resolved is not None
        item.update(signature=signature,routed_episode_id=resolved[0][3].episode_id,
            selection_uses_answer=False,selection_uses_label=False,inference_performed=False)
    output=dict(real_routes=inputs,registered_artifact_ids=[a.artifact_id for a in provider.snapshot()],
        component_entries=[],preserve_existing_outer_prototype_allowlist=True,
        unavailable=['reference comparison: no qualifying fitted policy',
            'bounded difference wording: new analyzer version has no fitted policy',
            'area/population compound: no jointly fitted empirical policy'],
        empirical_pairs_or_triples=False,activation_performed=False)
    (target/'real-routing.json').write_text(json.dumps(output,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    (target/'source-fact-provenance.json').write_text(json.dumps(source_facts,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print([(i['family'],i['question'],i['distribution']) for i in inputs])


if __name__=='__main__':main()
