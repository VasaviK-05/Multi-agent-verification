CREATE TABLE IF NOT EXISTS reputation_manager_state (
    state_id SMALLINT PRIMARY KEY DEFAULT 1,
    schema_version INTEGER NOT NULL,
    state JSONB NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT reputation_manager_state_singleton
        CHECK (state_id = 1),

    CONSTRAINT reputation_manager_state_version_positive
        CHECK (schema_version > 0),

    CONSTRAINT reputation_manager_state_object
        CHECK (jsonb_typeof(state) = 'object')
);