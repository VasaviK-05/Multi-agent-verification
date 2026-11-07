-- A report identity can be a parent UUID (atomic execution) or a
-- component-scoped SHA-256 content ID (Compound execution).
-- Preserve existing UUID values as their canonical text representation.
DO $$
DECLARE
    existing_type TEXT;
BEGIN
    SELECT data_type
    INTO existing_type
    FROM information_schema.columns
    WHERE table_schema = 'public'
      AND table_name = 'live_verifier_attempts'
      AND column_name = 'report_validation_id';

    IF existing_type IS NULL THEN
        RAISE EXCEPTION
            'live_verifier_attempts.report_validation_id is missing';
    ELSIF existing_type = 'uuid' THEN
        ALTER TABLE public.live_verifier_attempts
            ALTER COLUMN report_validation_id TYPE TEXT
            USING report_validation_id::TEXT;
    ELSIF existing_type <> 'text' THEN
        RAISE EXCEPTION
            'Unsupported type for live_verifier_attempts.report_validation_id: %',
            existing_type;
    END IF;
END
$$;
