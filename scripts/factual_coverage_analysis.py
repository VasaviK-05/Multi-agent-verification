"""Exploratory development-only coverage analysis over retained recordings."""
import argparse
from collections import Counter
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path('build/factual-policy42-20261029')
OUT=Path('build/factual-coverage-exploration42')

def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def save(p,v):
    with Path(p).open('x',encoding='utf-8') as f:json.dump(v,f,indent=2,allow_nan=False)

def diagnose():
    from app.game.artifacts import PolicyArtifact
    from app.game.research.specification import PolicyBuildSpecification
    from app.game.offline.evaluation import construct_payoffs
    from app.game.offline.attacks import enumerate_attacks
    from app.decision.decision_engine import log_odds_weight
    OUT.mkdir(exist_ok=False)
    artifact=PolicyArtifact.model_validate_json((ROOT/'fitted-policy/policy.json').read_text(encoding='utf-8'))
    spec=PolicyBuildSpecification.model_validate(read(ROOT/'policy-input.json'))
    evaluation=construct_payoffs(artifact.context,spec.manifest,spec.contract,spec.attacks)
    save(OUT/'original-evaluation.json',evaluation.model_dump(mode='json'))
    attacks=enumerate_attacks(artifact.context.dependencies,spec.attacks)
    rows=[]
    for strategy in artifact.policy.strategies:
        cells=[]
        for attack in attacks:
            outcomes=[o for o in evaluation.outcomes if o.strategy_id==strategy.strategy_id and o.attack_id==attack.attack_id]
            metrics=next(m for s,a,m in evaluation.metrics if s==strategy.strategy_id and a==attack.attack_id)
            cells.append(dict(attack=attack.kind,metrics=metrics.model_dump(mode='json'),validation_loss=metrics.validation_loss(artifact.context.loss_configuration),
                contributors=dict(Counter(o.contributors for o in outcomes)),reasons=dict(Counter(r for o in outcomes for r in o.reasons)),
                preliminary_status=dict(Counter(o.numerical_status for o in outcomes)),public_status=dict(Counter(o.public_status for o in outcomes))))
        rows.append(dict(**strategy.model_dump(mode='json'),scenarios=cells,worst_case_objective=max(c['metrics']['mean_loss'] for c in cells)))
    result=dict(scope=spec.scientific_scope,original_artifact_id=artifact.artifact_id,
        original_sha256=hashlib.sha256((ROOT/'fitted-policy/policy.json').read_bytes()).hexdigest(),
        history=[dict(**asdict(s),log_odds=log_odds_weight(s.posterior_mean)) for s in artifact.context.plan.reputation_statistics],
        strategies=rows,dependencies=artifact.context.dependencies.model_dump(mode='json'),
        settings=artifact.context.loss_configuration.model_dump(mode='json'),budget=artifact.context.budget,
        provenance='Existing history/development only; no new inference/calibration; exploratory targets .25/.50/.75 authorized by user')
    save(OUT/'all-strategies.json',result)
    lines=['# All-strategy diagnosis (before changes)','','Development only; every strategy and attack retained.','',json.dumps(result['history'],indent=2)]
    for row in rows:
        lines+=['',f"## {row['verifiers']} / {row['aggregation']}",'',f"Cost {row['estimated_cost']:.9f} ms; worst objective {row['worst_case_objective']:.9f}."]
        for c in row['scenarios']:
            m=c['metrics'];lines.append(f"- {c['attack']}: coverage {m['decision_coverage']:.6f}; false accept/reject {m['false_accept']}/{m['false_reject']}; validation loss {c['validation_loss']:.9f}; objective {m['mean_loss']:.9f}; contributors {c['contributors']}; reasons {c['reasons']}.")
    with (OUT/'all-strategies.md').open('x',encoding='utf-8') as f:f.write('\n'.join(lines)+'\n')
    print('All 14 strategies diagnosed:',OUT)


def variants():
    import math
    import os
    import random
    import requests
    from app.game.artifacts import PolicyArtifact, InMemoryPolicyProvider, DeploymentEpisode
    from app.game.offline.evaluation import Evaluation, export_artifact, summarize
    from app.game.offline.coverage import fit_clean_coverage
    from app.game.research.specification import PolicyBuildSpecification
    from app.game.solver import validate_solution
    from app.game.offline.build import verify_equivalent, environment_versions
    from app.game.models import content_id
    from app.game.offline.attacks import enumerate_attacks
    from app.game.offline.replay import replay
    from app.game.execution import GameRuntime, VerifierExecutionFailure
    from app.game.offline.recording_adapters import ProjectObserver
    from app.game.offline.collection import RecordingBundle
    from app.verifiers.base_verifier import BaseVerifier
    from app.selection.verifier_selector import VerifierSelector
    from app.selection.capabilities import BUILTIN_CAPABILITIES
    from app.selection.models import VerifierUnavailable
    from app.models.schemas import ValidationRequest
    from scripts.run_factual_diagnostic import NetworkBudget
    original=PolicyArtifact.model_validate_json((ROOT/'fitted-policy/policy.json').read_text(encoding='utf-8'))
    diagnosis=read(OUT/'all-strategies.json')
    if hashlib.sha256((ROOT/'fitted-policy/policy.json').read_bytes()).hexdigest()!=diagnosis['original_sha256']:
        raise ValueError('original artifact changed')
    spec=PolicyBuildSpecification.model_validate(read(ROOT/'policy-input.json'))
    evaluation=Evaluation.model_validate(read(OUT/'original-evaluation.json'))
    if evaluation.matrix!=original.policy.matrix:raise ValueError('diagnosis differs from original matrix')
    bundle=RecordingBundle.model_validate(read(ROOT/'collection/recordings.json'))
    os.environ['VERIFIER_COLLECTION_ADAPTER_CONFIG']=str((ROOT/'adapter.json').resolve())
    observer=ProjectObserver()
    audit=(OUT/'runtime-network.jsonl').open('x',encoding='utf-8')
    guard=NetworkBudget(read(ROOT/'adapter.json')['ollama_url'],audit,generation_limit=0,metadata_limit=100)
    request_original=requests.Session.request
    requests.Session.request=lambda session,method,url,*args,**kw:guard.call(request_original,session,method,url,*args,**kw)
    class Retained(BaseVerifier):
        def __init__(self,attempt):self.attempt=attempt
        @property
        def name(self):return self.attempt.verifier_name
        def verify(self,*args,**kw):
            if self.attempt.state=='failed':raise VerifierExecutionFailure('retained failure')
            if self.attempt.state=='unavailable':raise VerifierUnavailable('retained unavailable')
            return self.attempt.report
    class Draw:
        def __init__(self,value):self.value=value
        def random(self):return self.value
    outputs=[]
    for target in (.25,.50,.75):
        destination=OUT/('coverage-'+str(int(target*100)))
        destination.mkdir(exist_ok=False)
        context,policy=fit_clean_coverage(original.context,spec.manifest,spec.contract,spec.attacks,evaluation,minimum=target)
        artifact=export_artifact(policy,context,spec.manifest,spec.contract,spec.attacks,applicable_domain=context.plan.domain)
        artifact=PolicyArtifact.model_validate_json(artifact.model_dump_json())
        validate_solution(artifact.policy.matrix,artifact.policy.solution)
        repeated_context,repeated_policy=fit_clean_coverage(original.context,spec.manifest,spec.contract,spec.attacks,evaluation,minimum=target)
        repeated=export_artifact(repeated_policy,repeated_context,spec.manifest,spec.contract,spec.attacks,applicable_domain=context.plan.domain)
        equivalence=verify_equivalent(artifact,repeated)
        probabilities=dict(policy.solution.probabilities)
        scenarios=[]
        for attack in enumerate_attacks(context.dependencies,spec.attacks):
            metrics=summarize(tuple((o,probabilities[o.strategy_id]) for o in evaluation.outcomes if o.attack_id==attack.attack_id),context.loss_configuration)
            scenarios.append(dict(attack=attack.kind,metrics=metrics.model_dump(mode='json'),validation_loss=metrics.validation_loss(context.loss_configuration),
                uncertainty_rate=metrics.uncertainty_rate))
        checks=[];cumulative=0.
        for strategy in policy.strategies:
            probability=probabilities[strategy.strategy_id]
            draw=cumulative+probability/2;cumulative+=probability
            if probability==0:continue
            for correct in (True,False):
                example=next(e for e in spec.manifest.partition('development').examples if e.answer_is_correct==correct)
                recorded=next(e for e in bundle.request.examples if e.run_id==example.validation_id)
                selector=VerifierSelector(verifiers=[Retained(a) for a in example.attempts],capabilities={a.verifier_name:BUILTIN_CAPABILITIES[a.verifier_name] for a in example.attempts})
                episode=DeploymentEpisode(episode_id='exploratory-retained-parity',context=context,contract=spec.contract,execution_configuration_id=artifact.execution_configuration_id)
                run=GameRuntime(InMemoryPolicyProvider((artifact,)),episode,Draw(draw),resource_observer=observer).run(selector,recorded.analysis,
                    ValidationRequest(question=recorded.question,answer=recorded.answer,context=recorded.reference),example.validation_id)
                expected=replay(context,strategy,enumerate_attacks(context.dependencies,spec.attacks)[0],spec.attacks,spec.contract,example)
                if (run.summary['selection_status']!='selected' or run.summary['selected_strategy_id']!=strategy.strategy_id
                    or run.public_status!=expected.public_status or run.detail.raw_score!=expected.numerical_score):raise ValueError('variant runtime/replay mismatch')
                checks.append(dict(example_id=example.example_id,strategy_id=strategy.strategy_id,parity=True,summary=run.summary))
        result=dict(label='EXPLORATORY DEVELOPMENT ONLY; not approved primary settings',target=target,artifact_id=artifact.artifact_id,
            policy_id=policy.policy_id,matrix_id=policy.matrix.matrix_id,source_artifact_id=original.artifact_id,
            constraint=json.loads(context.clean_coverage_json),certificate=policy.solution.model_dump(mode='json'),
            strategies=[dict(**s.model_dump(mode='json'),probability=probabilities[s.strategy_id]) for s in policy.strategies],
            scenarios=scenarios,worst_case_objective=policy.solution.game_value,
            worst_case_attacked_coverage=min(s['metrics']['decision_coverage'] for s in scenarios[1:]),
            reproducibility=equivalence,runtime_checks=checks,
            provenance=dict(configuration='Only additive finalized clean-development coverage constraint changed; all original losses, resources, budgets, priors, dependencies and guards retained',
                original_approval=read(ROOT/'approval-binding.json'),environment=environment_versions(),
                application_source_digest=content_id([(p.as_posix(),hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted(Path('app').rglob('*.py'))]),
                driver_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),sampling_seed=42,additional_inference=0))
        save(destination/'report.json',result)
        with (destination/'policy.json').open('x',encoding='utf-8') as f:f.write(artifact.model_dump_json(indent=2))
        PolicyArtifact.model_validate_json((destination/'policy.json').read_text(encoding='utf-8'))
        outputs.append(result)
        print('Published exploratory target',target,'coverage',scenarios[0]['metrics']['decision_coverage'],'worst objective',policy.solution.game_value,flush=True)
    assert hashlib.sha256((ROOT/'fitted-policy/policy.json').read_bytes()).hexdigest()==diagnosis['original_sha256']
    save(OUT/'variants-summary.json',outputs)
    print('No inference; network counts:',guard.counts)


def verify():
    from app.game.artifacts import PolicyArtifact
    from app.game.offline.coverage import prepare_clean_coverage
    from app.game.offline.evaluation import Evaluation
    from app.game.research.specification import PolicyBuildSpecification
    from app.game.solver import validate_solution
    original=PolicyArtifact.model_validate_json((ROOT/'fitted-policy/policy.json').read_text(encoding='utf-8'))
    spec=PolicyBuildSpecification.model_validate(read(ROOT/'policy-input.json'))
    source=Evaluation.model_validate(read(OUT/'original-evaluation.json'))
    diagnosis=read(OUT/'all-strategies.json')
    assert original.artifact_id==diagnosis['original_artifact_id']
    assert hashlib.sha256((ROOT/'fitted-policy/policy.json').read_bytes()).hexdigest()==diagnosis['original_sha256']
    checked=[]
    lines=['# Exploratory coverage-constrained development results','',
        'Not primary paper settings or held-out evidence. Clean coverage is the exact policy-weighted expectation over retained development examples, not a Monte Carlo estimate.',
        '', 'The original policy remains unchanged. All fourteen strategies are retained in every variant.',
        '', 'History weights: Evidence and Confidence each posterior 41/42, log-odds log(41), group reliability 20/21; Semantic and Rule each 1/2 and zero weights.',
        'Group aggregation counts active reports, including zero-reliability Semantic; log-odds aggregation excludes its zero-weight vote. This existing contract is unchanged.',
        '', '## Original', '', 'Clean/all-attack loss 0.2; coverage 0; expected cost 181.689941 ms; worst objective 0.201402409692. Evidence + Rule / reputation-weighted probability 1; all thirteen other probabilities zero.']
    for target in (.25,.5,.75):
        destination=OUT/('coverage-'+str(int(target*100)))
        artifact=PolicyArtifact.model_validate_json((destination/'policy.json').read_text(encoding='utf-8'))
        context,matrix=prepare_clean_coverage(original.context,spec.manifest,spec.contract,spec.attacks,source,minimum=target)
        assert matrix==artifact.policy.matrix and context==artifact.context
        assert context.reputation_snapshot_id==original.context.reputation_snapshot_id
        validate_solution(matrix,artifact.policy.solution)
        report=read(destination/'report.json')
        assert all(c['parity'] for c in report['runtime_checks']) and len(report['runtime_checks'])==4
        checked.append(dict(target=target,artifact_id=artifact.artifact_id,policy_id=artifact.policy.policy_id,matrix_id=matrix.matrix_id,
            certificate=artifact.policy.solution.coverage_certificate.model_dump(mode='json'),clean_source_replay_verified=True,
            provider_reload=True,runtime_checks=len(report['runtime_checks']),reproducibility=report['reproducibility']))
        lines+=['',f'## Target {target:.0%}', '',f"Artifact `{artifact.artifact_id}`; worst objective {report['worst_case_objective']:.12g}.",'','Every strategy:']
        for s in report['strategies']:lines.append(f"- {s['verifiers']} / {s['aggregation']}: probability {s['probability']:.12g}, estimated cost {s['estimated_cost']:.9f} ms.")
        lines+=['','Scenarios (false counts are expected counts out of forty):']
        for cell in report['scenarios']:
            m=cell['metrics']
            lines.append(f"- {cell['attack']}: coverage {m['decision_coverage']:.3%}, false accept/reject {m['false_accept']:.6g}/{m['false_reject']:.6g}, uncertainty {cell['uncertainty_rate']:.3%}, validation loss {cell['validation_loss']:.9f}, estimated cost {m['estimated_resource_cost']:.9f} ms, cost-inclusive objective {m['mean_loss']:.9f}.")
        lines+=['','Certificate:','```json',json.dumps(artifact.policy.solution.coverage_certificate.model_dump(mode='json'),indent=2),'```']
    # Retain actual per-example effective weights, confidence and group influence.
    weight_examples=[]
    for strategy in original.policy.strategies:
        outcomes=[o for o in source.outcomes if o.strategy_id==strategy.strategy_id and o.attack_id==source.matrix.attack_ids[0]]
        weight_examples.append(dict(strategy=strategy.model_dump(mode='json'),decisions=[json.loads(next(o for o in outcomes if o.answer_is_correct==correct).decision_json) for correct in (True,False)]))
    save(OUT/'effective-weight-examples.json',weight_examples)
    lines+=['','## Recommendation and limitations','',
        'Use the 50% target as a concrete next exploratory engineering candidate if making a decisive clean decision on half the supported population is worth increasing worst-case objective from 0.20140241 to 0.35160113. Do not activate or call it universally best. Targets 25% and 75% are explicit alternatives, not publication selection.',
        'Scope remains the reference-assisted known-corpus capital-fact pilot. One shared compromise component includes all informative verifiers. The constraint cannot create independent evidence, improve the source labels, or guarantee attacked coverage. Suppression yields zero coverage in all variants.',
        'Only additive clean coverage settings changed. All original losses, budgets, dependencies, guards, recordings and calibration remain unchanged. Final-test payload access is forbidden throughout these commands.']
    with (OUT/'exploratory-results.md').open('x',encoding='utf-8') as f:f.write('\n'.join(lines)+'\n')
    save(OUT/'final-verification.json',dict(original_artifact_unchanged=True,original_artifact_id=original.artifact_id,variants=checked,
        final_payload_access_guard=True,final_evaluation=False,additional_inference=0,additional_calibration=False,
        source_validation='Recomputed finalized clean replay from source records; exact original matrices and source evaluation bindings checked'))
    print(json.dumps(checked,indent=2))

def main():
    def guard(event,args):
        if event=='open' and isinstance(args[0],str) and 'custody' in Path(args[0]).parts:raise AssertionError('final payload access forbidden')
    sys.addaudithook(guard)
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['diagnose','variants','verify']);a=p.parse_args()
    if a.phase=='diagnose':diagnose()
    elif a.phase=='variants':variants()
    else:verify()

if __name__=='__main__':main()
