"""Validation for the published, narrowly scoped compound resource transfer.

This is deliberately separate from path relocation: the transfer projects a
frozen full roster to the exact Evidence/Rule roster required by one compound
contract. Any Evidence index relocation still needs its own verified proof.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from app.game.models import content_id
from app.game.resource_provenance import ResourceManifest


TRANSFER_VERSION = "compound_required_resource_transfer_v1"
TRANSFER_SCOPE = ("evidence", "rule")


def project_manifest(manifest, names=TRANSFER_SCOPE):
    manifest = ResourceManifest.model_validate(manifest)
    names = tuple(names)
    if names != TRANSFER_SCOPE:
        raise ValueError("only the published Evidence/Rule transfer scope is supported")
    selected = tuple(v for v in manifest.verifiers if v.verifier_name in names)
    if {v.verifier_name for v in selected} != set(names):
        raise ValueError("full resource manifest lacks the required Evidence/Rule entries")
    return ResourceManifest(verifiers=selected)


def validate_compound_transfer(transfer, policy, *, repository_root=None):
    """Validate the published transfer against an unchanged empirical policy."""
    if not isinstance(transfer, dict):
        raise ValueError("scoped resource transfer must be an object")
    transfer = dict(transfer)
    transfer_id = transfer.pop("transfer_id", None)
    if not isinstance(transfer_id, str) or transfer_id != content_id(transfer):
        raise ValueError("scoped resource transfer digest differs")
    transfer["transfer_id"] = transfer_id
    if transfer.get("version") != TRANSFER_VERSION:
        raise ValueError("unsupported scoped resource transfer version")
    if tuple(transfer.get("scope", ())) != TRANSFER_SCOPE:
        raise ValueError("scoped transfer must authorize exactly Evidence and Rule")
    for flag in (
        "required_entries_exactly_equal",
        "policy_bytes_unchanged",
        "decision_semantics_unchanged",
        "no_refit",
        "network_forbidden",
    ):
        if transfer.get(flag) is not True:
            raise ValueError("scoped transfer lacks required assertion: " + flag)

    contract = policy.contract
    full = contract.actual_resources
    if (
        contract.binding_version != "fact_plus_sum_binding_v2"
        or full is None
        or contract.component_assignments != (
            ("base_fact", ("evidence",)),
            ("derived_sum", ("rule",)),
        )
    ):
        raise ValueError("scoped transfer applies only to the published V2 Evidence/Rule contract")
    if transfer.get("original_policy_id") != policy.policy_id:
        raise ValueError("scoped transfer names a different component policy")
    if transfer.get("original_full_resource_id") != full.manifest_id:
        raise ValueError("scoped transfer names a different original full resource manifest")

    setup = transfer.get("scoped_setup")
    if not isinstance(setup, dict) or not isinstance(setup.get("resources"), dict):
        raise ValueError("scoped transfer has no typed scoped resource setup")
    scoped = ResourceManifest.model_validate(setup["resources"])
    if transfer.get("scoped_resource_id") != scoped.manifest_id:
        raise ValueError("scoped transfer resource identity differs from its setup")
    if scoped != project_manifest(full):
        raise ValueError("scoped transfer is not the exact Evidence/Rule projection of the policy manifest")

    hashes = transfer.get("code_hashes")
    if not isinstance(hashes, dict) or not hashes:
        raise ValueError("scoped transfer lacks its source-code seal")
    root = Path(repository_root or Path(__file__).resolve().parents[2]).resolve()
    for relative, expected in hashes.items():
        path = Path(relative)
        if path.is_absolute() or ".." in path.parts:
            raise ValueError("scoped transfer source seal contains an unsafe path")
        candidate = (root / path).resolve()
        try:
            candidate.relative_to(root)
        except ValueError as exc:
            raise ValueError("scoped transfer source seal escapes the repository") from exc
        if not candidate.is_file():
            raise ValueError("scoped transfer source file is missing: " + relative)
        actual = hashlib.sha256(candidate.read_bytes()).hexdigest()
        if actual != expected:
            raise ValueError("scoped transfer source seal differs: " + relative)

    return transfer


def authorize_scoped_observation(transfer, expected_full, current_full, observed_scoped,
                                 *, relocation_authorization=None):
    """Validate the exact scoped projection and any separate index relocation."""
    expected_full = ResourceManifest.model_validate(expected_full)
    current_full = ResourceManifest.model_validate(current_full)
    observed_scoped = ResourceManifest.model_validate(observed_scoped)
    transfer_scope = ResourceManifest.model_validate(transfer["scoped_setup"]["resources"])
    if transfer["original_full_resource_id"] != expected_full.manifest_id:
        raise ValueError("scoped transfer does not bind the expected full manifest")
    if transfer_scope != project_manifest(expected_full):
        raise ValueError("scoped transfer projection differs from the expected full manifest")
    if observed_scoped != project_manifest(current_full):
        raise ValueError("observer did not return the exact current Evidence/Rule projection")

    relocation = None
    if current_full != expected_full:
        if not isinstance(relocation_authorization, dict):
            raise ValueError("full resource drift requires its separate verified relocation proof")
        expected_rows = {
            (r.kind, r.resource_id): r.sha256
            for v in expected_full.verifiers for r in v.resources
        }
        current_rows = {
            (r.kind, r.resource_id): r.sha256
            for v in current_full.verifiers for r in v.resources
        }
        changed = {
            key for key in set(expected_rows) | set(current_rows)
            if expected_rows.get(key) != current_rows.get(key)
        }
        if changed != {("index", "evidence-index")}:
            raise ValueError("scoped transfer cannot authorize non-relocation resource differences")
        if (
            relocation_authorization.get("version") != "verified_resource_relocation_v1"
            or relocation_authorization.get("expected_resource_manifest_id") != expected_full.manifest_id
            or relocation_authorization.get("historical_resource_manifest_id") != expected_full.manifest_id
            or relocation_authorization.get("observed_resource_manifest_id") != current_full.manifest_id
            or relocation_authorization.get("authorized_resource_ids") != ["index:evidence-index"]
        ):
            raise ValueError("scoped transfer received an unbound relocation proof")
        relocation = relocation_authorization
    elif relocation_authorization is not None:
        raise ValueError("relocation proof supplied when full manifests are already identical")

    expected_scoped_rows = {
        (r.kind, r.resource_id): r.sha256
        for v in transfer_scope.verifiers for r in v.resources
    }
    observed_scoped_rows = {
        (r.kind, r.resource_id): r.sha256
        for v in observed_scoped.verifiers for r in v.resources
    }
    scoped_changes = {
        key for key in set(expected_scoped_rows) | set(observed_scoped_rows)
        if expected_scoped_rows.get(key) != observed_scoped_rows.get(key)
    }
    if scoped_changes and (
        relocation is None or scoped_changes != {("index", "evidence-index")}
    ):
        raise ValueError("scoped Evidence/Rule resources differ beyond authorized index relocation")

    return {
        "version": transfer["version"],
        "transfer_id": transfer["transfer_id"],
        "original_policy_id": transfer["original_policy_id"],
        "original_full_resource_manifest_id": expected_full.manifest_id,
        "published_scoped_resource_manifest_id": transfer_scope.manifest_id,
        "observed_scoped_resource_manifest_id": observed_scoped.manifest_id,
        "scope": list(TRANSFER_SCOPE),
        "relocation_authorization": relocation,
    }
