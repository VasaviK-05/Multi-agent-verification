from __future__ import annotations

import json

import pytest

from evaluation.data_preparation import final_test_workflow as ft
from evaluation.data_preparation import person1_validation as p1

GSM = p1.SOURCE_VERSIONS["GSM8K"]


def cand(cid, question, partition, status="verified_correct", benchmark="GSM8K", dataset_id=None, method="benchmark_gold"):
    dataset_id = dataset_id or f"src-{question}"
    nested = {}
    if benchmark == "HotpotQA":
        nested = {"evidence_provenance": {"source_id": dataset_id, "context_hashes": [f"h-{question}"],
                                          "supporting_facts": [{"title": question, "sentence_id": 0}]}}
    return {"candidate_id": cid, "source_candidate_record": nested, "question": question, "benchmark": benchmark, "partition": partition,
            "dataset_id": dataset_id, "related_group_id": ft.group_id(benchmark, question),
            "correctness_status": status, "candidate_generation_method": method,
            "dataset_version": p1.SOURCE_VERSIONS[benchmark],
            "validation_method": "rule" if status != "unresolved" else None,
            "validation_basis": {"evidence_provenance": {"source_id": dataset_id},
                                 "unresolved_reason": "needs review" if status == "unresolved" else None}}


def dataset():
    return {
        "history": [cand("h1", "q one", "history"), cand("h2", "q one", "history", "verified_incorrect", method="perturb")],
        "development": [
            cand("d1", "q two", "development"), cand("d2", "q two", "development", "unresolved"),
            cand("d3", "q three", "development", "unresolved"),
            cand("d4", "q four", "development", benchmark="HotpotQA"),
            cand("d5", "q five", "development", benchmark="HotpotQA"),
        ],
    }


def test_composition_detects_duplicates_and_cross_partition_groups():
    rows = dataset()
    assert not any(p1.composition(rows)["duplicates"].values())
    rows["development"].append(cand("h1", "q one", "development"))
    dup = p1.composition(rows)["duplicates"]
    assert dup["duplicate_candidate_ids"] == 1 and dup["groups_in_multiple_partitions"] == 1


def test_composition_flags_unknown_status_and_missing_unresolved_reason():
    rows = dataset()
    rows["development"][1]["validation_basis"]["unresolved_reason"] = None
    rows["history"][0]["correctness_status"] = "probably_correct"
    comp = p1.composition(rows)
    assert comp["unknown_statuses"] == ["probably_correct"]
    assert comp["provenance"]["unresolved_without_reason"] == 1


def test_identity_leakage_is_reported():
    rows = dataset()
    assert not any(v for b in p1.history_development_leakage(rows)["identity_overlaps"].values() for v in b.values())
    rows["development"].append(cand("d9", "Q ONE!", "development"))
    assert p1.history_development_leakage(rows)["identity_overlaps"]["GSM8K"]["normalized_questions"] == 1


def test_development_roster_excludes_unresolved_and_reports_groups_without_binary_labels():
    rosters = p1.development_rosters(dataset())
    assert {c["candidate_id"] for c in rosters["candidates"]} == {"d1", "d4", "d5"}
    assert all(c["correctness_status"] != "unresolved" for c in rosters["candidates"])
    assert [g["dataset_id"] for g in rosters["ineligible_groups"]] == ["src-q three"]
    assert rosters["ineligible_groups"][0]["reason"] == "no_binary_labelled_candidate"


def test_ordered_roster_is_deterministic_label_free_group_complete_and_alternating():
    rosters = p1.development_rosters(dataset())
    first = p1.ordered_group_roster(rosters["groups"], rosters["candidates"], "salt")
    assert first == p1.ordered_group_roster(list(reversed(rosters["groups"])), list(reversed(rosters["candidates"])), "salt")
    assert all("correctness_status" not in r and "answer_is_correct" not in r for r in first)
    assert {r["candidate_id"] for r in first} == {c["candidate_id"] for c in rosters["candidates"]}
    assert first[0]["benchmark"] == "GSM8K" and first[1]["benchmark"] == "HotpotQA"
    assert [r["group_rank"] for r in first] == sorted(r["group_rank"] for r in first)


def test_unresolved_queue_never_assigns_labels():
    queue = p1.unresolved_queue(dataset())
    assert {q["candidate_id"] for q in queue} == {"d2", "d3"}
    assert all(q["assigned_label"] is None and q["review_status"] == "PENDING_INDEPENDENT_HUMAN_REVIEW" for q in queue)


def test_estimability_marks_missing_negative_class():
    est = p1.estimability(dataset())
    assert est["development:HotpotQA"]["false_acceptance_rate"].startswith("NOT ESTIMABLE")
    assert est["history:GSM8K"]["false_acceptance_rate"] == "ESTIMABLE_AFTER_ATTEMPTS"


def test_experiment_contracts_leave_budgets_and_loss_pending():
    contracts = p1.experiment_contracts({"development_eligible_candidates.jsonl": "a", "live_runtime_validation_order.jsonl": "b"},
                                        dataset(), "m")
    exp = contracts["experiments"]
    assert exp["2_budget_sensitivity"]["budgets"]["values"] is None
    assert exp["2_budget_sensitivity"]["budgets"]["minimum_count"] == 3
    assert exp["1_clean_and_attacked"]["loss_configuration"] == {"value": None, "status": "PENDING_APPROVAL"}
    assert set(exp["1_clean_and_attacked"]["attack_scenarios"]) == {"clean", "forced_support", "forced_rejection",
                                                                     "confidence_inflation", "suppression"}


def _final_test_fixture(tmp_path, rows):
    eval_dir, cust_dir = tmp_path / "eval", tmp_path / "cust"
    eval_dir.mkdir(), cust_dir.mkdir()
    roster = [{"benchmark": "GSM8K", "question": "fresh question", "question_id": "t1", "source_id": "t1",
               "related_group_id": ft.group_id("GSM8K", "fresh question"), "candidate_id": "t1:c0",
               "candidate_generation_method": "benchmark_gold", "source_split": "test", "source_version": GSM}]
    roster_bytes = ft.jsonl_bytes(roster)
    audit = ft.audit_leakage(roster, rows["history"], rows["development"])
    audit_bytes = ft.canonical_bytes(audit)
    labels = b"this is not json and must never be parsed\n"
    core = {"status": "NOT_AUTHORIZED", "enabled": False, "source_sha256": {}, "candidate_ids": ["t1:c0"],
            "group_ids": [roster[0]["related_group_id"]], "leakage_audit": audit,
            "evaluation_roster_sha256": ft.sha256_bytes(roster_bytes), "label_file_sha256": ft.sha256_bytes(labels),
            "leakage_audit_sha256": ft.sha256_bytes(audit_bytes), "custody": {"human_custodian": None}}
    core["manifest_sha256"] = ft.sha256_bytes(ft.canonical_bytes(core))
    manifest = ft.canonical_bytes(core)
    (eval_dir / "evaluation_roster.jsonl").write_bytes(roster_bytes)
    (eval_dir / "leakage_audit.json").write_bytes(audit_bytes)
    (cust_dir / "custodian_labels.jsonl").write_bytes(labels)
    for d in (eval_dir, cust_dir):
        (d / "manifest.json").write_bytes(manifest)
    receipt = {"evaluation_roster.jsonl": ft.sha256_bytes(roster_bytes), "leakage_audit.json": ft.sha256_bytes(audit_bytes),
               "evaluation_manifest.json": ft.sha256_bytes(manifest), "custodian_labels.jsonl": ft.sha256_bytes(labels),
               "custodian_manifest.json": ft.sha256_bytes(manifest)}
    for d in (eval_dir, cust_dir):
        (d / "integrity_receipt.json").write_text(json.dumps(receipt), encoding="utf-8")
    return eval_dir, cust_dir


def test_final_test_isolation_verifies_hashes_without_parsing_labels(tmp_path):
    rows = dataset()
    eval_dir, cust_dir = _final_test_fixture(tmp_path, rows)
    result = p1.final_test_isolation(rows, eval_dir, cust_dir)
    assert result["label_payload_parsed"] is False
    assert result["manifest_self_hash_verified"] and result["label_payload_byte_hash_verified"] and result["integrity_receipt_verified"]
    assert result["recomputed_matches_frozen_audit"] and not any(result["recomputed_leakage_comparisons"].values())
    assert result["roster_label_fields_present"] == []


def test_final_test_isolation_detects_label_tampering(tmp_path):
    rows = dataset()
    eval_dir, cust_dir = _final_test_fixture(tmp_path, rows)
    (cust_dir / "custodian_labels.jsonl").write_bytes(b"changed\n")
    result = p1.final_test_isolation(rows, eval_dir, cust_dir)
    assert not result["label_payload_byte_hash_verified"] and not result["integrity_receipt_verified"]


def test_final_test_leakage_with_development_fails_closed(tmp_path):
    rows = dataset()
    eval_dir, cust_dir = _final_test_fixture(tmp_path, rows)
    rows["development"].append(cand("leak", "fresh question", "development", dataset_id="t1"))
    with pytest.raises(ValueError, match="leakage detected"):
        p1.final_test_isolation(rows, eval_dir, cust_dir)


def test_generate_refuses_existing_output(tmp_path):
    with pytest.raises(FileExistsError):
        p1.generate(tmp_path)
