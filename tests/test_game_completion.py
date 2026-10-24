"""Synthetic engine contract checks; no real verifiers or scientific claims."""

from dataclasses import replace
import json

import pytest

from app.game.artifacts import DeploymentEpisode, InMemoryPolicyProvider
from app.game.domain_routing import DomainRoute
from app.game.execution import GameRuntime
from app.game.execution_contract import ExecutionContract
from app.game.models import PlanningContext, PayoffMatrix, canonical_json
from app.game.offline.evaluation import bind_evaluation, construct_payoffs, export_artifact, fit_policy
from app.game.offline.pooling import PoolMember, fit_pooled_policies, evaluate_pooled_final_test
from app.game.offline.records import DatasetManifest
from app.game.offline.replay import category_id
from app.game.policy import build_policy
from app.game.pooling_contract import unpooled_context
from app.game.resource_provenance import ResourceFingerprint, VerifierResources, ResourceManifest
from app.models.schemas import ValidationRequest
from tests.test_game_offline import fixture
from tests.test_game_runtime import runtime_fixture, CountingRNG, Analyzer


def member(domain, *, resource_bound=False, incorrect=False):
    context, manifest, contract, attacks = fixture(names=("a", "b"))
    raw = context.model_dump()
    raw.update(offline_evaluation_id=None, execution_contract_json=None)
    plan = json.loads(raw["selection_json"])
    plan["domain"] = domain
    for statistics in plan["reputation_statistics"]:
        statistics["domain"] = domain
    raw["selection_json"] = canonical_json(plan)
    raw["provenance"]["category"] = domain
    for key in ("history_dataset", "development_dataset", "final_test_dataset"):
        raw["provenance"][key] = domain + "/" + raw["provenance"][key]
    context = PlanningContext(**raw)
    resources = None
    if resource_bound:
        resources = ResourceManifest(verifiers=tuple(VerifierResources(verifier_name=n, resources=(
            ResourceFingerprint(resource_id=n + "-code", kind="implementation", sha256="a" * 64),
            ResourceFingerprint(resource_id=n + "-config", kind="configuration", sha256="b" * 64))) for n in ("a", "b")))
        contract = ExecutionContract(**{**contract.model_dump(), "version": "offline_public_decision_v2",
            "execution_configuration_id": resources.manifest_id, "resource_manifest": resources})
    data = manifest.model_dump()
    for part in data["partitions"]:
        part["dataset_id"] = domain + "/" + part["dataset_id"]
        for example in part["examples"]:
            for key in ("example_id", "split_identity", "question_id", "validation_id", "question"):
                example[key] = domain + "/" + example[key]
            example.update(domain=domain, planning_category=category_id(context),
                execution_configuration_id=contract.execution_configuration_id)
            if part["role"] == "development":
                example["answer_is_correct"] = not incorrect
            for attempt in example["attempts"]:
                attempt.update(execution_id=example["validation_id"], configuration_id=contract.execution_configuration_id)
                if resources is not None:
                    observation = next(v for v in resources.verifiers if v.verifier_name == attempt["verifier_name"])
                    attempt["observed_resources_json"] = canonical_json(observation.model_dump(mode="json"))
    manifest = DatasetManifest(**data)
    context = bind_evaluation(context, manifest, contract, attacks)
    return PoolMember(context=context, manifest=manifest, contract=contract, attacks=attacks)


def pooled():
    members = (member("general"), member("science", incorrect=True), member("history"))
    return members, fit_pooled_policies(members, pool_id="fixture-pool", source_weights=(("general", .25), ("science", .75)))


def test_weighted_pool_matches_source_means_and_exact_target_snapshots():
    members, (pool, fitted, evaluations) = pooled()
    sources = dict(evaluations)
    for domain, context, policy in fitted:
        original = next(m for m in members if m.context.plan.domain == domain)
        assert unpooled_context(context) == original.context
        assert context.reputation_snapshot_id == original.context.reputation_snapshot_id
        assert context.compatibility_id != original.context.compatibility_id
        for row, a, b in zip(policy.matrix.values, sources["general"].matrix.values, sources["science"].matrix.values):
            assert row == pytest.approx(tuple(.25 * x + .75 * y for x, y in zip(a, b)))
    assert {s.domain for s in pool.sources} == {"general", "science"}
    assert len({p.solution.probabilities for _, _, p in fitted}) == 1


def test_pool_order_is_canonical():
    members, (pool, fitted, _) = pooled()
    other, reverse, _ = fit_pooled_policies(tuple(reversed(members)), pool_id="fixture-pool",
        source_weights=(("science", .75), ("general", .25)))
    assert other == pool and reverse == fitted


@pytest.mark.parametrize("weights", [(("general", 1.),), (("general", .5), ("science", .4)),
    (("general", True), ("science", 0.)), (("general", .5), ("other", .5)),
    (("general", .25), ("general", .25), ("science", .5))])
def test_bad_pool_weights_reject(weights):
    with pytest.raises(ValueError):
        fit_pooled_policies((member("general"), member("science")), pool_id="p", source_weights=weights)


def test_pool_rejects_incompatible_losses_and_cross_role_group_leakage():
    a, b = member("general"), member("science")
    data = b.context.model_dump()
    data["loss_configuration"]["uncertain"] = .4
    with pytest.raises(ValueError, match="semantics"):
        fit_pooled_policies((a, b.model_copy(update={"context": PlanningContext(**data)})),
            pool_id="p", source_weights=(("general", .5), ("science", .5)))
    data = b.manifest.model_dump()
    next(p for p in data["partitions"] if p["role"] == "final_test")["examples"][0]["split_identity"] = a.manifest.partition("development").examples[0].split_identity
    manifest = DatasetManifest(**data)
    raw = b.context.model_dump()
    raw.update(offline_evaluation_id=None)
    b = b.model_copy(update={"manifest": manifest, "context": bind_evaluation(PlanningContext(**raw), manifest, b.contract, b.attacks)})
    with pytest.raises(ValueError, match="leakage"):
        fit_pooled_policies((a, b), pool_id="p", source_weights=(("general", .5), ("science", .5)))


def test_pool_rejects_altered_payoffs_and_target_rebinding():
    _, (_, fitted, _) = pooled()
    _, context, policy = fitted[0]
    data = policy.matrix.model_dump()
    data["values"] = tuple(tuple(x + .1 for x in row) for row in data["values"])
    with pytest.raises(ValueError, match="pooled development payoffs"):
        build_policy(context, PayoffMatrix(**data))
    data = context.model_dump()
    data["budget"] = 9.
    with pytest.raises(ValueError, match="applicability"):
        PlanningContext(**data)


def test_pooled_final_scoring_never_fits_or_updates_development(monkeypatch):
    members, (_, fitted, _) = pooled()
    domain, context, policy = fitted[0]
    original = next(m for m in members if m.context.plan.domain == domain)
    import app.game.policy as module
    monkeypatch.setattr(module, "solve_minimax", lambda *a, **kw: pytest.fail("no final-test fitting"))
    result = evaluate_pooled_final_test(policy, context, original)
    assert result.policy_id == policy.policy_id
    assert {o.example_id for o in result.outcomes} == {original.manifest.partition("final_test").examples[0].example_id}


def episode(context, contract, name):
    return DeploymentEpisode(episode_id=name, context=context, contract=contract,
        execution_configuration_id=contract.execution_configuration_id)


def test_sparse_route_dispatches_pooled_exact_team_and_audits_choice():
    members, (_, fitted, _) = pooled()
    original = next(m for m in members if m.context.plan.domain == "general")
    _, context, policy = next(f for f in fitted if f[0] == "general")
    artifact = export_artifact(policy, context, original.manifest, original.contract, original.attacks, applicable_domain="general")
    direct = episode(original.context, original.contract, "direct")
    pooled_episode = episode(context, original.contract, "pooled")
    route = DomainRoute(direct_episode=direct, pooled_episode=pooled_episode, minimum_history_observations=1)
    orchestrator, checkers, _, rng = runtime_fixture(artifact=artifact)
    runtime = GameRuntime(InMemoryPolicyProvider((artifact,)), direct, rng, True, domain_routes=(route,))
    orchestrator._game_runtime = runtime
    response = orchestrator.validate(ValidationRequest(question="q", answer="a"))
    assert response.execution_audit["selection_status"] == "selected"
    assert response.execution_audit["policy_route"] == "pooled"
    assert response.execution_audit["episode_id"] == "pooled"
    assert sum(c.calls for c in checkers) == len(response.selected_verifiers)
    assert rng.calls == 1


@pytest.mark.parametrize("change", ["missing", "digest", "identity"])
def test_bound_recordings_require_exact_observed_resources(change):
    m = member("general", resource_bound=True)
    data = m.manifest.model_dump()
    attempt = data["partitions"][0]["examples"][0]["attempts"][0]
    if change == "missing":
        attempt["observed_resources_json"] = None
    else:
        observed = json.loads(attempt["observed_resources_json"])
        if change == "digest":
            observed["resources"][0]["sha256"] = "c" * 64
        else:
            observed["resources"][0]["resource_id"] = "different"
        attempt["observed_resources_json"] = canonical_json(observed)
    manifest = DatasetManifest(**data)
    with pytest.raises(ValueError, match="resources"):
        bind_evaluation(m.context, manifest, m.contract, m.attacks)


def test_resource_manifest_binds_execution_identity_and_survives_copied_attacks():
    m = member("general", resource_bound=True)
    evaluation = construct_payoffs(m.context, m.manifest, m.contract, m.attacks)
    assert evaluation.outcomes
    assert m.contract.execution_configuration_id == m.contract.resource_manifest.manifest_id
    with pytest.raises(ValueError, match="manifest digest"):
        ExecutionContract(**{**m.contract.model_dump(), "execution_configuration_id": "unbound"})


@pytest.mark.parametrize("mode", ["missing", "mismatch", "stable", "drift"])
def test_runtime_observed_resources_fail_closed_before_rng_or_after_drift(mode):
    m = member("general", resource_bound=True)
    policy, _ = fit_policy(m.context, m.manifest, m.contract, m.attacks)
    artifact = export_artifact(policy, m.context, m.manifest, m.contract, m.attacks, applicable_domain="general")
    orchestrator, checkers, _, rng = runtime_fixture(artifact=artifact)
    manifest = m.contract.resource_manifest
    altered = manifest.model_dump()
    altered["verifiers"][0]["resources"][0]["sha256"] = "c" * 64
    changed = ResourceManifest(**altered)
    class Observer:
        calls = 0
        def snapshot(self):
            self.calls += 1
            return changed if mode == "mismatch" or (mode == "drift" and self.calls > 1) else manifest
    observer = None if mode == "missing" else Observer()
    orchestrator._game_runtime = replace(orchestrator._game_runtime, resource_observer=observer)
    response = orchestrator.validate(ValidationRequest(question="q", answer="a"))
    if mode in {"missing", "mismatch"}:
        assert response.execution_audit["selection_status"] == "provenance_incompatible"
        assert rng.calls == 0 and sum(c.calls for c in checkers) == 0
    else:
        assert rng.calls == 1
        assert response.execution_audit["observed_resource_manifest_id"] == manifest.manifest_id
        if mode == "drift":
            assert response.final_status == "uncertain"
            assert "resource_provenance_changed_during_execution" in response.execution_audit["override_reasons"]


def test_legacy_optional_fields_do_not_change_serialized_contract_or_records():
    context, manifest, contract, _ = fixture()
    assert "resource_manifest" not in contract.model_dump()
    assert "pooling_contract_json" not in context.model_dump()
    assert "observed_resources_json" not in manifest.partition("history").examples[0].attempts[0].model_dump()


@pytest.mark.parametrize("name,missing", [("semantic", "model"), ("evidence", "corpus"), ("confidence", "prompt")])
def test_builtin_resource_kinds_are_required(name, missing):
    with pytest.raises(ValueError, match=missing):
        VerifierResources(verifier_name=name, resources=(
            ResourceFingerprint(resource_id="code", kind="implementation", sha256="a" * 64),
            ResourceFingerprint(resource_id="config", kind="configuration", sha256="b" * 64)))


def test_pool_cannot_be_refit_as_one_domain():
    members, (_, fitted, _) = pooled()
    domain, context, _ = fitted[0]
    original = next(m for m in members if m.context.plan.domain == domain)
    with pytest.raises(ValueError, match="target-only matrix"):
        construct_payoffs(context, original.manifest, original.contract, original.attacks)


def test_readiness_reports_resource_locations_without_execution(monkeypatch):
    from app.game.research.readiness import check_readiness
    from app.game.research.specification import ExperimentSpecification
    from tests.test_game_research import study, REVISION
    m = member("general", resource_bound=True)
    data = study(names=("a", "b")).model_dump()
    data.update(context=m.context.model_dump(), manifest=m.manifest.model_dump(),
                contract=m.contract.model_dump())
    for description in data["datasets"]:
        description["dataset_id"] = m.manifest.partition(description["role"]).dataset_id
    data["recording"]["execution_configuration_id"] = m.contract.execution_configuration_id
    spec = ExperimentSpecification(**data)
    assert check_readiness(spec, actual_code_revision=REVISION).ready
    data = spec.model_dump()
    example = data["manifest"]["partitions"][0]["examples"][0]
    example["attempts"][0]["observed_resources_json"] = None
    spec = ExperimentSpecification(**data)
    import app.game.solver as solver
    monkeypatch.setattr(solver, "solve_minimax", lambda *a, **kw: pytest.fail("no readiness fitting"))
    report = check_readiness(spec, actual_code_revision=REVISION)
    assert not report.ready and len(report.resource_blockers) == 1
    assert report.resource_blockers[0].example_id == example["example_id"]
    assert report.resource_blockers[0].verifier_name == "a"


def test_readiness_requires_resource_bound_contract_for_empirical_study():
    from app.game.research.readiness import check_readiness
    from app.game.research.specification import ExperimentSpecification
    from tests.test_game_research import study, REVISION
    data = study().model_dump()
    data["manifest"]["evidence_kind"] = "empirical"
    data["context"]["provenance"]["evidence_kind"] = "empirical"
    spec = ExperimentSpecification(**data)
    report = check_readiness(spec, actual_code_revision=REVISION)
    assert not report.ready
    assert "empirical_study_requires_resource_bound_execution_v2" in report.blockers


def revise_member(m, *, manifest_data=None, candidate_capability=None):
    """Rebind synthetic inputs without manufacturing history statistics."""
    data = m.context.model_dump()
    data.update(offline_evaluation_id=None, execution_contract_json=None)
    plan = json.loads(data["selection_json"])
    if candidate_capability is not None:
        plan["candidates"][0]["expected_capabilities"].append(candidate_capability)
    data["selection_json"] = canonical_json(plan)
    context = PlanningContext(**data)
    manifest_data = manifest_data or m.manifest.model_dump()
    for part in manifest_data["partitions"]:
        for example in part["examples"]:
            example["planning_category"] = category_id(context)
    manifest = DatasetManifest(**manifest_data)
    return PoolMember(context=bind_evaluation(context, manifest, m.contract, m.attacks),
                      manifest=manifest, contract=m.contract, attacks=m.attacks)


def test_pool_rejects_different_candidate_contract_even_with_identical_actions():
    from app.game.strategies import enumerate_strategies
    a, b = member("general"), revise_member(member("science"), candidate_capability="semantic_comparison")
    assert enumerate_strategies(a.context).strategies == enumerate_strategies(b.context).strategies
    with pytest.raises(ValueError, match="semantics"):
        fit_pooled_policies((a, b), pool_id="synthetic", source_weights=(("general", .5), ("science", .5)))


@pytest.mark.parametrize("change", ["missing_source", "different_context"])
def test_pool_lineage_requires_consistent_source_applicability(change):
    from app.game.pooling_contract import PoolingContract
    _, (pool, _, _) = pooled()
    data = pool.model_dump()
    data["applicability"] = tuple((d, "different" if change == "different_context" and d == "science" else digest)
        for d, digest in data["applicability"] if not (change == "missing_source" and d == "science"))
    with pytest.raises(ValueError, match="source.*applicability"):
        PoolingContract(**data)


def test_pool_fits_one_shared_distribution_even_with_multiple_optimal_mixtures(monkeypatch):
    import app.game.policy as policy_module
    from app.game.solver import solution_diagnostics
    real_solve = policy_module.solve_minimax
    calls = []
    def alternating_optimum(matrix):
        solution = real_solve(matrix)
        calls.append(matrix.matrix_id)
        probabilities = dict(solution.probabilities)
        chosen = next(i for i, s in enumerate(matrix.strategy_ids) if probabilities[s] > 0)
        alternatives = [i for i, row in enumerate(matrix.values) if row == matrix.values[chosen]]
        replacement = alternatives[len(calls) % len(alternatives)]
        values = tuple(float(i == replacement) for i in range(len(matrix.strategy_ids)))
        diagnostics = solution_diagnostics(matrix, values, tuple(p for _, p in solution.attack_probabilities), solution.tolerance)
        return solution.model_copy(update={**diagnostics, "probabilities": tuple(zip(matrix.strategy_ids, values))})
    monkeypatch.setattr(policy_module, "solve_minimax", alternating_optimum)
    _, (_, fitted, _) = pooled()
    assert len(calls) == 1
    assert len({policy.solution.probabilities for _, _, policy in fitted}) == 1


def history_member(domain, *, unregistered_b=False):
    from dataclasses import asdict
    from app.game.offline.records import history_reputation
    from tests.test_game_offline import report
    m = member(domain)
    manifest_data = m.manifest.model_dump()
    history = next(p for p in manifest_data["partitions"] if p["role"] == "history")
    for attempt in history["examples"][0]["attempts"]:
        if attempt["verifier_name"] == "a" or not unregistered_b:
            attempt.update(state="directional", report_json=report(attempt["verifier_name"]).model_dump_json())
    manifest = DatasetManifest(**manifest_data)
    manager = history_reputation(manifest, prior_alpha=m.contract.history_prior_alpha, prior_beta=m.contract.history_prior_beta)
    data = m.context.model_dump()
    data.update(offline_evaluation_id=None, execution_contract_json=None)
    plan = json.loads(data["selection_json"])
    statistics = manager.statistics_batch(tuple((c["verifier_name"], domain) for c in plan["candidates"]))
    plan["reputation_statistics"] = [asdict(s) for s in statistics]
    for candidate, s in zip(plan["candidates"], statistics):
        candidate.update(reputation=round(s.posterior_mean, 6), observation_count=s.observation_count, cold_start=s.cold_start)
        if unregistered_b and candidate["verifier_name"] == "b":
            candidate["registered"] = False
            candidate["eligible"] = False
    data["selection_json"] = canonical_json(plan)
    context = PlanningContext(**data)
    for part in manifest_data["partitions"]:
        for example in part["examples"]:
            example["planning_category"] = category_id(context)
    manifest = DatasetManifest(**manifest_data)
    return PoolMember(context=bind_evaluation(context, manifest, m.contract, m.attacks), manifest=manifest,
                      contract=m.contract, attacks=m.attacks)


@pytest.mark.parametrize("threshold,expected", [(1, False), (2, True)])
@pytest.mark.parametrize("unregistered_b", [False, True])
def test_sparse_route_boundary_uses_frozen_registered_participants(threshold, expected, unregistered_b):
    members = tuple(history_member(d, unregistered_b=unregistered_b) for d in ("general", "science"))
    _, fitted, _ = fit_pooled_policies(members, pool_id="synthetic", source_weights=(("general", .5), ("science", .5)))
    _, context, _ = next(f for f in fitted if f[0] == "general")
    route = DomainRoute(direct_episode=episode(members[0].context, members[0].contract, "direct"),
        pooled_episode=episode(context, members[0].contract, "pooled"), minimum_history_observations=threshold)
    assert route.history_observations == 1 and route.is_sparse == expected
    with pytest.raises(ValueError):
        DomainRoute(**{**route.model_dump(), "minimum_history_observations": True})


def test_pool_uses_each_domains_distinct_history_and_unequal_example_counts():
    a, b = member("general"), history_member("science")
    assert a.context.reputation_snapshot_id != b.context.reputation_snapshot_id
    data = b.manifest.model_dump()
    development = next(p for p in data["partitions"] if p["role"] == "development")
    original = development["examples"][0]
    other = json.loads(json.dumps(original))
    other.update(example_id="science/extra", question_id="science/extra", question="science extra", validation_id="science/extra")
    other["answer_is_correct"] = False
    for attempt in other["attempts"]:
        attempt["execution_id"] = other["validation_id"]
    development["examples"] = (original, other)
    b = revise_member(b, manifest_data=data)
    pool, fitted, evaluations = fit_pooled_policies((a, b), pool_id="synthetic", source_weights=(("general", .25), ("science", .75)))
    ea, eb = dict(evaluations)["general"], dict(evaluations)["science"]
    for _, context, policy in fitted:
        assert unpooled_context(context).reputation_snapshot_id == (a if context.plan.domain == "general" else b).context.reputation_snapshot_id
        for row, ar, br in zip(policy.matrix.values, ea.matrix.values, eb.matrix.values):
            assert row == pytest.approx(tuple(.25*x + .75*y for x, y in zip(ar, br)))
    # Pure one-member clean row: .25 * 0 + .75 * .5 error loss + .1 cost.
    assert fitted[0][2].matrix.values[0][0] == pytest.approx(.475)


def test_target_development_labels_do_not_enter_pool_fit():
    sources = (member("general"), member("science"))
    target = member("history")
    first = fit_pooled_policies((*sources, target), pool_id="synthetic", source_weights=(("general", .5), ("science", .5)))
    data = target.manifest.model_dump()
    next(p for p in data["partitions"] if p["role"] == "development")["examples"][0]["answer_is_correct"] = False
    changed = revise_member(target, manifest_data=data)
    other = fit_pooled_policies((*sources, changed), pool_id="synthetic", source_weights=(("general", .5), ("science", .5)))
    assert [p.matrix.values for _, _, p in first[1]] == [p.matrix.values for _, _, p in other[1]]
    assert [p.solution.probabilities for _, _, p in first[1]] == [p.solution.probabilities for _, _, p in other[1]]
    assert first[0].pooling_id != other[0].pooling_id


def test_single_domain_research_workflow_explicitly_rejects_pooled_context():
    from tests.test_game_research import study, REVISION
    from app.game.research.specification import ExperimentSpecification
    from app.game.research.readiness import check_readiness
    members, (_, fitted, _) = pooled()
    domain, context, _ = next(f for f in fitted if f[0] == "general")
    original = next(m for m in members if m.context.plan.domain == domain)
    data = study(names=("a", "b")).model_dump()
    data.update(context=context, manifest=original.manifest, contract=original.contract)
    for description in data["datasets"]:
        description["dataset_id"] = original.manifest.partition(description["role"]).dataset_id
    result = check_readiness(ExperimentSpecification(**data), actual_code_revision=REVISION)
    assert not result.ready and "pooled_context_requires_explicit_multi_domain_workflow" in result.blockers


@pytest.mark.parametrize("mode", ["invalid_before", "invalid_after", "programming_error"])
def test_resource_observer_invalid_snapshots_and_programming_failures(mode):
    m = member("general", resource_bound=True)
    policy, _ = fit_policy(m.context, m.manifest, m.contract, m.attacks)
    artifact = export_artifact(policy, m.context, m.manifest, m.contract, m.attacks, applicable_domain="general")
    orchestrator, checkers, _, rng = runtime_fixture(artifact=artifact)
    class Observer:
        calls = 0
        def snapshot(self):
            self.calls += 1
            if mode == "programming_error":
                raise RuntimeError("synthetic observer bug")
            if mode == "invalid_before" or (mode == "invalid_after" and self.calls == 2):
                return {"verifiers": []}
            return m.contract.resource_manifest
    orchestrator._game_runtime = replace(orchestrator._game_runtime, resource_observer=Observer())
    if mode == "programming_error":
        with pytest.raises(RuntimeError, match="observer bug"):
            orchestrator.validate(ValidationRequest(question="q", answer="a"))
        assert rng.calls == 0 and all(c.calls == 0 for c in checkers)
    else:
        result = orchestrator.validate(ValidationRequest(question="q", answer="a"))
        assert result.final_status == "uncertain"
        assert rng.calls == (1 if mode == "invalid_after" else 0)
        if mode == "invalid_after":
            assert result.execution_audit["estimated_attempted_cost"] > 0
            assert "resource_provenance_changed_during_execution" in result.execution_audit["override_reasons"]


def test_pooled_v2_runtime_isolated_from_offline_and_optimization(tmp_path):
    import subprocess
    import sys
    members = tuple(member(d, resource_bound=True) for d in ("general", "science"))
    _, fitted, _ = fit_pooled_policies(members, pool_id="synthetic", source_weights=(("general", .5), ("science", .5)))
    _, context, policy = next(f for f in fitted if f[0] == "general")
    m = members[0]
    artifact = export_artifact(policy, context, m.manifest, m.contract, m.attacks, applicable_domain="general")
    path = tmp_path / "synthetic-pooled-v2.json"
    path.write_text(artifact.model_dump_json(), encoding="utf-8")
    code = r'''
import importlib.abc, sys
from pathlib import Path
class DenyOffline(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.startswith('app.game.offline'):
            raise AssertionError('runtime imported offline fitting')
sys.meta_path.insert(0, DenyOffline())
from app.game.artifacts import PolicyArtifact, DeploymentEpisode
from app.game.domain_routing import DomainRoute
from app.game.pooling_contract import unpooled_context
from app.game.execution import GameRuntime
from app.selection.verifier_selector import VerifierSelector
from app.selection.capabilities import CapabilityDescriptor
from app.models.schemas import VerificationResult, ValidationRequest
from app.verifiers.base_verifier import BaseVerifier
from app.analysis.models import QuestionAnalysis, QuestionResearchContext
import app.game.solver as solver
def forbidden(*args, **kwargs): raise AssertionError('runtime optimizer call')
solver.linprog = forbidden
solver.solve_minimax = forbidden
artifact = PolicyArtifact.model_validate_json(Path(sys.argv[1]).read_text(encoding='utf-8'))
class Checker(BaseVerifier):
    def __init__(self, name): self._name, self.calls = name, 0
    @property
    def name(self): return self._name
    def verify(self, *args):
        self.calls += 1
        return VerificationResult(verifier_name=self.name, passed=True, score=1., metadata={
            'decision':'SUPPORT','rule_kind':'factual','rule':'arithmetic_addition'})
class Provider:
    calls = 0
    def snapshot(self): self.calls += 1; return (artifact,)
class RNG:
    calls = 0
    def random(self): self.calls += 1; return .2
class Observer:
    calls = 0
    def snapshot(self): self.calls += 1; return artifact.contract.resource_manifest
checkers = [Checker(c.verifier_name) for c in artifact.context.plan.candidates]
selector = VerifierSelector(verifiers=checkers, capabilities={c.name:CapabilityDescriptor(('arithmetic',)) for c in checkers},
    difficulty_range={'hard':(1,1)})
context = artifact.context
contract = artifact.contract
direct = DeploymentEpisode(episode_id='direct', context=unpooled_context(context), contract=contract,
    execution_configuration_id=contract.execution_configuration_id)
pooled = DeploymentEpisode(episode_id='pooled', context=context, contract=contract,
    execution_configuration_id=contract.execution_configuration_id)
route = DomainRoute(direct_episode=direct, pooled_episode=pooled, minimum_history_observations=1)
provider, rng, observer = Provider(), RNG(), Observer()
runtime = GameRuntime(provider, direct, rng, True, resource_observer=observer, domain_routes=(route,))
analysis = QuestionAnalysis('general','hard',.8,domain_status='known',verification_types=['arithmetic'],
    research_context=QuestionResearchContext('question_context_v1',['arithmetic'],{'arithmetic':1.},True,None,'known','heuristic','rubric_v1'))
result = runtime.run(selector, analysis, ValidationRequest(question='synthetic',answer='synthetic'), 'synthetic-run')
assert result.summary['selection_status'] == 'selected', result.summary
assert result.summary['policy_route'] == 'pooled'
assert provider.calls == 1 and rng.calls == 1 and observer.calls == 2
assert sum(c.calls for c in checkers) == len(result.summary['team'])
assert not any(n.startswith('app.game.offline') or n.startswith('app.database') for n in sys.modules)
'''
    result = subprocess.run([sys.executable, "-B", "-c", code, str(path)], text=True, capture_output=True)
    assert result.returncode == 0, result.stdout + result.stderr
