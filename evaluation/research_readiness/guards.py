"""Authorization guards for collection and scoring.

These functions refuse work. They do not grant authorization.
"""

from __future__ import annotations


class ResearchAuthorizationError(PermissionError):
    """A research operation is not authorized."""


def assert_not_final_test(partition: str | None = None, path: str | None = None) -> None:
    text = f"{partition or ''} {path or ''}".replace("\\", "/").lower()
    if "final_test" in text or "final-test" in text:
        raise ResearchAuthorizationError("Final Test access and scoring are not authorized.")


def assert_collection_authorized(record: dict, *, synthetic_fixture: bool = False) -> None:
    """Allow only an explicit synthetic fixture, never a research recording."""
    assert_not_final_test(record.get("partition"), record.get("output_path"))
    if synthetic_fixture:
        if record.get("evidence_label") != "SYNTHETIC":
            raise ResearchAuthorizationError("A synthetic collection must be labeled SYNTHETIC.")
        if record.get("partition") not in {"synthetic", "development_fixture"}:
            raise ResearchAuthorizationError("Synthetic collection cannot use a research partition.")
        return
    if record.get("collection_authorized") is not True or record.get("approved") is not True:
        raise ResearchAuthorizationError("Development and History collection are not authorized.")
    if not record.get("approver") or not record.get("approval_date"):
        raise ResearchAuthorizationError("Collection authorization requires an approver and a date.")


def assert_scoring_authorized(record: dict) -> None:
    assert_not_final_test(record.get("partition"), record.get("manifest"))
    if record.get("scoring_authorized") is not True or record.get("label_release") == "NOT_AUTHORIZED":
        raise ResearchAuthorizationError("Scoring is not authorized.")
    if not record.get("approver") or not record.get("approval_date"):
        raise ResearchAuthorizationError("Scoring authorization requires an approver and a date.")
