
-- ============================================================
-- Verifier cost measurement persistence
-- ============================================================

-- 1. Measurement environment and configuration
CREATE TABLE verifier_measurement_setups (
    setup_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    setup_fingerprint TEXT NOT NULL UNIQUE,
    verifier_name TEXT NOT NULL,

    verifier_implementation TEXT,
    implementation_fingerprint TEXT,
    verifier_config JSONB NOT NULL DEFAULT '{}'::jsonb,
    config_fingerprint TEXT,

    model_fingerprint TEXT,
    corpus_fingerprint TEXT,
    index_fingerprint TEXT,

    machine_config JSONB NOT NULL DEFAULT '{}'::jsonb,
    runtime_config JSONB NOT NULL DEFAULT '{}'::jsonb,
    concurrency INTEGER,
    cache_config JSONB NOT NULL DEFAULT '{}'::jsonb,

    code_revision TEXT,
    dependency_versions JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT verifier_setup_concurrency_positive
        CHECK (concurrency IS NULL OR concurrency > 0)
);

-- 2. Individual verifier attempts
CREATE TABLE verifier_cost_attempts (
    attempt_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id UUID NOT NULL,
    verifier_name TEXT NOT NULL,
    setup_id UUID NOT NULL,
    dataset_id TEXT,

    duration_ms DOUBLE PRECISION,
    outcome TEXT NOT NULL,
    error_type TEXT,
    error_message TEXT,

    is_warmup BOOLEAN NOT NULL DEFAULT FALSE,
    measurement_purpose TEXT NOT NULL DEFAULT 'calibration',
    data_role TEXT NOT NULL DEFAULT 'development',

    source_verifier_result_id UUID,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT verifier_attempt_setup_fk
        FOREIGN KEY (setup_id)
        REFERENCES verifier_measurement_setups(setup_id),

    CONSTRAINT verifier_attempt_source_result_fk
        FOREIGN KEY (source_verifier_result_id)
        REFERENCES verifier_outputs(verifier_result_id),

    CONSTRAINT verifier_attempt_duration_nonnegative
        CHECK (duration_ms IS NULL OR duration_ms >= 0),

    CONSTRAINT verifier_attempt_outcome_valid
        CHECK (
            outcome IN ('returned', 'failure', 'timeout', 'interrupted')
        ),

    CONSTRAINT verifier_attempt_purpose_valid
        CHECK (
            measurement_purpose IN ('calibration', 'benchmark', 'production')
        ),

    CONSTRAINT verifier_attempt_role_valid
        CHECK (
            data_role IN (
                'history', 'development', 'validation', 'test', 'production'
            )
        )
);

CREATE INDEX verifier_cost_attempts_run_idx
    ON verifier_cost_attempts(run_id);

CREATE INDEX verifier_cost_attempts_verifier_time_idx
    ON verifier_cost_attempts(verifier_name, recorded_at);

CREATE INDEX verifier_cost_attempts_setup_idx
    ON verifier_cost_attempts(setup_id);

-- 3. Calculated cost per verifier
CREATE TABLE verifier_cost_estimates (
    estimate_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    calibration_id UUID NOT NULL,
    verifier_name TEXT NOT NULL,
    setup_id UUID NOT NULL,
    dataset_id TEXT,

    mean_attempt_cost_ms DOUBLE PRECISION,
    median_duration_ms DOUBLE PRECISION,
    p95_duration_ms DOUBLE PRECISION,

    attempt_count INTEGER NOT NULL,
    failure_count INTEGER NOT NULL,
    include_warmups BOOLEAN NOT NULL DEFAULT FALSE,

    estimator_version TEXT NOT NULL,
    input_digest TEXT NOT NULL,
    source_attempt_ids UUID[] NOT NULL,

    calculated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT verifier_cost_estimate_setup_fk
        FOREIGN KEY (setup_id)
        REFERENCES verifier_measurement_setups(setup_id),

    CONSTRAINT verifier_cost_estimate_counts_valid
        CHECK (
            attempt_count >= 0
            AND failure_count >= 0
            AND failure_count <= attempt_count
        ),

    CONSTRAINT verifier_cost_estimate_durations_nonnegative
        CHECK (
            (mean_attempt_cost_ms IS NULL OR mean_attempt_cost_ms >= 0)
            AND (median_duration_ms IS NULL OR median_duration_ms >= 0)
            AND (p95_duration_ms IS NULL OR p95_duration_ms >= 0)
        )
);

CREATE INDEX verifier_cost_estimates_lookup_idx
    ON verifier_cost_estimates(
        verifier_name, setup_id, calculated_at DESC
    );
