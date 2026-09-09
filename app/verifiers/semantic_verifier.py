"""Semantic verifier — placeholder implementation."""

from typing import Optional

from app.models.schemas import VerificationResult
from app.verifiers.base_verifier import BaseVerifier


class SemanticVerifier(BaseVerifier):
    """Semantic similarity verifier.

    TODO: Implement embeddings / SBERT semantic similarity checks.
    """

    @property
    def name(self) -> str:
        return "semantic"

    def verify(
        self,
        question: str,
        answer: str,
        context: Optional[str] = None,
    ) -> VerificationResult:
        # TODO: Replace with real semantic similarity logic
        return VerificationResult(
            verifier_name=self.name,
            score=0.5,
            passed=True,
            reasoning="Placeholder implementation",
        )
