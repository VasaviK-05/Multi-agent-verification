# Generated-answer session association

Apply `013_generated_answer_sessions.sql` once, in numerical migration order, before deploying this backend/frontend change. Stop the application first and obtain database-owner approval. Use the existing secure PostgreSQL credential mechanism; do not put passwords in command arguments. For example, with approved connection credentials already supplied securely:

```powershell
psql --host localhost --port 5432 --dbname multi_agent_review_test --username YOUR_APPROVED_USER --set ON_ERROR_STOP=1 --file db/migrations/013_generated_answer_sessions.sql
```

Migration 013 was successfully applied and verified in the development database `multi_agent_review_test` on 18 November 2026. Do not rerun it in that database. This status does not establish application in any other environment: each other database must independently verify its schema and migration history, and explicitly apply migration 013 only if it is not already applied. It adds a nullable foreign key and index. Existing answers remain unassociated; no session can safely be inferred for them. Old clients may omit session_id. Session deletion nulls the association rather than deleting generated answers. History retains validation rows and suppresses a generated-only row when the same question_id has a validation row in the same session. Multiple existing validation attempts remain visible as before.

Deployment requires the migration first: the updated insert and history query reference the new column. DDL/index construction can lock the table; schedule accordingly. Roll back application code before removing the column. The SQL file documents reverse DDL; reversing discards session associations but preserves answers. No migration runner or automatic startup migration is introduced.

Generated-only history has history_state=generated_only and null validation identity, status, score and domain. This is generation persistence, not validation. Generation provenance remains response-only in the separate two-request flow. Browser refresh reloads session history; selection of the exact previous session is not persisted across reloads.
