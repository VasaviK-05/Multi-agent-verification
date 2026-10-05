"""Abstract base class and shared output contract for all verifiers.

Every verifier returns a ``VerificationResult``. That schema only has a
bounded ``score`` and a binary ``passed`` flag, so the verifiers agree on
two additional ``metadata`` keys that carry what the schema cannot:

``metadata["decision"]``
    One of ``SUPPORT``, ``REJECT``, ``UNSURE``. This is the verifier's own
    three-way judgment. ``passed`` is derived from it but is lossy:
    ``passed=False`` covers both ``REJECT`` and ``UNSURE``.

``metadata["score_meaning"]``
    One sentence stating what ``score`` measures for this verifier (cosine
    similarity, NLI class probability, deterministic outcome bit, agreement
    fraction). Equal numbers from different verifiers are not equal
    evidence, and none of them is a calibrated probability of correctness.

The decision layer currently reads abstentions through verifier-specific
hooks (see ``app/decision/vote_normalization.py``). ``decision`` is
additional information for that layer; it does not replace those hooks.
"""

from abc import ABC, abstractmethod
from typing import Optional

from app.models.schemas import VerificationResult

DECISION_SUPPORT = "SUPPORT"
DECISION_REJECT = "REJECT"
DECISION_UNSURE = "UNSURE"
DECISIONS = (DECISION_SUPPORT, DECISION_REJECT, DECISION_UNSURE)


class BaseVerifier(ABC):
    """Base contract for verifier services."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier for this verifier."""
        ...

    @abstractmethod
    def verify(
        self,
        question: str,
        answer: str,
        context: Optional[str] = None,
    ) -> VerificationResult:
        """Verify an answer against a question.

        Implementations must set ``metadata["decision"]`` and
        ``metadata["score_meaning"]`` as described in the module docstring.
        """
        ...
