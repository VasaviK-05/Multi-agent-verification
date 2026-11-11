"""Label-free Experiment 1 preparation checks. Synthetic fixtures only."""
from __future__ import annotations

import json

import pytest

from evaluation.data_preparation import experiment1_preparation as prep
from evaluation.data_preparation import final_test_workflow as ft


def write_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
    return path


def test_contamination_audit_matches_content_and_categorizes_sources(tmp_path):
    roster = write_jsonl(tmp_path / "evaluation/datasets/ft/evaluation_roster.jsonl", [
        {"benchmark": "GSM8K", "related_group_id": "g1", "source_id": "s1", "question": "How many apples?"},
        {"benchmark": "HotpotQA", "related_group_id": "g2", "source_id": "s2", "question": "Who wrote X?"},
        {"benchmark": "HotpotQA", "related_group_id": "g3", "source_id": "s3", "question": "Fresh?"}])
    manifest = tmp_path / "evaluation/datasets/ft/manifest.json"
    manifest.write_text(json.dumps({"manifest_sha256": "f" * 64}), encoding="utf-8")
    exposed = tmp_path / "evaluation/datasets/unified/final_test.json"
    exposed.parent.mkdir(parents=True)
    exposed.write_text(json.dumps([{"id": "other", "question": "how many APPLES"}]), encoding="utf-8")
    baseline = write_jsonl(tmp_path / "evaluation/results/baseline/baseline_results.jsonl",
                           [{"nested": {"question": "Who wrote X"}}])
    dev = write_jsonl(tmp_path / "evaluation/datasets/processed/development.jsonl", [{"question": "Who wrote X?"}])
    index, _, digests = prep.scan([exposed, baseline, dev], tmp_path)
    audit = prep.contamination_audit(roster, manifest, index, digests, tmp_path)
    assert audit["verdict"] == "CONTAMINATED" and audit["contaminated_group_count"] == 2
    assert audit["contaminated_groups_by_benchmark"] == {"GSM8K": 1, "HotpotQA": 1}
    assert audit["clean_groups_by_benchmark"] == {"GSM8K": 0, "HotpotQA": 1}
    assert audit["by_category"]["exposed_final_test"] == {"GSM8K": 1}
    assert audit["by_category"]["baseline_outputs"] == {"HotpotQA": 1}
    assert audit["by_category"]["development_files"] == {"HotpotQA": 1}
    assert audit["target"]["manifest_sha256"] == "f" * 64 and audit["custodian_labels_opened"] is False


def test_categories_cover_requested_sources():
    assert prep.category("evaluation/datasets/unified/final_test.json") == "exposed_final_test"
    assert prep.category("evaluation/datasets/processed/final_test.json") == "exposed_final_test"
    assert prep.category("evaluation/results/baseline/x.jsonl") == "baseline_outputs"
    assert prep.category("evaluation/results/evidence_hotpotqa_results.json") == "verifier_outputs"
    assert prep.category("evaluation/datasets/unified/development.json") == "development_files"


def test_development_balance_flags_benchmark_without_incorrect(tmp_path):
    dev = write_jsonl(tmp_path / "dev.jsonl", [
        {"benchmark": "GSM8K", "correctness_status": "verified_correct"},
        {"benchmark": "GSM8K", "correctness_status": "verified_incorrect"},
        {"benchmark": "HotpotQA", "correctness_status": "verified_correct"},
        {"benchmark": "HotpotQA", "correctness_status": "unresolved"}])
    balance = prep.development_label_balance({"development": dev}, tmp_path)
    assert balance["benchmarks_without_verified_incorrect"] == {"development": ["HotpotQA"]}
    assert balance["binary_estimable_false_acceptance"] == {"development": ["GSM8K"]}
    assert balance["roles"]["development"]["counts"]["HotpotQA"] == {"verified_correct": 1, "verified_incorrect": 0, "unresolved": 1}


def test_pool_excludes_exposed_duplicate_and_shared_paragraph_without_answers():
    exposed_paragraph = {"title": ["P"], "sentences": [["shared text."]]}
    contexts = ft.context_hashes(exposed_paragraph)
    rows = [{"id": "a", "question": "Seen before?", "context": {"title": ["Q"], "sentences": [["x"]]}},
            {"id": "b", "question": "New one?", "context": {"title": ["R"], "sentences": [["y"]]}},
            {"id": "c", "question": "new ONE", "context": {"title": ["S"], "sentences": [["z"]]}},
            {"id": "d", "question": "Other?", "context": exposed_paragraph}]
    result = prep.pool("HotpotQA", "validation", rows, {ft.norm_question("Seen before?"): {"f"}}, contexts, set())
    assert result["eligible"] == 1 and result["source_rows"] == 4
    assert result["exclusion_reason_counts"] == {"duplicate_normalized_question": 1, "exposed_exact_paragraph": 1,
                                                 "previously_exposed_question": 1}
    assert result["eligible_source_id_sha256"] == ft.sha256_bytes(ft.canonical_bytes(["b"]))


def test_raw_rows_never_load_answer_or_supporting_fact_columns(tmp_path):
    from datasets import Dataset
    assert "answer" not in sum(prep.LABEL_FREE_COLUMNS.values(), [])
    assert "supporting_facts" not in sum(prep.LABEL_FREE_COLUMNS.values(), [])
    Dataset.from_dict({"question": ["q1", "q2"], "answer": ["SECRET", "SECRET"]}).save_to_disk(
        str(tmp_path / prep.RAW["GSM8K", "train"]))
    rows = list(prep.raw_rows("GSM8K", "train", tmp_path))
    assert rows == [{"question": "q1"}, {"question": "q2"}]


def test_selection_plan_is_plan_only_and_records_pending_decisions():
    plan = prep.selection_plan({"GSM8K": {}}, {}, set(), {"evaluation/datasets/a.json": "0" * 64})
    assert plan["status"] == "PLAN_ONLY_NOT_BUILT_NOT_AUTHORIZED"
    assert plan["labels_accessed"] is False and plan["answer_columns_loaded"] is False
    assert "PENDING" in plan["candidate_design"]["sample_size"]
    assert "PENDING" in plan["candidate_design"]["GSM8K_negative_rule"]


def test_generate_refuses_existing_output(tmp_path):
    (tmp_path / "existing.json").write_text("{}", encoding="utf-8")
    with pytest.raises(FileExistsError):
        prep.generate(tmp_path)
