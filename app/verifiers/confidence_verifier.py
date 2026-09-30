"""Confidence verifier based on self-consistency."""

from collections import Counter
from typing import Optional

from app.models.schemas import VerificationResult
from app.verifiers.base_verifier import BaseVerifier


class ConfidenceVerifier(BaseVerifier):
    """Estimates confidence from agreement among verification judgments."""

    @property
    def name(self) -> str:
        return "confidence"

    def calculate_confidence(
        self,
        judgments: list[str],
    ) -> tuple[float, str]:
        """Calculate confidence from majority agreement."""

        if not judgments:
            return 0.0, "No judgments were provided."

        normalized = [
            judgment.strip().lower()
            for judgment in judgments
            if judgment.strip()
        ]

        if not normalized:
            return 0.0, "No valid judgments were provided."

        counts = Counter(normalized)

        majority_label, majority_count = counts.most_common(1)[0]

        confidence = majority_count / len(normalized)

        reasoning = (
            f"Majority judgment: {majority_label}. "
            f"Agreement: {majority_count}/{len(normalized)}. "
            f"Confidence: {confidence:.4f}."
        )

        return confidence, reasoning

    def verify(
        self,
        question: str,
        answer: str,
        context: Optional[str] = None,
    ) -> VerificationResult:
        """Estimate confidence from verification judgments.

        For the initial prototype, judgments are supplied through
        the context field as comma-separated values.

        Example:
            "support,support,support,reject,support"
        """

        if not context:
            return VerificationResult(
                verifier_name=self.name,
                score=0.0,
                passed=False,
                reasoning="No verification judgments were provided.",
                metadata={
                    "method": "self_consistency",
                    "judgments": [],
                },
            )

        judgments = [
            judgment.strip().lower()
            for judgment in context.split(",")
            if judgment.strip()
        ]

        if not judgments:
            return VerificationResult(
                verifier_name=self.name,
                score=0.0,
                passed=False,
                reasoning="No valid verification judgments were provided.",
                metadata={
                    "method": "self_consistency",
                    "judgments": [],
                },
            )

        confidence, reasoning = self.calculate_confidence(judgments)

        counts = Counter(judgments)
        majority_label, agreement_count = counts.most_common(1)[0]

        passed = majority_label == "support"

        return VerificationResult(
            verifier_name=self.name,
            score=confidence,
            passed=passed,
            reasoning=reasoning,
            metadata={
                "method": "self_consistency",
                "judgments": judgments,
                "majority_label": majority_label,
                "agreement_count": agreement_count,
                "total_judgments": len(judgments),
            },
        )