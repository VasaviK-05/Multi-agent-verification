"""Experiment 3 execution gate. Synthetic checks are not empirical findings."""

import json
from pathlib import Path

import pytest

from evaluation.analysis.experiment3 import method_metrics, paired_loss_differences, validate_rows
from evaluation.analysis.visualization.experiment3 import attack_stratified_plot, coverage_risk_plot
from evaluation.experiments.experiment3.collection_gate import collection_allowed, validate_recording_file
from evaluation.experiments.experiment3.prerequisite_validator import READY_FOR_APPROVAL


def _row(**overrides):
    row = {
        "related_group_id": "g1", "benchmark": "GSM8K", "attack_condition": "clean",
        "dependency_model": "shared_unknown", "dependency_scenario": "independent_failures",
        "aggregation_method": "full_minimax", "decision": "passed", "gold_label": "VERIFIED_CORRECT",
        "validation_loss": 0.2, "coverage": 1.0, "uncertainty": 0.0,
        "verifier_reports": [], "verifier_costs": [{"verifier": "rule", "cost": 1.0}],
        "execution_status": "complete", "provenance": {"configuration_id": "synthetic-fixture"},
        "configuration_id": "synthetic-fixture", "evidence_label": "SYNTHETIC",
    }
    row.update(overrides)
    return row


def test_live_collection_is_not_authorized():
    report = collection_allowed()
    assert report["status"] == READY_FOR_APPROVAL
    assert report["collection_started"] is False
    assert report["recordings_created"] is False
    assert report["empirical_recording_count"] == 0


def test_synthetic_file_and_final_test_paths_are_refused():
    with pytest.raises(ValueError, match="synthetic fixture"):
        validate_recording_file(Path("evaluation/experiments/experiment3/synthetic/results.json"))
    with pytest.raises(ValueError, match="Final Test"):
        validate_recording_file(Path("evaluation/datasets/final_test_research_v1_eval_v2/labels.jsonl"))


def test_hypothetical_rows_cannot_be_called_empirical():
    with pytest.raises(ValueError, match="hypothetical"):
        validate_rows([_row(evidence_label="EMPIRICAL", result_class="HYPOTHETICAL")])


def test_unresolved_labels_stay_out_of_rates_and_are_counted():
    rows = [
        _row(),
        _row(related_group_id="g2", gold_label="UNRESOLVED", validation_loss=0.9),
        _row(related_group_id="g3", decision="failed", gold_label="VERIFIED_CORRECT", validation_loss=1.0),
        _row(related_group_id="g4", execution_status="failed", validation_loss=None),
    ]
    summary = method_metrics(rows)[0]
    assert summary["unresolved_or_unauthorized"] == 1
    assert summary["execution_failures"] == 1
    assert summary["false_rejection_count"] == 1
    assert summary["correct_acceptance_count"] == 1
    assert summary["false_rejection_rate"] == pytest.approx(0.5)
    assert summary["imputed"] == 0
    assert summary["analyzable_rows"] == 2


def test_paired_interval_is_reproducible_and_one_group_is_not_an_interval():
    rows = []
    for group, base in (("g1", 0.2), ("g2", 0.4)):
        rows.append(_row(related_group_id=group, aggregation_method="full_minimax", validation_loss=base))
        rows.append(_row(related_group_id=group, aggregation_method="fixed_reputation_weighted", validation_loss=base + 0.2))
        rows.append(_row(related_group_id=group, aggregation_method="fixed_dependency_group", validation_loss=base))
    first = paired_loss_differences(rows, resamples=20, confidence_level=0.9, seed=20261113)
    second = paired_loss_differences(rows, resamples=20, confidence_level=0.9, seed=20261113)
    assert first == second
    one = paired_loss_differences(rows[:3], resamples=20, confidence_level=0.9, seed=20261113)[0]
    assert one["confidence_interval"]["reason"] == "at_least_two_related_groups_required"


def test_new_plots_stay_synthetic(tmp_path: Path):
    rows = [_row(), _row(aggregation_method="fixed_reputation_weighted", decision="failed", gold_label="SYNTHETIC_INCORRECT", validation_loss=0.4, coverage=1.0)]
    rows.append(_row(aggregation_method="fixed_dependency_group"))
    coverage = coverage_risk_plot(rows, tmp_path / "coverage.svg")
    attacks = attack_stratified_plot(rows, tmp_path / "attacks.svg")
    assert "SYNTHETIC" in coverage.read_text(encoding="utf-8")
    assert "SYNTHETIC" in attacks.read_text(encoding="utf-8")
    with pytest.raises(ValueError, match="empirical"):
        coverage_risk_plot(rows, tmp_path / "empirical" / "coverage.svg")


def test_hypothetical_configuration_has_no_filled_loss():
    payload = json.loads(Path("evaluation/experiments/experiment3/hypothetical/configurations.json").read_text(encoding="utf-8"))
    assert payload["approved"] is False
    assert payload["empirical_loss"] is None
    assert payload["measured_dependence"] is False
