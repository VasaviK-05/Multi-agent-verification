"""Requirement precedence and validation without modifying analyzer outputs."""

import math

from app.analysis.models import QuestionAnalysis, QuestionResearchContext
from app.analysis.model_assessment import RUBRIC_FIELDS, VERIFICATION_TYPES
from app.selection.models import RequirementInputs


def _labels(value) -> tuple[str, ...]:
    if not isinstance(value, list):
        return () if value is None else (f"<{type(value).__name__}>",)
    return tuple(dict.fromkeys(item if isinstance(item, str) else
                               f"<{type(item).__name__}:{item!r}>" for item in value))


def requirement_inputs(analysis: QuestionAnalysis) -> RequirementInputs:
    legacy = _labels(analysis.verification_types)
    legacy_unrecognized = tuple(label for label in legacy if label not in VERIFICATION_TYPES)
    context = analysis.research_context
    source = "legacy" if context is None else "research_context"
    labels = legacy if context is None else _labels(getattr(context, "verification_requirements", None))
    recognized = tuple(label for label in VERIFICATION_TYPES if label in labels)
    unsupported = tuple(label for label in labels if label not in VERIFICATION_TYPES)
    disagreements = () if context is None or set(labels) == set(legacy) else (
        "research_context requirements differ from legacy verification_types",
    )
    errors = []
    weights = {}
    weight_discrepancies = ()
    if context is not None:
        if not isinstance(context, QuestionResearchContext):
            errors.append("research_context is not QuestionResearchContext")
        else:
            if context.context_version != "question_context_v1":
                errors.append("unsupported context_version")
            if not isinstance(context.verification_requirements, list) or any(
                not isinstance(label, str) or not label.strip() for label in context.verification_requirements
            ):
                errors.append("verification_requirements must be a list of nonblank strings")
            if type(context.requirements_known) is not bool or context.requirements_known != bool(recognized):
                errors.append("requirements_known must match presence of recognized requirements")
            if not all(isinstance(value, str) and value for value in (
                context.scoring_version, context.domain_status, context.analysis_method
            )):
                errors.append("context provenance fields must be nonempty strings")
            raw = context.requirement_weights
            if not isinstance(raw, dict) or any(
                not isinstance(key, str) or isinstance(value, bool) or not isinstance(value, (float, int))
                or not 0 <= value <= 1 or not math.isfinite(value) for key, value in raw.items()
            ):
                errors.append("requirement_weights must be finite numbers in [0, 1]")
            else:
                # Validate the whole finite vector before filtering. The analyzer
                # emits zero entries for absent requirements; those are allowed.
                weight_discrepancies = tuple(
                    (label, float(raw[label])) for label in sorted(raw)
                    if label not in labels and raw[label] > 0
                )
                if weight_discrepancies:
                    errors.append("positive requirement weights assigned to omitted requirements")
                missing_weights = any(label not in raw for label in recognized)
                if missing_weights:
                    errors.append("requirement_weights missing recognized requirements")
                if not weight_discrepancies and not missing_weights:
                    weights = {label: float(raw[label]) for label in recognized}
                    if weights and sum(weights.values()) <= 0:
                        errors.append("recognized requirements must have positive total weight")
            rubric = context.normalized_rubric
            if rubric is not None and (not isinstance(rubric, dict) or set(rubric) != set(RUBRIC_FIELDS)
                or any(isinstance(value, bool) or not isinstance(value, (int, float))
                       or not 0 <= value <= 1 for value in rubric.values())):
                errors.append("normalized_rubric must contain normalized rubric fields or be None")
    else:
        weights = {label: 1.0 for label in recognized}
    # Invalid present context must never silently fall back to legacy hints.
    if errors:
        return RequirementInputs(source, "invalid", recognized, (), False, legacy,
                                 disagreements, unsupported, tuple(errors), legacy_unrecognized,
                                 weight_discrepancies)
    total = sum(weights.values())
    normalized = tuple((label, weights[label] / total) for label in recognized) if total else ()
    return RequirementInputs(source, "known" if recognized else "unknown", recognized,
                             normalized, bool(recognized), legacy, disagreements, unsupported,
                             legacy_unrecognized=legacy_unrecognized)
