"""Explicit sparse-domain routing over already fitted, frozen deployment episodes."""

from pydantic import Field, StrictInt, model_validator

from app.game.artifacts import DeploymentEpisode
from app.game.dependencies import FrozenModel
from app.game.pooling_contract import unpooled_context


class DomainRoute(FrozenModel):
    direct_episode: DeploymentEpisode
    pooled_episode: DeploymentEpisode
    minimum_history_observations: StrictInt = Field(gt=0)

    @model_validator(mode="after")
    def check(self):
        direct, pooled = self.direct_episode.context, self.pooled_episode.context
        if direct.pooling_contract_json is not None or pooled.pooling_contract_json is None:
            raise ValueError("route requires a direct episode and an explicitly pooled episode")
        if unpooled_context(pooled) != direct:
            raise ValueError("direct and pooled routes must share the exact target context and history")
        return self

    @property
    def domain(self):
        return self.direct_episode.context.plan.domain

    @property
    def history_observations(self):
        # Conservative declared rule: the least-observed eligible candidate.
        plan = self.direct_episode.context.plan
        eligible = {c.verifier_name for c in plan.candidates if c.eligible}
        return min((s.observation_count for s in plan.reputation_statistics if s.verifier_name in eligible), default=0)

    @property
    def is_sparse(self):
        return self.history_observations < self.minimum_history_observations
