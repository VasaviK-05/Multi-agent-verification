"""Run the existing selector against frozen statistics without modifying live state."""

from copy import copy, deepcopy
from dataclasses import replace


class PlanningMismatch(ValueError):
    pass


class FrozenPlanningReputation:
    def __init__(self, context):
        self._statistics = {s.verifier_name: s for s in context.plan.reputation_statistics}
        self._domain = context.plan.domain

    def statistics_batch(self, pairs):
        pairs = tuple(pairs)
        if any(domain != self._domain or name not in self._statistics for name, domain in pairs):
            raise PlanningMismatch("current domain/candidate set differs from frozen episode")
        return tuple(replace(self._statistics[name]) for name, _ in pairs)


def frozen_selector(selector, context):
    """Shallow-clone identity/factories; detach mutable planning config and live manager slot.

    This narrow adapter deliberately reuses plan()/resolve(), capability definitions,
    prerequisites and lazy factories. The original selector and manager are untouched.
    """
    captured = copy(selector)
    for field in ("verifier_profiles", "difficulty_range", "type_mapping", "_capabilities"):
        setattr(captured, field, deepcopy(getattr(selector, field)))
    captured._injected = None if selector._injected is None else list(selector._injected)
    # Operational lazy-instance caching is shared, as in baseline resolution;
    # planning never reads or populates it. Only planning configuration is cloned.
    captured._cache = selector._cache
    captured._reputation_manager = FrozenPlanningReputation(context)
    return captured
