from __future__ import annotations

import copy

import pytest

from evaluation.data_preparation import build_research_dataset as pipeline


def row(dataset_id: str, benchmark: str, question: str) -> dict:
    return {
        "id": dataset_id,
        "benchmark": benchmark,
        "question": question,
        "gold_answer": "1",
        "candidate_answers": [
            {"answer": "1", "source": "benchmark_gold", "expected_correct": True},
            {"answer": "2", "source": "synthetic_numeric_perturbation", "expected_correct": False},
        ],
    }


def test_incremental_sampling_is_deterministic_and_preserves_prior_identity():
    original = row("gsm8k_train_0", "GSM8K", "How many apples are there?")
    additions = [row(f"gsm8k_train_{i}", "GSM8K", f"How many apples are there in case {i}?") for i in range(1, 8)]
    by_part = {"history": [original, *additions[:4]], "development": additions[4:]}
    old_gid = pipeline.group_id("GSM8K", original["question"])
    prior = {old_gid: {"dataset_id": original["id"], "partition": "history", "question": original["question"]}}
    quotas = {"history": 3, "development": 2}
    first = pipeline.sample_incremental_groups(by_part, "GSM8K", prior, quotas, 42)
    second = pipeline.sample_incremental_groups(by_part, "GSM8K", prior, quotas, 42)
    assert [(x["row"]["id"], x["partition"]) for x in first] == [(x["row"]["id"], x["partition"]) for x in second]
    kept = next(x for x in first if x["row"]["id"] == original["id"])
    assert kept["group_id"] == old_gid and kept["partition"] == "history" and kept["reused"]
    assert len({x["group_id"] for x in first}) == 5


def test_group_and_candidate_ids_are_stable_across_versions():
    question = "How many apples are there?"
    assert pipeline.group_id("GSM8K", question) == pipeline.group_id("GSM8K", question)
    assert pipeline.group_id("GSM8K", question) != pipeline.group_id("HotpotQA", question)
    assert f"gsm8k_train_17::candidate_0" == f"{row('gsm8k_train_17', 'GSM8K', question)['id']}::candidate_0"


def test_duplicate_normalized_group_does_not_inflate_selected_groups():
    a = row("gsm8k_train_1", "GSM8K", "How many apples?")
    b = row("gsm8k_train_2", "GSM8K", "HOW MANY APPLES!!!")
    c = row("gsm8k_train_3", "GSM8K", "How many oranges?")
    result = pipeline.sample_incremental_groups({"history": [a, b, c], "development": []}, "GSM8K", {}, {"history": 2, "development": 0}, 5)
    assert len({item["group_id"] for item in result}) == 2
    assert len(result) == 2


def test_candidate_validator_rejects_history_development_group_leakage():
    a = {
        "candidate_id": "x::candidate_0", "dataset_id": "x", "benchmark": "GSM8K",
        "related_group_id": "same", "partition": "history", "correctness_status": "verified_correct",
        "source_candidate_index": 0, "validation_method": "source", "unresolved_reason": None,
    }
    b = copy.deepcopy(a)
    b.update(candidate_id="x::candidate_1", partition="development", correctness_status="unresolved", unresolved_reason="review")
    selected = {"GSM8K": [{"group_id": "same", "row": {"id": "x"}, "partition": "history", "reused": False}],
                "HotpotQA": [{"group_id": "hp", "row": {"id": "hp"}, "partition": "history", "reused": False}]}
    with pytest.raises(ValueError, match="group roster|group count|leakage"):
        pipeline.validate_candidate_rows({"GSM8K": [a, b], "HotpotQA": []}, selected,
                                         {"GSM8K": {"history": 1, "development": 0}, "HotpotQA": {"history": 1, "development": 0}})


def test_candidate_validator_rejects_duplicate_canonical_ids():
    a = {"candidate_id": "same", "dataset_id": "x", "benchmark": "GSM8K", "related_group_id": "g",
         "partition": "history", "correctness_status": "verified_correct", "source_candidate_index": 0}
    b = dict(a, source_candidate_index=1)
    selected = {"GSM8K": [{"group_id": "g", "row": {"id": "x"}, "partition": "history", "reused": False}], "HotpotQA": []}
    with pytest.raises(ValueError, match="duplicate canonical candidate IDs"):
        pipeline.validate_candidate_rows({"GSM8K": [a, b], "HotpotQA": []}, selected,
            {"GSM8K": {"history": 1, "development": 0}, "HotpotQA": {"history": 0, "development": 0}})


def test_unresolved_and_hotpot_borrowed_candidates_cannot_be_auto_negative():
    row_data = {
        "candidate_id": "hp::candidate_1", "dataset_id": "hp", "benchmark": "HotpotQA",
        "related_group_id": "hp-group", "partition": "history", "correctness_status": "unresolved",
        "source_candidate_index": 1, "candidate_source": "synthetic_cross_example_answer", "unresolved_reason": "review",
        "candidate_answer": "Borrowed",
    }
    selected = {"GSM8K": [], "HotpotQA": [{"group_id": "hp-group", "row": {"id": "hp"}, "partition": "history", "reused": False}]}
    result = pipeline.validate_candidate_rows({"GSM8K": [], "HotpotQA": [row_data]}, selected,
        {"GSM8K": {"history": 0, "development": 0}, "HotpotQA": {"history": 1, "development": 0}})
    assert result["benchmarks"]["HotpotQA"]["unresolved"] == 1
    row_data["correctness_status"] = "verified_incorrect"
    with pytest.raises(ValueError, match="cannot be auto-labelled incorrect"):
        pipeline.validate_candidate_rows({"GSM8K": [], "HotpotQA": [row_data]}, selected,
            {"GSM8K": {"history": 0, "development": 0}, "HotpotQA": {"history": 1, "development": 0}})


def test_prior_hotpot_negation_is_preserved_but_not_imported_as_incorrect():
    source = {
        "candidate_id": "hp::candidate_2", "benchmark": "HotpotQA",
        "correctness_status": "verified_incorrect", "source_correctness_status": "verified_incorrect",
        "validation_method": "source_answer_match_plus_supporting_fact_context_and_literal_negation_check",
        "validation_basis": {"validation_evidence": [{"kind": "support"}]},
    }
    derived = pipeline.apply_conservative_hotpot_label_policy([source])[0]
    assert derived["correctness_status"] == "unresolved"
    assert derived["source_correctness_status"] == "verified_incorrect"
    assert derived["prior_active_correctness_status"] == "verified_incorrect"
    assert derived["protocol_status_adjustment"] == "verified_incorrect_to_unresolved"
    assert source["correctness_status"] == "verified_incorrect"


def test_serialization_hashes_are_deterministic():
    value = [{"candidate_id": "x", "label": "unresolved"}]
    assert pipeline.digest_bytes(pipeline.jsonl_bytes(value)) == pipeline.digest_bytes(pipeline.jsonl_bytes(value))


def test_offline_verifier_input_excludes_gold_and_solution_provenance():
    from evaluation.data_preparation.build_offline_examples import prepare_rows

    source = {
        "candidate_id": "gsm8k_train_1::candidate_0", "dataset_id": "gsm8k_train_1", "benchmark": "GSM8K",
        "related_group_id": "g1", "partition": "history", "correctness_status": "verified_correct",
        "question": "What is 1 + 1?", "candidate_answer": "2", "gold_answer": "2",
        "validation_method": "benchmark_source_match_plus_independent_arithmetic_replay",
        "validation_basis": {"validation_method": "benchmark_source_match_plus_independent_arithmetic_replay",
                             "validation_evidence": [{"kind": "replay", "solution": "<<1+1=2>>"}]},
        "source_candidate_record": {"candidate_id": "gsm8k_train_1::candidate_0",
                                    "original_unified_source_record": {"solution": "gold worked solution"}},
        "candidate_source": "benchmark_gold", "candidate_generation_method": "benchmark_gold",
    }
    prepared, _ = prepare_rows({"GSM8K": [source], "HotpotQA": []})
    verifier_input = prepared["history"][0]["verifier_input"]
    assert verifier_input == {"benchmark": "GSM8K", "question": "What is 1 + 1?", "candidate_answer": "2", "evidence_context": []}
    assert "gold_answer" not in verifier_input and "solution" not in str(verifier_input)
