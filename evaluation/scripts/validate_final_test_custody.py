"""Check Final Test v2 metadata. Does not open the label file."""

from __future__ import annotations

import json

from evaluation.research_readiness.audit import audit_final_test_metadata
from evaluation.research_readiness.canonical import ROOT


def main() -> None:
    report = audit_final_test_metadata(ROOT)
    print(json.dumps(report, indent=2))
    if report["blockers"] or report["label_file_opened"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
