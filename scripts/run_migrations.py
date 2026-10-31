
import os
from pathlib import Path

import psycopg2
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
SCHEMA_FILE = ROOT / "db" / "schema.sql"
MIGRATIONS_DIR = ROOT / "db" / "migrations"

MIGRATIONS = [
    "001_review_updates.sql",
    "002_reputation_state.sql",
    "003_validation_audit.sql",
    "004_audit_execution_metadata.sql",
    "005_verifier_cost_measurements.sql",
]

# Required schema evidence for adopting migrations on an existing database.
REQUIRED_COLUMNS = {
    "001_review_updates.sql": {
        "validation_records": {
            "difficulty", "selected_verifiers", "early_stop_reason",
            "signed_score", "question_id",
        },
        "verifier_outputs": {
            "latency_ms", "execution_order", "question_id",
        },
        "ground_truth_labels": {"question_id"},
    },
    "002_reputation_state.sql": {
        "reputation_manager_state": {
            "state_id", "schema_version", "state", "updated_at",
        },
    },
    "003_validation_audit.sql": {
        "validation_audits": {
            "audit_id", "validation_id", "question_id", "session_id",
            "run_status", "started_at", "completed_at", "policy_version",
            "selected_strategy", "execution_contract",
            "reputation_snapshot", "reputation_snapshot_id",
            "selected_verifiers", "ranking_explanations",
            "decision_summary", "coverage_outcomes", "execution_costs",
            "failure_details", "created_at", "updated_at",
        },
    },
    "004_audit_execution_metadata.sql": {
        "validation_audits": {"selection_plan", "run_summary"},
    },
    "005_verifier_cost_measurements.sql": {
        "verifier_measurement_setups": {
            "setup_id", "setup_fingerprint", "verifier_name",
            "verifier_implementation", "implementation_fingerprint",
            "verifier_config", "config_fingerprint", "model_fingerprint",
            "corpus_fingerprint", "index_fingerprint", "machine_config",
            "runtime_config", "concurrency", "cache_config", "code_revision",
            "dependency_versions", "created_at",
        },
        "verifier_cost_attempts": {
            "attempt_id", "run_id", "verifier_name", "setup_id",
            "dataset_id", "duration_ms", "outcome", "error_type",
            "error_message", "is_warmup", "measurement_purpose",
            "data_role", "source_verifier_result_id", "metadata",
            "recorded_at",
        },
        "verifier_cost_estimates": {
            "estimate_id", "calibration_id", "verifier_name", "setup_id",
            "dataset_id", "mean_attempt_cost_ms", "median_duration_ms",
            "p95_duration_ms", "attempt_count", "failure_count",
            "include_warmups", "estimator_version", "input_digest",
            "source_attempt_ids", "calculated_at",
        },
    },
}

REQUIRED_CONSTRAINTS = {
    "001_review_updates.sql": {
        "fk_validation_question",
        "fk_verifier_question",
        "fk_ground_truth_validation",
        "fk_ground_truth_question",
        "feedback_validation_id_unique",
    },
    "002_reputation_state.sql": {
        "reputation_manager_state_singleton",
        "reputation_manager_state_version_positive",
        "reputation_manager_state_object",
    },
    "003_validation_audit.sql": {
        "validation_audits_validation_fk",
        "validation_audits_question_fk",
        "validation_audits_session_fk",
        "validation_audits_status_check",
        "validation_audits_contract_object",
        "validation_audits_selected_verifiers_array",
        "validation_audits_ranking_array",
        "validation_audits_decision_object",
        "validation_audits_coverage_object",
        "validation_audits_costs_object",
        "validation_audits_failures_array",
    },
    "005_verifier_cost_measurements.sql": {
        "verifier_measurement_setups_pkey",
        "verifier_measurement_setups_setup_fingerprint_key",
        "verifier_setup_concurrency_positive",
        "verifier_cost_attempts_pkey",
        "verifier_attempt_setup_fk",
        "verifier_attempt_source_result_fk",
        "verifier_attempt_duration_nonnegative",
        "verifier_attempt_outcome_valid",
        "verifier_attempt_purpose_valid",
        "verifier_attempt_role_valid",
        "verifier_cost_estimates_pkey",
        "verifier_cost_estimate_setup_fk",
        "verifier_cost_estimate_counts_valid",
        "verifier_cost_estimate_durations_nonnegative",
    },
}

REQUIRED_INDEXES = {
    "003_validation_audit.sql": {
        "idx_validation_audits_question_id",
        "idx_validation_audits_session_id",
        "idx_validation_audits_run_status",
        "idx_validation_audits_created_at",
    },
    "005_verifier_cost_measurements.sql": {
        "verifier_cost_attempts_run_idx",
        "verifier_cost_attempts_setup_idx",
        "verifier_cost_attempts_verifier_time_idx",
        "verifier_cost_estimates_lookup_idx",
    },
}


def get_existing_columns(cursor):
    cursor.execute("""
        SELECT table_name, column_name
        FROM information_schema.columns
        WHERE table_schema = 'public'
    """)
    columns = {}
    for table_name, column_name in cursor.fetchall():
        columns.setdefault(table_name, set()).add(column_name)
    return columns


def get_existing_constraints(cursor):
    cursor.execute("""
        SELECT conname
        FROM pg_constraint
        WHERE connamespace = 'public'::regnamespace
    """)
    return {row[0] for row in cursor.fetchall()}


def get_existing_indexes(cursor):
    cursor.execute("""
        SELECT indexname
        FROM pg_indexes
        WHERE schemaname = 'public'
    """)
    return {row[0] for row in cursor.fetchall()}


def verify_migration_schema(cursor, filename):
    columns = get_existing_columns(cursor)
    constraints = get_existing_constraints(cursor)
    indexes = get_existing_indexes(cursor)

    missing = []

    for table, expected in REQUIRED_COLUMNS.get(filename, {}).items():
        absent = expected - columns.get(table, set())
        if absent:
            missing.append(f"{table} columns: {sorted(absent)}")

    absent_constraints = (
        REQUIRED_CONSTRAINTS.get(filename, set()) - constraints
    )
    if absent_constraints:
        missing.append(f"constraints: {sorted(absent_constraints)}")

    absent_indexes = REQUIRED_INDEXES.get(filename, set()) - indexes
    if absent_indexes:
        missing.append(f"indexes: {sorted(absent_indexes)}")

    if missing:
        raise RuntimeError(
            f"Cannot safely adopt {filename}; schema checks failed: "
            + "; ".join(missing)
        )


def main():
    load_dotenv(ROOT / ".env")

    required = ["DB_HOST", "DB_NAME", "DB_USER", "DB_PASSWORD"]
    missing = [key for key in required if not os.getenv(key)]
    if missing:
        raise RuntimeError(
            f"Missing database settings in .env: {', '.join(missing)}"
        )

    connection = psycopg2.connect(
        host=os.getenv("DB_HOST"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        port=os.getenv("DB_PORT", "5432"),
    )

    try:
        with connection:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT to_regclass('public.questions_answers')
                """)
                is_initialized = cursor.fetchone()[0] is not None

                if not is_initialized:
                    cursor.execute(
                        SCHEMA_FILE.read_text(encoding="utf-8")
                    )
                    print("Applied base schema: db/schema.sql")

                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS schema_migrations (
                            migration_name TEXT PRIMARY KEY,
                            applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                        )
                    """)

                    for filename in MIGRATIONS:
                        sql_path = MIGRATIONS_DIR / filename
                        cursor.execute(
                            sql_path.read_text(encoding="utf-8")
                        )
                        cursor.execute(
                            """
                            INSERT INTO schema_migrations (migration_name)
                            VALUES (%s)
                            """,
                            (filename,),
                        )
                        print(f"Applied: {filename}")

                else:
                    print(
                        "Existing database detected; checking migration history."
                    )

                    cursor.execute("""
                        SELECT to_regclass('public.schema_migrations')
                    """)
                    history_exists = cursor.fetchone()[0] is not None

                    if not history_exists:
                        cursor.execute("""
                            CREATE TABLE schema_migrations (
                                migration_name TEXT PRIMARY KEY,
                                applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                            )
                        """)
                        print("Created schema_migrations table.")

                cursor.execute(
                    "SELECT migration_name FROM schema_migrations"
                )
                recorded = {row[0] for row in cursor.fetchall()}

                unknown = recorded - set(MIGRATIONS)
                if unknown:
                    raise RuntimeError(
                        "Unknown migration records found; refusing to "
                        f"change history: {sorted(unknown)}"
                    )

                # Verify every migration before changing migration history.
                for filename in MIGRATIONS:
                    verify_migration_schema(cursor, filename)
                    print(f"Schema verified: {filename}")

                # Only after all checks pass, record missing migrations.
                for filename in MIGRATIONS:
                    if filename in recorded:
                        print(f"Already recorded: {filename}")
                        continue

                    cursor.execute(
                        """
                        INSERT INTO schema_migrations (migration_name)
                        VALUES (%s)
                        """,
                        (filename,),
                    )
                    print(f"Adopted existing migration: {filename}")

                print(
                    "Existing schema verified; no migrations were rerun."
                )

        print("Database migration history reconciled successfully.")

    finally:
        connection.close()


if __name__ == "__main__":
    main()
