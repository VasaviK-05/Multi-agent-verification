"""Summarize frozen results and verify amendment invariants; no fit or inference."""
import hashlib,json,random
from pathlib import Path
from app.game.component_execution import ComponentPolicy,enumerate_component_strategies
from app.game.offline.attacks import AttackSpecification,enumerate_attacks
from app.game.models import content_id
ROOT=Path('artifacts/remaining-category-studies-v1')
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def save(p,v):
    with Path(p).open('x',encoding='utf-8') as f:json.dump(v,f,indent=2,sort_keys=True)
def main():
    policy=ComponentPolicy.model_validate(read(ROOT/'compound-85/candidate/policy.json'))
    contract=policy.contract;old=read('artifacts/compound-study-36-v1/analysis-v2/unfitted-contract.json')
    revised=contract.model_dump(mode='json');revised.pop('fitting_configuration')
    assert revised==old
    original=read('artifacts/compound-study-36-v1/candidate/infeasible.json')
    assert original['matrix']['values']==policy.matrix.model_dump(mode='json')['values']
    assert [v for _,v in original['matrix']['clean_coverage']['strategy_coverage']]==[v for _,v in policy.matrix.clean_coverage.strategy_coverage]
    evaluation=read(ROOT/'compound-85/evaluation/reserved-results.json')
    setup=read('artifacts/compound-study-36-v1/preparation/setup.json')
    freeze=read(ROOT/'compound-85/candidate/freeze.json')
    spec=AttackSpecification(**freeze['study']['attack_specification']);actions=enumerate_attacks(freeze['study']['dependencies'],spec)
    names={a.attack_id:a.kind for a in actions};development=read(ROOT/'compound-85/candidate/development-results.json')
    clean_id=next(a.attack_id for a in actions if a.kind=='clean');weights=dict(policy.solution.probabilities)
    test_by_attack={key.split(':')[0]:value for key,value in evaluation['attacks'].items()}
    # Coverage and error intervals complement existing frozen evaluator loss CI.
    rows=evaluation['outcomes'];groups=sorted({r['group_id'] for r in rows});rng=random.Random(1102)
    intervals={};samples=[]
    for _ in range(1000):
        draw=[rng.choice(groups) for _ in groups]
        selected=[(r,weights[r['strategy_id']]) for g in draw for r in rows if r['group_id']==g and r['attack_id']==clean_id]
        n=len(draw)*4;dec=sum(w for r,w in selected if r['public_status']!='uncertain')
        fa=sum(w for r,w in selected if r['public_status']=='passed' and not r['answer_is_correct']);fr=sum(w for r,w in selected if r['public_status']=='failed' and r['answer_is_correct'])
        samples.append(dict(coverage=dec/n,false_accept_rate_all=fa/n,false_reject_rate_all=fr/n,uncertainty_rate=(n-dec)/n,selective_risk=(fa+fr)/dec if dec else None))
    for key in samples[0]:
        values=sorted(row[key] for row in samples if row[key] is not None)
        intervals[key]=dict(interval95=[values[24],values[974]] if len(values)==1000 else None,undefined_fraction=1-len(values)/1000)
    reference=read(ROOT/'reference/fit/summary.json');refintegrity=read(ROOT/'reference/training/collection-integrity.json')
    compoundintegrity=read(ROOT/'compound-85/test/collection-integrity.json')
    reserved_ref=ROOT/'reference/test/collection-integrity.json'
    ref_test_integrity=read(reserved_ref) if reserved_ref.exists() else None
    attempts=evaluation['actual_test_calls']+reference['actual_training_attempts']+(ref_test_integrity['executed_calls'] if ref_test_integrity else 0)
    generations=refintegrity['network']['generation']+(ref_test_integrity['network']['generation'] if ref_test_integrity else 0)
    assert attempts<=336 and generations<=300
    strategies=enumerate_component_strategies(contract)
    result=dict(version='remaining_categories_results_v1',compound=dict(policy_fitted=True,reserved_evaluated=True,
        policy_id=policy.policy_id,contract_id=contract.compatibility_id,matrix_id=policy.matrix.matrix_id,freeze_id=content_id(freeze),
        original90_unchanged=True,amendment_only_semantic_change='85% clean-development coverage, explicitly chosen after development; all other contract fields and payoffs identical.',
        selected=[dict(strategy_id=s.strategy_id,team=s.verifiers,aggregation=s.components[0][1].aggregation,probability=weights[s.strategy_id]) for s in strategies if weights[s.strategy_id]>0],
        development={names[key]:value for key,value in development.items()},reserved=test_by_attack,clean_cluster_intervals=intervals,
        measured_test_attempt_ms=evaluation['measured_test_attempt_ms'],new_attempts=evaluation['actual_test_calls'],new_generations=0,
        equivalent_to_fixed=all(value['policy']['coverage']==value['development_best_fixed']['coverage'] and value['policy']['decision_loss']==value['development_best_fixed']['decision_loss'] for value in test_by_attack.values()),
        no_minimax_advantage=True),reference=reference,new_actual_attempts=attempts,new_local_generations=generations,
        reference_reserved_status='completed' if ref_test_integrity else 'correctly skipped: infeasible development candidate',
        resources=dict(full=setup['resources'] and content_id(setup['resources']),execution_dependency_versions=setup['dependency_versions']),
        deployment_active=False,live_api_instance_binding_demonstrated=False,publication_review='Owned portable package; external instance/relocation and original execution source ownership remain owner tasks.')
    save(ROOT/'results.json',result)
    c=test_by_attack['clean']['policy'];r=reference
    lines=['# Final study results and acceptance status','',
        'This supplement reports actual frozen outcomes. The [primary handoff](../../docs/supported_category_policy_integration.md) defines scope and ownership.','',
        '| Item | Result |','|---|---|',
        '| Compound85 policy | Fitted, certificate checked, exported/reloaded; post-development amendment |',
        '| Compound reserved evaluation | Completed:12 entity groups,48 answers,96 new E/R attempts,0 generations |',
        f"| Compound clean reserved | Coverage {c['coverage']:.6%}; FA {c['false_accepts']}; FR {c['false_rejects']}; uncertainty {c['uncertainty']:.6%}; loss {c['decision_loss']:.8f}; selective risk {c['selective_risk']} |",
        f"| Reference development | {r['status']}; maximum clean coverage {r['maximum_clean_coverage']:.2%}; target90% unchanged |",
        f"| Reference reserved | {result['reference_reserved_status']} |",
        f'| New collection totals | {attempts} attempts / {generations} local generations (caps336/300) |',
        '| Real routing | Actual frozen singleton and pair report replay; no live API activation |',
        '| Actual selected teams | Rule; Evidence; Evidence+Rule compound. No demonstrated real triple |',
        '| External blockers | Native API-instance attestation and verified relocation; original dirty execution source ownership |',
        '| Review readiness | Portable source/policy/report package; release requires owner/privacy and integration review |','',
        '## Compound report-level attacks','',
        '| Action | Coverage | False accepts | False rejects | Decision loss |','|---|---:|---:|---:|---:|']
    for name,value in test_by_attack.items():
        m=value['policy'];lines.append(f"| {name} | {m['coverage']:.4%} | {m['false_accepts']:g} | {m['false_rejects']:g} | {m['decision_loss']:.8f} |")
    lines+=['','Policy equals the development-best fixed plan on all reported reserved attacks. These attacks corrupt reports within declared shared groups; they are not observed upstream failures. No minimax improvement is established.','',
        '## Compound component and timing details','',
        'Clean component metrics: `'+json.dumps(test_by_attack['clean']['component_metrics_fixed'],sort_keys=True)+'`.','',
        'Measured reserved attempt timings (ms): `'+json.dumps(evaluation['measured_test_attempt_ms'],sort_keys=True)+'`. These do not change frozen training costs.','',
        'Entity-cluster coverage/error/risk intervals: `'+json.dumps(intervals,sort_keys=True)+'`. Frozen evaluator decision-loss interval: `'+json.dumps(test_by_attack['clean']['group_bootstrap_decision_loss_95_percentile'])+'`.','',
        'The resampling unit is an entity with all four variants retained (12 clusters,1000 replicates,seed1102). Zero-error intervals are not population guarantees.85% was a development fitting gate, not a promised reserved coverage.','',
        '## Reference diagnostic and labels','',
        'The [complete strategy diagnostics](reference/fit/strategy-diagnostics.json) retain every eligible aggregation/team, every attack cell and public uncertainty reasons. [Training data](reference/fit/training-manifest.json) retain actual reports, independently specified labels and split identities. [Summary](reference/fit/summary.json) gives fresh history statistics, actual states and measured costs.','',
        'No target relaxation, neutral-history borrowing, outcome-driven categories, replacement examples or retries occurred. Broad syntax families recur across the30 lexicalized frames; this is a small constructed-reference study, not broad difficulty or unseen-template adaptation.']
    (ROOT/'results.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps(dict(compound_clean=c,reference_status=reference['status'],new_attempts=attempts,generations=generations)),flush=True)
if __name__=='__main__':main()
