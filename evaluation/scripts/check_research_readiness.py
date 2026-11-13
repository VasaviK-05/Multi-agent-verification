"""Write the machine-readable research-readiness status.

The status is derived from repository evidence. This script does not approve
or authorize anything.
"""

from __future__ import annotations

import json
from pathlib import Path

from evaluation.research_readiness.canonical import ROOT
from evaluation.research_readiness.check import check_research_readiness


def main() -> None:
    report = check_research_readiness(ROOT)
    destination = ROOT / "evaluation" / "config" / "research_v1" / "readiness_status.json"
    destination.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "overall_status": report["overall_status"],
        "experiment3_status": report["experiment3_status"],
        "development_collection_authorized": report["development_collection_authorized"],
        "final_test_scoring_authorized": report["final_test_scoring_authorized"],
        "wrote": str(destination.relative_to(ROOT)).replace("\\", "/"),
    }, indent=2))


if __name__ == "__main__":
    main()
