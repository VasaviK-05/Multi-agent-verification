"""Offline paired comparison. Reads frozen recordings; never dispatches inference.
Run from isolated checkout: python -m scripts.evaluate_flexible_teams --source <original>/build/multitask-policy42 --output <new directory>
"""
import argparse
from collections import Counter
from pathlib import Path
import hashlib
import json
from app.game.models import PlanningContext
from app.game.execution_contract import ExecutionContract, TeamRequirements
from app.game.offline.records import TrainingManifest
from app.game.offline.attacks import AttackSpecification, enumerate_attacks
from app.game.offline.evaluation import bind_evaluation, construct_payoffs, summarize
from app.game.offline.reliability import prepare_reliability_first
from app.game.strategies import enumerate_strategies
from app.game.solver import solve_minimax
from app.game.policy import build_policy


def read(p): return json.loads(p.read_text(encoding='utf-8'))
def save(p,x): p.write_text(json.dumps(x,indent=2,sort_keys=True)+'\n',encoding='utf-8')
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()


def describe(metrics, loss):
    return {**metrics.model_dump(mode='json'),
            'decision_loss': metrics.validation_loss(loss),
            'uncertainty_rate': metrics.uncertainty_rate,
            'false_accept_rate': metrics.false_accept / metrics.examples,
            'false_reject_rate': metrics.false_reject / metrics.examples}



def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=False)
    hashes={};results=[];baseline_checks=[]
    for cohort in ('arithmetic','factual','semantic'):
        directory=args.source/cohort
        paths=[directory/n for n in ('source-context.json','training-manifest.json','contract.json','policy-input.json','development-evaluation.json')]
        hashes.update({str(p.resolve()):digest(p) for p in paths})
        context=PlanningContext.model_validate(read(paths[0]))
        manifest=TrainingManifest.model_validate(read(paths[1]))
        original=ExecutionContract.model_validate(read(paths[2]))
        attacks=AttackSpecification.model_validate(read(paths[3])['attacks'])
        # Strict original binding validates independent history, task identity and all
        # recorded resource fingerprints before changing only aggregation minima.
        bind_evaluation(context,manifest,original,attacks)
        for minimum in (2,1):
            target=args.output/f'{cohort}-minimum-{minimum}';target.mkdir()
            contract=ExecutionContract(**{**original.model_dump(),'team_requirements':TeamRequirements(minimum_selected=minimum,minimum_informative=minimum)})
            base=PlanningContext(**{**context.model_dump(),'execution_contract_json':None,'offline_evaluation_id':None,'clean_coverage_json':None,'reliability_first_json':None})
            bound=bind_evaluation(base,manifest,contract,attacks)
            enumeration=enumerate_strategies(bound)
            save(target/'enumeration.json',enumeration.model_dump(mode='json'))
            evaluation=construct_payoffs(bound,manifest,contract,attacks)
            if minimum == 2:
                historical = read(paths[4])['matrix']
                if historical['strategy_ids'] != list(evaluation.matrix.strategy_ids) or historical['attack_ids'] != list(evaluation.matrix.attack_ids):
                    raise ValueError('historical minimum-two strategy/attack axes changed')
                difference = max(abs(a-b) for old,new in zip(historical['values'],evaluation.matrix.values) for a,b in zip(old,new))
                if difference > 1e-12:
                    raise ValueError('historical minimum-two payoff values changed')
                baseline_checks.append(dict(cohort=cohort,axes_identical=True,maximum_payoff_difference=difference))
            fitted,matrix=prepare_reliability_first(bound,manifest,contract,attacks,evaluation,minimum=.90,epsilon=1e-8,cost_tolerance=1e-8)
            solution=solve_minimax(matrix,tolerance=1e-8)
            save(target/'context.json',fitted.model_dump(mode='json'));save(target/'contract.json',contract.model_dump(mode='json'))
            save(target/'matrix.json',matrix.model_dump(mode='json'));save(target/'solution.json',solution.model_dump(mode='json'))
            actions=enumerate_attacks(bound.dependencies,attacks)
            rows=[]
            for s in enumeration.strategies:
                cells={}
                for a in actions:
                    outcomes=[o for o in evaluation.outcomes if o.strategy_id==s.strategy_id and o.attack_id==a.attack_id]
                    metrics=summarize(tuple((o,1.) for o in outcomes),bound.loss_configuration)
                    reasons=Counter(reason for o in outcomes for reason in o.reasons)
                    cells[a.kind+':'+a.attack_id]=dict(metrics=describe(metrics,bound.loss_configuration),decision_loss=metrics.validation_loss(bound.loss_configuration),uncertainty_reasons=dict(reasons))
                rows.append(dict(strategy=s.model_dump(mode='json'),attacks=cells))
            save(target/'strategy-diagnostics.json',rows)
            summary=dict(cohort=cohort,minimum=minimum,status=solution.status,strategies=len(enumeration.strategies),team_sizes=sorted({len(s.verifiers) for s in enumeration.strategies}),held_out='Not evaluated: reserved final examples have no recorded verifier outputs; no new inference authorized.',maximum_clean_coverage=max(m.decision_coverage for sid,aid,m in evaluation.metrics if aid==actions[0].attack_id))
            if solution.status=='optimal':
                policy=build_policy(fitted,matrix,tolerance=1e-8);save(target/'policy.json',policy.model_dump(mode='json'))
                probabilities=dict(policy.solution.probabilities)
                summary['selection_probability_by_team_size']={str(size):sum(probabilities[s.strategy_id] for s in policy.strategies if len(s.verifiers)==size) for size in range(1,5)}
                summary['selected_strategies']=[dict(team=s.verifiers,aggregation=s.aggregation,probability=probabilities[s.strategy_id]) for s in policy.strategies if probabilities[s.strategy_id]>0]
                summary['development_attack_metrics']={a.kind+':'+a.attack_id:describe(summarize(tuple((o,probabilities[o.strategy_id]) for o in evaluation.outcomes if o.attack_id==a.attack_id),bound.loss_configuration),bound.loss_configuration) for a in actions}
            results.append(summary);save(target/'summary.json',summary)
            print(cohort,minimum,solution.status,'max coverage',summary['maximum_clean_coverage'],flush=True)
    if any(digest(Path(p))!=h for p,h in hashes.items()): raise ValueError('historical input bytes changed')
    save(args.output/'input-hashes.json',hashes)
    save(args.output/'baseline-reproduction.json',baseline_checks)
    save(args.output/'comparison.json',dict(scope='Development diagnostics only; fixed original objective, attacks, budget, history, costs, threshold and 0.90 clean coverage target. Costs are historical estimates, not newly measured runtime.',results=results))

if __name__=='__main__': main()
