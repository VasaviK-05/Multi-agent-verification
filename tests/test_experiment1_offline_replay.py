"""Experiment 1 replay rules. These tests do not call verifiers or score the corpus."""

import json
from pathlib import Path

import pytest

from app.game.models import PayoffMatrix
from evaluation.experiments.experiment1.offline_replay import (
    METHODS,
    PUBLISHED,
    assert_destination,
    fixed_strategy_id,
    greedy_plan,
    protected_hashes,
    pure_probabilities,
    uniform_probabilities,
    _selector,
)


def test_methods_and_probabilities():
    assert METHODS == ("full_minimax", "coverage_aware_greedy", "uniform", "deterministic_minimax")
    pure = pure_probabilities(("a", "b"), "b")
    assert pure == {"a": 0.0, "b": 1.0}
    uniform = uniform_probabilities(("a", "b", "c", "d"))
    assert sum(uniform.values()) == pytest.approx(1.0)
    assert set(uniform.values()) == {0.25}


def test_fixed_strategy_uses_worst_column_then_id():
    matrix = PayoffMatrix(
        strategy_ids=("b-team", "a-team", "c-team"),
        attack_ids=("clean", "forced"),
        values=((0.2, 0.4), (0.2, 0.4), (0.1, 0.9)),
        compatibility_id="test",
    )
    assert fixed_strategy_id(matrix) == "a-team"


def test_destination_guard():
    with pytest.raises(RuntimeError):
        assert_destination(Path("evaluation/experiments/experiment3/empirical"))
    with pytest.raises(RuntimeError):
        assert_destination(Path("evaluation/datasets/final_test/replay"))


def test_greedy_plan_does_not_call_a_verifier():
    plan = greedy_plan(
        {"question": "What is 2 plus 2?", "context": ""},
        _selector(),
    )
    assert plan["team"]
    assert plan["minimum_count"] >= 2


def test_frozen_experiment3_hashes_are_unchanged():
    assert protected_hashes() == PUBLISHED


def test_completed_replay_records_the_predeclared_policies():
    root = Path("evaluation/experiments/experiment1/development")
    manifest = json.loads((root / "policy_manifest.json").read_text(encoding="utf-8"))
    policies = manifest["policies"]
    assert policies["full_minimax"]["verifiers"] == ["evidence", "rule"]
    assert policies["deterministic_minimax"]["strategy_id"] == policies["full_minimax"]["strategy_id"]
    assert policies["uniform"]["strategy_count"] == 14
    greedy = policies["coverage_aware_greedy"]
    assert greedy["feasible_candidates"] == 510
    assert greedy["infeasible_candidates"] == 234
    figure = (root / "figures" / "method_decision_loss.svg").read_text(encoding="utf-8")
    assert "EMPIRICAL" in figure
    assert "SYNTHETIC" not in figure
