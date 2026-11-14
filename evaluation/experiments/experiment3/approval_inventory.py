"""Experiment 3 approval inventory. It records hashes and never signs a record."""

from __future__ import annotations

import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[3]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from evaluation.data_preparation.final_test_workflow import sha256_file

MANIFEST_RELATIVE = "evaluation/experiments/experiment3/approval_package/manifest.json"

ARTIFACTS = (
    {
        "role": "protocol",
        "path": "evaluation/config/experiments/experiment3_specification.json",
        "version_key": "record_type",
        "dependencies": [
            "evaluation/artifacts/person1/research_v1_exploratory_eligibility_approved_v1/eligibility_manifest.json",
            "evaluation/config/experiments/experiment3_settings_proposal.json",
        ],
    },
    {
        "role": "loss_settings",
        "path": "evaluation/config/experiments/experiment3_settings_proposal.json",
        "version_key": "record_type",
        "dependencies": [],
    },
    {
        "role": "settings_approval_template",
        "path": "evaluation/config/experiments/approvals/experiment3_settings_approval_record.json",
        "version_key": "record_type",
        "dependencies": ["evaluation/config/experiments/experiment3_settings_proposal.json"],
    },
    {
        "role": "protocol_approval_template",
        "path": "evaluation/config/experiments/approvals/experiment3_protocol_approval_record.json",
        "version_key": "record_type",
        "dependencies": ["evaluation/config/experiments/experiment3_specification.json"],
    },
    {
        "role": "resource_configuration",
        "path": "evaluation/experiments/experiment3/approval_package/resource_configuration_proposal.json",
        "version_key": "record_type",
        "dependencies": ["artifacts/research-v1-development-cost-calibration-v1/freeze-manifest.json"],
    },
    {
        "role": "resource_approval_template",
        "path": "evaluation/config/experiments/approvals/experiment3_resource_approval_record.json",
        "version_key": "record_type",
        "dependencies": ["evaluation/experiments/experiment3/approval_package/resource_configuration_proposal.json"],
    },
    {
        "role": "resource_declaration",
        "path": "evaluation/config/research_v1/resource_config.json",
        "version_key": "record_type",
        "dependencies": ["evaluation/artifacts/person1/development_evidence_corpus_v1/corpus.json"],
    },
    {
        "role": "cost_calibration",
        "path": "artifacts/research-v1-development-cost-calibration-v1/calibration.json",
        "version_key": "version",
        "dependencies": ["artifacts/research-v1-development-cost-calibration-v1/measurements.json"],
    },
    {
        "role": "cost_measurements",
        "path": "artifacts/research-v1-development-cost-calibration-v1/measurements.json",
        "version_key": "version",
        "dependencies": [],
    },
    {
        "role": "cost_calibration_provenance",
        "path": "artifacts/research-v1-development-cost-calibration-v1/calibration-provenance.json",
        "version_key": "version",
        "dependencies": ["artifacts/research-v1-development-cost-calibration-v1/measurements.json"],
    },
    {
        "role": "cost_calibration_freeze",
        "path": "artifacts/research-v1-development-cost-calibration-v1/freeze-manifest.json",
        "version_key": "version",
        "dependencies": [
            "artifacts/research-v1-development-cost-calibration-v1/calibration.json",
            "artifacts/research-v1-development-cost-calibration-v1/measurements.json",
            "artifacts/research-v1-development-cost-calibration-v1/calibration-provenance.json",
        ],
    },
    {
        "role": "reputation_configuration",
        "path": "evaluation/experiments/experiment3/approval_package/reputation_initialization_proposal.json",
        "version_key": "record_type",
        "dependencies": ["evaluation/config/experiments/experiment3_reputation_policy_inputs.json"],
    },
    {
        "role": "reputation_approval_template",
        "path": "evaluation/config/experiments/approvals/experiment3_reputation_approval_record.json",
        "version_key": "record_type",
        "dependencies": ["evaluation/experiments/experiment3/approval_package/reputation_initialization_proposal.json"],
    },
    {
        "role": "reputation_inputs",
        "path": "evaluation/config/experiments/experiment3_reputation_policy_inputs.json",
        "version_key": "record_type",
        "dependencies": [],
    },
    {
        "role": "dependency_configuration",
        "path": "evaluation/config/experiments/experiment3_dependency_configuration.json",
        "version_key": "record_type",
        "dependencies": [],
    },
    {
        "role": "dependency_approval_template",
        "path": "evaluation/config/experiments/approvals/experiment3_dependency_approval_record.json",
        "version_key": "record_type",
        "dependencies": ["evaluation/config/experiments/experiment3_dependency_configuration.json"],
    },
    {
        "role": "evidence_corpus",
        "path": "evaluation/artifacts/person1/development_evidence_corpus_v1/corpus.json",
        "version_key": None,
        "dependencies": [],
    },
    {
        "role": "corpus_package",
        "path": "evaluation/config/experiments/experiment3_corpus_approval_package.json",
        "version_key": "record_type",
        "dependencies": ["evaluation/artifacts/person1/development_evidence_corpus_v1/corpus.json"],
    },
    {
        "role": "corpus_approval_template",
        "path": "evaluation/config/experiments/approvals/experiment3_corpus_approval_record.json",
        "version_key": "record_type",
        "dependencies": ["evaluation/artifacts/person1/development_evidence_corpus_v1/corpus.json"],
    },
    {
        "role": "collection_configuration",
        "path": "evaluation/config/experiments/experiment3_collection_configuration.json",
        "version_key": "record_type",
        "dependencies": [
            "evaluation/artifacts/person1/research_v1_exploratory_eligibility_approved_v1/eligibility_manifest.json",
            "evaluation/artifacts/person1/development_evidence_corpus_v1/corpus.json",
        ],
    },
    {
        "role": "collection_authorization_template",
        "path": "evaluation/config/experiments/approvals/experiment3_collection_authorization_record.json",
        "version_key": "record_type",
        "dependencies": ["evaluation/config/experiments/experiment3_collection_configuration.json"],
    },
    {
        "role": "verifier_configuration",
        "path": "evaluation/config/research_v1/verifier_config.json",
        "version_key": "record_type",
        "dependencies": [],
    },
    {
        "role": "runtime_configuration",
        "path": "evaluation/config/research_v1/environment_manifest.json",
        "version_key": "record_type",
        "dependencies": [],
    },
    {
        "role": "development_eligibility",
        "path": "evaluation/artifacts/person1/research_v1_exploratory_eligibility_approved_v1/eligibility_manifest.json",
        "version_key": "eligibility_version",
        "dependencies": [],
    },
)


def _load_json(path: Path):
    if "final_test" in path.as_posix().lower():
        raise RuntimeError(f"refusing a Final Test path: {path.as_posix()}")
    if path.suffix != ".json":
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def preparation_status(role: str, payload) -> str:
    """Map a file to proposed, prepared, or approved without creating a signature."""
    if not isinstance(payload, dict):
        return "prepared"
    if role == "development_eligibility" and payload.get("approved") is True and payload.get("collection_authorized") is False:
        return "approved"
    if role == "cost_calibration_freeze" and payload.get("authorization", {}).get("approver"):
        return "approved"
    if role in {"cost_calibration", "cost_measurements", "cost_calibration_provenance"}:
        return "prepared"
    signed = payload.get("approved") is True and payload.get("approver") and payload.get("approval_date") and payload.get("status") == "APPROVED"
    if signed and role.endswith("_template"):
        return "approved"
    return "proposed"


REQUIRED_SIGNER = {
    "protocol": "research lead",
    "loss_settings": "research lead",
    "settings_approval_template": "research lead",
    "protocol_approval_template": "research lead",
    "resource_configuration": "research lead",
    "resource_approval_template": "research lead",
    "resource_declaration": "research lead",
    "cost_calibration": "none for Experiment 3; the file is a prepared calibration input",
    "cost_measurements": "none for Experiment 3; the file is a prepared calibration input",
    "cost_calibration_provenance": "none for Experiment 3; the file is a prepared calibration input",
    "cost_calibration_freeze": "already signed for the cost-calibration freeze only; not an Experiment 3 protocol signature",
    "reputation_configuration": "research lead",
    "reputation_approval_template": "research lead",
    "reputation_inputs": "research lead",
    "dependency_configuration": "research lead",
    "dependency_approval_template": "research lead",
    "evidence_corpus": "research lead, by signing the corpus approval",
    "corpus_package": "research lead",
    "corpus_approval_template": "research lead",
    "collection_configuration": "research lead, after Person 2 fills verifier hashes, the seed, and the cost measurement id",
    "collection_authorization_template": "research lead",
    "verifier_configuration": "Person 2 supplies weight and rule hashes; the research lead accepts them by signing collection authorization",
    "runtime_configuration": "Person 2 records the runtime; the research lead accepts collection authorization",
    "development_eligibility": "already approved for Development eligibility only; not a collection signature",
}


def inventory(root: Path) -> dict:
    root = Path(root)
    rows = []
    for artifact in ARTIFACTS:
        path = root / artifact["path"]
        if "final_test" in path.as_posix().lower():
            raise RuntimeError(f"refusing a Final Test path: {artifact['path']}")
        if not path.is_file():
            raise FileNotFoundError(artifact["path"])
        payload = _load_json(path)
        version = None if artifact["version_key"] is None or not isinstance(payload, dict) else payload.get(artifact["version_key"])
        rows.append({
            "role": artifact["role"],
            "path": artifact["path"],
            "sha256": sha256_file(path),
            "version": version,
            "dependencies": list(artifact["dependencies"]),
            "preparation_status": preparation_status(artifact["role"], payload),
            "required_signer": REQUIRED_SIGNER[artifact["role"]],
            "approver": payload.get("approver") if isinstance(payload, dict) else None,
            "approved_flag": payload.get("approved") if isinstance(payload, dict) else None,
        })
    return {
        "record_type": "experiment3_approval_package_manifest_v1",
        "status": "PREPARED_FOR_REVIEW",
        "approved": False,
        "approver": None,
        "approval_date": None,
        "signs_nothing": True,
        "collection_authorized": False,
        "artifacts": rows,
    }


def validate_manifest(root: Path, manifest_path: Path | None = None) -> dict:
    """Recompute hashes. A mismatch or a new signature fails closed."""
    root = Path(root)
    path = Path(manifest_path) if manifest_path is not None else root / MANIFEST_RELATIVE
    recorded = json.loads(path.read_text(encoding="utf-8"))
    if recorded.get("approved") is True or recorded.get("collection_authorized") is True or recorded.get("approver"):
        raise ValueError("approval package manifest cannot sign or authorize collection")
    current = inventory(root)
    recorded_rows = {row["path"]: row for row in recorded.get("artifacts") or []}
    current_rows = {row["path"]: row for row in current["artifacts"]}
    if set(recorded_rows) != set(current_rows):
        raise ValueError("approval package artifact list changed")
    mismatches = []
    for relative, row in current_rows.items():
        previous = recorded_rows[relative]
        if previous.get("sha256") != row["sha256"] or previous.get("preparation_status") != row["preparation_status"]:
            mismatches.append(relative)
    if mismatches:
        raise ValueError("approval package hash or status mismatch: " + ", ".join(mismatches))
    return current


def main() -> int:
    root = _ROOT
    payload = inventory(root)
    destination = root / MANIFEST_RELATIVE
    destination.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"artifacts": len(payload["artifacts"]), "approved": payload["approved"], "path": MANIFEST_RELATIVE}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
