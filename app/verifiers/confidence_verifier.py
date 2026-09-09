"""Confidence verifier — placeholder implementation."""

from typing import Optional

from app.models.schemas import VerificationResult
from app.verifiers.base_verifier import BaseVerifier


class ConfidenceVerifier(BaseVerifier):
    """Confidence estimation verifier.

    TODO: Implement calibration and confidence estimation logic.
    """

    @property
    def name(self) -> str:
        return "confidence"

    def verify(
        self,
        question: str,
        answer: str,
        context: Optional[str] = None,
    ) -> VerificationResult:
        # TODO: Replace with real confidence estimation
        return VerificationResult(
            verifier_name=self.name,
            score=0.5,
            passed=True,
            reasoning="Placeholder implementation",
        )
