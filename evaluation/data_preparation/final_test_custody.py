"""Final Test v2 custody: the dataset creator is the designated custodian.

This is not independent custody and it does not authorize evaluation. Label release
stays pending until the protocol is frozen and a separate authorization record exists.
Verifier developers and Development experiment runners are refused.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

APPOINTMENT_TYPE = "final_test_v2_custodian_appointment_v1"
CUSTODY_STATUS = "DESIGNATED_CUSTODIAN_IS_DATASET_CREATOR"
PREVIOUS_CUSTODY_STATUS = "PENDING_NO_INDEPENDENT_CUSTODIAN"
APPOINTMENT_PATH = Path(__file__).resolve().parents[1] / "config" / "final_test_v2_custodian_appointment.json"
DENIED_ROLES = frozenset({"verifier_developer", "development_experiment_runner"})
DENIED_ACTIVITIES = (
    "verifier_development", "reputation_fitting", "policy_selection",
    "development", "training", "tuning",
)
RESPONSIBILITIES = (
    "Maintain label confidentiality.",
    "Prevent Final Test leakage into Development, training, tuning, reputation fitting, or policy selection.",
    "Preserve the existing Final Test v2 dataset and its hashes.",
    "Release labels only after protocol freeze and explicit authorization.",
)


def load_appointment(path: Path = APPOINTMENT_PATH) -> dict:
    record = json.loads(path.read_text(encoding="utf-8"))
    if record.get("record_type") != APPOINTMENT_TYPE:
        raise ValueError("Unsupported Final Test custodian appointment")
    if record.get("independent_custodian") is not False or record.get("custody_independence") != "NOT_INDEPENDENT":
        raise ValueError("This appointment must not claim independent custody")
    if record.get("evaluation_authorized") is not False or record.get("evaluation_authorization") != "PENDING":
        raise ValueError("Custodian appointment must leave evaluation authorization pending")
    if record.get("label_release") != "NOT_AUTHORIZED" or record.get("protocol_freeze") != "PENDING":
        raise ValueError("Custodian appointment must not release labels or mark the protocol frozen")
    if set(record.get("roles") or ()) != {"dataset_creator", "designated_final_test_custodian"}:
        raise ValueError("Appointee must be both dataset creator and designated Final Test custodian")
    if record.get("custody_status") != CUSTODY_STATUS or not str(record.get("appointee", "")).strip():
        raise ValueError("Appointment needs the designated-creator custody status and an appointee")
    if tuple(record.get("responsibilities") or ()) != RESPONSIBILITIES:
        raise ValueError("Appointment responsibilities do not match the custody protocol")
    if set(record.get("label_access", {}).get("denied_roles") or ()) != DENIED_ROLES:
        raise ValueError("Appointment must deny verifier developers and Development experiment runners")
    return record


def is_appointment(record: dict | None) -> bool:
    return isinstance(record, dict) and record.get("record_type") == APPOINTMENT_TYPE


def denied_activities(purpose: str) -> list[str]:
    text = "_".join(re.findall(r"[a-z0-9]+", purpose.lower()))
    return [activity for activity in DENIED_ACTIVITIES if activity in text]


def label_access_decision(*, role: str | None, purpose: str, authorization: dict | None,
                          protocol_frozen: bool) -> dict:
    """Whether a caller may receive Final Test labels. Appointment never grants this."""
    if role in DENIED_ROLES:
        return {"permitted": False, "reason": "role_denied", "role": role}
    activities = denied_activities(purpose)
    if activities:
        return {"permitted": False, "reason": "activity_denied", "activities": activities}
    if is_appointment(authorization):
        return {"permitted": False, "reason": "custodian_appointment_is_not_evaluation_authorization"}
    if not authorization or authorization.get("approved") is not True:
        return {"permitted": False, "reason": "evaluation_authorization_pending"}
    if not protocol_frozen:
        return {"permitted": False, "reason": "protocol_not_frozen"}
    return {"permitted": True, "reason": "authorized_after_protocol_freeze"}


def release_block(manifest: dict, authorization: dict | None, *, role: str | None, purpose: str) -> str | None:
    """Block label release. A pending v2 manifest cannot be overridden by an authorization file."""
    decision = label_access_decision(role=role, purpose=purpose, authorization=authorization,
                                     protocol_frozen=authorization.get("protocol_frozen") is True
                                     if isinstance(authorization, dict) else False)
    if not decision["permitted"] and decision["reason"] in {"role_denied", "activity_denied",
                                                           "custodian_appointment_is_not_evaluation_authorization"}:
        return decision["reason"]
    if manifest.get("evaluation_authorization") == "PENDING" or manifest.get("label_release") == "NOT_AUTHORIZED":
        return "label_release_pending_protocol_freeze_and_authorization"
    if manifest.get("custody_status") == CUSTODY_STATUS and not decision["permitted"]:
        return decision["reason"]
    return None
