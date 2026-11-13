"""Synthetic Experiment 3 prerequisites. No Development or Final Test run."""

import subprocess

import pytest

from app.game.dependencies import (CONTROLLED_SYNTHETIC_ASSUMPTION, DependencyRegistry,
                                   controlled_two_group_registry, shared_unknown_registry)
from app.game.offline.attacks import AttackSpecification, enumerate_attacks
from app.game.offline.evaluation import export_artifact, fit_policy
from app.game.offline.replay import replay
from app.game.research.comparison import (aggregation_selection_frequencies, prepare_comparison,
                                          score_development_pilot, verifier_inclusion_frequencies)
from app.game.research.experiment3 import (DEPENDENT_GROUP, INDEPENDENT_GROUP, SYNTHETIC_NAMES,
                                           assert_claim_allowed, render_synthetic_results,
                                           scenario_attempts, scenario_observations, synthetic_specification)
from app.game.research.specification import ExperimentSpecification
from app.game.strategies import enumerate_strategies

REVISION = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()


def _members(registry):
    specification = AttackSpecification(version="report_corruption_v1", suppression="unavailable")
    return {attack.members for attack in enumerate_attacks(registry, specification) if attack.kind != "clean"}


def test_existing_shared_unknown_registry_is_unchanged():
    existing = DependencyRegistry(version="deps_v1", unresolved=SYNTHETIC_NAMES)
    assert existing.unknown_treatment == "shared_unknown"
    assert existing.dependencies == ()
    assert _members(existing) == {SYNTHETIC_NAMES}
    assert _members(shared_unknown_registry(SYNTHETIC_NAMES)) == {SYNTHETIC_NAMES}


def test_two_disjoint_groups_produce_two_attack_targets():
    registry = controlled_two_group_registry(INDEPENDENT_GROUP, DEPENDENT_GROUP)
    assert registry.unresolved == ()
    assert registry.unknown_treatment == "shared_unknown"
    assert {row.compromise_pathway for row in registry.dependencies} == {CONTROLLED_SYNTHETIC_ASSUMPTION}
    assert _members(registry) == {INDEPENDENT_GROUP, DEPENDENT_GROUP}
    with pytest.raises(ValueError):
        controlled_two_group_registry(("a", "b"), ("b", "c"))


def test_controlled_registry_keeps_the_shared_unknown_contract():
    spec = synthetic_specification("controlled_synthetic_two_group", REVISION)
    assert spec.dependency_registry_kind == "controlled_synthetic_two_group"
    assert spec.unknown_dependency_treatment == "shared_unknown"
    assert spec.manifest.evidence_kind == "synthetic_test_fixture"
    data = spec.model_dump()
    data.pop("unknown_dependency_treatment")
    with pytest.raises(ValueError):
        ExperimentSpecification(**data)
    empirical = spec.model_dump()
    empirical["manifest"]["evidence_kind"] = "empirical"
    with pytest.raises(ValueError, match="cannot support an empirical claim"):
        ExperimentSpecification(**empirical)


@pytest.fixture(scope="module")
def contrast():
    spec = synthetic_specification("controlled_synthetic_two_group", REVISION, names=("a", "b"))
    policy, development = fit_policy(spec.context, spec.manifest, spec.contract, spec.attacks)
    artifact = export_artifact(policy, spec.context, spec.manifest, spec.contract, spec.attacks,
                               applicable_domain=spec.context.plan.domain)
    frozen = prepare_comparison(spec, development, artifact, freeze_record="SYNTHETIC freeze only",
                                actual_code_revision=REVISION)
    return spec, frozen, score_development_pilot(spec, frozen, actual_code_revision=REVISION)


def _policy(frozen, method):
    return next(row for row in frozen.policies if row.method == method)


def _clean_loss(result, method):
    row = next(item for item in result.methods if item.method == method)
    return next(metrics.mean_loss for attack_id, metrics in row.attack_metrics if attack_id == row.clean_attack_id)


def test_joint_policy_can_use_both_aggregations_and_fixed_policies_stay_restricted(contrast):
    _spec, frozen, _result = contrast
    joint = _policy(frozen, "full_minimax")
    assert {row.aggregation for row in joint.development_matrix.strategy_definitions} == {
        "reputation_weighted", "dependency_group"}
    assert [name for name, _probability in joint.probabilities] == list(joint.development_matrix.strategy_ids)
    for method, aggregation in (("fixed_reputation_weighted", "reputation_weighted"),
                                ("fixed_dependency_group", "dependency_group")):
        policy = _policy(frozen, method)
        assert {row.aggregation for row in policy.development_matrix.strategy_definitions} == {aggregation}


def test_policies_differ_when_aggregation_losses_differ(contrast):
    _spec, frozen, result = contrast
    matrix = frozen.full_artifact.policy.matrix
    paired = {}
    for strategy, values in zip(matrix.strategy_definitions, matrix.values):
        paired.setdefault(strategy.verifiers, {})[strategy.aggregation] = values
    assert any(item["reputation_weighted"] != item["dependency_group"] for item in paired.values())
    assert _clean_loss(result, "fixed_reputation_weighted") != _clean_loss(result, "fixed_dependency_group")


def test_aggregation_and_verifier_frequencies_follow_the_frozen_probabilities(contrast):
    _spec, frozen, _result = contrast
    for policy in frozen.policies:
        if policy.method not in {"full_minimax", "fixed_reputation_weighted", "fixed_dependency_group"}:
            continue
        manual_aggregation, manual_inclusion = {}, {}
        for strategy, (_name, probability) in zip(policy.development_matrix.strategy_definitions, policy.probabilities):
            manual_aggregation[strategy.aggregation] = manual_aggregation.get(strategy.aggregation, 0.) + probability
            for verifier in strategy.verifiers:
                manual_inclusion[verifier] = manual_inclusion.get(verifier, 0.) + probability
        assert aggregation_selection_frequencies(policy) == {key: manual_aggregation[key] for key in sorted(manual_aggregation)}
        assert verifier_inclusion_frequencies(policy) == {key: manual_inclusion[key] for key in sorted(manual_inclusion)}
        assert sum(aggregation_selection_frequencies(policy).values()) == pytest.approx(1)
    assert aggregation_selection_frequencies(_policy(frozen, "fixed_reputation_weighted")) == pytest.approx(
        {"reputation_weighted": 1})
    assert aggregation_selection_frequencies(_policy(frozen, "fixed_dependency_group")) == pytest.approx(
        {"dependency_group": 1})
    inclusion = verifier_inclusion_frequencies(_policy(frozen, "fixed_reputation_weighted"))
    assert inclusion == pytest.approx({"a": 1, "b": 1})


def test_empirical_claim_is_blocked_when_complete_development_attempts_are_zero():
    with pytest.raises(ValueError, match="complete Development attempts are zero"):
        assert_claim_allowed(claim="empirical", complete_development_attempts=0)
    assert_claim_allowed(claim="synthetic", complete_development_attempts=0)
    assert_claim_allowed(claim="empirical", complete_development_attempts=1)


@pytest.fixture(scope="module")
def controlled():
    return synthetic_specification("controlled_synthetic_two_group", REVISION)


def test_controlled_scenarios_cover_the_declared_failure_patterns(controlled):
    observations = scenario_observations(controlled)
    assert set(observations) == {"all_correct", "one_verifier_failing_independently",
        "multiple_dependent_verifiers_failing_together", "compromised_dependency_group",
        "conflicting_reports", "missing_reports", "execution_failures"}
    assert observations["all_correct"]["public_status"] == {"reputation_weighted": "passed", "dependency_group": "passed"}
    independent = observations["one_verifier_failing_independently"]["attempts"]
    assert [row["recorded_passed"] for row in independent] == [False, True, True]
    dependent = observations["multiple_dependent_verifiers_failing_together"]["attempts"]
    assert [row["recorded_passed"] for row in dependent] == [True, False, False]
    compromised = observations["compromised_dependency_group"]
    assert compromised["attack_members"] == ["b", "c"]
    assert [(row["verifier"], row["passed"]) for row in compromised["attempts"]] == [("a", True), ("b", False), ("c", False)]
    conflicting = scenario_attempts("conflicting_reports")
    assert {passed for _name, _state, passed in conflicting} == {True, False}
    assert set(observations["conflicting_reports"]["public_status"]) == {"reputation_weighted", "dependency_group"}
    assert "missing recording" in observations["missing_reports"]["rejected"]
    assert observations["execution_failures"]["public_status"] == "uncertain"
    assert "selected_execution_incomplete" in observations["execution_failures"]["reasons"]
    context = controlled.context
    from app.game.research.experiment3 import _example
    recorded = _example(context, "scenario", scenario_attempts("all_correct"))
    clean = enumerate_attacks(context.dependencies, controlled.attacks)[0]
    reputation = replay(context, next(row for row in enumerate_strategies(context).strategies
        if row.aggregation == "reputation_weighted" and row.verifiers == ("a", "b")), clean, controlled.attacks,
        controlled.contract, recorded)
    dependency = replay(context, next(row for row in enumerate_strategies(context).strategies
        if row.aggregation == "dependency_group" and row.verifiers == ("a", "b")), clean, controlled.attacks,
        controlled.contract, recorded)
    assert reputation.public_status == "uncertain" and reputation.reasons == ("minimum_contributors",)
    assert dependency.public_status == "passed" and dependency.reasons == ()


def test_synthetic_runner_reports_both_configurations_without_an_empirical_claim():
    payload = render_synthetic_results(REVISION)
    assert payload["output_class"] == "SYNTHETIC" and payload["empirical_claim"] is False
    assert payload["protocol"]["complete_development_attempts_outside_fixture"] == 0
    assert "not an empirically established dependency" in payload["protocol"]["dependency_statement"]
    shared = payload["configurations"]["shared_unknown"]
    controlled_result = payload["configurations"]["controlled_synthetic_two_group"]
    assert shared["reports_digest"] == controlled_result["reports_digest"]
    assert {tuple(column["members"]) for column in shared["attack_columns"] if column["kind"] != "clean"} == {SYNTHETIC_NAMES}
    assert {tuple(column["members"]) for column in controlled_result["attack_columns"] if column["kind"] != "clean"} == {
        INDEPENDENT_GROUP, DEPENDENT_GROUP}
    for configuration in (shared, controlled_result):
        assert configuration["evidence_label"] == "SYNTHETIC"
        assert set(configuration["methods"]) == {"full_minimax", "fixed_reputation_weighted", "fixed_dependency_group"}
        attack_ids = [column["attack_id"] for column in configuration["attack_columns"]]
        for method in configuration["methods"].values():
            assert [row["attack"]["attack_id"] for row in method["attacks"]] == attack_ids
            for field in ("loss", "false_acceptance", "false_rejection", "coverage", "uncertainty",
                          "selective_risk", "cost"):
                assert field in method["attacks"][0]
            assert "worst_case_expected_loss" in method
            assert abs(sum(method["aggregation_selection_frequencies"].values()) - 1) < 1e-9
