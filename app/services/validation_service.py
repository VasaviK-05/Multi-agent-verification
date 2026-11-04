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
            from app.benchmark.project_adapter import create_verifiers
            from app.selection.capabilities import BUILTIN_CAPABILITIES
            from app.selection.verifier_selector import VerifierSelector

            # Game execution and Phase 2 collection share the reviewed adapter
            # factory, including its explicit relocation proof when configured.
            # Baseline mode keeps its existing lazy default verifier behavior.
            verifiers, _measurement_setup = create_verifiers()
            selector = VerifierSelector(
                verifiers=verifiers,
                capabilities=BUILTIN_CAPABILITIES,
            )

            self._orchestrator = ValidationOrchestrator(
                verifier_selector=selector,
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
