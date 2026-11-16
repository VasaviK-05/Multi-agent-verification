"""Report repository self-custody without reading Final Test labels."""

from __future__ import annotations

import json

from evaluation.research_readiness.audit import audit_final_test_metadata
from evaluation.research_readiness.canonical import ROOT
from evaluation.research_readiness.v2_authorization import SELF_CUSTODY, assess_self_custody


def main() -> int:
    record = json.loads(SELF_CUSTODY.read_text(encoding="utf-8")) if SELF_CUSTODY.is_file() else None
    metadata = audit_final_test_metadata(ROOT)
    report = assess_self_custody(record, metadata=metadata)
    amendment_path = ROOT / "evaluation/config/research_v1/final_test_self_custody_amendment_2026-11-13.json"
    amendment = json.loads(amendment_path.read_text(encoding="utf-8"))
    report["labels_opened"] = metadata["label_file_opened"]
    report["custody_status"] = amendment["custody_status"]
    report["research_lead_approval"] = amendment["research_lead_approval"]
    report["research_lead_scoring_authorization"] = amendment["research_lead_scoring_authorization"]
    report["operational_scoring"] = amendment["operational_scoring"]
    print(json.dumps(report, indent=2))
    expected = {
        "self_custody": "ACKNOWLEDGED",
        "independent_custody": "NOT_ESTABLISHED",
        "protocol_approval": "VERBAL_TEAM_APPROVAL_STATED",
        "signed_evidence": False,
        "protocol_freeze": "PENDING",
        "release": "AUTHORIZED",
        "scoring": "AUTHORIZED",
        "final_test_execution": "NOT_RUN",
        "labels": "SEALED",
        "labels_opened": False,
        "custody_status": "SELF_CUSTODY",
        "research_lead_approval": "PENDING",
        "research_lead_scoring_authorization": "PENDING",
        "operational_scoring": "NOT_AUTHORIZED_UNTIL_FREEZE_AND_RESEARCH_LEAD_AUTHORIZATION",
    }
    return 0 if all(report[key] == value for key, value in expected.items()) else 2


if __name__ == "__main__":
    raise SystemExit(main())
