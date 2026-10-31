"""Retained-report task routing parity with recorded-resource simulation only."""
from dataclasses import asdict
from pathlib import Path
from types import SimpleNamespace
import json
import sys
from scripts.multitask_policy42 import read,save
from scripts.multitask_uncertainty_sweep import SOURCE,OUT
from app.analysis.task_analyzer import TaskQuestionAnalyzer
from app.game.task_conditioning import TaskPolicyRouter,analysis_signature
from app.game.artifacts import PolicyArtifact,DeploymentEpisode,InMemoryPolicyProvider
from app.game.offline.collection import RecordingBundle,export_training
from app.game.offline.replay import replay
from app.game.offline.attacks import enumerate_attacks,AttackSpecification
from app.game.models import PlanningContext
from app.game.execution import VerifierExecutionFailure
from app.selection.models import VerifierUnavailable
from app.selection.verifier_selector import VerifierSelector
from app.selection.capabilities import BUILTIN_CAPABILITIES
from app.models.schemas import ValidationRequest
from app.verifiers.base_verifier import BaseVerifier

class Retained(BaseVerifier):
    def __init__(self,a):self.attempt=a
    @property
    def name(self):return self.attempt.verifier_name
    def verify(self,*args,**kwargs):
        if self.attempt.state=='failed':raise VerifierExecutionFailure('retained failure')
        if self.attempt.state=='unavailable':raise VerifierUnavailable('retained unavailable')
        return self.attempt.report

def main():
    def guard(event,args):
        if event=='open' and isinstance(args[0],str) and any(p.casefold()=='custody' for p in Path(args[0]).parts):raise AssertionError('final payload forbidden')
    sys.addaudithook(guard)
    checks=[];analyzer=TaskQuestionAnalyzer()
    for row in read(OUT/'comparison.json')['rows']:
        if not row['artifact_created']:continue
        a=PolicyArtifact.model_validate(read(row['artifact_path']));c=a.context
        bundle=RecordingBundle.model_validate(read(SOURCE/row['cohort']/'collection/recordings.json'))
        fresh=PlanningContext(**{**c.model_dump(),'offline_evaluation_id':None,'execution_contract_json':None,
            'clean_coverage_json':None,'reliability_first_json':None,'task_conditioning_json':None})
        manifest=export_training(bundle,fresh);episode=DeploymentEpisode(episode_id='retained-sweep',context=c,contract=a.contract,execution_configuration_id=a.execution_configuration_id)
        first=bundle.request.examples[0];signature=analysis_signature(analyzer.analyze(first.question),first.reference)
        router=TaskPolicyRouter(((signature,c.budget,True,episode,''),));provider=InMemoryPolicyProvider((a,))
        cumulative=0.
        for strategy in a.policy.strategies:
            p=dict(a.policy.solution.probabilities)[strategy.strategy_id];draw=cumulative+p/2;cumulative+=p
            if p==0:continue
            for correct in (True,False):
                e=next(e for e in manifest.partition('development').examples if e.answer_is_correct==correct)
                source=next(s for s in bundle.request.examples if s.run_id==e.validation_id)
                analysis=analyzer.analyze(source.question)
                assert asdict(analysis)==asdict(source.analysis)
                selector=VerifierSelector(verifiers=[Retained(t) for t in e.attempts],capabilities={t.verifier_name:BUILTIN_CAPABILITIES[t.verifier_name] for t in e.attempts})
                request=ValidationRequest(question=source.question,answer=source.answer,context=source.reference)
                actual=router.run(selector,analysis,request,source.run_id,provider=provider,rng=SimpleNamespace(random=lambda:draw),
                    resource_observer=SimpleNamespace(snapshot=lambda:a.contract.resource_manifest))
                specification=AttackSpecification(version='report_corruption_v1',suppression='unavailable')
                expected=replay(c,strategy,enumerate_attacks(c.dependencies,specification)[0],specification,a.contract,e)
                assert actual.summary['selected_strategy_id']==strategy.strategy_id
                assert (actual.public_status,actual.detail.raw_score,actual.summary['contributors'])==(expected.public_status,expected.numerical_score,expected.contributors)
                checks.append(dict(cohort=row['cohort'],target=row['target'],strategy_id=strategy.strategy_id,example=e.example_id,public_status=actual.public_status,parity=True))
    save(OUT/'runtime-parity.json',dict(scope='Retained reports and recorded-resource observer simulation. Not live resource revalidation, inference or final evaluation. Each variant is an explicitly chosen episode, not per-request coverage routing.',checks=checks,network_calls=0,generation_calls=0))
    print(len(checks),'retained-report parity checks passed')

if __name__=='__main__':main()
