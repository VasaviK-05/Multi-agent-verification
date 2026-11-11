from __future__ import annotations

import json

import pytest

from evaluation.data_preparation import run_development_feasibility_pilot as pilot
from evaluation.data_preparation.final_test_workflow import validate_readiness


def _candidate(cid, status, answer, index):
    return {
        "candidate_id": cid, "dataset_id": "gsm-source", "question_id": "GSM8K:gsm-source",
        "related_group_id": "gsm-group", "partition": "development", "benchmark": "GSM8K",
        "question": "How many objects?", "candidate_answer": answer, "correctness_status": status,
        "validation_method": "source_replay_test", "validation_basis": {"evidence": "fixture"},
        "source_candidate_record": {"source": "test-fixture"}, "validation_evidence": [{"kind": "fixture"}],
    }


def _fixture(tmp_path):
    prepared = tmp_path / "development_prepared.jsonl"
    reconciled = tmp_path / "development_candidates.jsonl"
    sources = [_candidate("c_correct", "verified_correct", "2", 0),
               _candidate("c_wrong", "verified_incorrect", "3", 1),
               _candidate("c_unresolved", "unresolved", "4", 2)]
    prepared_rows = []
    for source in sources[:2]:
        prepared_rows.append({
            "candidate_id": source["candidate_id"], "dataset_id": source["dataset_id"],
            "question_id": source["question_id"], "related_group_id": source["related_group_id"],
            "partition": "development", "benchmark": "GSM8K", "question": source["question"],
            "candidate_answer": source["candidate_answer"],
            "correctness_status": source["correctness_status"],
            "answer_is_correct": source["correctness_status"] == "verified_correct",
            "label_method": "independent_ground_truth",
            "verifier_input": {"benchmark": "GSM8K", "question": source["question"],
                               "candidate_answer": source["candidate_answer"], "evidence_context": []},
        })
    prepared.write_text("".join(json.dumps(row) + "\n" for row in prepared_rows), encoding="utf-8")
    reconciled.write_text("".join(json.dumps(row) + "\n" for row in sources), encoding="utf-8")
    return prepared, reconciled


def test_development_only_access_and_reproducible_roster(tmp_path):
    prepared, reconciled = _fixture(tmp_path)
    first = pilot.load_development_roster(prepared, reconciled)
    second = pilot.load_development_roster(prepared, reconciled)
    assert first["source_hashes"] == second["source_hashes"]
    assert first["rows"] == second["rows"]
    assert first["source_candidate_count"] == 3
    assert first["labelled_candidate_count"] == 2
    assert first["unresolved"][0]["correctness_status"] == "unresolved"
    assert all(row["partition"] == "development" for row in first["rows"])
    assert "answer_is_correct" not in first["rows"][0]


def test_final_test_input_path_is_rejected_before_read(tmp_path):
    prepared, reconciled = _fixture(tmp_path)
    bad = tmp_path / "final_test" / "development_candidates.jsonl"
    with pytest.raises(ValueError, match="Development input artifact"):
        pilot.load_development_roster(prepared, bad)


def test_invalid_labels_fail_closed(tmp_path):
    prepared, reconciled = _fixture(tmp_path)
    rows = [json.loads(line) for line in prepared.read_text(encoding="utf-8").splitlines()]
    rows[0]["answer_is_correct"] = "true"
    prepared.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
    with pytest.raises(ValueError, match="invalid or inconsistent binary label"):
        pilot.load_development_roster(prepared, reconciled)


def test_missing_label_provenance_fails_closed(tmp_path):
    prepared, reconciled = _fixture(tmp_path)
    rows = [json.loads(line) for line in reconciled.read_text(encoding="utf-8").splitlines()]
    rows[0]["validation_method"] = ""
    reconciled.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
    with pytest.raises(ValueError, match="missing label provenance"):
        pilot.load_development_roster(prepared, reconciled)


def test_missing_dependencies_create_blocked_artifact_without_calls(tmp_path, monkeypatch):
    prepared, reconciled = _fixture(tmp_path)
    monkeypatch.delenv("VERIFIER_COLLECTION_ADAPTER_CONFIG", raising=False)
    output = tmp_path / "pilot-output"
    result = pilot.run(output, prepared, reconciled)
    assert result["status"] == "BLOCKED_PREFLIGHT"
    assert result["actual_verifier_calls"] == 0
    assert result["final_test_accessed"] is False
    assert "unset" in result["preflight_blockers"][0]["reason"]
    assert not (output / "attempts.jsonl").exists()


def test_execution_failures_and_missing_outputs_are_counted(tmp_path):
    prepared, reconciled = _fixture(tmp_path)
    roster = pilot.load_development_roster(prepared, reconciled)
    cid = roster["rows"][0]["candidate_id"]
    failed = {"candidate_id": cid, "attempt": {"verifier_name": "semantic", "state": "failed", "report_json": None},
              "duration_ms": 12.5}
    report = pilot.analyze_attempts(roster, {(cid, "semantic"): failed}, 0.2)
    assert report["states_all_verifiers"]["failed"] == 1
    assert report["states_all_verifiers"]["missing"] == 7
    assert report["missing_attempt_outputs"] == 7
    assert report["status"] == "INCOMPLETE"
    assert report["runtime"]["cost"].startswith("not measured")


def test_missing_attempt_outputs_are_not_fabricated(tmp_path):
    prepared, reconciled = _fixture(tmp_path)
    roster = pilot.load_development_roster(prepared, reconciled)
    report = pilot.analyze_attempts(roster, {}, 0.0)
    assert report["recorded_calls"] == 0
    assert report["missing_attempt_outputs"] == 8
    assert report["groups_attempted"] == 0


def test_output_validation_rejects_non_development_manifest(tmp_path):
    prepared, reconciled = _fixture(tmp_path)
    roster = pilot.load_development_roster(prepared, reconciled)
    output = tmp_path / "output"
    output.mkdir()
    (output / "pilot_manifest.json").write_text(json.dumps({
        "partition": "history", "final_test_accessed": False, "history_inputs_read": False,
        "source_hashes": roster["source_hashes"],
    }), encoding="utf-8")
    with pytest.raises(ValueError, match="Development-only"):
        pilot.validate_output(output, roster)


def test_readiness_keeps_policy_fitting_blocked():
    result = validate_readiness(pilot.ROOT / "evaluation/config/protocol_readiness.yaml")
    assert result["confirmatory_readiness"] == "BLOCKED"
    assert result["checks"]["policy_fitting_readiness"] == "BLOCKED"
    assert result["checks"]["attempts_availability"] == "BLOCKED"
