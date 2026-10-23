"""Selector-owned bounded expectations; never execution certificates."""

from dataclasses import dataclass


@dataclass(frozen=True)
class CapabilityDescriptor:
    expected_capabilities: tuple[str, ...] = ()
    requires_reference: bool = False
    readiness: str = "unknown"
    unavailable_reason: str | None = None
    limitations: tuple[str, ...] = ()

    def __post_init__(self):
        for field in ("expected_capabilities", "limitations"):
            raw = getattr(self, field)
            if not isinstance(raw, (tuple, list)):
                raise ValueError(f"{field} must be a sequence of strings")
            value = tuple(raw)
            if any(not isinstance(item, str) or not item.strip() for item in value):
                raise ValueError(f"{field} must contain nonblank strings")
            object.__setattr__(self, field, tuple(dict.fromkeys(value)))
        if type(self.requires_reference) is not bool:
            raise ValueError("requires_reference must be boolean")
        if self.readiness not in {"ready", "unknown", "unavailable"}:
            raise ValueError("readiness must be ready, unknown, or unavailable")
        if self.readiness == "unavailable" and (
            not isinstance(self.unavailable_reason, str) or not self.unavailable_reason.strip()
        ):
            raise ValueError("unavailable readiness requires a reason")


# Used only for the built-in factory, never inferred from injected names.
BUILTIN_CAPABILITIES = {
    "rule": CapabilityDescriptor(("arithmetic",), limitations=(
        "Only implemented arithmetic patterns; no arbitrary logical_rule capability.",
        "Other deterministic/structural checks do not establish general factual coverage.",
    )),
    "evidence": CapabilityDescriptor(("direct_fact", "evidence_retrieval"), limitations=(
        "Retrieval is limited to the configured evidence corpus and relevance/NLI gates.",
        "Corpus/model readiness and claim coverage are unknown until execution.",
    )),
    "semantic": CapabilityDescriptor(("semantic_comparison",), requires_reference=True,
        limitations=("Reference similarity is not factual correctness.",)),
    "confidence": CapabilityDescriptor(("consistency",), limitations=(
        "Generation/judgment agreement is not factual evidence or independence.",
        "Provider readiness is unknown until execution.",
    )),
}


def prerequisite_status(descriptor: CapabilityDescriptor, context: str | None) -> tuple[str, str | None]:
    if descriptor.readiness == "unavailable":
        return "unavailable", descriptor.unavailable_reason
    if descriptor.requires_reference:
        if not context or not context.strip():
            return "missing_reference", "reference context is absent"
        # This is exactly the existing semantic verifier's label-list rejection.
        from app.verifiers.confidence_verifier import parse_judgment_list
        if parse_judgment_list(context) is not None:
            return "missing_reference", "context contains judgment labels, not reference text"
    return descriptor.readiness, None
