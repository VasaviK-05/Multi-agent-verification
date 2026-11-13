"""Derive research readiness from files. This module never grants approval."""

from __future__ import annotations

import json
from pathlib import Path

from app.verifiers.evidence_retriever import default_corpus_path
from app.verifiers.task_compatibility import POPULATION_SUPPORT, POPULATIONS, VERIFIERS
from evaluation.research_readiness.audit import audit_corpus, audit_datasets, audit_final_test_metadata
from evaluation.research_readiness.canonical import CANONICAL_CORPUS, ROOT
from evaluation.research_readiness.v2_authorization import assess_self_custody

CONFIG_DIR = "evaluation/config/research_v1"


def _load(root: Path, relative: str) -> dict:
    return json.loads((root / relative).read_text(encoding="utf-8"))


def _pending(record: dict) -> bool:
    return record.get("approved") is not True and record.get("approver") in {None, ""} and record.get("approval_date") in {None, ""}


def check_research_readiness(root: Path | None = None) -> dict:
    root = root or ROOT
    datasets = audit_datasets(root)
    corpus = audit_corpus(root)
    custody = audit_final_test_metadata(root)
    self_custody_path = root / "evaluation/config/research_v1/final_test_self_custody.json"
    self_record = json.loads(self_custody_path.read_text(encoding="utf-8")) if self_custody_path.is_file() else None
    self_status = assess_self_custody(self_record, metadata=custody)
    dependency = _load(root, "evaluation/config/experiments/experiment3_dependency_configuration.json")
    groups = dependency.get("groups") or []
    one_group_of_all = len(groups) == 1 and set(groups[0].get("members") or []) == set(VERIFIERS)
    env_path = Path(default_corpus_path())
    if not env_path.is_absolute():
        env_path = root / env_path
    env_ok = env_path.is_file() and env_path.resolve() == (root / CANONICAL_CORPUS).resolve()

    packages = {
        name: _load(root, f"{CONFIG_DIR}/{name}")
        for name in (
            "verifier_config.json",
            "resource_config.json",
            "environment_manifest.json",
            "dataset_manifest.json",
            "dataset_eligibility.json",
            "dataset_approval_package.json",
            "evidence_corpus_manifest.json",
            "evidence_corpus_approval_package.json",
            "final_test_custody_manifest.json",
            "final_test_release_authorization_template.json",
            "collection_manifest.json",
            "collection_authorization_package.json",
            "baseline_freeze_package.json",
            "final_test_scoring_package.json",
            "protocol_index.json",
        )
    }
    fabricated = [
        name for name, record in packages.items()
        if record.get("approved") is True or record.get("collection_authorized") is True or record.get("scoring_authorized") is True
    ]

    requirements = {
        "supported_task_populations": {
            "status": "TECHNICALLY_READY",
            "approval": "PENDING",
            "authorization": "NOT_APPLICABLE",
            "matrix_complete": all(population in POPULATION_SUPPORT[verifier] for verifier in VERIFIERS for population in POPULATIONS),
        },
        "verifier_resource_configuration": {
            "status": "INCOMPLETE" if not env_ok or one_group_of_all else "READY_FOR_APPROVAL",
            "approval": "PENDING",
            "authorization": "NOT_AUTHORIZED",
            "canonical_corpus_path_is_file": env_ok,
            "all_verifiers_in_one_failure_group": one_group_of_all,
            "model_weight_hashes": "UNKNOWN",
        },
        "datasets_and_labels": {
            "status": "READY_FOR_APPROVAL" if not datasets["blockers"] else "BLOCKED",
            "approval": "ELIGIBILITY_APPROVED_COLLECTION_NOT_APPROVED",
            "authorization": "NOT_AUTHORIZED",
            "blockers": datasets["blockers"],
        },
        "development_evidence_corpus": {
            "status": "READY_FOR_APPROVAL" if not corpus["blockers"] else "BLOCKED",
            "approval": "PENDING",
            "authorization": "NOT_AUTHORIZED",
            "blockers": corpus["blockers"],
            "hotpotqa_any_chunk_at_or_above_0_78": corpus["hotpotqa_any_chunk_at_or_above_0_78"],
        },
        "final_test_custody": {
            "status": "NOT_AUTHORIZED" if not custody["blockers"] else "BLOCKED",
            "approval": "PENDING",
            "authorization": "NOT_AUTHORIZED",
            "independent_custody": False,
            "independent_custody_state": "CUSTODY_VERIFICATION_PENDING",
            "self_custody": self_status["self_custody"],
            "protocol_approval": self_status["protocol_approval"],
            "signed_evidence": False,
            "protocol_freeze": "PENDING",
            "self_custody_release": self_status["release"],
            "self_custody_scoring": self_status["scoring"],
            "final_test_execution": "NOT_RUN",
            "blockers": custody["blockers"],
        },
        "scientific_protocols": {
            "status": "READY_FOR_APPROVAL",
            "approval": "PENDING",
            "authorization": "NOT_AUTHORIZED",
            "experiments": packages["protocol_index.json"].get("experiments"),
        },
        "collection_and_scoring": {
            "status": "NOT_AUTHORIZED",
            "approval": "PENDING",
            "authorization": "NOT_AUTHORIZED",
            "research_recordings_created": False,
        },
    }
    if fabricated:
        for item in requirements.values():
            item["status"] = "BLOCKED"
            item.setdefault("blockers", []).append("a generated package claims approval or authorization")

    return {
        "overall_status": "BLOCKED" if fabricated or datasets["blockers"] or corpus["blockers"] or custody["blockers"] or one_group_of_all or not env_ok else "READY_FOR_APPROVAL",
        "execution_ready": False,
        "empirically_complete": False,
        "experiment3_status": "READY_FOR_APPROVAL",
        "development_collection_authorized": False,
        "final_test_scoring_authorized": False,
        "packages_do_not_self_approve": not fabricated,
        "requirements": requirements,
        "dataset_audit": datasets,
        "corpus_audit": {
            "corpus_sha256": corpus["corpus_sha256"],
            "hotpotqa_any_chunk_at_or_above_0_78": corpus["hotpotqa_any_chunk_at_or_above_0_78"],
            "hotpotqa_questions": corpus["hotpotqa_questions"],
            "gsm8k_questions": corpus["gsm8k_questions"],
            "retrieval_status_counts": corpus["retrieval_status_counts"],
            "fever_in_canonical_source": corpus["fever_in_canonical_source"],
            "blockers": corpus["blockers"],
        },
        "final_test_metadata": custody,
    }
