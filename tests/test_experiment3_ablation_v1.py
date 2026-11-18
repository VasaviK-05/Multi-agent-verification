"""Checks for the Experiment 3 aggregation and dependency ablation."""

import json
from pathlib import Path

import pytest

from app.game.offline.attacks import transform
from app.game.offline.records import Attempt
from app.models.schemas import VerificationResult
from evaluation.experiments.experiment3.ablation_v1.failures import (
    apply_attack,
    correlated_attacks,
    declared_registry,
    fully_correlated_registry,
    forced_support_attack,
    group_bootstrap,
    group_members,
    independent_attacks,
    independent_registry,
    matched_attacks,
    native_attacks,
    paired_group_difference,
    severity,
)
from evaluation.experiments.experiment3.ablation_v1.figures import aggregation_figure
from evaluation.experiments.experiment3.empirical_executor import SPECIFICATION, _attempt

ROOT = Path(__file__).resolve().parents[1]


def _attempt_for(name: str, decision: str, score: float) -> Attempt:
    passed = decision == "SUPPORT"
    result = VerificationResult(verifier_name=name, passed=passed, score=score, metadata={"decision": decision})
    return Attempt(
        verifier_name=name, state="abstention" if decision == "UNSURE" else "directional",
        report_json=result.model_dump_json(), execution_id="candidate", configuration_id="ablation-v1",
        report_provenance="unit-test", adapter={"rule": "rule_v1", "evidence": "evidence_v1", "confidence": "confidence_v1", "semantic": "semantic_v1"}[name],
    )


def _bundle(decisions: dict[str, str]) -> dict[str, Attempt]:
    return {name: _attempt_for(name, decision, 0.4 if decision != "UNSURE" else 0.0) for name, decision in decisions.items()}


def test_registries_have_the_expected_groups():
    assert set(group_members(declared_registry())) == {("confidence", "evidence", "semantic"), ("rule",)}
    assert set(group_members(independent_registry())) == {("confidence",), ("evidence",), ("rule",), ("semantic",)}
    assert group_members(fully_correlated_registry()) == (("confidence", "evidence", "rule", "semantic"),)


def test_independent_failure_changes_only_the_targeted_verifier():
    original = {"semantic": "SUPPORT", "evidence": "REJECT", "rule": "UNSURE", "confidence": "SUPPORT"}
    attempts = _bundle(original)
    attack = forced_support_attack(("evidence",))
    _transformed, audits = apply_attack(attempts, attack)
    summary = severity(audits, attack)
    assert summary["targeted_verifiers"] == ["evidence"]
    assert summary["actually_corrupted_count"] == 1
    assert all(not row["effective"] for row in audits if row["verifier"] != "evidence")
    evidence = next(row for row in audits if row["verifier"] == "evidence")
    assert evidence["before_passed"] is False and evidence["after_passed"] is True


def test_correlated_failure_changes_the_shared_group_and_preserves_abstention():
    attempts = _bundle({"semantic": "REJECT", "evidence": "SUPPORT", "rule": "UNSURE", "confidence": "UNSURE"})
    attack = correlated_attacks(declared_registry())[0]
    assert set(attack.members) == {"confidence", "evidence", "semantic"}
    _transformed, audits = apply_attack(attempts, attack)
    summary = severity(audits, attack)
    changed = {row["verifier"] for row in audits if row["effective"]}
    assert changed == {"semantic", "evidence"}
    assert summary["preserved_abstention_count"] == 1
    rule = next(row for row in audits if row["verifier"] == "rule")
    assert rule["reason"] == "outside_target" and rule["effective"] is False


def test_original_attempt_and_report_payload_stay_unchanged():
    attempts = _bundle({"semantic": "REJECT", "evidence": "REJECT", "rule": "REJECT", "confidence": "REJECT"})
    before = {name: attempts[name].report_json for name in attempts}
    attack = forced_support_attack(("confidence", "evidence", "rule", "semantic"))
    transformed, _audits = apply_attack(attempts, attack)
    assert {name: attempts[name].report_json for name in attempts} == before
    assert transformed["evidence"].report.passed is True
    assert attempts["evidence"].report.passed is False


def test_matched_columns_do_not_depend_on_the_aggregation_assumption():
    first = matched_attacks()
    second = matched_attacks()
    assert [attack.members for attack in first["independent_failures"]] == [attack.members for attack in second["independent_failures"]]
    assert [attack.members for attack in first["correlated_failures"]] == [("confidence", "evidence", "semantic"), ("rule",)]
    native = native_attacks("fully_correlated")
    assert [attack.members for attack in native["correlated_failures"]] == [("confidence", "evidence", "rule", "semantic")]
    assert [attack.members for attack in native["independent_failures"]] == [attack.members for attack in independent_attacks()]


def test_bootstrap_resamples_question_groups_not_candidate_rows():
    losses = {"group-a": [0.0, 1.0], "group-b": [0.2, 0.2]}
    summary = group_bootstrap(losses, seed=5, resamples=20)
    assert summary["groups"] == 2
    assert summary["paired_observations"] == 4
    assert summary["resamples"] == 20
    repeated = group_bootstrap(losses, seed=5, resamples=20)
    assert summary["lower"] == repeated["lower"]
    assert summary["upper"] == repeated["upper"]


def test_missing_group_is_not_treated_as_zero():
    with pytest.raises(ValueError, match="missing question groups"):
        paired_group_difference({"a": [0.2], "b": [0.2]}, {"a": [0.2]})


def test_figure_refuses_a_missing_measured_value(tmp_path: Path):
    source = tmp_path / "results.json"
    source.write_text(json.dumps({
        "record_type": "experiment3_ablation_v1",
        "aggregation": {
            "neutral": {
                "reproduction_matches_historical": True,
                "methods": {
                    "full_minimax": {"mean_decision_loss": 0.2, "coverage": None},
                    "fixed_reputation_weighted": {"mean_decision_loss": 0.2, "coverage": 0.2},
                    "fixed_dependency_group": {"mean_decision_loss": 0.2, "coverage": 0.2},
                },
            },
            "non_neutral_reputation": {"status": "not_estimable", "reason": "no approved observations"},
        },
    }), encoding="utf-8")
    with pytest.raises(ValueError, match="missing a measured value"):
        aggregation_figure(source, tmp_path / "figure.svg")


def test_saved_report_transform_uses_the_experiment_adapter():
    result = VerificationResult(verifier_name="rule", passed=False, score=0.0, metadata={"decision": "REJECT", "rule": "arithmetic_addition"})
    attempt = _attempt("rule", result.model_dump(mode="json"), "candidate")
    attack = forced_support_attack(("rule",))
    transformed, audit = transform(attempt, attack, SPECIFICATION)
    assert audit.effective is True
    assert transformed.report.passed is True
    assert attempt.report.passed is False


def test_completed_ablation_outputs_exist_and_do_not_invent_cells():
    results = ROOT / "evaluation/experiments/experiment3/ablation_v1/outputs/results.json"
    if not results.is_file():
        pytest.skip("ablation v1 has not been executed")
    payload = json.loads(results.read_text(encoding="utf-8"))
    assert payload["reports_unchanged"] is True
    matrix = payload["dependency"]["native_matrix"]
    for assumption in ("declared_structural", "independent", "fully_correlated"):
        for scenario in ("independent_failures", "correlated_failures"):
            cell = matrix[assumption][scenario]
            assert cell["status"] == "available"
            assert cell["worst_column_decision_loss"] is not None
            assert cell["candidates"] == 744
    assert payload["aggregation"]["non_neutral_reputation"]["ran"] is False
    figures = ROOT / "evaluation/experiments/experiment3/ablation_v1/outputs/figures"
    for name in (
        "aggregation_ablation_grouped_bars.svg",
        "dependency_robustness_heatmap.svg",
        "dependency_coverage_heatmap.svg",
        "ablation_effect_differences.svg",
    ):
        text = (figures / name).read_text(encoding="utf-8")
        assert "unavailable" not in text or name.startswith("dependency")
        assert "<svg" in text
