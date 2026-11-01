
import os
import sys
import json
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")
os.environ["DB_NAME"] = "capstone_test_db"

from database import get_connection
from app.database.validation_repository import save_validation
from app.database.verifier_repository import save_verifier_outputs
from app.database.feedback_repository import save_feedback
from app.database.reputation_repository import (
    load_reputation_manager_state,
    save_reputation_state_and_rows,
)
from app.models.schemas import VerificationResult
from app.orchestration.validation_orchestrator import ValidationOrchestrator


def verify_database():
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT current_database()")
        name = cursor.fetchone()[0]
        cursor.close()

        if name != "capstone_test_db":
            raise RuntimeError(
                f"Safety check failed. Connected to: {name}"
            )

        print(f"Connected safely to: {name}")
    finally:
        connection.close()


def backup_snapshot():
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("""
            SELECT schema_version, state, updated_at
            FROM reputation_manager_state
            WHERE state_id = 1
        """)
        return cursor.fetchone()
    finally:
        connection.close()


def remove_snapshot():
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("""
            DELETE FROM reputation_manager_state
            WHERE state_id = 1
        """)
        connection.commit()
        cursor.close()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def restore_snapshot(snapshot):
    connection = get_connection()
    try:
        cursor = connection.cursor()

        cursor.execute("""
            DELETE FROM reputation_manager_state
            WHERE state_id = 1
        """)

        if snapshot is not None:
            schema_version, state, updated_at = snapshot

            if isinstance(state, str):
                state = json.loads(state)

            cursor.execute("""
                INSERT INTO reputation_manager_state (
                    state_id, schema_version, state, updated_at
                )
                VALUES (1, %s, %s::jsonb, %s)
            """, (
                schema_version,
                json.dumps(state),
                updated_at,
            ))

        connection.commit()
        cursor.close()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def cleanup(validation_id, question_id, verifier_name, domain):
    connection = get_connection()
    try:
        cursor = connection.cursor()

        if validation_id:
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

        if verifier_name and domain:
            cursor.execute("""
                DELETE FROM verifier_reputation
                WHERE verifier_name = %s AND domain = %s
            """, (verifier_name, domain))

        if question_id is not None:
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
    verify_database()

    validation_id = str(uuid4())
    domain = f"snapshot-recovery-{uuid4().hex}"
    verifier_name = f"recovery-verifier-{uuid4().hex[:8]}"

    question_id = None
    snapshot = backup_snapshot()

    print(
        "Original snapshot:",
        "present" if snapshot is not None else "absent",
    )

    try:
        # 1. Create a test question.
        connection = get_connection()
        try:
            cursor = connection.cursor()
            cursor.execute("""
                INSERT INTO questions_answers (question, answer)
                VALUES (%s, %s)
                RETURNING id
            """, (
                "Missing snapshot integration question",
                "Expected integration answer",
            ))
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
            question="Missing snapshot integration question",
            generated_answer="Integration test answer",
            context=None,
            final_status="completed",
            final_score=0.9,
            session_id=None,
            domain=domain,
            difficulty="easy",
            selected_verifiers=[verifier_name],
        )

        # 3. Persist verifier output.
        result = VerificationResult(
            verifier_name=verifier_name,
            score=0.9,
            passed=True,
            reasoning="Snapshot recovery test",
            metadata={"test": True},
        )

        save_verifier_outputs(
            validation_id=validation_id,
            question_id=question_id,
            results=[result],
        )

        # 4. Persist feedback.
        save_feedback(
            validation_id=validation_id,
            is_correct=True,
            comment="Missing snapshot recovery test",
        )

        print("Validation, verifier output and feedback persisted.")

        # 5. Remove only the snapshot, not reputation rows.
        remove_snapshot()

        assert load_reputation_manager_state() is None

        print("Snapshot removed: PASS")

        # 6. A fresh orchestrator must rebuild from feedback.
        recovered = ValidationOrchestrator()

        assert recovered._contexts == {}

        rebuilt_state = recovered._reputation_manager.export_state()

        matching_pairs = [
            pair
            for pair in rebuilt_state["pairs"]
            if pair["verifier_name"] == verifier_name
            and pair["domain"] == domain
        ]

        assert len(matching_pairs) == 1, (
            "Test verifier/domain pair was not reconstructed."
        )

        pair = matching_pairs[0]
        observations = (
            pair.get("successes", 0) + pair.get("failures", 0)
        )

        assert observations > 0, (
            f"Expected reconstructed observations, got {observations}"
        )

        print("Reputation rebuilt from PostgreSQL feedback: PASS")
        print("Reconstructed observations:", observations)

        # 7. Persist the rebuilt state again.
        save_reputation_state_and_rows(rebuilt_state)

        saved_state = load_reputation_manager_state()

        assert saved_state is not None

        saved_pairs = [
            pair
            for pair in saved_state["pairs"]
            if pair["verifier_name"] == verifier_name
            and pair["domain"] == domain
        ]

        assert len(saved_pairs) == 1

        print("Rebuilt snapshot persisted: PASS")

        # 8. Verify replay does not apply the event twice.
        retry_count = recovered.record_persisted_ground_truth(
            validation_id=validation_id,
            answer_is_correct=True,
        )

        assert retry_count == 0

        print("Replayed feedback remains idempotent: PASS")
        print("\nMISSING SNAPSHOT RECOVERY TEST: PASS")

    finally:
        try:
            cleanup(
                validation_id,
                question_id,
                verifier_name,
                domain,
            )
        finally:
            restore_snapshot(snapshot)
            print("Original reputation snapshot restored.")


if __name__ == "__main__":
    main()
