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
            from app.game.deployment import FlexiblePolicyGameRuntime, create_game_runtime
            from app.selection.capabilities import BUILTIN_CAPABILITIES
            from app.selection.verifier_selector import VerifierSelector

            runtime = create_game_runtime()
            question_analyzer = None
            if isinstance(runtime, FlexiblePolicyGameRuntime):
                # Flexible routes construct their own reviewed, route-scoped
                # selector/observer. Keep the orchestrator slot inert so an
                # E/R compound request does not initialize Confidence/Ollama.
                # Its heuristic analysis is metadata only; QuestionPolicyRouter
                # owns category classification and policy lookup.
                from app.analysis.question_analyzer import QuestionAnalyzer
                selector = VerifierSelector(verifiers=[])
                question_analyzer = QuestionAnalyzer(mode="heuristic")
            else:
                from app.benchmark.project_adapter import create_verifiers

                # Existing prototype/single-artifact game behavior continues
                # to inject the active verifier instances for ProjectObserver.
                verifiers, _measurement_setup = create_verifiers()
                selector = VerifierSelector(
                    verifiers=verifiers,
                    capabilities=BUILTIN_CAPABILITIES,
                )

            self._orchestrator = ValidationOrchestrator(
                question_analyzer=question_analyzer,
                verifier_selector=selector,
                execution_mode="game",
                game_runtime=runtime,
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
