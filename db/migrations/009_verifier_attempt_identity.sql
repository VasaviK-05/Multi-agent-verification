-- ============================================================
-- 009: Stable verifier attempt and output identity
-- ============================================================

ALTER TABLE live_verifier_attempts
ADD COLUMN identity_binding JSONB NOT NULL DEFAULT '{}'::jsonb
CHECK (jsonb_typeof(identity_binding) = 'object');


ALTER TABLE verifier_outputs
ADD COLUMN attempt_id UUID;

ALTER TABLE verifier_outputs
ADD CONSTRAINT fk_verifier_output_attempt
FOREIGN KEY (attempt_id)
REFERENCES live_verifier_attempts(attempt_id)
ON DELETE RESTRICT;

ALTER TABLE verifier_outputs
ADD CONSTRAINT verifier_outputs_attempt_unique
UNIQUE (attempt_id);