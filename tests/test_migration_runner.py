import pytest
from unittest.mock import Mock

from scripts import run_migrations


class FakeCursor:
    def __init__(self):
        self.executed = []
        self.result = None

    def execute(self, query, params=None):
        self.executed.append((query, params))

    def fetchone(self):
        return self.result

    def fetchall(self):
        return []

    def close(self):
        pass


def test_migration_runner_module_loads():
    assert callable(run_migrations.main)
    assert callable(run_migrations.verify_migration_schema)


def test_migration_list_contains_existing_migrations():
    assert run_migrations.MIGRATIONS == [
        "001_review_updates.sql",
        "002_reputation_state.sql",
        "003_validation_audit.sql",
        "004_audit_execution_metadata.sql",
        "005_verifier_cost_measurements.sql",
        "006_ground_truth_idempotency.sql",
        "007_verifier_cost_estimate_idempotency.sql",
    ]


def test_verify_migration_schema_rejects_missing_columns(monkeypatch):
    cursor = FakeCursor()

    monkeypatch.setattr(
        run_migrations,
        "get_existing_columns",
        lambda cursor: {"ground_truth_labels": set()},
    )

    monkeypatch.setattr(
        run_migrations,
        "get_existing_constraints",
        lambda cursor: set(),
    )

    monkeypatch.setattr(
        run_migrations,
        "get_existing_indexes",
        lambda cursor: set(),
    )

    run_migrations.REQUIRED_COLUMNS["test_migration.sql"] = {
        "ground_truth_labels": {"question_id"}
    }

    try:
        with pytest.raises(RuntimeError, match="question_id"):
            run_migrations.verify_migration_schema(
                cursor, "test_migration.sql"
            )
    finally:
        run_migrations.REQUIRED_COLUMNS.pop(
            "test_migration.sql", None
        )


def test_recorded_migration_is_verified_not_executed(monkeypatch):
    cursor = FakeCursor()
    verify = Mock()

    monkeypatch.setattr(
        run_migrations,
        "verify_migration_schema",
        verify,
    )

    run_migrations.process_migration(
        cursor,
        "001_review_updates.sql",
        {"001_review_updates.sql"},
    )

    verify.assert_called_once_with(
        cursor, "001_review_updates.sql"
    )

    assert cursor.executed == []


def test_existing_schema_is_adopted(monkeypatch):
    cursor = FakeCursor()
    verify = Mock()
    recorded = set()

    monkeypatch.setattr(
        run_migrations,
        "verify_migration_schema",
        verify,
    )

    run_migrations.process_migration(
        cursor,
        "001_review_updates.sql",
        recorded,
    )

    verify.assert_called_once()

    assert "001_review_updates.sql" in recorded
    assert len(cursor.executed) == 1
    assert "INSERT INTO schema_migrations" in cursor.executed[0][0]


def test_new_migration_is_applied_and_recorded(
    monkeypatch, tmp_path
):
    cursor = FakeCursor()
    recorded = set()

    migration_file = tmp_path / "006_test.sql"
    migration_file.write_text("SELECT 1;", encoding="utf-8")

    monkeypatch.setattr(
        run_migrations,
        "MIGRATIONS_DIR",
        tmp_path,
    )

    verify = Mock(
        side_effect=[
            RuntimeError("Missing schema"),
            None,
        ]
    )

    monkeypatch.setattr(
        run_migrations,
        "verify_migration_schema",
        verify,
    )

    run_migrations.process_migration(
        cursor,
        "006_test.sql",
        recorded,
        allow_apply=True,
    )

    assert verify.call_count == 2
    assert "006_test.sql" in recorded

    assert any(
        "SELECT 1;" in query
        for query, _ in cursor.executed
    )

    assert any(
        "INSERT INTO schema_migrations" in query
        for query, _ in cursor.executed
    )


def test_historical_migration_is_not_reexecuted(monkeypatch):
    cursor = FakeCursor()

    monkeypatch.setattr(
        run_migrations,
        "verify_migration_schema",
        Mock(side_effect=RuntimeError("Missing schema")),
    )

    with pytest.raises(
        RuntimeError,
        match="Refusing to rerun",
    ):
        run_migrations.process_migration(
            cursor,
            "001_review_updates.sql",
            set(),
        )

    assert cursor.executed == []


def test_only_whitelisted_migration_can_be_applied():
    assert run_migrations.APPLYABLE_MIGRATIONS == {
        "006_ground_truth_idempotency.sql",
        "007_verifier_cost_estimate_idempotency.sql",
    }