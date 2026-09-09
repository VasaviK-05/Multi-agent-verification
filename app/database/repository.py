"""Database repository — placeholder for future PostgreSQL integration.

TODO: Implement real database operations when PostgreSQL is configured.
The scaffold runs entirely in-memory with no database connection.
"""

from typing import Optional

from app.database.models import (
    DomainReputationRecord,
    FeedbackRecord,
    ValidationRecord,
    VerifierOutputRecord,
)


class ValidationRepository:
    """Repository for validation records and related entities."""

    def save_validation(self, record: ValidationRecord) -> None:
        """Persist a validation record. Scaffold: no-op."""
        # TODO: INSERT into validation_records table
        pass

    def get_validation(self, validation_id: str) -> Optional[ValidationRecord]:
        """Retrieve a validation record by ID. Scaffold: returns None."""
        # TODO: SELECT from validation_records table
        return None

    def save_verifier_output(self, output: VerifierOutputRecord) -> None:
        """Persist a verifier output. Scaffold: no-op."""
        # TODO: INSERT into verifier_outputs table
        pass

    def get_reputation(
        self, verifier_name: str, domain: str
    ) -> Optional[DomainReputationRecord]:
        """Retrieve domain reputation. Scaffold: returns None."""
        # TODO: SELECT from domain_reputation table
        return None

    def save_feedback(self, feedback: FeedbackRecord) -> None:
        """Persist feedback. Scaffold: no-op."""
        # TODO: INSERT into feedback table
        pass
