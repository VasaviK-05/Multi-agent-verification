"""Domain-aware verifier reputation.

Each verifier × domain pair has its own Beta counts. The reported
reputation is the posterior mean

    R = alpha / (alpha + beta)

which is the mean used by the Beta reputation system (Jøsang and Ismail,
2002) when positive evidence is alpha - 1 and negative evidence is
beta - 1. With the default prior alpha = beta = 1 this is Laplace's
rule of succession: R = (r + 1) / (r + s + 2).

Cold start is explicit. Before any trusted label arrives, alpha and beta
stay at the prior, R is 0.5, and no other domain is copied in.

Updates run only from a ground-truth label received after validation:

    verifier_correct = (verifier_passed == answer_is_correct)
    correct     → alpha += 1
    incorrect   → beta += 1

``verifier_passed`` is that verifier's own vote. ``answer_is_correct`` is
the external label. The validation system's final status is not a label
and is rejected if it is passed in place of a boolean. A source other
than "ground_truth" is rejected, so a caller cannot record the system's
own prediction as evidence.

The prior and the +1 step size are UNCALIBRATED. This is not an EWMA.
See docs/decision_formulas.md.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class _BetaState:
    alpha: float
    beta: float

    @property
    def reputation(self) -> float:
        total = self.alpha + self.beta
        if total <= 0.0:
            return 0.5
        return self.alpha / total


class ReputationManager:
    """Maintains a separate Beta reputation for each verifier and domain."""

    # UNCALIBRATED uniform prior. R = 1 / (1 + 1) = 0.5 until a label arrives.
    DEFAULT_ALPHA = 1.0
    DEFAULT_BETA = 1.0
    GROUND_TRUTH_SOURCE = "ground_truth"

    def __init__(
        self,
        prior_alpha: float = DEFAULT_ALPHA,
        prior_beta: float = DEFAULT_BETA,
    ) -> None:
        if prior_alpha <= 0.0 or prior_beta <= 0.0:
            raise ValueError(
                "Beta prior parameters must be positive. "
                "The cold start uses alpha = beta = 1, which gives reputation 0.5."
            )
        self._prior_alpha = float(prior_alpha)
        self._prior_beta = float(prior_beta)
        self._table: dict[tuple[str, str], _BetaState] = {}

    def _state(self, verifier_name: str, domain: str) -> _BetaState:
        key = (verifier_name, domain)
        if key not in self._table:
            self._table[key] = _BetaState(self._prior_alpha, self._prior_beta)
        return self._table[key]

    def observation_count(self, verifier_name: str, domain: str) -> int:
        """How many ground-truth updates have been applied to this pair.

        The prior itself is not an observation. Cold start is a count of 0.
        """
        state = self._state(verifier_name, domain)
        raw = (state.alpha - self._prior_alpha) + (state.beta - self._prior_beta)
        return int(round(raw))

    def is_cold_start(self, verifier_name: str, domain: str) -> bool:
        """True when this pair still has only the prior, in this domain alone."""
        return self.observation_count(verifier_name, domain) == 0

    def get_reputation(self, verifier_name: str, domain: str) -> float:
        """Return R = alpha / (alpha + beta) for this verifier and domain.

        The default prior yields exactly 0.5. That value means "no labels
        yet" (or an even split of labels), not a measured accuracy.
        """
        return round(self._state(verifier_name, domain).reputation, 6)

    def update_reputation(
        self,
        verifier_name: str,
        domain: str,
        agreed_with_ground_truth: bool,
        *,
        source: str = GROUND_TRUTH_SOURCE,
    ) -> None:
        """Apply one Bernoulli observation from a trusted label.

        ``agreed_with_ground_truth`` must mean the verifier's vote matched
        an external label. It must not be the verifier's pass bit alone, and
        it must not be derived from this system's final status.
        """
        if source != self.GROUND_TRUTH_SOURCE:
            raise ValueError(
                "Reputation updates require source='ground_truth'. "
                "The system's own prediction is not evidence."
            )
        if not isinstance(agreed_with_ground_truth, bool):
            raise TypeError(
                "agreed_with_ground_truth must be a boolean. "
                "Pass the comparison with an external label, not a status string."
            )
        state = self._state(verifier_name, domain)
        if agreed_with_ground_truth:
            state.alpha += 1.0
        else:
            state.beta += 1.0

    def update_from_ground_truth(
        self,
        verifier_name: str,
        domain: str,
        verifier_passed: bool,
        answer_is_correct: bool,
    ) -> None:
        """Score one verifier vote against a label received after validation.

        The verifier was correct when its pass/reject vote matches the label.
        A reject on an incorrect answer is a success. A pass on an incorrect
        answer is a failure, even if the decision engine said "passed".
        """
        if not isinstance(verifier_passed, bool) or not isinstance(answer_is_correct, bool):
            raise TypeError(
                "verifier_passed and answer_is_correct must be booleans. "
                "A status string such as 'passed' is not a ground-truth label."
            )
        self.update_reputation(
            verifier_name,
            domain,
            verifier_passed == answer_is_correct,
            source=self.GROUND_TRUTH_SOURCE,
        )
