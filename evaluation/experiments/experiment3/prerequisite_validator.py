"""Experiment 3 prerequisite states. A synthetic fixture is never an empirical recording."""
from __future__ import annotations

import json
from pathlib import Path

from evaluation.analysis.experiment3 import protocol_gaps, validate_rows
from evaluation.data_preparation.final_test_workflow import ROOT, canonical_bytes, sha256_bytes, sha256_file

SPEC = "evaluation/config/experiments/experiment3_specification.json"
CORPUS = "evaluation/config/experiments/experiment3_corpus_approval_package.json"
COLLECTION = "evaluation/config/experiments/experiment3_collection_configuration.json"
DEPENDENCY = "evaluation/config/experiments/experiment3_dependency_configuration.json"
REPUTATION = "evaluation/config/experiments/experiment3_reputation_policy_inputs.json"
SETTINGS_PROPOSAL = "evaluation/config/experiments/experiment3_settings_proposal.json"
DEPENDENCY_DECISION = "evaluation/config/experiments/experiment3_dependency_decision.json"
PROTOCOL_APPROVAL = "evaluation/config/experiments/approvals/experiment3_protocol_approval_record.json"
CORPUS_APPROVAL = "evaluation/config/experiments/approvals/experiment3_corpus_approval_record.json"
DEPENDENCY_APPROVAL = "evaluation/config/experiments/approvals/experiment3_dependency_approval_record.json"
COLLECTION_AUTHORIZATION = "evaluation/config/experiments/approvals/experiment3_collection_authorization_record.json"
ACCEPTED_SETTING_FIELDS = ("false_acceptance_loss", "false_rejection_loss", "uncertainty_loss", "resource_coefficient", "decision_threshold", "verifier_budget", "suppression_mode", "bootstrap_resamples", "confidence_level", "bootstrap_seed", "sample_size_justification")
ELIGIBILITY = "evaluation/artifacts/person1/research_v1_exploratory_eligibility_approved_v1/eligibility_manifest.json"
CORPUS_FILE = "evaluation/artifacts/person1/development_evidence_corpus_v1/corpus.json"

READY_FOR_APPROVAL = "READY_FOR_APPROVAL"
READY_FOR_COLLECTION_AUTHORIZATION = "READY_FOR_COLLECTION_AUTHORIZATION"
READY_FOR_DEVELOPMENT_COLLECTION = "READY_FOR_DEVELOPMENT_COLLECTION"
READY_FOR_EMPIRICAL_EXPERIMENT = "READY_FOR_EMPIRICAL_EXPERIMENT"
READY_FOR_EMPIRICAL_EXPERIMENT_ANALYSIS = "READY_FOR_EMPIRICAL_EXPERIMENT_ANALYSIS"
BLOCKED = "BLOCKED"


def _load(root: Path, relative: str) -> dict:
    path = root / relative
    if not path.is_file():
        raise FileNotFoundError(relative)
    if "final_test" in relative.replace("\\", "/"):
        raise RuntimeError(f"refusing a Final Test path: {relative}")
    return json.loads(path.read_text(encoding="utf-8"))


def _eligibility_body_hash(root: Path) -> str:
    manifest = _load(root, ELIGIBILITY)
    body = {key: value for key, value in manifest.items() if key != "eligibility_manifest_sha256"}
    return sha256_bytes(canonical_bytes(body))


def _signed(record: dict) -> bool:
    return bool(record.get("status") == "APPROVED" and record.get("approved") is True and record.get("decision") == "APPROVED" and record.get("approver") and record.get("approval_date"))


def _hash_ok(root: Path, record: dict) -> bool:
    artifact = str(record.get("artifact") or "")
    if "final_test" in artifact.replace("\\", "/"):
        return False
    path = root / artifact
    return path.is_file() and sha256_file(path) == record.get("artifact_sha256")


def _settings_accepted(record: dict) -> bool:
    settings = record.get("approved_settings")
    return isinstance(settings, dict) and all(settings.get(field) is not None for field in ACCEPTED_SETTING_FIELDS)


def assess(root: Path | None = None) -> dict:
    root = root or ROOT
    blockers: list[str] = []
    try:
        spec = _load(root, SPEC)
        corpus = _load(root, CORPUS)
        collection = _load(root, COLLECTION)
        dependency = _load(root, DEPENDENCY)
        reputation = _load(root, REPUTATION)
        eligibility = _load(root, ELIGIBILITY)
        proposal = _load(root, spec.get("settings_proposal") or SETTINGS_PROPOSAL)
        dependency_decision = _load(root, DEPENDENCY_DECISION)
        protocol_approval = _load(root, spec.get("approval_records", {}).get("protocol", PROTOCOL_APPROVAL))
        corpus_approval = _load(root, spec.get("approval_records", {}).get("corpus", CORPUS_APPROVAL))
        dependency_approval = _load(root, spec.get("approval_records", {}).get("dependency", DEPENDENCY_APPROVAL))
        collection_approval = _load(root, spec.get("approval_records", {}).get("collection", COLLECTION_AUTHORIZATION))
    except FileNotFoundError as exc:
        return {"status": BLOCKED, "blockers": [f"missing {exc}"]}
    except RuntimeError as exc:
        return {"status": BLOCKED, "blockers": [str(exc)]}

    if spec.get("comparison_methods") != ["full_minimax", "fixed_reputation_weighted", "fixed_dependency_group"]:
        blockers.append("comparison methods are incomplete")
    gaps = protocol_gaps(spec)
    if not spec.get("research_questions") or not spec.get("outcomes") or not spec.get("analysis") or gaps:
        blockers.append("protocol specification is incomplete")
        blockers.extend(gaps)
    if spec.get("synthetic_fixture", {}).get("satisfies_empirical_recording_requirement") is not False:
        blockers.append("synthetic fixture was treated as an empirical recording")
    expected_eligibility = "f2cc0fd108b961bf4795767df4f90e92d7fa0f418ef9865d0206f32d7b45282d"
    if spec.get("eligibility_manifest_sha256") != expected_eligibility or eligibility.get("eligibility_manifest_sha256") != expected_eligibility:
        blockers.append("eligibility manifest reference does not match the approved hash")
    if _eligibility_body_hash(root) != expected_eligibility:
        blockers.append("eligibility manifest body hash changed")
    corpus_path = root / CORPUS_FILE
    if not corpus_path.is_file() or sha256_file(corpus_path) != corpus.get("corpus_sha256"):
        blockers.append("corpus checksum does not match the approval package")
    if corpus.get("checksum_status") == "CONFLICTING_PROVENANCE":
        blockers.append("corpus file hash conflicts with the preparation report")
    if proposal.get("approved") is True or proposal.get("status") != "PROPOSED_PENDING_APPROVAL":
        blockers.append("proposal cannot be used as an approval")
    if dependency_decision.get("approved") is True or dependency_decision.get("empirical_evidence") != "none":
        blockers.append("dependency decision package is not an approval and has no measured evidence")
    for label, record in (("protocol", protocol_approval), ("corpus", corpus_approval), ("dependency", dependency_approval), ("collection", collection_approval)):
        if "final_test" in str(record.get("artifact", "")).replace("\\", "/"):
            blockers.append("refusing a Final Test path")
        elif not _hash_ok(root, record):
            blockers.append(f"{label} approval record hash does not match the artifact")
    if spec.get("approved") is True and not _signed(protocol_approval):
        blockers.append("inline protocol flag is not an approval record")
    if corpus.get("approved") is True and not _signed(corpus_approval):
        blockers.append("inline corpus flag is not an approval record")
    claims_freeze = corpus.get("frozen") is True or corpus_approval.get("freeze_status") == "FROZEN"
    valid_freeze = corpus.get("frozen") is True and corpus_approval.get("freeze_status") == "FROZEN" and _signed(corpus_approval)
    if claims_freeze and not valid_freeze:
        blockers.append("corpus freeze requires a signed approval record")
    if collection.get("collection_authorized") is True and not (_signed(collection_approval) and collection_approval.get("collection_authorized") is True):
        blockers.append("collection authorization requires a signed authorization record")
    if _signed(collection_approval) and not (_signed(protocol_approval) and _settings_accepted(protocol_approval) and _signed(corpus_approval) and _signed(dependency_approval)):
        blockers.append("collection authorization requires approved protocol and corpus")
    required_collection = ("roster", "corpus", "verifiers", "environment", "execution", "logging", "cost_units")
    if any(key not in collection for key in required_collection) or len(collection.get("verifiers") or []) != 4:
        blockers.append("collection configuration is incomplete")
    if collection.get("development_recordings_available") is True and collection.get("synthetic_fixture_is_not_a_recording") is not True:
        blockers.append("recordings flag does not separate the synthetic fixture")
    if dependency.get("status") not in {"PROVISIONAL", "EMPIRICAL"} or dependency.get("empirical_evidence") not in {"none", "recorded"}:
        blockers.append("dependency configuration is invalid")
    if dependency.get("status") == "EMPIRICAL" and dependency.get("empirical_evidence") != "recorded":
        blockers.append("empirical dependency status lacks recorded evidence")
    if dependency.get("synthetic_two_group_registry", {}).get("usable_as_empirical_dependency") is not False:
        blockers.append("synthetic dependency groups were marked empirical")
    recordings = int(collection.get("empirical_recording_count") or 0)
    if collection.get("empirical_recording_label") == "SYNTHETIC":
        recordings = 0
        if collection.get("development_recordings_available") is True:
            blockers.append("synthetic recordings were counted as Development recordings")
    costs_available = bool(collection.get("cost_measurements_available")) and collection.get("cost_measurement_id") not in {None, "", "UNKNOWN"}
    reputation_available = int(reputation.get("observations_count") or 0) > 0 and reputation.get("synthetic_fixture_reputations_are_empirical") is False and reputation.get("reputation_source") not in {None, "synthetic_fixture"}

    if blockers:
        return {"status": BLOCKED, "blockers": blockers, "empirical_recording_count": recordings}

    status = READY_FOR_APPROVAL
    approvals_present = _signed(protocol_approval) and _settings_accepted(protocol_approval) and _signed(corpus_approval) and _signed(dependency_approval)
    if approvals_present:
        status = READY_FOR_COLLECTION_AUTHORIZATION
    def hash_known(row: dict) -> bool:
        if row.get("verifier_name") == "rule":
            return row.get("rule_version_hash") not in {None, "UNKNOWN"}
        return row.get("model_weight_snapshot_hash") not in {None, "UNKNOWN"}

    hashes_known = all(hash_known(row) for row in collection["verifiers"])
    collection_signed = _signed(collection_approval) and collection_approval.get("collection_authorized") is True
    if status == READY_FOR_COLLECTION_AUTHORIZATION and collection_signed and valid_freeze and hashes_known and collection.get("environment", {}).get("random_seed") is not None:
        status = READY_FOR_DEVELOPMENT_COLLECTION
    dependency_ready = dependency.get("status") == "PROVISIONAL" or dependency.get("empirical_evidence") == "recorded"
    if status == READY_FOR_DEVELOPMENT_COLLECTION and recordings > 0 and costs_available and reputation_available and dependency_ready:
        status = READY_FOR_EMPIRICAL_EXPERIMENT
    analysis_blockers = _analysis_blockers(root, spec, protocol_approval if _signed(protocol_approval) else {})
    if status == READY_FOR_EMPIRICAL_EXPERIMENT and not analysis_blockers:
        status = READY_FOR_EMPIRICAL_EXPERIMENT_ANALYSIS
    return {"status": status, "blockers": [], "protocol_complete": not gaps, "analysis_blockers": analysis_blockers,
            "empirical_recording_count": recordings, "costs_available": costs_available,
            "reputation_observations": int(reputation.get("observations_count") or 0)}


def _analysis_blockers(root: Path, spec: dict, protocol_approval: dict) -> list[str]:
    pending = []
    settings = protocol_approval.get("approved_settings") if _signed(protocol_approval) else None
    accepted = isinstance(settings, dict) and all(settings.get(field) is not None for field in ("bootstrap_resamples", "confidence_level", "bootstrap_seed", "sample_size_justification"))
    if not accepted:
        pending.append("statistical analysis configuration is pending approval")
    result = spec.get("empirical_results") or {}
    relative = result.get("path")
    if not relative:
        pending.append("empirical Experiment 3 result rows are absent")
        return pending
    path = root / relative
    if "final_test" in str(relative).replace("\\", "/") or "synthetic" in str(relative).replace("\\", "/"):
        pending.append("empirical analysis cannot read Final Test or synthetic results")
        return pending
    if not path.is_file():
        pending.append("empirical Experiment 3 result rows are absent")
        return pending
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows = payload.get("rows") if isinstance(payload, dict) else payload
    try:
        validate_rows(rows)
    except ValueError as exc:
        pending.append(str(exc))
        return pending
    if rows[0].get("evidence_label") != "EMPIRICAL":
        pending.append("result rows are not empirical")
    return pending
