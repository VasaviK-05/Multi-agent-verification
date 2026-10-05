"""Reputation-weighted decision score.

This is a weighted vote. It does not solve a game, and the score is not
a probability.

For an informative verifier i, with domain reputation p_i, confidence
s_i in [0, 1], and vote v_i = +1 on pass and -1 on reject:

    w_i = log(p_i / (1 - p_i))     # Bernoulli log likelihood ratio
    mass_i = s_i * v_i             # in [-1, 1]

s_i is not always the raw ``score`` field. A supported rule stores score
0 on failure; that result is still confidence 1 in a reject. An
unsupported rule, a semantic check with no context, evidence with no
directional NLI label, and confidence with no judgments are abstentions
and contribute no mass. See app/decision/vote_normalization.py.

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

Cuts, also UNCALIBRATED, applied to the bounded score before rounding.
The band is symmetric about 0 because a positive score is net pass
evidence and a negative score is net reject evidence. A tie at 0 is
inside the band. The default threshold is 0.55:

    raw >  threshold → passed
    raw < -threshold → failed
    otherwise        → uncertain

The value returned to callers is that raw score rounded to 6 decimals.
Rounding can land on the threshold after the raw score has already
crossed it. Status follows the raw comparison, not the rounded number.

See docs/decision_formulas.md.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Sequence

from app.decision.vote_normalization import is_abstention, signed_mass, vote_confidence
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
    below 0.5. Reputations of 0 and 1 are clamped into ``(eps, 1 - eps)``.
    Non-finite or out-of-range reputations, and an ``eps`` that is not
    strictly inside (0, 0.5), are rejected. ``eps`` must also be large
    enough that ``1 - eps`` is strictly below 1 in floating point. A
    smaller value is a ``ValueError``, not a division by zero.
    """
    if isinstance(reputation, bool) or not isinstance(reputation, (int, float)):
        raise TypeError("reputation must be a finite value in [0, 1]")
    if not math.isfinite(reputation) or reputation < 0.0 or reputation > 1.0:
        raise ValueError("reputation must be a finite value in [0, 1]")
    if isinstance(eps, bool) or not isinstance(eps, (int, float)):
        raise TypeError("eps must be a finite value strictly between 0 and 0.5")
    if not math.isfinite(eps) or eps <= 0.0 or eps >= 0.5:
        raise ValueError("eps must be a finite value strictly between 0 and 0.5")
    upper = 1.0 - float(eps)
    if not math.isfinite(upper) or upper >= 1.0:
        raise ValueError("eps must be large enough that 1 - eps is strictly below 1")
    p = min(max(float(reputation), float(eps)), upper)
    if p == 0.5:
        return 0.0
    return math.log(p / (1.0 - p))


def _require_domain(domain: object) -> str:
    if not isinstance(domain, str) or domain.strip() == "":
        raise ValueError("domain must be a non-blank string")
    return domain


def _require_threshold(threshold: object) -> float:
    if isinstance(threshold, bool) or not isinstance(threshold, (int, float)):
        raise TypeError("threshold must be a finite value strictly between 0 and 1")
    if not math.isfinite(threshold) or threshold <= 0.0 or threshold >= 1.0:
        raise ValueError("threshold must be a finite value strictly between 0 and 1")
    return float(threshold)


@dataclass(frozen=True)
class VoteExplanation:
    """One verifier's detached contribution to a decision.

    ``contribution`` is ``weight * mass`` in log-odds mode and ``mass`` in
    equal-weight mode. An abstention and a zero-weight vote that was ignored
    because another weight was nonzero both contribute 0.
    """

    verifier_name: str
    abstained: bool
    passed: bool
    confidence: float
    reputation: float
    weight: float
    contribution: float


@dataclass(frozen=True)
class DecisionDetail:
    """Immutable explanation of one ``decide`` call.

    ``raw_score`` is the bounded score used for the status cut. ``score``
    is ``raw_score`` rounded to 6 decimals. ``aggregation`` is ``unknown``,
    ``abstentions``, ``log_odds``, or ``equal_weight``.
    """

    domain: str
    status: str
    raw_score: float
    score: float
    threshold: float
    aggregation: str
    votes: tuple[VoteExplanation, ...]


class DecisionEngine:
    """Aggregates verifier votes with domain log-odds weights."""

    def __init__(
        self,
        reputation_manager: ReputationManager | None = None,
        default_domain: str = "general",
        threshold: float = ABSTAIN_ABOVE,
    ) -> None:
        self._reputation_manager = reputation_manager or ReputationManager()
        self._default_domain = _require_domain(default_domain)
        self._threshold = _require_threshold(threshold)

    @property
    def reputation_manager(self) -> ReputationManager:
        return self._reputation_manager

    @property
    def threshold(self) -> float:
        return self._threshold

    def decide(
        self,
        results: list[VerificationResult],
        domain: str | None = None,
    ) -> tuple[str, float]:
        """Return (status, score) for one domain.

        ``score`` is the uncalibrated signed agreement in [-1, 1] described
        in the module docstring, rounded to 6 decimals. It is not a
        probability of correctness. Status is "passed", "failed",
        "uncertain", or "unknown", and it follows the unrounded score.
        """
        detail = self.decide_detailed(results, domain=domain)
        return detail.status, detail.score

    def decide_detailed(
        self,
        results: list[VerificationResult],
        domain: str | None = None,
    ) -> DecisionDetail:
        """Return the same decision as ``decide``, with per-verifier terms.

        Reputation is read once for every supplied verifier. This method
        does not update the manager.
        """
        if domain is None:
            domain_name = self._default_domain
        else:
            domain_name = _require_domain(domain)
        checked = _checked_results(results)
        if not checked:
            return DecisionDetail(
                domain=domain_name,
                status="unknown",
                raw_score=0.0,
                score=0.0,
                threshold=self._threshold,
                aggregation="unknown",
                votes=(),
            )

        statistics = self._reputation_manager.statistics_batch(
            tuple((result.verifier_name, domain_name) for result in checked)
        )
        reputations = {
            stats.verifier_name: round(stats.posterior_mean, 6) for stats in statistics
        }
        prepared: list[tuple[VerificationResult, bool, float, float, float]] = []
        informative: list[tuple[VerificationResult, float, float, float]] = []
        for result in checked:
            abstained = is_abstention(result)
            confidence = vote_confidence(result)
            reputation = reputations[result.verifier_name]
            weight = log_odds_weight(reputation)
            prepared.append((result, abstained, confidence, reputation, weight))
            if abstained:
                continue
            mass = signed_mass(result)
            if mass is None:
                continue
            informative.append((result, mass, reputation, weight))

        if not informative:
            return DecisionDetail(
                domain=domain_name,
                status="uncertain",
                raw_score=0.0,
                score=0.0,
                threshold=self._threshold,
                aggregation="abstentions",
                votes=tuple(
                    VoteExplanation(
                        verifier_name=result.verifier_name,
                        abstained=True,
                        passed=result.passed,
                        confidence=0.0,
                        reputation=reputation,
                        weight=weight,
                        contribution=0.0,
                    )
                    for result, _abstained, _confidence, reputation, weight in prepared
                ),
            )

        absolute_weight = sum(abs(weight) for _result, _mass, _reputation, weight in informative if weight != 0.0)
        if absolute_weight == 0.0:
            aggregation = "equal_weight"
            raw_score = sum(mass for _result, mass, _reputation, _weight in informative) / len(informative)
        else:
            aggregation = "log_odds"
            weighted_sum = sum(
                weight * mass
                for _result, mass, _reputation, weight in informative
                if weight != 0.0
            )
            raw_score = weighted_sum / absolute_weight

        raw_score = min(max(raw_score, SCORE_LOW), SCORE_HIGH)
        status = _status(raw_score, self._threshold)
        contributions = {
            id(result): _contribution(mass, weight, aggregation)
            for result, mass, _reputation, weight in informative
        }
        return DecisionDetail(
            domain=domain_name,
            status=status,
            raw_score=raw_score,
            score=round(raw_score, 6),
            threshold=self._threshold,
            aggregation=aggregation,
            votes=tuple(
                VoteExplanation(
                    verifier_name=result.verifier_name,
                    abstained=abstained,
                    passed=result.passed,
                    confidence=0.0 if abstained else confidence,
                    reputation=reputation,
                    weight=weight,
                    contribution=0.0 if abstained else contributions[id(result)],
                )
                for result, abstained, confidence, reputation, weight in prepared
            ),
        )


def _checked_results(results: Sequence[VerificationResult]) -> tuple[VerificationResult, ...]:
    if isinstance(results, (str, bytes)) or not isinstance(results, Sequence):
        raise TypeError("results must be a sequence of VerificationResult values")
    seen: set[str] = set()
    checked: list[VerificationResult] = []
    for result in results:
        if not isinstance(result, VerificationResult):
            raise TypeError("results must contain VerificationResult values")
        is_abstention(result)
        name = result.verifier_name
        if name in seen:
            raise ValueError(f"duplicate verifier name {name!r}")
        seen.add(name)
        checked.append(result)
    return tuple(checked)


def _contribution(mass: float, weight: float, aggregation: str) -> float:
    if aggregation == "equal_weight":
        return mass
    if weight == 0.0:
        return 0.0
    return weight * mass


def _status(raw_score: float, threshold: float) -> str:
    if raw_score > threshold:
        return "passed"
    if raw_score < -threshold:
        return "failed"
    return "uncertain"
