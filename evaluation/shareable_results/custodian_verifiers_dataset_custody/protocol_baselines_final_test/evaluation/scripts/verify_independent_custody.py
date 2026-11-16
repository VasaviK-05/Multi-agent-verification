"""Report Final Test v2 custody state without parsing labels.

Byte hashing is off unless --hash-bytes is passed. That mode hashes the label
file in chunks and does not print its contents. It is still a local read, not
an independent verification.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path

from evaluation.research_readiness.v2_authorization import (
    INDEPENDENT_APPOINTMENT,
    LABEL_SHA256,
    MANIFEST_SHA256,
    RELEASE_TEMPLATE,
    ROSTER_SHA256,
    SCORING_TEMPLATE,
    SEALED_LABEL,
    SEALED_MANIFEST,
    SEALED_ROSTER,
    custody_state,
    validate_independent_appointment,
)

ROOT = Path(__file__).resolve().parents[2]
VERIFICATION = ROOT / "evaluation/config/research_v1/independent_custody_verification.json"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _access_report() -> dict:
    exists = SEALED_LABEL.exists()
    readable = bool(exists and os.access(SEALED_LABEL, os.R_OK))
    return {
        "label_path_exists": exists,
        "current_account_can_read_label_file": readable,
        "os_access_denial": "PENDING",
        "missing_external_step": "An independent custodian must store the label file where this developer account is denied read access, then record that denial. Python path checks are not OS access control.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hash-bytes", action="store_true")
    args = parser.parse_args()
    appointment = json.loads(INDEPENDENT_APPOINTMENT.read_text(encoding="utf-8"))
    verification = json.loads(VERIFICATION.read_text(encoding="utf-8"))
    release = json.loads(RELEASE_TEMPLATE.read_text(encoding="utf-8"))
    scoring = json.loads(SCORING_TEMPLATE.read_text(encoding="utf-8"))
    if args.hash_bytes:
        verification["local_manifest_sha256_matches"] = _sha256(SEALED_MANIFEST) == MANIFEST_SHA256
        verification["local_roster_sha256_matches"] = _sha256(SEALED_ROSTER) == ROSTER_SHA256
        verification["local_label_sha256_matches"] = _sha256(SEALED_LABEL) == LABEL_SHA256
        verification["label_bytes_hashed_by_this_record"] = True
        verification["labels_parsed"] = False
        verification["independent_verification"] = "PENDING"
    access = _access_report()
    state = custody_state(appointment, verification, {"approved": False, "protocol_sha256": None}, release, scoring)
    report = {
        "custody_state": state,
        "appointment_blockers": validate_independent_appointment(appointment),
        "independent_verification": verification.get("independent_verification"),
        "labels_parsed": False,
        "access": access,
        "protocol_freeze": "PENDING",
        "release_authorized": False,
        "scoring_authorized": False,
    }
    print(json.dumps(report, indent=2))
    return 0 if state in {"CUSTODY_NOT_ESTABLISHED", "CUSTODY_VERIFICATION_PENDING", "PROTOCOL_NOT_FROZEN", "RELEASE_NOT_AUTHORIZED", "SCORING_NOT_AUTHORIZED"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
