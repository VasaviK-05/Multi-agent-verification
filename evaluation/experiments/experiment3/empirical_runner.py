"""Gated Experiment 3 runner.

The runner binds the Development roster, the frozen cost calibration, and the
recorded research-lead execution configuration. ``run`` does not call verifiers.
Empirical execution is ``empirical_executor.execute``.
"""

from __future__ import annotations

import hashlib
import json
import platform
import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[3]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from evaluation.analysis.experiment3 import METHODS, REQUIRED_FIELDS, binary_correctness, method_metrics, paired_loss_differences, validate_rows
from evaluation.experiments.experiment3.calibration_integrity import verify_bundle
from evaluation.experiments.experiment3.development_roster import load_roster
from evaluation.experiments.experiment3.prerequisite_validator import assess
from evaluation.experiments.experiment3.reputation_policy import authoritative_behavior, policy_blockers, snapshot_blockers

ROOT = Path(__file__).resolve().parents[3]
EXPERIMENT_ID = "experiment3"
CONDITIONS = ("clean", "forced_support", "forced_rejection", "confidence_inflation")
DEPENDENCY_MODEL = "structural_shared_resource_v1"
RECORDING_FIELDS = REQUIRED_FIELDS + (
    "experiment_id", "candidate_id", "question_id", "selected_verifiers", "dependency_groups",
    "reputation_snapshot_id", "policy_snapshot_id", "resource_configuration_hash",
    "cost_calibration_hash", "execution_cost", "label_provenance", "correctness", "failure_reason",
)


def _git_commit(root: Path) -> str | None:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def _git_branch(root: Path) -> str | None:
    try:
        return subprocess.check_output(["git", "branch", "--show-current"], cwd=root, text=True).strip() or None
    except (OSError, subprocess.CalledProcessError):
        return None


def collection_blockers(root: Path) -> list[str]:
    """Integrity gaps that stop verifier execution. A JSON approval flag is not enough."""
    root = Path(root)
    blockers = []
    try:
        roster = load_roster(root)
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
        return [str(exc)]
    if roster["collection_authorized"] is not False or roster["recording_authorized"] is not False:
        blockers.append("eligibility manifest collection flag is not the recorded withheld state")
    if roster["final_test_authorized"] is not False:
        blockers.append("eligibility manifest final-test flag is not the recorded withheld state")
    withheld = set(roster["does_not_authorize"])
    for item in ("verifier collection", "attempt recording", "policy fitting"):
        if item not in withheld:
            blockers.append(f"eligibility manifest no longer withholds {item}")
    from evaluation.experiments.experiment3.execution_readiness import execution_report
    report = execution_report(root)
    if not report["authorized_by_research_lead"]:
        blockers.append("execution configuration failed automated integrity validation")
        blockers.extend(report["blockers"])
    if not report["verifiers_available"]:
        blockers.extend(report["verifier_gaps"])
    calibration = verify_bundle(root)
    if not calibration["all_frozen_files_match"]:
        blockers.append("frozen cost-calibration bundle failed integrity validation")
    if calibration["policy_fitting_authorized_by_freeze"] is not False:
        blockers.append("cost-calibration freeze unexpectedly authorizes policy fitting")
    if calibration["cost_units"] != "ms":
        blockers.append("calibration cost unit is not milliseconds")
    return list(dict.fromkeys(blockers))


def _signed_settings(root: Path) -> dict | None:
    path = root / "evaluation/config/experiments/approvals/experiment3_protocol_approval_record.json"
    if not path.is_file():
        return None
    record = json.loads(path.read_text(encoding="utf-8"))
    signed = record.get("status") == "APPROVED" and record.get("approved") is True and record.get("decision") == "APPROVED" and record.get("approver") and record.get("approval_date")
    settings = record.get("approved_settings")
    if not signed or not isinstance(settings, dict):
        return None
    return settings


def matched_plan(root: Path) -> dict:
    """Matched cells across methods and conditions. This plan is not a result."""
    roster = load_roster(root)
    group_ids = [group["related_group_id"] for group in roster["paired_groups"]]
    candidate_ids = [candidate["candidate_id"] for group in roster["paired_groups"] for candidate in group["candidates"]]
    identity = {
        "group_ids": group_ids,
        "candidate_ids": candidate_ids,
        "conditions": list(CONDITIONS),
        "methods": list(METHODS),
        "dependency_model": DEPENDENCY_MODEL,
        "suppression_included": False,
    }
    digest = hashlib.sha256((json.dumps(identity, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")).hexdigest()
    cells = len(candidate_ids) * len(CONDITIONS) * len(METHODS)
    return {
        "experiment_id": EXPERIMENT_ID,
        "executed": False,
        "verifiers_called": False,
        "groups": len(group_ids),
        "candidates": len(candidate_ids),
        "groups_by_benchmark": roster["groups_by_benchmark"],
        "conditions": list(CONDITIONS),
        "aggregation_methods": list(METHODS),
        "suppression": "excluded",
        "dependency_model": DEPENDENCY_MODEL,
        "dependency_status": "PROVISIONAL",
        "planned_candidate_condition_method_cells": cells,
        "plan_sha256": digest,
        "same_inputs_across_methods": ["question_groups", "candidate_ids", "conditions", "verifier_roster", "resource_configuration", "cost_calibration"],
    }


def assert_unique_recordings(rows: list[dict]) -> None:
    seen = set()
    for row in rows:
        key = (
            row.get("experiment_id", EXPERIMENT_ID),
            row.get("related_group_id"),
            row.get("candidate_id"),
            row.get("attack_id"),
            row.get("attack_condition"),
            row.get("aggregation_method"),
            row.get("dependency_model"),
        )
        if key in seen:
            raise ValueError("duplicate Experiment 3 recording")
        seen.add(key)


def collapse_to_groups(rows: list[dict]) -> list[dict]:
    """One analysis row per question group. Candidate rows are not resampled separately."""
    if not any("candidate_id" in row for row in rows):
        return rows
    grouped: dict[tuple, list[dict]] = {}
    for row in rows:
        key = (row["related_group_id"], row["attack_condition"], row["aggregation_method"], row["dependency_model"], row["benchmark"])
        grouped.setdefault(key, []).append(row)
    collapsed = []
    for key in sorted(grouped):
        members = grouped[key]
        analyzable = [row for row in members if row.get("execution_status") == "complete" and row.get("validation_loss") is not None and row.get("gold_label") not in {None, "UNRESOLVED", "UNAUTHORIZED"}]
        base = dict(members[0])
        base.pop("candidate_id", None)
        if not analyzable:
            base["validation_loss"] = None
            base["gold_label"] = "UNRESOLVED"
            base["decision"] = "unresolved"
            base["coverage"] = 0
            base["uncertainty"] = 0
            base["execution_status"] = "incomplete"
        else:
            base["validation_loss"] = sum(row["validation_loss"] for row in analyzable) / len(analyzable)
            base["coverage"] = sum(float(row["coverage"]) for row in analyzable) / len(analyzable)
            base["uncertainty"] = sum(float(row["uncertainty"]) for row in analyzable) / len(analyzable)
            # The group row carries the mean loss. It is not one candidate's label.
            base["gold_label"] = "GROUP_AGGREGATE"
            base["decision"] = "group_aggregate"
            base["execution_status"] = "complete"
        base["candidate_rows"] = len(members)
        base["analyzable_candidate_rows"] = len(analyzable)
        collapsed.append(base)
    return collapsed


def decision_validation_loss(counts: dict, weights: dict) -> float:
    """Same decision loss as Metrics.validation_loss. Cost is not included."""
    examples = int(counts.get("examples") or 0)
    if examples <= 0:
        raise ValueError("decision loss requires at least one analyzable example")
    for field in ("false_accept", "false_reject", "uncertain"):
        if weights.get(field) is None:
            raise ValueError(f"decision loss weight {field} is absent")
    return (
        counts.get("false_accept", 0) * weights["false_accept"]
        + counts.get("false_reject", 0) * weights["false_reject"]
        + counts.get("uncertain", 0) * weights["uncertain"]
    ) / examples


def analyze_recordings(rows: list[dict], *, evidence_label: str, resamples: int | None, confidence_level: float | None, seed: int | None) -> dict:
    """Summarize one evidence class. Empirical and synthetic rows stay separate."""
    if evidence_label not in {"EMPIRICAL", "SYNTHETIC"}:
        raise ValueError("evidence label must be EMPIRICAL or SYNTHETIC")
    if any(row.get("evidence_label") != evidence_label for row in rows):
        raise ValueError("rows mix evidence labels")
    assert_unique_recordings(rows)
    validate_rows(rows)
    # Candidate rows keep their gold labels. paired_loss_differences resamples
    # related_group_id, so two candidates from one question are not independent draws.
    metric_rows = []
    for row in rows:
        item = dict(row)
        target = row.get("attack_target") or []
        if target:
            item["attack_condition"] = row["attack_condition"] + " [" + ",".join(target) + "]"
        metric_rows.append(item)
    metrics = method_metrics(metric_rows)
    differences = paired_loss_differences(metric_rows, resamples=resamples, confidence_level=confidence_level, seed=seed)
    worst = []
    for method in METHODS:
        losses = [row["validation_loss"] for row in metrics if row["aggregation_method"] == method and row["validation_loss"] is not None]
        worst.append({"aggregation_method": method, "evidence_label": evidence_label, "worst_case_loss": max(losses) if losses else None, "cells": len(losses)})
    classified = [binary_correctness(row) for row in rows]
    group_ids = {row.get("related_group_id") for row in rows}
    failed = sum(row.get("execution_status") != "complete" for row in rows)
    return {
        "evidence_label": evidence_label,
        "recording_rows": len(rows),
        "group_rows": len(group_ids),
        "metrics": metrics,
        "paired_differences": differences,
        "worst_case_loss": worst,
        "correctness_counts": {name: classified.count(name) for name in ("correct_acceptance", "correct_rejection", "false_acceptance", "false_rejection")},
        "unresolved_or_unclassified": classified.count(None),
        "failed_executions": failed,
        "imputed": 0,
    }


def build_manifest(root: Path | None = None) -> dict:
    root = Path(root) if root is not None else ROOT
    roster = load_roster(root)
    plan = matched_plan(root)
    calibration = verify_bundle(root)
    from evaluation.experiments.experiment3.execution_readiness import BUDGET_MS, COEFFICIENT, execution_report
    gate = execution_report(root)
    settings = _signed_settings(root)
    artifact_validation = calibration["artifact_validation"]
    manifest = {
        "record_type": "experiment3_empirical_run_manifest_v1",
        "experiment_id": EXPERIMENT_ID,
        "branch": _git_branch(root),
        "git_commit": _git_commit(root),
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "empirical_collection_started": False,
        "verifiers_called": False,
        "final_test_accessed": False,
        "rows_written": 0,
        "imputed_labels": 0,
        "gate_status": gate.get("status"),
        "historical_approval_gate": assess(root).get("status"),
        "independent_human_approval": False,
        "contributor_signatures_obtained": False,
        "eligibility": {
            "manifest": roster["eligibility_manifest"],
            "body_sha256": roster["eligibility_body_sha256"],
            "dataset_version": roster["dataset_version"],
            "label_protocol": roster["label_protocol"],
            "groups": roster["groups"],
            "candidates": roster["candidates"],
            "groups_by_benchmark": roster["groups_by_benchmark"],
            "output_lf_sha256": roster["output_lf_sha256"],
            "collection_authorized": roster["collection_authorized"],
            "does_not_authorize": roster["does_not_authorize"],
        },
        "plan": {key: value for key, value in plan.items() if key != "executed"},
        "calibration": {
            "bundle": calibration["bundle"],
            "valid": calibration["all_frozen_files_match"],
            "calibration_id": calibration["calibration_id"],
            "input_digest": calibration["input_digest"],
            "method": calibration["method"],
            "cost_units": calibration["cost_units"],
            "attempt_count": calibration["attempt_count"],
            "calibration_eligible_attempts": calibration["calibration_eligible_attempts"],
            "warmup_attempts": calibration["warmup_attempts"],
            "resource_manifest_id": artifact_validation.get("resource_manifest_id"),
            "setup_fingerprint": artifact_validation.get("setup_fingerprint"),
            "resource_manifest_id_matches_freeze": artifact_validation.get("resource_manifest_id") == calibration["resource_manifest_id"],
            "setup_fingerprint_matches_freeze": artifact_validation.get("setup_fingerprint") == calibration["setup_fingerprint"],
            "code_revision": artifact_validation.get("code_revision"),
            "estimates": calibration["estimates"],
            "policy_fitting_authorized_by_freeze": calibration["policy_fitting_authorized_by_freeze"],
            "files": calibration["files"],
        },
        "reputation": {
            "behavior": authoritative_behavior(),
            "snapshot_written": False,
            "snapshot_blockers": snapshot_blockers(root),
        },
        "policy": {"artifact_written": False, "blockers": policy_blockers(root)},
        "loss": {
            "signed_settings_present": settings is not None,
            "false_acceptance": 1.0,
            "false_rejection": 1.0,
            "uncertainty": 0.2,
            "decision_threshold": 0.55,
            "resource_coefficient": COEFFICIENT,
            "verifier_budget": BUDGET_MS,
            "cost_included": True,
            "selected_configuration_is_empirically_optimized": False,
            "signature_status": "unsigned; research-lead execution authorization is recorded separately and is not a signature",
        },
        "blockers": collection_blockers(root),
        "recording_schema": list(RECORDING_FIELDS),
        "historical_rehearsal": {
            "used_as_experiment3_dataset": False,
            "present_in_checkout": False,
            "recorded_external_archive": "research_v1_development_rehearsal_662bd5c.zip",
            "recorded_archive_sha256": "f688faff1cf4a25abe30d7e6516a0eab58bd0015a78d6863054c0435491d10f0",
            "note": "The ZIP is not in this checkout. Phase C listed its members and did not open the payload. It is not the 372-group Development collection.",
        },
        "reproduce": "python evaluation/experiments/experiment3/empirical_runner.py",
    }
    manifest["plan"]["executed"] = False
    return manifest


def _dump(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run(root: Path | None = None, destination: Path | None = None) -> dict:
    """Write a status manifest. This function does not call verifiers or invent rows."""
    root = Path(root) if root is not None else ROOT
    destination = Path(destination) if destination is not None else root / "evaluation/experiments/experiment3/empirical"
    if "final_test" in destination.as_posix().lower():
        raise RuntimeError("refusing to write Experiment 3 output under a Final Test path")
    blockers = collection_blockers(root)
    destination.mkdir(parents=True, exist_ok=True)
    manifest = build_manifest(root)
    results = {
        "record_type": "experiment3_empirical_results_v1",
        "evidence_label": None,
        "status": "NOT_COLLECTED" if blockers else "AUTHORIZED_NOT_EXECUTED",
        "rows": [],
        "reason": "Verifier execution did not start." if blockers else "Automated integrity checks passed. This command does not call verifiers.",
        "final_test_accessed": False,
        "independent_human_approval": False,
        "fabricated_signatures": False,
    }
    metrics = {
        "record_type": "experiment3_empirical_metrics_v1",
        "status": "NOT_COMPUTED",
        "evidence_label": None,
        "reason": "No empirical Development recordings exist. Proposed loss weights were not applied.",
        "metrics": [],
    }
    bootstrap = {
        "record_type": "experiment3_empirical_bootstrap_v1",
        "status": "NOT_COMPUTED",
        "evidence_label": None,
        "resamples": None,
        "confidence_level": None,
        "seed": None,
        "reason": "Bootstrap requires empirical group-level rows. None were collected.",
        "paired_differences": [],
    }
    _dump(destination / "run_manifest.json", manifest)
    _dump(destination / "results.json", results)
    _dump(destination / "metrics.json", metrics)
    _dump(destination / "bootstrap_results.json", bootstrap)
    return manifest


def main() -> int:
    manifest = run(ROOT)
    print(json.dumps({
        "empirical_collection_started": manifest["empirical_collection_started"],
        "gate_status": manifest["gate_status"],
        "groups": manifest["eligibility"]["groups"],
        "candidates": manifest["eligibility"]["candidates"],
        "blocker_count": len(manifest["blockers"]),
        "calibration_valid": manifest["calibration"]["valid"],
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
