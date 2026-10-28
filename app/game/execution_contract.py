"""Dataset-free, versioned execution semantics shared by deployment and replay."""

from typing import Literal
from pydantic import Field, StrictFloat, model_serializer, model_validator
from app.game.dependencies import FrozenModel, identifier
from app.game.resource_provenance import ResourceManifest

class ExecutionContract(FrozenModel):
    version: Literal["offline_public_decision_v1", "offline_public_decision_v2"]
    coverage_version: Literal["factual_output_contract_v1"]
    contributor_version: Literal["baseline_log_odds_active_group_v1"]
    threshold: StrictFloat = Field(gt=0, lt=1)
    failure_contract: Literal["all_selected_returned", "allow_failed_if_covered"]
    execution_configuration_id: str
    history_prior_alpha: StrictFloat = Field(gt=0)
    history_prior_beta: StrictFloat = Field(gt=0)
    resource_manifest: ResourceManifest | None = None

    @model_serializer(mode="wrap")
    def serialize_contract(self, handler):
        data = handler(self)
        if self.resource_manifest is None:
            data.pop("resource_manifest", None)
        return data

    @model_validator(mode="after")
    def check(self):
        identifier(self.execution_configuration_id)
        if self.version == "offline_public_decision_v2":
            if self.resource_manifest is None or self.execution_configuration_id != self.resource_manifest.manifest_id:
                raise ValueError("v2 execution identity must equal its resource manifest digest")
        elif self.resource_manifest is not None:
            raise ValueError("resource-bound execution requires contract v2")
        return self
