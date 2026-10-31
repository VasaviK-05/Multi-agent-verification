"""Finite minimax LP, with recomputed primal and dual numerical certificates."""

import math
import numpy as np
from scipy.optimize import linprog

from app.game.models import PayoffMatrix, SolverResult
from app.game.coverage_contract import CoverageCertificate
from app.game.reliability_contract import ReliabilityCertificate


# Normalization must not weaken when payoff tolerance is loosened.
PROBABILITY_TOLERANCE = 1e-12
OPTIMALITY_BASIS = "highs_status_0_and_recomputed_primal_dual_certificate"
COVERAGE_OPTIMALITY_BASIS='highs_status_0_and_clean_coverage_primal_dual_certificate_v1'
RELIABILITY_OPTIMALITY_BASIS='highs_validation_then_cost_two_stage_certificate_v1'
LOSS_FEASIBILITY_TOLERANCE=1e-12


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


def solution_diagnostics(matrix, probabilities, attack_probabilities, tolerance, *, coverage_multiplier=0.):
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
    constraint=matrix.clean_coverage
    extra={}
    if not math.isfinite(coverage_multiplier) or coverage_multiplier<0:
        raise ValueError('invalid coverage dual multiplier')
    if constraint is None:
        if coverage_multiplier!=0:raise ValueError('legacy game cannot have a coverage multiplier')
        qs=(0.,)*len(probabilities);minimum=0.
    else:
        qs=tuple(q for s,q in constraint.strategy_coverage);minimum=constraint.minimum
        achieved=math.fsum(p*q for p,q in zip(probabilities,qs))
        residual=achieved-minimum
        if residual < -PROBABILITY_TOLERANCE:
            raise ValueError('returned policy violates clean coverage target')
        extra['coverage_certificate']=CoverageCertificate(multiplier=coverage_multiplier,achieved=achieved,residual=residual)
    # Dual: max_{y in simplex, eta>=0} min_s(M_s y - eta Q_s) + eta q_min.
    lower = min(math.fsum(row[a] * attack_probabilities[a] for a in range(len(attack_probabilities)))-coverage_multiplier*q
                for row,q in zip(matrix.values,qs))+coverage_multiplier*minimum
    value = max(losses)
    gap = value - lower
    if not all(math.isfinite(x) for x in (*losses, lower, value, gap)) or abs(gap) > tolerance:
        raise ValueError("returned policy is not minimax within the primal-dual gap tolerance")
    return dict(game_value=value, attack_losses=tuple(zip(matrix.attack_ids, losses)),
                constraint_residuals=tuple((a, value - loss) for a, loss in zip(matrix.attack_ids, losses)),
                worst_case_attacks=tuple(a for a, loss in zip(matrix.attack_ids, losses) if value - loss <= tolerance),
                normalization_residual=math.fsum(probabilities) - 1,
                minimum_probability=min(probabilities), dual_lower_bound=lower, primal_dual_gap=gap,**extra)


def validate_solution(matrix: PayoffMatrix, solution: SolverResult) -> SolverResult:
    """Check imported diagnostics and a solver-derived dual witness, not just status."""
    matrix = PayoffMatrix.model_validate(matrix)
    solution = SolverResult.model_validate(solution)
    if solution.status != "optimal" or solution.matrix_id != matrix.matrix_id:
        raise ValueError("policy does not contain an optimal solution for its matrix")
    if (tuple(s for s, _ in solution.probabilities) != matrix.strategy_ids
        or tuple(a for a, _ in solution.attack_probabilities) != matrix.attack_ids):
        raise ValueError("policy probability labels differ from matrix")
    if matrix.reliability_first is not None:
        return validate_reliability_solution(matrix,solution)
    if solution.reliability_certificate is not None:
        raise ValueError('legacy solver result cannot contain a reliability certificate')
    constrained=matrix.clean_coverage is not None
    if constrained!=(solution.coverage_certificate is not None):
        raise ValueError('coverage certificate does not match matrix semantics')
    expected = solution_diagnostics(matrix, tuple(p for _, p in solution.probabilities),
                                    tuple(p for _, p in solution.attack_probabilities), solution.tolerance,
                                    coverage_multiplier=solution.coverage_certificate.multiplier if constrained else 0.)
    if solution.optimality_basis != (COVERAGE_OPTIMALITY_BASIS if constrained else OPTIMALITY_BASIS):
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
    if matrix.reliability_first is not None:
        return solve_reliability_first(matrix,tolerance=tolerance)
    common = dict(tolerance=tolerance, matrix_id=matrix.matrix_id)

    def failure(message):
        return SolverResult(status="solver_failure", message=message, **common)

    values = np.asarray(matrix.values, dtype=float)
    n, attacks = values.shape
    constraint=matrix.clean_coverage
    inequalities=np.column_stack((values.T, -np.ones(attacks)))
    bounds_rhs=np.zeros(attacks)
    if constraint is not None:
        qs=np.asarray([q for s,q in constraint.strategy_coverage])
        if max(qs)<constraint.minimum:
            return SolverResult(status='infeasible',message='clean coverage target exceeds every feasible strategy',**common)
        inequalities=np.vstack((inequalities,np.r_[-qs,0.]))
        bounds_rhs=np.r_[bounds_rhs,-constraint.minimum]
    try:
        result = linprog(np.r_[np.zeros(n), 1.0],
                         A_ub=inequalities,
                         b_ub=bounds_rhs, A_eq=[np.r_[np.ones(n), 0.0]],
                         b_eq=[1.0], bounds=[(0, None)] * n + [(None, None)],
                         method="highs")
    except Exception as exc:
        return failure(f"linprog raised {type(exc).__name__}: {exc}")
    if not getattr(result, "success", False) or getattr(result, "status", None) != 0:
        if constraint is not None and getattr(result,'status',None)==2:
            return SolverResult(status='infeasible',message=str(result.message),**common)
        return failure(f"linprog status {getattr(result, 'status', None)}: {getattr(result, 'message', '')}")
    try:
        raw = np.asarray(result.x, dtype=float)
        if raw.shape != (n + 1,) or not np.isfinite(raw).all():
            raise ValueError("solver returned malformed/nonfinite solution")
        probabilities = _distribution(raw[:-1], n, tolerance)
        # HiGHS inequality marginals have the opposite sign of attacker mass.
        dual = -np.asarray(result.ineqlin.marginals, dtype=float)
        if dual.shape != (attacks+int(constraint is not None),):
            raise ValueError("solver returned malformed dual solution")
        attack_probabilities = _distribution(dual[:attacks], attacks, tolerance)
        multiplier=max(0.,float(dual[-1])) if constraint is not None else 0.
        if constraint is not None and dual[-1]<-PROBABILITY_TOLERANCE:raise ValueError('negative coverage dual')
        diagnostics = solution_diagnostics(matrix, probabilities, attack_probabilities, tolerance,coverage_multiplier=multiplier)
        if abs(diagnostics["game_value"] - float(raw[-1])) > tolerance:
            raise ValueError("solver objective differs from returned distribution's worst-case loss")
    except (AttributeError, TypeError, ValueError, OverflowError) as exc:
        return failure(f"solution certificate failed: {exc}")
    return SolverResult(status="optimal", message=str(getattr(result, "message", "")),
                        probabilities=tuple(zip(matrix.strategy_ids, probabilities)),
                        attack_probabilities=tuple(zip(matrix.attack_ids, attack_probabilities)),
                        optimality_basis=COVERAGE_OPTIMALITY_BASIS if constraint is not None else OPTIMALITY_BASIS, **diagnostics, **common)


def validation_matrix(matrix):
    """Stage A uses empirical validation loss, never the cost-inclusive columns."""
    return PayoffMatrix(**{**matrix.model_dump(),'values':matrix.reliability_first.validation_values,'reliability_first':None})


def reliability_diagnostics(matrix,probabilities,stage_a,attack_multipliers,coverage_multiplier,tolerance):
    spec=matrix.reliability_first;constraint=matrix.clean_coverage
    if (len(probabilities)!=len(matrix.strategy_ids) or any(not math.isfinite(p) or p<0 for p in probabilities)
        or abs(math.fsum(probabilities)-1)>PROBABILITY_TOLERANCE):raise ValueError('invalid reliability policy probabilities')
    if (tuple(a for a,v in attack_multipliers)!=matrix.attack_ids
        or any(not math.isfinite(v) or v<0 for a,v in attack_multipliers)
        or not math.isfinite(coverage_multiplier) or coverage_multiplier<0):
        raise ValueError('invalid Stage B dual multipliers')
    values=spec.validation_values;qs=tuple(q for s,q in constraint.strategy_coverage)
    cap=stage_a.game_value+spec.epsilon
    losses=tuple(math.fsum(p*row[j] for p,row in zip(probabilities,values)) for j in range(len(matrix.attack_ids)))
    achieved=math.fsum(p*q for p,q in zip(probabilities,qs))
    if achieved<constraint.minimum-PROBABILITY_TOLERANCE:raise ValueError('Stage B violates clean coverage')
    if max(losses)>cap+LOSS_FEASIBILITY_TOLERANCE:raise ValueError('Stage B violates Stage A reliability cap')
    costs=tuple(s.estimated_cost for s in matrix.strategy_definitions)
    expected_cost=math.fsum(p*c for p,c in zip(probabilities,costs))
    # Dual of min c.x with V^T x <= cap, -Q.x <= -q and x in simplex.
    lower=min(c+math.fsum(mu*v for (a,mu),v in zip(attack_multipliers,row))-coverage_multiplier*q
        for c,row,q in zip(costs,values,qs))-cap*math.fsum(mu for a,mu in attack_multipliers)+coverage_multiplier*constraint.minimum
    gap=expected_cost-lower
    if not all(math.isfinite(v) for v in (*losses,expected_cost,lower,gap)) or abs(gap)>spec.cost_tolerance:
        raise ValueError('Stage B cost optimality certificate failed')
    certificate=ReliabilityCertificate(stage_a_json=stage_a.model_dump_json(),reliability_cap=cap,
        attack_multipliers=attack_multipliers,coverage_multiplier=coverage_multiplier,
        achieved_coverage=achieved,coverage_residual=achieved-constraint.minimum,
        expected_cost=expected_cost,cost_dual_lower_bound=lower,cost_primal_dual_gap=gap)
    worst=max(losses)
    return dict(game_value=worst,attack_losses=tuple(zip(matrix.attack_ids,losses)),
        constraint_residuals=tuple((a,cap-loss) for a,loss in zip(matrix.attack_ids,losses)),
        worst_case_attacks=tuple(a for a,loss in zip(matrix.attack_ids,losses) if worst-loss<=tolerance),
        normalization_residual=math.fsum(probabilities)-1,minimum_probability=min(probabilities),
        dual_lower_bound=stage_a.dual_lower_bound,primal_dual_gap=worst-stage_a.dual_lower_bound,
        reliability_certificate=certificate)


def validate_reliability_solution(matrix,solution):
    certificate=solution.reliability_certificate
    if certificate is None or solution.coverage_certificate is not None or solution.optimality_basis!=RELIABILITY_OPTIMALITY_BASIS:
        raise ValueError('reliability-first requires both stage certificates and its versioned optimality basis')
    stage_a=SolverResult.model_validate_json(certificate.stage_a_json)
    if stage_a.tolerance!=solution.tolerance:raise ValueError('Stage A certificate tolerance differs')
    validate_solution(validation_matrix(matrix),stage_a)
    if solution.attack_probabilities!=stage_a.attack_probabilities:raise ValueError('Stage A attacker witness differs')
    expected=reliability_diagnostics(matrix,tuple(p for s,p in solution.probabilities),stage_a,
        certificate.attack_multipliers,certificate.coverage_multiplier,solution.tolerance)
    for field,value in expected.items():
        if getattr(solution,field)!=value:raise ValueError('reliability diagnostic differs: '+field)
    return solution


def solve_reliability_first(matrix,*,tolerance):
    common=dict(matrix_id=matrix.matrix_id,tolerance=tolerance)
    stage_a=solve_minimax(validation_matrix(matrix),tolerance=tolerance)
    if stage_a.status!='optimal':return SolverResult(status=stage_a.status,message='Stage A: '+stage_a.message,**common)
    spec=matrix.reliability_first;constraint=matrix.clean_coverage
    values=np.asarray(spec.validation_values);n,attacks=values.shape
    qs=np.asarray([q for s,q in constraint.strategy_coverage]);costs=np.asarray([s.estimated_cost for s in matrix.strategy_definitions])
    cap=stage_a.game_value+spec.epsilon
    try:
        result=linprog(costs,A_ub=np.vstack((values.T,-qs)),b_ub=np.r_[np.full(attacks,cap),-constraint.minimum],
            A_eq=[np.ones(n)],b_eq=[1.],bounds=[(0,None)]*n,method='highs',
            options={'primal_feasibility_tolerance':1e-10,'dual_feasibility_tolerance':1e-10})
        if not result.success or result.status!=0:raise ValueError('Stage B solver status '+str(result.status)+': '+result.message)
        probabilities=_distribution(result.x,n,tolerance)
        dual=-np.asarray(result.ineqlin.marginals,dtype=float)
        if dual.shape!=(attacks+1,) or not np.isfinite(dual).all() or min(dual)<-PROBABILITY_TOLERANCE:
            raise ValueError('malformed Stage B dual')
        diagnostics=reliability_diagnostics(matrix,probabilities,stage_a,
            tuple(zip(matrix.attack_ids,(float(max(0.,v)) for v in dual[:attacks]))),float(max(0.,dual[-1])),tolerance)
        if abs(diagnostics['reliability_certificate'].expected_cost-float(result.fun))>spec.cost_tolerance:
            raise ValueError('Stage B returned cost differs from recomputed objective')
        solution=SolverResult(status='optimal',message='Stage A and Stage B: '+str(result.message),
            probabilities=tuple(zip(matrix.strategy_ids,probabilities)),attack_probabilities=stage_a.attack_probabilities,
            optimality_basis=RELIABILITY_OPTIMALITY_BASIS,**diagnostics,**common)
        return validate_solution(matrix,solution)
    except (Exception,) as exc:
        return SolverResult(status='solver_failure',message='Stage B: '+type(exc).__name__+': '+str(exc),**common)
