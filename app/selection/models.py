"""Detached, immutable selection inputs and audit records (no live agents)."""

from dataclasses import asdict, dataclass
import json
from app.reputation.reputation_manager import ReputationStatistics


@dataclass(frozen=True)
class RequirementInputs:
    source: str
    status: str
    requirements: tuple[str, ...]
    weights: tuple[tuple[str, float], ...]
    requirements_known: bool
    legacy_hints: tuple[str, ...]
    disagreements: tuple[str, ...]
    unsupported: tuple[str, ...]
    errors: tuple[str, ...] = ()
    legacy_unrecognized: tuple[str, ...] = ()
    weight_discrepancies: tuple[tuple[str, float], ...] = ()


@dataclass(frozen=True)
class CandidateExplanation:
    verifier_name: str
    registration_order: int
    reputation: float
    observation_count: int
    cold_start: bool
    cost: float
    latency: float
    resource_penalty: float
    suitability: float
    suitability_contribution: float
    utility: float
    registered: bool
    eligible: bool
    capability_source: str
    expected_capabilities: tuple[str, ...]
    requires_reference: bool
    configured_readiness: str
    prerequisite_status: str
    exclusion_reason: str | None
    limitations: tuple[str, ...]


@dataclass(frozen=True)
class SelectionPlan:
    policy_version: str
    domain: str
    domain_status: str
    difficulty: str
    difficulty_score: float
    analysis_method: str
    context_version: str | None
    scoring_version: str | None
    reference_available: bool
    requirements: RequirementInputs
    lambda_cost: float
    lambda_latency: float
    lambda_suitability: float
    type_mapping: tuple[tuple[str, str], ...]
    resource_units: str
    minimum_count: int
    target_count: int
    candidates: tuple[CandidateExplanation, ...]
    initial_selected: tuple[str, ...]
    fallback: tuple[str, ...]
    expected_covered: tuple[str, ...]
    expected_uncovered: tuple[str, ...]
    coverage_status: str
    exclusions: tuple[tuple[str, str], ...]
    reputation_statistics: tuple[ReputationStatistics, ...] = ()

    def to_dict(self) -> dict:
        """Return a fully detached JSON-shaped value for responses/persistence."""
        return json.loads(json.dumps(asdict(self), allow_nan=False))


class VerifierUnavailable(RuntimeError):
    """Explicit runtime contract for a temporarily unavailable verifier.

    Only this exception is recoverable by orchestration. ValueError,
    RuntimeError, import/model errors, etc. remain visible programming or
    configuration failures unless an adapter deliberately translates them.
    """
