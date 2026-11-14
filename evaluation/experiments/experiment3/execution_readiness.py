"""Automated Experiment 3 execution checks.

Human signatures are not a prerequisite and are not fabricated here. A JSON
``approved`` flag does not authorize collection. Authorization is the
research-lead instruction recorded in the execution configuration, and it is
accepted only when the selected values and input hashes match.
"""

from __future__ import annotations

import hashlib
import json
import math
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CONFIG_RELATIVE = "evaluation/experiments/experiment3/execution_configuration.json"
INPUTS_RELATIVE = "evaluation/datasets/research_v1_exploratory/research_v1_exploratory_v1/development_verifier_inputs.jsonl"
CORPUS_RELATIVE = "evaluation/artifacts/person1/development_evidence_corpus_v1/corpus.json"
DEPENDENCY_RELATIVE = "evaluation/config/experiments/experiment3_dependency_configuration.json"
REPUTATION_RELATIVE = "evaluation/config/experiments/experiment3_reputation_policy_inputs.json"
CALIBRATION_ID = "cc7e7ca8882f602b9854bf21b80b8a7bf70f6c70d05ccd12787322a84a12477d"
COEFFICIENT = 1.3399597937725295e-05
BUDGET_MS = 14996.39091498102
SEED = 20261113
# 744 candidates x (1 clean + 2 structural groups x 3 kinds) x 3 methods.
# The 8,928 figure is the one-column-per-kind count and is not this grid.
EXPECTED_CELLS = 15624
AUTHORIZATION_STATEMENT = (
    "Experiment 3 Development execution is authorized by the research lead "
    "under the documented session instruction. Independent human approval and "
    "other contributors' signatures were not obtained. This record is not a "
    "signature and does not modify another contributor's artifact."
)
STATUSES = (
    "BLOCKED",
    "TECHNICALLY_READY",
    "AUTHORIZED_BY_RESEARCH_LEAD",
    "EMPIRICALLY_EXECUTED",
    "EMPIRICALLY_COMPLETED",
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _close(left, right) -> bool:
    return isinstance(left, (int, float)) and isinstance(right, (int, float)) and math.isfinite(left) and math.isfinite(right) and math.isclose(left, right, rel_tol=0.0, abs_tol=1e-9)


def configuration_errors(payload: dict, *, coefficient: float, budget: float) -> list[str]:
    """Reject a payload that does not bind the selected configuration.

    ``approved: true`` is ignored. Matching requires the statement and values.
    """
    errors = []
    if not isinstance(payload, dict):
        return ["execution configuration is not an object"]
    if payload.get("approved") is True or payload.get("approver") or payload.get("approval_date"):
        errors.append("execution configuration carries a signature field; signatures are not accepted from this file")
    if payload.get("independent_human_approval") is not False:
        errors.append("execution configuration must record that independent human approval was not obtained")
    if payload.get("contributor_signatures_obtained") is not False:
        errors.append("execution configuration must record that contributor signatures were not obtained")
    if payload.get("fabricated_signatures") is not False:
        errors.append("execution configuration must record that no signature was fabricated")
    if payload.get("authorization_statement") != AUTHORIZATION_STATEMENT:
        errors.append("authorization statement does not match the recorded research-lead instruction")
    if payload.get("selected_configuration_is_empirically_optimized") is not False:
        errors.append("the selected coefficient and budget must be marked as not empirically optimized")
    expected = {
        "false_acceptance_loss": 1.0,
        "false_rejection_loss": 1.0,
        "uncertainty_loss": 0.2,
        "decision_threshold": 0.55,
        "suppression_mode": "unavailable",
        "bootstrap_resamples": 2000,
        "confidence_level": 0.95,
        "bootstrap_seed": SEED,
        "reputation_prior_alpha": 1.0,
        "reputation_prior_beta": 1.0,
        "reputation_observations": 0,
        "calibration_id": CALIBRATION_ID,
        "dependency_model": "structural_shared_resource_v1",
        "population_groups": 372,
        "population_candidates": 744,
    }
    for key, value in expected.items():
        if payload.get(key) != value:
            errors.append(f"execution configuration {key} does not match the selected protocol")
    if not _close(payload.get("resource_coefficient_loss_per_ms"), coefficient):
        errors.append("resource coefficient does not match the selected loss-per-millisecond value")
    if not _close(payload.get("verifier_budget_ms"), budget):
        errors.append("verifier budget does not match the selected confidence-entry budget")
    return errors


def _ollama_available() -> tuple[bool, str]:
    try:
        with urllib.request.urlopen("http://127.0.0.1:11434/api/tags", timeout=3) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        return False, f"Ollama is not reachable: {type(exc).__name__}: {exc}"
    names = {item.get("name") for item in payload.get("models") or [] if isinstance(item, dict)}
    if "llama3.2:3b" not in names and "llama3.2:latest" not in names:
        return False, "Ollama is reachable but llama3.2:3b is not installed"
    return True, "Ollama responded and llama3.2 is installed"


def _verifier_gaps(root: Path) -> list[str]:
    gaps = []
    try:
        import app.verifiers.rule_verifier  # noqa: F401
        import app.verifiers.semantic_verifier  # noqa: F401
        import app.verifiers.evidence_verifier  # noqa: F401
        import app.verifiers.confidence_verifier  # noqa: F401
    except Exception as exc:
        gaps.append(f"verifier implementation import failed: {type(exc).__name__}: {exc}")
    if not (root / CORPUS_RELATIVE).is_file():
        gaps.append("development evidence corpus is missing")
    available, detail = _ollama_available()
    if not available:
        gaps.append(detail)
    return gaps


def _selected_budget(root: Path) -> tuple[float, float]:
    from evaluation.experiments.experiment3.resource_sensitivity import frozen_calibration, roster_costs
    frozen = frozen_calibration()
    if frozen["calibration_id"] != CALIBRATION_ID:
        raise RuntimeError("resource proposal calibration id differs from the selected binding")
    if root != ROOT and not (root / "artifacts/research-v1-development-cost-calibration-v1/calibration.json").is_file():
        raise RuntimeError("checkout has no frozen calibration to bind")
    costs = roster_costs()
    triples = [costs[team] for team in costs if len(team) == 3 and "confidence" in team]
    if not triples:
        raise RuntimeError("frozen calibration has no confidence size-3 team")
    return 0.2 / frozen["means_ms"]["confidence"], min(triples)


def execution_report(root: Path | None = None) -> dict:
    root = Path(root) if root is not None else ROOT
    blockers: list[str] = []
    coefficient, budget = COEFFICIENT, BUDGET_MS
    try:
        coefficient, budget = _selected_budget(root)
    except Exception as exc:
        blockers.append(f"frozen calibration budget check failed: {exc}")
    if not _close(coefficient, COEFFICIENT) or not _close(budget, BUDGET_MS):
        blockers.append("recomputed coefficient or confidence-entry budget differs from the selected constants")
    config_path = root / CONFIG_RELATIVE
    payload = {}
    if not config_path.is_file():
        blockers.append("execution configuration is missing")
    else:
        try:
            payload = _load(config_path)
        except (OSError, json.JSONDecodeError) as exc:
            blockers.append(f"execution configuration is unreadable: {exc}")
        else:
            blockers.extend(configuration_errors(payload, coefficient=COEFFICIENT, budget=BUDGET_MS))
    inputs = root / INPUTS_RELATIVE
    if "final_test" in INPUTS_RELATIVE:
        blockers.append("verifier inputs path is a Final Test path")
    if not inputs.is_file():
        blockers.append("development verifier inputs are missing")
    dependency_path = root / DEPENDENCY_RELATIVE
    if dependency_path.is_file():
        dependency = _load(dependency_path)
        if dependency.get("configuration_version") != "structural_shared_resource_v1":
            blockers.append("dependency configuration is not structural_shared_resource_v1")
        if dependency.get("empirical_evidence") != "none" or dependency.get("measured_dependence_claim") is not False:
            blockers.append("dependency configuration claims measured evidence it does not have")
        if dependency.get("approved") is True:
            blockers.append("dependency configuration approved flag is not an authorization")
    else:
        blockers.append("dependency configuration is missing")
    reputation_path = root / REPUTATION_RELATIVE
    if reputation_path.is_file():
        reputation = _load(reputation_path)
        if reputation.get("approved") is True:
            blockers.append("reputation input approved flag is not an authorization")
        if reputation.get("observations_count") != 0:
            blockers.append("reputation inputs contain observations this execution did not approve")
    else:
        blockers.append("reputation inputs are missing")
    from evaluation.experiments.experiment3.calibration_integrity import verify_bundle
    from evaluation.experiments.experiment3.development_roster import load_roster
    try:
        calibration = verify_bundle(root)
    except Exception as exc:
        calibration = {"all_frozen_files_match": False, "calibration_id": None}
        blockers.append(f"calibration integrity failed: {exc}")
    else:
        if not calibration["all_frozen_files_match"]:
            blockers.append("frozen cost-calibration bundle failed integrity validation")
        if calibration.get("calibration_id") != CALIBRATION_ID:
            blockers.append("calibration id does not match the selected binding")
        if calibration.get("policy_fitting_authorized_by_freeze") is not False:
            blockers.append("cost-calibration freeze unexpectedly authorizes policy fitting")
    try:
        roster = load_roster(root)
    except Exception as exc:
        roster = None
        blockers.append(str(exc))
    else:
        if roster["collection_authorized"] is not False or roster["final_test_authorized"] is not False:
            blockers.append("eligibility manifest authorization flags were changed")
        if roster["groups"] != 372 or roster["candidates"] != 744:
            blockers.append("eligibility roster is not the 372-group Development population")
    gaps = _verifier_gaps(root) if root == ROOT else ["verifier runtime was not probed outside the live checkout"]
    results_path = root / "evaluation/experiments/experiment3/empirical/results.json"
    completed_rows = 0
    evidence = None
    if results_path.is_file():
        try:
            stored = _load(results_path)
        except (OSError, json.JSONDecodeError):
            stored = {}
        evidence = stored.get("evidence_label")
        completed_rows = sum(1 for row in stored.get("rows") or [] if row.get("execution_status") == "complete" and row.get("evidence_label") == "EMPIRICAL")
        if evidence == "EMPIRICAL" and stored.get("status") not in {None, "EMPIRICAL", "PARTIAL", "COMPLETE"}:
            blockers.append("empirical results file has an inconsistent status")
    integrity_ok = not blockers
    verifiers_available = not gaps
    authorized = integrity_ok
    if completed_rows >= EXPECTED_CELLS and evidence == "EMPIRICAL":
        status = "EMPIRICALLY_COMPLETED"
    elif completed_rows > 0 and evidence == "EMPIRICAL":
        status = "EMPIRICALLY_EXECUTED"
    elif authorized and verifiers_available:
        status = "AUTHORIZED_BY_RESEARCH_LEAD"
    elif authorized:
        status = "TECHNICALLY_READY"
    else:
        status = "BLOCKED"
    return {
        "status": status,
        "technically_ready": authorized and verifiers_available,
        "authorized_by_research_lead": authorized,
        "empirically_executed": completed_rows > 0 and evidence == "EMPIRICAL",
        "empirically_completed": status == "EMPIRICALLY_COMPLETED",
        "independent_human_approval": False,
        "contributor_signatures_obtained": False,
        "fabricated_signatures": False,
        "collection_started": False,
        "recordings_created": False,
        "empirical_recording_count": completed_rows,
        "verifiers_available": verifiers_available,
        "verifier_gaps": gaps,
        "blockers": blockers,
        "configuration_sha256": _sha256(config_path) if config_path.is_file() else None,
        "population_groups": None if roster is None else roster["groups"],
        "population_candidates": None if roster is None else roster["candidates"],
        "calibration_id": None if not isinstance(calibration, dict) else calibration.get("calibration_id"),
        "resource_coefficient_loss_per_ms": COEFFICIENT,
        "verifier_budget_ms": BUDGET_MS,
        "bootstrap_seed": SEED,
        "selected_configuration_is_empirically_optimized": False,
    }
