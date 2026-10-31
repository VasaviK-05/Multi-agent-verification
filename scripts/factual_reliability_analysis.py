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
        provenance=dict(original_approval=read(ROOT/'approval-binding.json'),environment={**environment_versions(),
            'linprog_options':{'stage_a':'SciPy defaults','stage_b':{'primal_feasibility_tolerance':1e-10,'dual_feasibility_tolerance':1e-10}}},
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


def report_results():
    from app.game.artifacts import PolicyArtifact
    from app.game.offline.evaluation import Evaluation, summarize
    from app.game.offline.attacks import enumerate_attacks, AttackSpecification
    from app.game.solver import validate_solution
    from app.game.models import content_id
    legacy=Evaluation.model_validate(read(OUT/'legacy-reproduced-evaluation.json'))
    current=Evaluation.model_validate(read(OUT/'informative-evaluation.json'))
    fitted=read(OUT/'reliability-first/report.json')
    sources=[('Original',ROOT/'fitted-policy/policy.json',legacy)]
    sources += [('Legacy coverage '+str(q)+'%',Path('build/factual-coverage-exploration42')/('coverage-'+str(q))/'policy.json',legacy) for q in (25,50,75)]
    sources += [('Informative contributors, old objective',OUT/'informative-old-objective/policy.json',current),
        ('Informative contributors, reliability first',OUT/'reliability-first/policy.json',current)]
    rows=[]
    lines=['# Informative-contributor reliability-first exploration','',
        'Development only. No final-test access, inference, recalibration or deployment. All fourteen strategies are retained in every policy.','',
        'Legacy all-strategy replay was reproduced exactly before changing code. New-contributor outcomes were rebuilt from the unchanged retained reports; history reputation is unchanged.']
    for label,path,evaluation in sources:
        artifact=PolicyArtifact.model_validate_json(path.read_text(encoding='utf-8'))
        validate_solution(artifact.policy.matrix,artifact.policy.solution)
        probs=dict(artifact.policy.solution.probabilities)
        clean_id=evaluation.matrix.attack_ids[0]
        qs={s:m.decision_coverage for s,a,m in evaluation.metrics if a==clean_id}
        scenarios=[]
        lines+=['',f'## {label}','',f'Artifact `{artifact.artifact_id}` at `{path.as_posix()}`.','', 'Every strategy:']
        for strategy in artifact.policy.strategies:
            lines.append(f"- {strategy.verifiers} / {strategy.aggregation}: probability {probs[strategy.strategy_id]:.12g}; estimated cost {strategy.estimated_cost:.9f} ms; finalized clean coverage {qs[strategy.strategy_id]:.6f}.")
        for attack in enumerate_attacks(artifact.context.dependencies,evaluation.attacks):
            m=summarize(tuple((o,probs[o.strategy_id]) for o in evaluation.outcomes if o.attack_id==attack.attack_id),artifact.context.loss_configuration)
            cell=dict(attack=attack.kind,metrics=m.model_dump(mode='json'),validation_loss=m.validation_loss(artifact.context.loss_configuration),uncertainty_rate=m.uncertainty_rate)
            scenarios.append(cell)
        zero=sum(probs[s] for s,q in qs.items() if q==0)
        lines+=['',f'Probability on zero-clean-coverage strategies: {zero:.12g}.','', 'Scenarios (expected false counts out of forty):']
        for c in scenarios:
            m=c['metrics'];lines.append(f"- {c['attack']}: coverage {m['decision_coverage']:.6%}, false accept/reject {m['false_accept']:.9g}/{m['false_reject']:.9g}, uncertainty {c['uncertainty_rate']:.6%}, validation loss {c['validation_loss']:.12g}, expected cost {m['estimated_resource_cost']:.9f} ms, old cost-inclusive diagnostic {m['mean_loss']:.12g}.")
        rows.append(dict(label=label,artifact_id=artifact.artifact_id,path=path.as_posix(),
            strategies=[dict(**s.model_dump(mode='json'),probability=probs[s.strategy_id],clean_coverage=qs[s.strategy_id]) for s in artifact.policy.strategies],
            scenarios=scenarios,zero_clean_coverage_probability=zero,worst_validation_loss=max(c['validation_loss'] for c in scenarios),
            worst_old_cost_inclusive_objective=max(c['metrics']['mean_loss'] for c in scenarios)))
    lines+=['','## Every strategy under the informative contract','']
    for row in read(OUT/'informative-all-strategies.json'):
        lines+=['',f"### {row['verifiers']} / {row['aggregation']}",f"Cost {row['estimated_cost']:.9f} ms."]
        for c in row['scenarios']:
            m=c['metrics'];lines.append(f"- {c['attack']}: coverage {m['decision_coverage']:.6f}, validation loss {c['validation_loss']:.9f}, false accept/reject {m['false_accept']}/{m['false_reject']}, contributors {c['contributor_counts']}, uncertainty reasons {c['reason_counts']}.")
    certificate=fitted['certificate']['reliability_certificate'];stage_a=json.loads(certificate['stage_a_json'])
    lines+=['','## Certificates and interpretation','',
        f"Stage A optimum {stage_a['game_value']:.12g}, primal/dual gap {stage_a['primal_dual_gap']:.12g}; loss tolerance 1e-8.",
        f"Stage B cap {certificate['reliability_cap']:.12g}; expected cost {certificate['expected_cost']:.9f} ms; cost dual bound {certificate['cost_dual_lower_bound']:.9f} ms; gap {certificate['cost_primal_dual_gap']:.12g} ms; cost tolerance 1e-8 ms.",
        'Epsilon is 1e-8 loss units; cap feasibility is checked at 1e-12 loss units. Coverage and probability normalization tolerance is 1e-12.',
        'The 90% floor binds. About 5.263% of draws choose a zero-clean-coverage plan; the rest choose Evidence+Confidence, which has 95% clean coverage on these records. This is expected coverage, not request-specific adaptation. Sampling precedes verifier outcomes.',
        'Evidence+Confidence is the least costly team with two informative history contributors. Evidence+Rule is the cheapest always-abstaining plan. Their mixture meets the approved floor at minimum primary loss, then minimum cost. The floor prevents Stage B from trading any further reliability for cost in this dataset.',
        'Both aggregations on Evidence+Confidence have equivalent finalized empirical losses/coverage under this contract. Solver allocation is not evidence that reputation weighting is superior.',
        'All informative verifiers remain in one modeled compromise group. Forced support is worst case and suppression gives zero coverage. Two informative contributors are not independent evidence.',
        'Recommendation: use this variant for the next engineering review when two informative contributors and 90% expected clean coverage are required. Its high shared-group worst-case error precludes a robustness claim or automatic operational activation.',
        'If the product forbids intentionally choosing an incapable plan, this variant still falls short. A future separately versioned, prospectively approved plan-admissibility contract could require enough positive-history potentially influential members before optimization. That rule is not implemented here; no strategy was removed after observing results.',
        'Scope remains the constructed reference-assisted known-corpus capital-fact pilot, not open-domain factual reliability. These are exploratory development findings, not held-out superiority or paper settings.']
    save(OUT/'comparison.json',rows)
    with (OUT/'comparison.md').open('x',encoding='utf-8') as f:f.write('\n'.join(lines)+'\n')
    for path,sha in read(OUT/'preserved-input-hashes.json').items():assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==sha
    save(OUT/'comparison-verification.json',dict(all_six_policies_reloaded_and_certified=True,original_files_unchanged=True,
        final_payload_access_guard=True,additional_inference=0,new_calibration=False,
        application_source_digest=content_id([(p.as_posix(),hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted(Path('app').rglob('*.py'))]),
        report_driver_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()))
    print('Six-policy comparison, all-strategy diagnostics and certificates written to',OUT,flush=True)


def isolate_optimization():
    """Same informative semantics and 90% coverage, old objective as a diagnostic."""
    from app.game.artifacts import PolicyArtifact
    from app.game.models import PlanningContext
    from app.game.execution_contract import ExecutionContract
    from app.game.research.specification import PolicyBuildSpecification
    from app.game.offline.evaluation import Evaluation, export_artifact, summarize
    from app.game.offline.coverage import fit_clean_coverage
    context=PlanningContext.model_validate(read(OUT/'informative-context.json'))
    contract=ExecutionContract.model_validate(read(OUT/'informative-contract.json'))
    source=Evaluation.model_validate(read(OUT/'informative-evaluation.json'))
    spec=PolicyBuildSpecification.model_validate(read(ROOT/'policy-input.json'))
    bound,policy=fit_clean_coverage(context,spec.manifest,contract,spec.attacks,source,minimum=.90)
    artifact=export_artifact(policy,bound,spec.manifest,contract,spec.attacks,applicable_domain=bound.plan.domain)
    directory=OUT/'informative-coverage90-old-objective';directory.mkdir()
    with (directory/'policy.json').open('x',encoding='utf-8') as f:f.write(artifact.model_dump_json(indent=2))
    PolicyArtifact.model_validate_json((directory/'policy.json').read_text(encoding='utf-8'))
    scenarios=[];probs=dict(policy.solution.probabilities)
    for attack in source.matrix.attack_ids:
        m=summarize(tuple((o,probs[o.strategy_id]) for o in source.outcomes if o.attack_id==attack),bound.loss_configuration)
        scenarios.append(dict(attack_id=attack,metrics=m.model_dump(mode='json'),validation_loss=m.validation_loss(bound.loss_configuration)))
    new=read(OUT/'reliability-first/report.json')
    equivalent=all(abs(a['validation_loss']-b['validation_loss'])<=1e-12
        and abs(a['metrics']['estimated_resource_cost']-b['metrics']['estimated_resource_cost'])<=1e-8
        and abs(a['metrics']['decision_coverage']-b['metrics']['decision_coverage'])<=1e-12
        for a,b in zip(scenarios,new['scenarios']))
    result=dict(label='DIAGNOSTIC: holds contributor semantics and 90% floor fixed; changes objective only',
        artifact_id=artifact.artifact_id,strategies=[dict(**s.model_dump(mode='json'),probability=probs[s.strategy_id]) for s in policy.strategies],
        scenarios=scenarios,certificate=policy.solution.model_dump(mode='json'),
        equivalent_finalized_metrics_to_lexicographic=equivalent,
        interpretation='This pilot does not demonstrate an empirical selection advantage from objective ordering when coverage and contributor contracts are held fixed. The synthetic solver case establishes the intended ordering when loss and cost conflict.')
    save(OUT/'optimization-isolation.json',result)
    print('Old objective with new semantics and 90% floor: equivalent finalized metrics to lexicographic:',equivalent,flush=True)

def main():
    def guard(event,args):
        if event=='open' and isinstance(args[0],str) and 'custody' in Path(args[0]).parts:raise AssertionError('final-test payload access forbidden')
    sys.addaudithook(guard)
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['baseline','replay','fit','report','isolate']);a=p.parse_args()
    if a.phase=='baseline':baseline()
    elif a.phase=='replay':new_replay()
    elif a.phase=='fit':fit()
    elif a.phase=='report':report_results()
    else:isolate_optimization()

if __name__=='__main__':main()
