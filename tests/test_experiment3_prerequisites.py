"""Experiment 3 prerequisite states. The live package is not an empirical authorization."""

import json
import shutil
from pathlib import Path

from evaluation.data_preparation.final_test_workflow import ROOT, sha256_file
from evaluation.analysis.experiment3 import REQUIRED_FIELDS
from evaluation.experiments.experiment3.prerequisite_validator import (
    BLOCKED, COLLECTION, COLLECTION_AUTHORIZATION, CORPUS, CORPUS_APPROVAL, DEPENDENCY, DEPENDENCY_APPROVAL,
    DEPENDENCY_DECISION, PROTOCOL_APPROVAL, READY_FOR_APPROVAL, READY_FOR_COLLECTION_AUTHORIZATION,
    READY_FOR_DEVELOPMENT_COLLECTION, READY_FOR_EMPIRICAL_EXPERIMENT, READY_FOR_EMPIRICAL_EXPERIMENT_ANALYSIS,
    REPUTATION, SETTINGS_PROPOSAL, SPEC, assess,
)

PACKAGE = [SPEC, CORPUS, COLLECTION, DEPENDENCY, REPUTATION, SETTINGS_PROPOSAL, DEPENDENCY_DECISION,
           PROTOCOL_APPROVAL, CORPUS_APPROVAL, DEPENDENCY_APPROVAL, COLLECTION_AUTHORIZATION]
GATE_SETTINGS = {
    "false_acceptance_loss": 1.0, "false_rejection_loss": 1.0, "uncertainty_loss": 0.2,
    "resource_coefficient": 1.0, "decision_threshold": 0.55, "verifier_budget": 1.0,
    "suppression_mode": "unavailable", "bootstrap_resamples": 20, "confidence_level": 0.95,
    "bootstrap_seed": 1, "sample_size_justification": "gate fixture only",
}


def _copy_package(tmp_path: Path, *, clear_corpus_conflict: bool = True) -> None:
    for relative in PACKAGE:
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(ROOT / relative, target)
    for relative in (
        "evaluation/artifacts/person1/research_v1_exploratory_eligibility_approved_v1/eligibility_manifest.json",
        "evaluation/artifacts/person1/development_evidence_corpus_v1/corpus.json",
    ):
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(ROOT / relative, target)
    if clear_corpus_conflict:
        corpus = json.loads((tmp_path / CORPUS).read_text(encoding="utf-8"))
        corpus["checksum_status"] = "MATCHES_FILE"
        (tmp_path / CORPUS).write_text(json.dumps(corpus), encoding="utf-8")


def _write(tmp_path: Path, relative: str, payload: dict) -> None:
    (tmp_path / relative).write_text(json.dumps(payload), encoding="utf-8")


def _sign(tmp_path: Path, record_path: str, artifact: str, **extra) -> None:
    record = json.loads((tmp_path / record_path).read_text(encoding="utf-8"))
    record.update(status="APPROVED", decision="APPROVED", approved=True, approver="Research Lead", approval_date="2026-11-13", artifact=artifact, artifact_sha256=sha256_file(tmp_path / artifact))
    record.update(extra)
    _write(tmp_path, record_path, record)


def _authorize_reviews(tmp_path: Path) -> None:
    _sign(tmp_path, PROTOCOL_APPROVAL, SPEC, approved_settings=GATE_SETTINGS)
    _sign(tmp_path, CORPUS_APPROVAL, "evaluation/artifacts/person1/development_evidence_corpus_v1/corpus.json")
    _sign(tmp_path, DEPENDENCY_APPROVAL, DEPENDENCY)


def test_restored_package_is_ready_for_approval_only():
    report = assess(ROOT)
    assert report["status"] == READY_FOR_APPROVAL
    assert report["blockers"] == []
    assert report["empirical_recording_count"] == 0


def test_corpus_hash_conflict_is_blocked(tmp_path: Path):
    _copy_package(tmp_path)
    corpus = json.loads((tmp_path / CORPUS).read_text(encoding="utf-8"))
    corpus["checksum_status"] = "CONFLICTING_PROVENANCE"
    _write(tmp_path, CORPUS, corpus)
    report = assess(tmp_path)
    assert report["status"] == BLOCKED
    assert "corpus file hash conflicts with the preparation report" in report["blockers"]


def test_consistent_package_is_ready_for_approval_only(tmp_path: Path):
    _copy_package(tmp_path)
    report = assess(tmp_path)
    assert report["status"] == READY_FOR_APPROVAL
    assert report["blockers"] == []
    assert report["empirical_recording_count"] == 0


def test_missing_specification_is_blocked(tmp_path: Path):
    report = assess(tmp_path)
    assert report["status"] == BLOCKED
    assert report["blockers"]


def test_invalid_dependency_status_is_blocked(tmp_path: Path):
    _copy_package(tmp_path)
    dependency = json.loads((tmp_path / DEPENDENCY).read_text(encoding="utf-8"))
    dependency["status"] = "EMPIRICAL"
    dependency["empirical_evidence"] = "none"
    _write(tmp_path, DEPENDENCY, dependency)
    report = assess(tmp_path)
    assert report["status"] == BLOCKED
    assert "empirical dependency status lacks recorded evidence" in report["blockers"]


def test_hash_mismatch_is_blocked(tmp_path: Path):
    _copy_package(tmp_path)
    spec = json.loads((tmp_path / SPEC).read_text(encoding="utf-8"))
    spec["eligibility_manifest_sha256"] = "0" * 64
    _write(tmp_path, SPEC, spec)
    report = assess(tmp_path)
    assert report["status"] == BLOCKED


def test_approved_package_can_wait_for_collection_authorization(tmp_path: Path):
    _copy_package(tmp_path)
    _authorize_reviews(tmp_path)
    assert assess(tmp_path)["status"] == READY_FOR_COLLECTION_AUTHORIZATION


def test_proposal_cannot_be_used_as_an_approval(tmp_path: Path):
    _copy_package(tmp_path)
    proposal = json.loads((tmp_path / SETTINGS_PROPOSAL).read_text(encoding="utf-8"))
    proposal["approved"] = True
    _write(tmp_path, SETTINGS_PROPOSAL, proposal)
    report = assess(tmp_path)
    assert report["status"] == BLOCKED
    assert "proposal cannot be used as an approval" in report["blockers"]


def test_wrong_approval_hash_is_blocked(tmp_path: Path):
    _copy_package(tmp_path)
    record = json.loads((tmp_path / PROTOCOL_APPROVAL).read_text(encoding="utf-8"))
    record["artifact_sha256"] = "0" * 64
    _write(tmp_path, PROTOCOL_APPROVAL, record)
    assert assess(tmp_path)["status"] == BLOCKED


def test_missing_approval_record_is_blocked(tmp_path: Path):
    _copy_package(tmp_path)
    (tmp_path / PROTOCOL_APPROVAL).unlink()
    assert assess(tmp_path)["status"] == BLOCKED


def test_corpus_freeze_requires_a_signed_record(tmp_path: Path):
    _copy_package(tmp_path)
    corpus = json.loads((tmp_path / CORPUS).read_text(encoding="utf-8"))
    corpus["frozen"] = True
    _write(tmp_path, CORPUS, corpus)
    report = assess(tmp_path)
    assert report["status"] == BLOCKED
    assert "corpus freeze requires a signed approval record" in report["blockers"]


def test_collection_authorization_requires_protocol_and_corpus(tmp_path: Path):
    _copy_package(tmp_path)
    _sign(tmp_path, COLLECTION_AUTHORIZATION, COLLECTION, collection_authorized=True)
    report = assess(tmp_path)
    assert report["status"] == BLOCKED
    assert "collection authorization requires approved protocol and corpus" in report["blockers"]


def test_final_test_approval_path_is_refused(tmp_path: Path):
    _copy_package(tmp_path)
    record = json.loads((tmp_path / PROTOCOL_APPROVAL).read_text(encoding="utf-8"))
    record["artifact"] = "evaluation/datasets/final_test_research_v1_eval_v2/manifest.json"
    _write(tmp_path, PROTOCOL_APPROVAL, record)
    report = assess(tmp_path)
    assert report["status"] == BLOCKED
    assert any("Final Test" in blocker for blocker in report["blockers"])


def test_collection_ready_state_requires_known_hashes(tmp_path: Path):
    _copy_package(tmp_path)
    corpus = json.loads((tmp_path / CORPUS).read_text(encoding="utf-8"))
    collection = json.loads((tmp_path / COLLECTION).read_text(encoding="utf-8"))
    corpus["frozen"] = True
    collection["collection_authorized"] = True
    collection["environment"]["random_seed"] = 20261113
    for row in collection["verifiers"]:
        if row["verifier_name"] == "rule":
            row["rule_version_hash"] = "a" * 64
        else:
            row["model_weight_snapshot_hash"] = "b" * 64
    _write(tmp_path, CORPUS, corpus)
    _write(tmp_path, COLLECTION, collection)
    _authorize_reviews(tmp_path)
    _sign(tmp_path, CORPUS_APPROVAL, "evaluation/artifacts/person1/development_evidence_corpus_v1/corpus.json", freeze_status="FROZEN")
    _sign(tmp_path, COLLECTION_AUTHORIZATION, COLLECTION, collection_authorized=True)
    assert assess(tmp_path)["status"] == READY_FOR_DEVELOPMENT_COLLECTION


def test_synthetic_recordings_do_not_make_the_experiment_empirical(tmp_path: Path):
    _copy_package(tmp_path)
    spec = json.loads((tmp_path / SPEC).read_text(encoding="utf-8"))
    corpus = json.loads((tmp_path / CORPUS).read_text(encoding="utf-8"))
    collection = json.loads((tmp_path / COLLECTION).read_text(encoding="utf-8"))
    reputation = json.loads((tmp_path / REPUTATION).read_text(encoding="utf-8"))
    spec.update(approved=True, approver="Research Lead", approval_date="2026-11-13")
    corpus.update(approved=True, frozen=True, approver="Research Lead", approval_date="2026-11-13")
    collection.update(collection_authorized=True, development_recordings_available=True, empirical_recording_count=10, empirical_recording_label="SYNTHETIC", cost_measurements_available=True, cost_measurement_id="cost-1")
    collection["environment"]["random_seed"] = 1
    for row in collection["verifiers"]:
        if row["verifier_name"] == "rule":
            row["rule_version_hash"] = "a" * 64
        else:
            row["model_weight_snapshot_hash"] = "b" * 64
    reputation.update(observations_count=4, reputation_source="history_attempts")
    _write(tmp_path, SPEC, spec)
    _write(tmp_path, CORPUS, corpus)
    _write(tmp_path, COLLECTION, collection)
    _write(tmp_path, REPUTATION, reputation)
    assert assess(tmp_path)["status"] == BLOCKED


def test_empirical_state_requires_recordings_costs_and_reputation(tmp_path: Path):
    _copy_package(tmp_path)
    corpus = json.loads((tmp_path / CORPUS).read_text(encoding="utf-8"))
    collection = json.loads((tmp_path / COLLECTION).read_text(encoding="utf-8"))
    reputation = json.loads((tmp_path / REPUTATION).read_text(encoding="utf-8"))
    corpus["frozen"] = True
    collection.update(collection_authorized=True, empirical_recording_count=3, empirical_recording_label="EMPIRICAL", cost_measurements_available=True, cost_measurement_id="cost-1")
    collection["environment"]["random_seed"] = 1
    for row in collection["verifiers"]:
        if row["verifier_name"] == "rule":
            row["rule_version_hash"] = "a" * 64
        else:
            row["model_weight_snapshot_hash"] = "b" * 64
    reputation.update(observations_count=4, reputation_source="history_attempts")
    _write(tmp_path, CORPUS, corpus)
    _write(tmp_path, COLLECTION, collection)
    _write(tmp_path, REPUTATION, reputation)
    _authorize_reviews(tmp_path)
    _sign(tmp_path, CORPUS_APPROVAL, "evaluation/artifacts/person1/development_evidence_corpus_v1/corpus.json", freeze_status="FROZEN")
    _sign(tmp_path, COLLECTION_AUTHORIZATION, COLLECTION, collection_authorized=True)
    assert assess(tmp_path)["status"] == READY_FOR_EMPIRICAL_EXPERIMENT
    assert assess(tmp_path)["analysis_blockers"]


def test_empirical_analysis_requires_rows_and_an_approved_interval(tmp_path: Path):
    _copy_package(tmp_path)
    spec = json.loads((tmp_path / SPEC).read_text(encoding="utf-8"))
    corpus = json.loads((tmp_path / CORPUS).read_text(encoding="utf-8"))
    collection = json.loads((tmp_path / COLLECTION).read_text(encoding="utf-8"))
    reputation = json.loads((tmp_path / REPUTATION).read_text(encoding="utf-8"))
    spec["empirical_results"]["path"] = "gate/rows.json"
    row = {field: "g1" if field == "related_group_id" else "EMPIRICAL" if field == "evidence_label" else "complete" if field == "execution_status" else "full_minimax" if field == "aggregation_method" else "VERIFIED_CORRECT" if field == "gold_label" else 0 for field in REQUIRED_FIELDS}
    row.update(benchmark="GSM8K", attack_condition="clean", dependency_model="shared_unknown", dependency_scenario="independent_failures", decision="passed", validation_loss=0.2, coverage=1, uncertainty=0, verifier_reports=[], verifier_costs=[], provenance={"configuration_id": "gate"}, configuration_id="gate")
    target = tmp_path / "gate" / "rows.json"
    target.parent.mkdir()
    target.write_text(json.dumps({"rows": [row]}), encoding="utf-8")
    corpus["frozen"] = True
    collection.update(collection_authorized=True, empirical_recording_count=3, empirical_recording_label="EMPIRICAL", cost_measurements_available=True, cost_measurement_id="cost-1")
    collection["environment"]["random_seed"] = 1
    for item in collection["verifiers"]:
        if item["verifier_name"] == "rule":
            item["rule_version_hash"] = "a" * 64
        else:
            item["model_weight_snapshot_hash"] = "b" * 64
    reputation.update(observations_count=4, reputation_source="history_attempts")
    _write(tmp_path, SPEC, spec)
    _write(tmp_path, CORPUS, corpus)
    _write(tmp_path, COLLECTION, collection)
    _write(tmp_path, REPUTATION, reputation)
    _authorize_reviews(tmp_path)
    _sign(tmp_path, CORPUS_APPROVAL, "evaluation/artifacts/person1/development_evidence_corpus_v1/corpus.json", freeze_status="FROZEN")
    _sign(tmp_path, COLLECTION_AUTHORIZATION, COLLECTION, collection_authorized=True)
    assert assess(tmp_path)["status"] == READY_FOR_EMPIRICAL_EXPERIMENT_ANALYSIS
