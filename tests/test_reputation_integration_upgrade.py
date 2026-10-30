"""Real learning/retry logic with controlled posterior I/O, never a live DB."""

from concurrent.futures import ThreadPoolExecutor
import json
import threading

import pytest

from app.analysis.question_analyzer import QuestionAnalysis
from app.models.schemas import ValidationRequest, VerificationResult
from app.orchestration import validation_orchestrator as module
from app.reputation.reputation_manager import ReputationManager
from app.selection.verifier_selector import VerifierSelector
from tests.test_adaptive_pipeline import FixedAnalyzer, MetadataChecker


@pytest.fixture
def make_run(monkeypatch):
    monkeypatch.setattr(module.AutomaticGroundTruthEvaluator, "evaluate", lambda *a, **kw: None)
    monkeypatch.setattr(module, "save_reputation", lambda **kw: None)
    monkeypatch.setattr(module, "save_reputation_state_and_rows", lambda state: None)

    def make(names=("a", "b"), decision="SUPPORT"):
        manager = ReputationManager()
        agents = [MetadataChecker(name, metadata={"decision": decision},
                                  passed=decision == "SUPPORT") for name in names]
        return module.ValidationOrchestrator(
            question_analyzer=FixedAnalyzer(QuestionAnalysis("general", "easy", .1)),
            verifier_selector=VerifierSelector(verifiers=agents, reputation_manager=manager),
            reputation_manager=manager,
        )
    return make


def validate(run):
    return run.validate(ValidationRequest(question="q", answer="a"))


def deliver(run, response, label=True, **kwargs):
    return run.record_ground_truth(response.results, label,
                                   validation_id=response.validation_id, **kwargs)


@pytest.mark.parametrize("source", [None, "user_feedback", "benchmark_ground_truth"])
def test_feedback_source_is_preserved_and_full_state_round_trips(make_run, source):
    run = make_run()
    response = validate(run)
    kwargs = {} if source is None else {"source": source}
    assert deliver(run, response, **kwargs) == 2
    state = run.reputation_manager.export_state()
    assert state["feedback"][0]["source"] == (source or "external_feedback")
    restored = ReputationManager(3, 7)
    restored.restore_state(json.loads(json.dumps(state, allow_nan=False)))
    assert restored.export_state() == state
    assert deliver(run, response, **kwargs) == 0


@pytest.mark.parametrize("source", [None, "", "  ", True, 1, float("nan")])
def test_invalid_source_has_no_learning_or_save_effects(make_run, monkeypatch, source):
    run = make_run()
    response = validate(run)
    state = run.reputation_manager.export_state()
    monkeypatch.setattr(module, "save_reputation", lambda **kw: pytest.fail("unexpected save"))
    with pytest.raises(ValueError, match="source"):
        deliver(run, response, source=source)
    assert run.reputation_manager.export_state() == state
    assert run._pending_posterior_pairs == set()


def test_failed_save_retry_learns_once_and_completed_duplicate_does_not_save(make_run, monkeypatch):
    run = make_run(("a",))
    response = validate(run)
    writes = []

    def save(**row):
        writes.append(row)
        if len(writes) == 1:
            raise OSError("offline save failure")

    monkeypatch.setattr(module, "save_reputation", save)
    with pytest.raises(OSError):
        deliver(run, response)
    assert run.reputation_manager.statistics("a", "general").successes == 1
    assert run._pending_posterior_pairs == {("a", "general")}
    assert deliver(run, response) == 0
    assert writes == [dict(verifier_name="a", domain="general", alpha=2., beta=1.)] * 2
    assert not run._pending_posterior_pairs
    assert deliver(run, response) == 0
    assert len(writes) == 2
    assert run.reputation_manager.observation_count("a", "general") == 1


def test_partial_failure_retries_only_unfinished_rows(make_run, monkeypatch):
    run = make_run()
    response = validate(run)
    calls = []

    def save(**row):
        calls.append(row["verifier_name"])
        if calls == ["a", "b"]:
            raise OSError("second row failed")

    monkeypatch.setattr(module, "save_reputation", save)
    with pytest.raises(OSError):
        deliver(run, response)
    assert run._pending_posterior_pairs == {("b", "general")}
    assert deliver(run, response) == 0
    assert calls == ["a", "b", "b"]
    assert not run._pending_posterior_pairs
    assert [run.reputation_manager.observation_count(n, "general") for n in ("a", "b")] == [1, 1]


@pytest.mark.parametrize("change", ["label", "source", "votes", "invalid_source"])
def test_conflicts_do_not_flush_pending_work(make_run, monkeypatch, change):
    run = make_run(("a",))
    response = validate(run)
    calls = []

    def fail(**row):
        calls.append(row)
        raise OSError("offline")

    monkeypatch.setattr(module, "save_reputation", fail)
    with pytest.raises(OSError):
        deliver(run, response)
    before = run.reputation_manager.export_state()
    kwargs = {"source": "different"} if change == "source" else {}
    if change == "invalid_source":
        kwargs["source"] = " "
    if change == "votes":
        response.results[0].passed = False
        response.results[0].metadata["decision"] = "REJECT"
    with pytest.raises(ValueError):
        deliver(run, response, label=change != "label", **kwargs)
    assert len(calls) == 1
    assert run.reputation_manager.export_state() == before
    assert run._pending_posterior_pairs == {("a", "general")}


def test_older_retry_saves_newest_counts_after_overlapping_feedback(make_run, monkeypatch):
    run = make_run(("a",))
    first, second = validate(run), validate(run)
    calls = []

    def save(**row):
        calls.append(row)
        if len(calls) <= 2:
            raise OSError("offline")

    monkeypatch.setattr(module, "save_reputation", save)
    for response in (first, second):
        with pytest.raises(OSError):
            deliver(run, response)
    assert deliver(run, first) == 0
    assert [row["alpha"] for row in calls] == [2., 3., 3.]
    assert run.reputation_manager.observation_count("a", "general") == 2
    assert not run._pending_posterior_pairs


@pytest.mark.parametrize("pending", [False, True])
def test_concurrent_duplicate_delivery_and_retry(make_run, monkeypatch, pending):
    run = make_run(("a",))
    response = validate(run)
    if pending:
        def fail(**row):
            raise OSError("offline")
        monkeypatch.setattr(module, "save_reputation", fail)
        with pytest.raises(OSError):
            deliver(run, response)
    rows = []
    monkeypatch.setattr(module, "save_reputation", lambda **row: rows.append(row))
    barrier = threading.Barrier(2)

    def send():
        barrier.wait(timeout=5)
        return deliver(run, response)

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(send) for _ in range(2)]
        assert sorted(f.result(timeout=5) for f in futures) == ([0, 0] if pending else [0, 1])
    assert len(rows) == 1 and rows[0]["alpha"] == 2.
    assert run.reputation_manager.observation_count("a", "general") == 1
    assert not run._pending_posterior_pairs


def test_inflight_old_save_cannot_overwrite_newer_feedback(make_run, monkeypatch):
    run = make_run(("a",))
    first, second = validate(run), validate(run)
    entered, release, newer_started = threading.Event(), threading.Event(), threading.Event()
    writes = []
    stored = {}

    def save(**row):
        if row["alpha"] == 2.:
            entered.set()
            assert release.wait(timeout=5)
        # Model the repository commit, rather than just entry into save().
        stored.update(row)
        writes.append(dict(row))

    def newer():
        newer_started.set()
        return deliver(run, second)

    monkeypatch.setattr(module, "save_reputation", save)
    with ThreadPoolExecutor(max_workers=2) as pool:
        older = pool.submit(deliver, run, first)
        try:
            assert entered.wait(timeout=5)
            latest = pool.submit(newer)
            assert newer_started.wait(timeout=5)
        finally:
            release.set()
        assert older.result(timeout=5) == latest.result(timeout=5) == 1
    latest = run.reputation_manager.statistics("a", "general")
    assert [row["alpha"] for row in writes] == [2., 3.]
    assert stored == dict(verifier_name="a", domain="general",
                          alpha=latest.alpha, beta=latest.beta)
    assert latest.successes == latest.observation_count == 2
    assert latest.failures == 0
    assert not run._pending_posterior_pairs


@pytest.mark.parametrize("names,decision", [((), "SUPPORT"), (("a",), "UNSURE")])
def test_zero_observation_events_do_not_invent_posterior_writes(make_run, monkeypatch, names, decision):
    run = make_run(names, decision)
    response = validate(run)
    monkeypatch.setattr(module, "save_reputation", lambda **row: pytest.fail("no posterior changed"))
    assert deliver(run, response) == 0
    assert deliver(run, response) == 0
    state = run.reputation_manager.export_state()
    assert state["pairs"] == [] and len(state["feedback"]) == 1
    assert not run._pending_posterior_pairs


def test_unscoped_source_validation_preserves_legacy_counting(make_run):
    run = make_run()
    vote = VerificationResult(verifier_name="custom", passed=True, score=0.)
    before = run.reputation_manager.export_state()
    with pytest.raises(ValueError):
        run.record_ground_truth([vote], True, "technical", source="")
    assert run.reputation_manager.export_state() == before
    for _ in range(2):
        assert run.record_ground_truth([vote], True, "technical", source="user_feedback") == 1
    assert run.reputation_manager.observation_count("custom", "technical") == 2
    assert run.reputation_manager.is_cold_start("custom", "general")


def test_completed_duplicate_with_different_source_conflicts(make_run, monkeypatch):
    run = make_run(("a",))
    response = validate(run)
    assert deliver(run, response, source="user_feedback") == 1
    state = run.reputation_manager.export_state()
    monkeypatch.setattr(module, "save_reputation", lambda **kw: pytest.fail("conflict must not save"))
    with pytest.raises(ValueError, match="conflicting feedback"):
        deliver(run, response, source="benchmark_ground_truth")
    assert run.reputation_manager.export_state() == state
