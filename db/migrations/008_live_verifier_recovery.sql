
-- ============================================================
-- 008: Live verifier execution checkpoint and recovery journal
-- ============================================================

CREATE TABLE validation_executions (
    validation_id UUID PRIMARY KEY
        REFERENCES validation_records(validation_id)
        ON DELETE RESTRICT,

    execution_status TEXT NOT NULL DEFAULT 'initializing'
        CHECK (execution_status IN (
            'initializing', 'ready', 'running',
            'blocked', 'completed', 'failed'
        )),

    execution_mode TEXT NOT NULL,

    request_payload JSONB NOT NULL
        CHECK (jsonb_typeof(request_payload) = 'object'),
    request_digest TEXT NOT NULL,

    analysis_snapshot JSONB
        CHECK (
            analysis_snapshot IS NULL
            OR jsonb_typeof(analysis_snapshot) = 'object'
        ),

    plan_payload JSONB
        CHECK (
            plan_payload IS NULL
            OR jsonb_typeof(plan_payload) = 'object'
        ),
    plan_digest TEXT,

    final_response JSONB
        CHECK (
            final_response IS NULL
            OR jsonb_typeof(final_response) = 'object'
        ),
    final_response_digest TEXT,

    failure_details JSONB NOT NULL DEFAULT '{}'::jsonb
        CHECK (jsonb_typeof(failure_details) = 'object'),

    block_reason TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,

    CONSTRAINT validation_executions_request_digest_valid
        CHECK (request_digest ~ '^[0-9a-f]{64}$'),

    CONSTRAINT validation_executions_plan_digest_valid
        CHECK (
            plan_digest IS NULL
            OR plan_digest ~ '^[0-9a-f]{64}$'
        ),

    CONSTRAINT validation_executions_response_digest_valid
        CHECK (
            final_response_digest IS NULL
            OR final_response_digest ~ '^[0-9a-f]{64}$'
        ),

    CONSTRAINT validation_executions_plan_pair
        CHECK ((plan_payload IS NULL) = (plan_digest IS NULL)),

    CONSTRAINT validation_executions_response_pair
        CHECK (
            (final_response IS NULL)
            = (final_response_digest IS NULL)
        ),

    CONSTRAINT validation_executions_completed_response
        CHECK (
            execution_status <> 'completed'
            OR final_response IS NOT NULL
        )
);

CREATE TABLE live_verifier_attempts (
    attempt_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    validation_id UUID NOT NULL
        REFERENCES validation_executions(validation_id)
        ON DELETE RESTRICT,

    call_key TEXT NOT NULL,
    execution_order INTEGER NOT NULL CHECK (execution_order >= 0),

    verifier_name TEXT NOT NULL,
    component_id TEXT,
    report_validation_id UUID,

    lifecycle_status TEXT NOT NULL DEFAULT 'planned'
        CHECK (lifecycle_status IN (
            'planned', 'started', 'completed',
            'execution_failed', 'unavailable',
            'error', 'ambiguous'
        )),

    outcome TEXT
        CHECK (outcome IN (
            'directional', 'abstention',
            'failed', 'unavailable', 'error'
        )),

    report JSONB
        CHECK (
            report IS NULL
            OR jsonb_typeof(report) = 'object'
        ),
    report_digest TEXT,

    error_type TEXT,
    error_message TEXT,

    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,

    duration_ms DOUBLE PRECISION
        CHECK (
            duration_ms IS NULL
            OR (
                duration_ms >= 0
                AND duration_ms NOT IN (
                    'NaN'::float8,
                    'Infinity'::float8,
                    '-Infinity'::float8
                )
            )
        ),

    estimated_cost DOUBLE PRECISION
        CHECK (
            estimated_cost IS NULL
            OR (
                estimated_cost >= 0
                AND estimated_cost NOT IN (
                    'NaN'::float8,
                    'Infinity'::float8,
                    '-Infinity'::float8
                )
            )
        ),
    cost_units TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT live_attempt_call_key_nonblank
        CHECK (length(trim(call_key)) > 0),

    CONSTRAINT live_attempt_verifier_nonblank
        CHECK (length(trim(verifier_name)) > 0),

    CONSTRAINT live_attempt_identity_unique
        UNIQUE (validation_id, call_key),

    CONSTRAINT live_attempt_order_unique
        UNIQUE (validation_id, execution_order),

    CONSTRAINT live_attempt_report_pair
        CHECK ((report IS NULL) = (report_digest IS NULL)),

    CONSTRAINT live_attempt_report_digest_valid
        CHECK (
            report_digest IS NULL
            OR report_digest ~ '^[0-9a-f]{64}$'
        ),

    CONSTRAINT live_attempt_state_consistency
        CHECK (
            (lifecycle_status = 'planned'
                AND outcome IS NULL
                AND started_at IS NULL
                AND completed_at IS NULL
                AND report IS NULL)
            OR
            (lifecycle_status = 'started'
                AND outcome IS NULL
                AND started_at IS NOT NULL
                AND completed_at IS NULL)
            OR
            (lifecycle_status = 'completed'
                AND outcome IN ('directional', 'abstention')
                AND started_at IS NOT NULL
                AND completed_at IS NOT NULL
                AND report IS NOT NULL)
            OR
            (lifecycle_status = 'execution_failed'
                AND outcome = 'failed'
                AND started_at IS NOT NULL
                AND completed_at IS NOT NULL
                AND report IS NULL)
            OR
            (lifecycle_status = 'unavailable'
                AND outcome = 'unavailable'
                AND started_at IS NOT NULL
                AND completed_at IS NOT NULL
                AND report IS NULL)
            OR
            (lifecycle_status = 'error'
                AND outcome = 'error'
                AND started_at IS NOT NULL
                AND completed_at IS NOT NULL)
            OR
            (lifecycle_status = 'ambiguous'
                AND outcome IS NULL
                AND started_at IS NOT NULL
                AND completed_at IS NULL)
        )
);

CREATE INDEX idx_validation_executions_status
    ON validation_executions (execution_status, updated_at);

CREATE INDEX idx_live_attempts_validation_order
    ON live_verifier_attempts (validation_id, execution_order);

CREATE INDEX idx_live_attempts_status
    ON live_verifier_attempts (lifecycle_status, updated_at);
