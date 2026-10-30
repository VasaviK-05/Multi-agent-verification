
import pytest

from app.database import verifier_cost_repository as repository


SETUP_ID = "11111111-1111-4111-8111-111111111111"
RUN_ID = "22222222-2222-4222-8222-222222222222"
ATTEMPT_ID = "33333333-3333-4333-8333-333333333333"
ESTIMATE_ID = "44444444-4444-4444-8444-444444444444"


class FakeCursor:
    def __init__(self, rows=None):
        self.rows = rows or []
        self.executed = []
        self.closed = False

    def execute(self, query, params=None):
        self.executed.append((query, params))

    def fetchone(self):
        return self.rows[0] if self.rows else None

    def fetchall(self):
        return self.rows

    def close(self):
        self.closed = True


class FakeConnection:
    def __init__(self, rows=None):
        self.fake_cursor = FakeCursor(rows)
        self.commits = 0
        self.rollbacks = 0
        self.closed = False

    def cursor(self):
        return self.fake_cursor

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1

    def close(self):
        self.closed = True


def patch_connection(monkeypatch, connection):
    monkeypatch.setattr(
        repository, "get_connection", lambda: connection
    )


def test_save_measurement_setup(monkeypatch):
    connection = FakeConnection([(SETUP_ID,)])
    patch_connection(monkeypatch, connection)

    result = repository.save_measurement_setup(
        verifier_name="test-verifier",
        setup_fingerprint="setup-fingerprint-1",
        implementation_fingerprint="impl-hash",
        config_fingerprint="config-hash",
        model_fingerprint="model-hash",
        verifier_config={"temperature": 0},
    )

    query, params = connection.fake_cursor.executed[0]

    assert "INSERT INTO verifier_measurement_setups" in query
    assert "implementation_fingerprint" in query
    assert "config_fingerprint" in query
    assert params[1] == "setup-fingerprint-1"
    assert params[2] == "test-verifier"
    assert result == SETUP_ID
    assert connection.commits == 1
    assert connection.rollbacks == 0
    assert connection.closed
    assert connection.fake_cursor.closed


@pytest.mark.parametrize(
    "outcome",
    ["returned", "failure", "timeout", "interrupted"],
)
def test_save_verifier_attempt_accepts_valid_outcomes(
    monkeypatch, outcome
):
    connection = FakeConnection([(ATTEMPT_ID,)])
    patch_connection(monkeypatch, connection)

    result = repository.save_verifier_attempt(
        run_id=RUN_ID,
        verifier_name="test-verifier",
        setup_id=SETUP_ID,
        outcome=outcome,
        duration_ms=12.5,
        is_warmup=False,
        data_role="development",
    )

    query, params = connection.fake_cursor.executed[0]

    assert "INSERT INTO verifier_cost_attempts" in query
    assert params[6] == outcome
    assert result == ATTEMPT_ID
    assert connection.commits == 1
    assert connection.closed


@pytest.mark.parametrize(
    "kwargs, message",
    [
        ({"outcome": "success"}, "Invalid outcome"),
        ({"outcome": "error"}, "Invalid outcome"),
        ({"outcome": "returned", "duration_ms": -1},
         "duration_ms cannot be negative"),
        ({"outcome": "returned", "measurement_purpose": "unknown"},
         "Invalid measurement purpose"),
        ({"outcome": "returned", "data_role": "unknown"},
         "Invalid data role"),
    ],
)
def test_save_verifier_attempt_rejects_invalid_values(kwargs, message):
    with pytest.raises(ValueError, match=message):
        repository.save_verifier_attempt(
            run_id=RUN_ID,
            verifier_name="test-verifier",
            setup_id=SETUP_ID,
            **kwargs,
        )


def test_save_verifier_attempt_rolls_back_on_database_error(monkeypatch):
    connection = FakeConnection()

    def fail_execute(query, params=None):
        raise RuntimeError("database write failed")

    connection.fake_cursor.execute = fail_execute
    patch_connection(monkeypatch, connection)

    with pytest.raises(RuntimeError, match="database write failed"):
        repository.save_verifier_attempt(
            run_id=RUN_ID,
            verifier_name="test-verifier",
            setup_id=SETUP_ID,
            outcome="returned",
        )

    assert connection.commits == 0
    assert connection.rollbacks == 1
    assert connection.closed
    assert connection.fake_cursor.closed


def test_save_cost_estimate(monkeypatch):
    connection = FakeConnection([(ESTIMATE_ID,)])
    patch_connection(monkeypatch, connection)

    result = repository.save_cost_estimate(
        calibration_id=RUN_ID,
        verifier_name="test-verifier",
        setup_id=SETUP_ID,
        mean_attempt_cost_ms=10.5,
        median_duration_ms=9.5,
        p95_duration_ms=18.0,
        attempt_count=10,
        failure_count=2,
        estimator_version="v1",
        input_digest="sha256-example",
        source_attempt_ids=[ATTEMPT_ID],
    )

    query, params = connection.fake_cursor.executed[0]

    assert "INSERT INTO verifier_cost_estimates" in query
    assert "mean_attempt_cost_ms" in query
    assert params[5] == 10.5
    assert params[8] == 10
    assert params[9] == 2
    assert params[12] == "sha256-example"
    assert params[13] == [ATTEMPT_ID]
    assert result == ESTIMATE_ID
    assert connection.commits == 1
    assert connection.closed


@pytest.mark.parametrize(
    "attempt_count, failure_count",
    [( -1, 0), (2, -1), (2, 3)],
)
def test_save_cost_estimate_rejects_invalid_counts(
    attempt_count, failure_count
):
    with pytest.raises(ValueError, match="Invalid attempt_count/failure_count"):
        repository.save_cost_estimate(
            calibration_id=RUN_ID,
            verifier_name="test-verifier",
            setup_id=SETUP_ID,
            attempt_count=attempt_count,
            failure_count=failure_count,
            estimator_version="v1",
            input_digest="digest",
            source_attempt_ids=[],
        )


def test_calculate_and_save_cost_estimate(monkeypatch):
    attempt_rows = [
        (ATTEMPT_ID, 10.0, "returned", False, None, "calibration", "development"),
        ("55555555-5555-4555-8555-555555555555", 20.0, "returned", False, None, "calibration", "development"),
        ("66666666-6666-4666-8666-666666666666", 30.0, "failure", False, None, "calibration", "development"),
    ]

    read_connection = FakeConnection()
    read_connection.fake_cursor.rows = attempt_rows
    patch_connection(monkeypatch, read_connection)

    saved = {}

    def fake_save_cost_estimate(**kwargs):
        saved.update(kwargs)
        return ESTIMATE_ID

    monkeypatch.setattr(
        repository, "save_cost_estimate", fake_save_cost_estimate
    )

    result = repository.calculate_and_save_cost_estimate(
        calibration_id=RUN_ID,
        verifier_name="test-verifier",
        setup_id=SETUP_ID,
    )

    assert result == ESTIMATE_ID
    assert saved["mean_attempt_cost_ms"] == 20.0
    assert saved["median_duration_ms"] == 20.0
    assert saved["p95_duration_ms"] == 30.0
    assert saved["attempt_count"] == 3
    assert saved["failure_count"] == 1
    assert len(saved["source_attempt_ids"]) == 3
    assert len(saved["input_digest"]) == 64
    assert read_connection.closed
    assert read_connection.fake_cursor.closed


def test_calculate_cost_estimate_excludes_warmups_by_default(monkeypatch):
    connection = FakeConnection([
        (ATTEMPT_ID, 10.0, "returned", False, None, "calibration", "development"),
    ])
    patch_connection(monkeypatch, connection)

    saved = {}
    monkeypatch.setattr(
        repository,
        "save_cost_estimate",
        lambda **kwargs: saved.update(kwargs) or ESTIMATE_ID,
    )

    repository.calculate_and_save_cost_estimate(
        calibration_id=RUN_ID,
        verifier_name="test-verifier",
        setup_id=SETUP_ID,
    )

    assert saved["attempt_count"] == 1
    assert saved["mean_attempt_cost_ms"] == 10.0
    assert saved["include_warmups"] is False
    query, params = connection.fake_cursor.executed[0]
    assert "is_warmup = FALSE" in query
    assert params[-1] is False


def test_calculate_cost_estimate_counts_untimed_failures(monkeypatch):
    connection = FakeConnection([
        (ATTEMPT_ID, 10.0, "returned", False, None, "calibration", "development"),
        ("55555555-5555-4555-8555-555555555555", None, "timeout", False, None, "calibration", "development"),
    ])
    patch_connection(monkeypatch, connection)

    saved = {}
    monkeypatch.setattr(
        repository,
        "save_cost_estimate",
        lambda **kwargs: saved.update(kwargs) or ESTIMATE_ID,
    )

    repository.calculate_and_save_cost_estimate(
        calibration_id=RUN_ID,
        verifier_name="test-verifier",
        setup_id=SETUP_ID,
    )

    assert saved["attempt_count"] == 2
    assert saved["failure_count"] == 1
    assert saved["mean_attempt_cost_ms"] == 10.0
    assert saved["median_duration_ms"] == 10.0
    assert saved["p95_duration_ms"] == 10.0


def test_calculate_cost_estimate_rejects_no_matching_attempts(monkeypatch):
    connection = FakeConnection([])
    patch_connection(monkeypatch, connection)

    with pytest.raises(ValueError, match="No matching verifier attempts"):
        repository.calculate_and_save_cost_estimate(
            calibration_id=RUN_ID,
            verifier_name="test-verifier",
            setup_id=SETUP_ID,
        )

    assert connection.closed
    assert connection.fake_cursor.closed


def test_calculate_cost_estimate_can_include_warmups(monkeypatch):
    connection = FakeConnection([
        (ATTEMPT_ID, 10.0, "returned", False, None, "calibration", "development"),
        ("55555555-5555-4555-8555-555555555555", 100.0, "returned", True, None, "calibration", "development"),
    ])
    patch_connection(monkeypatch, connection)

    saved = {}
    monkeypatch.setattr(
        repository,
        "save_cost_estimate",
        lambda **kwargs: saved.update(kwargs) or ESTIMATE_ID,
    )

    repository.calculate_and_save_cost_estimate(
        calibration_id=RUN_ID,
        verifier_name="test-verifier",
        setup_id=SETUP_ID,
        include_warmups=True,
    )

    assert saved["attempt_count"] == 2
    assert saved["mean_attempt_cost_ms"] == 55.0
    assert saved["include_warmups"] is True
    query, params = connection.fake_cursor.executed[0]
    assert params[-1] is True


def test_calculate_cost_estimate_digest_is_reproducible(monkeypatch):
    rows = [
        (ATTEMPT_ID, 10.0, "returned", False, None, "calibration", "development"),
        ("55555555-5555-4555-8555-555555555555", 20.0, "failure", False, None, "calibration", "development"),
    ]

    digests = []

    for _ in range(2):
        connection = FakeConnection(rows)
        patch_connection(monkeypatch, connection)

        saved = {}
        monkeypatch.setattr(
            repository,
            "save_cost_estimate",
            lambda **kwargs: saved.update(kwargs) or ESTIMATE_ID,
        )

        repository.calculate_and_save_cost_estimate(
            calibration_id=RUN_ID,
            verifier_name="test-verifier",
            setup_id=SETUP_ID,
        )
        digests.append(saved["input_digest"])

    assert digests[0] == digests[1]
    assert len(digests[0]) == 64

