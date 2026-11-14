"""Reuse finalized cells only when the sole planning change is a hard budget."""

from app.game.models import PayoffMatrix
from app.game.offline.evaluation import Evaluation, _inputs
from app.game.strategies import enumerate_strategies

def restrict_budget_evaluation(
    source_context,
    source_manifest,
    target_context,
    target_manifest,
    contract,
    attacks,
    evaluation,
):
    """Reuse Development cells only for a budget-only planning change."""
    from app.game.task_conditioning import TaskSnapshotBinding

    source_context, source_manifest, contract, attacks = _inputs(
        source_context, source_manifest, contract, attacks
    )
    target_context, target_manifest, _, _ = _inputs(
        target_context, target_manifest, contract, attacks
    )

    excluded = {
        "budget",
        "task_conditioning_json",
        "offline_evaluation_id",
        "execution_contract_json",
    }

    if (
        source_context.model_dump(exclude=excluded)
        != target_context.model_dump(exclude=excluded)
    ):
        raise ValueError(
            "budget cache requires identical decision/planning semantics and costs"
        )

    # Both contexts must have valid bindings, independently checked by _inputs.
    source_binding = source_context.task_conditioning_json
    target_binding = target_context.task_conditioning_json

    if (source_binding is None) != (target_binding is None):
        raise ValueError("budget cache task-conditioning binding mismatch")

    if source_binding is not None:
        source_task = TaskSnapshotBinding.model_validate_json(source_binding)
        target_task = TaskSnapshotBinding.model_validate_json(target_binding)

        # The history digest may change because planning_category is
        # budget-dependent. The task and underlying history source may not.
        if (
            source_task.version != target_task.version
            or source_task.identity != target_task.identity
            or source_task.history_dataset_id != target_task.history_dataset_id
            or source_task.sparse_history != target_task.sparse_history
        ):
            raise ValueError("budget cache task identity or history source differs")

    def raw(manifest):
        data = manifest.model_dump()
        for partition in data["partitions"]:
            for example in partition["examples"]:
                example.pop("planning_category")
        return data

    if raw(source_manifest) != raw(target_manifest):
        raise ValueError("budget cache source recordings/labels differ")

    evaluation = Evaluation.model_validate(evaluation)

    if (
        evaluation.role != "development"
        or evaluation.compatibility_id != source_context.compatibility_id
        or evaluation.manifest_id != source_manifest.manifest_id
        or evaluation.contract != contract
        or evaluation.attacks != attacks
    ):
        raise ValueError("budget cache source identity mismatch")

    strategies = enumerate_strategies(target_context).strategies
    indices = {
        strategy_id: i
        for i, strategy_id in enumerate(evaluation.matrix.strategy_ids)
    }

    if not strategies or any(
        strategy.strategy_id not in indices
        or evaluation.matrix.strategy_definitions[indices[strategy.strategy_id]]
        != strategy
        for strategy in strategies
    ):
        raise ValueError("budget cache lacks exact target strategies")

    ids = tuple(strategy.strategy_id for strategy in strategies)

    matrix = PayoffMatrix(
        strategy_ids=ids,
        strategy_definitions=strategies,
        attack_ids=evaluation.matrix.attack_ids,
        values=tuple(
            evaluation.matrix.values[indices[strategy_id]]
            for strategy_id in ids
        ),
        compatibility_id=target_context.compatibility_id,
    )

    return Evaluation(
        role="development",
        manifest_id=target_manifest.manifest_id,
        compatibility_id=target_context.compatibility_id,
        contract=contract,
        attacks=attacks,
        matrix=matrix,
        outcomes=tuple(
            outcome for outcome in evaluation.outcomes
            if outcome.strategy_id in ids
        ),
        metrics=tuple(
            (strategy_id, attack_id, metric)
            for strategy_id, attack_id, metric in evaluation.metrics
            if strategy_id in ids
        ),
    )
