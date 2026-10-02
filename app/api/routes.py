"""FastAPI route definitions."""

from typing import Optional

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


class GenerateAndValidateRequest(BaseModel):
    question: str = Field(..., min_length=1)
    context: Optional[str] = None


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


@router.post("/generate-and-validate")
def generate_and_validate(request: GenerateAndValidateRequest):
    """Generate an answer and validate it through the verification pipeline."""
    try:
        answer = generate_answer(request.question)

        validation_request = ValidationRequest(
            question=request.question,
            answer=answer,
            context=request.context,
        )

        validation_result = _validation_service.validate(validation_request)

        return {
            "question": request.question,
            "answer": answer,
            "validation": validation_result,
            "status": "success",
        }

    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Generation or validation failed: {exc}",
        )