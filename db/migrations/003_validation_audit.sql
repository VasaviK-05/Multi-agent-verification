
-- ============================================================
-- Migration: Validation-Level Audit Trail
-- ============================================================

CREATE TABLE IF NOT EXISTS validation_audits (
    audit_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Identity and relationships
    validation_id UUID NOT NULL UNIQUE,
    question_id BIGINT,
    session_id UUID,

    -- Lifecycle
    run_status TEXT NOT NULL DEFAULT 'started',
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,

    -- Reproducibility metadata
    policy_version TEXT,
    selected_strategy TEXT,
    execution_contract JSONB NOT NULL DEFAULT '{}'::jsonb,
    reputation_snapshot JSONB,
    reputation_snapshot_id UUID,

    -- Decision and execution details
    selected_verifiers JSONB NOT NULL DEFAULT '[]'::jsonb,
    ranking_explanations JSONB NOT NULL DEFAULT '[]'::jsonb,
    decision_summary JSONB NOT NULL DEFAULT '{}'::jsonb,
    coverage_outcomes JSONB NOT NULL DEFAULT '{}'::jsonb,
    execution_costs JSONB NOT NULL DEFAULT '{}'::jsonb,
    failure_details JSONB NOT NULL DEFAULT '[]'::jsonb,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT validation_audits_validation_fk
        FOREIGN KEY (validation_id)
        REFERENCES validation_records(validation_id),

    CONSTRAINT validation_audits_question_fk
        FOREIGN KEY (question_id)
        REFERENCES questions_answers(id),

    CONSTRAINT validation_audits_session_fk
        FOREIGN KEY (session_id)
        REFERENCES sessions(session_id),

    CONSTRAINT validation_audits_status_check
        CHECK (
            run_status IN (
                'started',
                'completed',
                'failed',
                'partial'
            )
        ),

    CONSTRAINT validation_audits_contract_object
        CHECK (jsonb_typeof(execution_contract) = 'object'),

    CONSTRAINT validation_audits_selected_verifiers_array
        CHECK (jsonb_typeof(selected_verifiers) = 'array'),

    CONSTRAINT validation_audits_ranking_array
        CHECK (jsonb_typeof(ranking_explanations) = 'array'),

    CONSTRAINT validation_audits_decision_object
        CHECK (jsonb_typeof(decision_summary) = 'object'),

    CONSTRAINT validation_audits_coverage_object
        CHECK (jsonb_typeof(coverage_outcomes) = 'object'),

    CONSTRAINT validation_audits_costs_object
        CHECK (jsonb_typeof(execution_costs) = 'object'),

    CONSTRAINT validation_audits_failures_array
        CHECK (jsonb_typeof(failure_details) = 'array')
);

CREATE INDEX IF NOT EXISTS idx_validation_audits_question_id
    ON validation_audits(question_id);

CREATE INDEX IF NOT EXISTS idx_validation_audits_session_id
    ON validation_audits(session_id);

CREATE INDEX IF NOT EXISTS idx_validation_audits_run_status
    ON validation_audits(run_status);

CREATE INDEX IF NOT EXISTS idx_validation_audits_created_at
    ON validation_audits(created_at);
