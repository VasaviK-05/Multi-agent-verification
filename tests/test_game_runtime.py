"""Synthetic deployment fixtures only; no empirical policy or production inputs."""

from dataclasses import asdict
import json
from pathlib import Path
import random
import subprocess
import sys

import pytest
from pydantic import ValidationError

from app.game.artifacts import DeploymentEpisode, InMemoryPolicyProvider, PolicyArtifact
from app.game.execution import GameRuntime, VerifierExecutionFailure
from app.game.execution_contract import ExecutionContract
from app.game.models import PayoffMatrix, PlanningContext, canonical_json
from app.game.offline.attacks import enumerate_attacks
from app.game.offline.evaluation import export_artifact, fit_policy
from app.game.offline.replay import replay
from app.game.policy import build_policy
from app.game.strategies import enumerate_strategies
from app.models.schemas import ValidationRequest
from app.orchestration.validation_orchestrator import ValidationOrchestrator, RUN_SUMMARY_KEY
from app.reputation.reputation_manager import ReputationManager
from app.selection.capabilities import CapabilityDescriptor
from app.selection.models import VerifierUnavailable
from app.selection.verifier_selector import VerifierSelector
from app.verifiers.base_verifier import BaseVerifier
from tests.test_game_foundation import analysis
from tests.test_game_offline import fixture, report, attempt


class CountingRNG:
    def __init__(self, value=.2):
        self.value, self.calls = value, 0

    def random(self):
        self.calls += 1
        return self.value


class Checker(BaseVerifier):
    def __init__(self, name, behavior=None):
        self._name, self.behavior, self.calls = name, behavior, 0

    @property
    def name(self):
        return self._name

    def verify(self, question, answer, context=None):
        self.calls += 1
        if isinstance(self.behavior, Exception):
            raise self.behavior
        if callable(self.behavior):
            return self.behavior()
        return self.behavior if self.behavior is not None else report(self.name)


class Analyzer:
    def __init__(self, value=None):
        self.value = value or analysis()
        if value is None:
            self.value.difficulty, self.value.difficulty_score = 'hard', .8

    def analyze(self, question):
        return self.value


@pytest.fixture(autouse=True)
def persistence_boundaries(monkeypatch):
    import app.orchestration.validation_orchestrator as module
    # Main now persists complete snapshots as well as aggregate rows. Keep the
    # existing offline test boundary around both; decision/feedback logic is real.
    monkeypatch.setattr(module, "load_reputation_manager_state", lambda: None)
    monkeypatch.setattr(module, "save_reputation_state_and_rows", lambda state: None)
    monkeypatch.setattr(module, 'build_reputation_state', lambda: ReputationManager().export_state())
    monkeypatch.setattr(module, 'save_reputation', lambda **kw: None)
    monkeypatch.setattr(module, 'save_reputation_state_and_rows', lambda state: None)
    monkeypatch.setattr(module.AutomaticGroundTruthEvaluator, 'evaluate', lambda *a, **kw: None)


def artifact_fixture(*, names=('a', 'b', 'c'), team=('a', 'b'), aggregation='dependency_group', failure='all_selected_returned'):
    context, manifest, contract, specification = fixture(names=names, failure=failure)
    strategies = enumerate_strategies(context).strategies
    actions = enumerate_attacks(context.dependencies, specification)
    # Explicit solver fixture: one preferred strategy; never called empirical.
    values = tuple(tuple(0. if s.verifiers == team and s.aggregation == aggregation else 1. for _ in actions) for s in strategies)
    matrix = PayoffMatrix(strategy_ids=tuple(s.strategy_id for s in strategies),
        strategy_definitions=strategies, attack_ids=tuple(a.attack_id for a in actions), values=values,
        compatibility_id=context.compatibility_id)
    policy = build_policy(context, matrix)
    artifact = export_artifact(policy, context, manifest, contract, specification, applicable_domain='general')
    return artifact, manifest, specification


def runtime_fixture(*, artifact=None, behaviors=None, allow=True, provider=None, episode=None, analyzer=None):
    artifact = artifact or artifact_fixture()[0]
    manager = ReputationManager()
    names = tuple(c.verifier_name for c in artifact.context.plan.candidates)
    checkers = [Checker(n, (behaviors or {}).get(n)) for n in names]
    selector = VerifierSelector(verifiers=checkers, reputation_manager=manager,
        capabilities={n: CapabilityDescriptor(('arithmetic',)) for n in names}, difficulty_range={'hard': (1, 1)})
    episode = episode or DeploymentEpisode(episode_id='fixture-episode', context=artifact.context,
        contract=artifact.contract, execution_configuration_id=artifact.execution_configuration_id)
    provider = provider if provider is not None else InMemoryPolicyProvider((artifact,))
    rng = CountingRNG()
    runtime = GameRuntime(provider, episode, rng, allow_synthetic_for_tests=allow)
    run = ValidationOrchestrator(question_analyzer=analyzer or Analyzer(), verifier_selector=selector,
        reputation_manager=manager, execution_mode='game', game_runtime=runtime)
    return run, checkers, manager, rng


@pytest.mark.parametrize('aggregation', ['reputation_weighted', 'dependency_group'])
def test_exact_complete_team_and_one_sample_no_early_stop_or_fallback(aggregation, monkeypatch):
    artifact, _, _ = artifact_fixture(aggregation=aggregation)
    run, checkers, manager, rng = runtime_fixture(artifact=artifact)
    monkeypatch.setattr(run._early_termination, 'should_terminate', lambda *a, **k: pytest.fail('no early stopping'))
    monkeypatch.setattr(manager, 'statistics_batch', lambda *a: pytest.fail('no live planning read'))
    before = manager.export_state()
    response = run.validate(ValidationRequest(question='fixture question', answer='fixture answer'))
    assert response.final_status == 'passed' and response.signed_score == 1.
    assert response.selected_verifiers == ['a', 'b'] and [c.calls for c in checkers] == [1, 1, 0]
    assert rng.calls == 1 and manager.export_state() == before
    audit = response.execution_audit
    assert audit['aggregation'] == aggregation and audit['estimated_attempted_cost'] == 2.
    assert audit['policy_id'] == artifact.policy.policy_id and audit['matrix_id'] == artifact.policy.matrix.matrix_id
    assert audit['reputation_snapshot_id'] == artifact.context.reputation_snapshot_id
    assert not audit['early_stopping_enabled'] and not audit['fallback_enabled']


@pytest.mark.parametrize('mode', ['missing', 'ambiguous', 'incompatible', 'synthetic'])
def test_selection_failures_are_uncertain_without_dispatch(mode):
    artifact, _, _ = artifact_fixture()
    if mode == 'missing':
        provider = InMemoryPolicyProvider()
    elif mode == 'ambiguous':
        provider = InMemoryPolicyProvider((artifact, artifact))
    elif mode == 'incompatible':
        class UntrustedProvider:
            def snapshot(self):
                return (artifact.model_copy(update={'execution_configuration_id': 'wrong'}),)
        provider = UntrustedProvider()
    else:
        provider = InMemoryPolicyProvider((artifact,))
    run, checkers, _, rng = runtime_fixture(artifact=artifact, provider=provider, allow=mode != 'synthetic')
    response = run.validate(ValidationRequest(question='q', answer='a'))
    assert response.final_status == 'uncertain' and response.results == []
    assert all(c.calls == 0 for c in checkers) and rng.calls == 0
    assert response.execution_audit['selection_status'] in {'missing_policy', 'ambiguous_policy', 'incompatible'}
    assert response.execution_audit['selection_reasons']


@pytest.mark.parametrize('change', ['threshold', 'failure_contract', 'configuration', 'version', 'reputation'])
def test_artifact_rejects_contract_or_context_tampering(change):
    artifact, _, _ = artifact_fixture()
    data = artifact.model_dump()
    if change == 'threshold': data['contract']['threshold'] = .7
    elif change == 'failure_contract': data['contract']['failure_contract'] = 'allow_failed_if_covered'
    elif change == 'configuration': data['execution_configuration_id'] = 'different'
    elif change == 'version': data['contract']['coverage_version'] = 'future'
    else:
        plan = artifact.context.plan
        from dataclasses import replace
        data['context']['selection_json'] = canonical_json(asdict(replace(plan,
            reputation_statistics=tuple(replace(s, posterior_mean=.9) for s in plan.reputation_statistics))))
    with pytest.raises(ValueError):
        PolicyArtifact(**data)


@pytest.mark.parametrize('change', ['candidate', 'requirement', 'budget', 'dependency', 'reference', 'analyzer'])
def test_current_inputs_require_exact_compatibility_without_dispatch(change):
    artifact, _, _ = artifact_fixture()
    episode = None
    if change in {'budget', 'dependency'}:
        context = artifact.context.model_dump()
        if change == 'budget': context['budget'] = 0.
        else: context['dependencies']['version'] = 'different'
        episode = DeploymentEpisode(episode_id='new-settings', context=PlanningContext(**context), contract=artifact.contract,
                                    execution_configuration_id=artifact.execution_configuration_id)
    run, checkers, _, rng = runtime_fixture(artifact=artifact, episode=episode)
    request = ValidationRequest(question='q', answer='a', context='reference' if change == 'reference' else None)
    if change == 'candidate':
        run.verifier_selector._capabilities['b'] = CapabilityDescriptor(('consistency',))
    elif change == 'requirement':
        run._question_analyzer = Analyzer(analysis(('consistency',)))
    elif change == 'analyzer':
        run._question_analyzer.value.analysis_method = 'different'
    response = run.validate(request)
    assert response.final_status == 'uncertain' and response.results == []
    assert all(c.calls == 0 for c in checkers) and rng.calls == 0


@pytest.mark.parametrize('failure', ['all_selected_returned', 'allow_failed_if_covered'])
@pytest.mark.parametrize('exception', [VerifierUnavailable, VerifierExecutionFailure])
def test_identified_execution_failures_record_cost_and_apply_contract(failure, exception):
    artifact, _, _ = artifact_fixture(failure=failure)
    run, checkers, _, _ = runtime_fixture(artifact=artifact, behaviors={'b': exception('fixture failure')})
    response = run.validate(ValidationRequest(question='q', answer='a'))
    expected = 'uncertain' if failure == 'all_selected_returned' else 'passed'
    assert response.final_status == expected and response.signed_score == 1.
    assert response.execution_audit['estimated_attempted_cost'] == 2.
    assert response.execution_audit['attempts'][1]['state'] == ('unavailable' if exception is VerifierUnavailable else 'failed')
    assert [c.calls for c in checkers] == [1, 1, 0]


@pytest.mark.parametrize('behavior', [ValueError('bug'), RuntimeError('bug'),
    {'unexpected': 'dict'}, report('wrong'),
    report('b', metadata={'decision': 'SUPPORT', 'validation_id': 'wrong-run'}),
    report('b').model_copy(update={'score': float('nan')})])
def test_programming_errors_and_malformed_outputs_never_become_learning_votes(behavior):
    run, _, manager, _ = runtime_fixture(behaviors={'b': behavior})
    before = manager.export_state()
    with pytest.raises((ValueError, RuntimeError, TypeError)):
        run.validate(ValidationRequest(question='q', answer='a'))
    assert manager.export_state() == before and not run._contexts and not run._result_binding


def test_frozen_episode_survives_feedback_and_provider_replacement_mid_run():
    artifact, _, _ = artifact_fixture()
    provider = InMemoryPolicyProvider((artifact,))
    run, checkers, manager, _ = runtime_fixture(artifact=artifact, provider=provider)
    def changing():
        provider.replace(())
        for _ in range(10): manager.update_reputation('b', 'general', False)
        return report('a')
    checkers[0].behavior = changing
    response = run.validate(ValidationRequest(question='q', answer='a'))
    assert response.final_status == 'passed' and response.signed_score == 1.
    assert response.execution_audit['reputation_snapshot_id'] == artifact.context.reputation_snapshot_id
    assert run.verifier_selector.reputation_manager is manager
    assert run.validate(ValidationRequest(question='q', answer='a')).results == []


def test_detached_audit_and_existing_external_feedback_identity_binding():
    run, _, manager, _ = runtime_fixture()
    response = run.validate(ValidationRequest(question='q', answer='a'))
    snapshot = run.validation_context(response.validation_id)
    assert response.results[-1].metadata[RUN_SUMMARY_KEY] == response.execution_audit
    response.execution_audit['team'].clear()
    assert run.validation_context(response.validation_id).run_summary['team'] == ['a', 'b']
    assert run.record_ground_truth(response.results, False, validation_id=response.validation_id) == 2
    assert run.record_ground_truth(response.results, False, validation_id=response.validation_id) == 0
    assert manager.observation_count('a', 'general') == 1
    assert snapshot.results[0].metadata['decision'] == 'SUPPORT'

    assert manager.observation_count('a', 'general') == 1
    assert snapshot.results[0].metadata['decision'] == 'SUPPORT'


def test_effective_configuration_fingerprint_is_stable():
    run, _, _, _ = runtime_fixture()

    first = run.validate(ValidationRequest(question='q', answer='a'))
    second = run.validate(ValidationRequest(question='q', answer='a'))

    first_fingerprint = first.execution_audit['effective_configuration_fingerprint']
    second_fingerprint = second.execution_audit['effective_configuration_fingerprint']

    assert first_fingerprint
    assert first_fingerprint == second_fingerprint


@pytest.mark.parametrize('aggregation', ['reputation_weighted', 'dependency_group'])
@pytest.mark.parametrize('case', ['directional', 'abstention', 'zero', 'unavailable', 'failed', 'gap', 'structural'])
def test_runtime_offline_public_decision_parity(aggregation, case):
    artifact, manifest, spec = artifact_fixture(aggregation=aggregation)
    row = report('b')
    if case == 'abstention': row = report('b', metadata={'decision': 'UNSURE'})
    elif case == 'zero': row = report('b', strength=0.)
    elif case == 'gap': row = report('b', metadata={'decision': 'SUPPORT'})
    elif case == 'structural':
        # Current structural exclusion is scoped to the rule verifier identity.
        artifact, manifest, spec = artifact_fixture(names=('a', 'rule'), team=('a', 'rule'), aggregation=aggregation)
        row = report('rule', metadata={'decision': 'SUPPORT', 'rule_kind': 'structural', 'rule': 'email_regex'})
    second = artifact.policy.strategies[next(i for i, (_, p) in enumerate(artifact.policy.solution.probabilities) if p > 0)].verifiers[-1]
    behavior = VerifierUnavailable('fixture') if case == 'unavailable' else VerifierExecutionFailure('fixture') if case == 'failed' else row
    run, _, _, _ = runtime_fixture(artifact=artifact, behaviors={second: behavior})
    response = run.validate(ValidationRequest(question='q', answer='a'))
    state = 'unavailable' if case == 'unavailable' else 'failed' if case == 'failed' else 'abstention' if case == 'abstention' else 'directional'
    example = manifest.partition('development').examples[0]
    recorded = []
    for name in (c.verifier_name for c in artifact.context.plan.candidates):
        if name == second:
            recorded.append(attempt(name, state=state, row=None if state in {'unavailable', 'failed'} else row,
                                    adapter='rule_v1' if name == 'rule' else 'generic_v1'))
        else: recorded.append(attempt(name))
    example = example.model_copy(update={'attempts': tuple(recorded)})
    strategy = next(s for s in artifact.policy.strategies if s.strategy_id == response.execution_audit['selected_strategy_id'])
    expected = replay(artifact.context, strategy, enumerate_attacks(artifact.context.dependencies, spec)[0], spec, artifact.contract, example)
    audit = response.execution_audit
    assert response.final_status == expected.public_status and response.signed_score == expected.numerical_score
    assert audit['numerical_decision']['status'] == expected.numerical_status
    assert audit['contributors'] == expected.contributors
    assert tuple(audit['achieved']) == expected.achieved and tuple(audit['unresolved']) == expected.unresolved
    assert tuple(audit['override_reasons']) == expected.reasons
    assert audit['estimated_attempted_cost'] == expected.estimated_attempt_cost


def test_artifact_json_imports_and_runtime_do_not_load_offline_or_call_optimizer(tmp_path):
    artifact, _, _ = artifact_fixture()
    path = tmp_path/'fixture-artifact.json';path.write_text(artifact.model_dump_json(), encoding='utf-8')
    work = Path(__file__).resolve().parents[1]
    code = '''import sys, importlib.abc
class NoOffline(importlib.abc.MetaPathFinder):
 def find_spec(self, fullname, path=None, target=None):
  if fullname.startswith('app.game.offline'): raise AssertionError('runtime imported offline data')
sys.meta_path.insert(0, NoOffline())
from app.game.artifacts import PolicyArtifact
from pathlib import Path
artifact = PolicyArtifact.model_validate_json(Path(sys.argv[1]).read_text())
import app.game.policy as p
p.solve_minimax = lambda *a, **kw: (_ for _ in ()).throw(AssertionError('optimizer called'))
from app.game.execution import GameRuntime
from app.game.artifacts import InMemoryPolicyProvider, DeploymentEpisode
from app.game.policy import sample_policy
import random
from app.analysis.models import QuestionAnalysis, QuestionResearchContext
from app.models.schemas import ValidationRequest, VerificationResult
from app.reputation.reputation_manager import ReputationManager
from app.selection.capabilities import CapabilityDescriptor
from app.selection.verifier_selector import VerifierSelector
from app.verifiers.base_verifier import BaseVerifier
class Checker(BaseVerifier):
 def __init__(self, name): self._name = name
 @property
 def name(self): return self._name
 def verify(self, question, answer, context=None):
  return VerificationResult(verifier_name=self.name, score=1., passed=True,
   metadata={'decision':'SUPPORT', 'rule_kind':'factual', 'rule':'arithmetic_addition'})
names = [c.verifier_name for c in artifact.context.plan.candidates]
selector = VerifierSelector(verifiers=[Checker(n) for n in names], reputation_manager=ReputationManager(),
 capabilities={n:CapabilityDescriptor(('arithmetic',)) for n in names}, difficulty_range={'hard':(1,1)})
analysis = QuestionAnalysis('general', 'hard', .8, domain_status='known', verification_types=['arithmetic'],
 research_context=QuestionResearchContext('question_context_v1', ['arithmetic'], {'arithmetic':1.},
 True, None, 'known', 'heuristic', 'rubric_v1'))
episode = DeploymentEpisode(episode_id='fresh-process', context=artifact.context, contract=artifact.contract,
 execution_configuration_id=artifact.execution_configuration_id)
runtime = GameRuntime(InMemoryPolicyProvider((artifact,)), episode, random.Random(2), allow_synthetic_for_tests=True)
result = runtime.run(selector, analysis, ValidationRequest(question='q',answer='a'), 'fresh-run')
assert result.public_status == 'passed'
assert not any(n.startswith('app.game.offline') for n in sys.modules)
assert not any(n.startswith('app.database') for n in sys.modules)
'''
    subprocess.run([sys.executable, '-c', code, str(path)], cwd=work, check=True)


def test_server_mode_is_explicit_and_request_cannot_supply_policies():
    with pytest.raises(ValueError, match='server-configured'):
        ValidationOrchestrator(execution_mode='game')
    run, _, _, _ = runtime_fixture()
    request = ValidationRequest(question='q', answer='a').model_copy(update={'policy': 'untrusted', 'execution_mode': 'baseline'})
    assert run.validate(request).execution_audit['execution_mode'] == 'game'


def test_reproducible_sampling_with_injected_rng():
    artifact, _, _ = artifact_fixture()
    first, _, _, _ = runtime_fixture(artifact=artifact)
    second, _, _, _ = runtime_fixture(artifact=artifact)
    request = ValidationRequest(question='q', answer='a')
    assert first.validate(request).execution_audit['selected_strategy_id'] == second.validate(request).execution_audit['selected_strategy_id']


def test_legacy_opaque_offline_binding_cannot_be_claimed_as_deployable_contract():
    artifact, _, _ = artifact_fixture()
    context = artifact.context.model_copy(update={'execution_contract_json': None})
    with pytest.raises(ValueError):
        PolicyArtifact(**{**artifact.model_dump(), 'context': context})


@pytest.mark.parametrize('case,label', [('abstention', 'abstentions'), ('zero', 'zero_confidence'), ('unavailable', 'unknown')])
@pytest.mark.parametrize('aggregation', ['reputation_weighted', 'dependency_group'])
def test_empty_and_inactive_team_audits_preserve_numerical_distinctions(case, label, aggregation):
    artifact, _, _ = artifact_fixture(aggregation=aggregation)
    behaviors = {n: VerifierUnavailable('fixture') if case == 'unavailable' else
        report(n, metadata={'decision': 'UNSURE'}) if case == 'abstention' else report(n, strength=0.) for n in ('a', 'b')}
    run, checkers, manager, _ = runtime_fixture(artifact=artifact, behaviors=behaviors)
    before = manager.export_state()
    response = run.validate(ValidationRequest(question='q', answer='a'))
    assert response.final_status == 'uncertain' and response.signed_score == 0.
    assert response.execution_audit['numerical_decision']['aggregation'] == label
    assert response.execution_audit['estimated_attempted_cost'] == 2.
    assert [c.calls for c in checkers] == [1, 1, 0] and manager.export_state() == before


def test_decisive_numerical_result_is_overridden_by_actual_coverage_gap():
    run, _, _, _ = runtime_fixture(behaviors={n: report(n, metadata={'decision': 'SUPPORT'}) for n in ('a', 'b')})
    response = run.validate(ValidationRequest(question='q', answer='a'))
    assert response.signed_score == 1. and response.final_status == 'uncertain'
    assert response.execution_audit['numerical_decision']['status'] == 'passed'
    assert response.execution_audit['unresolved'] == ['arithmetic']


def test_budget_failure_does_not_construct_any_default_verifier(monkeypatch):
    from app.selection.verifier_selector import DEFAULT_VERIFIER_ORDER
    import app.selection.verifier_selector as selectors
    artifact, _, _ = artifact_fixture(names=DEFAULT_VERIFIER_ORDER, team=('rule',))
    data = artifact.context.model_dump();data['budget'] = 0.
    episode = DeploymentEpisode(episode_id='zero-budget', context=PlanningContext(**data), contract=artifact.contract,
                                execution_configuration_id=artifact.execution_configuration_id)
    manager = ReputationManager()
    selector = VerifierSelector(reputation_manager=manager)
    monkeypatch.setattr(selectors, '_build_default_verifier', lambda *a: pytest.fail('budget rejection must precede construction'))
    runtime = GameRuntime(InMemoryPolicyProvider((artifact,)), episode, CountingRNG(), allow_synthetic_for_tests=True)
    run = ValidationOrchestrator(question_analyzer=Analyzer(), verifier_selector=selector,
        execution_mode='game', game_runtime=runtime, reputation_manager=manager)
    response = run.validate(ValidationRequest(question='q', answer='a'))
    assert response.results == [] and response.final_status == 'uncertain' and selector._cache == {}


def test_explicit_pooled_artifact_registration_keeps_domain_compatibility():
    artifact, _, _ = artifact_fixture()
    data = artifact.context.model_dump()
    data['provenance'].update(category_kind='pooled', category='explicit-fixture-pool')
    context = PlanningContext(**data)
    matrix = PayoffMatrix(**{**artifact.policy.matrix.model_dump(), 'compatibility_id': context.compatibility_id})
    policy = build_policy(context, matrix)
    pooled = PolicyArtifact(policy=policy, context=context, contract=artifact.contract,
        execution_configuration_id=artifact.execution_configuration_id, applicable_domain='general')
    run, _, _, _ = runtime_fixture(artifact=pooled)
    assert run.validate(ValidationRequest(question='q', answer='a')).final_status == 'passed'
    with pytest.raises(ValueError, match='applicability'):
        PolicyArtifact(**{**pooled.model_dump(), 'applicable_domain': 'medical'})


def test_relabeling_contract_and_context_still_rejects_old_matrix_and_policy():
    artifact, _, _ = artifact_fixture()
    data = artifact.model_dump();data['contract']['threshold'] = .8
    data['context']['execution_contract_json'] = canonical_json(data['contract'])
    with pytest.raises(ValueError, match='incompatible'):
        PolicyArtifact(**data)


def test_new_episode_with_new_reputation_cannot_reuse_old_policy():
    from app.game.models import capture_context
    artifact, _, _ = artifact_fixture()
    run, checkers, manager, rng = runtime_fixture(artifact=artifact)
    manager.update_reputation('a', 'general', True)
    configuration = artifact.context.model_dump(exclude={'selection_json', 'analyzer_provenance'})
    changed = capture_context(run.verifier_selector, Analyzer().value, **configuration)
    new_episode = DeploymentEpisode(episode_id='new-history', context=changed, contract=artifact.contract,
        execution_configuration_id=artifact.execution_configuration_id)
    run._game_runtime = GameRuntime(InMemoryPolicyProvider((artifact,)), new_episode, rng, allow_synthetic_for_tests=True)
    response = run.validate(ValidationRequest(question='q', answer='a'))
    assert response.final_status == 'uncertain' and all(c.calls == 0 for c in checkers) and rng.calls == 0


def test_artifact_provider_detaches_caller_owned_serialized_inputs():
    artifact, _, _ = artifact_fixture()
    data = artifact.model_dump(mode='json')
    loaded = PolicyArtifact(**data)
    provider = InMemoryPolicyProvider((loaded,))
    data['policy']['matrix']['values'][0][0] = 999.
    data['contract']['threshold'] = .99
    assert provider.snapshot()[0].artifact_id == artifact.artifact_id
    assert provider.snapshot()[0].contract.threshold == .55

def test_deployment_loader_rejects_baseline_mode(monkeypatch):
    from app.game import deployment

    monkeypatch.setattr(deployment.settings, "EXECUTION_MODE", "baseline")
    with pytest.raises(ValueError, match="EXECUTION_MODE=game"):
        deployment.create_game_runtime()


def test_deployment_loader_requires_artifact_path(monkeypatch):
    from app.game import deployment

    monkeypatch.setattr(deployment.settings, "EXECUTION_MODE", "game")

    monkeypatch.setattr(
        deployment.settings,
        "GAME_POLICY_BUNDLE_PATH",
        None,
    )

    monkeypatch.setattr(deployment.settings, "GAME_POLICY_ARTIFACT_PATH", "")
    with pytest.raises(RuntimeError, match="GAME_POLICY_ARTIFACT_PATH"):
        deployment.create_game_runtime()


def test_deployment_loader_rejects_missing_artifact(monkeypatch, tmp_path):
    from app.game import deployment

    monkeypatch.setattr(deployment.settings, "EXECUTION_MODE", "game")

    monkeypatch.setattr(
        deployment.settings,
        "GAME_POLICY_BUNDLE_PATH",
        None,
    )

    monkeypatch.setattr(
        deployment.settings, "GAME_POLICY_ARTIFACT_PATH",
        str(tmp_path / "missing-policy.json"),
    )
    with pytest.raises(FileNotFoundError, match="artifact does not exist"):
        deployment.create_game_runtime()


def test_deployment_loader_rejects_invalid_artifact(monkeypatch, tmp_path):
    from app.game import deployment

    artifact_path = tmp_path / "invalid-policy.json"
    artifact_path.write_text('{"version": "invalid"}', encoding="utf-8")
    monkeypatch.setattr(deployment.settings, "EXECUTION_MODE", "game")

    monkeypatch.setattr(
        deployment.settings,
        "GAME_POLICY_BUNDLE_PATH",
        None,
    )

    monkeypatch.setattr(
        deployment.settings, "GAME_POLICY_ARTIFACT_PATH", str(artifact_path)
    )
    with pytest.raises(ValueError, match="Invalid game deployment artifact"):
        deployment.create_game_runtime()


def test_validation_service_uses_baseline_mode(monkeypatch):
    from app.services import validation_service

    created = {}

    class FakeOrchestrator:
        def __init__(self, *args, **kwargs):
            created["args"] = args
            created["kwargs"] = kwargs

    monkeypatch.setattr(
        validation_service.settings, "EXECUTION_MODE", "baseline"
    )
    monkeypatch.setattr(
        validation_service, "ValidationOrchestrator", FakeOrchestrator
    )

    service = validation_service.ValidationService()

    assert isinstance(service._orchestrator, FakeOrchestrator)
    assert created["kwargs"] == {}


def test_validation_service_uses_game_mode(monkeypatch):
    from app.services import validation_service
    from app.game import deployment

    fake_runtime = object()
    created = {}

    class FakeOrchestrator:
        def __init__(self, *args, **kwargs):
            created["kwargs"] = kwargs

    monkeypatch.setattr(
        validation_service.settings, "EXECUTION_MODE", "game"
    )
    monkeypatch.setattr(
        deployment, "create_game_runtime", lambda: fake_runtime
    )
    monkeypatch.setattr(
        validation_service, "ValidationOrchestrator", FakeOrchestrator
    )

    service = validation_service.ValidationService()

    assert isinstance(service._orchestrator, FakeOrchestrator)
    assert created["kwargs"]["execution_mode"] == "game"
    assert created["kwargs"]["game_runtime"] is fake_runtime


def test_validation_service_rejects_invalid_execution_mode(monkeypatch):
    from app.services import validation_service

    monkeypatch.setattr(
        validation_service.settings, "EXECUTION_MODE", "invalid"
    )

    with pytest.raises(ValueError, match="EXECUTION_MODE"):
        validation_service.ValidationService()


def test_deployment_loader_loads_valid_artifact(monkeypatch, tmp_path):
    from app.game import deployment

    artifact, _, _ = artifact_fixture()
    artifact_path = tmp_path / "valid-policy.json"
    artifact_path.write_text(
        artifact.model_dump_json(),
        encoding="utf-8",
    )

    monkeypatch.setattr(deployment.settings, "EXECUTION_MODE", "game")

    monkeypatch.setattr(
        deployment.settings,
        "GAME_POLICY_BUNDLE_PATH",
        None,
    )

    monkeypatch.setattr(
        deployment.settings,
        "GAME_POLICY_ARTIFACT_PATH",
        str(artifact_path),
    )
    monkeypatch.setattr(
        deployment.settings, "GAME_EPISODE_ID", "loader-test-episode"
    )

    runtime = deployment.create_game_runtime()

    assert isinstance(runtime, GameRuntime)
    assert runtime.episode.episode_id == "loader-test-episode"
    assert runtime.episode.execution_configuration_id == artifact.execution_configuration_id
    assert runtime.provider.snapshot()[0].policy.policy_id == artifact.policy.policy_id
    assert runtime.allow_synthetic_for_tests is False

