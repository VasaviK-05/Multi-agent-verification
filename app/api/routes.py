"""FastAPI route definitions."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.models.schemas import ValidationRequest, ValidationResponse
from app.services.validation_service import ValidationService
from llm_service import generate_answer

router = APIRouter()
_validation_service = ValidationService()


@router.get("/health")
def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}


@router.post("/validate", response_model=ValidationResponse)
def validate(request: ValidationRequest) -> ValidationResponse:
    """Validate an answer against a question."""
    return _validation_service.validate(request)


class QuestionRequest(BaseModel):
    question: str = Field(..., min_length=1)


@router.post("/generate-answer")
def generate(request: QuestionRequest):
    """Generate an answer using the LLM."""
    try:
        answer = generate_answer(request.question)

        return {
            "question": request.question,
            "answer": answer,
            "status": "success",
        }

    except Exception:
        raise HTTPException(
            status_code=503,
            detail="LLM service is unavailable",
        )