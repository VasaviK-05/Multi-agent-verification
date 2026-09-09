"""Verifier selector — placeholder implementation."""

from app.analysis.question_analyzer import QuestionAnalysis
from app.verifiers.base_verifier import BaseVerifier
from app.verifiers.confidence_verifier import ConfidenceVerifier
from app.verifiers.evidence_verifier import EvidenceVerifier
from app.verifiers.rule_verifier import RuleVerifier
from app.verifiers.semantic_verifier import SemanticVerifier


class VerifierSelector:
    """Selects which verifiers to run for a given question.

    TODO: Implement adaptive verifier selection based on
    domain, difficulty, cost, and reputation.
    """

    def __init__(self) -> None:
        self._all_verifiers: list[BaseVerifier] = [
            SemanticVerifier(),
            EvidenceVerifier(),
            RuleVerifier(),
            ConfidenceVerifier(),
        ]

    def select(self, analysis: QuestionAnalysis) -> list[BaseVerifier]:
        """Return verifiers to run for the given question analysis.

        Scaffold: returns all available verifiers.
        Extend this method for adaptive selection.
        """
        # TODO: Replace with adaptive selection logic
        return self._all_verifiers
