"""Dataset-free, versioned execution semantics shared by deployment and replay."""

from typing import Literal
from pydantic import Field, StrictFloat, model_validator
from app.game.dependencies import FrozenModel, identifier

class ExecutionContract(FrozenModel):
    version: Literal["offline_public_decision_v1"]
    coverage_version: Literal["factual_output_contract_v1"]
    contributor_version: Literal["baseline_log_odds_active_group_v1"]
    threshold: StrictFloat = Field(gt=0, lt=1)
    failure_contract: Literal["all_selected_returned", "allow_failed_if_covered"]
    execution_configuration_id: str
    history_prior_alpha: StrictFloat = Field(gt=0)
    history_prior_beta: StrictFloat = Field(gt=0)

    @model_validator(mode="after")
    def check(self):
        identifier(self.execution_configuration_id)
        return self
