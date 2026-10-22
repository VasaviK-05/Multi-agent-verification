"""Finite minimax LP, with recomputed primal and dual numerical certificates."""

import math
import numpy as np
from scipy.optimize import linprog

from app.game.models import PayoffMatrix, SolverResult


# Normalization must not weaken when payoff tolerance is loosened.
PROBABILITY_TOLERANCE = 1e-12
OPTIMALITY_BASIS = "highs_status_0_and_recomputed_primal_dual_certificate"


def _distribution(raw, count, tolerance):
    values = tuple(float(x) for x in raw)
    if (len(values) != count or not all(math.isfinite(x) for x in values)
        or min(values) < -tolerance or abs(math.fsum(values) - 1) > tolerance):
        raise ValueError("solver distribution violates probability constraints")
    cleaned = tuple(max(0.0, x) for x in values)
    total = math.fsum(cleaned)
    if total <= 0:
        raise ValueError("solver returned zero probability mass")
    return tuple(x / total for x in cleaned)


def solution_diagnostics(matrix, probabilities, attack_probabilities, tolerance):
    """Recompute feasible bounds without an LP call, in floating-point arithmetic."""
    for distribution in (probabilities, attack_probabilities):
        if (not distribution or any(not math.isfinite(p) or p < 0 for p in distribution)
            or abs(math.fsum(distribution) - 1) > PROBABILITY_TOLERANCE):
            raise ValueError("invalid returned policy distribution")
    if len(probabilities) != len(matrix.strategy_ids) or len(attack_probabilities) != len(matrix.attack_ids):
        raise ValueError("distribution dimensions differ from matrix")
    losses = tuple(math.fsum(probabilities[i] * matrix.values[i][a]
                            for i in range(len(probabilities)))
                   for a in range(len(attack_probabilities)))
    lower = min(math.fsum(row[a] * attack_probabilities[a] for a in range(len(attack_probabilities)))
                for row in matrix.values)
    value = max(losses)
    gap = value - lower
    if not all(math.isfinite(x) for x in (*losses, lower, value, gap)) or abs(gap) > tolerance:
        raise ValueError("returned policy is not minimax within the primal-dual gap tolerance")
    return dict(game_value=value, attack_losses=tuple(zip(matrix.attack_ids, losses)),
                constraint_residuals=tuple((a, value - loss) for a, loss in zip(matrix.attack_ids, losses)),
                worst_case_attacks=tuple(a for a, loss in zip(matrix.attack_ids, losses) if value - loss <= tolerance),
                normalization_residual=math.fsum(probabilities) - 1,
                minimum_probability=min(probabilities), dual_lower_bound=lower, primal_dual_gap=gap)


def validate_solution(matrix: PayoffMatrix, solution: SolverResult) -> SolverResult:
    """Check imported diagnostics and a solver-derived dual witness, not just status."""
    matrix = PayoffMatrix.model_validate(matrix)
    solution = SolverResult.model_validate(solution)
    if solution.status != "optimal" or solution.matrix_id != matrix.matrix_id:
        raise ValueError("policy does not contain an optimal solution for its matrix")
    if (tuple(s for s, _ in solution.probabilities) != matrix.strategy_ids
        or tuple(a for a, _ in solution.attack_probabilities) != matrix.attack_ids):
        raise ValueError("policy probability labels differ from matrix")
    expected = solution_diagnostics(matrix, tuple(p for _, p in solution.probabilities),
                                    tuple(p for _, p in solution.attack_probabilities), solution.tolerance)
    if solution.optimality_basis != OPTIMALITY_BASIS:
        raise ValueError("policy lacks a checked primal-dual optimality basis")
    for field, value in expected.items():
        if getattr(solution, field) != value:
            raise ValueError(f"policy diagnostic {field} differs from returned distribution")
    return solution


def solve_minimax(matrix: PayoffMatrix, *, tolerance: float = 1e-8) -> SolverResult:
    if (isinstance(tolerance, bool) or not isinstance(tolerance, (int, float))
        or not math.isfinite(tolerance) or not 0 < tolerance <= 1e-3):
        raise ValueError("tolerance must be finite in (0, 0.001]")
    matrix = PayoffMatrix.model_validate(matrix)
    common = dict(tolerance=tolerance, matrix_id=matrix.matrix_id)

    def failure(message):
        return SolverResult(status="solver_failure", message=message, **common)

    values = np.asarray(matrix.values, dtype=float)
    n, attacks = values.shape
    try:
        result = linprog(np.r_[np.zeros(n), 1.0],
                         A_ub=np.column_stack((values.T, -np.ones(attacks))),
                         b_ub=np.zeros(attacks), A_eq=[np.r_[np.ones(n), 0.0]],
                         b_eq=[1.0], bounds=[(0, None)] * n + [(None, None)],
                         method="highs")
    except Exception as exc:
        return failure(f"linprog raised {type(exc).__name__}: {exc}")
    if not getattr(result, "success", False) or getattr(result, "status", None) != 0:
        return failure(f"linprog status {getattr(result, 'status', None)}: {getattr(result, 'message', '')}")
    try:
        raw = np.asarray(result.x, dtype=float)
        if raw.shape != (n + 1,) or not np.isfinite(raw).all():
            raise ValueError("solver returned malformed/nonfinite solution")
        probabilities = _distribution(raw[:-1], n, tolerance)
        # HiGHS inequality marginals have the opposite sign of attacker mass.
        dual = -np.asarray(result.ineqlin.marginals, dtype=float)
        if dual.shape != (attacks,):
            raise ValueError("solver returned malformed dual solution")
        attack_probabilities = _distribution(dual, attacks, tolerance)
        diagnostics = solution_diagnostics(matrix, probabilities, attack_probabilities, tolerance)
        if abs(diagnostics["game_value"] - float(raw[-1])) > tolerance:
            raise ValueError("solver objective differs from returned distribution's worst-case loss")
    except (AttributeError, TypeError, ValueError, OverflowError) as exc:
        return failure(f"solution certificate failed: {exc}")
    return SolverResult(status="optimal", message=str(getattr(result, "message", "")),
                        probabilities=tuple(zip(matrix.strategy_ids, probabilities)),
                        attack_probabilities=tuple(zip(matrix.attack_ids, attack_probabilities)),
                        optimality_basis=OPTIMALITY_BASIS, **diagnostics, **common)
