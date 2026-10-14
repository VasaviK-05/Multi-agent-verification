"""FastAPI route definitions."""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from database import get_connection
from app.database.reputation_repository import load_reputation

from app.database.session_repository import (
    create_session,
    get_session_questions,
    get_sessions,
)
from app.database.validation_repository import save_validation
from app.database.verifier_repository import save_verifier_outputs
from app.database.feedback_repository import save_feedback
from app.models.schemas import (
    CreateSessionRequest,
    SessionResponse,
    ValidationRequest,
    ValidationResponse,
    FeedbackRequest,
)
from app.services.validation_service import ValidationService
from database import get_connection
from llm_service import generate_answer
from app.ground_truth.storage import save_ground_truth


router = APIRouter()
_validation_service = ValidationService()


@router.get("/health")
def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}


@router.post("/validate", response_model=ValidationResponse)
def validate(request: ValidationRequest):
    result = _validation_service.validate(request)

    if result.validation_id is not None:
        save_validation(
            validation_id=result.validation_id,
            question_id=request.question_id,
            question=request.question,
            generated_answer=request.answer,
            context=request.context,
            final_status=result.final_status,
            final_score=result.final_score,
            session_id=request.session_id,
            domain=result.domain,
            difficulty=result.difficulty,
            selected_verifiers=result.selected_verifiers,
            early_stop_reason=result.early_stop_reason,
            signed_score=result.signed_score,
        )

        save_verifier_outputs(
            validation_id=result.validation_id,
            question_id=request.question_id,
            results=result.results,
        )

        if result.ground_truth and request.question_id is not None:
            save_ground_truth(
                validation_id=UUID(result.validation_id),
                question_id=request.question_id,
                label=result.ground_truth.label,
                source=result.ground_truth.source,
            )

    return result


class QuestionRequest(BaseModel):
    question: str = Field(..., min_length=1)


class GenerateAndValidateRequest(BaseModel):
    question: str = Field(..., min_length=1)
    context: Optional[str] = None
    session_id: Optional[str] = None


@router.post("/generate-answer")
def generate(request: QuestionRequest):
    """Generate an answer using the LLM and store it."""

    connection = None
    cursor = None

    try:
        answer = generate_answer(request.question)

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO questions_answers (
                question,
                answer,
                created_at
            )
            VALUES (%s, %s, NOW())
            RETURNING id
            """,
            (
                request.question,
                answer,
            ),
        )

        question_id = cursor.fetchone()[0]
        connection.commit()

        return {
            "question_id": question_id,
            "question": request.question,
            "answer": answer,
            "status": "success",
        }

    except Exception:
        if connection:
            connection.rollback()

        raise HTTPException(
            status_code=503,
            detail="LLM service is unavailable",
        )

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


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
            question_id=question_id,
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
            difficulty=validation_result.difficulty,
            selected_verifiers=validation_result.selected_verifiers,
            early_stop_reason=validation_result.early_stop_reason,
            signed_score=validation_result.signed_score,
        )

        save_verifier_outputs(
            validation_id=validation_result.validation_id,
            question_id=question_id,
            results=validation_result.results,
        )

        if validation_result.ground_truth:
            save_ground_truth(
                validation_id=UUID(validation_result.validation_id),
                question_id=question_id,
                label=validation_result.ground_truth.label,
                source=validation_result.ground_truth.source,
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

@router.post("/feedback")
def submit_feedback(request: FeedbackRequest):
    """Store user feedback for a validation result."""

    try:
        feedback = save_feedback(
            validation_id=request.validation_id,
            is_correct=request.is_correct,
            comment=request.comment,
        )

        return {
            "status": "success",
            "feedback": feedback,
        }

    except ValueError as e:
        raise HTTPException(
            status_code=409,
            detail=str(e),
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save feedback: {str(e)}",
        )

@router.get("/reputation")
def get_reputation():
    """Return persisted verifier reputation data."""
    return load_reputation()