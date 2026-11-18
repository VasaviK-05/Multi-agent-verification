"""Read-only catalog verification for generated-answer session associations."""
MIGRATION_013 = "013_generated_answer_sessions.sql"


def generated_answer_session_problems(cursor):
    """Return mismatches; never execute migration SQL or change tracking."""
    problems = []
    cursor.execute("""
        SELECT data_type, is_nullable, udt_schema, udt_name
        FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'questions_answers'
          AND column_name = 'session_id'
    """)
    if cursor.fetchone() != ('uuid', 'YES', 'pg_catalog', 'uuid'):
        problems.append("questions_answers.session_id must be nullable UUID")

    cursor.execute("""
        SELECT ARRAY(SELECT a.attname FROM unnest(c.conkey) WITH ORDINALITY k(num, pos)
                     JOIN pg_attribute a ON a.attrelid=c.conrelid AND a.attnum=k.num ORDER BY k.pos),
               rn.nspname, rt.relname,
               ARRAY(SELECT a.attname FROM unnest(c.confkey) WITH ORDINALITY k(num, pos)
                     JOIN pg_attribute a ON a.attrelid=c.confrelid AND a.attnum=k.num ORDER BY k.pos),
               c.confdeltype, c.convalidated
        FROM pg_constraint c
        JOIN pg_class t ON t.oid=c.conrelid
        JOIN pg_namespace n ON n.oid=t.relnamespace
        JOIN pg_class rt ON rt.oid=c.confrelid
        JOIN pg_namespace rn ON rn.oid=rt.relnamespace
        WHERE n.nspname='public' AND t.relname='questions_answers'
          AND c.conname='questions_answers_session_fk' AND c.contype='f'
    """)
    if cursor.fetchone() != (['session_id'], 'public', 'sessions', ['session_id'], 'n', True):
        problems.append("questions_answers_session_fk must be validated session_id -> public.sessions(session_id) ON DELETE SET NULL")

    cursor.execute("""
        SELECT i.indisvalid, i.indisready, am.amname, i.indisunique,
               i.indnkeyatts, i.indnatts, i.indpred IS NULL, i.indexprs IS NULL,
               ARRAY(SELECT pg_get_indexdef(i.indexrelid, k, true)
                     FROM generate_series(1, i.indnkeyatts) k ORDER BY k)
        FROM pg_index i
        JOIN pg_class ix ON ix.oid=i.indexrelid
        JOIN pg_class t ON t.oid=i.indrelid
        JOIN pg_namespace n ON n.oid=t.relnamespace
        JOIN pg_am am ON am.oid=ix.relam
        WHERE n.nspname='public' AND t.relname='questions_answers'
          AND ix.relname='idx_questions_answers_session_created'
    """)
    if cursor.fetchone() != (True, True, 'btree', False, 3, 3, True, True,
                             ['session_id', 'created_at', 'id']):
        problems.append("idx_questions_answers_session_created must be a valid ready nonunique nonpartial btree on (session_id, created_at, id)")
    return problems
