"""FastAPI route definitions."""

from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.database.session_repository import (
    create_session,
    get_session_questions,
    get_sessions,
)
from app.database.validation_repository import save_validation
from app.models.schemas import (
    CreateSessionRequest,
    SessionResponse,
    ValidationRequest,
    ValidationResponse,
)
from app.services.validation_service import ValidationService
from database import get_connection
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
    session_id: Optional[str] = None


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

        connection = None
        cursor = None

        try:
            connection = get_connection()
            cursor = connection.cursor()

            cursor.execute(
                """
                INSERT INTO questions_answers (question, answer)
                VALUES (%s, %s)
                RETURNING id
                """,
                (request.question, answer),
            )

            question_id = cursor.fetchone()[0]
            connection.commit()

        except Exception:
            if connection:
                connection.rollback()
            raise
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

        validation_request = ValidationRequest(
            question=request.question,
            answer=answer,
            context=request.context,
            session_id=request.session_id,
        )

        validation_result = _validation_service.validate(validation_request)

        save_validation(
            validation_id=validation_result.validation_id,
            question_id=question_id,
            question=request.question,
            generated_answer=answer,
            context=request.context,
            final_status=validation_result.final_status,
            final_score=validation_result.final_score,
            session_id=request.session_id,
            domain=validation_result.domain,
        )

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


@router.post("/sessions", response_model=SessionResponse)
def create_new_session(request: CreateSessionRequest) -> SessionResponse:
    """Create a new validation session."""
    return create_session(request.title)


@router.get("/sessions", response_model=list[SessionResponse])
def list_sessions() -> list[SessionResponse]:
    """Return all validation sessions."""
    return get_sessions()

@router.get("/sessions/{session_id}/questions")
def list_session_questions(session_id: str):
    """Return all questions asked in a validation session."""
    return get_session_questions(session_id)