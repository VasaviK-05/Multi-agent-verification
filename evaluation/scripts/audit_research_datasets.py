"""Audit dataset counts, eligibility, and identifier overlap.

Prints counts and blocker names. Does not print Final Test labels or identifiers.
"""

from __future__ import annotations

import json

from evaluation.research_readiness.audit import audit_datasets
from evaluation.research_readiness.canonical import ROOT


def main() -> None:
    report = audit_datasets(ROOT)
    print(json.dumps(report, indent=2))
    if report["blockers"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
