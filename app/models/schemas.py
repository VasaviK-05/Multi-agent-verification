"""Shared Pydantic models for validation requests and responses."""

from typing import Any, Optional

from pydantic import BaseModel, Field


class ValidationRequest(BaseModel):
    """Input payload for answer validation."""

    question: str
    answer: str
    context: Optional[str] = None
    session_id: Optional[str] = None
    question_id: Optional[int] = None

class VerificationResult(BaseModel):
    """Output from a single verifier."""

    verifier_name: str
    score: float = Field(ge=0.0, le=1.0)
    passed: bool
    reasoning: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None

class GroundTruthEvaluation(BaseModel):
    """Automatic correctness result based on available ground truth."""

    label: str
    source: str
    answer_is_correct: bool


class ValidationResponse(BaseModel):
    """Aggregated validation response returned to the client.

    ``validation_id`` and ``domain`` identify the run for a later label.
    They are empty when a caller builds a response without the orchestrator.
    """

    results: list[VerificationResult]
    final_status: str
    final_score: Optional[float] = None
    validation_id: Optional[str] = None
    domain: Optional[str] = None
    session_id: Optional[str] = None
    ground_truth: Optional[GroundTruthEvaluation] = None

class CreateSessionRequest(BaseModel):
    """Input payload for creating a session."""

    title: str


class SessionResponse(BaseModel):
    """Session information returned to the client."""

    session_id: str
    title: str
    created_at: Any
    updated_at: Any

class FeedbackRequest(BaseModel):
    validation_id: str
    is_correct: bool
    comment: Optional[str] = None