"""Strategic verifier selector.

Chooses a subset of existing verifier instances. This module does not
implement semantic, evidence, rule, or confidence verification.

Utility, with UNCALIBRATED weights and cost/latency estimates:

    U(v, d) = R(v, d) - lambda_cost * cost(v) - lambda_latency * latency(v)

R(v, d) is the domain reputation in [0, 1]. cost(v) and latency(v) are
explicit estimates in [0, 1], not measured runtimes. At the cold-start
reputation 0.5 every verifier shares the same R, so rank follows the
cost and latency estimates.

How many verifiers to run:

    position = where difficulty_score sits inside its band, in [0, 1]
    count = min_n + floor((max_n - min_n) * position + 1/2)

floor(x + 1/2) is half-up for this non-negative value, so both ends of
the configured (min, max) range are reachable. Truncating with int()
never reaches max when max - min == 1 and the score is below 1.

Lambdas, profiles, and ranges are UNCALIBRATED. See docs/decision_formulas.md.
"""

from __future__ import annotations

import math

from app.analysis.question_analyzer import EASY_MAX, MEDIUM_MAX, QuestionAnalysis
from app.reputation.reputation_manager import ReputationManager
from app.verifiers.base_verifier import BaseVerifier

# UNCALIBRATED: relative cost/latency estimates in [0, 1]. Not measured times.
DEFAULT_VERIFIER_PROFILES: dict[str, dict[str, float]] = {
    "semantic": {"cost": 0.30, "latency": 0.40},
    "evidence": {"cost": 0.80, "latency": 0.90},
    "rule": {"cost": 0.20, "latency": 0.20},
    "confidence": {"cost": 0.40, "latency": 0.30},
}

# Registration order is the tie-break when utilities are equal.
DEFAULT_VERIFIER_ORDER = ("semantic", "evidence", "rule", "confidence")

# UNCALIBRATED: (min, max) selected verifiers by difficulty band.
DEFAULT_DIFFICULTY_RANGE: dict[str, tuple[int, int]] = {
    "easy": (1, 2),
    "medium": (2, 3),
    "hard": (3, 4),
}

# UNCALIBRATED tradeoff weights.
DEFAULT_LAMBDA_COST = 0.15
DEFAULT_LAMBDA_LATENCY = 0.10


def band_position(difficulty: str, difficulty_score: float) -> float:
    """Map a score into [0, 1] inside the named difficulty band.

    Easy uses [0, EASY_MAX), medium [EASY_MAX, MEDIUM_MAX), hard
    [MEDIUM_MAX, 1]. Any other label uses the full [0, 1] interval.
    Scores outside the band are clamped, so a hand-built analysis can
    still reach both ends of the verifier-count range.
    """
    score = min(max(difficulty_score, 0.0), 1.0)
    if difficulty == "easy":
        low, high = 0.0, EASY_MAX
    elif difficulty == "hard":
        low, high = MEDIUM_MAX, 1.0
    elif difficulty == "medium":
        low, high = EASY_MAX, MEDIUM_MAX
    else:
        low, high = 0.0, 1.0
    width = high - low
    if width <= 0.0:
        return 0.0
    return min(max((score - low) / width, 0.0), 1.0)


def target_verifier_count(
    difficulty: str,
    difficulty_score: float,
    difficulty_range: dict[str, tuple[int, int]] | None = None,
) -> int:
    """Return how many verifiers the configured range allows for this score."""
    ranges = difficulty_range or DEFAULT_DIFFICULTY_RANGE
    band = difficulty if difficulty in ranges else "medium"
    min_n, max_n = ranges[band]
    if max_n <= min_n:
        return min_n
    span = max_n - min_n
    position = band_position(band, difficulty_score)
    # int(span * position) drops the top of a span-1 range for every score < 1.
    extra = int(math.floor(span * position + 0.5))
    extra = min(max(extra, 0), span)
    return min_n + extra


def _build_default_verifier(name: str) -> BaseVerifier:
    """Construct one default verifier. Imports are local so unused models stay unloaded."""
    if name == "semantic":
        from app.verifiers.semantic_verifier import SemanticVerifier

        return SemanticVerifier()
    if name == "evidence":
        from app.verifiers.evidence_verifier import EvidenceVerifier

        return EvidenceVerifier()
    if name == "rule":
        from app.verifiers.rule_verifier import RuleVerifier

        return RuleVerifier()
    if name == "confidence":
        from app.verifiers.confidence_verifier import ConfidenceVerifier

        return ConfidenceVerifier()
    raise KeyError(f"unknown verifier {name!r}")


class VerifierSelector:
    """Selects verifiers by domain reputation and explicit resource estimates."""

    def __init__(
        self,
        reputation_manager: ReputationManager | None = None,
        lambda_cost: float = DEFAULT_LAMBDA_COST,
        lambda_latency: float = DEFAULT_LAMBDA_LATENCY,
        verifier_profiles: dict[str, dict[str, float]] | None = None,
        difficulty_range: dict[str, tuple[int, int]] | None = None,
        verifiers: list[BaseVerifier] | None = None,
    ) -> None:
        self._reputation_manager = reputation_manager or ReputationManager()
        self.lambda_cost = lambda_cost
        self.lambda_latency = lambda_latency
        self.verifier_profiles = verifier_profiles or {
            name: dict(profile) for name, profile in DEFAULT_VERIFIER_PROFILES.items()
        }
        self.difficulty_range = difficulty_range or dict(DEFAULT_DIFFICULTY_RANGE)
        self._injected = list(verifiers) if verifiers is not None else None
        self._cache: dict[str, BaseVerifier] = {}

    @property
    def reputation_manager(self) -> ReputationManager:
        return self._reputation_manager

    def minimum_count(self, analysis: QuestionAnalysis) -> int:
        """Minimum verifiers for this difficulty. Early stopping must not go below it."""
        band = analysis.difficulty if analysis.difficulty in self.difficulty_range else "medium"
        return self.difficulty_range[band][0]

    def target_count(self, analysis: QuestionAnalysis) -> int:
        return target_verifier_count(
            analysis.difficulty,
            analysis.difficulty_score,
            self.difficulty_range,
        )

    def utility(self, verifier_name: str, domain: str) -> float:
        reputation = self._reputation_manager.get_reputation(verifier_name, domain)
        profile = self.verifier_profiles.get(verifier_name, {"cost": 0.5, "latency": 0.5})
        return (
            reputation
            - self.lambda_cost * float(profile["cost"])
            - self.lambda_latency * float(profile["latency"])
        )

    def _default_instance(self, name: str) -> BaseVerifier:
        cached = self._cache.get(name)
        if cached is None:
            cached = _build_default_verifier(name)
            self._cache[name] = cached
        return cached

    def select(self, analysis: QuestionAnalysis) -> list[BaseVerifier]:
        """Return a difficulty-aware subset, highest utility first.

        Equal utilities keep registration order. Only the chosen default
        verifiers are constructed.
        """
        count = self.target_count(analysis)
        if self._injected is not None:
            ranked = sorted(
                self._injected,
                key=lambda verifier: self.utility(verifier.name, analysis.domain),
                reverse=True,
            )
            return ranked[: min(count, len(ranked))]

        names = sorted(
            DEFAULT_VERIFIER_ORDER,
            key=lambda name: self.utility(name, analysis.domain),
            reverse=True,
        )
        return [self._default_instance(name) for name in names[: min(count, len(names))]]
