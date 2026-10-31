"""Content-addressed compatible policies; no production dispatcher or learned defaults."""

import math

from app.game.dependencies import FrozenModel, identifier
from app.game.models import PlanningContext, PayoffMatrix, PayoffProvenance, SolverResult, Strategy, content_id
from app.game.solver import solve_minimax, validate_solution
from app.game.strategies import enumerate_strategies
from app.game.coverage_contract import check_coverage_matrix
from app.game.reliability_contract import check_reliability_matrix

COVERAGE_POLICY_VERSION='game_policy_clean_coverage_v1'
INFORMATIVE_POLICY_VERSION='game_policy_informative_v1'
RELIABILITY_POLICY_VERSION='game_policy_reliability_first_v1'


def semantics_version(context,matrix):
    if matrix.reliability_first is not None:return RELIABILITY_POLICY_VERSION
    if matrix.clean_coverage is not None:return COVERAGE_POLICY_VERSION
    if context.execution_contract_json is not None:
        from app.game.execution_contract import ExecutionContract
        if ExecutionContract.model_validate_json(context.execution_contract_json).contributor_version=='informative_history_influence_v1':
            return INFORMATIVE_POLICY_VERSION
    return 'game_policy_v1'


def check_semantics(context,matrix,version):
    base,parent=check_reliability_matrix(context,matrix)
    check_coverage_matrix(base,parent)
    expected=semantics_version(context,matrix)
    reserved={COVERAGE_POLICY_VERSION,INFORMATIVE_POLICY_VERSION,RELIABILITY_POLICY_VERSION}
    if (expected!='game_policy_v1' and version!=expected) or (expected=='game_policy_v1' and version in reserved):
        raise ValueError('policy version does not match execution/optimization semantics')


class Policy(FrozenModel):
    version: str
    compatibility_id: str
    provenance: PayoffProvenance
    matrix: PayoffMatrix
    solution: SolverResult
    strategies: tuple[Strategy, ...]

    @property
    def policy_id(self) -> str:
        return content_id(self.model_dump(mode="json"))


class PolicyDecision(FrozenModel):
    policy_id: str
    policy_version: str
    strategy_id: str
    verifier_names: tuple[str, ...]
    aggregation: str
    estimated_cost: float
    budget: float
    cost_units: str
    dependency_assumptions: tuple[str, ...]
    reputation_snapshot_id: str
    selection_status: str
    explanation: str


def build_policy(context: PlanningContext, matrix: PayoffMatrix, *, version=None, tolerance=None) -> Policy:
    context = PlanningContext.model_validate(context)
    matrix = PayoffMatrix.model_validate(matrix)
    if version is None:
        version=semantics_version(context,matrix)
    identifier(version)
    check_semantics(context,matrix,version)
    if matrix.compatibility_id != context.compatibility_id:
        raise ValueError("incompatible payoff matrix")
    strategies = enumerate_strategies(context).strategies
    if not strategies or set(matrix.strategy_ids) != {s.strategy_id for s in strategies}:
        raise ValueError("matrix must cover exactly the feasible strategy set")
    lookup = {s.strategy_id: s for s in strategies}
    ordered = tuple(lookup[s] for s in matrix.strategy_ids)
    if matrix.strategy_definitions != ordered:
        raise ValueError("matrix row definitions must bind the exact feasible strategies")
    from app.game.pooling_contract import check_pool_matrix
    check_pool_matrix(context, matrix)
    # Preserve the original default call protocol for existing callers/adapters.
    solution = solve_minimax(matrix) if tolerance is None else solve_minimax(matrix, tolerance=tolerance)
    if solution.status != "optimal":
        raise ValueError("cannot build policy: " + solution.message)
    return Policy(version=version, compatibility_id=context.compatibility_id, provenance=context.provenance, matrix=matrix,
                  solution=solution, strategies=ordered)


def validate_policy(policy: Policy, context: PlanningContext) -> Policy:
    context = PlanningContext.model_validate(context)
    policy = Policy.model_validate(policy)
    identifier(policy.version)
    check_semantics(context,policy.matrix,policy.version)
    if (policy.compatibility_id != context.compatibility_id or policy.matrix.compatibility_id != context.compatibility_id
        or policy.provenance != context.provenance):
        raise ValueError("incompatible policy; rebuild or retrieve a compatible policy")
    expected = {s.strategy_id: s for s in enumerate_strategies(context).strategies}
    if (len(policy.strategies) != len(expected) or {s.strategy_id: s for s in policy.strategies} != expected
        or tuple(s.strategy_id for s in policy.strategies) != policy.matrix.strategy_ids):
        raise ValueError("policy strategy set differs from current feasible strategies")
    if policy.matrix.strategy_definitions != policy.strategies:
        raise ValueError("matrix row definitions differ from policy strategies")
    from app.game.pooling_contract import check_pool_matrix
    check_pool_matrix(context, policy.matrix)
    validate_solution(policy.matrix, policy.solution)
    return policy


def sample_policy(policy: Policy, context: PlanningContext, *, rng) -> PolicyDecision:
    context = PlanningContext.model_validate(context)
    policy = validate_policy(policy, context)
    draw = rng.random()
    if isinstance(draw, bool) or not isinstance(draw, (float, int)) or not math.isfinite(draw) or not 0 <= draw < 1:
        raise ValueError("rng.random() must return a finite number in [0,1)")
    probabilities = tuple(p for _, p in policy.solution.probabilities)
    selected = None
    for index, (strategy, probability) in enumerate(zip(policy.strategies, probabilities)):
        cumulative = math.fsum(probabilities[:index + 1])
        if probability > 0 and draw < cumulative:
            selected = strategy
            break
    if selected is None:
        # Only floating point accumulation at the upper boundary can reach this.
        selected = next(s for s, (_, p) in reversed(tuple(zip(policy.strategies, policy.solution.probabilities))) if p > 0)
    return PolicyDecision(policy_id=policy.policy_id, policy_version=policy.version,
                          strategy_id=selected.strategy_id, verifier_names=selected.verifiers,
                          aggregation=selected.aggregation, estimated_cost=selected.estimated_cost,
                          budget=context.budget, cost_units=context.cost_units,
                          dependency_assumptions=context.dependencies.assumptions,
                          reputation_snapshot_id=context.reputation_snapshot_id,
                          selection_status="selected", explanation=(
                              f"Sampled a validated compatible {context.provenance.evidence_kind} matrix policy; "
                              "execution is not enabled by Stage 1."))
