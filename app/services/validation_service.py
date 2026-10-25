
"""Validation service — application-level entry point for validation."""

from app.models.schemas import ValidationRequest, ValidationResponse
from app.orchestration.validation_orchestrator import (
    ValidationOrchestrator,
    ValidationContext,
)


class ValidationService:
    """Thin service layer wrapping the validation orchestrator."""

    def __init__(
        self, orchestrator: ValidationOrchestrator | None = None
    ) -> None:
        self._orchestrator = orchestrator or ValidationOrchestrator()

    def validate(self, request: ValidationRequest) -> ValidationResponse:
        """Validate an answer against a question."""
        return self._orchestrator.validate(request)

    def get_validation_context(
        self, validation_id: str
    ) -> ValidationContext:
        """Return the internal context for a completed validation."""
        return self._orchestrator.validation_context(validation_id)
