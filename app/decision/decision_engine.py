"""Reputation-weighted decision score.

This is a weighted vote. It does not solve a game, and the score is not
a probability.

For verifier i with domain reputation p_i, confidence s_i in [0, 1], and
vote v_i = +1 on pass and -1 on reject:

    w_i = log(p_i / (1 - p_i))     # Bernoulli log likelihood ratio
    mass_i = s_i * v_i             # in [-1, 1]

p_i is clamped into (EPS, 1 - EPS) so the log is finite.

Log-odds behavior, which the tests lock in:

- p > 0.5 → w > 0 → the vote is followed
- p = 0.5 → w = 0 → the vote is ignored while any other w is nonzero
- p < 0.5 → w < 0 → the vote is inverted

Inversion is what a negative likelihood ratio means: a verifier that is
wrong more often than chance, in this domain, is evidence for the
opposite call. The normalizer uses |w_i|, not w_i. Dividing by the signed
sum would cancel that inversion.

    score = sum_i w_i * mass_i / sum_i |w_i|     when some |w_i| > 0

Cold start, when every consulted reputation has w_i = 0 (the default
prior is 0.5):

    score = sum_i mass_i / n

The score is in [-1, 1]. +1 is a unanimous full-confidence pass after
any inversions. -1 is the same for reject. Values between the UNCALIBRATED
cuts are "uncertain" (abstain). No verifier results yield status "unknown"
and score 0; that 0 is an empty sentinel, not a calibrated chance and not
the same claim as an "uncertain" 0 from cancelling votes.

Cuts, also UNCALIBRATED, applied to the rounded score. The band is
symmetric about 0 because a positive score is net pass evidence and a
negative score is net reject evidence. A tie at 0 is inside the band.

    score >  0.55 → passed
    score < -0.55 → failed
    otherwise     → uncertain

See docs/decision_formulas.md.
"""

from __future__ import annotations

import math

from app.models.schemas import VerificationResult
from app.reputation.reputation_manager import ReputationManager

# Clamp so log(p / (1-p)) stays finite at reputations of 0 or 1.
EPS = 1e-6

# UNCALIBRATED cuts on the signed score in [-1, 1]. Not probabilities.
# Fail uses the negative of this value so a tie at 0 stays uncertain.
ABSTAIN_ABOVE = 0.55

SCORE_LOW = -1.0
SCORE_HIGH = 1.0


def log_odds_weight(reputation: float, eps: float = EPS) -> float:
    """Bernoulli weight of evidence for a reputation in [0, 1].

    Returns 0 at 0.5, a positive weight above 0.5, and a negative weight
    below 0.5. Non-finite input is rejected.
    """
    if not math.isfinite(reputation):
        raise ValueError("reputation must be a finite value in [0, 1]")
    p = min(max(float(reputation), eps), 1.0 - eps)
    if p == 0.5:
        return 0.0
    return math.log(p / (1.0 - p))


def _vote_mass(result: VerificationResult) -> float:
    """Confidence times the pass/reject vote. Pass is +1, reject is -1."""
    vote = 1.0 if result.passed else -1.0
    confidence = min(max(float(result.score), 0.0), 1.0)
    return confidence * vote


class DecisionEngine:
    """Aggregates verifier votes with domain log-odds weights."""

    def __init__(
        self,
        reputation_manager: ReputationManager | None = None,
        default_domain: str = "general",
    ) -> None:
        self._reputation_manager = reputation_manager or ReputationManager()
        self._default_domain = default_domain

    @property
    def reputation_manager(self) -> ReputationManager:
        return self._reputation_manager

    def decide(
        self,
        results: list[VerificationResult],
        domain: str | None = None,
    ) -> tuple[str, float]:
        """Return (status, score) for one domain.

        ``score`` is the uncalibrated signed agreement in [-1, 1] described
        in the module docstring. It is not a probability of correctness.
        Status is "passed", "failed", "uncertain", or "unknown".
        """
        if not results:
            return "unknown", 0.0

        domain_name = domain or self._default_domain
        weighted_sum = 0.0
        absolute_weight = 0.0
        uninformative: list[float] = []

        for result in results:
            reputation = self._reputation_manager.get_reputation(result.verifier_name, domain_name)
            weight = log_odds_weight(reputation)
            mass = _vote_mass(result)
            if weight == 0.0:
                # p = 0.5. Hold the vote for the all-uninformative fallback.
                uninformative.append(mass)
                continue
            weighted_sum += weight * mass
            absolute_weight += abs(weight)

        if absolute_weight == 0.0:
            # Cold start / every reputation is 0.5: equal-weight signed mean.
            final_score = sum(uninformative) / len(uninformative)
        else:
            # |w| in the denominator keeps negative log-odds inverted.
            final_score = weighted_sum / absolute_weight

        final_score = min(max(final_score, SCORE_LOW), SCORE_HIGH)
        final_score = round(final_score, 6)

        if final_score > ABSTAIN_ABOVE:
            status = "passed"
        elif final_score < -ABSTAIN_ABOVE:
            status = "failed"
        else:
            status = "uncertain"

        return status, final_score
