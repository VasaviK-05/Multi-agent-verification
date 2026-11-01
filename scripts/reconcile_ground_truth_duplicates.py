
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from database import get_connection


def main():
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            # Prevent concurrent writes during reconciliation.
            cursor.execute("""
                LOCK TABLE ground_truth_labels
                IN ACCESS EXCLUSIVE MODE
            """)

            # Confirm the expected number of redundant records.
            cursor.execute("""
                SELECT COALESCE(SUM(record_count - 1), 0)
                FROM (
                    SELECT COUNT(*) AS record_count
                    FROM ground_truth_labels
                    GROUP BY validation_id
                    HAVING COUNT(*) > 1
                ) duplicates
            """)

            redundant_count = cursor.fetchone()[0]

            if redundant_count != 2:
                raise RuntimeError(
                    f"Expected 2 redundant records, found {redundant_count}. "
                    "No changes will be made."
                )

            # Create a backup table with the original schema and constraints.
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS
                ground_truth_labels_duplicate_archive
                (LIKE ground_truth_labels INCLUDING ALL)
            """)

            cursor.execute("""
                ALTER TABLE ground_truth_labels_duplicate_archive
                ADD COLUMN IF NOT EXISTS archived_at
                TIMESTAMPTZ NOT NULL DEFAULT NOW()
            """)

            # Archive all but the earliest record in each duplicate group.
            cursor.execute("""
                WITH ranked AS (
                    SELECT
                        ground_truth_id,
                        ROW_NUMBER() OVER (
                            PARTITION BY validation_id
                            ORDER BY labeled_at ASC NULLS LAST,
                                     ground_truth_id ASC
                        ) AS record_rank
                    FROM ground_truth_labels
                )
                INSERT INTO ground_truth_labels_duplicate_archive (
                    ground_truth_id,
                    validation_id,
                    label,
                    source,
                    labeled_at,
                    question_id
                )
                SELECT
                    g.ground_truth_id,
                    g.validation_id,
                    g.label,
                    g.source,
                    g.labeled_at,
                    g.question_id
                FROM ground_truth_labels g
                JOIN ranked r
                  ON r.ground_truth_id = g.ground_truth_id
                WHERE r.record_rank > 1
                ON CONFLICT (ground_truth_id) DO NOTHING
            """)

            # Verify that both redundant records are safely archived.
            cursor.execute("""
                SELECT COUNT(*)
                FROM ground_truth_labels_duplicate_archive
                WHERE validation_id = %s
            """, ("078777c4-91ba-4deb-9aa2-0eb05eb8dfb3",))

            archived_count = cursor.fetchone()[0]

            if archived_count != 2:
                raise RuntimeError(
                    f"Expected 2 archived records, found {archived_count}."
                )

            # Remove only the redundant copies.
            cursor.execute("""
                WITH ranked AS (
                    SELECT
                        ground_truth_id,
                        ROW_NUMBER() OVER (
                            PARTITION BY validation_id
                            ORDER BY labeled_at ASC NULLS LAST,
                                     ground_truth_id ASC
                        ) AS record_rank
                    FROM ground_truth_labels
                )
                DELETE FROM ground_truth_labels g
                USING ranked r
                WHERE g.ground_truth_id = r.ground_truth_id
                  AND r.record_rank > 1
            """)

            deleted_count = cursor.rowcount

            if deleted_count != 2:
                raise RuntimeError(
                    f"Expected to delete 2 records, deleted {deleted_count}."
                )

            # Final duplicate check.
            cursor.execute("""
                SELECT COUNT(*)
                FROM (
                    SELECT validation_id
                    FROM ground_truth_labels
                    GROUP BY validation_id
                    HAVING COUNT(*) > 1
                ) duplicates
            """)

            remaining_duplicates = cursor.fetchone()[0]

            if remaining_duplicates != 0:
                raise RuntimeError(
                    "Duplicate validation IDs remain."
                )

        connection.commit()

        print("Ground-truth reconciliation: PASS")
        print("Archived records: 2")
        print("Removed redundant records: 2")
        print("Remaining duplicate groups: 0")
        print("Original earliest record preserved.")
        print("Transaction committed.")

    except Exception:
        connection.rollback()
        print("Reconciliation failed. Transaction rolled back.")
        raise

    finally:
        connection.close()


if __name__ == "__main__":
    main()
