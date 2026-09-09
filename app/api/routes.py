"""FastAPI route definitions."""

from fastapi import APIRouter

from app.models.schemas import ValidationRequest, ValidationResponse
from app.services.validation_service import ValidationService

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
