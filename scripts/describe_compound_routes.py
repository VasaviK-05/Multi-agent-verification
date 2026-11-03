"""Offline owned-router demonstration, without inference or registry activation."""
import json
from pathlib import Path
import random
from types import SimpleNamespace
from app.game.artifacts import PolicyArtifact,artifact_version
from app.game.models import PlanningContext
from app.game.execution_contract import ExecutionContract
from app.game.policy import Policy,sample_policy
from app.game.component_sources import SourceManifest
from app.game.question_routing import configuration_from_atomic_artifacts,QuestionPolicyConfiguration
from app.selection.verifier_selector import VerifierSelector
from app.selection.capabilities import BUILTIN_CAPABILITIES
from app.verifiers.base_verifier import BaseVerifier


class NoInference(BaseVerifier):
    def __init__(self,name):self._name=name
    @property
    def name(self):return self._name
    def verify(self,*args):raise AssertionError('routing audit must not dispatch inference')


def main():
    root=Path(__file__).resolve().parents[1];output=root/'artifacts/compound-empirical-v2'
    read=lambda p:json.loads(p.read_text(encoding='utf-8'))
    artifacts=[]
    for family in ('arithmetic','factual'):
        path=root/f'artifacts/flexible-teams-v1/{family}-minimum-1'
        context=PlanningContext.model_validate(read(path/'context.json'))
        contract=ExecutionContract.model_validate(read(path/'contract.json'));policy=Policy.model_validate(read(path/'policy.json'))
        artifacts.append(PolicyArtifact(version=artifact_version(context,policy),policy=policy,context=context,contract=contract,
            execution_configuration_id=contract.execution_configuration_id,applicable_domain=context.plan.domain))
    base,provider=configuration_from_atomic_artifacts(artifacts)
    sources=SourceManifest.model_validate(read(output/'audit/source-manifest.json'))
    router=QuestionPolicyConfiguration(atomic_routes=base.atomic_routes,component_catalog_json=sources.catalog.model_dump_json()).router()
    rows=[]
    examples=read(root/'artifacts/question-conditioned-components-v1/real-routing.json')['real_routes']
    selector=VerifierSelector(verifiers=[NoInference(n) for n in BUILTIN_CAPABILITIES],capabilities=BUILTIN_CAPABILITIES)
    for e,artifact in zip(examples,artifacts):
        kind,key,resolved=router.resolve(e['question'],e['reference'])
        assert kind=='atomic' and resolved is not None
        sampled=sample_policy(artifact.policy,artifact.context,rng=random.Random(1102))
        rows.append(dict(kind=kind,question=e['question'],policy_id=sampled.policy_id,
            team=sampled.verifier_names,strategy_id=sampled.strategy_id,inference=False))
    first=examples[0]
    bad=router.run(selector,SimpleNamespace(question=first['question'],answer='uninspected',context=first['reference']),
        'offline-invalid-resource-fixture',provider=provider,rng=random.Random(1102),resource_observer=SimpleNamespace(snapshot=lambda:{}))
    assert bad.public_status=='uncertain' and bad.summary['selection_status']=='provenance_incompatible',bad.summary
    from app.game.offline.compound import question
    fact=next(f for f in sources.facts if f.descriptor.source_id not in {'BH','BE'})
    compound=question(fact,'10' if fact.descriptor.measure=='area' else '1000')
    missing=router.resolve(compound)[0];unsupported=router.resolve(compound.replace('plus','times'))[0]
    assert missing=='missing_policy' and unsupported=='unsupported_category'
    report=dict(atomic_selections=rows,compound=dict(question=compound,status=missing,
        reason='No empirical policy: only36 eligible independent source groups;48 required'),
        unsupported_operation=unsupported,resource_failure=bad.summary,
        resource_failure_is_deliberately_invalid_offline_observation=True,
        empirical_compound_policy_exists=False,activation=False,new_verifier_attempts=0,
        deployed_outer_allowlist_unchanged=True,local_resource_snapshot_is_not_live_service_attestation=True)
    (output/'routing.json').write_text(json.dumps(report,indent=2,sort_keys=True),encoding='utf-8')
    print([(r['kind'],r['team']) for r in rows],missing,unsupported,bad.summary['selection_status'])


if __name__=='__main__':main()
