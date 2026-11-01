-- ============================================================
-- Ground truth idempotency
-- One ground-truth record per validation
-- ============================================================

DO $$
BEGIN
    IF EXISTS (
        SELECT validation_id
        FROM ground_truth_labels
        GROUP BY validation_id
        HAVING COUNT(*) > 1
    ) THEN
        RAISE EXCEPTION
            'Duplicate ground-truth records exist. '
            'Resolve them before applying this migration.';
    END IF;
END $$;

ALTER TABLE ground_truth_labels
ADD CONSTRAINT ground_truth_validation_id_unique
UNIQUE (validation_id);