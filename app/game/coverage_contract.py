"""Additive, development-only coverage obligation; not an attacked-coverage promise."""
from typing import Literal
from pydantic import Field, StrictFloat, model_validator
from app.game.dependencies import FrozenModel, identifier


class CleanCoverageConstraint(FrozenModel):
    version: Literal['finalized_clean_development_coverage_v1']
    minimum: StrictFloat = Field(ge=0,le=1)
    strategy_coverage: tuple[tuple[str,StrictFloat], ...]
    parent_matrix_id: str = Field(pattern=r'^[0-9a-f]{64}$')
    training_binding_id: str = Field(pattern=r'^[0-9a-f]{64}$')
    source_evaluation_id: str = Field(pattern=r'^[0-9a-f]{64}$')

    @model_validator(mode='after')
    def check(self):
        names=[s for s,q in self.strategy_coverage]
        if not names or len(names)!=len(set(names)):
            raise ValueError('coverage requires unique nonempty strategy axes')
        for s,q in self.strategy_coverage:
            identifier(s)
            if not 0<=q<=1:raise ValueError('invalid finalized clean coverage')
        return self


class CoverageCertificate(FrozenModel):
    version: Literal['clean_coverage_dual_v1']='clean_coverage_dual_v1'
    multiplier: StrictFloat = Field(ge=0)
    achieved: StrictFloat = Field(ge=0,le=1)
    residual: StrictFloat


def check_coverage_matrix(context,matrix):
    """Bind coverage, source matrix and training identity to deployment context."""
    from app.game.models import PlanningContext, PayoffMatrix
    constraint=matrix.clean_coverage
    if context.clean_coverage_json is None:
        if constraint is not None:raise ValueError('coverage matrix requires a bound coverage context')
        return
    expected=CleanCoverageConstraint.model_validate_json(context.clean_coverage_json)
    if constraint!=expected:raise ValueError('coverage matrix differs from context constraint')
    if expected.training_binding_id!=context.offline_evaluation_id:
        raise ValueError('coverage training binding differs from context')
    original=PlanningContext(**{**context.model_dump(),'clean_coverage_json':None})
    parent=PayoffMatrix(**{**matrix.model_dump(),'clean_coverage':None,'compatibility_id':original.compatibility_id})
    if parent.matrix_id!=expected.parent_matrix_id:
        raise ValueError('coverage matrix changed original development payoffs')
