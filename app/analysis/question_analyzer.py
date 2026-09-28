"""Question difficulty and domain analyzer.

This is an initial research-prototype heuristic. Feature weights and
difficulty thresholds are not calibrated. They will later be replaced
or fitted using benchmark data.
"""

from __future__ import annotations

from dataclasses import dataclass

# PROTOTYPE: reasoning verbs that typically indicate harder questions.
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

# PROTOTYPE: whole-word domain cues. Unknown domains fall back to "general".
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

# PROTOTYPE feature mix and cut-points — not research-validated.
LENGTH_SATURATION_WORDS = 40
FEATURE_WEIGHTS = {
    "length": 0.30,
    "clauses": 0.25,
    "reasoning": 0.25,
    "domain_terms": 0.20,
}
EASY_MAX = 0.35
MEDIUM_MAX = 0.65


def _tokenize(text: str) -> set[str]:
    cleaned = text.lower()
    for ch in ",.;:?!()[]{}\"'":
        cleaned = cleaned.replace(ch, " ")
    return set(cleaned.split())


@dataclass
class QuestionAnalysis:
    """Result of question analysis."""

    domain: str
    difficulty: str
    difficulty_score: float = 0.0


class QuestionAnalyzer:
    """Estimates domain and difficulty from interpretable text features.

    Prototype only. Do not treat scores as a final research estimator.
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
        clause_score = min(clause_hits / 3.0, 1.0)

        reasoning_hits = sum(1 for kw in REASONING_KEYWORDS if kw in tokens)
        reasoning_score = min(reasoning_hits / 2.0, 1.0)

        term_hits = sum(
            1 for kws in DOMAIN_KEYWORDS.values() for kw in kws if kw in tokens
        )
        domain_score = min(term_hits / 3.0, 1.0)

        score = min(
            FEATURE_WEIGHTS["length"] * length_score
            + FEATURE_WEIGHTS["clauses"] * clause_score
            + FEATURE_WEIGHTS["reasoning"] * reasoning_score
            + FEATURE_WEIGHTS["domain_terms"] * domain_score,
            1.0,
        )
        score = round(score, 2)

        if score < EASY_MAX:
            difficulty = "easy"
        elif score < MEDIUM_MAX:
            difficulty = "medium"
        else:
            difficulty = "hard"

        domain_counts = {
            name: sum(1 for kw in kws if kw in tokens)
            for name, kws in DOMAIN_KEYWORDS.items()
        }
        best_domain = max(domain_counts, key=domain_counts.get)
        domain = best_domain if domain_counts[best_domain] > 0 else "general"

        return QuestionAnalysis(
            domain=domain,
            difficulty=difficulty,
            difficulty_score=score,
        )
