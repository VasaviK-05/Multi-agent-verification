"""Reuse finalized cells only when the sole planning change is a hard budget."""
from app.game.models import PayoffMatrix
from app.game.offline.evaluation import Evaluation, _inputs
from app.game.strategies import enumerate_strategies

def restrict_budget_evaluation(source_context,source_manifest,target_context,target_manifest,contract,attacks,evaluation):
    source_context,source_manifest,contract,attacks=_inputs(source_context,source_manifest,contract,attacks)
    target_context,target_manifest,_,_=_inputs(target_context,target_manifest,contract,attacks)
    excluded={'budget','task_conditioning_json','offline_evaluation_id','execution_contract_json'}
    if source_context.model_dump(exclude=excluded)!=target_context.model_dump(exclude=excluded):
        raise ValueError('budget cache requires identical decision/planning semantics and costs')
    def raw(manifest):
        data=manifest.model_dump()
        for partition in data['partitions']:
            for example in partition['examples']:example.pop('planning_category')
        return data
    if raw(source_manifest)!=raw(target_manifest):raise ValueError('budget cache source recordings/labels differ')
    evaluation=Evaluation.model_validate(evaluation)
    if (evaluation.role!='development' or evaluation.compatibility_id!=source_context.compatibility_id
        or evaluation.manifest_id!=source_manifest.manifest_id or evaluation.contract!=contract or evaluation.attacks!=attacks):
        raise ValueError('budget cache source identity mismatch')
    strategies=enumerate_strategies(target_context).strategies
    indices={s:i for i,s in enumerate(evaluation.matrix.strategy_ids)}
    if not strategies or any(s.strategy_id not in indices or evaluation.matrix.strategy_definitions[indices[s.strategy_id]]!=s for s in strategies):
        raise ValueError('budget cache lacks exact target strategies')
    ids=tuple(s.strategy_id for s in strategies)
    matrix=PayoffMatrix(strategy_ids=ids,strategy_definitions=strategies,attack_ids=evaluation.matrix.attack_ids,
        values=tuple(evaluation.matrix.values[indices[s]] for s in ids),compatibility_id=target_context.compatibility_id)
    return Evaluation(role='development',manifest_id=target_manifest.manifest_id,compatibility_id=target_context.compatibility_id,
        contract=contract,attacks=attacks,matrix=matrix,outcomes=tuple(o for o in evaluation.outcomes if o.strategy_id in ids),
        metrics=tuple((s,a,m) for s,a,m in evaluation.metrics if s in ids))
