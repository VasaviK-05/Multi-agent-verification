"""Dependency aggregation and opt-in explanations; no execution/coverage policy."""

from dataclasses import asdict, dataclass, fields
import json
import math

from app.decision.decision_engine import DecisionDetail, VoteExplanation, _require_domain, _require_threshold, _status
from app.decision.report_identity import canonical_reports
from app.decision.vote_normalization import is_abstention, signed_mass, vote_confidence
from app.game.decision_inputs import DEPENDENCY_VERSION, REPUTATION_VERSION, checked_snapshot
from app.game.dependencies import DependencyRegistry
from app.game.models import content_id


@dataclass(frozen=True)
class AggregationVote(VoteExplanation):
    validation_id: str | None
    normalized_strength: float | None
    reliability_strength: float
    included: bool
    inclusion_reason: str
    failure_group_id: str | None


@dataclass(frozen=True)
class GroupExplanation:
    group_id: str
    active_members: tuple[str, ...]
    reliability_sum: float
    score: float
    influence: float
    fallback: str | None
    contribution: float


@dataclass(frozen=True)
class AggregationDetail(DecisionDetail):
    aggregation_id: str
    aggregation_version: str
    reputation_snapshot_id: str | None
    validation_id: str | None
    team: tuple[str, ...]
    missing_reports: tuple[str, ...]
    dependency_configuration_id: str | None
    dependency_version: str | None
    dependency_assumptions: tuple[str, ...]
    groups: tuple[GroupExplanation, ...]
    fallback: str | None
    lower_cut: float
    upper_cut: float

    def to_dict(self):
        return json.loads(json.dumps(asdict(self), allow_nan=False))


def explain_reputation(detail, snapshot, *, validation_id=None, team=None):
    votes = tuple(AggregationVote(**asdict(vote), validation_id=validation_id,
        normalized_strength=None if vote.abstained else vote.confidence * (1 if vote.passed else -1),
        reliability_strength=max(0., 2 * vote.reputation - 1),
        included=not vote.abstained and vote.confidence > 0 and (
            detail.aggregation == "equal_weight" or vote.weight != 0),
        inclusion_reason=("abstention" if vote.abstained else "zero_confidence" if vote.confidence == 0
                          else "zero_log_odds_weight" if detail.aggregation == "log_odds" and vote.weight == 0
                          else "included"), failure_group_id=None) for vote in detail.votes)
    names = tuple(team) if team is not None else tuple(v.verifier_name for v in votes)
    base = {field.name: getattr(detail, field.name) for field in fields(DecisionDetail)}
    base["votes"] = votes
    return AggregationDetail(**base, aggregation_id="reputation_weighted", aggregation_version=REPUTATION_VERSION,
        reputation_snapshot_id=snapshot.snapshot_id if snapshot is not None else None,
        validation_id=validation_id, team=names,
        missing_reports=tuple(sorted(set(names) - {v.verifier_name for v in votes})),
        dependency_configuration_id=None, dependency_version=None, dependency_assumptions=(), groups=(),
        fallback="equal_weight" if detail.aggregation == "equal_weight" else None,
        lower_cut=-detail.threshold, upper_cut=detail.threshold)


def aggregate_dependency_groups(results, *, domain, threshold, snapshot, dependencies=None,
                                team=None, validation_id=None):
    domain, threshold = _require_domain(domain), _require_threshold(threshold)
    rows, validation_id, names = canonical_reports(results, team=team, validation_id=validation_id)
    snapshot = checked_snapshot(snapshot, domain, names, "dependency_group")
    registry = snapshot.context.dependencies
    if dependencies is not None:
        supplied = DependencyRegistry.model_validate(dependencies)
        if supplied != registry:
            raise ValueError("dependency registry differs from the captured planning configuration")
    reputations = snapshot.means(domain, names)
    groups = registry.groups(names)
    membership = {name: group.group_id for group in groups for name in group.verifiers}
    prepared = []
    for row in rows:
        abstained, confidence, mass = is_abstention(row), vote_confidence(row), signed_mass(row)
        reputation = reputations[row.verifier_name]
        strength = max(0., 2 * reputation - 1)
        active = not abstained and confidence > 0
        prepared.append(AggregationVote(
            verifier_name=row.verifier_name, abstained=abstained, passed=row.passed, confidence=confidence,
            reputation=reputation, weight=strength, contribution=strength * mass if active else 0.,
            validation_id=validation_id, normalized_strength=mass, reliability_strength=strength,
            included=active, inclusion_reason="abstention" if abstained else "zero_confidence" if not active else "included",
            failure_group_id=membership[row.verifier_name]))
    active_groups = []
    for group in groups:
        active = [v for v in prepared if v.failure_group_id == group.group_id and v.included]
        if not active:
            continue
        reliability_sum = math.fsum(v.reliability_strength for v in active)
        group_score = (math.fsum(v.reliability_strength * v.normalized_strength for v in active) / reliability_sum
                       if reliability_sum > 0 else math.fsum(v.normalized_strength for v in active) / len(active))
        influence = max(v.reliability_strength for v in active)
        active_groups.append(GroupExplanation(group.group_id, tuple(v.verifier_name for v in active),
            reliability_sum, group_score, influence, None if reliability_sum > 0 else "unweighted_members",
            influence * group_score))
    influence_sum = math.fsum(g.influence for g in active_groups)
    fallback = None if influence_sum > 0 or not active_groups else "unweighted_groups"
    if not rows:
        score, status, aggregation = 0., "unknown", "unknown"
    elif not active_groups:
        score, status = 0., "uncertain"
        aggregation = "abstentions" if all(v.abstained for v in prepared) else "zero_confidence"
    else:
        score = (math.fsum(g.contribution for g in active_groups) / influence_sum if influence_sum > 0
                 else math.fsum(g.score for g in active_groups) / len(active_groups))
        score = min(max(score, -1.), 1.)
        status, aggregation = _status(score, threshold), "dependency_group"
    return AggregationDetail(
        domain=domain, status=status, raw_score=score, score=round(score, 6), threshold=threshold,
        aggregation=aggregation, votes=tuple(prepared), aggregation_id="dependency_group",
        aggregation_version=DEPENDENCY_VERSION, reputation_snapshot_id=snapshot.snapshot_id,
        validation_id=validation_id, team=names,
        missing_reports=tuple(sorted(set(names) - {row.verifier_name for row in rows})),
        dependency_configuration_id=content_id(registry.model_dump(mode="json")),
        dependency_version=registry.version, dependency_assumptions=registry.assumptions,
        groups=tuple(active_groups), fallback=fallback, lower_cut=-threshold, upper_cut=threshold)
