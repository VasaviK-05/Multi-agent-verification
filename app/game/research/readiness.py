"""Pure input readiness; no replay, optimization, scoring, dispatch or persistence."""

from app.game.dependencies import FrozenModel
from app.game.models import Strategy
from app.game.offline.attacks import Attack, AdapterIncompatibility, adapter_incompatibility, enumerate_attacks
from app.game.offline.evaluation import bind_evaluation
from app.game.offline.replay import category_id
from app.game.strategies import enumerate_strategies
from app.game.research.specification import ExperimentSpecification

EVIDENCE_FAILURES = (
    "tests/test_adaptive_pipeline.py::test_actual_evidence_output_contract_is_consumed_without_models[probabilities0-passed]",
    "tests/test_adaptive_pipeline.py::test_actual_evidence_output_contract_is_consumed_without_models[probabilities1-failed]",
    "tests/test_adaptive_pipeline.py::test_actual_conflicting_evidence_cannot_cover_factual_request",
)
SUPPORTED_ACHIEVED = frozenset({"arithmetic", "direct_fact"})


def greedy_strategy(spec, strategies):
    """Actual captured selector greedy team, admitted only if independently feasible."""
    team = tuple(sorted(spec.context.plan.initial_selected))
    return next((s for s in strategies if s.verifiers == team and s.aggregation == spec.greedy_aggregation), None)


class AdapterReadinessBlocker(AdapterIncompatibility):
    code: str
    partition: str
    example_id: str


class ResourceReadinessBlocker(FrozenModel):
    partition: str
    example_id: str
    verifier_name: str
    reason: str


class ReadinessReport(FrozenModel):
    ready: bool
    specification_id: str
    code_revision: str
    evidence_kind: str
    planning_category: str
    blockers: tuple[str, ...]
    adapter_blockers: tuple[AdapterReadinessBlocker, ...]
    unsupported_achieved: tuple[str, ...]
    strategies: tuple[Strategy, ...]
    attacks: tuple[Attack, ...]
    greedy_strategy_id: str | None
    evidence_failures: tuple[str, ...]
    resource_blockers: tuple[ResourceReadinessBlocker, ...] = ()


def check_readiness(spec, *, actual_code_revision):
    spec = ExperimentSpecification.model_validate(spec)
    context, manifest = spec.context, spec.manifest
    blockers = []
    adapter_blockers = []
    resource_blockers = []
    if context.pooling_contract_json is not None:
        blockers.append("pooled_context_requires_explicit_multi_domain_workflow")
    if manifest.evidence_kind == "empirical" and spec.contract.resource_manifest is None:
        blockers.append("empirical_study_requires_resource_bound_execution_v2")
    if actual_code_revision != spec.code_revision:
        blockers.append("code_revision_mismatch")
    try:
        bound = bind_evaluation(context, manifest, spec.contract, spec.attacks)
        if bound.compatibility_id != context.compatibility_id or context.execution_contract_json is None:
            blockers.append("explicit_bound_context_required")
    except ValueError as exc:
        blockers.append("history_or_evaluation_binding_incompatible:" + str(exc))
    required = set(context.plan.requirements.requirements) | set(context.plan.requirements.unsupported)
    unsupported = tuple(sorted(required - SUPPORTED_ACHIEVED))
    if unsupported:
        blockers.append("unsupported_achieved_coverage:" + ",".join(unsupported))
    # Conservative gate: evidence-bearing studies need a separately reviewed repair.
    # A user-provided boolean cannot attest that these known defects are fixed.
    evidence = bool(required & {"direct_fact", "evidence_retrieval"}) or any(
        a.adapter == "evidence_v1" for p in manifest.partitions for e in p.examples for a in e.attempts)
    if evidence:
        blockers.append("known_evidence_contract_failures_require_repair_or_explicit_scope_revision")
    names = {c.verifier_name for c in context.plan.candidates}
    category = category_id(context)
    for part in manifest.partitions:
        for example in part.examples:
            prefix = f"{part.role}/{example.example_id}:"
            for attempt in example.attempts:
                if spec.contract.resource_manifest is not None:
                    from app.game.resource_provenance import VerifierResources
                    try:
                        if attempt.observed_resources_json is None:
                            raise ValueError("missing observed resources")
                        observation = VerifierResources.model_validate_json(attempt.observed_resources_json, strict=True)
                        spec.contract.resource_manifest.require_observation(observation)
                    except ValueError as exc:
                        resource_blockers.append(ResourceReadinessBlocker(partition=part.role,
                            example_id=example.example_id, verifier_name=attempt.verifier_name, reason=str(exc)))
                        blockers.append(prefix + attempt.verifier_name + ":resource_provenance_incompatible")
                incompatible = adapter_incompatibility(attempt)
                if incompatible is not None:
                    adapter_blockers.append(AdapterReadinessBlocker(**incompatible.model_dump(),
                        code="incompatible_attack_adapter", partition=part.role, example_id=example.example_id))
                    blockers.append(prefix + attempt.verifier_name + ":incompatible_attack_adapter")
            if {a.verifier_name for a in example.attempts} != names or any(a.state == "missing" for a in example.attempts):
                blockers.append(prefix + "incomplete_candidate_recordings")
            if example.execution_configuration_id != spec.contract.execution_configuration_id:
                blockers.append(prefix + "recording_configuration_mismatch")
            if example.domain != context.plan.domain or example.planning_category != category:
                blockers.append(prefix + "incompatible_planning_category")
            if bool(example.reference and example.reference.strip()) != context.plan.reference_available:
                blockers.append(prefix + "reference_prerequisite_mismatch")
    enumeration = enumerate_strategies(context)
    if not enumeration.strategies:
        blockers.append("no_feasible_strategy:" + str(tuple(r.reasons for r in enumeration.rejected)))
    greedy = greedy_strategy(spec, enumeration.strategies)
    if greedy is None:
        blockers.append("captured_coverage_aware_greedy_team_is_not_feasible")
    if context.aggregation_versions != (("dependency_group", "groups_v1"), ("reputation_weighted", "log_odds_v1")):
        blockers.append("unsupported_aggregation_versions")
    return ReadinessReport(ready=not blockers, specification_id=spec.specification_id,
        code_revision=actual_code_revision, evidence_kind=manifest.evidence_kind, planning_category=category,
        blockers=tuple(blockers), adapter_blockers=tuple(adapter_blockers),
        unsupported_achieved=unsupported, strategies=enumeration.strategies,
        attacks=enumerate_attacks(context.dependencies, spec.attacks),
        greedy_strategy_id=greedy.strategy_id if greedy else None, evidence_failures=EVIDENCE_FAILURES,
        resource_blockers=tuple(resource_blockers))


def require_ready(spec, *, actual_code_revision):
    report = check_readiness(spec, actual_code_revision=actual_code_revision)
    if not report.ready:
        raise ValueError("experiment not ready: " + "; ".join(report.blockers))
    return report
