"""Synthetic resource-grid tests. No Development collection and no approval edits."""

from pathlib import Path
from types import SimpleNamespace

import pytest

from app.game.models import LossConfiguration
from app.game.offline.evaluation import summarize
from app.game.strategies import enumerate_strategies
from evaluation.experiments.experiment3.resource_sensitivity import (
    LABEL, LOSS_PER_MS, MILLISECONDS, PROPOSAL_FALSE_ACCEPT, PROPOSAL_UNCERTAIN,
    ROOT, assert_safe_output, coefficient_scenarios, frozen_calibration, loss_configuration,
    planning_context)

EXPERIMENT = ROOT / "evaluation" / "experiments" / "experiment3"
SCENARIOS = EXPERIMENT / "sensitivity" / "scenarios.json"
RESULTS = EXPERIMENT / "sensitivity" / "results.json"
MANIFEST = EXPERIMENT / "sensitivity" / "reproducibility_manifest.json"


def _load(path):
    import json
    return json.loads(path.read_text(encoding="utf-8"))


def test_zero_resource_weight_is_supported_and_adds_no_penalty():
    loss = loss_configuration(0.0)
    assert loss.resource_weight == 0.0
    outcome = SimpleNamespace(example_id="e", public_status="failed", answer_is_correct=True,
                              unresolved=(), estimated_attempt_cost=14925.820978323463)
    metrics = summarize([(outcome, 1.0)], loss)
    assert metrics.validation_loss(loss) == pytest.approx(1.0)
    assert metrics.mean_loss == pytest.approx(metrics.validation_loss(loss))
    with pytest.raises(ValueError):
        LossConfiguration(version="sensitivity-loss-v1", false_accept=1.0, false_reject=1.0,
                          uncertain=0.2, resource_weight=-1.0, cost_units="ms")


def test_coefficients_use_loss_per_millisecond_and_select_nothing():
    means = frozen_calibration()["means_ms"]
    rows = {row["id"]: row for row in coefficient_scenarios(means)}
    assert rows["no_resource_penalty"]["value_loss_per_ms"] == 0.0
    assert rows["no_resource_penalty"]["reference_only"] is True
    assert rows["low"]["value_loss_per_ms"] == pytest.approx(PROPOSAL_UNCERTAIN / means["confidence"])
    assert rows["moderate"]["value_loss_per_ms"] == pytest.approx(PROPOSAL_FALSE_ACCEPT / means["confidence"])
    assert rows["high"]["value_loss_per_ms"] == pytest.approx(PROPOSAL_UNCERTAIN / means["semantic"])
    assert {row["unit"] for row in rows.values()} == {LOSS_PER_MS}
    assert all(row["selected"] is False for row in rows.values())
    published = _load(SCENARIOS)
    assert published["label"] == LABEL
    assert published["selected_configuration"] is None
    assert published["empirical_claim"] is False
    assert published["calibration"]["four_verifier_sum_is_a_selected_budget"] is False
    permissive = next(row for row in published["budgets"] if row["id"] == "permissive")
    assert permissive["unit"] == MILLISECONDS
    assert permissive["not_a_protocol_budget"] is True
    assert permissive["uses_four_verifier_sum"] is True
    assert permissive["selected"] is False
    assert permissive["value_ms"] == pytest.approx(published["calibration"]["computed_four_verifier_sum_ms"])
    assert all(row["unit"] == MILLISECONDS and row["selected"] is False for row in published["budgets"])


def test_budget_admits_equal_cost_and_rejects_a_strict_excess():
    published = _load(SCENARIOS)
    moderate = next(row for row in published["budgets"] if row["id"] == "moderate")
    context = planning_context(moderate["value_ms"], 0.0, 2)
    result = enumerate_strategies(context)
    teams = {tuple(strategy.verifiers): strategy.estimated_cost for strategy in result.strategies}
    defining = tuple(moderate["defining_team"])
    assert defining in teams
    assert teams[defining] <= moderate["value_ms"]
    assert all("confidence" not in team for team in teams)
    rejected = {tuple(item.verifiers): item.reasons for item in result.rejected}
    confidence = ("confidence", "rule", "semantic")
    assert "budget" in rejected[confidence]
    tighter = planning_context(teams[defining], 0.0, 2)
    still = {tuple(strategy.verifiers) for strategy in enumerate_strategies(tighter).strategies}
    assert defining in still
    below = planning_context(teams[defining] - 1e-9, 0.0, 2)
    assert defining not in {tuple(strategy.verifiers) for strategy in enumerate_strategies(below).strategies}


def test_decision_loss_and_resource_penalty_stay_separate():
    means = frozen_calibration()["means_ms"]
    weight = PROPOSAL_FALSE_ACCEPT / means["confidence"]
    loss = loss_configuration(weight)
    outcome = SimpleNamespace(example_id="e", public_status="passed", answer_is_correct=False,
                              unresolved=(), estimated_attempt_cost=means["confidence"])
    metrics = summarize([(outcome, 1.0)], loss)
    assert metrics.validation_loss(loss) == pytest.approx(PROPOSAL_FALSE_ACCEPT)
    assert metrics.estimated_resource_cost == pytest.approx(means["confidence"])
    assert metrics.mean_loss == pytest.approx(
        metrics.validation_loss(loss) + loss.resource_weight * metrics.estimated_resource_cost)
    assert loss.resource_weight * means["confidence"] == pytest.approx(1.0)


def test_published_grid_keeps_decision_loss_apart_from_the_penalty_and_selects_nothing():
    import hashlib
    results = _load(RESULTS)
    manifest = _load(MANIFEST)
    assert results["label"] == LABEL and results["empirical_claim"] is False
    assert results["selected_configuration"] is None
    assert results["collection_executed"] is False and results["approval_records_modified"] is False
    assert results["fixture"]["max_abs_decomposition_error"] == 0.0
    assert results["fixture"]["calibrated_roster_scored_by_fixture"] is False
    digest = hashlib.sha256((EXPERIMENT / "synthetic" / "results.json").read_bytes()).hexdigest()
    assert results["fixture"]["sha256"] == digest
    for name, record in manifest["files"].items():
        if name == "reproducibility_manifest.json":
            continue
        path = ROOT / record["path"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == record["sha256"]
    infeasible = {(row["coefficient_id"], row["budget_id"], row["floor_id"]) for row in results["findings"]["infeasible_cells"]}
    assert infeasible == {(weight, "restrictive", "participant_floor_3")
                          for weight in ("no_resource_penalty", "low", "moderate", "high")}
    for cell in results["cells"]:
        assert cell["selected"] is False
        same_budget = [other for other in results["cells"]
                       if other["budget_id"] == cell["budget_id"] and other["floor_id"] == cell["floor_id"]]
        assert {tuple(team["verifiers"]) for team in cell["feasible_teams"]} == {
            tuple(team["verifiers"]) for team in same_budget[0]["feasible_teams"]}
        if cell["budget_id"] == "moderate":
            assert cell["confidence_feasible"] is False and cell["feasible"] is True
        if cell["budget_id"] == "permissive":
            assert cell["full_roster_feasible"] is True
        if not cell["feasible"]:
            assert all(block["status"] == "not_called" for overlay in cell["overlays"].values()
                       for block in overlay.values())
            continue
        assert all(block["status"] == "optimal" for overlay in cell["overlays"].values() for block in overlay.values())
        if cell["coefficient_id"] == "no_resource_penalty":
            continue
        for name, overlay in cell["overlays"].items():
            for method, solved in overlay.items():
                assert {tuple(item["verifiers"]) for item in solved["optimal_strategies"]} == {tuple(cell["cheapest_team"])}
                worst_decision = results["fixture"]["configurations"][name]["methods"][method]["worst_case_decision_loss"]
                if method == "full_minimax":
                    worst_decision = min(
                        results["fixture"]["configurations"][name]["methods"][item]["worst_case_decision_loss"]
                        for item in ("fixed_reputation_weighted", "fixed_dependency_group"))
                assert solved["game_value"] == pytest.approx(
                    worst_decision + cell["resource_penalty_on_cheapest_team"])


def test_writer_refuses_preserved_artifact_directories():
    with pytest.raises(RuntimeError):
        assert_safe_output(EXPERIMENT / "synthetic" / "results.json")
    with pytest.raises(RuntimeError):
        assert_safe_output(EXPERIMENT / "empirical" / "results.json")
    with pytest.raises(RuntimeError):
        assert_safe_output(EXPERIMENT / "approval_package" / "manifest.json")
