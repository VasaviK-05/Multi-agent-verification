"""Opt-in informative-contributor, reliability-first development study."""
import argparse
from collections import Counter
from pathlib import Path
import hashlib
import json
import sys
ROOT=Path('build/factual-policy42-20261029')
OUT=Path('build/factual-reliability-first42')
def read(path):return json.loads(Path(path).read_text(encoding='utf-8'))
def save(path,value):
    with Path(path).open('x',encoding='utf-8') as f:json.dump(value,f,indent=2,allow_nan=False)

def baseline():
    from app.game.artifacts import PolicyArtifact
    from app.game.research.specification import PolicyBuildSpecification
    from app.game.offline.evaluation import construct_payoffs
    OUT.mkdir(exist_ok=False)
    original=PolicyArtifact.model_validate_json((ROOT/'fitted-policy/policy.json').read_text(encoding='utf-8'))
    spec=PolicyBuildSpecification.model_validate(read(ROOT/'policy-input.json'))
    actual=construct_payoffs(original.context,spec.manifest,spec.contract,spec.attacks)
    assert actual.matrix==original.policy.matrix
    prior=read('build/factual-coverage-exploration42/original-evaluation.json')
    assert actual.model_dump(mode='json')==prior
    save(OUT/'legacy-reproduced-evaluation.json',actual.model_dump(mode='json'))
    paths=[ROOT/'fitted-policy/policy.json',ROOT/'calibration.json',ROOT/'approval-binding.json',ROOT/'collection/recordings.json']
    paths+=list(Path('build/factual-coverage-exploration42').glob('coverage-*/policy.json'))
    save(OUT/'preserved-input-hashes.json',{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths})
    print('Reproduced every legacy strategy/attack from retained records; exact match.',flush=True)


def new_replay():
    from app.game.artifacts import PolicyArtifact
    from app.game.research.specification import PolicyBuildSpecification
    from app.game.execution_contract import ExecutionContract
    from app.game.models import PlanningContext, content_id
    from app.game.offline.evaluation import bind_evaluation, construct_payoffs, export_artifact
    from app.game.offline.attacks import enumerate_attacks
    from app.game.policy import build_policy
    original=PolicyArtifact.model_validate_json((ROOT/'fitted-policy/policy.json').read_text(encoding='utf-8'))
    spec=PolicyBuildSpecification.model_validate(read(ROOT/'policy-input.json'))
    contract=ExecutionContract(**{**spec.contract.model_dump(),'version':'offline_public_decision_v3','contributor_version':'informative_history_influence_v1'})
    unbound=PlanningContext(**{**original.context.model_dump(),'offline_evaluation_id':None,'execution_contract_json':None})
    context=bind_evaluation(unbound,spec.manifest,contract,spec.attacks)
    assert context.reputation_snapshot_id==original.context.reputation_snapshot_id
    evaluation=construct_payoffs(context,spec.manifest,contract,spec.attacks)
    save(OUT/'informative-context.json',context.model_dump(mode='json'))
    save(OUT/'informative-contract.json',contract.model_dump(mode='json'))
    save(OUT/'informative-evaluation.json',evaluation.model_dump(mode='json'))
    actions=enumerate_attacks(context.dependencies,spec.attacks);rows=[]
    for strategy in evaluation.matrix.strategy_definitions:
        cells=[]
        for attack in actions:
            cell=[o for o in evaluation.outcomes if o.strategy_id==strategy.strategy_id and o.attack_id==attack.attack_id]
            metrics=next(m for s,a,m in evaluation.metrics if s==strategy.strategy_id and a==attack.attack_id)
            cells.append(dict(attack=attack.kind,metrics=metrics.model_dump(mode='json'),validation_loss=metrics.validation_loss(context.loss_configuration),
                contributor_counts=dict(Counter(o.contributors for o in cell)),reason_counts=dict(Counter(r for o in cell for r in o.reasons))))
        rows.append(dict(**strategy.model_dump(mode='json'),scenarios=cells))
    save(OUT/'informative-all-strategies.json',rows)
    # Isolates the contributor change: old objective, no coverage or lexicographic constraint.
    policy=build_policy(context,evaluation.matrix,tolerance=1e-8)
    artifact=export_artifact(policy,context,spec.manifest,contract,spec.attacks,applicable_domain=context.plan.domain)
    destination=OUT/'informative-old-objective';destination.mkdir()
    with (destination/'policy.json').open('x',encoding='utf-8') as f:f.write(artifact.model_dump_json(indent=2))
    save(OUT/'replay-provenance.json',dict(original_artifact_id=original.artifact_id,raw_recordings_unchanged=True,
        history_snapshot_id=context.reputation_snapshot_id,execution_contract=contract.model_dump(mode='json'),
        application_source_digest=content_id([(p.as_posix(),hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted(Path('app').rglob('*.py'))])))
    print('New contract replay complete. Maximum finalized clean coverage:',max(row['scenarios'][0]['metrics']['decision_coverage'] for row in rows),flush=True)


def fit():
    import math
    import os
    import requests
    from app.game.artifacts import PolicyArtifact, InMemoryPolicyProvider, DeploymentEpisode
    from app.game.models import PlanningContext, content_id
    from app.game.execution_contract import ExecutionContract
    from app.game.research.specification import PolicyBuildSpecification
    from app.game.offline.evaluation import Evaluation, export_artifact, summarize
    from app.game.offline.reliability import fit_reliability_first
    from app.game.offline.build import verify_equivalent, environment_versions
    from app.game.offline.attacks import enumerate_attacks
    from app.game.offline.replay import replay
    from app.game.offline.collection import RecordingBundle
    from app.game.offline.recording_adapters import ProjectObserver
    from app.game.execution import GameRuntime, VerifierExecutionFailure
    from app.verifiers.base_verifier import BaseVerifier
    from app.selection.models import VerifierUnavailable
    from app.selection.verifier_selector import VerifierSelector
    from app.selection.capabilities import BUILTIN_CAPABILITIES
    from app.models.schemas import ValidationRequest
    from app.game.solver import validate_solution
    from scripts.run_factual_diagnostic import NetworkBudget
    spec=PolicyBuildSpecification.model_validate(read(ROOT/'policy-input.json'))
    context=PlanningContext.model_validate(read(OUT/'informative-context.json'))
    contract=ExecutionContract.model_validate(read(OUT/'informative-contract.json'))
    evaluation=Evaluation.model_validate(read(OUT/'informative-evaluation.json'))
    maximum=max(row['scenarios'][0]['metrics']['decision_coverage'] for row in read(OUT/'informative-all-strategies.json'))
    if maximum<.90:
        save(OUT/'infeasible.json',dict(target=.90,maximum_achievable_clean_coverage=maximum,artifact_created=False,target_relaxed=False))
        raise ValueError('approved 90% coverage infeasible; no artifact created')
    bound,policy=fit_reliability_first(context,spec.manifest,contract,spec.attacks,evaluation,minimum=.90,epsilon=1e-8,tolerance=1e-8,cost_tolerance=1e-8)
    artifact=export_artifact(policy,bound,spec.manifest,contract,spec.attacks,applicable_domain=bound.plan.domain)
    artifact=PolicyArtifact.model_validate_json(artifact.model_dump_json())
    validate_solution(artifact.policy.matrix,artifact.policy.solution)
    repeated_context,repeated_policy=fit_reliability_first(context,spec.manifest,contract,spec.attacks,evaluation,minimum=.90,epsilon=1e-8,tolerance=1e-8,cost_tolerance=1e-8)
    repeated=export_artifact(repeated_policy,repeated_context,spec.manifest,contract,spec.attacks,applicable_domain=bound.plan.domain)
    equivalence=verify_equivalent(artifact,repeated)
    destination=OUT/'reliability-first';destination.mkdir()
    with (destination/'policy.json').open('x',encoding='utf-8') as f:f.write(artifact.model_dump_json(indent=2))
    PolicyArtifact.model_validate_json((destination/'policy.json').read_text(encoding='utf-8'))
    os.environ['VERIFIER_COLLECTION_ADAPTER_CONFIG']=str((ROOT/'adapter.json').resolve())
    observer=ProjectObserver();bundle=RecordingBundle.model_validate(read(ROOT/'collection/recordings.json'))
    handle=(OUT/'runtime-network.jsonl').open('x',encoding='utf-8')
    guard=NetworkBudget(read(ROOT/'adapter.json')['ollama_url'],handle,generation_limit=0,metadata_limit=200)
    original_request=requests.Session.request
    requests.Session.request=lambda session,method,url,*args,**kw:guard.call(original_request,session,method,url,*args,**kw)
    class Retained(BaseVerifier):
        def __init__(self,attempt):self.attempt=attempt
        @property
        def name(self):return self.attempt.verifier_name
        def verify(self,*args,**kw):
            if self.attempt.state=='failed':raise VerifierExecutionFailure('retained failed attempt')
            if self.attempt.state=='unavailable':raise VerifierUnavailable('retained unavailable attempt')
            return self.attempt.report
    class Draw:
        def __init__(self,value):self.value=value
        def random(self):return self.value
    probabilities=dict(policy.solution.probabilities);checks=[];cumulative=0.
    for strategy in policy.strategies:
        probability=probabilities[strategy.strategy_id];draw=cumulative+probability/2;cumulative+=probability
        if probability==0:continue
        for correct in (True,False):
            example=next(e for e in spec.manifest.partition('development').examples if e.answer_is_correct==correct)
            recorded=next(e for e in bundle.request.examples if e.run_id==example.validation_id)
            selector=VerifierSelector(verifiers=[Retained(a) for a in example.attempts],capabilities={a.verifier_name:BUILTIN_CAPABILITIES[a.verifier_name] for a in example.attempts})
            episode=DeploymentEpisode(episode_id='reliability-retained-parity',context=bound,contract=contract,execution_configuration_id=artifact.execution_configuration_id)
            actual=GameRuntime(InMemoryPolicyProvider((artifact,)),episode,Draw(draw),resource_observer=observer).run(selector,recorded.analysis,
                ValidationRequest(question=recorded.question,answer=recorded.answer,context=recorded.reference),example.validation_id)
            expected=replay(bound,strategy,enumerate_attacks(bound.dependencies,spec.attacks)[0],spec.attacks,contract,example)
            if (actual.summary['selection_status']!='selected' or actual.summary['selected_strategy_id']!=strategy.strategy_id
                or actual.public_status!=expected.public_status or actual.detail.raw_score!=expected.numerical_score
                or actual.summary['contributors']!=expected.contributors):raise ValueError('new contract runtime/replay mismatch')
            checks.append(dict(example_id=example.example_id,strategy_id=strategy.strategy_id,parity=True,summary=actual.summary))
    def metrics_for(artifact,source):
        probs=dict(artifact.policy.solution.probabilities);rows=[]
        for attack in enumerate_attacks(artifact.context.dependencies,spec.attacks):
            metrics=summarize(tuple((o,probs[o.strategy_id]) for o in source.outcomes if o.attack_id==attack.attack_id),artifact.context.loss_configuration)
            rows.append(dict(attack=attack.kind,metrics=metrics.model_dump(mode='json'),validation_loss=metrics.validation_loss(artifact.context.loss_configuration),uncertainty_rate=metrics.uncertainty_rate))
        return rows
    intermediate=PolicyArtifact.model_validate_json((OUT/'informative-old-objective/policy.json').read_text(encoding='utf-8'))
    qs=dict(policy.matrix.clean_coverage.strategy_coverage)
    scenarios=metrics_for(artifact,evaluation)
    result=dict(label='EXPLORATORY DEVELOPMENT ONLY; informative contributors and reliability-first optimization',
        artifact_id=artifact.artifact_id,policy_id=policy.policy_id,matrix_id=policy.matrix.matrix_id,
        settings=dict(q_min=.90,epsilon_loss=1e-8,loss_tolerance=1e-8,cost_tolerance_ms=1e-8,budget_ms=bound.budget,original_losses=bound.loss_configuration.model_dump(mode='json')),
        maximum_achievable_clean_coverage=maximum,scenarios=scenarios,
        zero_clean_coverage_probability=math.fsum(p for sid,p in policy.solution.probabilities if qs[sid]==0),
        coverage_floor_binding=abs(scenarios[0]['metrics']['decision_coverage']-.90)<=1e-12,
        strategies=[dict(**s.model_dump(mode='json'),probability=probabilities[s.strategy_id],clean_coverage=qs[s.strategy_id]) for s in policy.strategies],
        certificate=policy.solution.model_dump(mode='json'),reproducibility=equivalence,runtime_checks=checks,
        original_policy=read(ROOT/'fitted-policy/build-report.json')['scientific_outputs'],
        original_coverage_variants=read('build/factual-coverage-exploration42/variants-summary.json'),
        informative_old_objective=dict(artifact_id=intermediate.artifact_id,probabilities=intermediate.policy.solution.probabilities,scenarios=metrics_for(intermediate,evaluation)),
        provenance=dict(original_approval=read(ROOT/'approval-binding.json'),environment=environment_versions(),
            source_evaluation_id=content_id(evaluation.model_dump(mode='json')),history_snapshot=bound.reputation_snapshot_id,
            application_source_digest=content_id([(p.as_posix(),hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted(Path('app').rglob('*.py'))]),
            driver_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),sampling_seed=42,additional_inference=0,new_calibration=False),network_counts=guard.counts)
    save(destination/'report.json',result)
    for path,sha in read(OUT/'preserved-input-hashes.json').items():assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==sha
    save(OUT/'final-verification.json',dict(original_inputs_unchanged=True,provider_reload=True,two_stage_certificates=True,
        repeat_equivalence=equivalence,runtime_checks=len(checks),final_payload_access_guard=True,new_inference=0,new_calibration=False))
    print('Reliability-first artifact:',artifact.artifact_id,'clean coverage:',scenarios[0]['metrics']['decision_coverage'],
        'zero-coverage probability:',result['zero_clean_coverage_probability'],'worst validation loss:',policy.solution.game_value,
        'expected cost:',policy.solution.reliability_certificate.expected_cost,flush=True)

def main():
    def guard(event,args):
        if event=='open' and isinstance(args[0],str) and 'custody' in Path(args[0]).parts:raise AssertionError('final-test payload access forbidden')
    sys.addaudithook(guard)
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['baseline','replay','fit']);a=p.parse_args()
    if a.phase=='baseline':baseline()
    elif a.phase=='replay':new_replay()
    else:fit()

if __name__=='__main__':main()
