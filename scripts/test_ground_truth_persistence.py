import os
import sys
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")
os.environ["DB_NAME"] = "capstone_test_db"

from database import get_connection
from app.database.validation_repository import save_validation
from app.ground_truth.storage import save_ground_truth


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
            "DELETE FROM ground_truth_labels WHERE validation_id = %s",
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
                    "Ground truth integration test question",
                    "Paris",
                ),
            )

            question_id = cursor.fetchone()[0]

            connection.commit()
            cursor.close()

        finally:
            connection.close()

        print("Test question created:", question_id)

        # 2. Persist a validation record.
        save_validation(
            validation_id=validation_id,
            question_id=question_id,
            question="What is the capital of France?",
            generated_answer="Paris",
            context=None,
            final_status="completed",
            final_score=1.0,
            session_id=None,
            domain="ground-truth-integration",
            difficulty="easy",
            selected_verifiers=[],
        )

        print("Validation persisted.")

        # 3. First ground-truth save.
        first = save_ground_truth(
            validation_id=validation_id,
            question_id=question_id,
            label="Paris",
            source="integration-test",
        )

        print("Initial ground-truth save: PASS")

        # 4. Retry with identical data.
        second = save_ground_truth(
            validation_id=validation_id,
            question_id=question_id,
            label="Paris",
            source="integration-test",
        )

        assert first.ground_truth_id == second.ground_truth_id
        assert first.label == second.label

        print("Identical retry returns existing record: PASS")

        # 5. Retry with a conflicting label.
        try:
            save_ground_truth(
                validation_id=validation_id,
                question_id=question_id,
                label="London",
                source="integration-test",
            )

        except ValueError:
            print("Conflicting label rejected: PASS")

        else:
            raise AssertionError(
                "Conflicting ground-truth label was accepted."
            )

        # 6. Retry with a conflicting source.
        try:
            save_ground_truth(
                validation_id=validation_id,
                question_id=question_id,
                label="Paris",
                source="different-source",
            )

        except ValueError:
            print("Conflicting source rejected: PASS")

        else:
            raise AssertionError(
                "Conflicting ground-truth source was accepted."
            )

        # 7. Verify exactly one database record exists.
        connection = get_connection()

        try:
            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT COUNT(*)
                FROM ground_truth_labels
                WHERE validation_id = %s
                """,
                (validation_id,),
            )

            record_count = cursor.fetchone()[0]
            cursor.close()

        finally:
            connection.close()

        assert record_count == 1, (
            f"Expected exactly one record, found {record_count}"
        )

        print("Exactly one ground-truth record exists: PASS")

        print(
            "\nGROUND-TRUTH POSTGRESQL INTEGRATION TEST: PASS"
        )

    finally:
        if question_id is not None:
            cleanup(validation_id, question_id)


if __name__ == "__main__":
    main()