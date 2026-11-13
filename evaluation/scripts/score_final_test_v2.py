"""Final Test v2 scoring entry point.

An unsigned verbal acknowledgment does not make this command score. It does not
read a release confirmation, and it does not read the label file.
"""

from __future__ import annotations

import json
from pathlib import Path

from evaluation.research_readiness.v2_authorization import (
    RELEASE_TEMPLATE,
    SCORING_TEMPLATE,
    CustodyAuthorizationError,
    refuse_self_custody_live,
    refuse_v2_scoring,
)

ROOT = Path(__file__).resolve().parents[2]


def score(release_path: Path | None = None, scoring_path: Path | None = None) -> dict:
    release_path = release_path or RELEASE_TEMPLATE
    scoring_path = scoring_path or SCORING_TEMPLATE
    release = json.loads(release_path.read_text(encoding="utf-8")) if release_path.is_file() else None
    scoring = json.loads(scoring_path.read_text(encoding="utf-8")) if scoring_path.is_file() else None
    refuse_v2_scoring(release, scoring)
    refuse_self_custody_live()
    raise CustodyAuthorizationError("Signed records passed the binding check, and no scoring implementation is enabled while labels stay sealed.")


def main() -> int:
    try:
        score()
    except CustodyAuthorizationError as exc:
        print(json.dumps({"scored": False, "error": str(exc), "labels_opened": False}))
        return 2
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
