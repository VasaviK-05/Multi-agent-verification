"""Opt-in question-only task rules; legacy QuestionAnalyzer remains unchanged."""
import re
from app.analysis.question_analyzer import QuestionAnalyzer
from app.analysis.research_context import build_research_context

RULE_VERSION='explicit_task_questions_v1'

class TaskQuestionAnalyzer:
    def __init__(self):self.base=QuestionAnalyzer(mode='heuristic',environ={})
    def analyze(self,question):
        analysis=self.base.analyze(question)
        text=question.strip().casefold()
        if re.fullmatch(r'paraphrase this reference: .+',text,re.DOTALL):
            analysis.verification_types=['semantic_comparison']
        elif re.fullmatch(r'what is the (?:currency|area) of [a-z]+\?',text):
            analysis.verification_types=['direct_fact']
        analysis.research_context=build_research_context(analysis)
        analysis.research_context.scoring_version=RULE_VERSION
        return analysis
