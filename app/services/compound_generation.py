"""Source-known Compound generation; no models, verifier dispatch or persistence.

Only the reviewed package loader supplies registrations. None means non-Compound;
registered Compound failures raise typed errors and must never trigger LLM fallback.
"""
from dataclasses import dataclass
from decimal import Decimal, DecimalException, Inexact, Rounded, localcontext
import hashlib
import json
from pathlib import Path
import re
from typing import Literal

from app.game.component_binding import BindingError, ComponentPlan, _NUMBER
from app.game.component_execution import ComponentPolicy, bind_contract
from app.game.component_sources import (
    Catalog, Descriptor, SourceFact, SourceManifest, VERSION, question_plan,
    source_manifest, validate_source_material,
)
from app.game.question_routing import (
    QuestionPolicyConfiguration, QuestionClassificationError,
    UnsupportedCompoundSyntaxError, classify_generation_question,
)
from scripts.reconciliation import load_bundle

_ARCHIVE = Path(__file__).resolve().parents[2] / "artifacts/compound-study-36-v1/portable-inputs"
_REQUIRED = ("corpus.json", "geonames-countryInfo.txt", "countries.json")


class CompoundGenerationError(ValueError):
    """Safe public message; callers must not expose chained internal exceptions."""


class ConfigurationLoadingError(CompoundGenerationError):
    pass


class UnsupportedRegistrationError(CompoundGenerationError):
    pass


class SourceUnavailableError(CompoundGenerationError):
    pass


class SourceIntegrityError(CompoundGenerationError):
    pass


class FactLookupError(CompoundGenerationError):
    pass


class ArithmeticFailure(CompoundGenerationError):
    pass


class ContractBindingError(CompoundGenerationError):
    pass


@dataclass(frozen=True)
class CompoundGenerationSpec:
    question: str
    policy: ComponentPolicy
    catalog: Catalog
    plan: ComponentPlan


@dataclass(frozen=True)
class CompoundGenerationResult:
    answer: str
    policy_id: str
    contract_id: str
    plan_id: str
    source_manifest_id: str
    descriptor: Descriptor
    source_hashes: tuple[tuple[str, str], ...]
    corpus_record_sha256: str
    source_verified: Literal[True] = True
    arithmetic_validated: Literal[True] = True
    binder_accepted: Literal[True] = True
    generation_method: Literal["source_grounded_deterministic_v1"] = "source_grounded_deterministic_v1"
    source_scope: Literal["approved_frozen_snapshot"] = "approved_frozen_snapshot"


def resolve_registered_compound(
    question: str, *, configuration: QuestionPolicyConfiguration | None = None,
) -> CompoundGenerationSpec | None:
    """Use validation's reviewed registry, never client policy/category hints."""
    if not isinstance(question, str) or not question.strip():
        raise UnsupportedRegistrationError("Unsupported question registration.")
    try:
        if configuration is None:
            configuration, _, _ = load_bundle()
        if not isinstance(configuration, QuestionPolicyConfiguration) or configuration.allowlist is None:
            raise ConfigurationLoadingError("Reviewed generation configuration is unavailable.")
        router = configuration.router()
        kind, signature, resolved = router.resolve(question, None)
        if resolved is None:
            # The existing classifier distinguishes unregistered Compound requests
            # from ordinary questions; do not reproduce its grammar or keywords.
            try:
                classified, _, _ = classify_generation_question(
                    question, None, component_catalog=router.catalog,
                    reference_question_version=configuration.reference_question_version,
                )
            except UnsupportedCompoundSyntaxError as exc:
                raise UnsupportedRegistrationError("Compound question is not registered.") from exc
            except QuestionClassificationError:
                return None
            if classified == "component":
                raise UnsupportedRegistrationError("Compound question is not registered.")
            return None
        if kind != "component":
            return None
        route, _ = resolved
        matches = [p for sig, budget, _, p in router.components
                   if sig == signature and budget == route[1]]
        if configuration.allowlist is None or question not in configuration.allowlist or len(matches) != 1:
            raise UnsupportedRegistrationError("Compound question is not uniquely registered.")
        policy = matches[0]
        if policy.evidence_kind != "empirical" or policy.contract.binding_version != VERSION:
            raise UnsupportedRegistrationError("Compound registration is not supported.")
        catalog = Catalog.model_validate_json(policy.contract.descriptor_catalog_json)
        return CompoundGenerationSpec(question, policy, catalog, question_plan(question, catalog))
    except CompoundGenerationError:
        raise
    except (OSError, ValueError, TypeError, KeyError) as exc:
        raise ConfigurationLoadingError("Reviewed generation configuration could not be verified.") from exc


def _load_sources(catalog: Catalog) -> SourceManifest:
    try:
        manifest = json.loads((_ARCHIVE / "manifest.json").read_bytes())
        entries = manifest["files"]
        if not isinstance(entries, dict) or not set(_REQUIRED).issubset(entries):
            raise SourceIntegrityError("Approved source inventory is incomplete.")
        raw = {}
        for name, identity in entries.items():
            if not isinstance(name, str) or Path(name).name != name:
                raise SourceIntegrityError("Approved source inventory is invalid.")
            data = (_ARCHIVE / name).read_bytes()
            if hashlib.sha256(data).hexdigest() != identity["sha256"] or len(data) != identity["bytes"]:
                raise SourceIntegrityError("Approved source integrity check failed.")
            raw[name] = data
        sources = source_manifest(*(raw[name] for name in _REQUIRED))
        validate_source_material(sources, tuple(
            (str(_ARCHIVE / name), entries[name]["sha256"]) for name in _REQUIRED
        ))
        if sources.manifest_id != catalog.source_manifest_id or sources.catalog != catalog:
            raise SourceIntegrityError("Sources do not match the registered catalog.")
        return sources
    except CompoundGenerationError:
        raise
    except OSError as exc:
        raise SourceUnavailableError("Approved source material is unavailable.") from exc
    except (ValueError, TypeError, KeyError, IndexError, AttributeError) as exc:
        raise SourceIntegrityError("Approved source material could not be verified.") from exc


def _find_fact(spec: CompoundGenerationSpec, sources: SourceManifest) -> SourceFact:
    descriptors = [d for d in spec.catalog.descriptors
                   if d.entity == spec.plan.entity and d.measure == spec.plan.measure]
    if len(descriptors) != 1:
        raise FactLookupError("A unique registered source descriptor is required.")
    facts = [f for f in sources.facts if f.descriptor == descriptors[0]]
    if len(facts) != 1:
        raise FactLookupError("A unique approved source fact is required.")
    return facts[0]


def _plain_decimal(value: Decimal) -> str:
    text = format(value, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    if value == 0:
        text = "0"
    if re.fullmatch(_NUMBER, text) is None:
        raise ArithmeticFailure("Value exceeds the answer contract's decimal bounds.")
    return text


def _derived_value(base: str, increment: str) -> str:
    if any(not isinstance(v, str) or re.fullmatch(_NUMBER, v) is None for v in (base, increment)):
        raise ArithmeticFailure("Bounded decimal operands are required.")
    try:
        with localcontext() as context:
            # Binder operands have at most 21 digits; this also ignores ambient
            # precision settings and refuses any implicit rounding.
            context.prec = 64
            context.traps[Inexact] = True
            context.traps[Rounded] = True
            return _plain_decimal(Decimal(base) + Decimal(increment))
    except DecimalException as exc:
        raise ArithmeticFailure("Exact decimal arithmetic failed.") from exc


def _validate_answer(spec: CompoundGenerationSpec, fact: SourceFact, answer: str) -> None:
    try:
        plan, _, _ = bind_contract(spec.policy.contract, spec.question, answer, None)
        if plan != spec.plan:
            raise ContractBindingError("Generated answer does not match the registered plan.")
    except (BindingError, ValueError, TypeError) as exc:
        raise ContractBindingError("Generated answer violates the registered contract.") from exc
    fields = json.loads(answer)  # Duplicate keys/types were checked by bind_contract.
    if Decimal(fields["base"]) != Decimal(fact.value):
        raise SourceIntegrityError("Generated base differs from the approved source fact.")
    if Decimal(fields["derived"]) != Decimal(_derived_value(fact.value, spec.plan.increment)):
        raise ArithmeticFailure("Generated derived value does not equal base plus increment.")


def generate_compound_answer(
    question: str, *, configuration: QuestionPolicyConfiguration | None = None,
) -> CompoundGenerationResult | None:
    """Return a verified generation, None for non-Compound, or a typed failure.

    This performs no verifier validation and grants no deployment authorization.
    """
    spec = resolve_registered_compound(question, configuration=configuration)
    if spec is None:
        return None
    sources = _load_sources(spec.catalog)
    fact = _find_fact(spec, sources)
    answer = json.dumps({"base": _plain_decimal(Decimal(fact.value)),
                         "derived": _derived_value(fact.value, spec.plan.increment)}, separators=(",", ":"))
    _validate_answer(spec, fact, answer)
    return CompoundGenerationResult(
        answer=answer, policy_id=spec.policy.policy_id,
        contract_id=spec.policy.contract.compatibility_id, plan_id=spec.plan.plan_id,
        source_manifest_id=sources.manifest_id, descriptor=fact.descriptor,
        source_hashes=tuple(zip(_REQUIRED, (sources.corpus_sha256,
            sources.independent_source_sha256, sources.independent_countries_sha256))),
        corpus_record_sha256=hashlib.sha256(fact.corpus_row_json.encode()).hexdigest(),
    )
