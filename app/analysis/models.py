"""Analyzer output.

Selection reads domain, difficulty, difficulty_score, and verification_types.
Reputation uses domain only. The decision score does not read analyzer metadata.
"""

from __future__ import annotations

from dataclasses import dataclass, field


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
