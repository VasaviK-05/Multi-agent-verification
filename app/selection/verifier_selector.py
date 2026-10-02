"""Strategic verifier selector.

Chooses a subset of existing verifier instances. This module does not
implement semantic, evidence, rule, or confidence verification, and it
does not call a model.

Utility, with UNCALIBRATED weights, cost/latency estimates, and
suitability hints:

    U(v, d) = R(v, d) - lambda_cost * cost(v) - lambda_latency * latency(v)
    U(v, d, q) = U(v, d) + lambda_suitability * S(v, q)

R(v, d) is the domain reputation in [0, 1] for analysis.domain only.
cost(v) and latency(v) are explicit estimates in [0, 1], not measured
runtimes. S(v, q) is 0 when verification_types is empty, which keeps the
legacy ranking. Otherwise S is the share of unique types mapped to v,
in [0, 1]. Duplicate labels are counted once. An unknown label matches
no verifier and still occupies one share, so a longer list cannot raise
anyone's bonus above that share. At the cold-start reputation 0.5 every
verifier shares the same R, so an empty type list ranks by the cost and
latency estimates.

The type map is a hint, not a proof that the verifier can decide the
question. RuleVerifier covers a few deterministic patterns and abstains
with metadata.rule "unsupported" otherwise. SemanticVerifier abstains
without reference context. ConfidenceVerifier abstains without supplied
judgments. EvidenceVerifier can abstain when retrieval or NLI is not
directional. Those abstentions stay in iter_ranked so the orchestrator
can consult the next candidate.

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
from dataclasses import dataclass
from typing import Mapping

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

# UNCALIBRATED tradeoff weights. lambda_suitability scales a hint in [0, 1].
# It is not a measured accuracy gain.
DEFAULT_LAMBDA_COST = 0.15
DEFAULT_LAMBDA_LATENCY = 0.10
DEFAULT_LAMBDA_SUITABILITY = 0.20

# UNCALIBRATED hints from the analyzer vocabulary to the verifier that
# currently has the closest capability. Not a guarantee of coverage.
DEFAULT_TYPE_SUITABILITY: dict[str, str] = {
    "arithmetic": "rule",
    "logical_rule": "rule",
    "direct_fact": "evidence",
    "evidence_retrieval": "evidence",
    "semantic_comparison": "semantic",
    "consistency": "confidence",
}


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


@dataclass(frozen=True)
class RankingExplanation:
    """One candidate's ranking terms. Building this does not construct a verifier."""

    verifier_name: str
    reputation: float
    resource_penalty: float
    suitability: float
    suitability_contribution: float
    utility: float


def suitability_by_verifier(
    verification_types: list[str] | None,
    mapping: Mapping[str, str],
) -> dict[str, float]:
    """Share of unique verification types mapped to each verifier, in [0, 1].

    An empty list yields an empty mapping, so every suitability contribution
    is 0. Unknown labels, including non-strings, match nobody and remain in
    the denominator. Repeated labels are counted once, in first-seen order.
    """
    if not isinstance(verification_types, list) or not verification_types:
        return {}
    unique: list[str] = []
    seen: set[str] = set()
    for item in verification_types:
        token = item if isinstance(item, str) else f"<{type(item).__name__}:{item!r}>"
        if token in seen:
            continue
        seen.add(token)
        unique.append(token)
    if not unique:
        return {}
    share = 1.0 / len(unique)
    scores: dict[str, float] = {}
    for token in unique:
        verifier_name = mapping.get(token)
        if verifier_name is None:
            continue
        scores[verifier_name] = scores.get(verifier_name, 0.0) + share
    return scores


def _require_unit_weight(name: str, value: object) -> float:
    """Accept a finite weight in [0, 1]. Reject booleans and non-numbers."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a finite number in [0, 1]")
    number = float(value)
    if not math.isfinite(number) or number < 0.0 or number > 1.0:
        raise ValueError(f"{name} must be a finite number in [0, 1]")
    return number


def _copy_type_mapping(mapping: Mapping[str, str] | None) -> dict[str, str]:
    source: Mapping[str, str] = DEFAULT_TYPE_SUITABILITY if mapping is None else mapping
    if not isinstance(source, Mapping):
        raise ValueError("type_mapping must map verification types to verifier names")
    copied: dict[str, str] = {}
    for key, value in source.items():
        if (
            not isinstance(key, str)
            or key.strip() == ""
            or not isinstance(value, str)
            or value.strip() == ""
        ):
            raise ValueError("type_mapping keys and values must be non-empty strings")
        copied[key] = value
    return copied


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
    """Selects verifiers by domain reputation, resource estimates, and type hints."""

    def __init__(
        self,
        reputation_manager: ReputationManager | None = None,
        lambda_cost: float = DEFAULT_LAMBDA_COST,
        lambda_latency: float = DEFAULT_LAMBDA_LATENCY,
        verifier_profiles: dict[str, dict[str, float]] | None = None,
        difficulty_range: dict[str, tuple[int, int]] | None = None,
        verifiers: list[BaseVerifier] | None = None,
        lambda_suitability: float = DEFAULT_LAMBDA_SUITABILITY,
        type_mapping: Mapping[str, str] | None = None,
    ) -> None:
        self._reputation_manager = reputation_manager or ReputationManager()
        self.lambda_cost = lambda_cost
        self.lambda_latency = lambda_latency
        self.lambda_suitability = _require_unit_weight(
            "lambda_suitability",
            lambda_suitability,
        )
        self.type_mapping = _copy_type_mapping(type_mapping)
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
        """Domain utility without a question-type bonus.

        Callers that only have a domain keep the previous ranking term.
        iter_ranked uses ranking_utility, which adds suitability when the
        analysis carries verification types.
        """
        return self._resource_utility(verifier_name, domain)

    def ranking_utility(self, verifier_name: str, analysis: QuestionAnalysis) -> float:
        """Shared utility for injected and default candidates."""
        return self._factors(verifier_name, analysis).utility

    def explain_ranking(self, analysis: QuestionAnalysis) -> list[RankingExplanation]:
        """Return every registered candidate, highest utility first.

        Default verifiers are named here and not constructed. Equal utilities
        keep registration order.
        """
        names = self._candidate_names()
        rows = [self._factors(name, analysis) for name in names]
        order = sorted(range(len(rows)), key=lambda index: rows[index].utility, reverse=True)
        return [rows[index] for index in order]

    def _resource_utility(self, verifier_name: str, domain: str) -> float:
        reputation = self._reputation_manager.get_reputation(verifier_name, domain)
        return reputation - self._resource_penalty(verifier_name)

    def _resource_penalty(self, verifier_name: str) -> float:
        profile = self.verifier_profiles.get(
            verifier_name,
            {"cost": 0.5, "latency": 0.5},
        )
        return (
            self.lambda_cost * float(profile["cost"])
            + self.lambda_latency * float(profile["latency"])
        )

    def _factors(self, verifier_name: str, analysis: QuestionAnalysis) -> RankingExplanation:
        reputation = self._reputation_manager.get_reputation(verifier_name, analysis.domain)
        penalty = self._resource_penalty(verifier_name)
        suitability = suitability_by_verifier(
            analysis.verification_types,
            self.type_mapping,
        ).get(verifier_name, 0.0)
        contribution = self.lambda_suitability * suitability
        return RankingExplanation(
            verifier_name=verifier_name,
            reputation=reputation,
            resource_penalty=penalty,
            suitability=suitability,
            suitability_contribution=contribution,
            utility=reputation - penalty + contribution,
        )

    def _candidate_names(self) -> list[str]:
        if self._injected is not None:
            return [verifier.name for verifier in self._injected]
        return list(DEFAULT_VERIFIER_ORDER)

    def _default_instance(self, name: str) -> BaseVerifier:
        cached = self._cache.get(name)
        if cached is None:
            cached = _build_default_verifier(name)
            self._cache[name] = cached
        return cached

    def iter_ranked(self, analysis: QuestionAnalysis):
        """Yield every candidate, highest utility first.

        Default verifiers are constructed one at a time so a later fallback
        does not load a model until the orchestrator asks for it. Equal
        utilities keep registration order.
        """
        if self._injected is not None:
            indexed = list(enumerate(self._injected))
            indexed.sort(
                key=lambda item: self.ranking_utility(item[1].name, analysis),
                reverse=True,
            )
            for _, verifier in indexed:
                yield verifier
            return

        names = self._candidate_names()
        order = sorted(
            range(len(names)),
            key=lambda index: self.ranking_utility(names[index], analysis),
            reverse=True,
        )
        for index in order:
            yield self._default_instance(names[index])

    def select(self, analysis: QuestionAnalysis) -> list[BaseVerifier]:
        """Return a difficulty-aware subset, highest utility first."""
        count = self.target_count(analysis)
        chosen: list[BaseVerifier] = []
        for verifier in self.iter_ranked(analysis):
            chosen.append(verifier)
            if len(chosen) >= count:
                break
        return chosen
