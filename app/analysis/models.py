"""Analyzer output.

Selection reads domain, difficulty, difficulty_score, and verification_types.
Reputation uses domain only. The decision score does not read analyzer metadata.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class QuestionResearchContext:
    """Derived research inputs, not correctness or calibrated probabilities.

    requirements_known means at least one supported requirement was identified,
    not that the assessment is complete. Zero weight does not prove absence of
    an obligation. This flag must not be a complete-coverage stopping condition.
    """

    context_version: str
    verification_requirements: list[str]
    requirement_weights: dict[str, float]
    requirements_known: bool
    normalized_rubric: dict[str, float] | None
    domain_status: str
    analysis_method: str
    scoring_version: str


@dataclass
class QuestionAnalysis:
    """Domain label, difficulty band, and numeric difficulty score in [0, 1].

    ``verification_types`` is an optional suitability hint for verifier ranking.
    subject, domain candidates, rubric ratings, analysis method, and fallback
    reason do not change selection, reputation, or the decision score.
    ``difficulty_score`` is not a probability.
    """

    domain: str
    difficulty: str
    difficulty_score: float = 0.0
    subject: str = ""
    domain_candidates: list[str] = field(default_factory=list)
    domain_status: str = "unknown"
    verification_types: list[str] = field(default_factory=list)
    analysis_method: str = "heuristic"
    fallback_reason: str | None = None
    rubric_ratings: dict[str, int] | None = None
    research_context: QuestionResearchContext | None = None
