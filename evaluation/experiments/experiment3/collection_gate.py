"""Development collection gate. A missing approval stops collection. It does not invent recordings."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from evaluation.analysis.experiment3 import REQUIRED_FIELDS, validate_rows
from evaluation.experiments.experiment3.prerequisite_validator import READY_FOR_DEVELOPMENT_COLLECTION, assess

EMPIRICAL = ROOT / "evaluation/experiments/experiment3/empirical"
SYNTHETIC = ROOT / "evaluation/experiments/experiment3/synthetic/results.json"


def collection_allowed(root: Path | None = None) -> dict:
    report = assess(root or ROOT)
    report["collection_started"] = False
    report["recordings_created"] = False
    report["reason"] = None if report["status"] == READY_FOR_DEVELOPMENT_COLLECTION else "collection requires signed protocol settings, corpus freeze, dependency approval, collection authorization, known verifier hashes, and a collection seed"
    return report


def validate_recording_file(path: Path) -> dict:
    text = str(path).replace("\\", "/").lower()
    if "final_test" in text or "final-test-v2-sealed-custody" in text:
        raise ValueError("Final Test recordings are refused")
    if path.resolve() == SYNTHETIC.resolve():
        raise ValueError("the synthetic fixture is not a Development recording")
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows = payload.get("rows") if isinstance(payload, dict) else payload
    validate_rows(rows)
    if rows[0]["evidence_label"] != "EMPIRICAL":
        raise ValueError("recording file is not empirical")
    missing = [field for field in REQUIRED_FIELDS if any(field not in row for row in rows)]
    if missing:
        raise ValueError(f"recording rows omit {missing}")
    return {"rows": len(rows), "evidence_label": "EMPIRICAL", "accepted_as_collection": False}


def main() -> int:
    report = collection_allowed()
    if report["status"] == READY_FOR_DEVELOPMENT_COLLECTION:
        report["reason"] = "The gate is open, but this command does not call verifiers or write recordings."
    destination = ROOT / "evaluation/experiments/experiment3/logs/collection_gate.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps({key: value for key, value in report.items() if key != "analysis_blockers"}, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "collection_started": False, "reason": report.get("reason")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
