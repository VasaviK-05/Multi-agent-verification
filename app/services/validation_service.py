"""Application-level entry point for validation."""

from app.models.schemas import ValidationRequest, ValidationResponse
from app.orchestration.validation_orchestrator import (
    ValidationOrchestrator,
    ValidationContext,
)
from app.utils.config import settings


class ValidationService:
    """Thin service layer wrapping the validation orchestrator."""

    def __init__(
        self, orchestrator: ValidationOrchestrator | None = None
    ) -> None:
        if orchestrator is not None:
            self._orchestrator = orchestrator
            return

        mode = settings.EXECUTION_MODE
        if mode == "baseline":
            self._orchestrator = ValidationOrchestrator()
        elif mode == "game":
            from app.game.deployment import create_game_runtime

            self._orchestrator = ValidationOrchestrator(
                execution_mode="game",
                game_runtime=create_game_runtime(),
            )
        else:
            raise ValueError(
                "EXECUTION_MODE must be either 'baseline' or 'game'"
            )

    def validate(self, request: ValidationRequest) -> ValidationResponse:
        """Validate an answer against a question."""
        return self._orchestrator.validate(request)

    def get_validation_context(
        self, validation_id: str
    ) -> ValidationContext:
        """Return the internal context for a completed validation."""
        return self._orchestrator.validation_context(validation_id)
