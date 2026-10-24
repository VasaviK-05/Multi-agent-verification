"""Opt-in batch identity validation, with strict JSON duplicate equality."""

import math
from collections.abc import Sequence

from app.models.schemas import VerificationResult
from app.decision.vote_normalization import is_abstention


def _name(value, label):
    # Validation IDs follow orchestration's existing nonblank-string contract.
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a nonblank string")
    return value


def _json_value(value, ancestors=frozenset()):
    """Reject coercions that could conceal normalization-relevant differences."""
    if value is None or type(value) in (str, bool, int):
        return
    if type(value) is float and math.isfinite(value):
        return
    if type(value) is list:
        if id(value) in ancestors:
            raise ValueError("report payload must contain acyclic native JSON values")
        for item in value:
            _json_value(item, ancestors | {id(value)})
        return
    if type(value) is dict and all(type(key) is str for key in value):
        if id(value) in ancestors:
            raise ValueError("report payload must contain acyclic native JSON values")
        for item in value.values():
            _json_value(item, ancestors | {id(value)})
        return
    raise ValueError("report payload must contain finite native JSON values")


def canonical_reports(results, *, team=None, validation_id=None, deduplicate=True):
    """Return detached rows, one effective run ID, and the declared/observed team.

    Full report fields determine equality; dict key order is irrelevant, list
    order and every metadata field matter. No JSON type coercions are allowed.
    """
    from app.game.models import canonical_json

    if isinstance(results, (str, bytes)) or not isinstance(results, Sequence):
        raise TypeError("results must be a sequence of VerificationResult values")
    if validation_id is not None:
        _name(validation_id, "validation_id")
    if team is not None:
        if isinstance(team, (str, bytes)) or not isinstance(team, Sequence):
            raise ValueError("team must be a sequence of verifier names")
        team = tuple(_name(name, "team verifier name") for name in team)
        if len(team) != len(set(team)):
            raise ValueError("team contains duplicate verifier names")
    copied, annotations, legacy = [], set(), False
    for result in results:
        if not isinstance(result, VerificationResult):
            raise TypeError("results must contain VerificationResult values")
        row = result.model_copy(deep=True)
        is_abstention(row)  # The shared normalizer validates names, score, pass/decision.
        if row.reasoning is not None and not isinstance(row.reasoning, str):
            raise ValueError("report reasoning must be a string or None")
        if row.metadata is not None and type(row.metadata) is not dict:
            raise ValueError("report metadata must be a JSON object or None")
        _json_value(row.metadata)  # Validate before Pydantic can serialize/coerce Any values.
        _json_value(row.model_dump(mode="python"))
        if team is not None and row.verifier_name not in team:
            raise ValueError("report verifier is outside the explicitly supplied team")
        metadata = row.metadata or {}
        if "validation_id" in metadata:
            annotated = _name(metadata["validation_id"], "report validation_id")
            annotations.add(annotated)
            if validation_id is not None and annotated != validation_id:
                raise ValueError("report validation_id differs from the supplied validation_id")
        else:
            legacy = True
        copied.append(row)
    if len(annotations) > 1 or (validation_id is None and annotations and legacy):
        raise ValueError("reports have mixed or ambiguous validation identities")
    effective_id = validation_id if validation_id is not None else next(iter(annotations), None)
    checked, seen = [], {}
    for row in copied:
        identity = (effective_id, row.verifier_name)
        payload = canonical_json(row.model_dump(mode="python"))
        if identity in seen:
            if not deduplicate:
                raise ValueError(f"duplicate verifier name {row.verifier_name!r}")
            if payload != seen[identity]:
                raise ValueError(f"conflicting reports for identity {identity!r}")
            continue
        seen[identity] = payload
        checked.append(row)
    names = tuple(sorted(team if team is not None else (row.verifier_name for row in checked)))
    return tuple(sorted(checked, key=lambda row: row.verifier_name)), effective_id, names
