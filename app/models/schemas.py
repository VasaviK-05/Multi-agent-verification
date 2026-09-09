"""Shared Pydantic models for validation requests and responses."""

from typing import Any, Optional

from pydantic import BaseModel, Field


class ValidationRequest(BaseModel):
    """Input payload for answer validation."""

    question: str
    answer: str
    context: Optional[str] = None


class VerificationResult(BaseModel):
    """Output from a single verifier."""

    verifier_name: str
    score: float = Field(ge=0.0, le=1.0)
    passed: bool
    reasoning: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None


class ValidationResponse(BaseModel):
    """Aggregated validation response returned to the client."""

    results: list[VerificationResult]
    final_status: str
    final_score: Optional[float] = None
