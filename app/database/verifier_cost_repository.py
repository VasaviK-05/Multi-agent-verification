
import hashlib
import json
import math
import statistics
from uuid import uuid4

from database import get_connection


VALID_OUTCOMES = {"returned", "failure", "timeout", "interrupted"}
VALID_PURPOSES = {"calibration", "benchmark", "production"}
VALID_ROLES = {"history", "development", "validation", "test", "production"}


def _save_one(sql: str, params: tuple, result_column: str) -> str:
    connection = None
    cursor = None

    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute(sql, params)
        saved_id = str(cursor.fetchone()[0])
        connection.commit()
        return saved_id
    except Exception:
        if connection:
            connection.rollback()
        raise
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


def save_measurement_setup(
    *,
    verifier_name: str,
    setup_fingerprint: str,
    verifier_config: dict | None = None,
    verifier_implementation: str | None = None,
    implementation_fingerprint: str | None = None,
    config_fingerprint: str | None = None,
    model_fingerprint: str | None = None,
    corpus_fingerprint: str | None = None,
    index_fingerprint: str | None = None,
    machine_config: dict | None = None,
    runtime_config: dict | None = None,
    concurrency: int | None = None,
    cache_config: dict | None = None,
    code_revision: str | None = None,
    dependency_versions: dict | None = None,
) -> str:
    """Persist a setup; repeated fingerprints return the existing setup ID."""
    sql = """
        INSERT INTO verifier_measurement_setups (
            setup_id, setup_fingerprint, verifier_name,
            verifier_implementation, implementation_fingerprint,
            verifier_config, config_fingerprint,
            model_fingerprint, corpus_fingerprint, index_fingerprint,
            machine_config, runtime_config, concurrency, cache_config,
            code_revision, dependency_versions
        )
        VALUES (
            %s, %s, %s, %s, %s, %s::jsonb, %s, %s, %s, %s,
            %s::jsonb, %s::jsonb, %s, %s::jsonb, %s, %s::jsonb
        )
        ON CONFLICT (setup_fingerprint)
        DO UPDATE SET setup_fingerprint = EXCLUDED.setup_fingerprint
        RETURNING setup_id
    """
    params = (
        str(uuid4()), setup_fingerprint, verifier_name,
        verifier_implementation, implementation_fingerprint,
        json.dumps(verifier_config or {}), config_fingerprint,
        model_fingerprint, corpus_fingerprint, index_fingerprint,
        json.dumps(machine_config or {}), json.dumps(runtime_config or {}),
        concurrency, json.dumps(cache_config or {}), code_revision,
        json.dumps(dependency_versions or {}),
    )
    return _save_one(sql, params, "setup_id")


def save_verifier_attempt(
    *,
    run_id: str,
    verifier_name: str,
    setup_id: str,
    outcome: str,
    duration_ms: float | None = None,
    dataset_id: str | None = None,
    error_type: str | None = None,
    error_message: str | None = None,
    is_warmup: bool = False,
    measurement_purpose: str = "calibration",
    data_role: str = "development",
    source_verifier_result_id: str | None = None,
    metadata: dict | None = None,
    attempt_id: str | None = None,
) -> str:
    """Persist one attempt, including failed or untimed attempts."""
    if outcome not in VALID_OUTCOMES:
        raise ValueError(f"Invalid outcome: {outcome}")
    if measurement_purpose not in VALID_PURPOSES:
        raise ValueError(f"Invalid measurement purpose: {measurement_purpose}")
    if data_role not in VALID_ROLES:
        raise ValueError(f"Invalid data role: {data_role}")
    if duration_ms is not None and duration_ms < 0:
        raise ValueError("duration_ms cannot be negative")

    sql = """
        INSERT INTO verifier_cost_attempts (
            attempt_id, run_id, verifier_name, setup_id, dataset_id,
            duration_ms, outcome, error_type, error_message,
            is_warmup, measurement_purpose, data_role,
            source_verifier_result_id, metadata
        )
        VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s::jsonb
        )
        RETURNING attempt_id
    """
    params = (
        attempt_id or str(uuid4()), run_id, verifier_name, setup_id,
        dataset_id, duration_ms, outcome, error_type, error_message,
        is_warmup, measurement_purpose, data_role,
        source_verifier_result_id, json.dumps(metadata or {}),
    )
    return _save_one(sql, params, "attempt_id")


def save_cost_estimate(
    *,
    calibration_id: str,
    verifier_name: str,
    setup_id: str,
    attempt_count: int,
    failure_count: int,
    estimator_version: str,
    input_digest: str,
    source_attempt_ids: list[str],
    dataset_id: str | None = None,
    mean_attempt_cost_ms: float | None = None,
    median_duration_ms: float | None = None,
    p95_duration_ms: float | None = None,
    include_warmups: bool = False,
    estimate_id: str | None = None,
) -> str:
    """Persist an estimate with the IDs of its source attempts."""
    if attempt_count < 0 or failure_count < 0 or failure_count > attempt_count:
        raise ValueError("Invalid attempt_count/failure_count")

    for value in (mean_attempt_cost_ms, median_duration_ms, p95_duration_ms):
        if value is not None and value < 0:
            raise ValueError("Cost and duration values cannot be negative")

    sql = """
        INSERT INTO verifier_cost_estimates (
            estimate_id, calibration_id, verifier_name, setup_id,
            dataset_id, mean_attempt_cost_ms, median_duration_ms,
            p95_duration_ms, attempt_count, failure_count,
            include_warmups, estimator_version, input_digest,
            source_attempt_ids
        )
        VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s::uuid[]
        )
        RETURNING estimate_id
    """
    params = (
        estimate_id or str(uuid4()), calibration_id, verifier_name, setup_id,
        dataset_id, mean_attempt_cost_ms, median_duration_ms, p95_duration_ms,
        attempt_count, failure_count, include_warmups, estimator_version,
        input_digest, source_attempt_ids,
    )
    return _save_one(sql, params, "estimate_id")


def calculate_and_save_cost_estimate(
    *,
    calibration_id: str,
    verifier_name: str,
    setup_id: str,
    estimator_version: str = "verifier-cost-v1",
    dataset_id: str | None = None,
    include_warmups: bool = False,
    measurement_purpose: str = "calibration",
    data_role: str = "development",
) -> str:
    """Calculate cost statistics from persisted attempts and save the estimate."""
    if measurement_purpose not in VALID_PURPOSES:
        raise ValueError(f"Invalid measurement purpose: {measurement_purpose}")
    if data_role not in VALID_ROLES:
        raise ValueError(f"Invalid data role: {data_role}")

    connection = None
    cursor = None

    try:
        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT attempt_id, duration_ms, outcome, is_warmup,
                   dataset_id, measurement_purpose, data_role
            FROM verifier_cost_attempts
            WHERE verifier_name = %s
              AND setup_id = %s
              AND measurement_purpose = %s
              AND data_role = %s
              AND (%s IS NULL OR dataset_id = %s)
              AND (%s OR is_warmup = FALSE)
            ORDER BY recorded_at, attempt_id
            """,
            (
                verifier_name,
                setup_id,
                measurement_purpose,
                data_role,
                dataset_id,
                dataset_id,
                include_warmups,
            ),
        )
        rows = cursor.fetchall()

        if not rows:
            raise ValueError("No matching verifier attempts found.")

        source_attempt_ids = [str(row[0]) for row in rows]
        durations = [
            float(row[1])
            for row in rows
            if row[1] is not None
        ]

        failure_outcomes = {"failure", "timeout", "interrupted"}
        failure_count = sum(row[2] in failure_outcomes for row in rows)

        mean_duration = statistics.mean(durations) if durations else None
        median_duration = statistics.median(durations) if durations else None

        if durations:
            sorted_durations = sorted(durations)
            p95_index = math.ceil(0.95 * len(sorted_durations)) - 1
            p95_duration = sorted_durations[p95_index]
        else:
            p95_duration = None

        digest_payload = {
            "verifier_name": verifier_name,
            "setup_id": str(setup_id),
            "dataset_id": dataset_id,
            "measurement_purpose": measurement_purpose,
            "data_role": data_role,
            "include_warmups": include_warmups,
            "estimator_version": estimator_version,
            "attempts": [
                {
                    "attempt_id": str(row[0]),
                    "duration_ms": float(row[1]) if row[1] is not None else None,
                    "outcome": row[2],
                    "is_warmup": row[3],
                    "dataset_id": row[4],
                    "measurement_purpose": row[5],
                    "data_role": row[6],
                }
                for row in rows
            ],
        }
        input_digest = hashlib.sha256(
            json.dumps(
                digest_payload,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

    return save_cost_estimate(
        calibration_id=calibration_id,
        verifier_name=verifier_name,
        setup_id=setup_id,
        dataset_id=dataset_id,
        mean_attempt_cost_ms=mean_duration,
        median_duration_ms=median_duration,
        p95_duration_ms=p95_duration,
        attempt_count=len(rows),
        failure_count=failure_count,
        include_warmups=include_warmups,
        estimator_version=estimator_version,
        input_digest=input_digest,
        source_attempt_ids=source_attempt_ids,
    )
