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

        observations_applied = orchestrator.record_persisted_ground_truth(
            validation_id=request.validation_id,
            answer_is_correct=request.is_correct,
        )

        return {
            "status": "success",
            "feedback": feedback,
            "validation_id": request.validation_id,
            "is_correct": request.is_correct,
            "observations_applied": observations_applied,
        }

    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process feedback: {str(exc)}",
        )