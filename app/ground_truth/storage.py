from datetime import datetime, timezone
from uuid import uuid4

from app.ground_truth.models import GroundTruthRecord
from database import get_connection


def save_ground_truth(
    validation_id: str,
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

        cursor.execute(
            """
            INSERT INTO ground_truth_labels
            (
                ground_truth_id,
                validation_id,
                label,
                source,
                labeled_at
            )
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                str(ground_truth_id),
                str(validation_id),
                label,
                source,
                labeled_at,
            ),
        )

        connection.commit()

        return GroundTruthRecord(
            ground_truth_id=ground_truth_id,
            validation_id=validation_id,
            label=label,
            source=source,
            labeled_at=labeled_at,
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