-- ============================================================
-- Multi-Agent AI Answer Verification System
-- PostgreSQL Database Schema
-- ============================================================

-- Required for gen_random_uuid()
CREATE EXTENSION IF NOT EXISTS pgcrypto;


-- ============================================================
-- Questions and generated answers
-- ============================================================

CREATE TABLE questions_answers (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);


-- ============================================================
-- Validation sessions
-- ============================================================

CREATE TABLE sessions (
    session_id UUID PRIMARY KEY,
    title TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);


-- ============================================================
-- Validation records
-- ============================================================

CREATE TABLE validation_records (
    validation_id UUID PRIMARY KEY,
    question TEXT NOT NULL,
    generated_answer TEXT NOT NULL,
    context TEXT,
    final_status TEXT,
    final_score DOUBLE PRECISION,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    domain TEXT,
    difficulty TEXT,
    selected_verifiers JSONB,
    early_stop_reason TEXT,
    signed_score DOUBLE PRECISION,
    question_id BIGINT,
    session_id UUID,

    CONSTRAINT fk_validation_session
        FOREIGN KEY (session_id)
        REFERENCES sessions(session_id)
);


-- ============================================================
-- Individual verifier outputs
-- ============================================================

CREATE TABLE verifier_outputs (
    verifier_result_id UUID PRIMARY KEY,
    validation_id UUID NOT NULL,
    verifier_name TEXT NOT NULL,
    score DOUBLE PRECISION,
    passed BOOLEAN,
    reasoning TEXT,
    metadata JSONB,
    latency_ms DOUBLE PRECISION,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    execution_order INTEGER,
    question_id BIGINT,

    FOREIGN KEY (validation_id)
        REFERENCES validation_records(validation_id)
);


-- ============================================================
-- Ground truth labels
-- ============================================================

CREATE TABLE ground_truth_labels (
    ground_truth_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    validation_id UUID NOT NULL,
    label TEXT NOT NULL,
    source TEXT,
    labeled_at TIMESTAMPTZ DEFAULT NOW(),
    question_id BIGINT
);


-- ============================================================
-- Verifier reputation
-- ============================================================

CREATE TABLE verifier_reputation (
    reputation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    verifier_name TEXT NOT NULL,
    domain TEXT NOT NULL,
    alpha DOUBLE PRECISION NOT NULL DEFAULT 1.0,
    beta DOUBLE PRECISION NOT NULL DEFAULT 1.0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT verifier_reputation_verifier_domain_unique
        UNIQUE (verifier_name, domain)
);


-- ============================================================
-- User feedback
-- ============================================================

CREATE TABLE feedback (
    id UUID PRIMARY KEY,
    validation_id UUID NOT NULL,
    is_correct BOOLEAN NOT NULL,
    comment TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),

    FOREIGN KEY (validation_id)
        REFERENCES validation_records(validation_id)
);