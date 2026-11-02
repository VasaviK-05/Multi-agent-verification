import hashlib
import json

import pytest

from app.game.offline.records import Example
from evaluation.data_preparation import build_offline_examples as adapter


def candidate(*, benchmark="GSM8K", status="verified_correct", partition="history",
              candidate_id="gsm-q1-c0", dataset_id="gsm-q1", group_id="gsm-group-1",
              validation_method=None, answer="42"):
    if validation_method is None:
        validation_method = {
            ("GSM8K", "verified_correct"): "benchmark_source_match_plus_independent_arithmetic_replay",
            ("GSM8K", "verified_incorrect"): "raw_worked_solution_source_match_plus_exact_rational_arithmetic_replay_and_distinct_integer_check",
            ("HotpotQA", "verified_correct"): "benchmark_source_answer_match_with_supporting_context_provenance",
            ("HotpotQA", "verified_incorrect"): "source_answer_match_plus_supporting_fact_context_and_literal_negation_check",
        }.get((benchmark, status), "unresolved_diagnostic")
    source = {
        "candidate_id": candidate_id,
        "dataset_id": dataset_id,
        "related_group_id": group_id,
        "benchmark": benchmark,
        "partition": partition,
        "question": "How many items are there?" if benchmark == "GSM8K" else "Who was the person?",
        "candidate_answer": answer,
        "gold_answer": "42" if benchmark == "GSM8K" else "Example Person",
        "correctness_status": status,
        "validation_method": validation_method,
        "candidate_generation_method": "benchmark_gold" if status == "verified_correct" else "test_control",
        "construction_version": "test-construction-v1",
        "validation_basis": {
            "validation_method": validation_method,
            "validation_evidence": [{"kind": "source_evidence", "text": "audit evidence"}],
            "evidence_provenance": {"source": "test-source"},
            "validation_rationale": "A recorded independent basis.",
            "unresolved_reason": "insufficient source support" if status == "unresolved" else None,
        },
        "source_correctness_status": status,
        "source_candidate_record": {"candidate_id": candidate_id, "correctness_status": status},
        "reconciliation": None,
    }
    return source


def test_correct_and_incorrect_statuses_map_to_binary_labels():
    assert adapter.map_status("verified_correct") is True
    assert adapter.map_status("verified_incorrect") is False
    assert "independent_ground_truth" in adapter.CONTRACT_LABEL_METHODS
    assert adapter.validate_label_method("independent_ground_truth") == "independent_ground_truth"


def test_unresolved_candidate_is_excluded_without_binary_label():
    row = candidate(status="unresolved", candidate_id="gsm-q1-c1", answer="43")
    prepared, excluded = adapter.prepare_rows({"GSM8K": [row], "HotpotQA": []})
    assert prepared["history"] == []
    assert len(excluded) == 1
    assert excluded[0]["correctness_status"] == "unresolved"
    assert "answer_is_correct" not in excluded[0]
    assert excluded[0]["exclusion_reason"] == "insufficient source support"


def test_duplicate_canonical_candidate_ids_are_rejected():
    first = candidate()
    second = candidate(dataset_id="gsm-q2", candidate_id=first["candidate_id"], group_id="gsm-group-2")
    with pytest.raises(ValueError, match="Duplicate canonical candidate ID"):
        adapter.prepare_rows({"GSM8K": [first, second], "HotpotQA": []})


def test_candidate_group_partition_identity_and_provenance_are_preserved():
    row = candidate(status="verified_incorrect", candidate_id="gsm-q1-c1", answer="43")
    prepared, excluded = adapter.prepare_rows({"GSM8K": [row], "HotpotQA": []})
    output = prepared["history"][0]
    assert excluded == []
    assert output["example_id"] == row["candidate_id"]
    assert output["candidate_id"] == row["candidate_id"]
    assert output["dataset_id"] == row["dataset_id"]
    assert output["related_group_id"] == row["related_group_id"]
    assert output["split_identity"] == row["related_group_id"]
    assert output["partition"] == "history"
    assert output["correctness_status"] == "verified_incorrect"
    assert output["answer_is_correct"] is False
    assert output["label_provenance"]["validation_basis"] == row["validation_basis"]
    assert output["candidate_generation_method"] == row["candidate_generation_method"]
    assert output["construction_version"] == row["construction_version"]
    assert output["offline_example_ready"] is False
    assert "attempts" not in output


def test_history_development_group_leakage_is_rejected():
    history = candidate(partition="history")
    development = candidate(partition="development", candidate_id="gsm-q1-c1", answer="43")
    with pytest.raises(ValueError, match="multiple questions/partitions"):
        adapter.prepare_rows({"GSM8K": [history, development], "HotpotQA": []})


def test_unsupported_label_methods_are_rejected():
    with pytest.raises(ValueError, match="Unsupported offline label method"):
        adapter.validate_label_method("framework_judgment")
    bad = candidate(validation_method="framework_judgment")
    with pytest.raises(ValueError, match="Unsupported validation provenance"):
        adapter.prepare_rows({"GSM8K": [bad], "HotpotQA": []})


def test_rendering_and_manifest_hashes_are_reproducible():
    gsm_correct = candidate()
    gsm_incorrect = candidate(status="verified_incorrect", candidate_id="gsm-q1-c1", answer="43")
    hp = candidate(benchmark="HotpotQA", candidate_id="hp-q2-c0", dataset_id="hp-q2",
                   group_id="hp-group-2", answer="Example Person")
    sources = {"GSM8K": [gsm_correct, gsm_incorrect], "HotpotQA": [hp]}
    hashes = {"gsm8k_reconciled.jsonl": "a" * 64, "hotpotqa_reconciled.jsonl": "b" * 64}
    first = adapter.render_artifacts(sources, hashes)
    second = adapter.render_artifacts(sources, hashes)
    assert first == second
    manifest = json.loads(first["manifest.json"])
    core = {key: value for key, value in manifest.items() if key != "manifest_sha256"}
    actual_manifest_hash = hashlib.sha256(adapter.json_bytes(core)).hexdigest()
    assert manifest["manifest_sha256"] == actual_manifest_hash
    for name, digest in manifest["output_sha256"].items():
        assert hashlib.sha256(first[name]).hexdigest() == digest


def test_example_contract_requires_recordings_and_limits_label_method():
    fields = Example.model_fields
    assert {"attempts", "validation_id", "execution_configuration_id"}.issubset(fields)
    assert set(adapter.CONTRACT_LABEL_METHODS) == {"independent_human", "independent_ground_truth"}
    # Adapter preparation never creates an Example or invents those required fields.
    assert adapter.REQUIRED_RECORDING_FIELDS == (
        "domain", "planning_category", "validation_id", "execution_configuration_id", "cache_contract", "attempts"
    )
