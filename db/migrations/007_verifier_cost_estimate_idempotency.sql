-- Make verifier cost estimate retries idempotent.
-- Refuse migration if duplicate estimates already exist.

DO $$
BEGIN
    IF EXISTS (
        SELECT calibration_id, input_digest
        FROM verifier_cost_estimates
        GROUP BY calibration_id, input_digest
        HAVING COUNT(*) > 1
    ) THEN
        RAISE EXCEPTION
            'Duplicate verifier cost estimates exist. '
            'Resolve them before applying this migration.';
    END IF;
END $$;

ALTER TABLE verifier_cost_estimates
ADD CONSTRAINT verifier_cost_estimates_calibration_digest_unique
UNIQUE (calibration_id, input_digest);
