-- Nullable association preserves existing generated answers and clients.
BEGIN;
ALTER TABLE questions_answers ADD COLUMN session_id UUID;
ALTER TABLE questions_answers ADD CONSTRAINT questions_answers_session_fk
    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE SET NULL;
CREATE INDEX idx_questions_answers_session_created
    ON questions_answers (session_id, created_at, id);
COMMIT;
-- Rollback (only when intentionally discarding these associations):
-- DROP INDEX idx_questions_answers_session_created;
-- ALTER TABLE questions_answers DROP CONSTRAINT questions_answers_session_fk;
-- ALTER TABLE questions_answers DROP COLUMN session_id;
