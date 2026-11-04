"""Explicit scoped-resource evaluation fork; original frozen policy unchanged."""
from app.game.offline.compound import *
def evaluate_scoped(frozen,test,scoped_setup):
    """The only consumer of reserved outcomes; no fitting or new cost/history update."""
    import random
    frozen=FrozenCandidate.model_validate(frozen);verify_code(frozen)
    test=validate_recordings(frozen.study,test,scoped_setup,freeze_id=frozen.freeze_id)
    if test.role!='final_test':raise ValueError('frozen evaluation requires reserved partition')
    study=frozen.study;contract=frozen.policy.contract
    strategies=enumerate_component_strategies(contract)
    attacks=enumerate_attacks(study.dependencies,study.attack_specification)
    result={};all_rows=[]
    probabilities=dict(frozen.policy.solution.probabilities)
    for attack in attacks:
        per_strategy={s.strategy_id:[replay_example(study,contract,s,e,test.bundles,attack)
            for e in examples(study,'final_test')] for s in strategies}
        all_rows.extend(row for rows in per_strategy.values() for row in rows)
        fixed=per_strategy[frozen.best_fixed_strategy_id]
        # Expected policy metrics, NOT resampling a favorable strategy per example.
        by_strategy={sid:metrics(rows) for sid,rows in per_strategy.items()}
        expected={key:sum(probabilities[sid]*value[key] for sid,value in by_strategy.items())
            for key in ('examples','coverage','false_accepts','false_rejects','uncertainty','decision_loss','estimated_cost','mean_loss')}
        decided=expected['examples']*expected['coverage']
        expected['selective_risk']=(expected['false_accepts']+expected['false_rejects'])/decided if decided else None
        component_metrics={}
        labels={e['example_id']:e['label'] for e in examples(study,'final_test')}
        for cid in ('base_fact','derived_sum'):
            values=[]
            for row in fixed:
                c=next(c for c in row['components'] if c['component_id']==cid)
                correct=labels[row['example_id']][cid];status=c['public_status']
                loss=study.loss.uncertain if status=='uncertain' else (0. if (status=='passed')==correct else study.loss.false_reject if correct else study.loss.false_accept)
                values.append(dict(public_status=status,answer_is_correct=correct,validation_loss=loss))
            component_metrics[cid]=metrics(values)
        groups=sorted({r['group_id'] for r in fixed});group_values={}
        for group in groups:
            group_values[group]=sum(probabilities[sid]*sum(r['validation_loss'] for r in rows if r['group_id']==group)/4
                for sid,rows in per_strategy.items())
        rng=random.Random(frozen.bootstrap_seed)
        boot=sorted(sum(group_values[rng.choice(groups)] for _ in groups)/len(groups) for _ in range(frozen.bootstrap_replicates))
        result[attack.kind+':'+attack.attack_id]=dict(policy=expected,development_best_fixed=metrics(fixed),
            component_metrics_fixed=component_metrics,
            variant_metrics_fixed={variant:metrics([r for r in fixed if r['variant']==variant]) for variant in ('correct','wrong_math','wrong_base','both_wrong')},
            group_bootstrap_decision_loss_95_percentile=(boot[24],boot[974]),groups=len(groups),
            bootstrap_limitation=f'Entity clusters;{len(groups)} known-source groups. Degenerate zero-error bootstrap is not proof of zero population risk.')
    return dict(freeze_id=frozen.freeze_id,policy_id=frozen.policy.policy_id,attacks=result,outcomes=all_rows,
        actual_test_calls=sum(a.executed for _,b in test.bundles for a in b.attempts),
        actual_upstream_failures=sum(a.executed and a.attempt.state in {'failed','unavailable'} for _,b in test.bundles for a in b.attempts),
        measured_test_attempt_ms={name:dict(count=len(durations),mean=sum(durations)/len(durations),total=sum(durations))
            for name in ('evidence','rule') if (durations:=[a.duration_ms for _,b in test.bundles for a in b.attempts if a.candidate==name and a.executed])},
        attack_type='simulated report corruption; not upstream failure evidence',
        singleton_baselines='infeasible: neither existing singleton covers both components',
        greedy_baseline='not included: no independently defined comparable component greedy executor',
        distinct_feasible_teams=[['evidence','rule']],strategic_team_selection_advantage_established=False)
