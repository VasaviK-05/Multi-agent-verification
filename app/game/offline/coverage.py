"""Add a clean-development coverage obligation to an existing replay evaluation."""
from app.game.models import PlanningContext, PayoffMatrix, canonical_json, content_id
from app.game.coverage_contract import CleanCoverageConstraint
from app.game.offline.evaluation import Evaluation, _inputs, summarize
from app.game.offline.attacks import enumerate_attacks
from app.game.policy import build_policy
from app.game.offline.records import TrainingManifest
from app.game.offline.replay import replay
from app.game.strategies import enumerate_strategies


def prepare_clean_coverage(context,manifest,contract,attacks,evaluation,*,minimum):
    """Reuse immutable finalized development outcomes; never accept caller-supplied Q.

    The public replay producer supplies outcomes, as it supplies the original
    payoffs. Check exact axes, example identities/truth and all recomputed cells
    before deriving Q. No labels are used to refit history or select exclusions.
    """
    # This fitting entry point cannot represent held-out outcomes.
    manifest=TrainingManifest.model_validate(manifest)
    context,manifest,contract,attacks=_inputs(context,manifest,contract,attacks)
    if context.clean_coverage_json is not None or context.pooling_contract_json is not None:
        raise ValueError('coverage variant requires an original unpooled, unconstrained context')
    evaluation=Evaluation.model_validate(evaluation)
    if (evaluation.role!='development' or evaluation.manifest_id!=manifest.manifest_id
        or evaluation.compatibility_id!=context.compatibility_id or evaluation.matrix.compatibility_id!=context.compatibility_id
        or evaluation.contract!=contract or evaluation.attacks!=attacks or evaluation.matrix.clean_coverage is not None):
        raise ValueError('coverage source must be the exact original development evaluation')
    actions=enumerate_attacks(context.dependencies,attacks)
    strategies={s.strategy_id:s for s in enumerate_strategies(context).strategies}
    if (set(evaluation.matrix.strategy_ids)!=set(strategies)
        or evaluation.matrix.strategy_definitions!=tuple(strategies[s] for s in evaluation.matrix.strategy_ids)):
        raise ValueError('coverage source must contain every exact feasible strategy definition')
    if evaluation.matrix.attack_ids!=tuple(a.attack_id for a in actions):raise ValueError('coverage source attack axes differ')
    expected={e.example_id:e for e in manifest.partition('development').examples}
    qs=[];keys=set()
    for o in evaluation.outcomes:
        key=(o.strategy_id,o.attack_id,o.example_id)
        if key in keys:raise ValueError('duplicate coverage source outcome')
        keys.add(key)
        e=expected.get(o.example_id)
        if (e is None or e.validation_id!=o.validation_id or e.answer_is_correct!=o.answer_is_correct
            or o.strategy_id not in evaluation.matrix.strategy_ids or o.attack_id not in evaluation.matrix.attack_ids):
            raise ValueError('coverage source example/strategy/attack identity mismatch')
    if len(keys)!=len(expected)*len(evaluation.matrix.strategy_ids)*len(actions):
        raise ValueError('incomplete coverage source outcomes')
    for i,sid in enumerate(evaluation.matrix.strategy_ids):
        for j,attack in enumerate(actions):
            cell=tuple((o,1.) for o in evaluation.outcomes if o.strategy_id==sid and o.attack_id==attack.attack_id)
            if j==0:
                # A matching mean loss alone cannot authenticate finalized Q:
                # errors, abstentions or costs could have been altered together.
                strategy=evaluation.matrix.strategy_definitions[i]
                actual={e.example_id:replay(context,strategy,attack,attacks,contract,e) for e in expected.values()}
                if any(actual[o.example_id]!=o for o,w in cell):
                    raise ValueError('cached clean coverage differs from finalized source-record replay')
            metrics=summarize(cell,context.loss_configuration)
            if abs(metrics.mean_loss-evaluation.matrix.values[i][j])>1e-12:
                raise ValueError('coverage source outcomes differ from original payoff matrix')
            if j==0:qs.append((sid,metrics.decision_coverage))
    constraint=CleanCoverageConstraint(version='finalized_clean_development_coverage_v1',minimum=minimum,
        strategy_coverage=tuple(qs),parent_matrix_id=evaluation.matrix.matrix_id,
        training_binding_id=context.offline_evaluation_id,source_evaluation_id=content_id(evaluation.model_dump(mode='json')))
    bound=PlanningContext(**{**context.model_dump(),'clean_coverage_json':canonical_json(constraint.model_dump(mode='json'))})
    matrix=PayoffMatrix(**{**evaluation.matrix.model_dump(),'compatibility_id':bound.compatibility_id,'clean_coverage':constraint})
    return bound,matrix


def fit_clean_coverage(context,manifest,contract,attacks,evaluation,*,minimum,tolerance=1e-8):
    bound,matrix=prepare_clean_coverage(context,manifest,contract,attacks,evaluation,minimum=minimum)
    return bound,build_policy(bound,matrix,tolerance=tolerance)
