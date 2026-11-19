"""Prove direct Game isolation and reject unclassified fallback triggers."""
from unittest.mock import Mock

import pytest

from app.models.schemas import ValidationRequest
from app.services.validation_service import ValidationService
from app.game.artifacts import InMemoryPolicyProvider
from app.game.execution import VerifierExecutionFailure
from app.game.models import EnumerationResult, Infeasibility
from app.selection.models import VerifierUnavailable
from tests.test_game_runtime import runtime_fixture, artifact_fixture
from tests.test_adaptive_pipeline import offline_pipeline_boundaries


@pytest.fixture(autouse=True)
def offline(offline_pipeline_boundaries):
    pass


def prohibit_baseline(run, monkeypatch):
    provider = Mock(side_effect=AssertionError("no baseline entry permitted"))
    monkeypatch.setattr(run, "_baseline_budget_provider", provider)
    # Game legitimately invokes plan() on its detached frozen selector for
    # compatibility checking. Guard the baseline execution branch itself.
    import app.orchestration.validation_orchestrator as module
    baseline_ledger = Mock(side_effect=AssertionError("no baseline execution ledger permitted"))
    monkeypatch.setattr(module, "BudgetLedger", baseline_ledger)
    return provider, baseline_ledger


def test_successful_game_executes_once_without_baseline(monkeypatch):
    run, checkers, _, rng = runtime_fixture()
    provider, baseline_ledger = prohibit_baseline(run, monkeypatch)
    result = ValidationService(run).validate(ValidationRequest(question="q", answer="a"))
    assert result.final_status == "passed" and result.selected_verifiers == ["a", "b"]
    assert [c.calls for c in checkers] == [1, 1, 0] and rng.calls == 1
    assert result.execution_audit["termination"] == "complete_selected_team"
    provider.assert_not_called()
    baseline_ledger.assert_not_called()


def test_game_default_selector_construction_never_consults_baseline_resources(monkeypatch):
    from app.orchestration.validation_orchestrator import ValidationOrchestrator
    from app.selection.verifier_selector import VerifierSelector
    from app.selection import baseline_resources
    from app.decision.decision_engine import DecisionEngine

    run, _, manager, _ = runtime_fixture()
    forbidden = Mock(side_effect=AssertionError("Game must not construct a Baseline selector or load its resources"))
    monkeypatch.setattr(baseline_resources, "BaselineVerifierSelector", forbidden)
    monkeypatch.setattr(baseline_resources, "load_baseline_evidence_configuration", forbidden)
    game = ValidationOrchestrator(question_analyzer=run._question_analyzer,
        decision_engine=DecisionEngine(manager), execution_mode="game", game_runtime=run._game_runtime)
    assert type(game.verifier_selector) is VerifierSelector
    assert game.reputation_manager is manager
    forbidden.assert_not_called()


def test_all_frozen_game_dependency_bytes_remain_reviewed():
    import hashlib
    import json
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    record = json.loads((root / "reconciliation/integration-dependencies.json").read_text())
    assert len(record["files"]) == 4
    for path, expected in record["files"].items():
        assert hashlib.sha256((root / path).read_bytes()).hexdigest() == expected, path


@pytest.mark.parametrize("error", [FileNotFoundError("missing policy"), ValueError("invalid policy"), RuntimeError("unavailable")])
def test_game_construction_failure_propagates_instead_of_falling_back(monkeypatch, error):
    from app.services import validation_service
    from app.game import deployment
    monkeypatch.setattr(validation_service.settings, "EXECUTION_MODE", "game")
    monkeypatch.setattr(deployment, "create_game_runtime", Mock(side_effect=error))
    constructor = Mock(side_effect=AssertionError("no substitute baseline orchestrator"))
    monkeypatch.setattr(validation_service, "ValidationOrchestrator", constructor)
    with pytest.raises(type(error)) as raised:
        ValidationService()
    assert raised.value is error
    constructor.assert_not_called()


@pytest.mark.parametrize("mode", ["missing", "ambiguous", "invalid"])
def test_policy_selection_failures_stay_in_game_without_dispatch(monkeypatch, mode):
    artifact = artifact_fixture()[0]
    if mode == "missing":
        registry = InMemoryPolicyProvider()
    elif mode == "ambiguous":
        registry = InMemoryPolicyProvider((artifact, artifact))
    else:
        registry = Mock(snapshot=lambda: (artifact.model_copy(update={"execution_configuration_id": "wrong"}),))
    run, checkers, _, rng = runtime_fixture(artifact=artifact, provider=registry)
    provider, baseline_ledger = prohibit_baseline(run, monkeypatch)
    result = ValidationService(run).validate(ValidationRequest(question="q", answer="a"))
    assert result.final_status == "uncertain" and result.results == []
    assert result.execution_audit["selection_status"] == {
        "missing": "missing_policy", "ambiguous": "ambiguous_policy", "invalid": "incompatible"}[mode]
    assert all(c.calls == 0 for c in checkers) and rng.calls == 0
    provider.assert_not_called()
    baseline_ledger.assert_not_called()


def test_controlled_infeasible_strategy_branch_is_not_baseline_fallback(monkeypatch):
    import app.game.execution as module
    run, checkers, _, rng = runtime_fixture()
    provider, _ = prohibit_baseline(run, monkeypatch)
    # Branch fixture, not a live over-budget experiment or altered frozen policy.
    monkeypatch.setattr(module, "enumerate_strategies", lambda context: EnumerationResult(
        status="no_feasible_strategy", strategies=(), exclusions=(),
        rejected=(Infeasibility(verifiers=(), reasons=("budget",)),)))
    result = run.validate(ValidationRequest(question="q", answer="a"))
    assert result.final_status == "uncertain"
    assert result.execution_audit["selection_status"] == "no_feasible_strategy"
    assert all(c.calls == 0 for c in checkers) and rng.calls == 0
    provider.assert_not_called()


@pytest.mark.parametrize("error,state", [(VerifierUnavailable("maintenance"), "unavailable"),
                                        (VerifierExecutionFailure("failure"), "failed")])
def test_expected_verifier_failure_completes_game_contract_without_retry(monkeypatch, error, state):
    run, checkers, _, rng = runtime_fixture(behaviors={"b": error})
    provider, baseline_ledger = prohibit_baseline(run, monkeypatch)
    result = run.validate(ValidationRequest(question="q", answer="a"))
    assert result.final_status == "uncertain"
    assert result.execution_audit["attempts"][1]["state"] == state
    assert [c.calls for c in checkers] == [1, 1, 0] and rng.calls == 1
    provider.assert_not_called()
    baseline_ledger.assert_not_called()


def test_unexpected_verifier_failure_propagates_without_second_execution(monkeypatch):
    error = RuntimeError("fixture bug")
    run, checkers, _, rng = runtime_fixture(behaviors={"b": error})
    provider, _ = prohibit_baseline(run, monkeypatch)
    with pytest.raises(RuntimeError) as raised:
        run.validate(ValidationRequest(question="q", answer="a"))
    assert raised.value is error and [c.calls for c in checkers] == [1, 1, 0]
    provider.assert_not_called()


def test_original_request_and_context_reach_game_unchanged(monkeypatch):
    run, _, _, _ = runtime_fixture()
    provider, _ = prohibit_baseline(run, monkeypatch)
    original_run = type(run._game_runtime).run
    seen = []

    def record(self, selector, analysis, request, execution_id, **kwargs):
        seen.append(request)
        return original_run(self, selector, analysis, request, execution_id, **kwargs)

    monkeypatch.setattr(type(run._game_runtime), "run", record)
    request = ValidationRequest(question="original question", answer="original answer",
                                context="original context", question_id=20)
    before = request.model_dump()
    result = ValidationService(run).validate(request)
    assert seen == [request] and seen[0] is request and request.model_dump() == before
    assert result.execution_audit is not None and "baseline_budget" not in result.execution_audit
    provider.assert_not_called()
