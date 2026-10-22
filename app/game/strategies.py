"""Exhaustive expected-coverage planning without constructing verifiers."""

from itertools import combinations
import math

from app.game.models import (AGGREGATIONS, EnumerationResult, Infeasibility,
                             PlanningContext, Strategy, content_id)


def enumerate_strategies(context: PlanningContext) -> EnumerationResult:
    context = PlanningContext.model_validate(context)
    plan = context.plan
    requirements = plan.requirements
    blockers = []
    if context.requirements_missing:
        blockers.append("requirements_missing")
    if requirements.status != "known" or not requirements.requirements_known or not requirements.requirements:
        blockers.append("requirements_" + requirements.status)
    if requirements.unsupported:
        blockers.append("unsupported_requirements")
    exclusions = tuple((c.verifier_name, c.exclusion_reason or "ineligible")
                       for c in plan.candidates if not c.eligible)
    if blockers:
        return EnumerationResult(status="no_feasible_strategy", strategies=(),
                                 rejected=(Infeasibility(verifiers=(), reasons=tuple(blockers)),),
                                 exclusions=exclusions)
    candidates = sorted((c for c in plan.candidates if c.eligible and c.registered),
                        key=lambda c: c.verifier_name)
    strategies, rejected = [], []
    costs = dict(context.attempt_costs)
    for size in range(1, len(candidates) + 1):
        for team in combinations(candidates, size):
            names = tuple(c.verifier_name for c in team)
            try:
                cost = math.fsum(costs[name] for name in names)
            except OverflowError:
                cost = math.inf  # A finite budget cannot admit this team.
            covered = {capability for c in team for capability in c.expected_capabilities}
            reasons = []
            if size < context.minimum_participant_count:
                reasons.append("minimum_participant_count")
            if not set(requirements.requirements) <= covered:
                reasons.append("expected_coverage")
            if cost > context.budget:
                reasons.append("budget")
            if reasons:
                rejected.append(Infeasibility(verifiers=names, reasons=tuple(reasons)))
                continue
            for aggregation in AGGREGATIONS:
                strategies.append(Strategy(strategy_id=content_id([names, aggregation]),
                                           verifiers=names, aggregation=aggregation, estimated_cost=cost))
    if not candidates:
        rejected.append(Infeasibility(verifiers=(), reasons=("no_eligible_candidates",)))
    return EnumerationResult(status="feasible" if strategies else "no_feasible_strategy",
                             strategies=tuple(strategies), rejected=tuple(rejected), exclusions=exclusions)
