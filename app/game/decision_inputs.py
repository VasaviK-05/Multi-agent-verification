"""Small decision adapter over the validated Stage 1 captured context."""

from pydantic import model_validator

from app.game.dependencies import FrozenModel
from app.game.models import PlanningContext


REPUTATION_VERSION = "log_odds_v1"
DEPENDENCY_VERSION = "groups_v1"


class FrozenReputationSnapshot(FrozenModel):
    context: PlanningContext
    snapshot_id: str

    @model_validator(mode="after")
    def validate_snapshot(self):
        if self.snapshot_id != self.context.reputation_snapshot_id:
            raise ValueError("reputation snapshot identifier differs from captured statistics")
        return self

    @classmethod
    def from_planning_context(cls, context: PlanningContext):
        context = PlanningContext.model_validate(context)
        return cls(context=context, snapshot_id=context.reputation_snapshot_id)

    def means(self, domain: str, names) -> dict[str, float]:
        names = tuple(names)
        plan = self.context.plan
        if domain != plan.domain:
            raise ValueError("decision domain differs from reputation snapshot domain")
        statistics = {row.verifier_name: row for row in plan.reputation_statistics}
        missing = set(names) - statistics.keys()
        if missing:
            raise ValueError(f"missing reputation snapshot statistics: {sorted(missing)}")
        return {name: statistics[name].posterior_mean for name in names}

    def require_version(self, aggregation: str, version: str) -> None:
        if dict(self.context.aggregation_versions).get(aggregation) != version:
            raise ValueError(f"snapshot aggregation version is incompatible with {aggregation}:{version}")


def checked_snapshot(snapshot, domain: str, names, aggregation: str) -> FrozenReputationSnapshot:
    if not isinstance(snapshot, FrozenReputationSnapshot):
        raise ValueError("a PlanningContext-backed FrozenReputationSnapshot is required")
    captured = FrozenReputationSnapshot.model_validate(snapshot)
    captured.means(domain, names)
    captured.require_version(aggregation, DEPENDENCY_VERSION if aggregation == "dependency_group" else REPUTATION_VERSION)
    return captured
