"""Validation service — application-level entry point for validation."""

from app.models.schemas import ValidationRequest, ValidationResponse
from app.orchestration.validation_orchestrator import ValidationOrchestrator


class ValidationService:
    """Thin service layer wrapping the validation orchestrator."""

    def __init__(self, orchestrator: ValidationOrchestrator | None = None) -> None:
        self._orchestrator = orchestrator or ValidationOrchestrator()

    def validate(self, request: ValidationRequest) -> ValidationResponse:
        """Validate an answer against a question."""
        return self._orchestrator.validate(request)
