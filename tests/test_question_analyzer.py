"""Isolated tests for QuestionAnalyzer."""

from app.analysis.question_analyzer import QuestionAnalyzer


def test_easy_question_is_easy():
    analysis = QuestionAnalyzer().analyze("What is 2 + 2?")
    assert analysis.difficulty == "easy"
    assert 0.0 <= analysis.difficulty_score <= 1.0
    assert analysis.domain == "general"


def test_hard_question_scores_higher_than_easy():
    analyzer = QuestionAnalyzer()
    easy = analyzer.analyze("What is 2 + 2?")
    hard = analyzer.analyze(
        "Compare and analyse clinical treatment protocols for cardiovascular "
        "patients; explain why diagnosis and drug outcomes differ."
    )
    assert easy.difficulty_score < hard.difficulty_score
    assert hard.difficulty == "hard"
    assert hard.domain == "medical"


def test_analysis_fields_are_present():
    analysis = QuestionAnalyzer().analyze("Explain how a database protocol works.")
    assert analysis.domain in {"general", "medical", "technical"}
    assert analysis.difficulty in {"easy", "medium", "hard"}
    assert isinstance(analysis.difficulty_score, float)
    assert 0.0 <= analysis.difficulty_score <= 1.0


def test_easy_score_matches_the_uncalibrated_formula():
    # 5 whitespace tokens, one "?", no reasoning cue, no domain cue.
    # 0.30 * (5/40) + 0.25 * (1/3) = 0.120833... → 0.12, which is below 0.35.
    analysis = QuestionAnalyzer().analyze("What is 2 + 2?")
    assert analysis.difficulty_score == 0.12
    assert analysis.difficulty == "easy"
    assert analysis.domain == "general"


def test_feature_weights_sum_to_one():
    from app.analysis.question_analyzer import FEATURE_WEIGHTS

    assert abs(sum(FEATURE_WEIGHTS.values()) - 1.0) < 1e-9


def test_tied_domain_cues_fall_back_to_general():
    analysis = QuestionAnalyzer().analyze("The patient algorithm failed.")
    assert analysis.domain == "general"


def test_simple_plural_matches_a_domain_cue():
    analysis = QuestionAnalyzer().analyze("The patients showed symptoms.")
    assert analysis.domain == "medical"


def test_score_stays_inside_the_unit_interval():
    text = "Why? Explain; analyze and compare and also additionally " * 15
    analysis = QuestionAnalyzer().analyze(text + "patient disease treatment diagnosis")
    assert 0.0 <= analysis.difficulty_score <= 1.0
    assert analysis.difficulty in {"easy", "medium", "hard"}
