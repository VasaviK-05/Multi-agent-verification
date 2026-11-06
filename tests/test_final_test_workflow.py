from __future__ import annotations

import json

import pytest

from evaluation.data_preparation import final_test_workflow as ft


def item(cid="c1", q="What is 1+1?", sid="q1", gid=None, benchmark="GSM8K", partition=None):
    group = gid or ft.group_id(benchmark, q)
    value = {"benchmark": benchmark, "source_version": "source@abc", "source_id": sid, "question_id": sid,
             "related_group_id": group, "candidate_id": cid, "question": q, "candidate_answer": "2",
             "label_provenance": "benchmark_source_answer"}
    if partition is not None:
        value["partition"] = partition
    return value


def label(cid="c1", status="verified_correct", provenance="benchmark_source_answer", binary=True):
    return {"candidate_id": cid, "correctness_status": status, "label_provenance": provenance,
            "binary_label": binary, "human_adjudicated": False}


def test_history_development_overlap_rejected():
    proposed = item()
    history = item(cid="old", sid="old")
    with pytest.raises(ValueError, match="leakage detected"):
        ft.audit_leakage([proposed], [history], [])


def test_exact_context_and_hotpot_support_provenance_overlap_rejected():
    proposed = item("new", "Who wrote book A?", "new", benchmark="HotpotQA")
    prior = item("old", "Who wrote book B?", "old", benchmark="HotpotQA")
    proposed.update(context=[{"title": "Page", "text": "shared paragraph"}], supporting_facts=[["Page", 0]])
    prior.update(context=[{"title": "Page", "text": "shared paragraph"}], supporting_facts=[["Page", 0]])
    with pytest.raises(ValueError, match="leakage detected"):
        ft.audit_leakage([proposed], [prior], [])


def test_candidate_level_split_leakage_rejected():
    first = item("c1", partition="history")
    second = item("c2", partition="development")
    with pytest.raises(ValueError, match="Candidate-level split leakage"):
        ft.validate_partition([first, second], [label("c1"), label("c2")], {"GSM8K": 1})


def test_duplicate_normalized_questions_rejected():
    first = item("c1", "What is 1+1?", "q1")
    second = item("c2", "WHAT IS 1 1", "q2")
    # The normalized identity is the group identity, so normalize using the canonical group.
    second["related_group_id"] = first["related_group_id"]
    with pytest.raises(ValueError, match="Duplicate normalized questions"):
        ft.validate_partition([first, second], [label("c1"), label("c2")], {"GSM8K": 1})


@pytest.mark.parametrize("field", ["source_id", "related_group_id"])
def test_missing_group_or_source_id_fails_closed(field):
    proposed = item()
    proposed[field] = ""
    if field == "source_id":
        proposed["question_id"] = ""
    with pytest.raises(ValueError, match="Missing required"):
        ft.audit_leakage([proposed], [], [])


def test_missing_label_provenance_rejected():
    proposed = item()
    bad = label(); bad["label_provenance"] = ""
    with pytest.raises(ValueError, match="Missing label provenance"):
        ft.validate_partition([proposed], [bad], {"GSM8K": 1})


def test_unresolved_not_converted_to_negative():
    proposed = item(); proposed["correctness_status"] = "unresolved"; proposed["label"] = "incorrect"
    with pytest.raises(ValueError, match="converted to negative"):
        ft.validate_partition([proposed], [label(status="unresolved", binary=None)], {"GSM8K": 1})
    proposed.pop("label")
    bad_label = label(status="unresolved", binary=False)
    with pytest.raises(ValueError, match="null binary label"):
        ft.validate_partition([proposed], [bad_label], {"GSM8K": 1})


def test_previously_exposed_final_test_path_rejected_without_opening_it(tmp_path, monkeypatch):
    config = tmp_path / "config.yaml"
    config.write_text("previously_exposed_final_test_reuse: true\n", encoding="utf-8")
    with pytest.raises(ValueError, match="explicitly set"):
        ft.build(config)


def test_previously_exposed_final_test_source_path_rejected(tmp_path):
    config = tmp_path / "config.yaml"
    config.write_text(
        "previously_exposed_final_test_reuse: false\n"
        "sample_size: {GSM8K: 1, HotpotQA: 1}\n"
        f"source_paths:\n  GSM8K: '{ft.EXPOSED_FINAL_TEST}'\n  HotpotQA: raw/validation\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="ineligible"):
        ft.build(config)


def test_final_test_access_denied_by_default(tmp_path):
    labels = tmp_path / "labels.jsonl"; labels.write_text('{"candidate_id":"c1"}\n', encoding="utf-8")
    auth = tmp_path / "auth.json"; auth.write_text('{"approved":false}', encoding="utf-8")
    log = tmp_path / "access.jsonl"
    with pytest.raises(PermissionError, match="not authorized"):
        ft.read_custodian_labels(labels, auth, log, person="reviewer", purpose="confirmatory", expected_manifest_sha256="abc")
    assert not log.exists()


def test_authorized_evaluation_access_logged_before_return(tmp_path):
    labels = tmp_path / "labels.jsonl"; labels.write_text('{"candidate_id":"c1"}\n', encoding="utf-8")
    roster = tmp_path / "roster.jsonl"; roster.write_text('{"candidate_id":"c1"}\n', encoding="utf-8")
    audit = {"passed": True, "comparisons": {}}
    manifest = {"partition": "final_test", "enabled": False, "status": "NOT_AUTHORIZED",
                "evaluation_roster_path": str(roster), "candidate_count": 1, "candidate_ids": ["c1"],
                "evaluation_roster_sha256": ft.sha256_file(roster), "label_file_sha256": ft.sha256_file(labels),
                "leakage_audit": audit, "leakage_audit_sha256": ft.sha256_bytes(ft.canonical_bytes(audit))}
    manifest["manifest_sha256"] = ft.sha256_bytes(ft.canonical_bytes(manifest))
    (tmp_path / "manifest.json").write_bytes(ft.canonical_bytes(manifest))
    auth = tmp_path / "auth.json"; auth.write_text(json.dumps({"approved": True, "person": "Ada", "purpose": "frozen evaluation", "manifest_sha256": manifest["manifest_sha256"]}), encoding="utf-8")
    log = tmp_path / "access.jsonl"
    result = ft.read_custodian_labels(labels, auth, log, person="Ada", purpose="frozen evaluation", expected_manifest_sha256=manifest["manifest_sha256"])
    assert result == [{"candidate_id": "c1"}]
    event = json.loads(log.read_text(encoding="utf-8"))
    assert event["person"] == "Ada" and event["purpose"] == "frozen evaluation"
    assert event["label_file_sha256"] == ft.sha256_file(labels)


def test_manifest_hash_integrity(tmp_path):
    roster = tmp_path / "roster.jsonl"; roster.write_text('{"candidate_id":"c1"}\n', encoding="utf-8")
    labels = tmp_path / "labels.jsonl"; labels.write_text('{"candidate_id":"c1"}\n', encoding="utf-8")
    manifest = {"evaluation_roster_sha256": ft.sha256_file(roster), "label_file_sha256": ft.sha256_file(labels)}
    manifest["manifest_sha256"] = ft.sha256_bytes(ft.canonical_bytes(manifest))
    mf = tmp_path / "manifest.json"; mf.write_bytes(ft.canonical_bytes(manifest))
    assert ft.validate_artifacts(roster, labels, mf)["passed"]
    labels.write_text("changed\n", encoding="utf-8")
    with pytest.raises(ValueError, match="label hash mismatch"):
        ft.validate_artifacts(roster, labels, mf)


def test_readiness_validator_blocks_missing_and_unapproved_requirements(tmp_path):
    cfg = tmp_path / "readiness.yaml"
    cfg.write_text("approved_benchmarks: null\nsource_versions: {approved: false}\npolicy_fitting_ready: false\n", encoding="utf-8")
    result = ft.validate_readiness(cfg)
    assert result["confirmatory_readiness"] == "BLOCKED"
    assert result["checks"]["approved_benchmark_population"] == "BLOCKED"
    assert result["checks"]["source_versions"] == "NOT APPROVED"
    assert result["checks"]["final_test_partition_and_custody"] == "BLOCKED"


def test_readiness_validator_current_config_is_not_confirmatory_ready():
    result = ft.validate_readiness(ft.ROOT / "evaluation/config/protocol_readiness.yaml")
    assert result["exploratory_readiness"] == "LIMITED"
    assert result["confirmatory_readiness"] == "BLOCKED"
