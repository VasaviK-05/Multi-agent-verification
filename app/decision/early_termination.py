"""Adaptive early-termination rule.

The orchestrator calls ``should_terminate`` after each selected verifier.
A False result means keep running the rest of the selected list. The rule
never stops before the difficulty minimum, and a hard question does not
stop early once that minimum is met.

This is an UNCALIBRATED threshold heuristic. It is not Wald's sequential
probability ratio test. See docs/decision_formulas.md.

Let n be the number of results so far, v_i the pass/reject vote, s_i the
confidence in [0, 1]:

    agreement = all votes equal
    avg_confidence = mean(s_i)
    margin = abs(mean(s_i * v_i))

Stop only when n >= minimum(difficulty) and the question is not hard and
either the easy rule or the strong-agreement rule holds:

    easy:  agreement and avg_confidence >= 0.75 and margin >= 0.60
    strong: agreement and avg_confidence >= 0.80 and margin >= 0.70

Otherwise continue. Disagreement continues. Low confidence continues.
"""

from __future__ import annotations

from app.analysis.question_analyzer import QuestionAnalysis
from app.models.schemas import VerificationResult

# UNCALIBRATED. These minima match VerifierSelector's default range minima.
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
    """Sequential stopping rule for an already chosen verifier list."""

    def should_terminate(
        self,
        results: list[VerificationResult],
        analysis: QuestionAnalysis,
        min_verifiers: int | None = None,
    ) -> dict:
        """Return {"terminate": bool, "reason": str}.

        ``min_verifiers`` overrides the difficulty minimum. The orchestrator
        passes the selector's minimum so the two cannot drift at runtime.
        """
        n = len(results)
        if n == 0:
            return {"terminate": False, "reason": "no verifier results yet"}

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

        if difficulty == "hard":
            return {
                "terminate": False,
                "reason": "hard question — continue verification",
            }

        votes = [result.passed for result in results]
        scores = [result.score for result in results]
        agreement = len(set(votes)) == 1
        avg_confidence = sum(scores) / n
        signed = [score if passed else -score for score, passed in zip(scores, votes)]
        margin = abs(sum(signed) / n)

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
