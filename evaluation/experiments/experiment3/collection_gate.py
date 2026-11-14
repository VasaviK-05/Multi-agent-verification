"""Development collection gate.

Signature fields are not a prerequisite and are not fabricated. Collection
readiness is the automated integrity report. This command does not call verifiers.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from evaluation.analysis.experiment3 import REQUIRED_FIELDS, validate_rows
from evaluation.experiments.experiment3.execution_readiness import execution_report

EMPIRICAL = ROOT / "evaluation/experiments/experiment3/empirical"
SYNTHETIC = ROOT / "evaluation/experiments/experiment3/synthetic/results.json"


def collection_allowed(root: Path | None = None) -> dict:
    report = execution_report(root or ROOT)
    report["collection_started"] = False
    report["recordings_created"] = False
    if report["status"] == "BLOCKED":
        report["reason"] = "automated integrity validation failed"
    elif report["status"] == "TECHNICALLY_READY":
        report["reason"] = "configuration integrity passed; verifier runtime is not available"
    elif report["status"] == "AUTHORIZED_BY_RESEARCH_LEAD":
        report["reason"] = "authorized by the recorded research-lead instruction; verifiers have not been called"
    elif report["status"] == "EMPIRICALLY_EXECUTED":
        report["reason"] = "empirical rows exist and the full cell count is not complete"
    else:
        report["reason"] = "empirical collection is complete"
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
    report["reason"] = (report.get("reason") or "") + " This command does not call verifiers or write recordings."
    destination = ROOT / "evaluation/experiments/experiment3/logs/collection_gate.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps({key: value for key, value in report.items() if key != "analysis_blockers"}, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "collection_started": False, "reason": report.get("reason")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
