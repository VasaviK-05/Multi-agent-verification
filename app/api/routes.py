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
from app.database.audit_repository import create_audit, update_audit
from app.models.schemas import (
    CreateSessionRequest,
    SessionResponse,
    ValidationRequest,
    ValidationResponse,
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

    if result.validation_id is None:
        return result

    # Persist validation first because the audit has a foreign key
    # referencing validation_records.
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

    # Create the initial audit record.
    initial_summary = getattr(result, "execution_audit", None) or {}
    initial_plan = initial_summary.get("selection_plan") or {}

    create_audit(
        validation_id=result.validation_id,
        question_id=request.question_id,
        session_id=request.session_id,
        policy_version=initial_plan.get("policy_version"),
        selected_strategy=initial_summary.get("selected_strategy_id"),
        execution_contract=initial_summary.get("execution_contract"),
        reputation_snapshot_id=initial_summary.get("reputation_snapshot_id"),
        selection_plan=initial_plan,
        run_summary=initial_summary,
    )

    # Persist verifier outputs and ground truth.
    try:
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

    except Exception:
        try:
            update_audit(
                result.validation_id,
                run_status="failed",
                failure_details=[
                    {
                        "stage": "persistence",
                        "reason": "Verifier or ground-truth persistence failed",
                    }
                ],
            )
        except Exception:
            pass

        raise

    # Build and persist the completed audit.
    try:
        audit_context = _validation_service.get_validation_context(
            result.validation_id
        )
        run_summary = audit_context.run_summary or {}
        selection_plan = run_summary.get("selection_plan") or {}
        candidates = selection_plan.get("candidates") or []

        update_audit(
            result.validation_id,
            run_status="completed",
            selected_verifiers=result.selected_verifiers or [],
            ranking_explanations=candidates,
            coverage_outcomes={
                "coverage": run_summary.get("coverage", {}),
                "missing_coverage": run_summary.get("missing_coverage", []),
            },
            decision_summary={
                "final_status": result.final_status,
                "final_score": result.final_score,
                "domain": result.domain,
                "early_stop_reason": result.early_stop_reason,
                "signed_score": result.signed_score,
                "termination": run_summary.get("termination"),
                "last_stopping_assessment": run_summary.get(
                    "last_stopping_assessment"
                ),
                "minimum_contributors": run_summary.get("minimum_contributors"),
                "contributors": run_summary.get("contributors"),
                "numerical_decision": run_summary.get("numerical_decision", {}),
                "selection_plan": selection_plan,
                "attempted_verifiers": run_summary.get("attempted_verifiers", []),
                "unavailable_verifiers": run_summary.get("unavailable_verifiers", []),
                "runtime_availability": run_summary.get("runtime_availability", {}),
                "stopping_policy_vetoes": run_summary.get(
                    "stopping_policy_vetoes", []
                ),
            },
            execution_costs={
                "candidate_estimated_costs": {
                    candidate["verifier_name"]: candidate.get("cost")
                    for candidate in candidates
                    if candidate.get("verifier_name") is not None
                },
                "candidate_estimated_latencies": {
                    candidate["verifier_name"]: candidate.get("latency")
                    for candidate in candidates
                    if candidate.get("verifier_name") is not None
                },
                "game_estimated_attempt_costs": {
                    attempt["verifier_name"]: attempt.get("estimated_attempt_cost")
                    for attempt in run_summary.get("attempts", [])
                    if attempt.get("verifier_name") is not None
                },
                "game_estimated_selected_cost": run_summary.get(
                    "estimated_selected_cost"
                ),
                "game_estimated_attempted_cost": run_summary.get(
                    "estimated_attempted_cost"
                ),
            },
            selection_plan=selection_plan,
            run_summary=run_summary,
        )

    except Exception:
        # If audit completion fails, make a best-effort attempt
        # to mark the audit as failed.
        try:
            update_audit(
                result.validation_id,
                run_status="failed",
                failure_details=[
                    {
                        "stage": "audit_completion",
                        "reason": "Audit completion update failed",
                    }
                ],
            )
        except Exception:
            pass

        raise

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
        validation_id = validation_result.validation_id

        if not validation_id:
            raise ValueError("Validation did not return a validation ID")

        # Persist validation before creating its audit.
        save_validation(
            validation_id=validation_id,
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

        initial_summary = validation_result.execution_audit or {}
        initial_plan = initial_summary.get("selection_plan") or {}

        # Audit creation has its own failure boundary.
        create_audit(
            validation_id=validation_id,
            question_id=question_id,
            session_id=request.session_id,
            policy_version=initial_plan.get("policy_version"),
            selected_strategy=initial_summary.get("selected_strategy_id"),
            execution_contract=initial_summary.get("execution_contract"),
            reputation_snapshot_id=initial_summary.get("reputation_snapshot_id"),
            selection_plan=initial_plan,
            run_summary=initial_summary,
        )

        # Persist verifier outputs and ground truth.
        try:
            save_verifier_outputs(
                validation_id=validation_id,
                question_id=question_id,
                results=validation_result.results,
            )

            if validation_result.ground_truth:
                save_ground_truth(
                    validation_id=UUID(validation_id),
                    question_id=question_id,
                    label=validation_result.ground_truth.label,
                    source=validation_result.ground_truth.source,
                )

        except Exception:
            try:
                update_audit(
                    validation_id,
                    run_status="failed",
                    failure_details=[
                        {
                            "stage": "persistence",
                            "reason": "Verifier or ground-truth persistence failed",
                        }
                    ],
                )
            except Exception:
                pass

            raise

        # Build and persist the completed audit.
        try:
            audit_context = _validation_service.get_validation_context(
                validation_id
            )
            run_summary = audit_context.run_summary or {}
            selection_plan = run_summary.get("selection_plan") or {}
            candidates = selection_plan.get("candidates") or []

            update_audit(
                validation_id,
                run_status="completed",
                selected_verifiers=validation_result.selected_verifiers or [],
                ranking_explanations=candidates,
                coverage_outcomes={
                    "coverage": run_summary.get("coverage", {}),
                    "missing_coverage": run_summary.get("missing_coverage", []),
                },
                decision_summary={
                    "final_status": validation_result.final_status,
                    "final_score": validation_result.final_score,
                    "domain": validation_result.domain,
                    "early_stop_reason": validation_result.early_stop_reason,
                    "signed_score": validation_result.signed_score,
                    "termination": run_summary.get("termination"),
                    "last_stopping_assessment": run_summary.get(
                        "last_stopping_assessment"
                    ),
                    "minimum_contributors": run_summary.get("minimum_contributors"),
                    "contributors": run_summary.get("contributors"),
                    "numerical_decision": run_summary.get("numerical_decision", {}),
                    "selection_plan": selection_plan,
                    "attempted_verifiers": run_summary.get("attempted_verifiers", []),
                    "unavailable_verifiers": run_summary.get("unavailable_verifiers", []),
                    "runtime_availability": run_summary.get("runtime_availability", {}),
                    "stopping_policy_vetoes": run_summary.get(
                        "stopping_policy_vetoes", []
                    ),
                },
                execution_costs={
                    "candidate_estimated_costs": {
                        candidate["verifier_name"]: candidate.get("cost")
                        for candidate in candidates
                        if candidate.get("verifier_name") is not None
                    },
                    "candidate_estimated_latencies": {
                        candidate["verifier_name"]: candidate.get("latency")
                        for candidate in candidates
                        if candidate.get("verifier_name") is not None
                    },
                    "game_estimated_attempt_costs": {
                        attempt["verifier_name"]: attempt.get("estimated_attempt_cost")
                        for attempt in run_summary.get("attempts", [])
                        if attempt.get("verifier_name") is not None
                    },
                    "game_estimated_selected_cost": run_summary.get(
                        "estimated_selected_cost"
                    ),
                    "game_estimated_attempted_cost": run_summary.get(
                        "estimated_attempted_cost"
                    ),
                },
                selection_plan=selection_plan,
                run_summary=run_summary,
            )

        except Exception:
            try:
                update_audit(
                    validation_id,
                    run_status="failed",
                    failure_details=[
                        {
                            "stage": "audit_completion",
                            "reason": "Audit completion update failed",
                        }
                    ],
                )
            except Exception:
                pass

            raise

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

@router.get("/reputation")
def get_reputation():
    """Return persisted verifier reputation data."""
    return load_reputation()
