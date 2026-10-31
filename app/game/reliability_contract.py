"""Versioned lexicographic validation-loss / measured-attempt-cost obligations."""
from typing import Literal
from pydantic import Field, StrictFloat, model_validator
from app.game.dependencies import FrozenModel


class ReliabilityFirst(FrozenModel):
    version: Literal['validation_then_attempt_cost_v1']
    epsilon: StrictFloat = Field(gt=0,le=1e-3)
    cost_tolerance: StrictFloat = Field(gt=0,le=1e-3)
    parent_matrix_id: str = Field(pattern=r'^[0-9a-f]{64}$')
    validation_values: tuple[tuple[StrictFloat,...],...]

    @model_validator(mode='after')
    def check(self):
        if not self.validation_values or any(not r or any(v<0 for v in r) for r in self.validation_values):
            raise ValueError('nonempty nonnegative empirical validation losses required')
        return self


class ReliabilityCertificate(FrozenModel):
    version: Literal['validation_then_cost_certificate_v1']='validation_then_cost_certificate_v1'
    stage_a_json: str
    reliability_cap: StrictFloat
    attack_multipliers: tuple[tuple[str,StrictFloat],...]
    coverage_multiplier: StrictFloat = Field(ge=0)
    achieved_coverage: StrictFloat = Field(ge=0,le=1)
    coverage_residual: StrictFloat
    expected_cost: StrictFloat = Field(ge=0)
    cost_dual_lower_bound: StrictFloat
    cost_primal_dual_gap: StrictFloat


def check_reliability_matrix(context,matrix):
    """Return exact parent cost-inclusive game for the existing coverage checks."""
    from app.game.models import PlanningContext, PayoffMatrix
    if context.reliability_first_json is None:
        if matrix.reliability_first is not None:raise ValueError('reliability-first matrix requires its context binding')
        return context,matrix
    expected=ReliabilityFirst.model_validate_json(context.reliability_first_json,strict=True)
    if expected!=matrix.reliability_first:raise ValueError('reliability-first matrix differs from context')
    if not matrix.strategy_definitions:raise ValueError('reliability-first requires measured strategy costs')
    for row,losses,strategy in zip(matrix.values,expected.validation_values,matrix.strategy_definitions):
        for cost_inclusive,loss in zip(row,losses):
            if abs(cost_inclusive-(loss+context.loss_configuration.resource_weight*strategy.estimated_cost))>1e-12:
                raise ValueError('validation objective differs from bound cost-inclusive diagnostics')
    original=PlanningContext(**{**context.model_dump(),'reliability_first_json':None})
    parent=PayoffMatrix(**{**matrix.model_dump(),'reliability_first':None,'compatibility_id':original.compatibility_id})
    if parent.matrix_id!=expected.parent_matrix_id:raise ValueError('reliability-first parent matrix changed')
    return original,parent
