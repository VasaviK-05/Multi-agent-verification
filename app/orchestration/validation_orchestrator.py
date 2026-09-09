"""Validation orchestrator — coordinates the validation pipeline."""

from app.analysis.question_analyzer import QuestionAnalyzer
from app.decision.decision_engine import DecisionEngine
from app.models.schemas import ValidationRequest, ValidationResponse, VerificationResult
from app.selection.verifier_selector import VerifierSelector


class ValidationOrchestrator:
    """Orchestrates the full validation flow:

    question analyzer → verifier selector → verifier services → decision engine
    """

    def __init__(
        self,
        question_analyzer: QuestionAnalyzer | None = None,
        verifier_selector: VerifierSelector | None = None,
        decision_engine: DecisionEngine | None = None,
    ) -> None:
        self._question_analyzer = question_analyzer or QuestionAnalyzer()
        self._verifier_selector = verifier_selector or VerifierSelector()
        self._decision_engine = decision_engine or DecisionEngine()

    def validate(self, request: ValidationRequest) -> ValidationResponse:
        """Execute the placeholder validation pipeline."""
        # Step 1: Analyze the question
        analysis = self._question_analyzer.analyze(request.question)

        # Step 2: Select verifiers
        verifiers = self._verifier_selector.select(analysis)

        # Step 3: Run selected verifiers
        results: list[VerificationResult] = [
            verifier.verify(request.question, request.answer, request.context)
            for verifier in verifiers
        ]

        # Step 4: Aggregate results via decision engine
        final_status, final_score = self._decision_engine.decide(results)

        return ValidationResponse(
            results=results,
            final_status=final_status,
            final_score=final_score,
        )
