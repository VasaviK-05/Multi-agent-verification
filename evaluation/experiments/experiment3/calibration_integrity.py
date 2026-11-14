"""Integrity check for the frozen Development cost-calibration bundle.

The check hashes files and validates the calibration artifact. It does not
select a budget, convert milliseconds, or authorize policy fitting.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

BUNDLE = "artifacts/research-v1-development-cost-calibration-v1"
FILES = ("measurements.json", "calibration.json", "calibration-provenance.json", "freeze-manifest.json")
_CACHE: dict[str, dict] = {}


def _digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _file_record(path: Path) -> dict:
    raw = path.read_bytes()
    normalized = raw.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return {
        "bytes": len(raw),
        "sha256": _digest(raw),
        "lf_normalized_bytes": len(normalized),
        "lf_normalized_sha256": _digest(normalized),
    }


def _matches(record: dict, expected: str) -> str | None:
    if record["sha256"] == expected:
        return "raw"
    if record["lf_normalized_sha256"] == expected:
        return "lf_normalized"
    return None


def verify_bundle(root: Path) -> dict:
    """Return hash, unit, and freeze-scope facts for the calibration bundle."""
    root = Path(root)
    cache_key = str(root.resolve())
    cached = _CACHE.get(cache_key)
    if cached is not None:
        return cached
    folder = root / BUNDLE
    freeze_path = folder / "freeze-manifest.json"
    if not freeze_path.is_file():
        raise FileNotFoundError(f"{BUNDLE}/freeze-manifest.json")
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    records = {name: _file_record(folder / name) for name in FILES}
    expected = {item["path"]: item for item in freeze.get("frozen_files") or []}
    comparisons = []
    for name, item in expected.items():
        record = records[name]
        mode = _matches(record, item.get("sha256"))
        comparisons.append({
            "path": f"{BUNDLE}/{name}",
            "expected_sha256": item.get("sha256"),
            "expected_bytes": item.get("size_bytes"),
            "working_tree_sha256": record["sha256"],
            "working_tree_bytes": record["bytes"],
            "match": mode,
            "size_matches_recorded_bytes": record["bytes"] == item.get("size_bytes") or record["lf_normalized_bytes"] == item.get("size_bytes"),
        })
    calibration = json.loads((folder / "calibration.json").read_text(encoding="utf-8"))
    provenance = json.loads((folder / "calibration-provenance.json").read_text(encoding="utf-8"))
    measurements = json.loads((folder / "measurements.json").read_text(encoding="utf-8"))
    attempts = ((measurements.get("attempts") or []) if isinstance(measurements, dict) else [])
    embedded = (((calibration.get("request") or {}).get("measurements") or {}).get("attempts") or [])
    validated = _validate_artifact(calibration)
    freeze_calibration = freeze.get("calibration") or {}
    freeze_measurement = freeze.get("measurement") or {}
    content_ok = (
        calibration.get("calibration_id") == freeze_calibration.get("artifact_id")
        and calibration.get("method") == freeze_calibration.get("method")
        and calibration.get("cost_units") == freeze_calibration.get("cost_units")
        and calibration.get("input_digest") == freeze_calibration.get("input_digest")
        and provenance.get("record_id") == (freeze.get("freeze_record_distinction") or {}).get("calibration_input_reference")
        and provenance.get("calibration", {}).get("cost_units") == "ms"
        and provenance.get("measurement_artifact", {}).get("sha256") == freeze_measurement.get("sha256")
        and len(attempts) == freeze_measurement.get("attempt_count")
        and len(embedded) == len(attempts)
    )
    scope = freeze.get("scope_statements") or {}
    result = {
        "bundle": BUNDLE,
        "freeze_manifest_working_tree_sha256": records["freeze-manifest.json"]["sha256"],
        "files": comparisons,
        "all_frozen_files_match": all(item["match"] for item in comparisons) and content_ok and validated["valid"],
        "content_matches_freeze_manifest": content_ok,
        "artifact_validation": validated,
        "method": calibration.get("method"),
        "cost_units": calibration.get("cost_units"),
        "calibration_id": calibration.get("calibration_id"),
        "input_digest": calibration.get("input_digest"),
        "include_warmups": (calibration.get("request") or {}).get("include_warmups"),
        "attempt_count": len(attempts),
        "calibration_eligible_attempts": sum(1 for row in attempts if row.get("purpose") == "calibration"),
        "warmup_attempts": sum(1 for row in attempts if row.get("purpose") == "warmup"),
        "roles": sorted({row.get("role") for row in attempts}),
        "dataset_ids": sorted({row.get("dataset_id") for row in attempts}),
        "estimates": (calibration.get("result") or {}).get("estimates"),
        "resource_manifest_id": (freeze.get("runtime") or {}).get("resource_manifest_id"),
        "setup_fingerprint": (freeze.get("runtime") or {}).get("setup_fingerprint"),
        "required_verifiers": list(freeze.get("required_verifiers") or []),
        "development_only": scope.get("development_only"),
        "policy_fitting_authorized_by_freeze": scope.get("policy_fitting_or_budget_selection_authorized_by_this_freeze"),
        "final_test_authorized_by_freeze": scope.get("final_test_access_or_execution_authorized"),
        "global_project_freeze": (freeze.get("freeze_record_distinction") or {}).get("global_project_freeze"),
        "provenance_record_id": provenance.get("record_id"),
        "line_ending_note": "calibration-provenance.json is LF in the freeze record. A CRLF checkout changes its raw SHA-256; the LF-normalized digest remains the frozen digest. measurements.json and calibration.json match the freeze record as checked-out bytes.",
    }
    _CACHE[cache_key] = result
    return result


def _validate_artifact(payload: dict) -> dict:
    try:
        from app.game.offline.calibration import CalibrationArtifact
        artifact = CalibrationArtifact.model_validate(payload)
    except Exception as exc:
        return {"valid": False, "error": f"{type(exc).__name__}: {exc}"}
    setup = artifact.request.measurements.setup
    return {
        "valid": True,
        "error": None,
        "calibration_id": artifact.calibration_id,
        "input_digest": artifact.input_digest,
        "cost_units": artifact.cost_units,
        "method": artifact.method,
        "resource_manifest_id": setup.resources.manifest_id,
        "setup_fingerprint": setup.fingerprint,
        "evidence_kind": setup.evidence_kind,
        "code_revision": setup.code_revision,
        "required_verifiers": list(artifact.request.required_verifiers),
    }
