"""Adaptive early-termination helper (not wired into the orchestrator).

Returns whether verification *could* stop given current results.
This component does not run verifiers and is not invoked by
validation_orchestrator.py until the team coordinates that change.
"""

from __future__ import annotations

from app.analysis.question_analyzer import QuestionAnalysis
from app.models.schemas import VerificationResult

# PROTOTYPE stopping thresholds — not benchmarked.
MIN_VERIFIERS_BY_DIFFICULTY = {
    "easy": 1,
    "medium": 2,
    "hard": 3,
}
EASY_CONFIDENCE = 0.75
STRONG_CONFIDENCE = 0.80
EASY_MARGIN = 0.60
STRONG_MARGIN = 0.70


class AdaptiveEarlyTermination:
    """Prototype sequential stopping rule for verifier ensembles."""

    def should_terminate(
        self,
        results: list[VerificationResult],
        analysis: QuestionAnalysis,
        min_verifiers: int | None = None,
    ) -> dict:
        """Return {"terminate": bool, "reason": str}."""
        n = len(results)
        difficulty = analysis.difficulty
        required = (
            min_verifiers
            if min_verifiers is not None
            else MIN_VERIFIERS_BY_DIFFICULTY.get(difficulty, 2)
        )

        if n < required:
            return {
                "terminate": False,
                "reason": f"minimum {required} verifier result(s) not yet available",
            }

        verdicts = [r.passed for r in results]
        scores = [r.score for r in results]
        agreement = len(set(verdicts)) == 1
        avg_confidence = sum(scores) / n
        signed = [(s if passed else -s) for s, passed in zip(scores, verdicts)]
        margin = abs(sum(signed) / n)

        if difficulty == "hard":
            return {
                "terminate": False,
                "reason": "hard question — continue verification",
            }

        if (
            difficulty == "easy"
            and agreement
            and avg_confidence >= EASY_CONFIDENCE
            and margin >= EASY_MARGIN
        ):
            return {
                "terminate": True,
                "reason": "easy question with strong agreement and confidence",
            }

        if agreement and avg_confidence >= STRONG_CONFIDENCE and margin >= STRONG_MARGIN:
            return {
                "terminate": True,
                "reason": "strong agreement and confidence margin",
            }

        if not agreement:
            return {
                "terminate": False,
                "reason": "verifier disagreement — continue verification",
            }

        return {
            "terminate": False,
            "reason": "insufficient confidence to stop early",
        }
