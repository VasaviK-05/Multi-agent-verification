-- GameContext.reputation_snapshot_id is a SHA-256 content identifier.
-- Preserve existing UUID values as their canonical text form while allowing
-- the runtime's full 64-character hexadecimal content IDs.
DO $$
DECLARE
    existing_type TEXT;
BEGIN
    SELECT data_type
    INTO existing_type
    FROM information_schema.columns
    WHERE table_schema = 'public'
      AND table_name = 'validation_audits'
      AND column_name = 'reputation_snapshot_id';

    IF existing_type IS NULL THEN
        RAISE EXCEPTION
            'validation_audits.reputation_snapshot_id is missing';
    ELSIF existing_type = 'uuid' THEN
        ALTER TABLE public.validation_audits
            ALTER COLUMN reputation_snapshot_id TYPE TEXT
            USING reputation_snapshot_id::TEXT;
    ELSIF existing_type <> 'text' THEN
        RAISE EXCEPTION
            'Unsupported type for validation_audits.reputation_snapshot_id: %',
            existing_type;
    END IF;
END
$$;
