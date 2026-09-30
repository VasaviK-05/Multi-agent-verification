"""Question difficulty and domain analyzer.

The score is a weighted sum of surface features. Every weight, divisor,
and cut-point below is an UNCALIBRATED prototype constant. They are not
fitted item-response parameters and they are not a published difficulty
model. See docs/decision_formulas.md.
"""

from __future__ import annotations

from dataclasses import dataclass

# UNCALIBRATED: whole-token reasoning cues. A token matches the cue or that
# cue plus a trailing "s". This is not a stemmer.
REASONING_KEYWORDS = frozenset(
    {
        "explain",
        "compare",
        "analyse",
        "analyze",
        "why",
        "how",
        "discuss",
        "evaluate",
        "justify",
    }
)

# UNCALIBRATED: whole-token domain cues. Unknown text, and exact ties, are
# "general". The same trailing-"s" rule used above applies.
DOMAIN_KEYWORDS: dict[str, frozenset[str]] = {
    "medical": frozenset(
        {
            "patient",
            "disease",
            "treatment",
            "diagnosis",
            "symptom",
            "clinical",
            "drug",
        }
    ),
    "technical": frozenset(
        {
            "algorithm",
            "system",
            "database",
            "api",
            "software",
            "network",
            "protocol",
        }
    ),
}

# UNCALIBRATED feature mix and cut-points.
LENGTH_SATURATION_WORDS = 40
CLAUSE_SATURATION = 3.0
REASONING_SATURATION = 2.0
DOMAIN_TERM_SATURATION = 3.0
FEATURE_WEIGHTS = {
    "length": 0.30,
    "clauses": 0.25,
    "reasoning": 0.25,
    "domain_terms": 0.20,
}
# Bands use the rounded score: [0, EASY_MAX) easy, [EASY_MAX, MEDIUM_MAX) medium,
# [MEDIUM_MAX, 1] hard.
EASY_MAX = 0.35
MEDIUM_MAX = 0.65
SCORE_DECIMALS = 2


def _tokenize(text: str) -> set[str]:
    cleaned = text.lower()
    for ch in ",.;:?!()[]{}\"'":
        cleaned = cleaned.replace(ch, " ")
    return set(cleaned.split())


def _contains_keyword(tokens: set[str], keyword: str) -> bool:
    """True when the token is the keyword or a simple plural of it."""
    return keyword in tokens or f"{keyword}s" in tokens


def _difficulty_band(score: float) -> str:
    if score < EASY_MAX:
        return "easy"
    if score < MEDIUM_MAX:
        return "medium"
    return "hard"


def _domain(tokens: set[str]) -> str:
    counts = {
        name: sum(1 for keyword in keywords if _contains_keyword(tokens, keyword))
        for name, keywords in DOMAIN_KEYWORDS.items()
    }
    best_count = max(counts.values(), default=0)
    winners = [name for name, count in counts.items() if count == best_count and count > 0]
    if len(winners) == 1:
        return winners[0]
    return "general"


@dataclass
class QuestionAnalysis:
    """Domain label, difficulty band, and numeric difficulty score in [0, 1]."""

    domain: str
    difficulty: str
    difficulty_score: float = 0.0


class QuestionAnalyzer:
    """Estimates domain and difficulty from interpretable text features.

    difficulty_score is rounded to SCORE_DECIMALS and then cut into the band
    stored on ``difficulty``. The number is a heuristic rank in [0, 1], not a
    probability and not a calibrated difficulty parameter.
    """

    def analyze(self, question: str) -> QuestionAnalysis:
        words = question.split()
        lowered = question.lower()
        tokens = _tokenize(question)

        length_score = min(len(words) / LENGTH_SATURATION_WORDS, 1.0)

        clause_hits = lowered.count("?") + lowered.count(";")
        clause_hits += sum(
            1 for sep in (" and ", " also ", " additionally ") if sep in lowered
        )
        clause_score = min(clause_hits / CLAUSE_SATURATION, 1.0)

        reasoning_hits = sum(
            1 for keyword in REASONING_KEYWORDS if _contains_keyword(tokens, keyword)
        )
        reasoning_score = min(reasoning_hits / REASONING_SATURATION, 1.0)

        term_hits = sum(
            1
            for keywords in DOMAIN_KEYWORDS.values()
            for keyword in keywords
            if _contains_keyword(tokens, keyword)
        )
        domain_score = min(term_hits / DOMAIN_TERM_SATURATION, 1.0)

        raw_score = (
            FEATURE_WEIGHTS["length"] * length_score
            + FEATURE_WEIGHTS["clauses"] * clause_score
            + FEATURE_WEIGHTS["reasoning"] * reasoning_score
            + FEATURE_WEIGHTS["domain_terms"] * domain_score
        )
        score = round(min(max(raw_score, 0.0), 1.0), SCORE_DECIMALS)

        return QuestionAnalysis(
            domain=_domain(tokens),
            difficulty=_difficulty_band(score),
            difficulty_score=score,
        )
