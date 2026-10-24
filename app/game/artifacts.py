"""Dataset-free deployable policies and explicit frozen deployment episodes."""

import threading
from typing import Literal, Protocol

from pydantic import model_validator

from app.game.dependencies import FrozenModel, identifier
from app.game.decision_inputs import DEPENDENCY_VERSION, REPUTATION_VERSION
from app.game.execution_contract import ExecutionContract
from app.game.models import PlanningContext, canonical_json, content_id
from app.game.policy import Policy, validate_policy


class DeploymentEpisode(FrozenModel):
    episode_id: str
    context: PlanningContext
    contract: ExecutionContract
    execution_configuration_id: str

    @model_validator(mode="after")
    def validate_episode(self):
        identifier(self.episode_id)
        if self.context.offline_evaluation_id is None or self.context.execution_contract_json is None:
            raise ValueError("deployment requires offline provenance and an explicit evaluated execution contract")
        if self.context.execution_contract_json != canonical_json(self.contract.model_dump(mode="json")):
            raise ValueError("execution contract differs from context's evaluated contract")
        if self.execution_configuration_id != self.contract.execution_configuration_id:
            raise ValueError("execution configuration differs from evaluated identity")
        if self.contract.resource_manifest is not None:
            self.contract.resource_manifest.require_candidates(c.verifier_name for c in self.context.plan.candidates)
        if dict(self.context.aggregation_versions) != {
            "reputation_weighted": REPUTATION_VERSION, "dependency_group": DEPENDENCY_VERSION}:
            raise ValueError("unsupported aggregation versions")
        return self


class PolicyArtifact(FrozenModel):
    version: Literal["deployable_game_policy_v1"] = "deployable_game_policy_v1"
    policy: Policy
    context: PlanningContext
    contract: ExecutionContract
    execution_configuration_id: str
    # Pooling does not waive domain/snapshot compatibility; register per-domain applicability.
    applicable_domain: str

    @model_validator(mode="after")
    def validate_artifact(self):
        identifier(self.applicable_domain)
        if self.applicable_domain != self.context.plan.domain:
            raise ValueError("applicability must explicitly match the captured domain, including pooled artifacts")
        DeploymentEpisode(episode_id="artifact_validation", context=self.context, contract=self.contract,
                          execution_configuration_id=self.execution_configuration_id)
        object.__setattr__(self, "policy", validate_policy(self.policy, self.context))
        return self

    @property
    def artifact_id(self):
        return content_id(self.model_dump(mode="json"))


class PolicyProvider(Protocol):
    def snapshot(self) -> tuple[PolicyArtifact, ...]:
        """Return one immutable registry view; no request-supplied policy IDs."""
        ...


class InMemoryPolicyProvider:
    def __init__(self, artifacts=()):
        self._lock = threading.Lock()
        self.replace(artifacts)

    def replace(self, artifacts):
        captured = tuple(PolicyArtifact.model_validate(a) for a in artifacts)
        with self._lock:
            self._artifacts = captured

    def snapshot(self):
        with self._lock:
            return self._artifacts
