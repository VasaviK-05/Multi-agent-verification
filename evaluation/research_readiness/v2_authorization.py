"""Fail-closed Final Test v2 release and scoring checks.

A template, a missing signature, or a self-declared boolean does not authorize
anything. This module does not read label bytes.
"""

from __future__ import annotations

import hashlib
import json
from datetime import date
from pathlib import Path

from evaluation.data_preparation.final_test_custody import load_appointment

ROOT = Path(__file__).resolve().parents[2]
SEALED_LABEL = ROOT / "evaluation/datasets/_custodian/final_test_research_v1_v2/labels.jsonl"
SEALED_MANIFEST = ROOT / "evaluation/datasets/final_test_research_v1_eval_v2/manifest.json"
SEALED_ROSTER = ROOT / "evaluation/datasets/final_test_research_v1_eval_v2/evaluation_roster.jsonl"
INDEPENDENT_APPOINTMENT = ROOT / "evaluation/config/research_v1/independent_custodian_appointment.json"
RELEASE_TEMPLATE = ROOT / "evaluation/config/research_v1/final_test_release_authorization_template.json"
SCORING_TEMPLATE = ROOT / "evaluation/config/research_v1/final_test_scoring_package.json"
SELF_CUSTODY = ROOT / "evaluation/config/research_v1/final_test_self_custody.json"
LABEL_LOCATION = ROOT / "evaluation/config/research_v1/final_test_label_custody_location.json"
DESIGNATED_APPOINTMENT = "evaluation/config/final_test_v2_custodian_appointment.json"

MANIFEST_SHA256 = "e572093a4f0420c03316c89c83b6a7ab665af3af894d19a1428a6b091d3319ee"
LABEL_SHA256 = "35b126ba350a942f42f11d1845e16e01fd755516d20b53faf3aaf616143858a6"
ROSTER_SHA256 = "3f8fcbf1e698174a9a7cf6c586ec51048bcc07ca11154b36fdef0dadc7796208"

FORBIDDEN_WITH_INDEPENDENT = frozenset({
    "dataset_creator",
    "developer",
    "researcher",
    "candidate_answer_author",
    "verifier_tuner",
    "development_evaluator",
})
KNOWN_ROLES = FORBIDDEN_WITH_INDEPENDENT | {"independent_custodian", "research_lead", "authorized_scorer"}


class CustodyAuthorizationError(PermissionError):
    """Final Test v2 release or scoring is not authorized."""


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _identity(value: str | None) -> str:
    return " ".join(str(value or "").casefold().split())


def dataset_creator_identity() -> str:
    return _identity(load_appointment().get("appointee"))


def _is_self_custody_record(record: dict | None) -> bool:
    if not isinstance(record, dict):
        return False
    kind = str(record.get("record_type") or "")
    return record.get("custody_mode") == "SELF_CUSTODY" or kind.startswith("final_test_v2_self_custody") or kind.startswith("self_custody_")


def validate_independent_appointment(record: dict | None) -> list[str]:
    """Return reasons a record is not an established independent appointment."""
    if not isinstance(record, dict):
        return ["missing_custodian_appointment"]
    reasons = []
    if _is_self_custody_record(record):
        reasons.append("self_custody_cannot_satisfy_independent_authorization")
    if record.get("record_type") != "independent_final_test_custodian_appointment_v1":
        reasons.append("unsupported_appointment_type")
    roles = set(record.get("roles") or [])
    unknown = roles - KNOWN_ROLES
    if unknown:
        reasons.append("unknown_roles")
    if "independent_custodian" in roles and roles & FORBIDDEN_WITH_INDEPENDENT:
        reasons.append("conflicting_custodian_roles")
    custodian = _identity(record.get("independent_custodian_id"))
    creator = dataset_creator_identity()
    if custodian and custodian == creator:
        reasons.append("creator_appointed_as_independent_custodian")
    if record.get("established") is True:
        reasons.append("self_declared_establishment_is_not_evidence")
    if not custodian:
        reasons.append("missing_independent_custodian_identity")
    if record.get("identity_verification") != "VERIFIED_EXTERNAL":
        reasons.append("missing_independent_verification")
    if not record.get("signature") or not record.get("approval_date"):
        reasons.append("unsigned_independent_appointment")
    return reasons


def _bound(record: dict, expected: dict) -> list[str]:
    reasons = []
    if record.get("approved") is not True or record.get("status") in {None, "NOT_AN_APPROVAL", "PENDING", "NOT_AUTHORIZED"}:
        reasons.append("unsigned_or_template")
    if not record.get("signature") or not record.get("approver") or not record.get("approval_date"):
        reasons.append("missing_signature")
    if record.get("revoked") is True:
        reasons.append("revoked")
    expires = record.get("expires_on")
    if isinstance(expires, str) and expires < date.today().isoformat():
        reasons.append("expired")
    pairs = (
        ("manifest_sha256", expected["manifest_sha256"], "manifest_hash_mismatch"),
        ("label_sha256", expected["label_sha256"], "label_hash_mismatch"),
        ("roster_sha256", expected["roster_sha256"], "roster_hash_mismatch"),
        ("protocol_sha256", expected.get("protocol_sha256"), "protocol_hash_mismatch"),
        ("dataset_version", expected["dataset_version"], "different_dataset"),
        ("custodian_id", expected.get("custodian_id"), "custodian_mismatch"),
    )
    for field, wanted, reason in pairs:
        if wanted is None:
            reasons.append("protocol_not_frozen" if field == "protocol_sha256" else reason)
        elif record.get(field) != wanted:
            reasons.append(reason)
    return reasons


def expected_binding(custodian_id: str | None, protocol_sha256: str | None) -> dict:
    return {
        "dataset_version": "research_v1_final_test_v2_exploratory_v1",
        "manifest_sha256": MANIFEST_SHA256,
        "label_sha256": LABEL_SHA256,
        "roster_sha256": ROSTER_SHA256,
        "protocol_sha256": protocol_sha256,
        "custodian_id": custodian_id,
    }


def release_blockers(record: dict | None, expected: dict) -> list[str]:
    if not isinstance(record, dict):
        return ["unsigned_release_authorization"]
    if _is_self_custody_record(record):
        return ["self_custody_cannot_satisfy_independent_authorization"]
    reasons = _bound(record, expected)
    if record.get("label_release") != "AUTHORIZED":
        reasons.append("release_not_authorized")
    if record.get("scoring_authorized") is True:
        reasons.append("release_record_must_not_grant_scoring")
    return reasons


def scoring_blockers(record: dict | None, release: dict | None, expected: dict) -> list[str]:
    release_reasons = release_blockers(release, expected)
    reasons = ["unsigned_release_authorization"] if release_reasons else []
    if "self_custody_cannot_satisfy_independent_authorization" in release_reasons:
        reasons.append("self_custody_cannot_satisfy_independent_authorization")
    if isinstance(record, dict) and _is_self_custody_record(record):
        return reasons + ["self_custody_cannot_satisfy_independent_authorization"]
    if not isinstance(record, dict):
        return reasons + ["unsigned_scoring_authorization"]
    reasons.extend(_bound(record, expected))
    if record.get("scoring_authorized") is not True:
        reasons.append("scoring_not_authorized")
    if record.get("label_release") == "AUTHORIZED":
        reasons.append("scoring_record_must_not_grant_release")
    scope = record.get("scope")
    if scope != "final_test_v2_scoring":
        reasons.append("scoring_scope_mismatch")
    if not record.get("authorized_scorer"):
        reasons.append("missing_authorized_scorer")
    return reasons


def custody_state(appointment: dict | None, verification: dict | None, protocol: dict | None, release: dict | None, scoring: dict | None) -> str:
    """Derive one state. Self-declared flags are ignored."""
    appointment_reasons = validate_independent_appointment(appointment)
    verified = isinstance(verification, dict) and verification.get("independent_verification") == "RECORDED" and verification.get("labels_parsed") is False
    if appointment is None:
        return "CUSTODY_NOT_ESTABLISHED"
    if appointment_reasons or not verified:
        return "CUSTODY_VERIFICATION_PENDING" if appointment else "CUSTODY_NOT_ESTABLISHED"
    protocol_hash = protocol.get("protocol_sha256") if isinstance(protocol, dict) else None
    protocol_signed = isinstance(protocol, dict) and protocol.get("approved") is True and protocol.get("signature") and protocol_hash
    if not protocol_signed:
        return "PROTOCOL_NOT_FROZEN"
    expected = expected_binding(appointment.get("independent_custodian_id"), protocol_hash)
    if release_blockers(release, expected):
        return "RELEASE_NOT_AUTHORIZED"
    if scoring_blockers(scoring, release, expected):
        return "SCORING_NOT_AUTHORIZED"
    if isinstance(scoring, dict) and scoring.get("scoring_completed") is True:
        return "SCORING_COMPLETED"
    return "SCORING_AUTHORIZED"


def sealed_label_paths() -> list[Path]:
    paths = [SEALED_LABEL]
    if LABEL_LOCATION.is_file():
        record = json.loads(LABEL_LOCATION.read_text(encoding="utf-8"))
        for key in ("label_path", "backup_path"):
            value = record.get(key)
            if isinstance(value, str) and value:
                paths.append(Path(value))
    return paths


def is_sealed_label_path(path: Path | str) -> bool:
    candidate = Path(path)
    targets = sealed_label_paths()
    text = str(candidate).replace("\\", "/").casefold()
    try:
        resolved = candidate.resolve()
        if any(resolved == target.resolve() for target in targets):
            return True
    except OSError:
        pass
    if text.endswith("evaluation/datasets/_custodian/final_test_research_v1_v2/labels.jsonl"):
        return True
    return any(text == str(target).replace("\\", "/").casefold() for target in targets)


def live_expected_binding() -> dict:
    appointment = _load(INDEPENDENT_APPOINTMENT) if INDEPENDENT_APPOINTMENT.is_file() else {}
    return expected_binding(appointment.get("independent_custodian_id"), None)


def refuse_sealed_label_without_release(label_file: Path) -> None:
    """Refuse the sealed v2 label file unless a signed release record binds it.

    Other paths, including synthetic fixtures and the retired v1 labels, are
    left to the existing custodian gate.
    """
    if not is_sealed_label_path(label_file):
        return
    release = _load(RELEASE_TEMPLATE) if RELEASE_TEMPLATE.is_file() else None
    reasons = release_blockers(release, live_expected_binding())
    if reasons:
        raise CustodyAuthorizationError("Final Test v2 label release is not authorized: " + ",".join(reasons))


def scoring_decision(release: dict | None, scoring: dict | None, expected: dict | None = None) -> dict:
    expected = expected or live_expected_binding()
    reasons = scoring_blockers(scoring, release, expected)
    return {"permitted": not reasons, "reasons": reasons}


def refuse_v2_scoring(release: dict | None, scoring: dict | None, expected: dict | None = None) -> None:
    decision = scoring_decision(release, scoring, expected)
    if not decision["permitted"]:
        raise CustodyAuthorizationError("Final Test v2 scoring is not authorized: " + ",".join(decision["reasons"]))


def _signed(record: dict | None) -> bool:
    if not isinstance(record, dict):
        return False
    if record.get("approved") is not True or record.get("status") != "APPROVED":
        return False
    if not record.get("signature") or not record.get("approver") or not record.get("approval_date"):
        return False
    if record.get("revoked") is True:
        return False
    expires = record.get("expires_on")
    if isinstance(expires, str) and expires < date.today().isoformat():
        return False
    return True


def _signature_gap(record: dict | None) -> list[str]:
    if not isinstance(record, dict):
        return ["unsigned_or_template"]
    if record.get("revoked") is True:
        return ["revoked"]
    expires = record.get("expires_on")
    if isinstance(expires, str) and expires < date.today().isoformat():
        return ["expired"]
    if not _signed(record):
        return ["unsigned_or_template"]
    return []


def _self_non_independent(record: dict | None) -> list[str]:
    if not isinstance(record, dict) or record.get("custody_mode") != "SELF_CUSTODY" or record.get("independent_custody") is not False or record.get("independent_custodian") is True:
        return ["self_custody_cannot_claim_independent_custody"]
    if "independent_custodian" in set(record.get("roles") or []):
        return ["self_custody_cannot_claim_independent_custody"]
    return []


def self_expected_binding(protocol_sha256: str | None) -> dict:
    return {
        "dataset_version": "research_v1_final_test_v2_exploratory_v1",
        "manifest_sha256": MANIFEST_SHA256,
        "roster_sha256": ROSTER_SHA256,
        "label_sha256": LABEL_SHA256,
        "protocol_sha256": protocol_sha256,
    }


def _hash_gaps(record: dict, expected: dict) -> list[str]:
    reasons = []
    if record.get("manifest_sha256") != expected["manifest_sha256"]:
        reasons.append("dataset_hash_mismatch")
    if record.get("roster_sha256") != expected["roster_sha256"]:
        reasons.append("roster_hash_mismatch")
    wanted = expected.get("protocol_sha256")
    if not wanted:
        reasons.append("protocol_not_frozen")
    elif record.get("protocol_sha256") != wanted:
        reasons.append("protocol_hash_mismatch")
    if record.get("dataset_version") not in {None, expected["dataset_version"]}:
        reasons.append("different_dataset")
    return reasons


def self_protocol_blockers(protocol: dict | None, expected: dict) -> list[str]:
    reasons = _self_non_independent(protocol)
    if not isinstance(protocol, dict) or not protocol.get("protocol_sha256"):
        return reasons + ["protocol_not_frozen"]
    reasons.extend(_signature_gap(protocol))
    if expected.get("protocol_sha256") and protocol.get("protocol_sha256") != expected.get("protocol_sha256"):
        reasons.append("protocol_hash_mismatch")
    if not expected.get("protocol_sha256"):
        reasons.append("protocol_not_frozen")
    return reasons


def self_release_blockers(protocol: dict | None, release: dict | None, expected: dict) -> list[str]:
    """Self-custody release. Protocol freeze is required and does not grant scoring."""
    reasons = self_protocol_blockers(protocol, expected)
    if not isinstance(release, dict):
        return reasons + ["unsigned_release_authorization"]
    reasons.extend(_self_non_independent(release))
    reasons.extend(_signature_gap(release))
    reasons.extend(_hash_gaps(release, expected))
    if release.get("label_release") != "AUTHORIZED":
        reasons.append("release_not_authorized")
    if release.get("scoring_authorized") is True:
        reasons.append("release_record_must_not_grant_scoring")
    return reasons


def self_scoring_blockers(protocol: dict | None, release: dict | None, scoring: dict | None, expected: dict) -> list[str]:
    reasons = []
    release_reasons = self_release_blockers(protocol, release, expected)
    if release_reasons:
        reasons.append("release_not_authorized")
    if not isinstance(scoring, dict):
        return reasons + ["missing_scoring_authorization"]
    reasons.extend(_self_non_independent(scoring))
    reasons.extend(_signature_gap(scoring))
    reasons.extend(_hash_gaps(scoring, expected))
    if scoring.get("scoring_authorized") is not True:
        reasons.append("missing_scoring_authorization")
    if scoring.get("label_release") == "AUTHORIZED":
        reasons.append("scoring_record_must_not_grant_release")
    if scoring.get("scope") != "final_test_v2_self_custody_scoring":
        reasons.append("scoring_scope_mismatch")
    return reasons


def self_scoring_decision(protocol: dict | None, release: dict | None, scoring: dict | None, expected: dict | None = None) -> dict:
    expected = expected or self_expected_binding(None)
    reasons = self_scoring_blockers(protocol, release, scoring, expected)
    return {"permitted": not reasons, "reasons": reasons, "independent_custody": "NOT_ESTABLISHED"}


def self_custody_declaration_ok(record: dict | None) -> bool:
    """A recorded non-independent declaration. It is not an authorization."""
    if not isinstance(record, dict):
        return False
    if record.get("record_type") != "final_test_v2_self_custody_v1" or record.get("custody_mode") != "SELF_CUSTODY":
        return False
    if record.get("independent_custody") is not False or record.get("independent_custodian") is not False:
        return False
    roles = set(record.get("roles") or [])
    if "dataset_creator" not in roles or "independent_custodian" in roles:
        return False
    if record.get("os_access_control_claimed") is True or record.get("os_access_restriction") != "NOT_IMPLEMENTED":
        return False
    if record.get("custodian_identity_source") != DESIGNATED_APPOINTMENT:
        return False
    if record.get("manifest_sha256") != MANIFEST_SHA256 or record.get("roster_sha256") != ROSTER_SHA256:
        return False
    if record.get("approved") is True or record.get("scoring_authorized") is True or record.get("label_release") == "AUTHORIZED":
        return False
    if record.get("scoring_confirmed") is True:
        return False
    if record.get("signed_evidence") is True or record.get("signature") not in {None, ""}:
        return False
    if record.get("release_confirmed") is True and record.get("self_custody_limitations_acknowledged") is not True:
        return False
    if record.get("protocol_sha256") not in {None, ""} or record.get("protocol_freeze") != "PENDING":
        return False
    approval = record.get("protocol_approval")
    if approval is not None and not _verbal_protocol_statement(approval):
        return False
    scoring = record.get("scoring_authorization")
    if scoring is not None and not _unsigned_scoring_shape(scoring):
        return False
    explicit = record.get("custodian_id")
    if explicit and _identity(explicit) != dataset_creator_identity():
        return False
    return True


def _verbal_protocol_statement(approval: dict | None) -> bool:
    if not isinstance(approval, dict):
        return False
    return (
        approval.get("status") == "VERBAL_TEAM_APPROVAL_STATED"
        and approval.get("evidence_form") == "UNSIGNED_VERBAL_ACKNOWLEDGMENT"
        and approval.get("signed_evidence") is False
        and approval.get("signature") in {None, ""}
        and approval.get("independent_verification") is False
        and approval.get("authorizes_release") is False
        and approval.get("authorizes_scoring") is False
    )


def _unsigned_scoring_shape(scoring: dict | None) -> bool:
    """A scoring confirmation that does not repeat the release action."""
    if not isinstance(scoring, dict):
        return False
    return (
        scoring.get("custody_mode") == "SELF_CUSTODY"
        and scoring.get("independent_custody") is False
        and scoring.get("independent_verification") is False
        and scoring.get("evidence_form") in {"UNSIGNED_VERBAL_ACKNOWLEDGMENT", "RESEARCHER_SELF_AUTHORIZATION"}
        and scoring.get("signed_evidence") is False
        and scoring.get("signature") in {None, ""}
        and scoring.get("self_custody_limitations_acknowledged") is True
        and scoring.get("action") == "SCORING"
        and scoring.get("scoring_confirmed") is True
        and scoring.get("scoring_authorized") is True
        and scoring.get("release_confirmed") is not True
        and scoring.get("label_release") != "AUTHORIZED"
        and scoring.get("dataset_version") == "research_v1_final_test_v2_exploratory_v1"
        and scoring.get("manifest_sha256") == MANIFEST_SHA256
        and scoring.get("roster_sha256") == ROSTER_SHA256
        and scoring.get("labels_opened") is not True
        and scoring.get("experiment_executed") is not True
        and scoring.get("revoked") is not True
    )


def _declaration_release_confirmation(record: dict | None) -> dict | None:
    if not isinstance(record, dict) or record.get("release_confirmed") is not True:
        return None
    return {
        "record_type": "researcher_self_authorization_v1",
        "custody_mode": "SELF_CUSTODY",
        "independent_custody": False,
        "independent_custodian": False,
        "independent_verification": False,
        "evidence_form": "RESEARCHER_SELF_AUTHORIZATION",
        "signed_evidence": False,
        "signature": None,
        "self_custody_limitations_acknowledged": record.get("self_custody_limitations_acknowledged"),
        "action": "RELEASE",
        "release_confirmed": True,
        "scoring_confirmed": False,
        "scoring_authorized": False,
        "dataset_version": record.get("dataset_version"),
        "manifest_sha256": record.get("manifest_sha256"),
        "roster_sha256": record.get("roster_sha256"),
        "revoked": False,
    }


def assess_self_custody(record: dict | None, metadata: dict | None = None) -> dict:
    implemented = self_custody_declaration_ok(record)
    acknowledged = implemented and isinstance(record, dict) and record.get("self_custody_limitations_acknowledged") is True
    approval = record.get("protocol_approval") if isinstance(record, dict) else None
    release = "NOT_AUTHORIZED"
    confirmation = _declaration_release_confirmation(record)
    if acknowledged and confirmation is not None and record.get("scoring_confirmed") is not True and record.get("scoring_authorized") is not True:
        if metadata is None:
            release = "AUTHORIZED"
        else:
            decision = unsigned_release_decision(record, confirmation, metadata)
            release = "AUTHORIZED" if decision["permitted"] else "NOT_AUTHORIZED"
    scoring_state = "NOT_AUTHORIZED"
    scoring_block = record.get("scoring_authorization") if isinstance(record, dict) else None
    if release == "AUTHORIZED" and _unsigned_scoring_shape(scoring_block):
        if metadata is None:
            scoring_state = "AUTHORIZED"
        else:
            scored = unsigned_scoring_decision(record, confirmation, scoring_block, metadata)
            scoring_state = "AUTHORIZED" if scored["permitted"] else "NOT_AUTHORIZED"
    if implemented and acknowledged:
        custody = "ACKNOWLEDGED"
    elif implemented:
        custody = "IMPLEMENTED"
    else:
        custody = "NOT_RECORDED"
    return {
        "self_custody": custody,
        "independent_custody": "NOT_ESTABLISHED",
        "protocol_approval": "VERBAL_TEAM_APPROVAL_STATED" if _verbal_protocol_statement(approval) else "NOT_RECORDED",
        "signed_evidence": False,
        "protocol_freeze": "PENDING",
        "release": release,
        "scoring": scoring_state,
        "final_test_execution": "NOT_RUN",
        "labels": "SEALED",
        "os_access_restriction": "NOT_IMPLEMENTED",
        "satisfies_independent_custody": False,
        "independent_verification": False,
    }


def dataset_integrity_blockers(declaration: dict | None, metadata: dict | None) -> list[str]:
    """Compare recorded identity fields. This does not open or hash labels."""
    reasons = []
    if not self_custody_declaration_ok(declaration):
        reasons.append("self_custody_declaration_missing")
    view = metadata.get("metadata") if isinstance(metadata, dict) and isinstance(metadata.get("metadata"), dict) else metadata
    if not isinstance(view, dict):
        return reasons + ["missing_dataset_metadata"]
    version = str(view.get("dataset_version") or "")
    partition = str(view.get("partition") or "")
    if version != "research_v1_final_test_v2_exploratory_v1" or view.get("manifest_sha256") != MANIFEST_SHA256:
        reasons.append("dataset_hash_mismatch")
    if declaration and declaration.get("roster_sha256") != ROSTER_SHA256:
        reasons.append("roster_hash_mismatch")
    if view.get("group_count") != 600 or view.get("candidate_count") != 1200:
        reasons.append("dataset_identity_mismatch")
    if partition != "final_test" or "history" in version or "development" in version:
        reasons.append("development_or_history_substituted")
    return reasons


def _unsigned_common_blockers(declaration: dict | None, confirmation: dict | None, metadata: dict | None) -> list[str]:
    reasons = dataset_integrity_blockers(declaration, metadata)
    if not isinstance(confirmation, dict):
        return reasons + ["missing_explicit_confirmation"]
    if confirmation.get("custody_mode") != "SELF_CUSTODY" or confirmation.get("independent_custody") is not False or confirmation.get("independent_verification") is not False:
        reasons.append("self_custody_cannot_claim_independent_custody")
    form = confirmation.get("evidence_form")
    if form not in {"UNSIGNED_VERBAL_ACKNOWLEDGMENT", "RESEARCHER_SELF_AUTHORIZATION"} or confirmation.get("signed_evidence") is not False or confirmation.get("signature") not in {None, ""}:
        reasons.append("signed_evidence_not_accepted_on_unsigned_path")
    if confirmation.get("self_custody_limitations_acknowledged") is not True:
        reasons.append("self_custody_limitations_not_acknowledged")
    if confirmation.get("revoked") is True:
        reasons.append("revoked")
    expires = confirmation.get("expires_on")
    if isinstance(expires, str) and expires < date.today().isoformat():
        reasons.append("expired")
    if confirmation.get("manifest_sha256") != MANIFEST_SHA256:
        reasons.append("dataset_hash_mismatch")
    if confirmation.get("roster_sha256") != ROSTER_SHA256:
        reasons.append("roster_hash_mismatch")
    if confirmation.get("dataset_version") != "research_v1_final_test_v2_exploratory_v1":
        reasons.append("different_dataset")
    return reasons


def unsigned_release_blockers(declaration: dict | None, confirmation: dict | None, metadata: dict | None) -> list[str]:
    """Explicit unsigned release confirmation. Protocol approval is not release."""
    reasons = _unsigned_common_blockers(declaration, confirmation, metadata)
    if not isinstance(confirmation, dict):
        return reasons
    if confirmation.get("action") == "PROTOCOL_APPROVAL" or confirmation.get("release_confirmed") is not True:
        reasons.append("protocol_approval_does_not_authorize_release" if confirmation.get("action") == "PROTOCOL_APPROVAL" else "release_not_confirmed")
    elif confirmation.get("action") != "RELEASE":
        reasons.append("release_not_confirmed")
    if confirmation.get("scoring_confirmed") is True or confirmation.get("scoring_authorized") is True:
        reasons.append("release_must_not_confirm_scoring")
    return reasons


def unsigned_scoring_blockers(declaration: dict | None, release_confirmation: dict | None, scoring_confirmation: dict | None, metadata: dict | None) -> list[str]:
    """Scoring needs its own confirmation. A release confirmation is not scoring consent."""
    reasons = []
    if unsigned_release_blockers(declaration, release_confirmation, metadata):
        reasons.append("release_not_authorized")
    confirmation_reasons = _unsigned_common_blockers(declaration, scoring_confirmation, metadata)
    reasons.extend(reason for reason in confirmation_reasons if reason not in reasons)
    if not isinstance(scoring_confirmation, dict):
        return reasons + ["scoring_not_confirmed"]
    if scoring_confirmation.get("action") == "RELEASE" or scoring_confirmation.get("scoring_confirmed") is not True:
        reasons.append("release_does_not_authorize_scoring" if scoring_confirmation.get("action") == "RELEASE" else "scoring_not_confirmed")
    elif scoring_confirmation.get("action") != "SCORING":
        reasons.append("scoring_not_confirmed")
    if scoring_confirmation.get("release_confirmed") is True or scoring_confirmation.get("label_release") == "AUTHORIZED":
        reasons.append("scoring_record_must_not_grant_release")
    return reasons


def _unsigned_decision(reasons: list[str], action: str) -> dict:
    return {
        "permitted": not reasons,
        "reasons": reasons,
        "action": action,
        "independent_custody": "NOT_ESTABLISHED",
        "independent_verification": False,
        "signed_evidence": False,
        "labels_opened": False,
        "experiment_executed": False,
    }


def unsigned_release_decision(declaration: dict | None, confirmation: dict | None, metadata: dict | None) -> dict:
    return _unsigned_decision(unsigned_release_blockers(declaration, confirmation, metadata), "RELEASE")


def unsigned_scoring_decision(declaration: dict | None, release_confirmation: dict | None, scoring_confirmation: dict | None, metadata: dict | None) -> dict:
    return _unsigned_decision(unsigned_scoring_blockers(declaration, release_confirmation, scoring_confirmation, metadata), "SCORING")


def refuse_self_custody_live() -> None:
    """The recorded self-custody declaration never authorizes scoring."""
    record = _load(SELF_CUSTODY) if SELF_CUSTODY.is_file() else None
    decision = self_scoring_decision(record, record, record, self_expected_binding(None))
    if decision["permitted"] or decision["independent_custody"] != "NOT_ESTABLISHED":
        raise CustodyAuthorizationError("Self-custody state is inconsistent.")
    raise CustodyAuthorizationError("Self-custody does not authorize Final Test v2 scoring: " + ",".join(decision["reasons"]))
