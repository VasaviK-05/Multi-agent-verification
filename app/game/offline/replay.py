"""Full-team public decisions with frozen reputation and no verifier dispatch."""

from app.game.dependencies import FrozenModel
from app.game.models import PlanningContext, Strategy
from app.game.strategies import enumerate_strategies
from app.game.offline.attacks import AttackAudit, enumerate_attacks, transform
from app.game.offline.records import Example


from app.game.execution_contract import ExecutionContract as ReplayContract
from app.game.finalization import finalize_decision


class ReplayOutcome(FrozenModel):
    example_id: str
    validation_id: str
    strategy_id: str
    attack_id: str
    answer_is_correct: bool
    public_status: str
    numerical_status: str
    numerical_score: float
    contributors: int
    required: tuple[str, ...]
    achieved: tuple[str, ...]
    unresolved: tuple[str, ...]
    reasons: tuple[str, ...]
    execution_states: tuple[tuple[str, str], ...]
    estimated_attempt_cost: float
    audit: tuple[AttackAudit, ...]
    decision_json: str


def category_id(context):
    data = context.model_dump()
    data["offline_evaluation_id"] = None
    data["execution_contract_json"] = None
    return PlanningContext(**data).compatibility_id


def replay(context, strategy, attack, specification, contract, example):
    from app.game.models import canonical_json
    context = PlanningContext.model_validate(context)
    strategy = Strategy.model_validate(strategy)
    example = Example.model_validate(example)
    contract = ReplayContract.model_validate(contract)
    if strategy not in enumerate_strategies(context).strategies:
        raise ValueError("strategy is not an exact feasible team/aggregation/cost definition")
    if attack not in enumerate_attacks(context.dependencies, specification):
        raise ValueError("attack differs from full captured registry")
    if (example.domain != context.plan.domain or example.planning_category != category_id(context)
        or example.execution_configuration_id != contract.execution_configuration_id
        or bool(example.reference and example.reference.strip()) != context.plan.reference_available):
        raise ValueError("incompatible planning category or execution provenance")
    lookup = {a.verifier_name: a for a in example.attempts}
    candidate_names = {c.verifier_name for c in context.plan.candidates}
    if set(lookup) != candidate_names:
        raise ValueError("recordings must declare every captured candidate outcome")
    if any(a.state == "missing" for a in example.attempts):
        raise ValueError("missing recording: evaluation input incomplete")
    attempts, audits = [], []
    for name in strategy.verifiers:
        result, audit = transform(lookup[name], attack, specification)
        attempts.append(result); audits.append(audit)
    finalized = finalize_decision(context, strategy, contract,
        [a.report for a in attempts if a.report is not None],
        tuple((a.verifier_name, a.state) for a in attempts), example.validation_id)
    detail = finalized.detail
    return ReplayOutcome(example_id=example.example_id, validation_id=example.validation_id,
        strategy_id=strategy.strategy_id, attack_id=attack.attack_id, answer_is_correct=example.answer_is_correct,
        public_status=finalized.public_status, numerical_status=detail.status,
        numerical_score=detail.raw_score, contributors=finalized.contributors, required=finalized.required, achieved=finalized.achieved,
        unresolved=finalized.unresolved, reasons=finalized.reasons, execution_states=tuple((a.verifier_name, a.state) for a in attempts),
        estimated_attempt_cost=strategy.estimated_cost, audit=tuple(audits), decision_json=canonical_json(detail.to_dict()))
