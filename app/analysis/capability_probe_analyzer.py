"""Opt-in bounded question-only diagnostics. No production routing changes.

Known atomic questions delegate unchanged. Newly recognized Rule wording has a
new question-rule identity. Mixed questions explicitly require a currently
unimplemented component-binding contract, so no team is falsely deemed complete.
"""
import re
from dataclasses import dataclass
from app.analysis.task_analyzer import TaskQuestionAnalyzer
from app.analysis.research_context import build_research_context

VERSION='capability_probe_questions_v1'
COMPONENT_CONTRACT='compound_component_binding_v1'
NUMBER=r'-?\d+(?:\.\d+)?'
DIFFERENCE=re.compile(rf"(?:what is|what's|calculate|compute|evaluate) the difference between {NUMBER} and {NUMBER}[?.]?",re.I)
MIXED=re.compile(rf'what is the (population|area) of ([a-z]+), and what is that (population|area) plus ({NUMBER})(?: square kilometres)?\? give both values\.',re.I)


@dataclass(frozen=True)
class CheckProfile:
    version: str
    category: str
    required_checks: tuple[str,...]
    input_supported: bool | None
    limitation: str


def question_profile(question):
    text=question.strip()
    match=MIXED.fullmatch(text)
    if match and match.group(1).lower()==match.group(3).lower():
        return CheckProfile(VERSION,'fact_then_calculation',('arithmetic','direct_fact'),False,
            'No verified component decomposition, answer binding or arithmetic report for this whole compound input.')
    if DIFFERENCE.fullmatch(text):
        return CheckProfile(VERSION,'binary_word_difference',('arithmetic',),True,
            'Standalone Rule input supported; no fitted policy for this new question-rule version.')
    return CheckProfile(VERSION,'existing_atomic_or_unknown',(),None,
        'Delegate to the unchanged task analyzer; this profile does not certify arbitrary inputs.')


class CapabilityProbeAnalyzer:
    """Explicitly injected only; existing TaskQuestionAnalyzer remains unchanged."""
    def __init__(self):self.base=TaskQuestionAnalyzer()
    def analyze(self,question):
        analysis=self.base.analyze(question);profile=question_profile(question)
        if profile.category=='existing_atomic_or_unknown':return analysis
        analysis.verification_types=list(profile.required_checks)
        analysis.research_context=build_research_context(analysis)
        analysis.research_context.scoring_version=VERSION
        if not profile.input_supported:
            # The requirement validator preserves this explicit unsupported check;
            # enumeration/routing fail closed instead of dropping the calculation.
            analysis.verification_types.append(COMPONENT_CONTRACT)
            analysis.research_context.verification_requirements.append(COMPONENT_CONTRACT)
            analysis.research_context.requirement_weights[COMPONENT_CONTRACT]=0.
        return analysis
