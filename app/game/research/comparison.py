"""Development-only comparisons and explicitly frozen final-test replay.

Research distributions are not deployable Policy objects. Restricted games retain
their exact row definitions and numerical certificate without weakening Stage 1.
"""

import math
from typing import Literal

from pydantic import StrictFloat, model_serializer, model_validator

from app.game.artifacts import PolicyArtifact
from app.game.dependencies import FrozenModel, identifier
from app.game.models import PayoffMatrix, PlanningContext, SolverResult, content_id
from app.game.offline.evaluation import Evaluation, Metrics, construct_payoffs, summarize
from app.game.offline.replay import replay
from app.game.research.readiness import greedy_strategy, require_ready
from app.game.research.specification import ExperimentSpecification, PolicyBuildSpecification
from app.game.solver import solve_minimax, validate_solution

METHODS = ("full_minimax", "uniform", "deterministic_minimax", "clean_development",
           "fixed_reputation_weighted", "fixed_dependency_group", "coverage_aware_greedy")


def comparison_specification(spec):
    """Accept training-only reservations without requiring released test labels."""
    schema = PolicyBuildSpecification if (isinstance(spec, PolicyBuildSpecification) or
        isinstance(spec, dict) and spec.get("version") == "offline_policy_build_v1") else ExperimentSpecification
    return schema.model_validate(spec)


def project_matrix(matrix, indices):
    """Research row projection; retain original provenance and objective settings.

    Parent/source IDs continue to identify the ORIGINAL development fit. This
    matrix is a research restriction, never a replacement deployment artifact.
    """
    data = matrix.model_dump()
    data.update(strategy_ids=tuple(matrix.strategy_ids[i] for i in indices),
        strategy_definitions=tuple(matrix.strategy_definitions[i] for i in indices) if matrix.strategy_definitions else (),
        values=tuple(matrix.values[i] for i in indices))
    if matrix.clean_coverage is not None:
        data['clean_coverage'] = {**matrix.clean_coverage.model_dump(),
            'strategy_coverage': tuple(matrix.clean_coverage.strategy_coverage[i] for i in indices)}
    if matrix.reliability_first is not None:
        data['reliability_first'] = {**matrix.reliability_first.model_dump(),
            'validation_values': tuple(matrix.reliability_first.validation_values[i] for i in indices)}
    return PayoffMatrix.model_validate(data)


def restricted_matrix(matrix, aggregation):
    indices = tuple(i for i, s in enumerate(matrix.strategy_definitions) if s.aggregation == aggregation)
    if not indices:
        raise ValueError("aggregation has no feasible strategies")
    return project_matrix(matrix, indices)


def coverage_compliance(matrix, probabilities):
    constraint = matrix.clean_coverage
    if constraint is None:
        return dict(minimum=None, achieved=None, satisfies=None)
    q = dict(constraint.strategy_coverage)
    achieved = math.fsum(p * q[s] for s, p in probabilities)
    return dict(minimum=constraint.minimum, achieved=achieved,
                satisfies=achieved >= constraint.minimum - 1e-12)


def deterministic_id(matrix, *, clean, tolerance=1e-8, costs=None):
    """Development-only coverage eligibility, validation first, then cost and ID."""
    eligible = list(range(len(matrix.strategy_ids)))
    if matrix.clean_coverage is not None:
        q = dict(matrix.clean_coverage.strategy_coverage)
        eligible = [i for i in eligible if q[matrix.strategy_ids[i]] >= matrix.clean_coverage.minimum]
    if not eligible:
        return None
    values = matrix.reliability_first.validation_values if matrix.reliability_first else matrix.values
    objective = lambda i: values[i][0] if clean else max(values[i])
    best = min(objective(i) for i in eligible)
    if matrix.reliability_first is not None:
        eligible = [i for i in eligible if objective(i) <= best + matrix.reliability_first.epsilon]
        return min(eligible, key=lambda i: (matrix.strategy_definitions[i].estimated_cost, matrix.strategy_ids[i]))
    if matrix.clean_coverage is not None:
        eligible = [i for i in eligible if objective(i) <= best + tolerance]
        costs = costs or tuple(s.estimated_cost for s in matrix.strategy_definitions)
        return min(eligible, key=lambda i: (costs[i], matrix.strategy_ids[i]))
    return min(eligible, key=lambda i: (objective(i), matrix.strategy_ids[i]))


def reconstructed_development(spec, development):
    """Validate stored fitting overlays by replaying DEVELOPMENT only; no solve."""
    from app.game.offline.coverage import prepare_clean_coverage
    from app.game.offline.reliability import prepare_reliability_first
    context = PlanningContext.model_validate({**spec.context.model_dump(),
        'clean_coverage_json': None, 'reliability_first_json': None})
    actual = construct_payoffs(context, spec.manifest, spec.contract, spec.attacks)
    if development != actual:
        raise ValueError("development evaluation differs from complete declared replay")
    if spec.context.reliability_first_json is not None:
        import json
        config = json.loads(spec.context.reliability_first_json)
        coverage = json.loads(spec.context.clean_coverage_json)
        bound, matrix = prepare_reliability_first(context, spec.manifest, spec.contract, spec.attacks,
            actual, minimum=coverage['minimum'], epsilon=config['epsilon'], cost_tolerance=config['cost_tolerance'])
    elif spec.context.clean_coverage_json is not None:
        import json
        bound, matrix = prepare_clean_coverage(context, spec.manifest, spec.contract, spec.attacks,
            actual, minimum=json.loads(spec.context.clean_coverage_json)['minimum'])
    else:
        bound, matrix = context, actual.matrix
    if bound != spec.context:
        raise ValueError("development overlays differ from frozen context")
    return matrix


class UnavailableMethod(FrozenModel):
    method: str
    status: Literal['infeasible', 'solver_failure', 'unavailable']
    reason: str
    development_matrix: PayoffMatrix | None = None
    solver_result: SolverResult | None = None


class ResearchPolicy(FrozenModel):
    method: Literal["full_minimax", "uniform", "deterministic_minimax", "clean_development",
                    "fixed_reputation_weighted", "fixed_dependency_group", "coverage_aware_greedy"]
    development_matrix: PayoffMatrix
    probabilities: tuple[tuple[str, StrictFloat], ...]
    selection_basis: Literal["development_minimax", "development_clean", "protocol_uniform", "captured_selector"]
    optimality_claim: Literal["none", "full_game_numerical_certificate", "declared_action_set_numerical_certificate"]
    certificate: SolverResult | None

    @property
    def coverage_compliance(self):
        return coverage_compliance(self.development_matrix, self.probabilities)

    @model_validator(mode="after")
    def validate_distribution(self):
        if tuple(k for k, _ in self.probabilities) != self.development_matrix.strategy_ids:
            raise ValueError("distribution labels must bind every declared action row in order")
        if not self.development_matrix.strategy_definitions:
            raise ValueError("explicit strategy definitions required")
        if any(p < 0 for _, p in self.probabilities) or abs(math.fsum(p for _, p in self.probabilities) - 1.) > 1e-12:
            raise ValueError("invalid research distribution")
        if self.certificate is not None:
            checked = validate_solution(self.development_matrix, self.certificate)
            if self.probabilities != checked.probabilities:
                raise ValueError("distribution differs from numerical certificate")
        if (self.optimality_claim != "none") != (self.certificate is not None):
            raise ValueError("optimality claim requires its exact action-set certificate")
        return self


class FrozenComparison(FrozenModel):
    version: Literal["frozen_research_comparison_v1"]
    specification_id: str
    code_revision: str
    manifest_id: str
    full_artifact: PolicyArtifact
    policies: tuple[ResearchPolicy, ...]
    freeze_record: str
    unavailable_methods: tuple[UnavailableMethod, ...] = ()

    @model_serializer(mode='wrap')
    def serialize_comparison(self, handler):
        data = handler(self)
        if not self.unavailable_methods:
            data.pop('unavailable_methods', None)
        return data

    @model_validator(mode="after")
    def bind_policies(self):
        identifier(self.freeze_record)
        available = tuple(p.method for p in self.policies)
        absent = tuple(p.method for p in self.unavailable_methods)
        if (len(available + absent) != len(METHODS) or len(set(available + absent)) != len(METHODS) or set(available + absent) != set(METHODS)
                or "full_minimax" not in available):
            raise ValueError("complete comparison roster required exactly once")
        for missing in self.unavailable_methods:
            if missing.method.startswith('fixed_'):
                expected = restricted_matrix(self.full_artifact.policy.matrix, missing.method.removeprefix('fixed_'))
                result = missing.solver_result
                if (missing.development_matrix != expected or result is None or result.status != missing.status
                        or result.matrix_id != expected.matrix_id or result.probabilities or result.status == 'optimal'):
                    raise ValueError('unavailable restriction lacks its exact failed solve')
                if result.status == 'infeasible' and (expected.clean_coverage is None or
                        max(q for _, q in expected.clean_coverage.strategy_coverage) >= expected.clean_coverage.minimum):
                    raise ValueError('restricted coverage is feasible; cannot report infeasibility')
            elif missing.method in {'deterministic_minimax', 'clean_development'}:
                if missing.status != 'infeasible' or deterministic_id(self.full_artifact.policy.matrix,
                        clean=missing.method == 'clean_development') is not None:
                    raise ValueError('fixed baseline is actually coverage feasible')
            elif missing.method == 'coverage_aware_greedy':
                team = tuple(sorted(self.full_artifact.context.plan.initial_selected))
                if missing.status != 'unavailable' or any(s.verifiers == team for s in self.full_artifact.policy.strategies):
                    raise ValueError('captured greedy team is actually feasible')
            else:
                raise ValueError('method cannot be omitted')
        matrix = self.full_artifact.policy.matrix
        for policy in self.policies:
            expected_matrix = matrix
            if policy.method.startswith("fixed_"):
                expected_matrix = restricted_matrix(matrix, policy.method.removeprefix("fixed_"))
            if policy.development_matrix != expected_matrix:
                raise ValueError("comparison action set differs from parent development matrix")
            method = policy.method
            expected_basis = ("protocol_uniform" if method == "uniform" else "captured_selector" if method == "coverage_aware_greedy"
                              else "development_clean" if method == "clean_development" else "development_minimax")
            expected_claim = ("full_game_numerical_certificate" if method == "full_minimax" else
                              "declared_action_set_numerical_certificate" if method.startswith("fixed_") else "none")
            if policy.selection_basis != expected_basis or policy.optimality_claim != expected_claim:
                raise ValueError("incorrect selection/optimality metadata")
            if method == "full_minimax":
                if policy.certificate != self.full_artifact.policy.solution:
                    raise ValueError("full minimax differs from artifact")
            elif method in {"deterministic_minimax", "clean_development"}:
                selected = deterministic_id(matrix, clean=method == "clean_development", tolerance=self.full_artifact.policy.solution.tolerance)
                if policy.probabilities != tuple((s, float(i == selected)) for i, s in enumerate(matrix.strategy_ids)):
                    raise ValueError("deterministic strategy is not the declared development optimum")
            elif method == "uniform":
                if policy.probabilities != tuple((s, 1. / len(matrix.strategy_ids)) for s in matrix.strategy_ids):
                    raise ValueError("uniform baseline changed")
            elif method == "coverage_aware_greedy":
                team = tuple(sorted(self.full_artifact.context.plan.initial_selected))
                selected = [s.strategy_id for s in matrix.strategy_definitions
                            if s.verifiers == team and dict(policy.probabilities)[s.strategy_id] == 1.]
                if len(selected) != 1 or any(p != float(s == selected[0]) for s, p in policy.probabilities):
                    raise ValueError("greedy baseline differs from the captured feasible selector team")
        return self

    @property
    def comparison_id(self):
        return content_id(self.model_dump(mode="json"))


def prepare_comparison(spec, development, full_artifact, *, freeze_record, actual_code_revision):
    """Explicit development entry. Requires an existing full policy, never fits it.

    Restricted aggregation LPs are solved here only. Dry-run and final scoring do
    not call this function. Stage 5A uses it only with labelled synthetic fixtures.
    """
    spec = comparison_specification(spec)
    readiness = require_ready(spec, actual_code_revision=actual_code_revision)
    development = Evaluation.model_validate(development)
    artifact = PolicyArtifact.model_validate(full_artifact)
    if development.role != "development":
        raise ValueError("baseline selection requires development data")
    if artifact.context != spec.context or artifact.contract != spec.contract:
        raise ValueError("artifact differs from experiment context/contract")
    if artifact.policy.solution.tolerance != spec.optimizer_tolerance:
        raise ValueError("full policy numerical tolerance differs from study specification")
    # Reuse replay to verify denominator, labels, rows, columns, costs and metrics.
    matrix = reconstructed_development(spec, development)
    if artifact.policy.matrix != matrix:
        raise ValueError("development evaluation/artifact differs from complete declared replay")
    if matrix.attack_ids != tuple(a.attack_id for a in readiness.attacks) or readiness.attacks[0].kind != "clean":
        raise ValueError("fixed attack columns differ")
    policies = []
    unavailable = []
    for method in METHODS:
        current = matrix
        certificate = None
        claim = "none"
        basis = "development_minimax"
        if method == "full_minimax":
            certificate = artifact.policy.solution
            probabilities = certificate.probabilities
            claim = "full_game_numerical_certificate"
        elif method.startswith("fixed_"):
            current = restricted_matrix(matrix, method.removeprefix("fixed_"))
            certificate = solve_minimax(current, tolerance=spec.optimizer_tolerance)
            if certificate.status != 'optimal':
                unavailable.append(UnavailableMethod(method=method, status=certificate.status,
                    reason=certificate.message, development_matrix=current, solver_result=certificate))
                continue
            validate_solution(current, certificate)
            probabilities = certificate.probabilities
            claim = "declared_action_set_numerical_certificate"
        elif method == "uniform":
            probabilities = tuple((s, 1. / len(matrix.strategy_ids)) for s in matrix.strategy_ids)
            basis = "protocol_uniform"
        else:
            if method == "coverage_aware_greedy":
                chosen = readiness.greedy_strategy_id
                if chosen is None:
                    unavailable.append(UnavailableMethod(method=method, status='unavailable',
                        reason='captured greedy team is not feasible under frozen protections'))
                    continue
                basis = "captured_selector"
            else:
                index = deterministic_id(matrix, clean=method == "clean_development", tolerance=spec.optimizer_tolerance)
                if index is None:
                    unavailable.append(UnavailableMethod(method=method, status='infeasible',
                        reason='no fixed strategy meets frozen development coverage floor'))
                    continue
                chosen = matrix.strategy_ids[index]
                if method == "clean_development":
                    basis = "development_clean"
            probabilities = tuple((s, float(s == chosen)) for s in matrix.strategy_ids)
        policies.append(ResearchPolicy(method=method, development_matrix=current, probabilities=probabilities,
            selection_basis=basis, optimality_claim=claim, certificate=certificate))
    return FrozenComparison(version="frozen_research_comparison_v1", specification_id=spec.specification_id,
        code_revision=actual_code_revision, manifest_id=spec.manifest.manifest_id,
        full_artifact=artifact, policies=tuple(policies), freeze_record=freeze_record, unavailable_methods=tuple(unavailable))


def validate_frozen(spec, frozen, *, actual_code_revision):
    spec = comparison_specification(spec)
    frozen = FrozenComparison.model_validate(frozen)
    require_ready(spec, actual_code_revision=actual_code_revision)
    if (frozen.specification_id != spec.specification_id or frozen.code_revision != spec.code_revision
            or frozen.manifest_id != spec.manifest.manifest_id or frozen.full_artifact.context != spec.context
            or frozen.full_artifact.contract != spec.contract):
        raise ValueError("frozen comparison is incompatible with specification")
    greedy = next((p for p in frozen.policies if p.method == "coverage_aware_greedy"), None)
    selected = greedy_strategy(spec, frozen.full_artifact.policy.strategies)
    if (greedy is not None and (selected is None or dict(greedy.probabilities).get(selected.strategy_id) != 1.)) or (greedy is None and selected is not None):
        raise ValueError("greedy aggregation differs from preregistered specification")
    report = require_ready(spec, actual_code_revision=actual_code_revision)
    if frozen.full_artifact.policy.matrix.attack_ids != tuple(a.attack_id for a in report.attacks):
        raise ValueError("frozen matrix attack columns differ from specification")
    if any(p.certificate is not None and p.certificate.tolerance != spec.optimizer_tolerance for p in frozen.policies):
        raise ValueError("frozen numerical tolerances differ from specification")
    return spec, frozen


class MethodResult(FrozenModel):
    method: str
    attack_metrics: tuple[tuple[str, Metrics], ...]
    clean_attack_id: str
    worst_case_expected_loss: float
    worst_case_attack_ids: tuple[str, ...]
    development_coverage: dict


class ComparisonResult(FrozenModel):
    run_kind: Literal["development_pilot", "frozen_final"]
    specification_id: str
    comparison_id: str
    manifest_id: str
    code_revision: str
    planning_category: str
    evidence_kind: str
    methods: tuple[MethodResult, ...]
    unavailable_methods: tuple[UnavailableMethod, ...] = ()


def comparison_examples(spec, role, final_partition=None):
    from app.game.offline.records import TrainingManifest, DatasetManifest
    if isinstance(spec.manifest, TrainingManifest) and role == 'final_test':
        if final_partition is None:
            raise ValueError('explicit separately released final partition required')
        final = spec.manifest.final_test_reservation.validate_payload(final_partition)
        DatasetManifest(version='released_research_comparison_v1', evidence_kind=spec.manifest.evidence_kind,
            partitions=(*spec.manifest.partitions, final))
        return final.examples
    if final_partition is not None:
        raise ValueError('final partition only accepted for training-only final evaluation')
    return spec.manifest.partition(role).examples


def _score(spec, frozen, role, actual_code_revision, final_partition=None):
    spec, frozen = validate_frozen(spec, frozen, actual_code_revision=actual_code_revision)
    readiness = require_ready(spec, actual_code_revision=actual_code_revision)
    examples = comparison_examples(spec, role, final_partition)
    # One common outcome cube; every declared example is retained for every row/action.
    outcomes = {(s.strategy_id, a.attack_id, e.example_id):
        replay(spec.context, s, a, spec.attacks, spec.contract, e)
        for s in frozen.full_artifact.policy.strategies for a in readiness.attacks
        for e in examples}
    methods = []
    for policy in frozen.policies:
        metrics = tuple((a.attack_id, summarize(tuple(
            (outcomes[s, a.attack_id, e.example_id], p) for s, p in policy.probabilities
            for e in examples), spec.context.loss_configuration)) for a in readiness.attacks)
        worst = max(m.mean_loss for _, m in metrics)
        methods.append(MethodResult(method=policy.method, attack_metrics=metrics,
            clean_attack_id=readiness.attacks[0].attack_id, worst_case_expected_loss=worst,
            worst_case_attack_ids=tuple(a for a, m in metrics if m.mean_loss == worst),
            development_coverage=policy.coverage_compliance))
    return ComparisonResult(run_kind="frozen_final" if role == "final_test" else "development_pilot",
        specification_id=spec.specification_id, comparison_id=frozen.comparison_id, manifest_id=spec.manifest.manifest_id,
        code_revision=actual_code_revision, planning_category=readiness.planning_category,
        evidence_kind=spec.manifest.evidence_kind, methods=tuple(methods), unavailable_methods=frozen.unavailable_methods)


def score_development_pilot(spec, frozen, *, actual_code_revision):
    return _score(spec, frozen, "development", actual_code_revision)


def score_frozen_final(spec, frozen, *, actual_code_revision, final_partition=None):
    """Separate explicit final-test entry; no selection, fitting or optimization."""
    return _score(spec, frozen, "final_test", actual_code_revision, final_partition)
