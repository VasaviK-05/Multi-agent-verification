-- ============================================================
-- 010: Execution leases and heartbeat-based crash recovery
-- ============================================================

ALTER TABLE validation_executions
    ADD COLUMN lease_token UUID,
    ADD COLUMN worker_id TEXT,
    ADD COLUMN heartbeat_at TIMESTAMPTZ,
    ADD COLUMN lease_expires_at TIMESTAMPTZ;

ALTER TABLE validation_executions
    ADD CONSTRAINT validation_execution_lease_pair
    CHECK (
        (
            lease_token IS NULL
            AND worker_id IS NULL
            AND heartbeat_at IS NULL
            AND lease_expires_at IS NULL
        )
        OR
        (
            lease_token IS NOT NULL
            AND worker_id IS NOT NULL
            AND length(trim(worker_id)) > 0
            AND heartbeat_at IS NOT NULL
            AND lease_expires_at IS NOT NULL
        )
    );

CREATE INDEX idx_validation_executions_lease_expiry
    ON validation_executions (lease_expires_at)
    WHERE execution_status = 'running';