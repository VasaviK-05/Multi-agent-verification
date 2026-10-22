"""Full-team public decisions with frozen reputation and no verifier dispatch."""

from typing import Literal
from pydantic import Field, StrictFloat, model_validator

from app.decision.coverage import factual_capabilities
from app.decision.decision_engine import DecisionEngine
from app.decision.early_termination import AdaptiveEarlyTermination, _is_structural_rule
from app.game.dependencies import FrozenModel, identifier
from app.game.decision_inputs import FrozenReputationSnapshot
from app.game.models import PlanningContext, Strategy
from app.game.strategies import enumerate_strategies
from app.game.offline.attacks import AttackAudit, enumerate_attacks, transform
from app.game.offline.records import Example


class ReplayContract(FrozenModel):
    version: Literal["offline_public_decision_v1"]
    coverage_version: Literal["factual_output_contract_v1"]
    contributor_version: Literal["baseline_log_odds_active_group_v1"]
    threshold: StrictFloat = Field(ge=0, le=1)
    failure_contract: Literal["all_selected_returned", "allow_failed_if_covered"]
    execution_configuration_id: str
    history_prior_alpha: StrictFloat = Field(gt=0)
    history_prior_beta: StrictFloat = Field(gt=0)

    @model_validator(mode="after")
    def check(self):
        identifier(self.execution_configuration_id)
        return self


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
    rows = [a.report for a in attempts if a.report is not None]
    detail = DecisionEngine(threshold=contract.threshold).decide_detailed(rows, domain=example.domain,
        snapshot=FrozenReputationSnapshot.from_planning_context(context), aggregation=strategy.aggregation,
        team=strategy.verifiers, validation_id=example.validation_id)
    if strategy.aggregation == "reputation_weighted":
        contributors = AdaptiveEarlyTermination.contributor_count(detail, rows)
    else:
        # Active directional reports count, including members of the zero-reliability fallback.
        contributors = sum(v.included and not _is_structural_rule(r) for v, r in zip(detail.votes, rows))
    required = tuple(sorted(set(context.plan.requirements.requirements + context.plan.requirements.unsupported)))
    achieved = tuple(sorted(set().union(*(factual_capabilities(r) for r in rows))))
    unresolved = tuple(r for r in required if r not in achieved)
    reasons = []
    if contributors < context.minimum_participant_count:
        reasons.append("minimum_contributors")
    if unresolved:
        reasons.append("missing_achieved_coverage")
    if not context.plan.requirements.requirements_known or context.plan.requirements.status != "known":
        reasons.append("requirements_unresolved")
    if contract.failure_contract == "all_selected_returned" and any(a.report is None for a in attempts):
        reasons.append("selected_execution_incomplete")
    return ReplayOutcome(example_id=example.example_id, validation_id=example.validation_id,
        strategy_id=strategy.strategy_id, attack_id=attack.attack_id, answer_is_correct=example.answer_is_correct,
        public_status="uncertain" if reasons else detail.status, numerical_status=detail.status,
        numerical_score=detail.raw_score, contributors=contributors, required=required, achieved=achieved,
        unresolved=unresolved, reasons=tuple(reasons), execution_states=tuple((a.verifier_name, a.state) for a in attempts),
        estimated_attempt_cost=strategy.estimated_cost, audit=tuple(audits), decision_json=canonical_json(detail.to_dict()))
