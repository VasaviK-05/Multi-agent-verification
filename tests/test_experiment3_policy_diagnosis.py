"""Diagnosis checks. They read the completed collection and do not call verifiers or rewrite it."""

import json
from pathlib import Path

import pytest

from evaluation.experiments.experiment3.policy_diagnosis import (
    DIAGNOSIS,
    PUBLISHED_HASHES,
    PROTECTED,
    audit_results,
    cold_start_controlled_example,
    protected_hashes,
    reproduction_check,
)
from evaluation.experiments.experiment3.write_empirical_figures import PRESERVED, write_all

ROOT = Path(__file__).resolve().parents[1]
EMPIRICAL = ROOT / "evaluation/experiments/experiment3/empirical"


def test_cold_start_agrees_for_one_vote_per_component_and_diverges_otherwise():
    example = cold_start_controlled_example()
    assert example["log_odds_weight_at_one_half"] == 0.0
    assert example["reliability_strength_at_one_half"] == 0.0
    pair = example["one_verifier_per_component"]
    assert pair["same_decision"] is True
    assert pair["statuses"]["reputation_weighted"]["status"] == "uncertain"
    split = example["two_verifiers_in_one_component"]
    assert split["same_decision"] is False
    assert split["statuses"]["reputation_weighted"]["status"] == "passed"
    assert split["statuses"]["dependency_group"]["status"] == "uncertain"


def test_completed_collection_matches_published_hashes_and_reproduces():
    hashes = protected_hashes()
    assert hashes == {path.name: PUBLISHED_HASHES[path.name] for path in PROTECTED}
    results = json.loads((EMPIRICAL / "results.json").read_text(encoding="utf-8"))
    metrics = json.loads((EMPIRICAL / "metrics.json").read_text(encoding="utf-8"))
    bootstrap = json.loads((EMPIRICAL / "bootstrap_results.json").read_text(encoding="utf-8"))
    audit = audit_results(results, results["rows"])
    assert audit["groups"] == 372
    assert audit["candidates"] == 744
    assert audit["rows"] == 15624
    assert audit["attack_columns"] == 7
    assert audit["duplicate_keys"] == 0
    assert audit["execution_failures"] == 0
    assert audit["final_test_accessed"] is False
    assert audit["decision_mismatches"] == 0
    assert audit["loss_mismatches"] == 0
    assert results["evidence_label"] == "EMPIRICAL"
    check = reproduction_check(results["rows"], metrics, bootstrap)
    assert check["metrics_match"] is True
    assert check["bootstrap_match"] is True
    assert protected_hashes() == hashes


def test_diagnosis_finds_a_unique_team_and_tied_aggregations():
    payload = json.loads(DIAGNOSIS.read_text(encoding="utf-8"))
    assert payload["evidence_label"] == "EMPIRICAL"
    assert payload["reproduction"]["metrics_match"] is True
    policy = payload["policy"]
    assert policy["methods"]["full_minimax"]["modal_matches_stored_results"] is True
    assert policy["methods"]["full_minimax"]["optimal_verifiers"] == [["evidence", "rule"]]
    assert policy["methods"]["full_minimax"]["optimal_strategy_count"] == 2
    assert policy["methods"]["fixed_reputation_weighted"]["optimal_strategy_count"] == 1
    assert policy["methods"]["fixed_dependency_group"]["optimal_strategy_count"] == 1
    assert all(row["decision_disagreements"] == 0 for row in policy["aggregation_disagreements"])
    zero = next(row for row in policy["coefficient_counterfactuals"] if row["scenario_id"] == "no_resource_penalty")
    high = next(row for row in policy["coefficient_counterfactuals"] if row["scenario_id"] == "high")
    assert {tuple(item["verifiers"]) for item in zero["optimal_strategies"]} == {("evidence", "rule")}
    assert {tuple(item["verifiers"]) for item in high["optimal_strategies"]} == {("rule", "semantic")}
    assert zero["evidence_class"] == "COUNTERFACTUAL_ON_STORED_EMPIRICAL_REPORTS"


def test_empirical_figures_are_labeled_and_do_not_replace_the_preserved_plot(tmp_path):
    payload = json.loads(DIAGNOSIS.read_text(encoding="utf-8"))
    before = protected_hashes()
    written = write_all(payload, tmp_path)
    assert len(written) == 7
    for path in written:
        text = path.read_text(encoding="utf-8")
        assert "EMPIRICAL" in text
        assert "SYNTHETIC" not in text
    with pytest.raises(ValueError):
        write_all(payload, tmp_path / "synthetic")
    with pytest.raises(ValueError):
        from evaluation.experiments.experiment3.write_empirical_figures import attack_loss_figure
        attack_loss_figure(payload, PRESERVED)
    assert protected_hashes() == before
