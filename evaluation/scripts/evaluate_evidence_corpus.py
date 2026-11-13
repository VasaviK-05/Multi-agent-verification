"""Validate the canonical corpus and summarize recorded retrieval coverage.

Does not instantiate EvidenceRetriever and does not rebuild the index.
"""

from __future__ import annotations

import json

from evaluation.research_readiness.audit import audit_corpus
from evaluation.research_readiness.canonical import ROOT


def main() -> None:
    report = audit_corpus(ROOT)
    destination = ROOT / "evaluation" / "artifacts" / "research_readiness" / "evidence_coverage_summary.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "corpus_sha256": report["corpus_sha256"],
        "hotpotqa_questions": report["hotpotqa_questions"],
        "hotpotqa_any_chunk_at_or_above_0_78": report["hotpotqa_any_chunk_at_or_above_0_78"],
        "gsm8k_questions": report["gsm8k_questions"],
        "fever_in_canonical_source": report["fever_in_canonical_source"],
        "blockers": report["blockers"],
    }, indent=2))
    if report["blockers"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
