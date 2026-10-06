"""Isolated tests for the keyword heuristic. These stay in heuristic mode."""

import pytest

from app.analysis.models import QuestionAnalysis
from app.analysis.question_analyzer import QuestionAnalyzer


def _heuristic() -> QuestionAnalyzer:
    return QuestionAnalyzer(mode="heuristic", environ={})


def test_legacy_positional_construction():
    analysis = QuestionAnalysis("general", "easy", 0.1)
    other = QuestionAnalysis("medical", "hard", 0.8)
    assert analysis.domain == "general"
    assert analysis.difficulty == "easy"
    assert analysis.difficulty_score == 0.1
    assert analysis.subject == ""
    assert analysis.domain_candidates == []
    assert analysis.domain_status == "unknown"
    assert analysis.verification_types == []
    assert analysis.analysis_method == "heuristic"
    assert analysis.fallback_reason is None
    assert analysis.rubric_ratings is None
    analysis.domain_candidates.append("medical")
    analysis.verification_types.append("arithmetic")
    assert other.domain_candidates == []
    assert other.verification_types == []


def test_easy_question_is_easy():
    analysis = _heuristic().analyze("What is 2 + 2?")
    assert analysis.difficulty == "easy"
    assert 0.0 <= analysis.difficulty_score <= 1.0
    assert analysis.domain == "general"


def test_hard_question_scores_higher_than_easy():
    analyzer = _heuristic()
    easy = analyzer.analyze("What is 2 + 2?")
    hard = analyzer.analyze(
        "Compare and analyse clinical treatment protocols for cardiovascular "
        "patients; explain why diagnosis and drug outcomes differ."
    )
    assert easy.difficulty_score < hard.difficulty_score
    assert hard.difficulty == "hard"
    assert hard.domain == "medical"


def test_analysis_fields_are_present():
    analysis = _heuristic().analyze("Explain how a database protocol works.")
    assert analysis.domain in {"general", "medical", "technical"}
    assert analysis.difficulty in {"easy", "medium", "hard"}
    assert isinstance(analysis.difficulty_score, float)
    assert 0.0 <= analysis.difficulty_score <= 1.0


def test_easy_score_matches_the_uncalibrated_formula():
    # 5 whitespace tokens, one "?", no reasoning cue, no domain cue.
    # 0.30 * (5/40) + 0.25 * (1/3) = 0.120833... → 0.12, which is below 0.35.
    analysis = _heuristic().analyze("What is 2 + 2?")
    assert analysis.difficulty_score == 0.12
    assert analysis.difficulty == "easy"
    assert analysis.domain == "general"
    assert analysis.analysis_method == "heuristic"
    assert analysis.fallback_reason is None
    assert analysis.domain_status == "unknown"
    assert analysis.rubric_ratings is None


def test_feature_weights_sum_to_one():
    from app.analysis.question_analyzer import FEATURE_WEIGHTS

    assert abs(sum(FEATURE_WEIGHTS.values()) - 1.0) < 1e-9


def test_tied_domain_cues_fall_back_to_general():
    analysis = _heuristic().analyze("The patient algorithm failed.")
    assert analysis.domain == "general"
    assert analysis.domain_status == "mixed"
    assert analysis.domain_candidates == ["medical", "technical"]
    assert analysis.analysis_method == "heuristic"


def test_simple_plural_matches_a_domain_cue():
    analysis = _heuristic().analyze("The patients showed symptoms.")
    assert analysis.domain == "medical"
    assert analysis.domain_status == "clear"
    assert analysis.domain_candidates == ["medical"]


def test_score_stays_inside_the_unit_interval():
    text = "Why? Explain; analyze and compare and also additionally " * 15
    analysis = _heuristic().analyze(text + "patient disease treatment diagnosis")
    assert 0.0 <= analysis.difficulty_score <= 1.0
    assert analysis.difficulty in {"easy", "medium", "hard"}


@pytest.mark.parametrize("question,hint,score", [
    ("Who wrote Hamlet?", "direct_fact", 0.11),
    ("What is the capital of France?", "direct_fact", 0.13),
    ("What is 2 + 2?", "arithmetic", 0.12),
    ("Calculate -2.5 * 4", "arithmetic", 0.03),
    ("What is the sum of 2 and 3?", "arithmetic", 0.23),
    ("Compute 8 / 2 + 1", "arithmetic", 0.04),
])
def test_conservative_routing_hints_preserve_difficulty(question, hint, score):
    analysis = _heuristic().analyze(question)
    assert analysis.verification_types == [hint]
    assert analysis.difficulty_score == score
    assert analysis.difficulty == "easy"
    assert analysis == _heuristic().analyze(question)


@pytest.mark.parametrize("question", [
    "Who should write my essay?", "Who would have written Hamlet if Shakespeare had not?",
    "What is the best treatment?", "What is the meaning of life?",
    "What is the capital of France and why was it chosen?",
    "Who wrote Hamlet and what should I read next?",
    "Explain why 2 + 2 equals 4.", "What would 2 + 2 mean in this story?",
    "What is it?", "Who are you?",
])
def test_non_lookup_questions_do_not_receive_factual_hints(question):
    assert _heuristic().analyze(question).verification_types == []


@pytest.mark.parametrize("question", [
    "Write a Python function to sort a list.",
    "Please implement a JavaScript function to sort a list.",
    "Debug a Python script that sorts names.",
])
def test_explicit_programming_requests_have_consistent_technical_metadata(question):
    analysis = _heuristic().analyze(question)
    assert analysis.domain == "technical"
    assert analysis.domain_status == "clear"
    assert analysis.domain_candidates == ["technical"]
    if question.startswith("Write"):
        assert analysis.difficulty_score == 0.06


@pytest.mark.parametrize("question", [
    "What is the function of the heart?", "Write a story about a python.",
    "Is Java a good place to visit?", "Write a Python poem.",
])
def test_standalone_programming_words_do_not_change_domain(question):
    assert _heuristic().analyze(question).domain == "general"


def test_mixed_domain_policy_keeps_unique_winner_and_exact_tie():
    winner = _heuristic().analyze("patient treatment algorithm")
    assert (winner.domain, winner.domain_status, winner.domain_candidates) == (
        "medical", "clear", ["medical"])
    tie = _heuristic().analyze("Write a Python function for a patient.")
    assert (tie.domain, tie.domain_status, tie.domain_candidates) == (
        "general", "mixed", ["medical", "technical"])
