"""Dependency assumptions and matched failure columns for Experiment 3 ablation v1.

The declared registry is the existing structural assumption. It is not a measured
correlation. Independent and fully correlated registries are alternative
assumptions applied to the same saved reports. Abstentions are preserved.
"""

from __future__ import annotations

import random

from app.game.dependencies import Dependency, DependencyRegistry
from app.game.models import content_id
from app.game.offline.attacks import Attack, AttackSpecification, transform
from app.game.research.uncertainty import _quantile

VERIFIERS = ("semantic", "evidence", "rule", "confidence")
SPECIFICATION = AttackSpecification(version="report_corruption_v1", suppression="unavailable")
OPERATOR = "forced_support"
ABSTENTION_POLICY = "preserve_abstentions"
SEED = 20261113
RESAMPLES = 2000


def declared_registry() -> DependencyRegistry:
    groups = (
        ("deterministic_rule", ("rule",)),
        ("embedding_minilm", ("semantic", "evidence")),
        ("nli_deberta", ("evidence", "confidence")),
        ("ollama_generator", ("confidence",)),
    )
    return DependencyRegistry(
        version="structural_shared_resource_v1",
        dependencies=tuple(
            Dependency(resource_id=name, compromise_pathway="structural_assumption", verifiers=members)
            for name, members in groups
        ),
        unresolved=(),
    )


def independent_registry() -> DependencyRegistry:
    return DependencyRegistry(
        version="independent_verifier_failures_v1",
        dependencies=tuple(
            Dependency(resource_id=name, compromise_pathway="independent_assumption", verifiers=(name,))
            for name in sorted(VERIFIERS)
        ),
        unresolved=(),
    )


def fully_correlated_registry() -> DependencyRegistry:
    return DependencyRegistry(
        version="fully_correlated_verifiers_v1",
        dependencies=(),
        unresolved=tuple(sorted(VERIFIERS)),
    )


def registries() -> dict[str, DependencyRegistry]:
    return {
        "declared_structural": declared_registry(),
        "independent": independent_registry(),
        "fully_correlated": fully_correlated_registry(),
    }


def group_members(registry: DependencyRegistry) -> tuple[tuple[str, ...], ...]:
    return tuple(tuple(group.verifiers) for group in registry.groups(VERIFIERS))


def forced_support_attack(members: tuple[str, ...]) -> Attack:
    ordered = tuple(sorted(members))
    if not ordered:
        raise ValueError("a failure column needs at least one targeted verifier")
    return Attack(
        specification_id=SPECIFICATION.specification_id,
        kind=OPERATOR,
        group_id=content_id(ordered),
        members=ordered,
    )


def independent_attacks() -> tuple[Attack, ...]:
    """One column per verifier. A failure does not target anyone else."""
    return tuple(forced_support_attack((name,)) for name in sorted(VERIFIERS))


def correlated_attacks(registry: DependencyRegistry) -> tuple[Attack, ...]:
    """One column per failure group. Every member of that group is targeted together."""
    return tuple(forced_support_attack(members) for members in group_members(registry))


def matched_attacks() -> dict[str, tuple[Attack, ...]]:
    """The same columns for every aggregation registry.

    Correlated columns use the declared structural groups, so a row difference
    cannot be explained by changing who was targeted.
    """
    return {
        "independent_failures": independent_attacks(),
        "correlated_failures": correlated_attacks(declared_registry()),
    }


def native_attacks(assumption: str) -> dict[str, tuple[Attack, ...]]:
    registry = registries()[assumption]
    return {
        "independent_failures": independent_attacks(),
        "correlated_failures": correlated_attacks(registry),
    }


def apply_attack(attempts: dict[str, object], attack: Attack) -> tuple[dict[str, object], tuple[dict, ...]]:
    """Return transformed attempts and a per-verifier audit. The input mapping is not updated."""
    transformed = {}
    audits = []
    for name in VERIFIERS:
        result, audit = transform(attempts[name], attack, SPECIFICATION)
        transformed[name] = result
        audits.append({
            "verifier": name,
            "targeted": name in attack.members,
            "reason": audit.reason,
            "effective": audit.effective,
            "before_state": audit.before_state,
            "after_state": audit.after_state,
            "before_passed": audit.before_passed,
            "after_passed": audit.after_passed,
            "before_mass": audit.before_mass,
            "after_mass": audit.after_mass,
        })
    return transformed, tuple(audits)


def severity(audits: tuple[dict, ...], attack: Attack) -> dict:
    targeted = [row for row in audits if row["targeted"]]
    corrupted = [row for row in targeted if row["effective"]]
    outside = [row for row in audits if not row["targeted"] and row["effective"]]
    if outside:
        raise RuntimeError("a verifier outside the targeted group changed")
    return {
        "targeted_verifiers": list(attack.members),
        "targeted_count": len(attack.members),
        "actually_corrupted_count": len(corrupted),
        "preserved_abstention_count": sum(row["reason"] == "preserved_abstention" for row in targeted),
        "operator": OPERATOR,
        "abstention_policy": ABSTENTION_POLICY,
        "direction": "SUPPORT",
        "confidence_rule": "directional reports in the target receive score 1 and decision SUPPORT; abstentions are unchanged",
    }


def group_means(losses_by_group: dict[str, list[float]]) -> dict[str, float]:
    if any(not values for values in losses_by_group.values()):
        raise ValueError("a question group has no losses")
    return {group: sum(values) / len(values) for group, values in losses_by_group.items()}


def group_bootstrap(losses_by_group: dict[str, list[float]], *, seed: int = SEED, resamples: int = RESAMPLES) -> dict:
    """Resample question groups. Candidates that share a group stay inside that draw."""
    means = group_means(losses_by_group)
    groups = sorted(means)
    if len(groups) < 2:
        return {
            "mean": None if not groups else means[groups[0]],
            "lower": None,
            "upper": None,
            "groups": len(groups),
            "paired_observations": sum(len(values) for values in losses_by_group.values()),
            "resamples": 0,
            "reason": "at_least_two_related_groups_required",
            "seed": seed,
        }
    rng = random.Random(seed)
    drawn = []
    for _ in range(resamples):
        sample = [means[rng.choice(groups)] for _ in groups]
        drawn.append(sum(sample) / len(sample))
    observed = sum(means.values()) / len(groups)
    return {
        "mean": observed,
        "lower": _quantile(drawn, 0.025),
        "upper": _quantile(drawn, 0.975),
        "groups": len(groups),
        "paired_observations": sum(len(values) for values in losses_by_group.values()),
        "resamples": resamples,
        "reason": None,
        "seed": seed,
        "exact_zero_groups": sum(value == 0.0 for value in means.values()),
    }


def paired_group_difference(left: dict[str, list[float]], right: dict[str, list[float]], *, seed: int = SEED, resamples: int = RESAMPLES) -> dict:
    """Difference is left minus right, after averaging candidates inside each question group."""
    shared = sorted(set(left) & set(right))
    missing = sorted((set(left) | set(right)) - set(shared))
    if missing:
        raise ValueError("paired comparison is missing question groups")
    left_means = group_means({group: left[group] for group in shared})
    right_means = group_means({group: right[group] for group in shared})
    differences = {group: [left_means[group] - right_means[group]] for group in shared}
    summary = group_bootstrap(differences, seed=seed, resamples=resamples)
    summary["contrast"] = "left_minus_right"
    summary["exact_ties"] = summary["exact_zero_groups"]
    return summary
