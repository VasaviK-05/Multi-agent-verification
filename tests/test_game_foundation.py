"""Synthetic matrices are test fixtures, never empirical research results."""

from dataclasses import asdict, replace
import json
import math
import random
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from app.analysis.models import QuestionAnalysis, QuestionResearchContext
from app.game.dependencies import Dependency, DependencyRegistry
from app.game.models import (LossConfiguration, PayoffMatrix, PayoffProvenance, PlanningContext,
                             canonical_json, capture_context)
from app.game.policy import build_policy, sample_policy, validate_policy
from app.game.solver import OPTIMALITY_BASIS, solve_minimax, validate_solution
from app.game.strategies import enumerate_strategies
from app.selection.capabilities import CapabilityDescriptor
from app.selection.verifier_selector import VerifierSelector
from app.reputation.reputation_manager import ReputationManager
from tests.test_verifier_selector import StubVerifier


def analysis(labels=("arithmetic",)):
    return QuestionAnalysis("general", "easy", .1, domain_status="known",
        verification_types=list(labels), research_context=QuestionResearchContext(
            "question_context_v1", list(labels), {s: 1. for s in labels}, bool(labels),
            None, "known", "heuristic", "rubric_v1"))


def make_context(*, labels=("arithmetic",), budget=10, minimum=1, capabilities=None,
                 names=("a", "b", "c", "d"), source=None, **overrides):
    selector = source or VerifierSelector(verifiers=[StubVerifier(n) for n in names],
        difficulty_range={"easy": (minimum, minimum), "hard": (minimum, minimum)}, capabilities=capabilities or {
            n: CapabilityDescriptor(("arithmetic",)) for n in names})
    names = tuple(row.verifier_name for row in selector.plan(analysis(labels)).candidates)
    configuration = dict(attempt_costs=[(n, 1.) for n in names], budget=budget,
        cost_units="estimated_attempt_units", dependencies=DependencyRegistry(version="deps_v1", unresolved=names),
        loss_configuration=LossConfiguration(version="explicit-test-loss-v1", false_accept=1., false_reject=1.,
            uncertain=.2, resource_weight=.1, cost_units="estimated_attempt_units"),
        aggregation_versions=[("reputation_weighted", "log_odds_v1"), ("dependency_group", "groups_v1")],
        provenance=PayoffProvenance(attack_specification="single_group_v1", history_dataset="history-v1",
            development_dataset="development-v1", final_test_dataset="test-v1", matrix_version="matrix-v1",
            loss_configuration="explicit-test-loss-v1", category="general", evidence_kind="synthetic_test_fixture"))
    configuration.update(overrides)
    a = analysis(labels)
    if minimum == 1 and source is None:
        a.difficulty, a.difficulty_score = "hard", .8
    return capture_context(selector, a, **configuration)


def matrix(values=((1, -1), (-1, 1)), **overrides):
    data = dict(strategy_ids=("first", "second"), attack_ids=("left", "right"),
                values=values, compatibility_id="test-fixture")
    data.update(overrides)
    return PayoffMatrix(**data)


def policy_fixture(context=None):
    context = context or make_context(names=("a",))
    strategies = enumerate_strategies(context).strategies
    payoff = matrix(strategy_ids=tuple(s.strategy_id for s in strategies),
                    strategy_definitions=strategies,
                    compatibility_id=context.compatibility_id)
    return context, build_policy(context, payoff)


def test_snapshot_detaches_nested_inputs_and_preserves_full_statistics():
    selector = VerifierSelector(verifiers=[StubVerifier("a")],
        difficulty_range={"easy": (1, 1)}, capabilities={"a": CapabilityDescriptor(("arithmetic",))})
    calls = []
    original = selector.reputation_manager.statistics_batch
    selector.reputation_manager.statistics_batch = lambda pairs: (calls.append(pairs) or original(pairs))
    a = analysis()
    config = make_context(names=("a",)).model_dump()
    config.pop("selection_json")
    config.pop("analyzer_provenance")
    config["attempt_costs"] = [list(pair) for pair in config["attempt_costs"]]
    config["aggregation_versions"] = [list(pair) for pair in config["aggregation_versions"]]
    context = capture_context(selector, a, **config)
    assert len(calls) == 1
    before = context.model_dump_json(), context.compatibility_id
    a.research_context.verification_requirements.clear()
    a.research_context.requirement_weights.clear()
    selector.reputation_manager.update_reputation("a", "general", True)
    config["attempt_costs"][0][1] = 1000
    config["aggregation_versions"][0][1] = "changed"
    config["dependencies"]["version"] = "changed"
    view = context.plan
    object.__setattr__(view.requirements, "requirements", ["changed"])
    assert (context.model_dump_json(), context.compatibility_id) == before
    assert context.plan.reputation_statistics[0].observation_count == 0
    assert context.plan.reputation_statistics[0].cold_start
    assert make_context(source=selector).reputation_snapshot_id != context.reputation_snapshot_id
    with pytest.raises(ValidationError):
        context.budget = 4


def test_equivalent_requirement_sets_have_same_signature_and_versions_are_preserved():
    first = make_context(labels=("arithmetic", "consistency"))
    second = make_context(labels=("consistency", "arithmetic"))
    assert first.requirement_signature == second.requirement_signature
    assert first.plan.analysis_method == "heuristic"
    assert first.plan.context_version == "question_context_v1"
    assert first.plan.scoring_version == "rubric_v1"
    assert PlanningContext.model_validate_json(first.model_dump_json()).compatibility_id == first.compatibility_id


@pytest.mark.parametrize("kind", ["missing", "unknown", "invalid", "unsupported"])
def test_requirement_uncertainty_is_not_an_empty_feasible_obligation(kind):
    context = make_context()
    selector = VerifierSelector(verifiers=[StubVerifier("a")])
    a = analysis()
    if kind == "missing":
        a.research_context = None
        a.verification_types = []
    elif kind == "unknown":
        a = analysis(())
    elif kind == "invalid":
        a.research_context.context_version = "future"
    else:
        a = analysis(("arithmetic", "unrecognized"))
    config = make_context(names=("a",)).model_dump()
    config.pop("selection_json")
    config.pop("analyzer_provenance")
    captured = capture_context(selector, a, **config)
    result = enumerate_strategies(captured)
    assert result.status == "no_feasible_strategy" and not result.strategies
    assert result.rejected[0].reasons
    assert captured.requirement_signature != context.requirement_signature
    if kind == "invalid":
        assert captured.plan.requirements.errors
        assert dict(captured.analyzer_provenance)["context_version"] == "future"
    if kind == "missing":
        assert captured.requirements_missing
        assert "requirements_missing" in result.rejected[0].reasons
    if kind == "unsupported":
        assert captured.plan.requirements.unsupported == ("unrecognized",)


def test_dependencies_overlap_unknowns_order_and_bridge_projection():
    deps = [Dependency(resource_id="index", compromise_pathway="trusted corrupted evidence", verifiers=["a", "b"]),
            Dependency(resource_id="model", compromise_pathway="shared model outputs", verifiers=["b", "c"])]
    registry = DependencyRegistry(version="v1", dependencies=deps, unresolved=["d", "e"])
    groups = registry.groups(["e", "a", "c", "d"])
    assert {g.verifiers for g in groups} == {("a", "c"), ("d", "e")}
    reordered = DependencyRegistry(version="v1", dependencies=list(reversed(deps)), unresolved=["e", "d"])
    assert registry == reordered
    assert groups == reordered.groups(["d", "c", "a", "e"])
    assert registry.groups(["a"])[0].group_id == next(g.group_id for g in groups if "a" in g.verifiers)
    deps.clear()
    assert len(registry.dependencies) == 2
    with pytest.raises(ValueError, match="explicit"):
        registry.groups(["unregistered"])


def test_known_and_unknown_dependency_overlap_merges_conservatively():
    registry = DependencyRegistry(version="v1", unresolved=["a", "c"], dependencies=[
        Dependency(resource_id="api", compromise_pathway="manipulated API", verifiers=["a", "b"])])
    assert registry.groups(["a", "b", "c"])[0].verifiers == ("a", "b", "c")
    assert len(registry.groups(["a", "b", "c"])) == 1


def test_maximum_enumeration_and_constraints_are_independent():
    context = make_context()
    result = enumerate_strategies(context)
    assert len(result.strategies) == 30
    assert len({s.strategy_id for s in result.strategies}) == 30
    constrained = make_context(minimum=2, budget=2, capabilities={
        "a": CapabilityDescriptor(("arithmetic",)), "b": CapabilityDescriptor(),
        "c": CapabilityDescriptor(), "d": CapabilityDescriptor(readiness="unavailable", unavailable_reason="disabled")})
    result = enumerate_strategies(constrained)
    assert {s.verifiers for s in result.strategies} == {("a", "b"), ("a", "c")}
    reasons = {reason for row in result.rejected for reason in row.reasons}
    assert reasons == {"minimum_participant_count", "expected_coverage", "budget"}
    assert result.exclusions == (("d", "disabled"),)
    assert enumerate_strategies(make_context(budget=0)).status == "no_feasible_strategy"
    assert enumerate_strategies(make_context(minimum=5)).status == "no_feasible_strategy"


def test_existing_execution_floor_is_preserved_for_easy_questions():
    selector = VerifierSelector(verifiers=[StubVerifier("a")],
        difficulty_range={"easy": (1, 1)}, capabilities={"a": CapabilityDescriptor(("arithmetic",))})
    context = make_context(source=selector)
    assert context.plan.minimum_count == 1
    assert context.minimum_participant_count == 2
    assert enumerate_strategies(context).status == "no_feasible_strategy"


@pytest.mark.parametrize("prior", [1e308, 1e-309])
def test_snapshot_preserves_existing_extreme_finite_prior_support(prior):
    selector = VerifierSelector(verifiers=[StubVerifier("a")],
        reputation_manager=ReputationManager(prior, prior))
    context = make_context(source=selector)
    assert context.plan.reputation_statistics[0].posterior_mean == .5
    assert context.plan.reputation_statistics[0].alpha == prior


def test_lazy_default_construction_and_reference_prerequisite(monkeypatch):
    import app.selection.verifier_selector as module
    monkeypatch.setattr(module, "_build_default_verifier", lambda name: pytest.fail("constructed during planning"))
    selector = VerifierSelector()
    context = make_context(source=selector)
    result = enumerate_strategies(context)
    assert "semantic" in dict(result.exclusions)
    assert all("semantic" not in s.verifiers for s in result.strategies)
    assert selector._cache == {}


@pytest.mark.parametrize("values,expected,value", [
    (((1, -1), (-1, 1)), (.5, .5), 0),
    (((0, 0), (1, 2)), (1, 0), 0),
    (((-4, -2), (-1, -3)), (0.5, 0.5), -2.5),
])
def test_minimax_mixed_pure_negative_and_diagnostics(values, expected, value):
    result = solve_minimax(matrix(values))
    assert result.status == "optimal"
    assert tuple(p for _, p in result.probabilities) == pytest.approx(expected)
    assert result.game_value == pytest.approx(value)
    assert result.normalization_residual == pytest.approx(0)
    assert result.minimum_probability >= 0
    assert min(r for _, r in result.constraint_residuals) >= -result.tolerance
    assert max(loss for _, loss in result.attack_losses) == pytest.approx(value)
    assert result.worst_case_attacks


@pytest.mark.parametrize("override", [
    {"strategy_ids": ()}, {"attack_ids": ("x", "x")}, {"strategy_ids": ("x", "x")},
    {"values": ((1,),)}, {"values": ((math.inf, 0), (0, 1))},
    {"values": ((math.nan, 0), (0, 1))}, {"attack_ids": (" ", "ok")},
    {"values": ((True, 0), (0, 1))}, {"values": (("1", 0), (0, 1))},
])
def test_malformed_matrices_rejected(override):
    with pytest.raises(ValueError):
        matrix(**override)


@pytest.mark.parametrize("failure", ["status", "exception", "nonfinite", "negative", "constraint", "sum"])
def test_solver_failure_never_returns_an_optimal_policy(monkeypatch, failure):
    import app.game.solver as module
    if failure == "exception":
        def broken(*args, **kwargs):
            raise RuntimeError("test failure")
        monkeypatch.setattr(module, "linprog", broken)
    else:
        x = {"nonfinite": [math.nan, .5, 0], "negative": [-.1, 1.1, 0],
             "constraint": [1, 0, 0], "sum": [.4, .4, 0]}.get(failure, [.5, .5, 0])
        monkeypatch.setattr(module, "linprog", lambda *a, **kw: SimpleNamespace(
            success=failure != "status", status=2 if failure == "status" else 0, message="fixture", x=x))
    result = solve_minimax(matrix())
    assert result.status == "solver_failure"
    assert not result.probabilities and result.game_value is None


def test_roundoff_cleanup_validates_returned_distribution(monkeypatch):
    import app.game.solver as module
    monkeypatch.setattr(module, "linprog", lambda *a, **kw: SimpleNamespace(
        success=True, status=0, message="fixture", x=[-1e-12, 1+1e-12, 2],
        ineqlin=SimpleNamespace(marginals=[-1., 0.])))
    result = solve_minimax(matrix(((3, 3), (2, 2))))
    assert result.status == "optimal"
    assert result.probabilities == (("first", 0), ("second", 1))
    assert result.normalization_residual == 0


def test_compatible_policy_reproducible_sampling_and_content_ids():
    context, policy = policy_fixture()
    first = sample_policy(policy, context, rng=random.Random(41))
    assert first == sample_policy(policy, context, rng=random.Random(41))
    assert first.policy_id == policy.policy_id and first.selection_status == "selected"
    assert first.estimated_cost <= first.budget
    assert first.reputation_snapshot_id == context.reputation_snapshot_id
    restored = type(policy).model_validate_json(policy.model_dump_json())
    assert restored.policy_id == policy.policy_id
    assert sample_policy(restored, context, rng=random.Random(41)) == first
    draws = [sample_policy(policy, context, rng=random.Random(seed)).strategy_id for seed in range(12)]
    assert len(set(draws)) == 2


@pytest.mark.parametrize("field", ["budget", "costs", "units", "dependencies", "aggregations", "provenance",
                                   "reputation", "availability", "requirements", "minimum", "analyzer"])
def test_policy_compatibility_rejects_every_changed_binding(field):
    context, policy = policy_fixture()
    data = context.model_dump()
    if field == "budget":
        data["budget"] = 20
    elif field == "costs":
        data["attempt_costs"] = [("a", 2)]
    elif field == "units":
        data["cost_units"] = "other_units"
        data["loss_configuration"]["cost_units"] = "other_units"
    elif field == "dependencies":
        data["dependencies"]["version"] = "deps_v2"
    elif field == "aggregations":
        data["aggregation_versions"] = [("reputation_weighted", "v2"), ("dependency_group", "v1")]
    elif field == "provenance":
        data["provenance"]["development_dataset"] = "development-v2"
    else:
        plan = context.plan
        if field == "reputation":
            stats = plan.reputation_statistics[0]
            changed = replace(stats, alpha=2, successes=1, observation_count=1, cold_start=False,
                              posterior_mean=2/3, posterior_variance=1/18)
            plan = replace(plan, reputation_statistics=(changed,))
            candidate = replace(plan.candidates[0], reputation=round(2/3, 6), observation_count=1, cold_start=False)
            plan = replace(plan, candidates=(candidate,))
        elif field == "availability":
            candidate = replace(plan.candidates[0], eligible=False, exclusion_reason="disabled")
            plan = replace(plan, candidates=(candidate,))
        elif field == "requirements":
            plan = replace(plan, requirements=replace(plan.requirements, requirements=("consistency",),
                                                       weights=(("consistency", 1.),)))
        elif field == "minimum":
            plan = replace(plan, minimum_count=2)
        else:
            plan = replace(plan, analysis_method="new_method")
        data["selection_json"] = canonical_json(asdict(plan))
    changed = PlanningContext(**data)
    with pytest.raises(ValueError, match="incompatible"):
        sample_policy(policy, changed, rng=random.Random(1))


def test_reject_missing_strategies_forged_distribution_and_solver_failure(monkeypatch):
    context, policy = policy_fixture()
    with pytest.raises(ValueError, match="strategy"):
        validate_policy(policy.model_copy(update={"strategies": policy.strategies[:1]}), context)
    forged = policy.solution.model_copy(update={"probabilities": tuple((s.strategy_id, float(i == 0))
                                                                      for i, s in enumerate(policy.strategies))})
    with pytest.raises(ValueError, match="not minimax"):
        validate_policy(policy.model_copy(update={"solution": forged}), context)
    import app.game.policy as module
    monkeypatch.setattr(module, "solve_minimax", lambda *a, **kw: policy.solution.model_copy(
        update={"status": "solver_failure", "message": "fixture"}))
    with pytest.raises(ValueError, match="cannot build policy"):
        build_policy(context, policy.matrix)


@pytest.mark.parametrize("override", [{"budget": -1}, {"budget": math.inf},
    {"budget": True}, {"attempt_costs": [("a", -1)]}, {"attempt_costs": []}, {"aggregation_versions": []}])
def test_invalid_context_configuration_rejected(override):
    with pytest.raises(ValueError):
        make_context(names=("a",), **override)


@pytest.mark.parametrize("field", ["attack_specification", "history_dataset", "final_test_dataset",
                                   "matrix_version", "category", "evidence_kind"])
def test_remaining_payoff_provenance_bindings_reject_changed_policies(field):
    context, policy = policy_fixture()
    data = context.model_dump()
    if field == "category":
        data["provenance"].update(category="pooled-general", category_kind="pooled")
    elif field == "evidence_kind":
        data["provenance"][field] = "empirical"
    else:
        data["provenance"][field] += "-changed"
    with pytest.raises(ValueError, match="incompatible"):
        validate_policy(policy, PlanningContext(**data))


def test_loss_units_and_dataset_role_conflicts_are_rejected():
    context = make_context()
    data = context.model_dump()
    data["loss_configuration"]["cost_units"] = "other"
    with pytest.raises(ValueError, match="units"):
        PlanningContext(**data)
    data = context.model_dump()
    data["provenance"]["final_test_dataset"] = data["provenance"]["development_dataset"]
    with pytest.raises(ValueError, match="distinct"):
        PlanningContext(**data)


def test_zero_weight_obligations_still_require_expected_coverage():
    selector = VerifierSelector(verifiers=[StubVerifier("a"), StubVerifier("b")],
        capabilities={"a": CapabilityDescriptor(("arithmetic",)), "b": CapabilityDescriptor(("arithmetic",))})
    a = analysis(("arithmetic", "consistency"))
    a.research_context.requirement_weights = {"arithmetic": 1., "consistency": 0.}
    data = make_context(names=("a", "b")).model_dump()
    data.pop("selection_json")
    data.pop("analyzer_provenance")
    context = capture_context(selector, a, **data)
    result = enumerate_strategies(context)
    assert result.status == "no_feasible_strategy"
    assert all("expected_coverage" in row.reasons for row in result.rejected)


def test_nested_unchecked_models_are_revalidated_detached_and_frozen():
    original = make_context()
    names = ["a", "b", "c", "d"]
    registry = original.dependencies.model_copy(update={"unresolved": names})
    config = original.model_dump()
    config["dependencies"] = registry
    captured = PlanningContext(**config)
    before = captured.compatibility_id
    names.clear()
    assert captured.dependencies.unresolved == ("a", "b", "c", "d")
    assert captured.compatibility_id == before
    assert captured.dependencies is not registry
    affected = ["a", "b", "c", "d"]
    resource = Dependency(resource_id="test-resource", compromise_pathway="fixture pathway",
                          verifiers=affected).model_copy(update={"verifiers": affected})
    unchecked_registry = registry.model_copy(update={"dependencies": (resource,), "unresolved": ()})
    detached = PlanningContext(**(config | {"dependencies": unchecked_registry}))
    affected.clear()
    assert detached.dependencies.dependencies[0].verifiers == ("a", "b", "c", "d")
    with pytest.raises(ValueError):
        PlanningContext(**(config | {"loss_configuration": original.loss_configuration.model_copy(
            update={"uncertain": math.nan})}))
    with pytest.raises(ValueError):
        enumerate_strategies(original.model_copy(update={"budget": -1}))


@pytest.mark.parametrize("field,value", [
    ("reputation", 1.1), ("reputation", math.nan), ("cost", -1), ("latency", math.inf),
    ("observation_count", -1), ("observation_count", True), ("cold_start", False),
    ("registration_order", -1), ("prerequisite_status", "invented"),
])
def test_imported_candidate_snapshot_rejects_invalid_numbers_counts_and_states(field, value):
    context = make_context()
    data = context.model_dump()
    plan = json.loads(data["selection_json"])
    plan["candidates"][0][field] = value
    data["selection_json"] = json.dumps(plan)
    with pytest.raises(ValueError):
        PlanningContext(**data)


@pytest.mark.parametrize("field,value", [
    ("alpha", 0), ("beta", math.inf), ("successes", -1), ("successes", 1.5),
    ("observation_count", True), ("cold_start", False), ("posterior_mean", 1.5),
    ("posterior_variance", .3), ("posterior_variance", math.nan),
])
def test_imported_full_statistics_reject_invalid_or_inconsistent_values(field, value):
    context = make_context()
    data = context.model_dump()
    plan = json.loads(data["selection_json"])
    plan["reputation_statistics"][0][field] = value
    data["selection_json"] = json.dumps(plan)
    with pytest.raises(ValueError):
        PlanningContext(**data)


def test_configuration_order_does_not_change_semantic_compatibility_or_strategies():
    first = VerifierSelector(verifiers=[StubVerifier(n) for n in ("a", "b")], capabilities={
        n: CapabilityDescriptor(("arithmetic", "consistency"), limitations=("one", "two")) for n in ("a", "b")})
    second = VerifierSelector(verifiers=[StubVerifier(n) for n in ("b", "a")], capabilities={
        n: CapabilityDescriptor(("consistency", "arithmetic"), limitations=("two", "one")) for n in ("b", "a")})
    left, right = make_context(source=first), make_context(source=second)
    assert left.compatibility_id == right.compatibility_id
    assert left.reputation_snapshot_id == right.reputation_snapshot_id
    assert enumerate_strategies(left).strategies == enumerate_strategies(right).strategies


def test_negative_zero_requirement_weight_is_canonical():
    context = make_context(labels=("arithmetic", "consistency"))
    plan = context.plan
    positive = replace(plan.requirements, weights=(("arithmetic", 1.), ("consistency", 0.)))
    negative = replace(positive, weights=(("arithmetic", 1.), ("consistency", -0.)))
    data = context.model_dump()
    left = PlanningContext(**(data | {"selection_json": canonical_json(asdict(replace(plan, requirements=positive)))}))
    right = PlanningContext(**(data | {"selection_json": canonical_json(asdict(replace(plan, requirements=negative)))}))
    assert left.requirement_signature == right.requirement_signature


def test_matrix_requires_explicit_exact_row_definitions_for_policy_building():
    context, policy = policy_fixture()
    with pytest.raises(ValueError, match="row definitions"):
        build_policy(context, policy.matrix.model_copy(update={"strategy_definitions": ()}))
    changed = policy.strategies[0].model_copy(update={"estimated_cost": 2.})
    with pytest.raises(ValueError, match="row definitions"):
        build_policy(context, policy.matrix.model_copy(update={"strategy_definitions": (changed, policy.strategies[1])}))
    for update in ({"verifiers": ("different",)}, {"aggregation": "dependency_group"}):
        forged = policy.strategies[0].model_copy(update=update)
        with pytest.raises(ValueError, match="strategy ID"):
            validate_policy(policy.model_copy(update={"strategies": (forged, policy.strategies[1])}), context)


@pytest.mark.parametrize("pure_index", [0, 1])
def test_zero_mass_and_sampling_boundaries_are_reproducible(pure_index):
    context, policy = policy_fixture()
    for draw, expected in [(0., 0), (math.nextafter(.5, 0), 0), (.5, 1),
                           (math.nextafter(1., 0), 1)]:
        decision = sample_policy(policy, context, rng=SimpleNamespace(random=lambda: draw))
        assert decision.strategy_id == policy.strategies[expected].strategy_id
    pure_values = ((0., 0.), (1., 2.)) if pure_index == 0 else ((1., 2.), (0., 0.))
    payoff = policy.matrix.model_copy(update={"values": pure_values})
    pure = build_policy(context, payoff)
    assert pure.solution.probabilities[1 - pure_index][1] == 0
    for draw in (0., math.nextafter(1., 0)):
        assert sample_policy(pure, context, rng=SimpleNamespace(random=lambda: draw)).strategy_id == pure.strategies[pure_index].strategy_id


@pytest.mark.parametrize("field,value", [
    ("attack_losses", (("left", 5.), ("right", 5.))),
    ("constraint_residuals", (("left", 5.), ("right", 5.))),
    ("game_value", 1e-12), ("worst_case_attacks", ("left",)),
    ("normalization_residual", .001), ("minimum_probability", 0.),
    ("primal_dual_gap", .01), ("dual_lower_bound", -10.),
    ("optimality_basis", "trust_me"),
])
def test_imported_policy_diagnostics_must_describe_returned_distribution(field, value):
    context, policy = policy_fixture()
    forged = policy.model_copy(update={"solution": policy.solution.model_copy(update={field: value})})
    with pytest.raises(ValueError, match="diagnostic|optimality basis"):
        validate_policy(forged, context)


def test_primal_feasible_but_suboptimal_solver_result_fails_dual_certificate(monkeypatch):
    import app.game.solver as module
    monkeypatch.setattr(module, "linprog", lambda *a, **kw: SimpleNamespace(
        success=True, status=0, message="not really optimal", x=[0., 1., 1.],
        ineqlin=SimpleNamespace(marginals=[-1., 0.])))
    result = solve_minimax(matrix(((0, 0), (1, 1))))
    assert result.status == "solver_failure" and not result.probabilities
    assert "primal-dual" in result.message


def test_solver_certificate_diagnostics_and_tied_worst_attacks():
    payoff = matrix()
    solution = solve_minimax(payoff)
    assert solution.optimality_basis == OPTIMALITY_BASIS
    assert solution.worst_case_attacks == ("left", "right")
    assert solution.primal_dual_gap == pytest.approx(0)
    assert solution.dual_lower_bound == pytest.approx(0)
    assert validate_solution(payoff, solution) == solution


def test_policy_validation_returns_the_detached_validated_object_used_for_sampling():
    context, policy = policy_fixture()
    mutable = [list(pair) for pair in policy.solution.probabilities]
    unchecked = policy.model_copy(update={"solution": policy.solution.model_copy(update={"probabilities": mutable})})
    validated = validate_policy(unchecked, context)
    mutable.clear()
    assert validated.solution.probabilities == policy.solution.probabilities
    assert sample_policy(validated, context, rng=random.Random(2)).policy_id == policy.policy_id
    caller_strategies = list(policy.strategies)
    unchecked = policy.model_copy(update={"strategies": caller_strategies})
    def mutating_rng():
        caller_strategies[0] = caller_strategies[0].model_copy(update={"verifiers": ("unexpected",)})
        return 0.
    decision = sample_policy(unchecked, context, rng=SimpleNamespace(random=mutating_rng))
    assert decision.verifier_names == policy.strategies[0].verifiers


def test_rectangular_game_orientation_and_defender_minimization():
    payoff = matrix(((0, 2, 0), (1, 0, 1)), attack_ids=("left", "middle", "right"))
    solution = solve_minimax(payoff)
    assert solution.status == "optimal"
    assert tuple(p for _, p in solution.probabilities) == pytest.approx((1/3, 2/3))
    assert solution.game_value == pytest.approx(2/3)
    assert set(solution.worst_case_attacks) == {"left", "middle", "right"}
    assert validate_solution(payoff, solution) == solution


def test_cleanup_that_changes_objective_beyond_tolerance_is_rejected(monkeypatch):
    import app.game.solver as module
    monkeypatch.setattr(module, "linprog", lambda *a, **kw: SimpleNamespace(
        success=True, status=0, message="fixture", x=[-1e-12, 1+1e-12, -1e-6],
        ineqlin=SimpleNamespace(marginals=[-1., 0.])))
    result = solve_minimax(matrix(((1e6, 1e6), (0, 0))))
    assert result.status == "solver_failure" and "objective differs" in result.message
    assert not result.probabilities


def test_exported_policy_keeps_fixture_provenance_explicit():
    context, policy = policy_fixture()
    assert json.loads(policy.model_dump_json())["provenance"]["evidence_kind"] == "synthetic_test_fixture"
    forged = policy.model_copy(update={"provenance": policy.provenance.model_copy(update={"evidence_kind": "empirical"})})
    with pytest.raises(ValueError, match="incompatible"):
        validate_policy(forged, context)


def test_snapshot_preserves_large_exact_integer_observation_total():
    manager = ReputationManager()
    state = manager.export_state()
    state["pairs"] = [dict(verifier_name="a", domain="general", successes=2**53, failures=1)]
    manager.restore_state(state)
    selector = VerifierSelector(verifiers=[StubVerifier("a")], reputation_manager=manager)
    captured = make_context(source=selector).plan.reputation_statistics[0]
    assert captured.observation_count == 2**53 + 1
    assert captured == manager.statistics("a", "general")
