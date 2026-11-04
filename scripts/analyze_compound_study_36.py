"""Describe the fixed development plans and infeasibility; never refit or infer.

This analysis cannot create/export a policy or open reserved verifier outcomes.
"""
import json
import random
from collections import Counter
from pathlib import Path
from app.game.offline.compound import Study,Training,build_contract,metrics,source_hashes
from app.game.offline.calibration import MeasurementSetup
from app.game.component_execution import enumerate_component_strategies


def main():
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,default=Path('artifacts/compound-study-36-v1/analysis'))
    args=parser.parse_args()
    root=Path('artifacts/compound-study-36-v1')
    read=lambda path:json.loads(Path(path).read_text(encoding='utf-8'))
    result=read(root/'candidate/infeasible.json')
    training=Training(study=Study.model_validate(read(root/'preparation/study.json')),
        setup=MeasurementSetup.model_validate(read(root/'preparation/setup.json')),
        history=read(root/'history/joint.json'),development=read(root/'development/joint.json'))
    contract=build_contract(training)
    assert contract.compatibility_id==result['matrix']['compatibility_id']
    strategies=enumerate_component_strategies(contract);lookup={s.strategy_id:s for s in strategies}
    from app.game.offline.attacks import Attack
    attacks={Attack.model_validate(a).attack_id:a for a in read(root/'attacks.json')}
    examples={e['example_id']:e for e in read(root/'examples.json')['development']}
    fixed=min(strategies,key=lambda s:(max(result['matrix']['values'][result['matrix']['strategy_ids'].index(s.strategy_id)]),s.estimated_cost,s.strategy_id))
    summary={};diagnostics=[]
    for attack_id in result['matrix']['attack_ids']:
        rows=[r for r in result['outcomes'] if r['strategy_id']==fixed.strategy_id and r['attack_id']==attack_id]
        components={}
        for cid in ('base_fact','derived_sum'):
            local=[]
            for row in rows:
                c=next(c for c in row['components'] if c['component_id']==cid)
                correct=examples[row['example_id']]['label'][cid];status=c['public_status']
                loss=training.study.loss.uncertain if status=='uncertain' else (0. if (status=='passed')==correct else
                    training.study.loss.false_reject if correct else training.study.loss.false_accept)
                obligation=next(o for o in contract.obligations if o.component_id==cid)
                name='evidence' if cid=='base_fact' else 'rule'
                local.append(dict(public_status=status,answer_is_correct=correct,validation_loss=loss,
                    estimated_cost=dict(obligation.context.attempt_costs)[name]))
            components[cid]=dict(**metrics(local),statuses=dict(Counter(x['public_status'] for x in local)))
        groups=sorted({r['group_id'] for r in rows});by_group={g:[r for r in rows if r['group_id']==g] for g in groups}
        rng=random.Random(1102);samples=[]
        for _ in range(1000):
            selected=[r for _ in groups for r in by_group[rng.choice(groups)]]
            samples.append(metrics(selected))
        interval={key:[sorted(x[key] for x in samples)[24],sorted(x[key] for x in samples)[974]] for key in ('coverage','decision_loss')}
        summary[attacks[attack_id]['kind']]=dict(whole=metrics(rows),statuses=dict(Counter(r['public_status'] for r in rows)),
            components=components,variants={v:metrics([r for r in rows if r['variant']==v]) for v in ('correct','wrong_math','wrong_base','both_wrong')},
            entity_groups=len(groups),entity_cluster_bootstrap_95_percentile=interval)
        if attacks[attack_id]['kind']=='clean':
            bundle=dict(training.development.bundles)['base_fact']
            for row in rows:
                if row['public_status']!='uncertain':continue
                e=examples[row['example_id']]
                a=next(a for a in bundle.attempts if a.example_id==row['example_id']+'-base_fact' and a.candidate=='evidence')
                report=a.attempt.report;m=report.metadata;component=row['components'][0]
                diagnostics.append(dict(entity=row['group_id'],variant=e['variant'],question=e['question'],answer=e['answer'],
                    whole_status=row['public_status'],fact_status=component['public_status'],math_status=row['components'][1]['public_status'],
                    evidence_score=report.score,decision=m.get('decision'),nli_label=m.get('nli_label'),score_meaning=m.get('score_meaning'),
                    contradicting_row_labels=[r.get('nli_label') for r in m.get('contradicting',[])],
                    component_reasons=component['reasons'],achieved=component['achieved'],
                    contributors=sum(v['included'] for v in component['detail']['votes']),
                    raw_evidence_report=report.model_dump(mode='json'),source_attempt_id=a.attempt_id))
    out=args.output;out.mkdir(exist_ok=False)
    (out/'unfitted-contract.json').write_text(contract.model_dump_json(indent=2),encoding='utf-8')
    for o in contract.obligations:
        (out/('unfitted-context-'+o.component_id+'.json')).write_text(o.context.model_dump_json(indent=2),encoding='utf-8')
    values=dict(status='infeasible',deployable_policy=False,solver=result['solution'],matrix_id=result['solution']['matrix_id'],
        contract_id=contract.compatibility_id,strategies=[dict(strategy_id=s.strategy_id,team=s.verifiers,
            estimated_cost=s.estimated_cost,**s.model_dump(mode='json')) for s in strategies],
        development_best_fixed_strategy_id=fixed.strategy_id,coverage_target=.9,
        fixed_baseline_meets_coverage_target=False,
        maximum_clean_coverage=max(q for _,q in result['matrix']['clean_coverage']['strategy_coverage']),
        strategy_probabilities=None,any_mixture_cannot_improve_equal_coverage=True,
        attack_metrics=summary,qualified_rejection_diagnostics=diagnostics,
        history_only_weights={o.component_id:[dict(name=s.verifier_name,alpha=s.alpha,beta=s.beta,observations=s.observation_count,posterior_mean=s.posterior_mean) for s in o.context.plan.reputation_statistics] for o in contract.obligations},
        estimated_call_cost_ms=dict(contract.obligations[0].context.attempt_costs),budget_ms=contract.budget,
        actual_full_resource_manifest_id=contract.actual_resources.manifest_id,
        projected_component_resource_manifest_id=contract.obligations[0].contract.resource_manifest.manifest_id,
        singleton_baselines='infeasible: missing one required component',triple='not evaluated: third useful verifier not included',
        greedy='not defined as comparable component executor',empirical_team_selection_advantage=False,
        reserved_verifier_outcomes_collected=False,actual_attempts=192,unused_attempt_allowance=96,
        source_hashes=source_hashes(),bootstrap_seed=1102,bootstrap_replicates=1000,
        limitations='12 source-known development clusters; bootstrap intervals do not change the fixed empirical90% gate or prove generalization.')
    (out/'results.json').write_text(json.dumps(values,indent=2),encoding='utf-8')
    print(json.dumps(dict(status='infeasible',clean=summary['clean']['whole'],budget_ms=contract.budget,
        context_resource_id=values['projected_component_resource_manifest_id']),indent=2))


if __name__=='__main__':main()
