"""Evidence verifier — placeholder implementation."""

from typing import Optional

from app.models.schemas import VerificationResult
from app.verifiers.base_verifier import BaseVerifier


class EvidenceVerifier(BaseVerifier):
    """Evidence-based verifier.

    TODO: Implement retrieval / RAG / external evidence search.
    """

    @property
    def name(self) -> str:
        return "evidence"

    def verify(
        self,
        question: str,
        answer: str,
        context: Optional[str] = None,
    ) -> VerificationResult:
        # TODO: Replace with real evidence retrieval and verification
        return VerificationResult(
            verifier_name=self.name,
            score=0.5,
            passed=True,
            reasoning="Placeholder implementation",
        )
