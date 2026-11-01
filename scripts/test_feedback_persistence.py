import os
import sys
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")

# Load project configuration, then force the isolated test database.
load_dotenv()
os.environ["DB_NAME"] = "capstone_test_db"

from database import get_connection
from app.database.validation_repository import save_validation
from app.database.verifier_repository import save_verifier_outputs
from app.database.feedback_repository import save_feedback
from app.models.schemas import VerificationResult
from app.orchestration.validation_orchestrator import ValidationOrchestrator


def verify_test_database():
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT current_database()")
        database_name = cursor.fetchone()[0]
        cursor.close()

        if database_name != "capstone_test_db":
            raise RuntimeError(
                f"Safety check failed: connected to {database_name}"
            )

        print(f"Connected safely to: {database_name}")
    finally:
        connection.close()


def cleanup(validation_id, question_id):
    connection = get_connection()
    try:
        cursor = connection.cursor()

        cursor.execute(
            "DELETE FROM feedback WHERE validation_id = %s",
            (validation_id,),
        )
        cursor.execute(
            "DELETE FROM ground_truth_labels WHERE validation_id = %s",
            (validation_id,),
        )
        cursor.execute(
            "DELETE FROM verifier_outputs WHERE validation_id = %s",
            (validation_id,),
        )
        cursor.execute(
            "DELETE FROM validation_audits WHERE validation_id = %s",
            (validation_id,),
        )
        cursor.execute(
            "DELETE FROM validation_records WHERE validation_id = %s",
            (validation_id,),
        )
        cursor.execute(
            "DELETE FROM questions_answers WHERE id = %s",
            (question_id,),
        )

        connection.commit()
        cursor.close()
        print("Test records cleaned up.")
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def main():
    verify_test_database()

    validation_id = str(uuid4())
    domain = f"feedback-integration-{uuid4().hex}"
    verifier_name = f"test-verifier-{uuid4().hex[:8]}"
    question_id = None

    try:
        # 1. Create a test question.
        connection = get_connection()
        try:
            cursor = connection.cursor()
            cursor.execute(
                """
                INSERT INTO questions_answers (question, answer)
                VALUES (%s, %s)
                RETURNING id
                """,
                (
                    "Integration test question",
                    "Integration test expected answer",
                ),
            )
            question_id = cursor.fetchone()[0]
            connection.commit()
            cursor.close()
        finally:
            connection.close()

        print("Test question created:", question_id)

        # 2. Persist validation.
        save_validation(
            validation_id=validation_id,
            question_id=question_id,
            question="Integration test question",
            generated_answer="Integration test answer",
            context=None,
            final_status="completed",
            final_score=0.9,
            session_id=None,
            domain=domain,
            difficulty="easy",
            selected_verifiers=[verifier_name],
        )

        print("Validation persisted.")

        # 3. Persist verifier output.
        result = VerificationResult(
            verifier_name=verifier_name,
            score=0.9,
            passed=True,
            reasoning="Integration test verifier result",
            metadata={"test": True},
        )

        save_verifier_outputs(
            validation_id=validation_id,
            question_id=question_id,
            results=[result],
        )

        print("Verifier output persisted.")

        # 4. Create the orchestrator BEFORE feedback is saved.
        first_orchestrator = ValidationOrchestrator()

        assert first_orchestrator._contexts == {}

        # Now save feedback.
        feedback = save_feedback(
            validation_id=validation_id,
            is_correct=True,
            comment="Integration test feedback",
        )

        # Apply feedback using the already initialized orchestrator.
        first_count = (
            first_orchestrator.record_persisted_ground_truth(
                validation_id=validation_id,
                answer_is_correct=True,
            )
        )

        assert first_count > 0, (
            f"Expected new reputation observations, got {first_count}"
        )

        print("Initial reputation learning: PASS")

        # 5. Simulate restart with a fresh orchestrator.
        restarted_orchestrator = ValidationOrchestrator()

        assert restarted_orchestrator._contexts == {}

        retry_feedback = save_feedback(
            validation_id=validation_id,
            is_correct=True,
            comment="Integration test feedback",
        )

        assert retry_feedback["id"] == feedback["id"]

        retry_count = (
            restarted_orchestrator.record_persisted_ground_truth(
                validation_id=validation_id,
                answer_is_correct=True,
            )
        )

        assert retry_count == 0, (
            "Feedback was applied again after restart."
        )

        print("Restart recovery: PASS")
        print("Duplicate feedback retry: PASS")
        print("No duplicate reputation observations: PASS")

        # 6. Verify the feedback row still exists exactly once.
        connection = get_connection()
        try:
            cursor = connection.cursor()
            cursor.execute(
                """
                SELECT COUNT(*)
                FROM feedback
                WHERE validation_id = %s
                """,
                (validation_id,),
            )
            feedback_count = cursor.fetchone()[0]
            cursor.close()
        finally:
            connection.close()

        assert feedback_count == 1

        print("Exactly one feedback record exists: PASS")
        print("\nFEEDBACK PERSISTENCE INTEGRATION TEST: PASS")

    finally:
        if question_id is not None:
            cleanup(validation_id, question_id)


if __name__ == "__main__":
    main()
