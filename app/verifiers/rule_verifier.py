"""Rule-based verifier — placeholder implementation."""

from typing import Optional

from app.models.schemas import VerificationResult
from app.verifiers.base_verifier import BaseVerifier


class RuleVerifier(BaseVerifier):
    """Rule-based verifier.

    TODO: Implement real rule engine and domain-specific rules.
    """

    @property
    def name(self) -> str:
        return "rule"

    def verify(
        self,
        question: str,
        answer: str,
        context: Optional[str] = None,
    ) -> VerificationResult:
        # TODO: Replace with real rule-based validation logic
        return VerificationResult(
            verifier_name=self.name,
            score=0.5,
            passed=True,
            reasoning="Placeholder implementation",
        )
