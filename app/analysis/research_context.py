"""Deterministic, detached research inputs derived from final analyzer output."""

from app.analysis.models import QuestionAnalysis, QuestionResearchContext
from app.analysis.model_assessment import RUBRIC_FIELDS, VERIFICATION_TYPES

CONTEXT_VERSION = "question_context_v1"
HEURISTIC_SCORING_VERSION = "heuristic_surface_features_v1"
RUBRIC_SCORING_VERSION = "rubric_sum_over_six_v1"


def build_research_context(analysis: QuestionAnalysis) -> QuestionResearchContext:
    """Equal relative demand weights; absent hints mean unknown requirements.

    Canonical order is VERIFICATION_TYPES, independent of legacy hint order.
    requirements_known only reports at least one identified supported label;
    it does not establish completeness. Zero weight does not prove absence of
    an obligation. Do not use the flag as a complete-coverage stopping condition.
    Unknown legacy labels are not research requirements. No legacy field is
    changed. Validated rubric ratings are divided by two, without calibration.
    """
    requirements = [label for label in VERIFICATION_TYPES if label in analysis.verification_types]
    weight = 1.0 / len(requirements) if requirements else 0.0
    rubric = analysis.rubric_ratings
    return QuestionResearchContext(
        context_version=CONTEXT_VERSION,
        verification_requirements=requirements,
        requirement_weights={label: weight if label in requirements else 0.0
                             for label in VERIFICATION_TYPES},
        requirements_known=bool(requirements),
        normalized_rubric=None if rubric is None else {name: rubric[name] / 2 for name in RUBRIC_FIELDS},
        domain_status=analysis.domain_status,
        analysis_method=analysis.analysis_method,
        scoring_version=(RUBRIC_SCORING_VERSION if analysis.analysis_method == "ollama"
                         else HEURISTIC_SCORING_VERSION),
    )
