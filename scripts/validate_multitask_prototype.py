"""Private retained-report package execution audit. No inference or network."""
from dataclasses import asdict
from pathlib import Path
from types import SimpleNamespace
import hashlib
import json
import socket
import sys
from app.game.prototype_bundle import load_prototype
from app.analysis.task_analyzer import TaskQuestionAnalyzer
from app.game.offline.collection import RecordingBundle
from app.game.offline.records import TrainingManifest
from app.game.offline.replay import replay
from app.game.offline.evaluation import Evaluation
from app.game.offline.attacks import enumerate_attacks
from app.game.offline.calibration import CalibrationArtifact
from app.game.resource_provenance import ResourceManifest
from app.selection.verifier_selector import VerifierSelector
from app.selection.capabilities import BUILTIN_CAPABILITIES
from app.models.schemas import ValidationRequest
from scripts.multitask_policy42 import read,save
from scripts.validate_uncertainty_sweep import Retained
from scripts.package_multitask_prototype import ROOT,SOURCE,STUDY

OUT=Path('build/multitask-prototype42-v1-validation')

def main():
    def guard(event,args):
        if event=='open' and isinstance(args[0],str) and any(p.casefold()=='custody' for p in Path(args[0]).parts):raise AssertionError('final payload forbidden')
    sys.addaudithook(guard)
    def no_network(*a,**kw):raise AssertionError('network forbidden in retained-report validation')
    socket.socket.connect=no_network
    package=load_prototype(ROOT);router=package.router();provider=package.provider();analyzer=TaskQuestionAnalyzer()
    OUT.mkdir(exist_ok=False);traces=[];negative=[];preserved={};marginals={}
    for entry,a in zip(package.manifest.entries,package.artifacts):
        cohort=entry.task;c=a.context
        original=SOURCE/cohort/('coverage-50' if cohort=='arithmetic' else 'coverage-25')/'policy.json'
        assert original.read_bytes()==(ROOT/entry.artifact_path).read_bytes()
        preserved[str(original)]=hashlib.sha256(original.read_bytes()).hexdigest()
        calibration=CalibrationArtifact.model_validate(read(STUDY/cohort/'calibration.json'))
        assert calibration.calibration_id==entry.calibration_id
        assert dict(c.attempt_costs)=={r['verifier_name']:r['attempt_cost'] for r in calibration.result['estimates']}
        recordings=RecordingBundle.model_validate(read(STUDY/cohort/'collection/recordings.json'))
        manifest=TrainingManifest.model_validate(read(STUDY/cohort/'training-manifest.json'))
        evaluation=Evaluation.model_validate(read(STUDY/cohort/'development-evaluation.json'))
        attack=enumerate_attacks(c.dependencies,evaluation.attacks)[0]
        examples={e.example_id:e for e in manifest.partition('development').examples}
        probabilities=dict(a.policy.solution.probabilities);cumulative=0.
        marginals[cohort]={n:sum(probabilities[s.strategy_id] for s in a.policy.strategies if n in s.verifiers) for n in ('rule','confidence','evidence','semantic')}
        def pool(example):
            calls=[];verifiers=[]
            for attempt in example.attempts:
                v=Retained(attempt);original_verify=v.verify
                def verify(*args,_name=v.name,_call=original_verify,**kwargs):
                    calls.append(_name);return _call(*args,**kwargs)
                v.verify=verify;verifiers.append(v)
            return VerifierSelector(verifiers=verifiers,capabilities={v.name:BUILTIN_CAPABILITIES[v.name] for v in verifiers}),calls
        for strategy in a.policy.strategies:
            p=probabilities[strategy.strategy_id];draw=cumulative+p/2;cumulative+=p
            if p==0:continue
            cells=[o for o in evaluation.outcomes if o.strategy_id==strategy.strategy_id and o.attack_id==attack.attack_id]
            for status in ('passed','failed','uncertain'):
                source=next((o for o in cells if o.public_status==status),None)
                if source is None:continue
                e=examples[source.example_id];request_source=next(r for r in recordings.request.examples if r.run_id==e.validation_id)
                analysis=analyzer.analyze(e.question)
                assert asdict(analysis)==asdict(request_source.analysis)
                selector,calls=pool(e);request=ValidationRequest(question=e.question,answer=e.answer,context=e.reference)
                actual=router.run(selector,analysis,request,e.validation_id,provider=provider,rng=SimpleNamespace(random=lambda:draw),
                    resource_observer=SimpleNamespace(snapshot=lambda:a.contract.resource_manifest))
                expected=replay(c,strategy,attack,evaluation.attacks,a.contract,e)
                assert actual.summary['selected_strategy_id']==strategy.strategy_id
                assert (actual.public_status,actual.detail.raw_score,actual.summary['contributors'])==(expected.public_status,expected.numerical_score,expected.contributors)
                traces.append(dict(task=cohort,artifact_id=a.artifact_id,policy_id=a.policy.policy_id,strategy_id=strategy.strategy_id,probability=p,
                    example_id=e.example_id,question=e.question,answer=e.answer,reference=e.reference,
                    raw_reports=[t.report.model_dump(mode='json') for t in e.attempts if t.verifier_name in strategy.verifiers and t.report is not None],
                    aggregate=actual.detail.to_dict(),summary=actual.summary,public_status=actual.public_status,
                    estimated_cost=strategy.estimated_cost,units=c.cost_units,executed_retained_verifiers=calls,replay_parity=True))
        assert {'passed','failed','uncertain'} <= {t['public_status'] for t in traces if t['task']==cohort}
        e=next(iter(examples.values()))
        for kind in ('missing_reference','blank_reference','judgment_reference','changed_resources','insufficient_budget','outside_scope'):
            selector,calls=pool(e);reference=e.reference;question=e.question;kwargs={}
            if kind=='missing_reference':reference=None
            if kind=='blank_reference':reference='  '
            if kind=='judgment_reference':reference='support,reject'
            if kind=='insufficient_budget':kwargs['budget']=c.budget-1.
            if kind=='outside_scope':question='What is 999 + 1000?' if cohort=='arithmetic' else 'What is the area of Atlantis?'
            observed=a.contract.resource_manifest
            if kind=='changed_resources':
                data=observed.model_dump();data['verifiers'][0]['resources'][0]['sha256']='0'*64
                observed=ResourceManifest.model_validate(data)
            run=router.run(selector,analyzer.analyze(question),ValidationRequest(question=question,answer=e.answer,context=reference),e.validation_id,
                provider=provider,rng=SimpleNamespace(random=lambda:.5),resource_observer=SimpleNamespace(snapshot=lambda:observed),**kwargs)
            assert run.public_status=='uncertain' and run.summary['selection_status']!='selected' and not calls
            negative.append(dict(task=cohort,case=kind,summary=run.summary,retained_dispatches=calls))
    for question,context in [('Paraphrase this reference: Alex carried a parcel.','Alex carried a parcel.'),('Tell me a tale.',None)]:
        result=router.run(None,analyzer.analyze(question),ValidationRequest(question=question,answer='Unsupported',context=context),'unsupported',
            provider=provider,rng=None,resource_observer=None)
        assert result.public_status=='uncertain' and result.summary['selection_status']!='selected'
        negative.append(dict(case='unsupported_task',summary=result.summary))
    for p,digest in preserved.items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==digest
    save(OUT/'execution-traces.json',dict(scope='Private retained development reports and recorded-resource observer simulation, not live model/resource evidence; not part of distributable zip',traces=traces))
    save(OUT/'validation.json',dict(bundle_id=package.manifest.bundle_id,acceptance_rejection_uncertainty=True,negative_checks=negative,
        trace_count=len(traces),marginal_selection=marginals,original_policy_hashes=preserved,network_calls=0,generation_calls=0,final_payload_access=False))
    print(json.dumps(dict(bundle_id=package.manifest.bundle_id,retained_traces=len(traces),safe_failures=len(negative),marginals=marginals),indent=2))

if __name__=='__main__':main()
