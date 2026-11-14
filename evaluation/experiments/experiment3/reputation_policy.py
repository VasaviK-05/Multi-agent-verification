"""Experiment 3 binding to the existing reputation manager and policy builder.

This module does not fit a policy or write a reputation snapshot. Development
labels are not a permitted reputation source, and the update rule is unapproved.
"""

from __future__ import annotations

import json
from pathlib import Path

from app.reputation.reputation_manager import ReputationManager

INPUTS = "evaluation/config/experiments/experiment3_reputation_policy_inputs.json"
VERIFIER_ROSTER = ("semantic", "evidence", "rule", "confidence")


def authoritative_behavior() -> dict:
    """Facts taken from ReputationManager and the game policy builder."""
    return {
        "implementation": "app.reputation.reputation_manager.ReputationManager",
        "policy_implementation": "app.game.policy.build_policy",
        "comparison_implementation": "app.game.research.comparison.prepare_comparison",
        "equations": {
            "alpha": "prior_alpha + successes",
            "beta": "prior_beta + failures",
            "posterior_mean": "alpha / (alpha + beta)",
            "reported_reputation": "round(posterior_mean, 6)",
            "posterior_variance": "alpha * beta / ((alpha + beta)^2 * (alpha + beta + 1))",
        },
        "prior_alpha": ReputationManager.DEFAULT_ALPHA,
        "prior_beta": ReputationManager.DEFAULT_BETA,
        "cold_start_reported_reputation": 0.5,
        "smoothing": "Beta(1, 1) prior only. Successes and failures are integer observations, not confidence-weighted pseudo-counts.",
        "decay": None,
        "update": "A directional vote succeeds when its passed flag equals the external boolean label. Abstentions and verifiers that did not run add no observation.",
        "replay": "record_feedback ignores an exact replay of the same validation id and rejects a changed label or vote list.",
        "persistence": "export_state/restore_state round-trips priors, integer counts, and scoped feedback at schema version 1. That export is not a database write.",
        "history_helper": "app.game.offline.records.history_reputation learns only from a history partition. Experiment 3 inputs allow that source only after an approved update rule.",
        "policy_algorithm": "build_policy enumerates the feasible strategies and solves the minimax linear program. prepare_comparison restricts that matrix for fixed_reputation_weighted and fixed_dependency_group and solves each restricted game.",
        "reproducibility": "app.game.offline.build.verify_equivalent refits the same specification and compares the matrix, reputation snapshot, and probabilities. It is not invoked while the Experiment 3 inputs are unapproved.",
        "verifier_roster": list(VERIFIER_ROSTER),
        "approved_initialization": None,
    }


def load_inputs(root: Path) -> dict:
    path = Path(root) / INPUTS
    if "final_test" in path.as_posix().lower():
        raise RuntimeError("refusing a Final Test path")
    return json.loads(path.read_text(encoding="utf-8"))


def snapshot_blockers(root: Path) -> list[str]:
    """Reasons an experiment reputation snapshot must not be written."""
    payload = load_inputs(root)
    blockers = []
    if payload.get("approved") is True:
        blockers.append("reputation input file cannot mark itself approved")
    if payload.get("status") != "PENDING_PERSON3":
        blockers.append("reputation input status is not the recorded pending state")
    if int(payload.get("observations_count") or 0) <= 0:
        blockers.append("Person 3 reputation observations are absent")
    if payload.get("reputation_source") in {None, "", "synthetic_fixture"}:
        blockers.append("no approved reputation source is recorded")
    if payload.get("initialization") != "APPROVED":
        blockers.append("reputation initialization is PENDING_APPROVAL")
    if payload.get("update_rule") != "APPROVED":
        blockers.append("reputation update rule is PENDING_APPROVAL; History snapshots stay unused")
    if payload.get("smoothing") != "APPROVED":
        blockers.append("reputation smoothing is PENDING_APPROVAL")
    if payload.get("synthetic_fixture_reputations_are_empirical") is not False:
        blockers.append("synthetic fixture reputations are not an empirical source")
    permitted = str(payload.get("permitted_history") or "")
    if "Development outcomes are not a reputation source" not in permitted:
        blockers.append("Development outcomes are not a recorded reputation source")
    if payload.get("exported_policy_path") not in {None, ""}:
        blockers.append("a policy export path is recorded without an approved builder run")
    return blockers


def policy_blockers(root: Path) -> list[str]:
    """Reasons build_policy must not emit an Experiment 3 policy artifact."""
    blockers = list(snapshot_blockers(root))
    reports = root / "evaluation/experiments/experiment3/empirical/verifier_reports.jsonl"
    recording_count = 0
    if reports.is_file():
        with reports.open(encoding="utf-8") as handle:
            recording_count = sum(1 for line in handle if line.strip())
    if recording_count == 0:
        blockers.append("no empirical Development verifier recordings exist")
    blockers.extend([
        "the protocol approval record has no signed loss, threshold, resource coefficient, or verifier budget",
        "the cost-calibration freeze does not authorize policy fitting or budget selection",
        "the eligibility manifest does not authorize policy fitting",
    ])
    return blockers


def reproducible_state(manager: ReputationManager) -> dict:
    """Round-trip a caller-supplied manager. This does not create observations."""
    if not isinstance(manager, ReputationManager):
        raise TypeError("manager must be the authoritative ReputationManager")
    exported = manager.export_state()
    restored = ReputationManager()
    restored.restore_state(exported)
    repeated = restored.export_state()
    if exported != repeated:
        raise RuntimeError("reputation export did not reproduce")
    return exported
