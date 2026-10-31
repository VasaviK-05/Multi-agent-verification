"""Development-only target sweep over frozen multitask records; no inference."""
import hashlib
import json
from pathlib import Path
import sys
from collections import Counter
from app.game.models import PlanningContext
from app.game.execution_contract import ExecutionContract
from app.game.offline.records import TrainingManifest
from app.game.offline.attacks import AttackSpecification, enumerate_attacks
from app.game.offline.evaluation import Evaluation, construct_payoffs, summarize, export_artifact
from app.game.offline.reliability import fit_reliability_first
from app.game.offline.build import verify_equivalent, environment_versions
from app.game.artifacts import PolicyArtifact
from scripts.multitask_policy42 import save, read

SOURCE=Path('build/multitask-policy42')
OUT=Path('build/multitask-uncertainty-sweep42')
TARGETS=(0.,.25,.50,.75,.90)

def weighted_reasons(evaluation,probabilities,attack):
    counts=Counter()
    for o in evaluation.outcomes:
        if o.attack_id!=attack or o.public_status!='uncertain':continue
        # Separate score-band uncertainty from guard overrides; guards can overlap.
        for reason in o.reasons or ('weak_or_conflicting_signal',):counts[reason]+=probabilities[o.strategy_id]
    return dict(counts)

def main():
    def guard(event,args):
        if event=='open' and isinstance(args[0],str) and any(p.casefold()=='custody' for p in Path(args[0]).parts):
            raise AssertionError('final payload access forbidden')
    sys.addaudithook(guard)
    OUT.mkdir(exist_ok=False)
    all_rows=[];audit=[];preserved={}
    for cohort in ('arithmetic','semantic','factual'):
        source=SOURCE/cohort;destination=OUT/cohort;destination.mkdir()
        for name in ('calibration.json','source-context.json','training-manifest.json','contract.json','development-evaluation.json','unconstrained-comparison/policy.json'):
            p=source/name;preserved[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()
        context=PlanningContext.model_validate(read(source/'source-context.json'))
        manifest=TrainingManifest.model_validate(read(source/'training-manifest.json'))
        contract=ExecutionContract.model_validate(read(source/'contract.json'))
        evaluation=Evaluation.model_validate(read(source/'development-evaluation.json'))
        attacks=evaluation.attacks
        actual=construct_payoffs(context,manifest,contract,attacks)
        if actual!=evaluation:raise ValueError('retained evaluation no longer reproduces: '+cohort)
        clean=evaluation.matrix.attack_ids[0]
        qs={sid:m.decision_coverage for sid,aid,m in evaluation.metrics if aid==clean}
        maximum=max(qs.values())
        for target in TARGETS:
            directory=destination/('coverage-'+str(round(target*100)).zfill(2));directory.mkdir()
            row=dict(cohort=cohort,target=target,maximum_clean_coverage=maximum,budget=context.budget,
                status='infeasible' if target>maximum else 'pending',artifact_created=False,
                provenance='User clarification ae37b9f0-5320-46b2-9e31-20e345f18f96; exploratory development, no activation',
                context_id=context.compatibility_id,source_manifest_id=manifest.manifest_id)
            if target<=maximum:
                bound,policy=fit_reliability_first(context,manifest,contract,attacks,evaluation,minimum=target)
                artifact=export_artifact(policy,bound,manifest,contract,attacks,applicable_domain=context.plan.domain)
                second_bound,second_policy=fit_reliability_first(context,manifest,contract,attacks,actual,minimum=target)
                second=export_artifact(second_policy,second_bound,manifest,contract,attacks,applicable_domain=context.plan.domain)
                equivalent=verify_equivalent(artifact,second)
                save(directory/'policy.json',artifact.model_dump(mode='json'))
                loaded=PolicyArtifact.model_validate(read(directory/'policy.json'))
                probabilities=dict(policy.solution.probabilities);scenarios=[]
                for attack in enumerate_attacks(context.dependencies,attacks):
                    m=summarize(tuple((o,probabilities[o.strategy_id]) for o in evaluation.outcomes if o.attack_id==attack.attack_id),context.loss_configuration)
                    scenarios.append(dict(attack=attack.kind,attack_id=attack.attack_id,metrics=m.model_dump(mode='json'),
                        validation_loss=m.validation_loss(context.loss_configuration),uncertainty_rate=m.uncertainty_rate,
                        uncertainty_reasons=weighted_reasons(evaluation,probabilities,attack.attack_id)))
                row.update(status='complete',artifact_created=True,artifact_id=loaded.artifact_id,
                    probabilities=[dict(**s.model_dump(mode='json'),probability=probabilities[s.strategy_id]) for s in policy.strategies],
                    zero_coverage_mass=sum(p for sid,p in probabilities.items() if qs[sid]==0),scenarios=scenarios,
                    worst_validation_loss=max(s['validation_loss'] for s in scenarios),certificate=policy.solution.model_dump(mode='json'),
                    reproducibility=equivalent,artifact_path=str(directory/'policy.json'))
            save(directory/'report.json',row);all_rows.append(row)
            print(cohort,target,row['status'],[(s['verifiers'],s['aggregation'],s['probability']) for s in row.get('probabilities',[]) if s['probability']>0],flush=True)
        # Raw paired reports and normalized votes are retained, not recalculated embeddings.
        from app.decision.vote_normalization import is_abstention,vote_confidence
        for partition in manifest.partitions:
            chosen=next(iter(partition.examples)).split_identity
            for e in partition.examples:
                if e.split_identity!=chosen:continue
                a=next(a for a in e.attempts if a.verifier_name=='semantic')
                r=a.report
                audit.append(dict(cohort=cohort,role=partition.role,example_id=e.example_id,question=e.question,answer=e.answer,
                    reference=e.reference,answer_is_correct=e.answer_is_correct,label_source=e.label_source,
                    label_meaning='semantic frame preservation' if cohort=='semantic' else 'independent arithmetic/source-snapshot answer correctness',
                    report=None if r is None else r.model_dump(mode='json'),abstained=None if r is None else is_abstention(r),
                    vote_confidence=None if r is None else vote_confidence(r),history_snapshot=[dict(verifier_name=s.verifier_name,mean=s.posterior_mean,n=s.observation_count) for s in context.plan.reputation_statistics]))
    for p,digest in preserved.items():
        if hashlib.sha256(Path(p).read_bytes()).hexdigest()!=digest:raise ValueError('source changed')
    save(OUT/'comparison.json',dict(scope='Exploratory development tradeoffs; expected coverage is population-level, not runtime confidence or per-request routing',
        targets=TARGETS,rows=all_rows,preserved_inputs=preserved,environment=environment_versions(),final_payload_access=False,
        producer_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()))
    save(OUT/'semantic-reference-audit.json',audit)

if __name__=='__main__':main()
