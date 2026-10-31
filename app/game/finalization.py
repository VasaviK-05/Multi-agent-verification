"""Pure full-team finalization; no datasets, verifiers, persistence or learning."""

from dataclasses import dataclass

from app.decision.coverage import factual_capabilities, task_capabilities
from app.decision.decision_engine import DecisionEngine
from app.decision.early_termination import AdaptiveEarlyTermination, _is_structural_rule
from app.decision.report_identity import canonical_reports
from app.decision.vote_normalization import is_abstention, vote_confidence
from app.game.decision_inputs import FrozenReputationSnapshot
from app.game.execution_contract import ExecutionContract
from app.game.models import PlanningContext, Strategy
from app.game.strategies import enumerate_strategies


@dataclass(frozen=True)
class FinalizedDecision:
    detail: object
    public_status: str
    contributors: int
    required: tuple[str, ...]
    achieved: tuple[str, ...]
    unresolved: tuple[str, ...]
    reasons: tuple[str, ...]
    execution_states: tuple[tuple[str, str], ...]
    estimated_attempt_cost: float


def informative_contributor_count(context,detail,rows,aggregation):
    """Count positively reliable, actually influential reports, not independence.

    For groups, influence is outer group influence times the member's within-group
    reliability fraction. Zero-weight active members and negative log-odds votes
    therefore cannot satisfy this opt-in minimum.
    """
    candidates={c.verifier_name:c for c in context.plan.candidates}
    votes={v.verifier_name:v for v in detail.votes}
    groups={g.group_id:g for g in detail.groups}
    count=0
    for row in rows:
        vote=votes[row.verifier_name];candidate=candidates[row.verifier_name]
        if (is_abstention(row) or vote_confidence(row)<=0 or vote.reputation<=.5
            or _is_structural_rule(row) or not candidate.eligible
            or (candidate.requires_reference and not context.plan.reference_available)):
            continue
        if aggregation=='reputation_weighted':
            influential=vote.included and vote.weight>0
        else:
            group=groups.get(vote.failure_group_id)
            influential=(vote.included and vote.reliability_strength>0 and group is not None
                and group.influence>0 and group.reliability_sum>0)
        count+=bool(influential)
    return count


def finalize_decision(context, strategy, contract, reports, execution_states, validation_id):
    context = PlanningContext.model_validate(context)
    strategy = Strategy.model_validate(strategy)
    contract = ExecutionContract.model_validate(contract)
    if context.execution_contract_json is not None:
        bound_contract=ExecutionContract.model_validate_json(context.execution_contract_json)
        task_aware='offline_public_decision_v4' in {bound_contract.version,contract.version}
        if ((task_aware and bound_contract!=contract)
            or bound_contract.contributor_version!=contract.contributor_version):
            raise ValueError('finalization execution contract differs from the bound execution semantics')
    if strategy not in enumerate_strategies(context).strategies:
        raise ValueError("strategy differs from the feasible team/aggregation/cost definition")
    states = tuple(execution_states)
    if tuple(name for name, state in states) != strategy.verifiers:
        raise ValueError("execution outcomes must match the complete selected team in order")
    if any(state not in {"directional", "abstention", "unavailable", "failed"} for _, state in states):
        raise ValueError("invalid execution state; missing recordings are not execution outcomes")
    rows, _, _ = canonical_reports(reports, team=strategy.verifiers, validation_id=validation_id, deduplicate=False)
    lookup = {r.verifier_name: r for r in rows}
    for name, state in states:
        if (name in lookup) != (state in {"directional", "abstention"}):
            raise ValueError("returned report does not match execution state")
        if name in lookup and is_abstention(lookup[name]) != (state == "abstention"):
            raise ValueError("normalized report differs from execution state")
    detail = DecisionEngine(threshold=contract.threshold).decide_detailed(rows, domain=context.plan.domain,
        snapshot=FrozenReputationSnapshot.from_planning_context(context), aggregation=strategy.aggregation,
        team=strategy.verifiers, validation_id=validation_id)
    if contract.contributor_version=='informative_history_influence_v1':
        contributors=informative_contributor_count(context,detail,rows,strategy.aggregation)
    elif strategy.aggregation == "reputation_weighted":
        contributors = AdaptiveEarlyTermination.contributor_count(detail, rows)
    else:
        contributors = sum(v.included and not _is_structural_rule(r) for v, r in zip(detail.votes, rows))
    required = tuple(sorted(set(context.plan.requirements.requirements + context.plan.requirements.unsupported)))
    achieved = tuple(sorted(set().union(*(task_capabilities(r,requirements=required,reference_available=context.plan.reference_available)
        if contract.coverage_version=='task_output_contract_v2' else factual_capabilities(r) for r in rows))))
    unresolved = tuple(r for r in required if r not in achieved)
    reasons = []
    if contributors < context.minimum_participant_count:
        reasons.append("minimum_contributors")
    if unresolved:
        reasons.append("missing_achieved_coverage")
    if not context.plan.requirements.requirements_known or context.plan.requirements.status != "known":
        reasons.append("requirements_unresolved")
    if contract.failure_contract == "all_selected_returned" and any(s in {"failed", "unavailable"} for _, s in states):
        reasons.append("selected_execution_incomplete")
    return FinalizedDecision(detail, "uncertain" if reasons else detail.status, contributors,
                             required, achieved, unresolved, tuple(reasons), states, strategy.estimated_cost)
