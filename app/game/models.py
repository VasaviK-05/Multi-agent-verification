"""Validated, detached planning records and deterministic content identifiers."""

from dataclasses import asdict
import hashlib
import json
import math

from pydantic import Field, StrictFloat, TypeAdapter, model_validator

from app.game.dependencies import DependencyRegistry, FrozenModel, identifier
from app.selection.models import SelectionPlan
from app.selection.capabilities import CapabilityDescriptor


# Strategy labels, not decision callables; execution integration remains separate.
AGGREGATIONS = ("reputation_weighted", "dependency_group")
_SELECTION_ADAPTER = TypeAdapter(SelectionPlan)


def canonical_json(value) -> str:
    def normalize(item):
        if isinstance(item, float) and item == 0:
            return 0.0  # Negative zero has the same numeric meaning.
        if isinstance(item, dict):
            return {key: normalize(value) for key, value in item.items()}
        if isinstance(item, (tuple, list)):
            return [normalize(value) for value in item]
        return item
    return json.dumps(normalize(value), sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False)


def content_id(value) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def requirement_signature(requirements) -> str:
    data = asdict(requirements)
    # Requirement order is not semantic. Preserve uncertainty, source and all
    # validator diagnostics, including legacy disagreement and invalidity.
    for key, value in data.items():
        if isinstance(value, tuple):
            data[key] = sorted(value)
    return content_id(data)


class PayoffProvenance(FrozenModel):
    attack_specification: str
    history_dataset: str
    development_dataset: str
    final_test_dataset: str
    matrix_version: str
    loss_configuration: str
    category: str
    category_kind: str = "domain"
    evidence_kind: str

    @model_validator(mode="after")
    def validate_provenance(self):
        for field in ("attack_specification", "history_dataset", "development_dataset",
                      "final_test_dataset", "matrix_version", "loss_configuration", "category"):
            identifier(getattr(self, field))
        if len({self.history_dataset, self.development_dataset, self.final_test_dataset}) != 3:
            raise ValueError("history, development and final-test partitions must be distinct")
        if self.category_kind not in {"domain", "pooled"}:
            raise ValueError("category_kind must be domain or pooled")
        if self.evidence_kind not in {"empirical", "synthetic_test_fixture"}:
            raise ValueError("payoffs require explicit evidence kind")
        return self


class LossConfiguration(FrozenModel):
    """Application-chosen penalties, not scientifically calibrated constants."""
    version: str
    false_accept: StrictFloat = Field(ge=0)
    false_reject: StrictFloat = Field(ge=0)
    uncertain: StrictFloat = Field(ge=0)
    resource_weight: StrictFloat = Field(ge=0)
    cost_units: str

    @model_validator(mode="after")
    def validate_loss(self):
        identifier(self.version)
        identifier(self.cost_units)
        return self


class PlanningContext(FrozenModel):
    # Canonical JSON is intentional: unlike a frozen wrapper around dicts or
    # permissively constructed legacy dataclasses it cannot retain mutable leaves.
    selection_json: str
    attempt_costs: tuple[tuple[str, StrictFloat], ...]
    budget: StrictFloat = Field(ge=0)
    cost_units: str
    loss_configuration: LossConfiguration
    analyzer_provenance: tuple[tuple[str, str | None], ...]
    dependencies: DependencyRegistry
    aggregation_versions: tuple[tuple[str, str], ...]
    provenance: PayoffProvenance
    version: str = "game_context_v1"

    @model_validator(mode="after")
    def validate_context(self):
        plan = _SELECTION_ADAPTER.validate_json(self.selection_json, strict=True)
        canonical = canonical_json(asdict(plan))
        object.__setattr__(self, "selection_json", canonical)
        identifier(plan.domain)
        identifier(plan.domain_status)
        identifier(plan.analysis_method)
        identifier(self.cost_units)
        if (self.loss_configuration.cost_units != self.cost_units
            or self.loss_configuration.version != self.provenance.loss_configuration):
            raise ValueError("loss configuration must match provenance and budget/cost units")
        provenance = dict(self.analyzer_provenance)
        if len(provenance) != len(self.analyzer_provenance) or set(provenance) != {
            "research_context_presence", "context_version", "scoring_version", "analysis_method", "domain_status"
        }:
            raise ValueError("complete detached analyzer provenance required")
        object.__setattr__(self, "analyzer_provenance", tuple(sorted(self.analyzer_provenance)))
        if self.version != "game_context_v1":
            raise ValueError("unsupported planning context version")
        if type(plan.minimum_count) is not int or plan.minimum_count < 1:
            raise ValueError("minimum count must be positive")
        requirements = plan.requirements
        if (requirements.source not in {"legacy", "research_context"}
            or requirements.status not in {"known", "unknown", "invalid"}
            or bool(requirements.errors) != (requirements.status == "invalid")
            or requirements.requirements_known != (requirements.status == "known")
            or (requirements.status == "known" and not requirements.requirements)
            or (requirements.status == "unknown" and requirements.requirements)):
            raise ValueError("inconsistent requirement-validation result")
        weights = dict(requirements.weights)
        if (len(weights) != len(requirements.weights)
            or any(weight < 0 or weight > 1 for weight in weights.values())
            or (requirements.status == "known" and (
                set(weights) != set(requirements.requirements)
                or not math.isclose(math.fsum(weights.values()), 1.0)))
            or (requirements.status != "known" and weights)):
            raise ValueError("inconsistent captured requirement weights")
        names = [row.verifier_name for row in plan.candidates]
        if len(names) != len(set(names)):
            raise ValueError("duplicate candidates")
        for row in plan.candidates:
            identifier(row.verifier_name)
            CapabilityDescriptor(row.expected_capabilities, row.requires_reference,
                                 row.configured_readiness, row.exclusion_reason, row.limitations)
            if (row.registration_order < 0 or row.observation_count < 0
                or not 0 <= row.reputation <= 1 or not 0 <= row.cost <= 1
                or not 0 <= row.latency <= 1 or not 0 <= row.suitability <= 1
                or row.resource_penalty < 0 or row.suitability_contribution < 0
                or row.prerequisite_status not in {"ready", "unknown", "unavailable", "missing_reference"}):
                raise ValueError("invalid captured candidate statistics/configuration")
            if row.eligible and (not row.registered or row.exclusion_reason is not None
                                 or row.prerequisite_status != row.configured_readiness
                                 or row.configured_readiness == "unavailable"
                                 or (row.requires_reference and not plan.reference_available)):
                raise ValueError("inconsistent candidate eligibility")
        costs = dict(self.attempt_costs)
        if len(costs) != len(self.attempt_costs) or set(costs) != set(names):
            raise ValueError("explicit attempt costs required for every candidate")
        if any(not math.isfinite(value) or value < 0 for value in costs.values()):
            raise ValueError("attempt costs must be finite and nonnegative")
        versions = dict(self.aggregation_versions)
        if len(versions) != len(self.aggregation_versions) or set(versions) != set(AGGREGATIONS):
            raise ValueError("both aggregation versions are required")
        for value in versions.values():
            identifier(value)
        statistics = plan.reputation_statistics
        if {s.verifier_name for s in statistics} != set(names) or len(statistics) != len(names):
            raise ValueError("complete captured reputation statistics required")
        for stats in statistics:
            if (stats.domain != plan.domain or stats.successes < 0 or stats.failures < 0
                or stats.observation_count != stats.successes + stats.failures
                or stats.cold_start != (stats.observation_count == 0)
                or stats.alpha <= 0 or stats.beta <= 0
                or stats.alpha < stats.successes or stats.beta < stats.failures
                or not 0 <= stats.posterior_mean <= 1 or stats.posterior_variance < 0):
                raise ValueError("inconsistent reputation statistics")
            # The manager supports priors whose sum overflows. Ratio arithmetic
            # preserves that existing contract without a second reputation read.
            ratio = min(stats.alpha, stats.beta) / max(stats.alpha, stats.beta)
            mean = 1 / (1 + ratio) if stats.alpha >= stats.beta else ratio / (1 + ratio)
            if not math.isclose(stats.posterior_mean, mean):
                raise ValueError("inconsistent reputation posterior mean")
            scale = max(stats.alpha, stats.beta)
            variance = (mean * (1 - mean) / (1 + scale * (1 + ratio)) if scale <= 1 else
                        mean * (1 - mean) / scale / (1 + ratio + 1 / scale))
            if not math.isclose(stats.posterior_variance, variance):
                raise ValueError("inconsistent reputation posterior variance")
            # Only the two component counts enter the manager's float updates.
            # Their exact integer sum need not itself be float-representable.
            for count in (stats.successes, stats.failures):
                try:
                    valid_count = math.isfinite(float(count)) and float(count) == count
                except OverflowError:
                    valid_count = False
                if not valid_count:
                    raise ValueError("reputation count cannot be represented exactly")
            candidate = next(row for row in plan.candidates if row.verifier_name == stats.verifier_name)
            if (candidate.reputation != round(stats.posterior_mean, 6)
                or candidate.observation_count != stats.observation_count
                or candidate.cold_start != stats.cold_start):
                raise ValueError("candidate statistics differ from captured reputation snapshot")
        self.dependencies.groups(names)
        if self.provenance.category_kind == "domain" and self.provenance.category != plan.domain:
            raise ValueError("policy category must match domain or explicitly declare pooling")
        object.__setattr__(self, "attempt_costs", tuple(sorted(self.attempt_costs)))
        object.__setattr__(self, "aggregation_versions", tuple(sorted(self.aggregation_versions)))
        return self

    @property
    def plan(self) -> SelectionPlan:
        """A fresh detached view; mutating it cannot change this context."""
        return _SELECTION_ADAPTER.validate_json(self.selection_json)

    @property
    def requirement_signature(self) -> str:
        return requirement_signature(self.plan.requirements)

    @property
    def requirements_missing(self) -> bool:
        requirements = self.plan.requirements
        return requirements.source == "legacy" and not requirements.legacy_hints

    @property
    def minimum_participant_count(self) -> int:
        """Include the existing orchestrator's easy/medium execution floor."""
        plan = self.plan
        return plan.minimum_count if plan.difficulty == "hard" else max(2, plan.minimum_count)

    @property
    def reputation_snapshot_id(self) -> str:
        return content_id(sorted((asdict(s) for s in self.plan.reputation_statistics),
                                 key=lambda s: s["verifier_name"]))

    @property
    def compatibility_id(self) -> str:
        data = self.model_dump(mode="json")
        plan = json.loads(data.pop("selection_json"))
        # Baseline rankings and diagnostic ordering do not define obligations.
        data["planning"] = {key: plan[key] for key in (
            "domain", "domain_status", "analysis_method", "context_version", "scoring_version",
            "reference_available", "minimum_count")}
        data["planning"]["requirement_signature"] = self.requirement_signature
        data["planning"]["minimum_participant_count"] = self.minimum_participant_count
        candidates = []
        for row in plan["candidates"]:
            # Greedy ranking terms/order do not affect exhaustive game planning.
            candidate = {key: row[key] for key in (
                "verifier_name", "registered", "eligible", "capability_source", "cost", "latency",
                "requires_reference", "configured_readiness", "prerequisite_status", "exclusion_reason")}
            candidate["expected_capabilities"] = sorted(set(row["expected_capabilities"]))
            candidate["limitations"] = sorted(set(row["limitations"]))
            candidates.append(candidate)
        data["planning"]["candidates"] = sorted(candidates, key=lambda c: c["verifier_name"])
        data["planning"]["reputation_snapshot_id"] = self.reputation_snapshot_id
        return content_id(data)


def capture_context(selector, analysis, *, context=None, **configuration) -> PlanningContext:
    """Reuse selector validation and its single atomic reputation read. No resolve()."""
    plan = selector.plan(analysis, context)
    research = analysis.research_context
    def provenance_value(field):
        value = getattr(research, field, None)
        return value if value is None or isinstance(value, str) else f"<invalid:{type(value).__name__}>"
    provenance = tuple((field, provenance_value(field)) for field in (
        "context_version", "scoring_version", "analysis_method", "domain_status"))
    provenance += (("research_context_presence", "missing" if research is None else "present"),)
    return PlanningContext(selection_json=canonical_json(asdict(plan)),
                           analyzer_provenance=provenance, **configuration)


class Strategy(FrozenModel):
    strategy_id: str
    verifiers: tuple[str, ...]
    aggregation: str
    estimated_cost: StrictFloat = Field(ge=0)

    @model_validator(mode="after")
    def validate_strategy(self):
        names = tuple(sorted(self.verifiers))
        if not names or len(names) != len(set(names)) or self.aggregation not in AGGREGATIONS:
            raise ValueError("strategy requires unique verifiers and a declared aggregation identifier")
        for name in names:
            identifier(name)
        if self.strategy_id != content_id([names, self.aggregation]):
            raise ValueError("strategy ID does not bind its verifier team and aggregation")
        object.__setattr__(self, "verifiers", names)
        return self


class Infeasibility(FrozenModel):
    verifiers: tuple[str, ...]
    reasons: tuple[str, ...]


class EnumerationResult(FrozenModel):
    status: str
    strategies: tuple[Strategy, ...]
    rejected: tuple[Infeasibility, ...]
    exclusions: tuple[tuple[str, str], ...]


class PayoffMatrix(FrozenModel):
    strategy_ids: tuple[str, ...]
    attack_ids: tuple[str, ...]
    values: tuple[tuple[StrictFloat, ...], ...]
    compatibility_id: str
    # Generic labelled games may omit row definitions. Policy construction may not.
    strategy_definitions: tuple[Strategy, ...] = ()

    @model_validator(mode="after")
    def validate_matrix(self):
        identifier(self.compatibility_id)
        for labels in (self.strategy_ids, self.attack_ids):
            if not labels or len(labels) != len(set(labels)):
                raise ValueError("matrix labels must be nonempty and unique")
            for label in labels:
                identifier(label)
        if len(self.values) != len(self.strategy_ids) or any(
            len(row) != len(self.attack_ids) for row in self.values
        ):
            raise ValueError("matrix dimensions must match labels")
        if self.strategy_definitions and tuple(s.strategy_id for s in self.strategy_definitions) != self.strategy_ids:
            raise ValueError("matrix row definitions must match strategy labels and order")
        return self

    @property
    def matrix_id(self) -> str:
        return content_id(self.model_dump(mode="json"))


class SolverResult(FrozenModel):
    status: str
    message: str
    tolerance: StrictFloat = Field(gt=0, le=1e-3)
    probabilities: tuple[tuple[str, StrictFloat], ...] = ()
    game_value: float | None = None
    constraint_residuals: tuple[tuple[str, float], ...] = ()
    attack_losses: tuple[tuple[str, float], ...] = ()
    worst_case_attacks: tuple[str, ...] = ()
    normalization_residual: float | None = None
    minimum_probability: float | None = None
    matrix_id: str
    attack_probabilities: tuple[tuple[str, StrictFloat], ...] = ()
    dual_lower_bound: float | None = None
    primal_dual_gap: float | None = None
    optimality_basis: str = "not_verified"
