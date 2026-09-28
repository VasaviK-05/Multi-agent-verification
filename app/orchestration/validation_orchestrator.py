"""Validation orchestrator — coordinates the validation pipeline."""

from __future__ import annotations

from app.analysis.question_analyzer import QuestionAnalysis, QuestionAnalyzer
from app.decision.decision_engine import DecisionEngine
from app.decision.early_termination import AdaptiveEarlyTermination
from app.models.schemas import ValidationRequest, ValidationResponse, VerificationResult
from app.reputation.reputation_manager import ReputationManager
from app.selection.verifier_selector import VerifierSelector


class ValidationOrchestrator:
    """Runs analyzer → selector → verifiers, with early stopping → decision.

    The selector and the decision engine share one ReputationManager.
    ``analyze().domain`` is the domain both of them use.

    ``validate`` does not update reputation. Call ``record_ground_truth``
    only when an external label arrives later. The final status produced
    here is not that label.
    """

    def __init__(
        self,
        question_analyzer: QuestionAnalyzer | None = None,
        verifier_selector: VerifierSelector | None = None,
        decision_engine: DecisionEngine | None = None,
        reputation_manager: ReputationManager | None = None,
        early_termination: AdaptiveEarlyTermination | None = None,
    ) -> None:
        self._question_analyzer = question_analyzer or QuestionAnalyzer()
        self._early_termination = early_termination or AdaptiveEarlyTermination()
        self._last_analysis: QuestionAnalysis | None = None
        self._verifier_selector, self._decision_engine, self._reputation_manager = (
            self._assemble(verifier_selector, decision_engine, reputation_manager)
        )

    @staticmethod
    def _assemble(
        verifier_selector: VerifierSelector | None,
        decision_engine: DecisionEngine | None,
        reputation_manager: ReputationManager | None,
    ) -> tuple[VerifierSelector, DecisionEngine, ReputationManager]:
        if verifier_selector is None and decision_engine is None:
            shared = reputation_manager or ReputationManager()
            return (
                VerifierSelector(reputation_manager=shared),
                DecisionEngine(reputation_manager=shared),
                shared,
            )

        if verifier_selector is None:
            assert decision_engine is not None
            shared = reputation_manager or decision_engine.reputation_manager
            if (
                reputation_manager is not None
                and decision_engine.reputation_manager is not reputation_manager
            ):
                raise ValueError(
                    "DecisionEngine must use the orchestrator's ReputationManager."
                )
            return (
                VerifierSelector(reputation_manager=shared),
                decision_engine,
                shared,
            )

        if decision_engine is None:
            shared = reputation_manager or verifier_selector.reputation_manager
            if (
                reputation_manager is not None
                and verifier_selector.reputation_manager is not reputation_manager
            ):
                raise ValueError(
                    "VerifierSelector must use the orchestrator's ReputationManager."
                )
            return (
                verifier_selector,
                DecisionEngine(reputation_manager=shared),
                shared,
            )

        if reputation_manager is None:
            if verifier_selector.reputation_manager is not decision_engine.reputation_manager:
                raise ValueError(
                    "VerifierSelector and DecisionEngine must share one ReputationManager."
                )
            return (
                verifier_selector,
                decision_engine,
                verifier_selector.reputation_manager,
            )

        if (
            verifier_selector.reputation_manager is not reputation_manager
            or decision_engine.reputation_manager is not reputation_manager
        ):
            raise ValueError(
                "Injected selector and decision engine must use the orchestrator's ReputationManager."
            )
        return verifier_selector, decision_engine, reputation_manager

    @property
    def reputation_manager(self) -> ReputationManager:
        return self._reputation_manager

    @property
    def verifier_selector(self) -> VerifierSelector:
        return self._verifier_selector

    @property
    def decision_engine(self) -> DecisionEngine:
        return self._decision_engine

    @property
    def last_analysis(self) -> QuestionAnalysis | None:
        return self._last_analysis

    def validate(self, request: ValidationRequest) -> ValidationResponse:
        """Validate one answer. Does not learn from this decision."""
        analysis = self._question_analyzer.analyze(request.question)
        self._last_analysis = analysis
        verifiers = self._verifier_selector.select(analysis)
        minimum = self._verifier_selector.minimum_count(analysis)

        results: list[VerificationResult] = []
        for verifier in verifiers:
            results.append(verifier.verify(request.question, request.answer, request.context))
            stop = self._early_termination.should_terminate(
                results,
                analysis,
                min_verifiers=minimum,
            )
            if stop["terminate"]:
                break

        final_status, final_score = self._decision_engine.decide(
            results,
            domain=analysis.domain,
        )
        return ValidationResponse(
            results=results,
            final_status=final_status,
            final_score=final_score,
        )

    def record_ground_truth(
        self,
        results: list[VerificationResult],
        answer_is_correct: bool,
        domain: str | None = None,
    ) -> None:
        """Update reputation from a label received after validation.

        ``answer_is_correct`` has to be the external label. This method does
        not read ``final_status``. When ``domain`` is omitted, the domain of
        the last ``validate`` call is used.
        """
        if domain is None:
            if self._last_analysis is None:
                raise ValueError("domain is required before validate() has been run")
            domain = self._last_analysis.domain
        for result in results:
            self._reputation_manager.update_from_ground_truth(
                result.verifier_name,
                domain,
                result.passed,
                answer_is_correct,
            )
