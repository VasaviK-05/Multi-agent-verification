"""Abstract base class for all verifier implementations."""

from abc import ABC, abstractmethod
from typing import Optional

from app.models.schemas import VerificationResult


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
        """Verify an answer against a question."""
        ...
