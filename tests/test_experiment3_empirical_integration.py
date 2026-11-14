"""Experiment 3 empirical runner. Status commands do not call verifiers; fixtures are synthetic."""

import json
from pathlib import Path

import pytest

from app.game.dependencies import Dependency, DependencyRegistry
from app.game.models import LossConfiguration
from app.game.offline.evaluation import Metrics
from app.reputation.reputation_manager import ReputationManager
from evaluation.analysis.experiment3 import binary_correctness
from evaluation.data_preparation.final_test_workflow import ROOT
from evaluation.experiments.experiment3.calibration_integrity import verify_bundle
from evaluation.experiments.experiment3.development_roster import _reject_final_test, load_roster
from evaluation.experiments.experiment3.empirical_runner import (
    CONDITIONS,
    analyze_recordings,
    assert_unique_recordings,
    build_manifest,
    collection_blockers,
    decision_validation_loss,
    matched_plan,
    run,
)
from evaluation.experiments.experiment3.reputation_policy import (
    authoritative_behavior,
    policy_blockers,
    reproducible_state,
    snapshot_blockers,
)

DEPENDENCY = ROOT / "evaluation/config/experiments/experiment3_dependency_configuration.json"


def _row(**overrides):
    row = {
        "related_group_id": "gsm8k-q-1",
        "candidate_id": "candidate-a",
        "benchmark": "GSM8K",
        "attack_condition": "clean",
        "dependency_model": "structural_shared_resource_v1",
        "dependency_scenario": "independent_failures",
        "aggregation_method": "full_minimax",
        "decision": "passed",
        "gold_label": "VERIFIED_CORRECT",
        "validation_loss": 0.0,
        "coverage": 1.0,
        "uncertainty": 0.0,
        "verifier_reports": [],
        "verifier_costs": [],
        "execution_status": "complete",
        "provenance": {"partition": "development", "label_source": "synthetic-fixture"},
        "configuration_id": "fixture",
        "evidence_label": "SYNTHETIC",
        "result_class": "SYNTHETIC",
    }
    row.update(overrides)
    return row


def test_development_roster_is_the_approved_paired_census():
    roster = load_roster(ROOT)
    assert roster["groups"] == 372
    assert roster["candidates"] == 744
    assert roster["groups_by_benchmark"] == {"GSM8K": 187, "HotpotQA": 185}
    assert roster["collection_authorized"] is False
    assert roster["final_test_authorized"] is False
    assert "verifier collection" in roster["does_not_authorize"]
    assert roster["eligibility_body_sha256"] == "f2cc0fd108b961bf4795767df4f90e92d7fa0f418ef9865d0206f32d7b45282d"
    for group in roster["paired_groups"]:
        labels = {candidate["label_class"] for candidate in group["candidates"]}
        assert labels == {"VERIFIED_CORRECT", "SYNTHETIC_INCORRECT"}
        assert len({candidate["candidate_id"] for candidate in group["candidates"]}) == 2


def test_final_test_paths_are_refused():
    with pytest.raises(RuntimeError, match="Final Test"):
        _reject_final_test(Path("evaluation/final_test/labels.json"))


def test_matched_plan_keeps_conditions_and_methods_aligned():
    first = matched_plan(ROOT)
    second = matched_plan(ROOT)
    assert first == second
    assert first["conditions"] == list(CONDITIONS)
    assert "suppression" not in first["conditions"]
    assert first["suppression"] == "excluded"
    assert first["aggregation_methods"] == ["full_minimax", "fixed_reputation_weighted", "fixed_dependency_group"]
    assert first["planned_candidate_condition_method_cells"] == 744 * 4 * 3
    assert first["verifiers_called"] is False
    assert first["groups_by_benchmark"]["GSM8K"] == first["groups_by_benchmark"]["HotpotQA"] + 2


def test_live_collection_is_blocked_and_writes_no_recordings(tmp_path: Path):
    from evaluation.experiments.experiment3.execution_readiness import execution_report
    readiness = execution_report(ROOT)
    assert readiness["authorized_by_research_lead"] is True
    assert readiness["independent_human_approval"] is False
    blockers = collection_blockers(ROOT)
    if readiness["verifiers_available"]:
        assert blockers == []
    manifest = run(ROOT, tmp_path)
    assert manifest["empirical_collection_started"] is False
    assert manifest["verifiers_called"] is False
    assert manifest["final_test_accessed"] is False
    assert manifest["rows_written"] == 0
    results = json.loads((tmp_path / "results.json").read_text(encoding="utf-8"))
    assert results["rows"] == []
    assert results["status"] == ("NOT_COLLECTED" if blockers else "AUTHORIZED_NOT_EXECUTED")
    metrics = json.loads((tmp_path / "metrics.json").read_text(encoding="utf-8"))
    bootstrap = json.loads((tmp_path / "bootstrap_results.json").read_text(encoding="utf-8"))
    assert metrics["status"] == "NOT_COMPUTED"
    assert bootstrap["status"] == "NOT_COMPUTED"
    repeated = run(ROOT, tmp_path)
    assert repeated == manifest


def test_reputation_export_reproduces_and_experiment_snapshot_is_withheld(tmp_path: Path):
    behavior = authoritative_behavior()
    assert behavior["prior_alpha"] == 1.0
    assert behavior["prior_beta"] == 1.0
    assert behavior["decay"] is None
    manager = ReputationManager()
    assert manager.get_reputation("semantic", "gsm8k") == 0.5
    manager.update_reputation("semantic", "gsm8k", True)
    exported = reproducible_state(manager)
    again = reproducible_state(manager)
    assert exported == again
    assert exported["pairs"] == [{"verifier_name": "semantic", "domain": "gsm8k", "successes": 1, "failures": 0}]
    blockers = snapshot_blockers(ROOT)
    assert "reputation initialization is PENDING_APPROVAL" in blockers
    assert "reputation update rule is PENDING_APPROVAL; History snapshots stay unused" in blockers
    assert policy_blockers(ROOT)
    assert not (tmp_path / "reputation_snapshot.json").exists()


def test_cost_calibration_provenance_matches_the_freeze():
    report = verify_bundle(ROOT)
    assert report["all_frozen_files_match"] is True
    assert report["cost_units"] == "ms"
    assert report["method"] == "mean_attempt_wall_time_ms_v1"
    assert report["attempt_count"] == 488
    assert report["calibration_eligible_attempts"] == 480
    assert report["warmup_attempts"] == 8
    assert report["roles"] == ["development"]
    assert report["policy_fitting_authorized_by_freeze"] is False
    assert report["final_test_authorized_by_freeze"] is False
    validation = report["artifact_validation"]
    assert validation["valid"] is True
    assert validation["resource_manifest_id"] == report["resource_manifest_id"]
    assert validation["setup_fingerprint"] == report["setup_fingerprint"]
    assert validation["calibration_id"] == "cc7e7ca8882f602b9854bf21b80b8a7bf70f6c70d05ccd12787322a84a12477d"
    provenance = next(item for item in report["files"] if item["path"].endswith("calibration-provenance.json"))
    assert provenance["match"] == "lf_normalized"


def test_dependency_configuration_stays_provisional_and_overlapping():
    payload = json.loads(DEPENDENCY.read_text(encoding="utf-8"))
    assert payload["status"] == "PROVISIONAL"
    assert payload["empirical_evidence"] == "none"
    membership = {group["group_id"]: set(group["members"]) for group in payload["groups"]}
    assert membership["deterministic_rule"] == {"rule"}
    assert "evidence" in membership["embedding_minilm"]
    assert "evidence" in membership["nli_deberta"]
    registry = DependencyRegistry(
        version="overlap_probe_v1",
        dependencies=(
            Dependency(resource_id="embedding_minilm", compromise_pathway="shared_embedding", verifiers=("semantic", "evidence")),
            Dependency(resource_id="nli_deberta", compromise_pathway="shared_nli", verifiers=("confidence", "evidence")),
        ),
        unresolved=("rule",),
    )
    components = registry.groups(("semantic", "evidence", "rule", "confidence"))
    assert len(components) == 2
    assert plan_does_not_claim_measured_dependence()


def plan_does_not_claim_measured_dependence() -> bool:
    plan = matched_plan(ROOT)
    return plan["dependency_status"] == "PROVISIONAL" and plan["executed"] is False


def test_decision_loss_matches_the_game_formula_and_is_not_signed():
    weights = {"false_accept": 1.0, "false_reject": 1.0, "uncertain": 0.2}
    counts = {"examples": 5, "false_accept": 1, "false_reject": 1, "uncertain": 1}
    loss = LossConfiguration(version="unit_test_loss_v1", false_accept=1.0, false_reject=1.0, uncertain=0.2, resource_weight=0.0, cost_units="ms")
    metrics = Metrics(examples=5, correct_accept=1, correct_reject=1, false_accept=1, false_reject=1, uncertain=1, unresolved=0, decision_coverage=0.8, selective_risk=0.5, estimated_resource_cost=99.0, mean_loss=3.0)
    assert decision_validation_loss(counts, weights) == pytest.approx(metrics.validation_loss(loss))
    assert decision_validation_loss(counts, weights) == pytest.approx(2.2 / 5)
    manifest = build_manifest(ROOT)
    assert manifest["loss"]["signed_settings_present"] is False
    assert manifest["independent_human_approval"] is False
    assert "unsigned" in manifest["loss"]["signature_status"]
    assert manifest["loss"]["resource_coefficient"] == pytest.approx(1.3399597937725295e-05)
    assert manifest["loss"]["verifier_budget"] == pytest.approx(14996.39091498102)


def test_unresolved_and_failed_rows_are_excluded_from_correctness():
    assert binary_correctness(_row(gold_label="UNRESOLVED", validation_loss=None)) is None
    assert binary_correctness(_row(execution_status="failed", decision="failed", validation_loss=None)) is None
    assert binary_correctness(_row()) == "correct_acceptance"
    assert binary_correctness(_row(decision="passed", gold_label="SYNTHETIC_INCORRECT")) == "false_acceptance"


def test_duplicate_recordings_are_rejected_and_reruns_match():
    row = _row()
    with pytest.raises(ValueError, match="duplicate"):
        assert_unique_recordings([row, dict(row)])
    first = matched_plan(ROOT)["plan_sha256"]
    second = matched_plan(ROOT)["plan_sha256"]
    assert first == second


def test_group_bootstrap_resamples_groups_and_is_deterministic():
    rows = []
    for group, full, other in (("group-a", (0.0, 1.0), (1.0, 1.0)), ("group-b", (0.2, 0.2), (0.2, 0.2))):
        for index, (full_loss, other_loss) in enumerate(zip(full, other)):
            for method, loss in (("full_minimax", full_loss), ("fixed_reputation_weighted", other_loss), ("fixed_dependency_group", other_loss)):
                rows.append(_row(
                    related_group_id=group,
                    candidate_id=f"{group}-{index}",
                    aggregation_method=method,
                    validation_loss=loss,
                    benchmark="GSM8K",
                ))
    report = analyze_recordings(rows, evidence_label="SYNTHETIC", resamples=200, confidence_level=0.95, seed=20261113)
    repeated = analyze_recordings(rows, evidence_label="SYNTHETIC", resamples=200, confidence_level=0.95, seed=20261113)
    assert report == repeated
    contrast = next(item for item in report["paired_differences"] if item["aggregation_method"] == "fixed_reputation_weighted")
    assert contrast["related_group_count"] == 2
    assert contrast["mean_loss_difference"] == pytest.approx(0.25)
    assert contrast["confidence_interval"]["resamples"] == 200
    assert contrast["confidence_interval"]["lower"] <= 0.25 <= contrast["confidence_interval"]["upper"]
    constant = []
    for group in ("group-a", "group-b"):
        for method, loss in (("full_minimax", 0.2), ("fixed_reputation_weighted", 0.4), ("fixed_dependency_group", 0.4)):
            constant.append(_row(related_group_id=group, candidate_id=f"{group}-only", aggregation_method=method, validation_loss=loss))
    constant_report = analyze_recordings(constant, evidence_label="SYNTHETIC", resamples=50, confidence_level=0.95, seed=20261113)
    constant_contrast = next(item for item in constant_report["paired_differences"] if item["aggregation_method"] == "fixed_reputation_weighted")
    assert constant_contrast["mean_loss_difference"] == pytest.approx(0.2)
    assert constant_contrast["confidence_interval"]["lower"] == pytest.approx(0.2)
    assert constant_contrast["confidence_interval"]["upper"] == pytest.approx(0.2)
    assert report["failed_executions"] == 0
    assert report["imputed"] == 0


def test_empirical_and_synthetic_rows_cannot_be_analyzed_together():
    with pytest.raises(ValueError, match="evidence"):
        analyze_recordings([_row(evidence_label="EMPIRICAL", result_class="EMPIRICAL"), _row()], evidence_label="EMPIRICAL", resamples=10, confidence_level=0.95, seed=1)
