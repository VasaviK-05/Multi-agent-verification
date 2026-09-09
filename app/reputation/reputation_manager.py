"""Reputation manager — placeholder implementation."""

DEFAULT_REPUTATION = 0.5


class ReputationManager:
    """Manages domain-specific verifier reputation scores.

    TODO: Implement domain-specific EWMA reputation logic here.
    """

    def get_reputation(self, verifier_name: str, domain: str) -> float:
        """Return the current reputation score for a verifier in a domain.

        Scaffold: returns a default placeholder value.
        """
        # TODO: Look up stored reputation from database
        return DEFAULT_REPUTATION

    def update_reputation(
        self, verifier_name: str, domain: str, outcome: bool
    ) -> None:
        """Update reputation based on verifier outcome.

        Scaffold: no-op placeholder.
        """
        # TODO: Apply EWMA update and persist to database
        pass
