"""Validation orchestrator — coordinates the validation pipeline."""

from __future__ import annotations

from app.analysis.question_analyzer import QuestionAnalysis, QuestionAnalyzer
from app.decision.decision_engine import DecisionEngine
from app.decision.early_termination import AdaptiveEarlyTermination
from app.decision.vote_normalization import is_abstention, vote_confidence
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
        """Validate one answer. Does not learn from this decision.

        Verifiers are taken in utility order. An abstention, such as an
        unsupported rule, is kept in the response and does not count as a
        vote or an early-stop signal. The next verifier is consulted until
        the difficulty target is filled with informative votes, early
        stopping applies, or no verifier remains.
        """
        analysis = self._question_analyzer.analyze(request.question)
        self._last_analysis = analysis
        minimum = self._verifier_selector.minimum_count(analysis)
        target = self._verifier_selector.target_count(analysis)

        results: list[VerificationResult] = []
        abstained: list[str] = []
        informative = 0
        for verifier in self._verifier_selector.iter_ranked(analysis):
            raw = verifier.verify(request.question, request.answer, request.context)
            if is_abstention(raw):
                abstained.append(raw.verifier_name)
                results.append(_annotate(raw, abstained_before=abstained[:-1], abstention=True))
                continue
            results.append(_annotate(raw, abstained_before=list(abstained), abstention=False))
            informative += 1
            if informative >= minimum:
                stop = self._early_termination.should_terminate(
                    results,
                    analysis,
                    min_verifiers=minimum,
                )
                if stop["terminate"]:
                    break
            if informative >= target:
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
            if is_abstention(result):
                continue
            self._reputation_manager.update_from_ground_truth(
                result.verifier_name,
                domain,
                result.passed,
                answer_is_correct,
            )


def _annotate(
    result: VerificationResult,
    *,
    abstained_before: list[str],
    abstention: bool,
) -> VerificationResult:
    """Attach a visible note about how this result was used. Verifier fields stay."""
    metadata = dict(result.metadata or {})
    if abstention:
        metadata["pipeline_role"] = "abstention"
        metadata["pipeline_note"] = (
            f"{result.verifier_name} abstained ({_abstention_reason(result)}). "
            "This result is not a pass or a reject, and it does not trigger early stopping. "
            "Another verifier is consulted when one is still available."
        )
    else:
        metadata["pipeline_role"] = "vote"
        confidence = vote_confidence(result)
        consulted = ""
        if abstained_before:
            consulted = (
                "Consulted after "
                + ", ".join(abstained_before)
                + " abstained. "
            )
        rule = metadata.get("rule")
        if isinstance(rule, str) and rule != "unsupported":
            scale = (
                f"Supported rule '{rule}' is deterministic, so the decision uses "
                f"confidence {confidence:.0f} rather than the stored score {result.score}."
            )
        else:
            scale = (
                f"The verifier score {result.score} is used as confidence {confidence:.4f} "
                "in this pass/reject vote."
            )
        side = "pass" if result.passed else "reject"
        metadata["pipeline_note"] = f"{consulted}Counted {result.verifier_name} as a {side} vote. {scale}"
    return result.model_copy(update={"metadata": metadata})


def _abstention_reason(result: VerificationResult) -> str:
    metadata = result.metadata or {}
    if metadata.get("rule") == "unsupported":
        return "no supported rule matched the question"
    if result.verifier_name == "semantic":
        return "no reference context"
    if result.verifier_name == "evidence":
        label = metadata.get("nli_label")
        if isinstance(label, str) and label.lower() == "neutral":
            return "retrieved evidence was neutral, not a contradiction"
        return "no evidence was retrieved"
    if result.verifier_name == "confidence":
        return "no verification judgments"
    return "the verifier did not cast a vote"
