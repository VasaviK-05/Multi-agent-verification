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
from app.database.validation_repository import update_validation_record
from app.database.verifier_repository import save_verifier_outputs
from app.database.audit_repository import create_audit, update_audit
from app.models.schemas import (
    CreateSessionRequest,
    SessionResponse,
    ValidationRequest,
    ValidationResponse,
)
from app.services.validation_service import ValidationService

from app.services.answer_generation import GeneratedAnswer, dispatch_generation
from app.services.compound_generation import (
    CompoundGenerationError, UnsupportedRegistrationError, SourceUnavailableError,
    SourceIntegrityError, FactLookupError, ArithmeticFailure, ContractBindingError,
    ConfigurationLoadingError,
)
from app.ground_truth.storage import save_ground_truth


router = APIRouter()
_validation_service = ValidationService(persist_execution=True)


@router.get("/health")
def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}




@router.post("/validate", response_model=ValidationResponse)
def validate(request: ValidationRequest):
    result = _validation_service.validate(request)

    if result.validation_id is None:
        return result

    orchestrator = _validation_service._orchestrator
    attempt_ids = {
        id(result_item): attempt_id
        for result_item in result.results
        if (attempt_id := orchestrator.get_attempt_id_for_result(result_item))
    }

    # Persist validation first because the audit has a foreign key
    # referencing validation_records.
    update_validation_record(
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
            attempt_ids=attempt_ids,
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
    session_id: UUID | None = None


class GenerateAndValidateRequest(BaseModel):
    question: str = Field(..., min_length=1)
    context: Optional[str] = None
    session_id: Optional[str] = None


def _generation_metadata(generated: GeneratedAnswer) -> dict:
    return {"generation_method": generated.generation_method,
            "generation_provenance": generated.provenance}


def _generate_for_request(question: str) -> GeneratedAnswer:
    # Keep this boundary outside persistence/validation exception handling.
    try:
        return dispatch_generation(question, validation_service=_validation_service)
    except HTTPException:
        raise
    except CompoundGenerationError as exc:
        mapping = {
            UnsupportedRegistrationError: (422, "COMPOUND_REGISTRATION_UNSUPPORTED", "Compound question is not registered."),
            SourceUnavailableError: (503, "COMPOUND_SOURCE_UNAVAILABLE", "Approved source material is unavailable."),
            SourceIntegrityError: (500, "COMPOUND_SOURCE_INTEGRITY_MISMATCH", "Approved source integrity check failed."),
            FactLookupError: (500, "COMPOUND_SOURCE_FACT_NOT_UNIQUE", "A unique approved source fact is required."),
            ArithmeticFailure: (500, "COMPOUND_ARITHMETIC_FAILED", "Exact Compound arithmetic failed."),
            ContractBindingError: (500, "COMPOUND_CONTRACT_BINDING_FAILED", "Generated answer violates its contract."),
            ConfigurationLoadingError: (500, "GENERATION_CONFIGURATION_INVALID", "Generation configuration is unavailable or inconsistent."),
        }
        status, code, message = next((value for kind, value in mapping.items() if isinstance(exc, kind)),
            (500, "GENERATION_INTERNAL_ERROR", "Answer generation failed."))
        raise HTTPException(status_code=status, detail={"code": code, "message": message, "stage": "generation"}) from None
    except Exception:
        raise HTTPException(status_code=500, detail={"code": "GENERATION_INTERNAL_ERROR",
            "message": "Answer generation failed.", "stage": "generation"}) from None


@router.post("/generate-answer")
def generate(request: QuestionRequest):
    """Generate an answer through shared dispatch, then store it once."""

    generated = _generate_for_request(request.question)
    answer = generated.answer
    connection = None
    cursor = None

    try:
        connection = get_connection()
        cursor = connection.cursor()

        if request.session_id is not None:
            cursor.execute("SELECT session_id FROM sessions WHERE session_id = %s",
                           (str(request.session_id),))
            if cursor.fetchone() is None:
                raise HTTPException(status_code=404, detail="Session not found.")

        cursor.execute(
            """
            INSERT INTO questions_answers (
                question,
                answer,
                session_id,
                created_at
            )
            VALUES (%s, %s, %s, NOW())
            RETURNING id
            """,
            (
                request.question,
                answer,
                str(request.session_id) if request.session_id is not None else None,
            ),
        )

        question_id = cursor.fetchone()[0]
        connection.commit()

        return {
            "question_id": question_id,
            "question": request.question,
            "answer": answer,
            "status": "success",
            **_generation_metadata(generated),
        }

    except HTTPException:
        if connection:
            connection.rollback()
        raise
    except Exception:
        if connection:
            connection.rollback()

        raise HTTPException(
            status_code=500,
            detail={"code": "ANSWER_PERSISTENCE_FAILED", "message": "Generated answer could not be stored.", "stage": "persistence"},
        )

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()



@router.post("/generate-and-validate")
def generate_and_validate(request: GenerateAndValidateRequest):
    """Generate an answer and validate it through the verification pipeline."""
    generated = _generate_for_request(request.question)
    answer = generated.answer
    stage = "persistence"
    try:

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

        stage = "validation"
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

        orchestrator = _validation_service._orchestrator
        attempt_ids = {
            id(result_item): attempt_id
            for result_item in validation_result.results
            if (attempt_id := orchestrator.get_attempt_id_for_result(result_item))
        }

        stage = "persistence"
        # Persist validation before creating its audit.
        update_validation_record(
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

        initial_summary = {**(validation_result.execution_audit or {}),
                           "generation": _generation_metadata(generated)}
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
                attempt_ids=attempt_ids,
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
            run_summary = {**(audit_context.run_summary or {}),
                           "generation": _generation_metadata(generated)}
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
            "question_id": question_id,
            "question": request.question,
            "answer": answer,
            "validation": validation_result,
            "status": "success",
            **_generation_metadata(generated),
        }

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=500,
            detail={"code": "PERSISTENCE_FAILED" if stage == "persistence" else "VALIDATION_FAILED",
                    "message": "The operation could not be completed.", "stage": stage},
        ) from None


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
