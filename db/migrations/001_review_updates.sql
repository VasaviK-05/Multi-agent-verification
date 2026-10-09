-- ============================================================
-- Multi-Agent AI Answer Verification System
-- Migration: Review Updates
-- ============================================================

-- Required for gen_random_uuid()
CREATE EXTENSION IF NOT EXISTS pgcrypto;


-- ============================================================
-- 1. Validation record fields
-- ============================================================

ALTER TABLE validation_records
ADD COLUMN IF NOT EXISTS difficulty TEXT;

ALTER TABLE validation_records
ADD COLUMN IF NOT EXISTS selected_verifiers JSONB;

ALTER TABLE validation_records
ADD COLUMN IF NOT EXISTS early_stop_reason TEXT;

ALTER TABLE validation_records
ADD COLUMN IF NOT EXISTS signed_score DOUBLE PRECISION;

ALTER TABLE validation_records
ADD COLUMN IF NOT EXISTS question_id BIGINT;


-- ============================================================
-- 2. Verifier output fields
-- ============================================================

ALTER TABLE verifier_outputs
ADD COLUMN IF NOT EXISTS latency_ms DOUBLE PRECISION;

ALTER TABLE verifier_outputs
ADD COLUMN IF NOT EXISTS execution_order INTEGER;

ALTER TABLE verifier_outputs
ADD COLUMN IF NOT EXISTS question_id BIGINT;


-- ============================================================
-- 3. Ground truth fields
-- ============================================================

ALTER TABLE ground_truth_labels
ADD COLUMN IF NOT EXISTS question_id BIGINT;


-- ============================================================
-- 4. Validation -> Question foreign key
-- ============================================================

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'fk_validation_question'
    ) THEN
        ALTER TABLE validation_records
        ADD CONSTRAINT fk_validation_question
        FOREIGN KEY (question_id)
        REFERENCES questions_answers(id);
    END IF;
END $$;


-- ============================================================
-- 5. Verifier output -> Question foreign key
-- ============================================================

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'fk_verifier_question'
    ) THEN
        ALTER TABLE verifier_outputs
        ADD CONSTRAINT fk_verifier_question
        FOREIGN KEY (question_id)
        REFERENCES questions_answers(id);
    END IF;
END $$;


-- ============================================================
-- 6. Ground truth -> Validation foreign key
-- ============================================================

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'fk_ground_truth_validation'
    ) THEN
        ALTER TABLE ground_truth_labels
        ADD CONSTRAINT fk_ground_truth_validation
        FOREIGN KEY (validation_id)
        REFERENCES validation_records(validation_id);
    END IF;
END $$;


-- ============================================================
-- 7. Ground truth -> Question foreign key
-- ============================================================

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'fk_ground_truth_question'
    ) THEN
        ALTER TABLE ground_truth_labels
        ADD CONSTRAINT fk_ground_truth_question
        FOREIGN KEY (question_id)
        REFERENCES questions_answers(id);
    END IF;
END $$;


-- ============================================================
-- 8. One feedback record per validation
-- ============================================================

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'feedback_validation_id_unique'
    ) THEN
        ALTER TABLE feedback
        ADD CONSTRAINT feedback_validation_id_unique
        UNIQUE (validation_id);
    END IF;
END $$;