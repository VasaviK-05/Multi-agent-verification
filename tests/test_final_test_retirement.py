"""Retirement, content-level exposure, and Final Test readiness gate. Synthetic fixtures only."""
from __future__ import annotations

import json

import pytest

from evaluation.data_preparation import final_test_workflow as ft

PROVISIONAL_SHA = "cc186376c9d884ecadbfed342e9ea40773840cc305e11c2d7327f42e1db87e46"
READINESS_KEYS = ("approved_benchmarks", "source_versions", "candidate_label_policy", "label_audit",
                  "verifier_eligibility", "evidence_configuration", "loss_configuration", "threshold_configuration",
                  "resource_budget", "attack_scenarios", "metrics_outcomes", "statistical_analysis_plan",
                  "development_pilot", "sample_size_justification", "attempts", "offline_examples",
                  "license_citation_status")


def registry(tmp_path, entries):
    path = tmp_path / "retirements.json"
    path.write_text(json.dumps({"version": "final_test_retirement_registry_v1", "retired": entries}), encoding="utf-8")
    return path


def entry(digest="a" * 64, **update):
    return {"manifest_sha256": digest, "confirmatory_use": "PERMANENTLY_FORBIDDEN", "reason": "contaminated", **update}


def mixed_manifest(**update):
    manifest = {"partition": "final_test", "status": "NOT_AUTHORIZED", "enabled": False,
                "label_counts": {"GSM8K": {"verified_correct": 3, "verified_incorrect": 2, "unresolved": 0},
                                 "HotpotQA": {"verified_correct": 3, "verified_incorrect": 1, "unresolved": 1}},
                "exposure_audit": {"method": ft.EXPOSURE_METHOD, "passed": True}, **update}
    manifest["manifest_sha256"] = ft.sha256_bytes(ft.canonical_bytes(manifest))
    return manifest


def test_missing_registry_retires_nothing(tmp_path):
    assert ft.load_retirements(tmp_path / "absent.json") == {}


@pytest.mark.parametrize("bad", [entry(digest="short"), entry(confirmatory_use="ALLOWED"), entry(reason=" ")])
def test_malformed_retirement_entries_fail_closed(tmp_path, bad):
    with pytest.raises(ValueError):
        ft.load_retirements(registry(tmp_path, [bad]))
    with pytest.raises(ValueError):
        ft.load_retirements(registry(tmp_path, [entry(), entry()]))


def test_retired_labels_refused_before_authorization_or_log(tmp_path):
    log = tmp_path / "access.jsonl"
    with pytest.raises(PermissionError, match="retired"):
        ft.read_custodian_labels(tmp_path / "never_opened.jsonl", tmp_path / "never_opened_auth.json", log,
                                 person="Ada", purpose="frozen evaluation", expected_manifest_sha256="a" * 64,
                                 retirements=registry(tmp_path, [entry()]))
    assert not log.exists()


def test_repository_registry_retires_the_provisional_final_test():
    retired = ft.load_retirements()
    assert retired[PROVISIONAL_SHA]["dataset_version"] == "research_v1_final_test_provisional_v1"
    assert retired[PROVISIONAL_SHA]["artifacts_preserved_unchanged"] is True


def test_provisional_manifest_is_blocked_by_gate():
    manifest = ft.ROOT / "evaluation/datasets/final_test_research_v1_eval_v1/manifest.json"
    if not manifest.exists():
        pytest.skip("local Git-ignored provisional Final Test is not present")
    result = ft.validate_readiness(ft.ROOT / "evaluation/config/protocol_readiness.yaml", manifest)
    reasons = result["final_test_gate_reasons"]
    assert result["checks"]["final_test_partition_and_custody"] == "BLOCKED"
    assert "retired_permanently_forbidden_for_confirmatory_use" in reasons
    assert "no_incorrect_candidates:GSM8K" in reasons and "no_incorrect_candidates:HotpotQA" in reasons
    assert "missing_passing_content_level_exposure_audit" in reasons


def test_gate_requires_both_classes_exposure_audit_and_external_authorization():
    good = mixed_manifest()
    assert ft.final_test_gate({}, None, {}) == ("BLOCKED", ["no_final_test_manifest"])
    assert ft.final_test_gate(good, None, {}) == ("NOT APPROVED", ["no_confirmatory_authorization_record"])
    auth = {"approved": True, "manifest_sha256": good["manifest_sha256"], "approver": "Protocol owner", "custodian": "Custodian"}
    assert ft.final_test_gate(good, auth, {}) == ("APPROVED", [])
    for broken in ({**auth, "manifest_sha256": "b" * 64}, {**auth, "custodian": ""}, {**auth, "approved": False}):
        assert ft.final_test_gate(good, broken, {})[0] == "BLOCKED"
    assert ft.final_test_gate(good, auth, {good["manifest_sha256"]: entry()})[0] == "BLOCKED"
    gold_only = mixed_manifest(label_counts={"GSM8K": {"verified_correct": 3, "verified_incorrect": 0}})
    assert ft.final_test_gate(gold_only, auth, {}) == ("BLOCKED", ["no_incorrect_candidates:GSM8K"])
    synthetic = mixed_manifest(label_counts={"GSM8K": {"VERIFIED_CORRECT": 3, "SYNTHETIC_INCORRECT": 3}})
    assert ft.final_test_gate(synthetic, {**auth, "manifest_sha256": synthetic["manifest_sha256"]}, {}) == ("APPROVED", [])
    assert ft.label_basis({"VERIFIED_CORRECT": 3, "SYNTHETIC_INCORRECT": 2, "HUMAN_VERIFIED_INCORRECT": 1}) == {
        "correct": 3, "incorrect": 3,
        "incorrect_by_label_source": {"legacy_unspecified": 0, "human_verified": 1, "synthetic": 2}}
    no_gold = mixed_manifest(label_counts={"HotpotQA": {"SYNTHETIC_INCORRECT": 2}})
    assert ft.final_test_gate(no_gold, auth, {}) == ("BLOCKED", ["no_correct_candidates:HotpotQA"])
    unaudited = mixed_manifest(exposure_audit=None)
    assert ft.final_test_gate(unaudited, auth, {})[1] == ["missing_passing_content_level_exposure_audit"]
    tampered = {**good, "enabled": True}
    assert "manifest_hash_mismatch" in ft.final_test_gate(tampered, auth, {})[1]


def test_confirmatory_readiness_is_reachable_only_with_every_approval(tmp_path):
    config = tmp_path / "readiness.yaml"
    extra = {"development_pilot": ", completed: true", "attempts": ", complete_count: 1", "offline_examples": ", complete_count: 1"}
    config.write_text("".join(f"{k}: {{approved: true{extra.get(k, '')}}}\n" for k in READINESS_KEYS)
                      + "policy_fitting_ready: true\n", encoding="utf-8")
    manifest = mixed_manifest()
    manifest_path = tmp_path / "manifest.json"; manifest_path.write_bytes(ft.canonical_bytes(manifest))
    auth = tmp_path / "auth.json"
    auth.write_text(json.dumps({"approved": True, "manifest_sha256": manifest["manifest_sha256"],
                                "approver": "Protocol owner", "custodian": "Custodian"}), encoding="utf-8")
    empty = registry(tmp_path, [])
    assert ft.validate_readiness(config, manifest_path, auth, empty)["confirmatory_readiness"] == "READY"
    assert ft.validate_readiness(config, manifest_path, None, empty)["confirmatory_readiness"] == "BLOCKED"
    retired = registry(tmp_path, [entry(manifest["manifest_sha256"])])
    assert ft.validate_readiness(config, manifest_path, auth, retired)["confirmatory_readiness"] == "BLOCKED"


def test_missing_data_is_blocked_not_pending_approval(tmp_path):
    config = tmp_path / "readiness.yaml"
    config.write_text("development_pilot: {approved: true, completed: false}\nattempts: {approved: true, complete_count: 0}\n"
                      "offline_examples: {complete_count: 0}\n", encoding="utf-8")
    checks = ft.validate_readiness(config)["checks"]
    assert checks["development_pilot_completion"] == checks["attempts_availability"] == "BLOCKED"
    assert checks["offline_examples_availability"] == "BLOCKED"


def test_question_texts_found_at_any_depth_and_normalized():
    record = {"rows": [{"question": "What is 1+1?"}, {"inner": {"question": "Who?"}}], "question_id": "x"}
    assert sorted(ft.iter_question_texts(record)) == ["What is 1+1?", "Who?"]


def test_exposure_files_skip_custodian_and_excluded_directories(tmp_path):
    for relative in ("evaluation/datasets/a.jsonl", "evaluation/datasets/_custodian/x/labels.jsonl",
                     "evaluation/datasets/target/roster.jsonl", "evaluation/results/r.json", "evaluation/results/n.txt"):
        path = tmp_path / relative; path.parent.mkdir(parents=True, exist_ok=True); path.write_text("{}\n", encoding="utf-8")
    found = ft.exposure_files(tmp_path, exclude=(tmp_path / "evaluation/datasets/target",))
    assert [p.relative_to(tmp_path).as_posix() for p in found] == ["evaluation/datasets/a.jsonl", "evaluation/results/r.json"]


def test_exposure_index_reasons_and_audit_use_question_content_not_ids(tmp_path):
    exposed = tmp_path / "evaluation/results/run.jsonl"; exposed.parent.mkdir(parents=True)
    exposed.write_text(json.dumps({"example_id": "different-id", "question": "WHAT is 1 + 1"}) + "\n", encoding="utf-8")
    index = ft.exposure_index([exposed], tmp_path)
    rows = [{"related_group_id": "g1", "question": "What is 1+1?", "source_id": "q1"},
            {"related_group_id": "g2", "question": "Fresh question?", "source_id": "q2"}]
    assert ft.exposure_reasons(rows[0], index) == ["previously_exposed_question"] and not ft.exposure_reasons(rows[1], index)
    audit = ft.exposure_audit(rows, index, [exposed], tmp_path)
    assert audit["passed"] is False and audit["overlapping_group_count"] == 1
    assert audit["overlap_counts_by_file"] == {"evaluation/results/run.jsonl": 1}
    assert ft.exposure_audit(rows[1:], index, [exposed], tmp_path)["passed"] is True
