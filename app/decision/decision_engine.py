"""Reputation-based game-theoretic decision engine (research prototype).

Verifier reputation p is converted into decision influence with
log-odds weights:

    w = log(p / (1 - p))

p is clamped away from 0 and 1. Aggregation uses existing
VerificationResult fields (score, passed, verifier_name).

This is a simplified reputation-based game-theoretic / weighted-majority
research prototype. It is NOT the final mathematical formulation.
"""

from __future__ import annotations

import math

from app.models.schemas import VerificationResult
from app.reputation.reputation_manager import ReputationManager


class DecisionEngine:
    """Aggregates verifier results into a final validation decision.

    Research prototype: reputation is mapped to log-odds influence and
    combined as a weighted majority. This is inspired by weighted-majority
    / game-theoretic decision literature and is not claimed to be the
    complete final mechanism.

    TODO: Pareto optimization, cost-aware selection inside aggregation,
    and ablation against unweighted majority.
    """

    EPS = 1e-6
    # PROTOTYPE score bands — not benchmarked.
    PASSED_THRESHOLD = 0.55
    FAILED_THRESHOLD = 0.45

    def __init__(
        self,
        reputation_manager: ReputationManager | None = None,
        default_domain: str = "general",
    ) -> None:
        self._reputation_manager = reputation_manager or ReputationManager()
        self._default_domain = default_domain

    def decide(
        self,
        results: list[VerificationResult],
        domain: str | None = None,
    ) -> tuple[str, float]:
        """Return (final_status, final_score) from verifier results.

        Status compatibility:
        passed ≈ VALID, failed ≈ INVALID, uncertain ≈ ambiguous region.
        Optional domain defaults so the existing orchestrator call still works.
        """
        if not results:
            return "unknown", 0.0

        domain = domain or self._default_domain
        weighted_sum = 0.0
        weight_total = 0.0

        for result in results:
            p = self._reputation_manager.get_reputation(result.verifier_name, domain)
            p = max(self.EPS, min(1.0 - self.EPS, p))
            weight = math.log(p / (1.0 - p))
            sign = 1.0 if result.passed else -1.0
            weighted_sum += weight * result.score * sign
            weight_total += abs(weight)

        if weight_total == 0.0:
            # Degenerate case: all reputations ≈ 0.5 so log-odds weights are 0.
            signed = [
                (r.score if r.passed else -r.score) for r in results
            ]
            final_score = sum(signed) / len(signed)
        else:
            final_score = weighted_sum / weight_total

        final_score = round(final_score, 6)

        if final_score > self.PASSED_THRESHOLD:
            status = "passed"
        elif final_score < self.FAILED_THRESHOLD:
            status = "failed"
        else:
            status = "uncertain"

        return status, final_score
