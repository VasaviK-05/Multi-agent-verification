"""Domain-aware verifier reputation (Beta prototype).

Reputation is tracked separately for each verifier × domain pair:

    R = alpha / (alpha + beta)

Successful verification increments alpha; incorrect verification
increments beta. This is a prototype Beta-reputation model, not the
final EWMA / calibrated reputation system.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class _BetaState:
    alpha: float
    beta: float

    @property
    def reputation(self) -> float:
        return self.alpha / (self.alpha + self.beta)


class ReputationManager:
    """Maintains domain-specific Beta reputation for each verifier."""

    # PROTOTYPE uniform prior: R = 1 / (1 + 1) = 0.5
    DEFAULT_ALPHA = 1.0
    DEFAULT_BETA = 1.0

    def __init__(
        self,
        prior_alpha: float = DEFAULT_ALPHA,
        prior_beta: float = DEFAULT_BETA,
    ) -> None:
        self._prior_alpha = prior_alpha
        self._prior_beta = prior_beta
        self._table: dict[tuple[str, str], _BetaState] = {}

    def _state(self, verifier_name: str, domain: str) -> _BetaState:
        key = (verifier_name, domain)
        if key not in self._table:
            self._table[key] = _BetaState(self._prior_alpha, self._prior_beta)
        return self._table[key]

    def get_reputation(self, verifier_name: str, domain: str) -> float:
        """Return E[R] = alpha / (alpha + beta) for this verifier/domain."""
        return round(self._state(verifier_name, domain).reputation, 6)

    def update_reputation(
        self, verifier_name: str, domain: str, outcome: bool
    ) -> None:
        """Update Beta counts. outcome=True means a correct verification."""
        state = self._state(verifier_name, domain)
        if outcome:
            state.alpha += 1
        else:
            state.beta += 1
