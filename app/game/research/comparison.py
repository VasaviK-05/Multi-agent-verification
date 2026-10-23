"""Development-only comparisons and explicitly frozen final-test replay.

Research distributions are not deployable Policy objects. Restricted games retain
their exact row definitions and numerical certificate without weakening Stage 1.
"""

import math
from typing import Literal

from pydantic import StrictFloat, model_validator

from app.game.artifacts import PolicyArtifact
from app.game.dependencies import FrozenModel, identifier
from app.game.models import PayoffMatrix, SolverResult, content_id
from app.game.offline.evaluation import Evaluation, Metrics, construct_payoffs, summarize
from app.game.offline.replay import replay
from app.game.research.readiness import greedy_strategy, require_ready
from app.game.research.specification import ExperimentSpecification
from app.game.solver import solve_minimax, validate_solution

METHODS = ("full_minimax", "uniform", "deterministic_minimax", "clean_development",
           "fixed_reputation_weighted", "fixed_dependency_group", "coverage_aware_greedy")


def restricted_matrix(matrix, aggregation):
    indices = tuple(i for i, s in enumerate(matrix.strategy_definitions) if s.aggregation == aggregation)
    return PayoffMatrix(strategy_ids=tuple(matrix.strategy_ids[i] for i in indices),
        strategy_definitions=tuple(matrix.strategy_definitions[i] for i in indices),
        attack_ids=matrix.attack_ids, values=tuple(matrix.values[i] for i in indices),
        compatibility_id=matrix.compatibility_id)


def deterministic_id(matrix, *, clean):
    # First column is checked against the enumerated clean action at preparation.
    objective = (lambda i: matrix.values[i][0]) if clean else (lambda i: max(matrix.values[i]))
    return min(range(len(matrix.strategy_ids)), key=lambda i: (objective(i), matrix.strategy_ids[i]))


class ResearchPolicy(FrozenModel):
    method: Literal["full_minimax", "uniform", "deterministic_minimax", "clean_development",
                    "fixed_reputation_weighted", "fixed_dependency_group", "coverage_aware_greedy"]
    development_matrix: PayoffMatrix
    probabilities: tuple[tuple[str, StrictFloat], ...]
    selection_basis: Literal["development_minimax", "development_clean", "protocol_uniform", "captured_selector"]
    optimality_claim: Literal["none", "full_game_numerical_certificate", "declared_action_set_numerical_certificate"]
    certificate: SolverResult | None

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

    @model_validator(mode="after")
    def bind_policies(self):
        identifier(self.freeze_record)
        if tuple(p.method for p in self.policies) != METHODS:
            raise ValueError("complete comparison roster required exactly once")
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
                selected = deterministic_id(matrix, clean=method == "clean_development")
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
    spec = ExperimentSpecification.model_validate(spec)
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
    actual = construct_payoffs(spec.context, spec.manifest, spec.contract, spec.attacks)
    if development != actual or artifact.policy.matrix != development.matrix:
        raise ValueError("development evaluation/artifact differs from complete declared replay")
    matrix = development.matrix
    if matrix.attack_ids != tuple(a.attack_id for a in readiness.attacks) or readiness.attacks[0].kind != "clean":
        raise ValueError("fixed attack columns differ")
    policies = []
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
            validate_solution(current, certificate)  # Failure is explicit, never an arbitrary policy.
            probabilities = certificate.probabilities
            claim = "declared_action_set_numerical_certificate"
        elif method == "uniform":
            probabilities = tuple((s, 1. / len(matrix.strategy_ids)) for s in matrix.strategy_ids)
            basis = "protocol_uniform"
        else:
            if method == "coverage_aware_greedy":
                chosen = readiness.greedy_strategy_id
                basis = "captured_selector"
            else:
                chosen = matrix.strategy_ids[deterministic_id(matrix, clean=method == "clean_development")]
                if method == "clean_development":
                    basis = "development_clean"
            probabilities = tuple((s, float(s == chosen)) for s in matrix.strategy_ids)
        policies.append(ResearchPolicy(method=method, development_matrix=current, probabilities=probabilities,
            selection_basis=basis, optimality_claim=claim, certificate=certificate))
    return FrozenComparison(version="frozen_research_comparison_v1", specification_id=spec.specification_id,
        code_revision=actual_code_revision, manifest_id=spec.manifest.manifest_id,
        full_artifact=artifact, policies=tuple(policies), freeze_record=freeze_record)


def validate_frozen(spec, frozen, *, actual_code_revision):
    spec = ExperimentSpecification.model_validate(spec)
    frozen = FrozenComparison.model_validate(frozen)
    require_ready(spec, actual_code_revision=actual_code_revision)
    if (frozen.specification_id != spec.specification_id or frozen.code_revision != spec.code_revision
            or frozen.manifest_id != spec.manifest.manifest_id or frozen.full_artifact.context != spec.context
            or frozen.full_artifact.contract != spec.contract):
        raise ValueError("frozen comparison is incompatible with specification")
    greedy = next(p for p in frozen.policies if p.method == "coverage_aware_greedy")
    selected = greedy_strategy(spec, frozen.full_artifact.policy.strategies)
    if selected is None or dict(greedy.probabilities).get(selected.strategy_id) != 1.:
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


class ComparisonResult(FrozenModel):
    run_kind: Literal["development_pilot", "frozen_final"]
    specification_id: str
    comparison_id: str
    manifest_id: str
    code_revision: str
    planning_category: str
    evidence_kind: str
    methods: tuple[MethodResult, ...]


def _score(spec, frozen, role, actual_code_revision):
    spec, frozen = validate_frozen(spec, frozen, actual_code_revision=actual_code_revision)
    readiness = require_ready(spec, actual_code_revision=actual_code_revision)
    # One common outcome cube; every declared example is retained for every row/action.
    outcomes = {(s.strategy_id, a.attack_id, e.example_id):
        replay(spec.context, s, a, spec.attacks, spec.contract, e)
        for s in frozen.full_artifact.policy.strategies for a in readiness.attacks
        for e in spec.manifest.partition(role).examples}
    methods = []
    for policy in frozen.policies:
        metrics = tuple((a.attack_id, summarize(tuple(
            (outcomes[s, a.attack_id, e.example_id], p) for s, p in policy.probabilities
            for e in spec.manifest.partition(role).examples), spec.context.loss_configuration)) for a in readiness.attacks)
        worst = max(m.mean_loss for _, m in metrics)
        methods.append(MethodResult(method=policy.method, attack_metrics=metrics,
            clean_attack_id=readiness.attacks[0].attack_id, worst_case_expected_loss=worst,
            worst_case_attack_ids=tuple(a for a, m in metrics if m.mean_loss == worst)))
    return ComparisonResult(run_kind="frozen_final" if role == "final_test" else "development_pilot",
        specification_id=spec.specification_id, comparison_id=frozen.comparison_id, manifest_id=spec.manifest.manifest_id,
        code_revision=actual_code_revision, planning_category=readiness.planning_category,
        evidence_kind=spec.manifest.evidence_kind, methods=tuple(methods))


def score_development_pilot(spec, frozen, *, actual_code_revision):
    return _score(spec, frozen, "development", actual_code_revision)


def score_frozen_final(spec, frozen, *, actual_code_revision):
    """Separate explicit final-test entry; no selection, fitting or optimization."""
    return _score(spec, frozen, "final_test", actual_code_revision)
