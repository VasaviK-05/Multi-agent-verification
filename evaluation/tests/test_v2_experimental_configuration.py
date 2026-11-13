import json

from evaluation.research_readiness.canonical import ROOT
from evaluation.research_readiness.guards import ResearchAuthorizationError, assert_not_final_test


def test_experimental_configuration_is_not_a_completed_freeze():
    path = ROOT / "evaluation/config/research_v1/final_test_v2_experimental_configuration_manifest.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    text = path.read_text(encoding="utf-8")
    assert manifest["protocol_freeze"] == "NOT_COMPLETE"
    assert manifest["frozen"] is False
    assert manifest["approved"] is False
    assert manifest["research_lead_approval"] == "PENDING"
    assert manifest["labels_opened"] is False
    assert manifest["experiment_executed"] is False
    assert manifest["final_test_used_for_tuning"] is False
    assert manifest["critical_unresolved"]
    assert manifest["team_approval_statement"]["signed_evidence"] is False
    assert manifest["team_approval_statement"]["status"] == "UNSIGNED_RESEARCHER_STATEMENT"
    assert manifest["parameters"]["resource_coefficient"]["status"] == "APPROVED_BY_TEAM_VALUE_REQUIRED"
    assert manifest["parameters"]["resource_coefficient"]["approved_value"] is None
    assert manifest["parameters"]["model_weight_snapshot_hashes"]["approved_value"] is None
    assert "final-test-v2-sealed-custody" not in text
    assert manifest["dataset_identity"]["manifest_sha256"] == "e572093a4f0420c03316c89c83b6a7ab665af3af894d19a1428a6b091d3319ee"
    assert manifest["dataset_identity"]["roster_sha256"] == "3f8fcbf1e698174a9a7cf6c586ec51048bcc07ca11154b36fdef0dadc7796208"
    try:
        assert_not_final_test(path="evaluation/datasets/final_test_research_v1_eval_v2/manifest.json")
    except ResearchAuthorizationError:
        return
    raise AssertionError("Final Test path was accepted for configuration use")
