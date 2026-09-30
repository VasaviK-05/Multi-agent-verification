"""Database models for validation, verifier, reputation, and feedback records.

These are plain Python dataclasses used by the application layer.
The PostgreSQL schema is managed separately.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional


@dataclass
class ValidationRecord:
    """A stored validation request and its outcome."""

    id: str
    question_id: int
    question: str
    answer: str
    context: Optional[str]
    final_status: str
    final_score: Optional[float]
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class VerifierOutputRecord:
    """Stored output from a single verifier run."""

    id: str
    validation_id: str
    question_id: int
    verifier_name: str
    score: float
    passed: bool
    reasoning: Optional[str]
    metadata: Optional[dict[str, Any]] = None
    latency_ms: Optional[float] = None
    execution_order: Optional[int] = None


@dataclass
class DomainReputationRecord:
    """Stored reputation score for a verifier in a domain."""

    verifier_name: str
    domain: str
    reputation: float
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class FeedbackRecord:
    """Stored feedback or ground truth for a validation."""

    id: str
    validation_id: str
    is_correct: bool
    ground_truth: Optional[str] = None
    comment: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)