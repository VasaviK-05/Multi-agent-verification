"""Paired cluster bootstrap. Exact policy expectations, no sampled-team noise."""

import random

from app.game.dependencies import FrozenModel
from app.game.offline.evaluation import summarize
from app.game.offline.replay import replay
from app.game.research.comparison import validate_frozen
from app.game.research.readiness import require_ready


class Interval(FrozenModel):
    method: str
    attack_id: str
    metric: str
    lower: float | None
    upper: float | None
    defined_resamples: int
    total_resamples: int


class GroupedUncertainty(FrozenModel):
    comparison_id: str
    specification_id: str
    code_revision: str
    manifest_id: str
    evidence_kind: str
    planning_category: str
    run_kind: str
    cluster_count: int
    reason: str | None
    intervals: tuple[Interval, ...]


def _quantile(values, q):
    values = sorted(values)
    position = (len(values) - 1) * q
    lower = int(position)
    upper = min(lower + 1, len(values) - 1)
    return values[lower] + (position - lower) * (values[upper] - values[lower])


def _bootstrap(spec, frozen, role, actual_code_revision):
    spec, frozen = validate_frozen(spec, frozen, actual_code_revision=actual_code_revision)
    report = require_ready(spec, actual_code_revision=actual_code_revision)
    examples = spec.manifest.partition(role).examples
    groups = {}
    for example in examples:
        groups.setdefault(example.split_identity, []).append(example)
    names = sorted(groups)
    common = dict(comparison_id=frozen.comparison_id, specification_id=spec.specification_id,
                  code_revision=actual_code_revision, run_kind="frozen_final" if role == "final_test" else "development_pilot",
                  manifest_id=spec.manifest.manifest_id, evidence_kind=spec.manifest.evidence_kind,
                  planning_category=report.planning_category, cluster_count=len(names))
    if len(names) < 2:
        return GroupedUncertainty(**common, reason="at_least_two_independent_split_identity_clusters_required", intervals=())
    cube = {(s.strategy_id, a.attack_id, e.example_id): replay(spec.context, s, a, spec.attacks, spec.contract, e)
            for s in frozen.full_artifact.policy.strategies for a in report.attacks for e in examples}
    rng = random.Random(spec.uncertainty.seed)
    samples = {}
    for _ in range(spec.uncertainty.resamples):
        # Same cluster draws across all policies and attacks preserve pairing.
        draw = [rng.choice(names) for _ in names]
        metrics_by_method = {}
        for policy in frozen.policies:
            attack_metrics = []
            for attack in report.attacks:
                weighted = tuple((cube[s, attack.attack_id, e.example_id].model_copy(
                    update={"example_id": f"{slot}:{e.example_id}"}), p)
                    for slot, name in enumerate(draw) for e in groups[name] for s, p in policy.probabilities)
                metric = summarize(weighted, spec.context.loss_configuration)
                attack_metrics.append(metric)
                for field in ("mean_loss", "decision_coverage", "selective_risk", "estimated_resource_cost"):
                    samples.setdefault((policy.method, attack.attack_id, field), []).append(getattr(metric, field))
            worst = max(m.mean_loss for m in attack_metrics)
            samples.setdefault((policy.method, "fixed_attack_set", "worst_case_expected_loss"), []).append(worst)
            metrics_by_method[policy.method] = attack_metrics
        # Paired differences are preferable to comparing marginal intervals.
        for method, metrics in metrics_by_method.items():
            if method == "full_minimax":
                continue
            for attack, full, baseline in zip(report.attacks, metrics_by_method["full_minimax"], metrics):
                for field in ("mean_loss", "decision_coverage", "selective_risk", "estimated_resource_cost"):
                    left, right = getattr(full, field), getattr(baseline, field)
                    difference = None if left is None or right is None else left - right
                    samples.setdefault(("full_minimax-minus-" + method, attack.attack_id, field), []).append(difference)
            difference = max(m.mean_loss for m in metrics_by_method["full_minimax"]) - max(m.mean_loss for m in metrics)
            samples.setdefault(("full_minimax-minus-" + method, "fixed_attack_set", "worst_case_expected_loss"), []).append(difference)
    tail = (1. - spec.uncertainty.confidence_level) / 2.
    intervals = []
    for (method, attack, field), values in sorted(samples.items()):
        defined = [v for v in values if v is not None]
        # Undefined selective risk in ANY resample prevents an unconditional CI.
        complete = len(defined) == len(values)
        intervals.append(Interval(method=method, attack_id=attack, metric=field,
            lower=_quantile(defined, tail) if complete else None,
            upper=_quantile(defined, 1. - tail) if complete else None,
            defined_resamples=len(defined), total_resamples=len(values)))
    return GroupedUncertainty(**common, reason=None, intervals=tuple(intervals))


def bootstrap_development_pilot(spec, frozen, *, actual_code_revision):
    return _bootstrap(spec, frozen, "development", actual_code_revision)


def bootstrap_frozen_final(spec, frozen, *, actual_code_revision):
    """Explicit final-test uncertainty entry, using already frozen policies."""
    return _bootstrap(spec, frozen, "final_test", actual_code_revision)
