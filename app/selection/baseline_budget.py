"""Baseline-only budget admission and accounting; no Game plan serialization changes."""
from dataclasses import dataclass, asdict
from itertools import combinations
import hashlib
import json
import math
from pathlib import Path

from app.game.models import content_id
from app.game.offline.calibration import CalibrationArtifact, MeasurementSetup, read_json
from app.game.offline.timing import TimedVerifier


@dataclass(frozen=True)
class BaselineBudgetSnapshot:
    status: str = "unconfigured"
    reason: str = "baseline_budget_configuration_absent"
    level: str | None = None
    limit_ms: float | None = None
    costs: tuple[tuple[str, float], ...] = ()
    calibration_id: str | None = None
    calibration_sha256: str | None = None
    setup_fingerprint: str | None = None
    configuration_id: str | None = None

    def __post_init__(self):
        if self.status not in {"configured", "unconfigured"}:
            raise ValueError("invalid baseline budget status")
        if self.status == "configured" and (type(self.limit_ms) not in (int, float)
                or not math.isfinite(self.limit_ms) or self.limit_ms < 0):
            raise ValueError("explicit finite nonnegative budget required")
        object.__setattr__(self, "costs", tuple(tuple(row) for row in self.costs))
        if len(dict(self.costs)) != len(self.costs):
            raise ValueError("duplicate empirical cost")


def validate_baseline_calibration(artifact, observed_setup):
    """Pure validation; production activation additionally requires empirical evidence."""
    # Reparse bytes, including existing model instances, to rerun integrity checks.
    if isinstance(artifact, CalibrationArtifact):
        artifact = artifact.model_dump(mode="json")
    artifact = CalibrationArtifact.model_validate(artifact)
    observed_setup = MeasurementSetup.model_validate(observed_setup)
    if artifact.request.measurements.setup != observed_setup:
        raise ValueError("baseline_calibration_setup_mismatch")
    names = {v.verifier_name for v in observed_setup.resources.verifiers}
    if set(artifact.request.required_verifiers) != names:
        raise ValueError("baseline_calibration_candidates_mismatch")
    return tuple((r["verifier_name"], r["attempt_cost"]) for r in artifact.result["estimates"])


def capture_baseline_budget_configuration(selector):
    """Read one server configuration and independently observe the default baseline.

    No artifact or copied expected fingerprint can provide its own observation.
    All failures preserve legacy execution with explicit unconfigured status.
    """
    from app.utils.config import settings
    from app.benchmark.baseline_setup import observe_baseline_setup, INITIALIZATION, NAMES
    from app.selection.baseline_resources import BaselineVerifierSelector

    if not settings.BASELINE_BUDGET_CONFIG_PATH:
        return BaselineBudgetSnapshot()
    stage = "configuration"
    try:
        path = Path(settings.BASELINE_BUDGET_CONFIG_PATH).resolve()
        config = read_json(path)
        if set(config) != {"version", "levels_ms", "active_level", "calibration_path",
                           "index_receipt_path", "service_observation_path"}:
            raise ValueError("invalid baseline budget keys")
        levels, level = config["levels_ms"], config["active_level"]
        if config["version"] != "baseline_budget_configuration_v1" or not isinstance(levels, dict) or not levels:
            raise ValueError("invalid baseline budget configuration")
        if any(not isinstance(k, str) or not k.strip() or type(v) not in (int, float)
               or not math.isfinite(v) or v < 0 for k, v in levels.items()) or level not in levels:
            raise ValueError("invalid baseline budget levels")

        def resource(key):
            value = config[key]
            if not isinstance(value, str) or not value.strip():
                raise ValueError("missing baseline resource")
            candidate = Path(value)
            return candidate if candidate.is_absolute() else path.parent / candidate

        stage = "calibration"
        raw = resource("calibration_path").read_bytes()
        artifact = CalibrationArtifact.model_validate_json(raw)
        setup = artifact.request.measurements.setup
        if setup.evidence_kind != "empirical" or setup.environment.get("initialization") != INITIALIZATION:
            return BaselineBudgetSnapshot(reason="calibration_not_baseline_empirical")
        if type(selector) is not BaselineVerifierSelector or not selector.uses_default_factory:
            return BaselineBudgetSnapshot(reason="baseline_custom_factory_not_reviewed")
        stage = "setup_observation"
        observed = observe_baseline_setup(index_receipt_path=resource("index_receipt_path"),
                                          service_observation_path=resource("service_observation_path"))
        stage = "compatibility"
        observed.resources.require_candidates(NAMES)
        selected = selector.baseline_evidence_configuration
        if observed.environment.get("baseline_evidence_configuration_id", "legacy_default") != (
                selected.configuration_id if selected else "legacy_default"):
            raise ValueError("baseline_selector_observer_resource_configuration_mismatch")
        costs = validate_baseline_calibration(artifact, observed)
        selector.bind_baseline_setup(observed.fingerprint)
        return BaselineBudgetSnapshot(status="configured", reason="compatible_empirical_calibration",
            level=level, limit_ms=float(levels[level]), costs=costs,
            calibration_id=artifact.calibration_id, calibration_sha256=hashlib.sha256(raw).hexdigest(),
            setup_fingerprint=observed.fingerprint, configuration_id=content_id(config))
    except Exception:
        # Configuration/provenance errors are not user errors and must not leak paths.
        return BaselineBudgetSnapshot(reason=f"baseline_budget_{stage}_unavailable_or_invalid")


@dataclass(frozen=True)
class BaselineBudgetPlan:
    initial_selected: tuple[str, ...]
    fallback: tuple[str, ...]
    feasible: bool
    reason: str
    estimated_initial_ms: float | None


def plan_with_budget(plan, snapshot):
    """Keep priority order; find a feasible initial team before allowing dispatch.

    Try the original target size first, then smaller teams down to the existing
    contributor floor. Unknown costs invalidate admission, never become zero.
    """
    names = plan.initial_selected + plan.fallback
    if snapshot.status != "configured":
        return BaselineBudgetPlan(plan.initial_selected, plan.fallback, True, "unconfigured", None)
    costs = dict(snapshot.costs)
    if any(n not in costs or not _valid_cost(costs[n]) for n in names):
        return BaselineBudgetPlan((), (), False, "missing_or_invalid_empirical_cost", None)
    minimum = max(plan.minimum_count, 2 if plan.difficulty != "hard" else 1)
    capabilities = {c.verifier_name: set(c.expected_capabilities) for c in plan.candidates if c.eligible}
    required = set(plan.requirements.requirements) if plan.requirements.requirements_known else set()
    if plan.requirements.status == "invalid":
        return BaselineBudgetPlan((), (), False, "invalid_coverage_requirements", None)
    target = min(len(names), max(minimum, len(plan.initial_selected)))
    for size in range(target, minimum - 1, -1):
        for team in combinations(names, size):
            covered = set().union(*(capabilities.get(n, set()) for n in team))
            try:
                total = math.fsum(costs[n] for n in team)
            except OverflowError:
                total = math.inf
            if total <= snapshot.limit_ms and required <= covered:
                return BaselineBudgetPlan(team, tuple(n for n in names if n not in team),
                                          True, "estimated_team_admitted", total)
    return BaselineBudgetPlan((), (), False, "estimated_budget_or_coverage_infeasible", None)


class BudgetLedger:
    """Per-request mutable accounting around immutable server-owned inputs.

    Admission is non-preemptive: a running call can overrun. No cancellation or
    total API-latency guarantee is implied.
    """
    def __init__(self, snapshot, execution_id):
        self.snapshot, self.execution_id = snapshot, execution_id
        self.attempts, self.skipped = [], []
        self.plan = None

    @property
    def actual_ms(self):
        return math.fsum(a["duration_ms"] for a in self.attempts)

    @property
    def remaining_ms(self):
        return None if self.snapshot.limit_ms is None else max(0., self.snapshot.limit_ms - self.actual_ms)

    def admit(self, name):
        if self.snapshot.status != "configured":
            return True
        cost = dict(self.snapshot.costs).get(name)
        reason = ("unknown_empirical_cost" if not _valid_cost(cost) else
                  "actual_budget_exhausted" if self.actual_ms >= self.snapshot.limit_ms else
                  "remaining_budget_insufficient" if cost > self.remaining_ms else None)
        if reason is not None:
            self.skipped.append(dict(verifier_name=name, reason=reason, remaining_ms=self.remaining_ms,
                                     estimated_cost_ms=cost))
            return False
        return True

    def verify(self, verifier, question, answer, context):
        rows = []
        try:
            return TimedVerifier(verifier, [], measurement_metadata={"execution_id": self.execution_id},
                                 measurements=rows).verify(question, answer, context)
        finally:
            for row in rows:
                estimate = dict(self.snapshot.costs).get(verifier.name) if self.snapshot.status == "configured" else None
                self.attempts.append({**row, "estimated_cost_ms": estimate,
                    "estimate_overrun": estimate is not None and row["duration_ms"] > estimate})
                self.attempts[-1]["remaining_ms_after_attempt"] = self.remaining_ms

    def metrics(self, name):
        if not self.attempts or self.attempts[-1]["verifier_name"] != name:
            return {}
        row = self.attempts[-1]
        return dict(duration_ms=row["duration_ms"], estimated_cost=row["estimated_cost_ms"], cost_units="ms")

    def audit(self):
        return {**asdict(self.snapshot), "units": "ms", "scope": "cumulative_external_verify_wall_time",
                "actual_attempt_ms": self.actual_ms, "remaining_ms": self.remaining_ms,
                "estimated_attempted_ms": (math.fsum(a["estimated_cost_ms"] for a in self.attempts)
                    if self.snapshot.status == "configured" and all(
                        _valid_cost(a["estimated_cost_ms"]) for a in self.attempts) else None),
                "actual_limit_exceeded": self.snapshot.limit_ms is not None and self.actual_ms > self.snapshot.limit_ms,
                "preemption_supported": False, "attempts": [dict(a) for a in self.attempts],
                "skipped": [dict(a) for a in self.skipped],
                "admission_plan": None if self.plan is None else asdict(self.plan)}


def _valid_cost(value):
    return type(value) in (int, float) and math.isfinite(value) and value >= 0
