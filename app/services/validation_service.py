"""Application-level entry point for validation."""

from app.models.schemas import ValidationRequest, ValidationResponse
from app.orchestration.validation_orchestrator import (
    ValidationOrchestrator,
    ValidationContext,
)
from app.utils.config import settings
from app.game.question_routing import QuestionPolicyConfiguration


class ValidationService:
    """Thin service layer wrapping the validation orchestrator."""

    def __init__(
        self,
        orchestrator: ValidationOrchestrator | None = None,
        *,
        persist_execution: bool = False,
    ) -> None:
        self._generation_runtime = None
        self._generation_configuration = None
        if orchestrator is not None:
            self._orchestrator = orchestrator
            return

        mode = settings.EXECUTION_MODE
        if mode == "baseline":
            self._orchestrator = ValidationOrchestrator(
                persist_execution=persist_execution
            )
        elif mode == "game":
            from app.game.deployment import FlexiblePolicyGameRuntime, create_game_runtime
            from app.selection.capabilities import BUILTIN_CAPABILITIES
            from app.selection.verifier_selector import VerifierSelector
            from app.orchestration.validation_orchestrator import _GameInitializationFailure

            try:
                runtime = create_game_runtime()
            except (FileNotFoundError, ValueError) as exc:
                # Do not turn arbitrary constructor/programming/infrastructure
                # failures into fallback. Only known policy-loading failures.
                from pathlib import Path
                policy_paths = [getattr(settings, name) for name in (
                    "GAME_FLEXIBLE_POLICY_PACKAGE_PATH", "GAME_POLICY_BUNDLE_PATH",
                    "GAME_POLICY_ARTIFACT_PATH") if getattr(settings, name)]
                message = str(exc)
                missing = (isinstance(exc, FileNotFoundError) and len(policy_paths) == 1
                    and not Path(policy_paths[0]).expanduser().exists()
                    and message.startswith(("Configured flexible policy package does not exist:",
                        "Configured game policy bundle does not exist:",
                        "Configured game policy artifact does not exist:")))
                incompatible = (type(exc) is ValueError and message in {
                    "frozen policy bundle bytes differ", "policy bundle digest differs",
                    "unsupported policy package"})
                if not (missing or incompatible):
                    raise
                runtime = _GameInitializationFailure({
                    "status": "game_policy_missing" if missing else "game_policy_incompatible",
                    "error_type": type(exc).__name__, "error_message": message,
                    "stage": "policy_initialization"})
            question_analyzer = None
            if isinstance(runtime, FlexiblePolicyGameRuntime):
                self._generation_runtime = runtime
                self._generation_configuration = runtime.get_policy_configuration()
                # Flexible routes construct their own reviewed, route-scoped
                # selector/observer. Keep the orchestrator slot inert so an
                # E/R compound request does not initialize Confidence/Ollama.
                # Its heuristic analysis is metadata only; QuestionPolicyRouter
                # owns category classification and policy lookup.
                from app.analysis.question_analyzer import QuestionAnalyzer
                selector = VerifierSelector(verifiers=[])
                question_analyzer = QuestionAnalyzer(mode="heuristic")
            elif isinstance(runtime, _GameInitializationFailure):
                selector = VerifierSelector(verifiers=[])
                from app.analysis.question_analyzer import QuestionAnalyzer
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
                persist_execution=persist_execution,
            )
        else:
            raise ValueError(
                "EXECUTION_MODE must be either 'baseline' or 'game'"
            )

    def get_generation_policy_configuration(self) -> QuestionPolicyConfiguration | None:
        """Expose only the active Flexible snapshot; never initialize a runtime."""
        from app.services.compound_generation import ConfigurationLoadingError
        if self._generation_runtime is None:
            return None
        if self._generation_configuration is None:
            raise ConfigurationLoadingError("An active reviewed Flexible runtime is required.")
        configuration = self._generation_runtime.get_policy_configuration()
        if configuration is not self._generation_configuration:
            raise ConfigurationLoadingError("Active generation configuration changed.")
        return configuration

    def validate(self, request: ValidationRequest) -> ValidationResponse:
        """Validate an answer against a question."""
        return self._orchestrator.validate(request)

    def get_validation_context(
        self, validation_id: str
    ) -> ValidationContext:
        """Return the internal context for a completed validation."""
        return self._orchestrator.validation_context(validation_id)
