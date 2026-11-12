import pytest
from unittest.mock import Mock

from scripts import run_migrations
from scripts import reconcile_migration_history


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


class FreshSchemaCursor(FakeCursor):
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def fetchone(self):
        return (None,)


class FreshSchemaConnection:
    def __init__(self):
        self.cursor_instance = FreshSchemaCursor()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def cursor(self):
        return self.cursor_instance

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
        "008_live_verifier_recovery.sql",
        "009_verifier_attempt_identity.sql",
        "010_execution_lease_recovery.sql",
        "011_reputation_snapshot_id_text.sql",
        "012_report_validation_id_text.sql",
    ]


def test_fresh_schema_path_includes_and_verifies_snapshot_text_migration(
    monkeypatch,
):
    connection = FreshSchemaConnection()
    verified = []
    monkeypatch.setattr(
        run_migrations.psycopg2,
        "connect",
        lambda **kwargs: connection,
    )
    monkeypatch.setattr(run_migrations, "load_dotenv", lambda *args: None)
    monkeypatch.setattr(
        run_migrations,
        "verify_migration_schema",
        lambda cursor, filename: verified.append(filename),
    )
    for key in ("DB_HOST", "DB_NAME", "DB_USER", "DB_PASSWORD"):
        monkeypatch.setenv(key, "test-value")

    run_migrations.main()

    migration_sql = (
        run_migrations.MIGRATIONS_DIR
        / "011_reputation_snapshot_id_text.sql"
    ).read_text(encoding="utf-8")
    assert any(
        query == migration_sql
        for query, _ in connection.cursor_instance.executed
    )
    assert verified.count("011_reputation_snapshot_id_text.sql") == 2
    assert verified.count("012_report_validation_id_text.sql") == 2


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


@pytest.mark.parametrize(
    "actual_type, expected_error",
    [
        ("uuid", "expected text, found uuid"),
        (None, "expected text, found missing"),
    ],
)
def test_verify_migration_schema_rejects_wrong_required_column_type(
    monkeypatch, actual_type, expected_error
):
    cursor = FakeCursor()
    monkeypatch.setattr(
        run_migrations,
        "get_existing_columns",
        lambda cursor: {"validation_audits": {"reputation_snapshot_id"}},
    )
    monkeypatch.setattr(
        run_migrations,
        "get_existing_column_types",
        lambda cursor: (
            {("validation_audits", "reputation_snapshot_id"): actual_type}
            if actual_type is not None
            else {}
        ),
    )
    monkeypatch.setattr(
        run_migrations, "get_existing_constraints", lambda cursor: set()
    )
    monkeypatch.setattr(
        run_migrations, "get_existing_indexes", lambda cursor: set()
    )

    with pytest.raises(RuntimeError, match=expected_error):
        run_migrations.verify_migration_schema(
            cursor, "011_reputation_snapshot_id_text.sql"
        )


def test_verify_migration_schema_accepts_required_text_column_type(monkeypatch):
    cursor = FakeCursor()
    monkeypatch.setattr(
        run_migrations,
        "get_existing_columns",
        lambda cursor: {"validation_audits": {"reputation_snapshot_id"}},
    )
    monkeypatch.setattr(
        run_migrations,
        "get_existing_column_types",
        lambda cursor: {("validation_audits", "reputation_snapshot_id"): "text"},
    )
    monkeypatch.setattr(
        run_migrations, "get_existing_constraints", lambda cursor: set()
    )
    monkeypatch.setattr(
        run_migrations, "get_existing_indexes", lambda cursor: set()
    )

    run_migrations.verify_migration_schema(
        cursor, "011_reputation_snapshot_id_text.sql"
    )


@pytest.mark.parametrize("module", [run_migrations, reconcile_migration_history])
def test_migration_012_requires_report_validation_id_text(module, monkeypatch):
    columns = {"live_verifier_attempts": {"report_validation_id"}}
    types = {("live_verifier_attempts", "report_validation_id"): "text"}
    cursor = FakeCursor()
    if module is run_migrations:
        monkeypatch.setattr(module, "get_existing_columns", lambda cursor: columns)
        monkeypatch.setattr(module, "get_existing_column_types", lambda cursor: types)
        monkeypatch.setattr(module, "get_existing_constraints", lambda cursor: set())
        monkeypatch.setattr(module, "get_existing_indexes", lambda cursor: set())
        module.verify_migration_schema(cursor, "012_report_validation_id_text.sql")
    else:
        assert module.verify_migration(
            "012_report_validation_id_text.sql", columns, set(), set(),
            types,
        ) == []


@pytest.mark.parametrize("module", [run_migrations, reconcile_migration_history])
def test_migration_012_rejects_uuid_report_validation_id(module, monkeypatch):
    columns = {"live_verifier_attempts": {"report_validation_id"}}
    types = {("live_verifier_attempts", "report_validation_id"): "uuid"}
    cursor = FakeCursor()
    if module is run_migrations:
        monkeypatch.setattr(module, "get_existing_columns", lambda cursor: columns)
        monkeypatch.setattr(module, "get_existing_column_types", lambda cursor: types)
        monkeypatch.setattr(module, "get_existing_constraints", lambda cursor: set())
        monkeypatch.setattr(module, "get_existing_indexes", lambda cursor: set())
        with pytest.raises(RuntimeError, match="expected text, found uuid"):
            module.verify_migration_schema(cursor, "012_report_validation_id_text.sql")
    else:
        assert any("expected text, found uuid" in problem for problem in module.verify_migration(
            "012_report_validation_id_text.sql", columns, set(), set(), types
        ))


def test_migration_012_converts_uuid_and_leaves_text_unchanged():
    migration = (
        run_migrations.MIGRATIONS_DIR / "012_report_validation_id_text.sql"
    ).read_text(encoding="utf-8")
    assert "existing_type = 'uuid'" in migration
    assert "USING report_validation_id::TEXT" in migration
    assert "existing_type <> 'text'" in migration
    assert "existing_type IS NULL" in migration


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
        "005_verifier_cost_measurements.sql",
        "006_ground_truth_idempotency.sql",
        "007_verifier_cost_estimate_idempotency.sql",
        "008_live_verifier_recovery.sql",
        "009_verifier_attempt_identity.sql",
        "010_execution_lease_recovery.sql",
        "011_reputation_snapshot_id_text.sql",
        "012_report_validation_id_text.sql",
    }


def test_migration_history_reconciler_tracks_current_migrations():
    assert reconcile_migration_history.MIGRATION_FILES == run_migrations.MIGRATIONS


@pytest.mark.parametrize("module", [run_migrations, reconcile_migration_history])
def test_legacy_008_snapshot_migration_history_is_recognized(module):
    legacy = "008_reputation_snapshot_id_text.sql"
    assert module.LEGACY_MIGRATION_ALIASES[legacy] == "011_reputation_snapshot_id_text.sql"
    assert module.unknown_migration_records({legacy}) == set()
    assert module.unknown_migration_records({"999_unrecognized.sql"}) == {
        "999_unrecognized.sql"
    }


def test_recorded_legacy_snapshot_migration_adopts_011_without_rewriting_history(
    monkeypatch,
):
    cursor = FakeCursor()
    recorded = {"008_reputation_snapshot_id_text.sql"}
    verify = Mock()
    monkeypatch.setattr(run_migrations, "verify_migration_schema", verify)

    run_migrations.process_migration(
        cursor,
        "011_reputation_snapshot_id_text.sql",
        recorded,
    )

    assert recorded == {
        "008_reputation_snapshot_id_text.sql",
        "011_reputation_snapshot_id_text.sql",
    }
    assert "INSERT INTO schema_migrations" in cursor.executed[0][0]
    assert cursor.executed[0][1] == ("011_reputation_snapshot_id_text.sql",)
    verify.assert_called_once_with(cursor, "011_reputation_snapshot_id_text.sql")


@pytest.mark.parametrize(
    "actual_type, expected_error",
    [
        ("uuid", "type expected text, found uuid"),
        (None, "type expected text, found missing"),
    ],
)
def test_migration_history_reconciler_rejects_wrong_snapshot_id_type(
    actual_type, expected_error
):
    types = (
        {("validation_audits", "reputation_snapshot_id"): actual_type}
        if actual_type is not None
        else {}
    )
    problems = reconcile_migration_history.verify_migration(
        "011_reputation_snapshot_id_text.sql",
        {"validation_audits": {"reputation_snapshot_id"}},
        set(),
        set(),
        types,
    )
    assert any(expected_error in problem for problem in problems)


def test_migration_history_reconciler_accepts_text_snapshot_id():
    problems = reconcile_migration_history.verify_migration(
        "011_reputation_snapshot_id_text.sql",
        {"validation_audits": {"reputation_snapshot_id"}},
        set(),
        set(),
        {("validation_audits", "reputation_snapshot_id"): "text"},
    )
    assert problems == []

def test_005_preconditions_allow_application_when_tables_are_absent(
    monkeypatch,
):
    cursor = FakeCursor()
    cursor.result = ("verifier_outputs",)

    monkeypatch.setattr(
        run_migrations,
        "get_existing_columns",
        lambda cursor: {
            "verifier_outputs": set(),
            "questions_answers": set(),
        },
    )

    run_migrations.validate_005_apply_preconditions(cursor)


def test_005_preconditions_reject_partial_tables(monkeypatch):
    cursor = FakeCursor()
    cursor.result = ("verifier_outputs",)

    monkeypatch.setattr(
        run_migrations,
        "get_existing_columns",
        lambda cursor: {
            "verifier_outputs": set(),
            "verifier_measurement_setups": set(),
        },
    )

    with pytest.raises(RuntimeError, match="target tables already exist"):
        run_migrations.validate_005_apply_preconditions(cursor)


def test_005_preconditions_require_verifier_outputs():
    cursor = FakeCursor()
    cursor.result = (None,)

    with pytest.raises(RuntimeError, match="verifier_outputs"):
        run_migrations.validate_005_apply_preconditions(cursor)