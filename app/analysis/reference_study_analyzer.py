"""Opt-in short single-frame reference category, fixed before study outcomes.

The score is a category constant, not an empirical difficulty estimate.
Callers must supply an explicit question allowlist; this does not broaden API scope.
"""
from app.analysis.task_analyzer import TaskQuestionAnalyzer
VERSION='bounded_reference_frames_v1'
def analyze_reference(question):
    if not question.startswith('Paraphrase this reference: '):raise ValueError('unsupported reference grammar')
    result=TaskQuestionAnalyzer().analyze(question)
    result.difficulty='easy';result.difficulty_score=.1
    result.research_context.scoring_version=VERSION
    return result
