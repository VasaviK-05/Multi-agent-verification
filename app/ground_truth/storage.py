from datetime import datetime, timezone
from uuid import UUID, uuid4

from app.ground_truth.models import GroundTruthRecord
from database import get_connection


def save_ground_truth(
    validation_id: UUID,
    question_id: int,
    label: str,
    source: str,
) -> GroundTruthRecord:

    ground_truth_id = uuid4()
    labeled_at = datetime.now(timezone.utc)

    connection = None
    cursor = None

    try:
        connection = get_connection()
        cursor = connection.cursor()

        # Attempt to insert a new ground-truth record.
        # If this validation already has a record, do nothing.
        cursor.execute(
            """
            INSERT INTO ground_truth_labels
            (
                ground_truth_id,
                validation_id,
                question_id,
                label,
                source,
                labeled_at
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (validation_id) DO NOTHING
            RETURNING
                ground_truth_id,
                validation_id,
                question_id,
                label,
                source,
                labeled_at
            """,
            (
                str(ground_truth_id),
                str(validation_id),
                question_id,
                label,
                source,
                labeled_at,
            ),
        )

        row = cursor.fetchone()

        # A new record was successfully inserted.
        if row is not None:
            connection.commit()

            return GroundTruthRecord(
                ground_truth_id=row[0],
                validation_id=row[1],
                question_id=row[2],
                label=row[3],
                source=row[4],
                labeled_at=row[5],
            )

        # A record already exists. Retrieve it.
        cursor.execute(
            """
            SELECT
                ground_truth_id,
                validation_id,
                question_id,
                label,
                source,
                labeled_at
            FROM ground_truth_labels
            WHERE validation_id = %s
            """,
            (str(validation_id),),
        )

        existing = cursor.fetchone()

        if existing is None:
            raise RuntimeError(
                "Ground-truth conflict occurred, "
                "but the existing record could not be retrieved."
            )

        existing_record = GroundTruthRecord(
            ground_truth_id=existing[0],
            validation_id=existing[1],
            question_id=existing[2],
            label=existing[3],
            source=existing[4],
            labeled_at=existing[5],
        )

        # Identical retry: return the existing record.
        if (
            existing_record.question_id == question_id
            and existing_record.label == label
            and existing_record.source == source
        ):
            connection.commit()
            return existing_record

        # Different data for the same validation: reject it.
        raise ValueError(
            f"Conflicting ground-truth data for validation "
            f"{validation_id}. An existing record has different "
            "question_id, label, or source."
        )

    except Exception:
        if connection:
            connection.rollback()
        raise

    finally:
        if cursor:
            cursor.close()

        if connection:
            connection.close()