"""Synthetic Experiment 3 figures. These rows are not empirical findings."""

from pathlib import Path

import pytest

from app.game.research.uncertainty import _quantile
from evaluation.analysis.experiment3 import (
    aggregation_comparison, binary_correctness, dependency_discrimination, dependency_robustness_matrix,
    identical_outcomes, paired_loss_differences,
)
from evaluation.analysis.visualization.experiment3 import (
    aggregation_grouped_bars, dependency_heatmap, paired_difference_plot,
)

METHODS = ("full_minimax", "fixed_reputation_weighted", "fixed_dependency_group")


def _row(**overrides):
    row = {
        "related_group_id": "g1",
        "benchmark": "GSM8K",
        "attack_condition": "clean",
        "dependency_model": "shared_unknown",
        "dependency_scenario": "independent_failures",
        "aggregation_method": "full_minimax",
        "decision": "passed",
        "gold_label": "VERIFIED_CORRECT",
        "validation_loss": 0.2,
        "coverage": 1.0,
        "uncertainty": 0.0,
        "verifier_reports": [{"verifier": "rule", "passed": True}],
        "verifier_costs": [{"verifier": "rule", "cost": 1.0}],
        "execution_status": "complete",
        "provenance": {"configuration_id": "synthetic-fixture"},
        "configuration_id": "synthetic-fixture",
        "evidence_label": "SYNTHETIC",
    }
    row.update(overrides)
    return row


def _matched_rows():
    losses = {
        ("g1", "clean", "full_minimax"): 0.2,
        ("g1", "clean", "fixed_reputation_weighted"): 0.4,
        ("g1", "clean", "fixed_dependency_group"): 0.2,
        ("g2", "clean", "full_minimax"): 0.2,
        ("g2", "clean", "fixed_reputation_weighted"): 0.6,
        ("g2", "clean", "fixed_dependency_group"): 0.2,
        ("g1", "attacked", "full_minimax"): 0.5,
        ("g1", "attacked", "fixed_reputation_weighted"): 0.7,
        ("g1", "attacked", "fixed_dependency_group"): 0.5,
        ("g2", "attacked", "full_minimax"): 0.5,
        ("g2", "attacked", "fixed_reputation_weighted"): 0.7,
        ("g2", "attacked", "fixed_dependency_group"): 0.5,
    }
    rows = []
    for (group, attack, method), loss in losses.items():
        rows.append(_row(related_group_id=group, attack_condition=attack, aggregation_method=method,
                          validation_loss=loss, coverage=0.0 if method == "fixed_reputation_weighted" else 1.0,
                          decision="uncertain" if method == "fixed_reputation_weighted" else "passed"))
    rows.append(_row(related_group_id="g3", aggregation_method="fixed_reputation_weighted", validation_loss=9.0, coverage=0.0, decision="uncertain"))
    rows.append(_row(related_group_id="g2", gold_label="UNRESOLVED", validation_loss=8.0))
    rows.append(_row(related_group_id="g2", execution_status="failed", validation_loss=7.0))
    return rows


def test_grouped_summary_covers_three_methods_and_excludes_unusable_rows():
    summaries = aggregation_comparison(_matched_rows())
    methods = {row["aggregation_method"] for row in summaries}
    assert methods == set(METHODS)
    clean_full = next(row for row in summaries if row["aggregation_method"] == "full_minimax" and row["attack_condition"] == "clean")
    assert clean_full["validation_loss"] == pytest.approx(0.2)
    assert clean_full["coverage"] == pytest.approx(1.0)
    assert clean_full["sample_size"] == 2
    reputation = next(row for row in summaries if row["aggregation_method"] == "fixed_reputation_weighted" and row["attack_condition"] == "clean")
    assert reputation["sample_size"] == 3
    assert reputation["coverage"] == pytest.approx(0.0)


def test_binary_correctness_skips_unresolved_and_refuses_final_test():
    assert binary_correctness(_row()) == "correct_acceptance"
    assert binary_correctness(_row(decision="passed", gold_label="SYNTHETIC_INCORRECT")) == "false_acceptance"
    assert binary_correctness(_row(gold_label="UNRESOLVED")) is None
    with pytest.raises(ValueError, match="Final Test"):
        binary_correctness(_row(partition="final_test"))


def test_paired_differences_have_the_expected_sign_and_keep_zero():
    contrasts = {row["aggregation_method"]: row for row in paired_loss_differences(_matched_rows())}
    reputation = contrasts["fixed_reputation_weighted"]
    dependency = contrasts["fixed_dependency_group"]
    assert reputation["mean_loss_difference"] == pytest.approx(0.25)
    assert reputation["mean_loss_difference"] > 0
    assert reputation["missing_pairs"] == 1
    assert dependency["mean_loss_difference"] == pytest.approx(0.0)
    assert dependency["zero_difference_count"] == 4


def test_confidence_interval_uses_the_paired_group_bootstrap():
    rows = _matched_rows()
    result = paired_loss_differences(rows, resamples=30, confidence_level=0.8, seed=2)[0]
    interval = result["confidence_interval"]
    assert interval["lower"] <= result["mean_loss_difference"] <= interval["upper"]
    pending = paired_loss_differences(rows)[0]["confidence_interval"]
    assert pending["lower"] is None and pending["reason"] == "statistical_configuration_pending"
    by_group = {"g1": [0.2, 0.2], "g2": [0.4, 0.2]}
    import random
    rng = random.Random(2)
    groups = sorted(by_group)
    means = []
    for _ in range(30):
        draw = [rng.choice(groups) for _ in groups]
        values = [value for name in draw for value in by_group[name]]
        means.append(sum(values) / len(values))
    assert interval["lower"] == pytest.approx(_quantile(means, 0.1))
    assert interval["upper"] == pytest.approx(_quantile(means, 0.9))


def test_identical_decisions_and_losses_are_detected():
    rows = [_row(aggregation_method=method, decision="passed", validation_loss=0.2) for method in METHODS]
    found = identical_outcomes(rows)
    assert found[0]["identical_decisions"] is True
    assert found[0]["identical_losses"] is True
    rows[1]["decision"] = "failed"
    assert identical_outcomes(rows)[0]["identical_decisions"] is False


def test_one_dependency_group_limits_discrimination_and_a_single_model_is_not_estimable():
    verifiers = ["semantic", "evidence", "rule", "confidence"]
    diagnosis = dependency_discrimination(verifiers, [verifiers])
    assert diagnosis["limited_dependency_discrimination"] is True
    rows = [_row(aggregation_method="full_minimax")]
    matrix = dependency_robustness_matrix(rows, aggregation_method="full_minimax", declared_model="shared_unknown", verifiers=verifiers, groups=[verifiers])
    assert matrix["estimable"] is False
    assert matrix["reason"] == "only one dependency model is available"
    assert all(cell["status"] == "unavailable" or cell["dependency_scenario"] == "independent_failures" for cell in matrix["cells"])
    assert matrix["dependency_discrimination"]["limited_dependency_discrimination"] is True


def test_missing_dependency_cell_stays_unavailable():
    rows = [
        _row(dependency_model="shared_unknown", dependency_scenario="independent_failures", validation_loss=0.4),
        _row(dependency_model="shared_unknown", dependency_scenario="correlated_failures", validation_loss=0.8),
        _row(dependency_model="two_group", dependency_scenario="independent_failures", validation_loss=0.3),
    ]
    matrix = dependency_robustness_matrix(rows, aggregation_method="full_minimax", declared_model="shared_unknown")
    assert matrix["estimable"] is True
    missing = next(cell for cell in matrix["cells"] if cell["dependency_model"] == "two_group" and cell["dependency_scenario"] == "correlated_failures")
    assert missing["status"] == "unavailable" and missing["validation_loss"] is None
    present = next(cell for cell in matrix["cells"] if cell["dependency_model"] == "two_group" and cell["dependency_scenario"] == "independent_failures")
    assert present["validation_loss"] == pytest.approx(0.3)


def test_synthetic_plots_are_labeled_and_stay_out_of_empirical_directories(tmp_path: Path):
    rows = _matched_rows()
    bars = aggregation_grouped_bars(rows, tmp_path / "bars.svg")
    heatmap = dependency_heatmap(dependency_robustness_matrix(
        [_row(), _row(dependency_model="two_group", validation_loss=0.3)],
        aggregation_method="full_minimax", declared_model="shared_unknown"), tmp_path / "heatmap.svg")
    paired = paired_difference_plot(rows, tmp_path / "paired.svg", resamples=20, confidence_level=0.9, seed=1)
    for path in (bars, heatmap, paired):
        text = path.read_text(encoding="utf-8")
        assert "SYNTHETIC" in text
        assert "EMPIRICAL" not in text.replace("synthetic figure cannot", "")
    assert 'data-zero="0"' in paired.read_text(encoding="utf-8")
    single = dependency_robustness_matrix([_row()], aggregation_method="full_minimax", declared_model="shared_unknown")
    not_estimable = dependency_heatmap(single, tmp_path / "not-estimable.svg").read_text(encoding="utf-8")
    assert "Not estimable" in not_estimable
    missing = dependency_heatmap(dependency_robustness_matrix(
        [_row(), _row(dependency_model="two_group", dependency_scenario="independent_failures")],
        aggregation_method="full_minimax", declared_model="shared_unknown"), tmp_path / "missing.svg")
    assert "unavailable" in missing.read_text(encoding="utf-8")
    with pytest.raises(ValueError, match="empirical result directory"):
        aggregation_grouped_bars(rows, tmp_path / "empirical" / "results.svg")
