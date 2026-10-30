"""Keyword difficulty heuristic.

Scoring matches the previous QuestionAnalyzer.analyze implementation.
Weights and cut-points are UNCALIBRATED. This is not model analysis.
"""

from __future__ import annotations

import re

from app.analysis.models import QuestionAnalysis

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


def difficulty_band(score: float) -> str:
    if score < EASY_MAX:
        return "easy"
    if score < MEDIUM_MAX:
        return "medium"
    return "hard"


def _domain_counts(tokens: set[str]) -> dict[str, int]:
    return {
        name: sum(1 for keyword in keywords if _contains_keyword(tokens, keyword))
        for name, keywords in DOMAIN_KEYWORDS.items()
    }


def _domain(tokens: set[str]) -> str:
    counts = _domain_counts(tokens)
    best_count = max(counts.values(), default=0)
    winners = [name for name, count in counts.items() if count == best_count and count > 0]
    if len(winners) == 1:
        return winners[0]
    return "general"


def _domain_metadata(tokens: set[str]) -> tuple[str, list[str]]:
    """Honest label for the same counts that choose ``domain``.

    A unique specialist winner is clear. A tie is mixed and still reported
    as domain ``general``. No cue hits are unknown, also ``general``.
    """
    counts = _domain_counts(tokens)
    best_count = max(counts.values(), default=0)
    winners = [name for name, count in counts.items() if count == best_count and count > 0]
    if len(winners) == 1:
        return "clear", winners
    if len(winners) > 1:
        return "mixed", winners
    return "unknown", []


def _programming_request(text: str) -> bool:
    """Bounded task phrases, rather than standalone language/function words."""
    return bool(re.match(
        r"(?:please\s+)?(?:write|implement|debug|refactor)\s+(?:a\s+|an\s+)?"
        r"(?:python|javascript|typescript|java|c\+\+)\s+"
        r"(?:function|program|script|class|code)\b", text,
    ))


def _verification_hints(text: str) -> list[str]:
    """Conservative routing cues; these do not judge answer correctness."""
    # Avoid explanation, speculation and advice, even if numbers are present.
    if re.search(r"\b(?:why|how|explain|would|could|should|if|recommend|best)\b", text):
        return []
    number = r"[+-]?(?:\d+(?:\.\d+)?|\.\d+)"
    expression = rf"{number}\s*(?:\+|-|\*\*?|/|×|÷)\s*{number}"
    if re.fullmatch(
        rf"(?:what is\s+|calculate\s+|compute\s+|evaluate\s+)?"
        rf"{expression}(?:\s*(?:\+|-|\*\*?|/|×|÷)\s*{number})*[?.!]*", text,
    ) or re.fullmatch(
        rf"(?:what is\s+)?(?:the\s+)?(?:sum|product|difference) of "
        rf"{number} and {number}[?.!]*", text,
    ):
        return ["arithmetic"]
    if re.fullmatch(
        r"(?:who (?:wrote|authored|invented|discovered|founded)|"
        r"what is the (?:capital|population|birthplace) of)\s+.+[?]?", text,
    ):
        return ["direct_fact"]
    return []


def heuristic_analysis(
    question: str,
    *,
    analysis_method: str = "heuristic",
    fallback_reason: str | None = None,
) -> QuestionAnalysis:
    """Score ``question`` with the original surface-feature formula."""
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
    # Programming cues affect domain routing only, not the legacy score.
    routing_text = " ".join(lowered.split())
    domain_tokens = tokens | {"software"} if _programming_request(routing_text) else tokens
    status, candidates = _domain_metadata(domain_tokens)

    return QuestionAnalysis(
        domain=_domain(domain_tokens),
        difficulty=difficulty_band(score),
        difficulty_score=score,
        subject="",
        domain_candidates=candidates,
        domain_status=status,
        verification_types=_verification_hints(routing_text),
        analysis_method=analysis_method,
        fallback_reason=fallback_reason,
        rubric_ratings=None,
    )
