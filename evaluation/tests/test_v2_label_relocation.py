import json
from pathlib import Path

import pytest

from evaluation.research_readiness.canonical import ROOT
from evaluation.research_readiness.v2_authorization import (
    LABEL_SHA256,
    CustodyAuthorizationError,
    refuse_sealed_label_without_release,
)


def test_labels_were_moved_outside_the_repository_without_opening_them():
    location = json.loads((ROOT / "evaluation/config/research_v1/final_test_label_custody_location.json").read_text(encoding="utf-8"))
    amendment = json.loads((ROOT / "evaluation/config/research_v1/final_test_self_custody_amendment_2026-11-13.json").read_text(encoding="utf-8"))
    label_path = Path(location["label_path"])
    assert location["label_sha256"] == LABEL_SHA256
    assert location["labels_parsed"] is False
    assert location["custody_status"] == "SELF_CUSTODY"
    assert location["independent_custody"] is False
    assert ROOT not in label_path.resolve().parents
    assert not (ROOT / location["previous_path"]).exists()
    assert amendment["custody_status"] == "SELF_CUSTODY"
    assert amendment["independent_custody"] is False
    assert amendment["research_lead_approval"] == "PENDING"
    assert amendment["research_lead_scoring_authorization"] == "PENDING"
    assert amendment["signed_evidence"] is False
    assert amendment["signature"] is None
    with pytest.raises(CustodyAuthorizationError):
        refuse_sealed_label_without_release(label_path)
    with pytest.raises(CustodyAuthorizationError):
        refuse_sealed_label_without_release(ROOT / location["previous_path"])
