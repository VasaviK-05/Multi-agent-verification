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
