"""Semantic similarity verifier."""

from typing import Optional

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

from app.models.schemas import VerificationResult
from app.verifiers.base_verifier import BaseVerifier


class SemanticVerifier(BaseVerifier):
    """Checks semantic similarity between an answer and reference context."""

    SIMILARITY_THRESHOLD = 0.5

    def __init__(self) -> None:
        self.model = SentenceTransformer("all-MiniLM-L6-v2")

    @property
    def name(self) -> str:
        return "semantic"

    def verify(
        self,
        question: str,
        answer: str,
        context: Optional[str] = None,
    ) -> VerificationResult:

        if not context:
            return VerificationResult(
                verifier_name=self.name,
                score=0.0,
                passed=False,
                reasoning="No reference context provided for semantic comparison.",
            )
        comparison_text = f"{question} {answer}"

        answer_embedding = self.model.encode(comparison_text)
        context_embedding = self.model.encode(context)

        score = cosine_similarity(
            [answer_embedding],
            [context_embedding],
        )[0][0]

        passed = score >= self.SIMILARITY_THRESHOLD

        return VerificationResult(
            verifier_name=self.name,
            score=float(score),
            passed=passed,
            reasoning=(
                f"Semantic similarity score: {score:.4f}. "
                f"Threshold: {self.SIMILARITY_THRESHOLD:.2f}."
            ),
        )