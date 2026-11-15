"""Development-only comparison preparation for bound component games.

Never flatten component reports or authorize atomic replay for a joint policy.
The original full policy is validated and retained, never optimized here.
"""
import math
from typing import Literal

from pydantic import model_validator

from app.game.component_execution import ComponentPolicy, enumerate_component_strategies
from app.game.dependencies import FrozenModel, identifier
from app.game.models import PayoffMatrix, SolverResult, content_id
from app.game.offline.compound import Training, construct_payoffs
from app.game.research.comparison import (
    METHODS, UnavailableMethod, coverage_compliance, deterministic_id, project_matrix,
)
from app.game.solver import solve_minimax, validate_solution


def component_restriction(policy, aggregation):
    strategies = enumerate_component_strategies(policy.contract)
    # A method fixes the aggregation on EVERY obligation, not a flattened vote.
    indices = tuple(i for i, strategy in enumerate(strategies)
                    if all(atomic.aggregation == aggregation for _, atomic in strategy.components))
    if not indices:
        raise ValueError('no component strategies for aggregation')
    return project_matrix(policy.matrix, indices)


class ComponentMethod(FrozenModel):
    method: str
    development_matrix: PayoffMatrix
    probabilities: tuple[tuple[str, float], ...]
    certificate: SolverResult | None = None

    @model_validator(mode='after')
    def check(self):
        if (tuple(s for s, _ in self.probabilities) != self.development_matrix.strategy_ids
                or any(p < 0 for _, p in self.probabilities)
                or abs(math.fsum(p for _, p in self.probabilities) - 1.) > 1e-12):
            raise ValueError('invalid component comparison distribution')
        if self.certificate is not None:
            validate_solution(self.development_matrix, self.certificate)
            if self.probabilities != self.certificate.probabilities:
                raise ValueError('component distribution differs from certificate')
        return self

    @property
    def coverage_compliance(self):
        return coverage_compliance(self.development_matrix, self.probabilities)


class FrozenComponentComparison(FrozenModel):
    version: Literal['frozen_component_comparison_v1'] = 'frozen_component_comparison_v1'
    full_policy: ComponentPolicy
    training_binding_id: str
    development_outcomes_id: str
    freeze_record: str
    methods: tuple[ComponentMethod, ...]
    unavailable_methods: tuple[UnavailableMethod, ...]

    @model_validator(mode='after')
    def check(self):
        identifier(self.freeze_record)
        strategies = enumerate_component_strategies(self.full_policy.contract)
        # Existing V2 scientific objective is only defined for equal-cost plans.
        if len({s.estimated_cost for s in strategies}) != 1:
            raise ValueError('unequal-cost joint plans require a declared two-stage objective')
        roster = tuple(m.method for m in self.methods) + tuple(m.method for m in self.unavailable_methods)
        if len(roster) != len(METHODS) or set(roster) != set(METHODS):
            raise ValueError('complete component method roster required')
        matrix = self.full_policy.matrix
        constraint = matrix.clean_coverage
        if constraint is not None and (constraint.training_binding_id != self.training_binding_id
                or constraint.source_evaluation_id != self.development_outcomes_id):
            raise ValueError('component development provenance differs from frozen coverage')
        costs = tuple(s.estimated_cost for s in strategies)
        for method in self.methods:
            expected = component_restriction(self.full_policy, method.method.removeprefix('fixed_')) if method.method.startswith('fixed_') else matrix
            if method.development_matrix != expected:
                raise ValueError('component comparison changed joint rows or protections')
            if method.method == 'full_minimax':
                if method.certificate != self.full_policy.solution:
                    raise ValueError('full component probabilities changed')
            elif method.method.startswith('fixed_'):
                if method.certificate is None:
                    raise ValueError('component restriction requires a certificate')
            elif method.method == 'uniform':
                if method.certificate is not None or method.probabilities != tuple((s, 1. / len(matrix.strategy_ids)) for s in matrix.strategy_ids):
                    raise ValueError('uniform component distribution changed')
            elif method.method in {'deterministic_minimax', 'clean_development'}:
                selected = deterministic_id(matrix, clean=method.method == 'clean_development',
                    tolerance=self.full_policy.solution.tolerance, costs=costs)
                if selected is None or method.certificate is not None or method.probabilities != tuple((s, float(i == selected)) for i, s in enumerate(matrix.strategy_ids)):
                    raise ValueError('fixed component strategy differs from development selection')
            else:
                raise ValueError('no independently defined comparable component greedy executor')
        for method in self.unavailable_methods:
            if method.method == 'coverage_aware_greedy':
                if method.status != 'unavailable':
                    raise ValueError('component greedy is unavailable, not an infeasible fitted game')
            elif method.method in {'deterministic_minimax', 'clean_development'}:
                if method.status != 'infeasible' or deterministic_id(matrix,
                    clean=method.method == 'clean_development', costs=costs) is not None:
                    raise ValueError('component fixed method is feasible')
            elif method.method.startswith('fixed_'):
                expected = component_restriction(self.full_policy, method.method.removeprefix('fixed_'))
                result = method.solver_result
                if (method.development_matrix != expected or result is None or result.status != method.status
                        or result.matrix_id != expected.matrix_id or result.probabilities or result.status == 'optimal'):
                    raise ValueError('component restriction lacks exact failed solve')
                if result.status == 'infeasible' and (expected.clean_coverage is None or
                        max(q for _, q in expected.clean_coverage.strategy_coverage) >= expected.clean_coverage.minimum):
                    raise ValueError('restricted component coverage is feasible')
            else:
                raise ValueError('component method cannot be omitted')
        return self

    @property
    def comparison_id(self):
        return content_id(self.model_dump(mode='json'))


def prepare_component_comparison(policy, training, *, freeze_record):
    """Reconstruct joint DEVELOPMENT cells with original provenance checks.

    No final recordings accepted. Requires canonical training inputs, rather than
    treating published finalized outcomes as a resource-observation substitute.
    """
    policy = ComponentPolicy.model_validate(policy)
    training = Training.model_validate(training)
    contract, matrix, outcomes = construct_payoffs(training, contract=policy.contract)
    if contract != policy.contract or matrix != policy.matrix:
        raise ValueError('component training differs from frozen policy')
    strategies = enumerate_component_strategies(contract)
    costs = tuple(s.estimated_cost for s in strategies)
    methods, unavailable = [], []
    for name in METHODS:
        current, certificate = matrix, None
        if name == 'coverage_aware_greedy':
            unavailable.append(UnavailableMethod(method=name, status='unavailable',
                reason='no independently defined comparable component greedy executor'))
            continue
        if name == 'full_minimax':
            certificate = policy.solution
            probabilities = certificate.probabilities
        elif name.startswith('fixed_'):
            current = component_restriction(policy, name.removeprefix('fixed_'))
            certificate = solve_minimax(current, tolerance=policy.solution.tolerance)
            if certificate.status != 'optimal':
                unavailable.append(UnavailableMethod(method=name, status=certificate.status,
                    reason=certificate.message, development_matrix=current, solver_result=certificate))
                continue
            probabilities = certificate.probabilities
        elif name == 'uniform':
            probabilities = tuple((s, 1. / len(matrix.strategy_ids)) for s in matrix.strategy_ids)
        else:
            selected = deterministic_id(matrix, clean=name == 'clean_development',
                tolerance=policy.solution.tolerance, costs=costs)
            if selected is None:
                unavailable.append(UnavailableMethod(method=name, status='infeasible',
                    reason='no fixed joint strategy meets development coverage floor'))
                continue
            probabilities = tuple((s, float(i == selected)) for i, s in enumerate(matrix.strategy_ids))
        methods.append(ComponentMethod(method=name, development_matrix=current,
            probabilities=probabilities, certificate=certificate))
    return FrozenComponentComparison(full_policy=policy, training_binding_id=training.binding_id,
        development_outcomes_id=content_id(outcomes), freeze_record=freeze_record,
        methods=tuple(methods), unavailable_methods=tuple(unavailable))
