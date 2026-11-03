"""Replay actual smoke reports through the new owned component decision path.

This is execution validation with borrowed constituent history, not fitted joint
reliability or a compound held-out result. No verifier inference occurs here.
"""
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
from app.models.schemas import VerificationResult
from app.verifiers.base_verifier import BaseVerifier
from app.selection.verifier_selector import VerifierSelector
from app.selection.capabilities import BUILTIN_CAPABILITIES
from app.game.component_execution import enumerate_component_strategies,run_component_diagnostic
from app.game.resource_provenance import ResourceManifest
from scripts.component_scenarios import diagnostic_contract


class ReplayVerifier(BaseVerifier):
    def __init__(self,name,records):self._name=name;self.records=records
    @property
    def name(self):return self._name
    def verify(self,question,answer,context=None):
        from app.game.execution import VerifierExecutionFailure
        if not self.records:raise AssertionError('unrecorded dispatch forbidden')
        record=self.records.pop(0)
        assert (question,answer)==(record['component']['question'],record['component']['answer'])
        if record['state']=='failed':raise VerifierExecutionFailure(record['error'])
        return VerificationResult.model_validate(record['report'])


def main():
    root=Path(__file__).resolve().parents[1]
    study=root/'artifacts/question-conditioned-components-v1'
    read=lambda p:json.loads(Path(p).read_text(encoding='utf-8'))
    save=lambda name,value:(study/name).write_text(json.dumps(value,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    protocol=read(study/'protocol.json')
    for path,digest in protocol['sealed_inputs'].items():
        current=hashlib.sha256(Path(path).read_bytes()).hexdigest()
        if current!=digest:
            assert Path(path).name=='component_binding.py'
            scope=read(study/'post-smoke-scope-guard.json')
            assert scope['current_binding_sha256']==current
            assert hashlib.sha256((study/'binding-at-smoke.py').read_bytes()).hexdigest()==digest
    before=read(study/'preservation-before.json')
    changed=[p for p,d in before.items() if hashlib.sha256(Path(p).read_bytes()).hexdigest()!=d]
    assert not changed,changed
    labels=read(study/'labels.json')
    records=[json.loads(line) for line in (study/'live/attempts.jsonl').read_text().splitlines()]
    assert len(records)==16 and len({r['call_id'] for r in records})==16
    bases={family:read(root/f'artifacts/flexible-teams-v1/{family}-minimum-1/context.json') for family in ('factual','arithmetic')}
    outputs=[];contracts={};strategies={}
    for example in read(study/'examples.json'):
        local=[r for r in records if r['example_id']==example['example_id']]
        verifiers=[ReplayVerifier(n,[r for r in local if r['verifier_name']==n]) for n in ('confidence','evidence','rule','semantic')]
        contract=diagnostic_contract(example['question'],example['reference'],bases,verifiers)
        strategy=next(s for s in enumerate_component_strategies(contract)
            if tuple(a.verifiers for _,a in s.components)==(('evidence',),('rule',))
            and s.components[0][1].aggregation=='reputation_weighted')
        selector=VerifierSelector(verifiers=verifiers,capabilities=BUILTIN_CAPABILITIES)
        observations=iter((read(study/'live/resources-before.json'),read(study/'live/resources-after.json')))
        observer=SimpleNamespace(snapshot=lambda:ResourceManifest.model_validate(next(observations)))
        result=run_component_diagnostic(contract,strategy,selector,example['question'],example['answer'],
            example['reference'],example['example_id'],resource_observer=observer)
        for attempt in result.summary['attempts']:
            original=next(r for r in local if r['verifier_name']==attempt['verifier_name'])
            attempt['live_elapsed_ms']=original['elapsed_ms']
            attempt['replay_elapsed_ms']=attempt.pop('elapsed_ms')
        assert len(result.summary['attempts'])==2
        outputs.append(dict(example_id=example['example_id'],independent_label=labels[example['example_id']],
            **result.summary))
        contracts[contract.category]=contract.model_dump(mode='json')
        strategies[contract.category]=strategy.model_dump(mode='json')
        assert not any(v.records for v in verifiers)
    save('diagnostic-contracts.json',contracts);save('diagnostic-strategies.json',strategies)
    save('component-outcomes.json',outputs)
    save('verification.json',dict(prior_artifact_count=len(before),prior_artifacts_unchanged=True,
        predeclared_inputs_verified=True,executed_binding_snapshot_verified=True,
        attempts=16,unique_call_ids=16,execution_mode='diagnostic_no_policy',
        independent_labels=[o['independent_label'] for o in outputs],
        statuses={o['example_id']:o['public_status'] for o in outputs},
        false_accepts=sum(o['public_status']=='passed' and not o['independent_label']['answer_is_correct'] for o in outputs),
        not_a_fitted_policy=True,no_new_inference_in_evaluation=True))
    print([(o['example_id'],o['public_status']) for o in outputs])


if __name__=='__main__':main()
