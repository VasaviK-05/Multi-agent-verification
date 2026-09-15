"""Strategic verifier selector.

Chooses a subset of existing verifier *instances*. This module does
not implement semantic, evidence, rule, or confidence verification.

Utility (prototype):

    utility = reputation - lambda_cost * cost - lambda_latency * latency

How many verifiers to run is driven by question difficulty. Lambdas,
cost/latency tables, and count ranges are configurable prototype
parameters, not calibrated research constants.
"""

from __future__ import annotations

from app.analysis.question_analyzer import QuestionAnalysis
from app.reputation.reputation_manager import ReputationManager
from app.verifiers.base_verifier import BaseVerifier
from app.verifiers.confidence_verifier import ConfidenceVerifier
from app.verifiers.evidence_verifier import EvidenceVerifier
from app.verifiers.rule_verifier import RuleVerifier
from app.verifiers.semantic_verifier import SemanticVerifier

# PROTOTYPE: relative cost/latency in [0, 1]. Not measured runtimes.
DEFAULT_VERIFIER_PROFILES: dict[str, dict[str, float]] = {
    "semantic": {"cost": 0.30, "latency": 0.40},
    "evidence": {"cost": 0.80, "latency": 0.90},
    "rule": {"cost": 0.20, "latency": 0.20},
    "confidence": {"cost": 0.40, "latency": 0.30},
}

# PROTOTYPE: (min, max) selected verifiers by difficulty band.
DEFAULT_DIFFICULTY_RANGE: dict[str, tuple[int, int]] = {
    "easy": (1, 2),
    "medium": (2, 3),
    "hard": (3, 4),
}

DEFAULT_LAMBDA_COST = 0.15
DEFAULT_LAMBDA_LATENCY = 0.10


class VerifierSelector:
    """Selects verifiers by domain reputation and approximate resource cost."""

    def __init__(
        self,
        reputation_manager: ReputationManager | None = None,
        lambda_cost: float = DEFAULT_LAMBDA_COST,
        lambda_latency: float = DEFAULT_LAMBDA_LATENCY,
        verifier_profiles: dict[str, dict[str, float]] | None = None,
        difficulty_range: dict[str, tuple[int, int]] | None = None,
    ) -> None:
        self._reputation_manager = reputation_manager or ReputationManager()
        self.lambda_cost = lambda_cost
        self.lambda_latency = lambda_latency
        self.verifier_profiles = verifier_profiles or dict(DEFAULT_VERIFIER_PROFILES)
        self.difficulty_range = difficulty_range or dict(DEFAULT_DIFFICULTY_RANGE)
        self._all_verifiers: list[BaseVerifier] = [
            SemanticVerifier(),
            EvidenceVerifier(),
            RuleVerifier(),
            ConfidenceVerifier(),
        ]

    def _target_count(self, analysis: QuestionAnalysis) -> int:
        difficulty = analysis.difficulty if analysis.difficulty in self.difficulty_range else "medium"
        min_n, max_n = self.difficulty_range[difficulty]
        span = max_n - min_n
        extra = int(span * min(max(analysis.difficulty_score, 0.0), 1.0))
        return min(max(min_n + extra, min_n), max_n)

    def utility(self, verifier_name: str, domain: str) -> float:
        reputation = self._reputation_manager.get_reputation(verifier_name, domain)
        profile = self.verifier_profiles.get(
            verifier_name, {"cost": 0.5, "latency": 0.5}
        )
        return (
            reputation
            - self.lambda_cost * profile["cost"]
            - self.lambda_latency * profile["latency"]
        )

    def select(self, analysis: QuestionAnalysis) -> list[BaseVerifier]:
        """Return a difficulty-aware subset of available verifier instances."""
        scored = sorted(
            self._all_verifiers,
            key=lambda v: self.utility(v.name, analysis.domain),
            reverse=True,
        )
        n = self._target_count(analysis)
        return scored[:n]
