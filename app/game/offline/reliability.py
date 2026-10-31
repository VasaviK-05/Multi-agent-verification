"""Reliability-first fit over finalized development outcomes, with no test payloads."""
from app.game.models import PlanningContext, PayoffMatrix, canonical_json
from app.game.reliability_contract import ReliabilityFirst
from app.game.offline.coverage import prepare_clean_coverage
from app.game.offline.evaluation import summarize
from app.game.policy import build_policy


def prepare_reliability_first(context,manifest,contract,attacks,evaluation,*,minimum=.90,epsilon=1e-8,cost_tolerance=1e-8):
    if contract.contributor_version!='informative_history_influence_v1':
        raise ValueError('reliability-first requires opt-in informative contributor contract')
    covered,matrix=prepare_clean_coverage(context,manifest,contract,attacks,evaluation,minimum=minimum)
    values=[]
    for sid in matrix.strategy_ids:
        row=[]
        for attack in matrix.attack_ids:
            metrics=summarize(tuple((o,1.) for o in evaluation.outcomes if o.strategy_id==sid and o.attack_id==attack),context.loss_configuration)
            row.append(metrics.validation_loss(context.loss_configuration))
        values.append(tuple(row))
    objective=ReliabilityFirst(version='validation_then_attempt_cost_v1',epsilon=epsilon,cost_tolerance=cost_tolerance,
        parent_matrix_id=matrix.matrix_id,validation_values=tuple(values))
    bound=PlanningContext(**{**covered.model_dump(),'reliability_first_json':canonical_json(objective.model_dump(mode='json'))})
    return bound,PayoffMatrix(**{**matrix.model_dump(),'compatibility_id':bound.compatibility_id,'reliability_first':objective})


def fit_reliability_first(context,manifest,contract,attacks,evaluation,*,minimum=.90,epsilon=1e-8,tolerance=1e-8,cost_tolerance=1e-8):
    bound,matrix=prepare_reliability_first(context,manifest,contract,attacks,evaluation,minimum=minimum,epsilon=epsilon,cost_tolerance=cost_tolerance)
    return bound,build_policy(bound,matrix,tolerance=tolerance)
