ALTER TABLE validation_audits
    ADD COLUMN IF NOT EXISTS selection_plan JSONB
        NOT NULL DEFAULT '{}'::jsonb,
    ADD COLUMN IF NOT EXISTS run_summary JSONB
        NOT NULL DEFAULT '{}'::jsonb;
