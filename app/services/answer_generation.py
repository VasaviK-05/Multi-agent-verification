"""Shared generation dispatch. No persistence, verifier dispatch or activation.

Separate generate-answer then validate requests have no durable server-side
provenance association. Only the combined operation retains provenance in its
existing validation audit; client-supplied provenance is never trusted.
"""
from dataclasses import asdict, dataclass
from typing import TYPE_CHECKING

import llm_service
from app.services.compound_generation import (
    ConfigurationLoadingError, generate_compound_answer,
)
from app.game.question_routing import (
    QuestionPolicyConfiguration, QuestionClassificationError,
    UnsupportedCompoundSyntaxError, classify_generation_question,
)

if TYPE_CHECKING:
    from app.services.validation_service import ValidationService


@dataclass(frozen=True)
class GeneratedAnswer:
    answer: str
    generation_method: str
    provenance: dict | None


def dispatch_generation(question: str, *, validation_service: "ValidationService") -> GeneratedAnswer:
    """Use the active captured registry exactly once; failures never fall back."""
    configuration_error = None
    try:
        configuration = validation_service.get_generation_policy_configuration()
        if configuration is not None and (
            not isinstance(configuration, QuestionPolicyConfiguration) or configuration.allowlist is None
        ):
            raise ConfigurationLoadingError("Active generation configuration is invalid.")
    except ConfigurationLoadingError as exc:
        configuration_error = exc
        configuration = None
    if configuration is None:
        # Reuse routing's finite grammar without loading a registry or resources.
        # A missing registry cannot authorize Compound generation. Ordinary
        # generation still works in baseline/prototype/injected-service modes.
        try:
            kind, _, _ = classify_generation_question(question)
        except QuestionClassificationError:
            kind = "atomic"
        except UnsupportedCompoundSyntaxError:
            kind = "component"
        if kind == "component":
            raise configuration_error or ConfigurationLoadingError(
                "An active reviewed Flexible configuration is required for Compound generation.")
        return GeneratedAnswer(llm_service.generate_answer(question), "llm", None)
    result = generate_compound_answer(question, configuration=configuration)
    if result is None:
        return GeneratedAnswer(llm_service.generate_answer(question), "llm", None)
    provenance = asdict(result)
    provenance.pop("answer")
    provenance.pop("generation_method")
    provenance["descriptor"] = result.descriptor.model_dump(mode="json")
    provenance["source_hashes"] = dict(result.source_hashes)
    return GeneratedAnswer(result.answer, result.generation_method, provenance)
