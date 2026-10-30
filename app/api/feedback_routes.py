from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.database.feedback_repository import save_feedback

from app.api.routes import _validation_service

router = APIRouter()


class FeedbackRequest(BaseModel):
    validation_id: str
    is_correct: bool
    comment: str | None = None


@router.post("/feedback")
def submit_feedback(request: FeedbackRequest):
    try:
        feedback = save_feedback(
            validation_id=request.validation_id,
            is_correct=request.is_correct,
            comment=request.comment,
        )
        
        orchestrator = _validation_service._orchestrator

        context = orchestrator.validation_context(request.validation_id)

        observations_applied = orchestrator.record_ground_truth(
            results=context.results,
            answer_is_correct=request.is_correct,
            domain=context.domain,
            validation_id=request.validation_id,
        )

        return {
            "status": "success",
            "validation_id": request.validation_id,
            "is_correct": request.is_correct,
            "observations_applied": observations_applied,
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        )