import json
from pathlib import Path

import pytest

from app.verifiers.evidence_retriever import default_corpus_path
from app.verifiers.task_compatibility import (
    confidence_contract,
    enforce_task_support,
    evidence_contract,
    population_support,
    rule_item,
    semantic_contract,
)
from evaluation.research_readiness.audit import audit_corpus, audit_datasets, audit_final_test_metadata
from evaluation.research_readiness.canonical import CANONICAL_CORPUS, ROOT
from evaluation.research_readiness.check import check_research_readiness
from evaluation.research_readiness.guards import (
    ResearchAuthorizationError,
    assert_collection_authorized,
    assert_not_final_test,
    assert_scoring_authorized,
)


def test_population_matrix_covers_four_verifiers_and_five_tasks():
    populations = ["direct_arithmetic", "gsm8k", "direct_facts", "hotpotqa", "fever"]
    for verifier in ("semantic", "evidence", "rule", "confidence"):
        for population in populations:
            assert population_support(verifier, population) in {"VERIFIED", "PARTIALLY_VERIFIED", "UNSUPPORTED", "UNKNOWN"}


def test_rule_verifies_direct_arithmetic_and_refuses_word_problems():
    direct = rule_item("What is 25 + 17?", "42", "direct_arithmetic")
    assert direct["task_support"] == "VERIFIED" and direct["passed"] is True and direct["score_is_correctness"] is True
    word = rule_item("Natalia sold 48 clips in April and half as many in May. How many clips did Natalia sell altogether?", "72", "gsm8k")
    assert word["task_support"] == "UNSUPPORTED" and word["passed"] is False and word["decision"] == "UNSURE"
    wrong = rule_item("What is 25 + 17?", "40", "direct_arithmetic")
    assert wrong["passed"] is False and wrong["decision"] == "REJECT"


def test_unsupported_success_is_downgraded():
    downgraded = enforce_task_support("rule", "fever", passed=True, decision="SUPPORT")
    assert downgraded["passed"] is False and downgraded["decision"] == "UNSURE"


def test_semantic_requires_reference_and_is_not_correctness():
    missing = semantic_contract("hotpotqa", None)
    assert missing["task_support"] == "UNSUPPORTED" and missing["passed"] is False
    judgments = semantic_contract("direct_facts", "support,reject")
    assert judgments["task_support"] == "UNSUPPORTED"
    present = semantic_contract("hotpotqa", "Paris is the capital of France.")
    assert present["score_is_correctness"] is False and present["passed"] is False
    assert semantic_contract("direct_arithmetic", "2 + 2 = 4")["task_support"] == "UNSUPPORTED"


def test_evidence_preserves_insufficient_evidence_and_refuses_fever_support():
    fever = evidence_contract("fever", None)
    assert fever["task_support"] == "UNSUPPORTED" and fever["passed"] is False
    hotpot = evidence_contract("hotpotqa", {"supporting_above_gate": False})
    assert hotpot["task_support"] == "INSUFFICIENT_EVIDENCE" and hotpot["decision"] == "UNSURE"
    hit = evidence_contract("hotpotqa", {"supporting_above_gate": True})
    assert hit["passed"] is False and hit["score_is_correctness"] is False
    assert evidence_contract("gsm8k")["task_support"] == "UNSUPPORTED"


def test_confidence_is_not_correctness():
    report = confidence_contract("gsm8k")
    assert report["score_is_correctness"] is False and report["passed"] is False
    assert confidence_contract("fever")["task_support"] == "UNKNOWN"


def test_canonical_evidence_path_is_the_corpus_file():
    resolved = Path(default_corpus_path())
    if not resolved.is_absolute():
        resolved = ROOT / resolved
    assert resolved.is_file()
    assert resolved.resolve() == (ROOT / CANONICAL_CORPUS).resolve()


def test_dependency_groups_are_not_one_group_of_every_verifier():
    payload = json.loads((ROOT / "evaluation/config/experiments/experiment3_dependency_configuration.json").read_text(encoding="utf-8"))
    assert payload["empirical_evidence"] == "none" and payload["approved"] is False
    assert len(payload["groups"]) > 1
    assert payload["synthetic_two_group_registry"]["usable_as_empirical_dependency"] is False


def test_dataset_audit_matches_the_canonical_roster():
    report = audit_datasets(ROOT)
    assert report["blockers"] == []
    assert report["eligibility"]["hotpotqa_groups"] == 185
    assert report["eligibility"]["groups"] == 372
    assert report["sealed_final_test_id_overlap"] == 0
    assert report["unified"]["history"]["rows"] == 8000


def test_corpus_and_custody_audits_do_not_open_labels():
    corpus = audit_corpus(ROOT)
    custody = audit_final_test_metadata(ROOT)
    assert corpus["blockers"] == []
    assert corpus["retriever_not_instantiated"] is True
    assert corpus["fever_in_canonical_source"] is False
    assert custody["label_file_opened"] is False
    assert custody["metadata"]["status"] == "NOT_AUTHORIZED"
    assert custody["blockers"] == []


def test_collection_and_scoring_are_refused():
    with pytest.raises(ResearchAuthorizationError):
        assert_not_final_test(path="evaluation/datasets/final_test_research_v1_eval_v2/manifest.json")
    with pytest.raises(ResearchAuthorizationError):
        assert_collection_authorized({"partition": "development", "collection_authorized": False, "approved": False})
    with pytest.raises(ResearchAuthorizationError):
        assert_scoring_authorized({"partition": "final_test", "scoring_authorized": False, "label_release": "NOT_AUTHORIZED"})
    assert_collection_authorized({"partition": "synthetic", "evidence_label": "SYNTHETIC"}, synthetic_fixture=True)


def test_generated_packages_do_not_approve_themselves():
    report = check_research_readiness(ROOT)
    assert report["packages_do_not_self_approve"] is True
    assert report["overall_status"] == "READY_FOR_APPROVAL"
    assert report["development_collection_authorized"] is False
    assert report["final_test_scoring_authorized"] is False
    assert report["execution_ready"] is False
    assert report["requirements"]["final_test_custody"]["status"] == "NOT_AUTHORIZED"
    assert report["requirements"]["collection_and_scoring"]["authorization"] == "NOT_AUTHORIZED"


def test_protocols_cite_the_quarantined_hotpotqa_count():
    for relative in (
        "evaluation/docs/experiment1_protocol.md",
        "evaluation/docs/experiment2_protocol.md",
        "evaluation/docs/experiment3_protocol.md",
        "evaluation/docs/experiment4_protocol.md",
    ):
        text = (ROOT / relative).read_text(encoding="utf-8")
        assert "185" in text
        assert "PENDING" in text or "pending" in text
        assert "not authorized" in text.lower() or "NOT_AUTHORIZED" in text or "not authorised" in text.lower()
