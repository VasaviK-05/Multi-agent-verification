"""Synthetic dependency heatmap. These losses are fixture scores, not empirical results."""

import json
from pathlib import Path

import pytest

from evaluation.analysis.visualization.experiment3 import assumption_heatmap
from evaluation.experiments.experiment3.synthetic_dependency_heatmap import (
    ATTACKS, METHODS, VERIFIERS, evaluate, registry_for, write_outputs,
)

ROOT = Path(__file__).resolve().parents[2]
FIGURES = ROOT / "evaluation/experiments/experiment3/synthetic/figures"


def test_dependency_registries_match_the_three_assumptions():
    independent = registry_for("independent").groups(VERIFIERS)
    correlated = registry_for("correlated_semantic_evidence").groups(VERIFIERS)
    full = registry_for("fully_correlated").groups(VERIFIERS)
    assert {frozenset(group.verifiers) for group in independent} == {frozenset({name}) for name in VERIFIERS}
    assert {frozenset(group.verifiers) for group in correlated} == {frozenset({"semantic", "evidence"}), frozenset({"rule"}), frozenset({"confidence"})}
    assert {frozenset(group.verifiers) for group in full} == {frozenset(VERIFIERS)}


def test_engine_scores_every_scenario_attack_and_method():
    payload = evaluate()
    assert payload["evidence_label"] == "SYNTHETIC"
    assert payload["empirical_claim"] is False
    assert payload["cells"]
    seen = {(cell["dependency_assumption"], cell["aggregation_method"], cell["attack_condition"]) for cell in payload["cells"]}
    assumptions = {row["assumption"] for row in payload["scenarios"]}
    assert assumptions == {"independent", "correlated_semantic_evidence", "fully_correlated"}
    assert seen == {(assumption, method, attack) for assumption in assumptions for method in METHODS for attack in ATTACKS}
    for cell in payload["cells"]:
        assert cell["validation_loss"] is not None
        assert cell["group_losses"]
    full = next(cell for cell in payload["cells"] if cell["dependency_assumption"] == "fully_correlated" and cell["attack_condition"] == "forced_rejection")
    independent = next(cell for cell in payload["cells"] if cell["dependency_assumption"] == "independent" and cell["attack_condition"] == "forced_rejection" and cell["aggregation_method"] == full["aggregation_method"])
    assert full["validation_loss"] > independent["validation_loss"]


def test_heatmap_files_are_synthetic_and_cannot_use_an_empirical_directory(tmp_path: Path):
    payload = json.loads((FIGURES / "dependency_robustness_metrics.json").read_text(encoding="utf-8"))
    paths = write_outputs(tmp_path / "synthetic" / "figures", payload)
    for method in METHODS:
        svg = paths[method]["svg"].read_text(encoding="utf-8")
        png = paths[method]["png"].read_bytes()
        assert "SYNTHETIC" in svg
        assert "Dependency assumption" in svg
        assert "Attack condition" in svg
        assert png.startswith(b"\x89PNG")
        assert b"SYNTHETIC" in png
        assert method.encode("ascii") in png
    with pytest.raises(ValueError, match="empirical"):
        write_outputs(tmp_path / "empirical" / "figures", payload)
    with pytest.raises(ValueError, match="empirical"):
        assumption_heatmap(payload, tmp_path / "empirical" / "heatmap.svg", method="full_minimax")


def test_published_synthetic_figures_exist():
    assert (FIGURES / "dependency_robustness_metrics.json").is_file()
    for method in METHODS:
        assert (FIGURES / f"dependency_robustness_{method}.svg").is_file()
        assert (FIGURES / f"dependency_robustness_{method}.png").is_file()
    stored = json.loads((FIGURES / "dependency_robustness_metrics.json").read_text(encoding="utf-8"))
    assert stored["evidence_label"] == "SYNTHETIC"
    assert len(stored["cells"]) == 3 * 3 * 4
