
import os
from pathlib import Path

import psycopg2
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent

MIGRATION_FILES = [
    "001_review_updates.sql",
    "002_reputation_state.sql",
    "003_validation_audit.sql",
    "004_audit_execution_metadata.sql",
    "005_verifier_cost_measurements.sql",
]

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

def read_schema_inventory(cursor):
    cursor.execute("""
        SELECT table_name, column_name
        FROM information_schema.columns
        WHERE table_schema = 'public'
    """)
    columns = {}
    for table, column in cursor.fetchall():
        columns.setdefault(table, set()).add(column)

    cursor.execute("""
        SELECT conname
        FROM pg_constraint
        WHERE connamespace = 'public'::regnamespace
    """)
    constraints = {row[0] for row in cursor.fetchall()}

    cursor.execute("""
        SELECT indexname
        FROM pg_indexes
        WHERE schemaname = 'public'
    """)
    indexes = {row[0] for row in cursor.fetchall()}

    return columns, constraints, indexes


def verify_migration(filename, columns, constraints, indexes):
    problems = []

    for table, required in REQUIRED_COLUMNS.get(filename, {}).items():
        missing = required - columns.get(table, set())
        if missing:
            problems.append(f"{table} missing columns {sorted(missing)}")

    missing_constraints = (
        REQUIRED_CONSTRAINTS.get(filename, set()) - constraints
    )
    if missing_constraints:
        problems.append(
            f"missing constraints {sorted(missing_constraints)}"
        )

    missing_indexes = REQUIRED_INDEXES.get(filename, set()) - indexes
    if missing_indexes:
        problems.append(f"missing indexes {sorted(missing_indexes)}")

    if filename == "002_reputation_state.sql":
        # The migration creates a singleton state table with validation checks.
        if "reputation_manager_state_singleton" not in constraints:
            problems.append("missing reputation_manager_state_singleton")
        if "reputation_manager_state_version_positive" not in constraints:
            problems.append("missing reputation_manager_state_version_positive")
        if "reputation_manager_state_object" not in constraints:
            problems.append("missing reputation_manager_state_object")

    return problems


def main():
    load_dotenv(ROOT / ".env")

    required_env = ["DB_HOST", "DB_NAME", "DB_USER", "DB_PASSWORD"]
    missing_env = [name for name in required_env if not os.getenv(name)]
    if missing_env:
        raise RuntimeError(
            f"Missing database settings: {', '.join(missing_env)}"
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
                if cursor.fetchone()[0] is None:
                    raise RuntimeError(
                        "Core schema is missing. This script only reconciles "
                        "history for an existing database."
                    )

                columns, constraints, indexes = read_schema_inventory(cursor)

                # Validate every migration before writing any history.
                errors = {}
                for filename in MIGRATION_FILES:
                    problems = verify_migration(
                        filename, columns, constraints, indexes
                    )
                    if problems:
                        errors[filename] = problems

                if errors:
                    details = "\n".join(
                        f"- {name}: {'; '.join(problems)}"
                        for name, problems in errors.items()
                    )
                    raise RuntimeError(
                        "Schema verification failed. No migration history "
                        f"was written:\n{details}"
                    )

                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS schema_migrations (
                        migration_name TEXT PRIMARY KEY,
                        applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                    )
                """)

                cursor.execute(
                    "SELECT migration_name FROM schema_migrations"
                )
                recorded = {row[0] for row in cursor.fetchall()}

                unknown = recorded - set(MIGRATION_FILES)
                if unknown:
                    raise RuntimeError(
                        "Unknown migration records found; refusing to "
                        f"change history: {sorted(unknown)}"
                    )

                for filename in MIGRATION_FILES:
                    if filename in recorded:
                        print(f"Already recorded: {filename}")
                    else:
                        cursor.execute(
                            """
                            INSERT INTO schema_migrations (migration_name)
                            VALUES (%s)
                            """,
                            (filename,),
                        )
                        print(f"Verified and recorded: {filename}")

        print(
            "Migration history reconciliation completed. "
            "No migration SQL was executed."
        )

    finally:
        connection.close()


if __name__ == "__main__":
    main()
