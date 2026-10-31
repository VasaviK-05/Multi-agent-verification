"""Controlled synthetic adapters; no model, network, historical data or test labels."""
import hashlib
import json

import pytest

from app.game.artifacts import InMemoryPolicyProvider, PolicyArtifact, DeploymentEpisode
from app.game.finalization import finalize_decision
from app.game.models import canonical_json, content_id
from app.game.offline.collection import RecordingRequest, RecordingBundle, collect
from app.game.offline.replay import ReplayContract
from app.game.offline.upstream import (UpstreamExperiment, UpstreamFit, ScenarioRecording,
    EvidenceIntervention, construct_upstream_payoffs, fit_upstream)
from app.game.resource_provenance import ResourceManifest
from app.models.schemas import VerificationResult
from tests.test_game_collection import fixture, Checker, Observer


class CorpusChecker(Checker):
    def __init__(self, name, corpus):
        super().__init__(name)
        self.corpus = corpus

    def verify(self, question, answer, context=None):
        self.calls.append((question, answer, context))
        # A real read of isolated fixture bytes, never a transformed clean report.
        support = self.corpus.read_text() == answer
        return VerificationResult(verifier_name=self.name, passed=support, score=1.,
            metadata={'decision': 'SUPPORT' if support else 'REJECT',
                      'rule_kind': 'factual', 'rule': 'arithmetic_addition'})


def experiment_fixture(tmp_path):
    request, _, setup, _, context, attacks = fixture()
    clean_path, altered_path = tmp_path/'clean.txt', tmp_path/'altered.txt'
    clean_path.write_text('SYNTHETIC answer')
    altered_path.write_text('SYNTHETIC different answer')
    data = setup.resources.model_dump(mode='json')
    data['verifiers'][0]['resources'].append(dict(kind='corpus', resource_id='fixture-corpus',
        sha256=hashlib.sha256(clean_path.read_bytes()).hexdigest()))
    resources = ResourceManifest.model_validate(data)
    setup = type(setup).model_validate({**setup.model_dump(), 'resources': resources})
    request = RecordingRequest.model_validate({**request.model_dump(), 'expected_setup': setup,
        'execution_configuration_id': resources.manifest_id})
    clean_pool = [CorpusChecker('a', clean_path), Checker('b', VerificationResult(
        verifier_name='b', passed=True, score=1., metadata={'decision': 'SUPPORT', 'rule_kind': 'factual',
                                                         'rule': 'arithmetic_addition'}))]
    clean = collect(request, clean_pool, setup, Observer(resources))
    # Freeze meaningful positive weights strictly from independently labelled
    # synthetic HISTORY; development labels never establish reputation.
    from app.game.offline.collection import export_training
    from app.game.offline.records import history_reputation
    from app.game.models import capture_context
    from app.selection.verifier_selector import VerifierSelector
    from app.selection.capabilities import CapabilityDescriptor
    manager = history_reputation(export_training(clean, context), prior_alpha=1., prior_beta=1.)
    selector = VerifierSelector(verifiers=clean_pool, reputation_manager=manager,
        capabilities={n: CapabilityDescriptor(('arithmetic',)) for n in ('a', 'b')},
        difficulty_range={'hard': (1, 1), 'easy': (1, 1)})
    context = capture_context(selector, request.examples[0].analysis,
        **context.model_dump(exclude={'selection_json', 'analyzer_provenance'}))
    changed = resources.model_dump(mode='json')
    for r in changed['verifiers'][0]['resources']:
        if r['kind'] == 'corpus':
            r['sha256'] = hashlib.sha256(altered_path.read_bytes()).hexdigest()
    altered = ResourceManifest.model_validate(changed)
    altered_setup = type(setup).model_validate({**setup.model_dump(), 'resources': altered})
    examples = [{**e.model_dump(), 'run_id': 'poison-'+e.run_id}
                for e in request.examples if e.role == 'development']
    altered_request = RecordingRequest.model_validate({**request.model_dump(),
        'examples': examples, 'expected_setup': altered_setup,
        'execution_configuration_id': altered.manifest_id})
    declaration = dict(version='upstream_evidence_intervention_v1', name='SYNTHETIC replacement',
        affected_resource='fixture-corpus', alteration='replace fixture text with a different answer',
        scope='one synthetic development corpus', provenance='controlled synthetic file writes',
        clean_resources=resources, altered_resources=altered, affected_verifiers=('a',),
        timing='committed_before_collection_and_team_sampling',
        knowledge='public_questions_references_and_clean_resources_no_labels_no_sampled_team',
        reuse_contract='complete_team_independent_within_fixed_scenario_v1',
        reuse_attestation='SYNTHETIC stateless adapters, fixed bytes, no team or prefix input',
        request_id=altered_request.request_id)
    pool = [CorpusChecker('a', altered_path), Checker('b')]
    bundle = collect(altered_request, pool, altered_setup, Observer(altered))
    contract = ReplayContract(version='offline_public_decision_v2', coverage_version='factual_output_contract_v1',
        contributor_version='baseline_log_odds_active_group_v1', threshold=.55,
        failure_contract='all_selected_returned', history_prior_alpha=1., history_prior_beta=1.,
        execution_configuration_id=resources.manifest_id, resource_manifest=resources)
    experiment = UpstreamExperiment(version='upstream_evidence_experiment_v1', clean=clean,
        context=context, contract=contract, report_attacks=attacks,
        scenarios=(ScenarioRecording(intervention=declaration, bundle=bundle),))
    assert clean_pool[0].calls and pool[0].calls
    return experiment


def test_actual_collection_payoff_fit_export_reload_and_retained_runtime_parity(tmp_path):
    experiment = experiment_fixture(tmp_path)
    clean = next(a for a in experiment.clean.attempts if a.example_id == 'development' and a.candidate == 'a')
    poisoned = next(a for a in experiment.scenarios[0].bundle.attempts if a.candidate == 'a')
    assert clean.attempt.report.passed and not poisoned.attempt.report.passed
    fitted = fit_upstream(experiment)
    path = tmp_path/'fit.json'
    path.write_text(fitted.model_dump_json())
    restored = UpstreamFit.model_validate_json(path.read_text())
    artifact = PolicyArtifact.model_validate_json(restored.artifact.model_dump_json())
    assert InMemoryPolicyProvider((artifact,)).snapshot() == (artifact,)
    DeploymentEpisode(episode_id='fixture', context=artifact.context, contract=artifact.contract,
                      execution_configuration_id=artifact.execution_configuration_id)
    context, matrix, _, outcomes = construct_upstream_payoffs(experiment)
    assert matrix == artifact.policy.matrix
    assert artifact.contract.resource_manifest == experiment.contract.resource_manifest
    assert artifact.contract.resource_manifest != experiment.scenarios[0].intervention.altered_resources
    assert len(artifact.policy.strategies) == len(matrix.strategy_ids)
    assert sum(p for _, p in artifact.policy.solution.probabilities) == pytest.approx(1.)
    assert any(row[0] != row[-1] for row in matrix.values)
    # Runtime and replay use the identical public finalizer. No verifier dispatch.
    for strategy in artifact.policy.strategies:
        selected = [a.attempt for a in experiment.clean.attempts
                    if a.example_id == 'development' and a.candidate in strategy.verifiers]
        selected.sort(key=lambda a: strategy.verifiers.index(a.verifier_name))
        result = finalize_decision(context, strategy, artifact.contract,
            [a.report for a in selected if a.report is not None],
            tuple((a.verifier_name, a.state) for a in selected), 'development')
        replayed = next(o for o in outcomes if o.strategy_id == strategy.strategy_id
                        and o.attack_id == matrix.attack_ids[0])
        assert (result.public_status, result.reasons) == (replayed.public_status, replayed.reasons)
    bad = restored.model_dump(mode='json')
    bad['artifact']['policy']['matrix']['values'][0][-1] += .01
    with pytest.raises(ValueError):
        UpstreamFit.model_validate(bad)


@pytest.mark.parametrize('change', ['missing', 'label', 'split', 'resource', 'request', 'reuse', 'clean-identity'])
def test_reject_mismatched_or_missing_scenario_records(tmp_path, change):
    experiment = experiment_fixture(tmp_path)
    data = experiment.model_dump(mode='json')
    scenario = data['scenarios'][0]
    if change == 'missing':
        scenario['bundle']['attempts'].pop()
    elif change == 'label':
        scenario['bundle']['request']['examples'][0]['label']['answer_is_correct'] = False
    elif change == 'split':
        scenario['bundle']['request']['examples'][0]['role'] = 'history'
    elif change == 'resource':
        scenario['bundle']['attempts'][0]['attempt']['observed_resources_json'] = canonical_json(
            experiment.clean.observed_setup.resources.verifiers[0].model_dump(mode='json'))
    elif change == 'request':
        scenario['intervention']['request_id'] = 'wrong'
    elif change == 'reuse':
        scenario['intervention']['reuse_contract'] = 'complete_team_independent_v1'
    else:
        scenario['intervention']['altered_resources'] = scenario['intervention']['clean_resources']
    with pytest.raises(ValueError):
        UpstreamExperiment.model_validate(data)


def test_incidental_timings_do_not_change_scientific_fit_identity(tmp_path):
    experiment = experiment_fixture(tmp_path)
    data = experiment.model_dump(mode='json')
    for bundle in [data['clean'], data['scenarios'][0]['bundle']]:
        for attempt in bundle['attempts']:
            attempt['duration_ms'] *= 2
            attempt['measurement']['duration_ms'] *= 2
    repeated = UpstreamExperiment.model_validate(data)
    assert experiment.experiment_id == repeated.experiment_id
    assert construct_upstream_payoffs(experiment)[1] == construct_upstream_payoffs(repeated)[1]


def test_validly_recollected_label_change_is_still_rejected(tmp_path):
    experiment = experiment_fixture(tmp_path)
    scenario = experiment.scenarios[0]
    data = scenario.bundle.request.model_dump(mode='json')
    data['examples'][0]['label']['answer_is_correct'] = False
    request = RecordingRequest.model_validate(data)
    bundle = collect(request, [Checker('a'), Checker('b')], scenario.bundle.observed_setup,
                     Observer(scenario.intervention.altered_resources))
    altered = ScenarioRecording(intervention={**scenario.intervention.model_dump(), 'request_id': request.request_id},
                                bundle=bundle)
    with pytest.raises(ValueError, match='independent label'):
        UpstreamExperiment.model_validate({**experiment.model_dump(), 'scenarios': [altered]})


def test_real_runtime_rejects_experimental_resources_before_dispatch(tmp_path):
    from app.game.execution import GameRuntime
    from app.selection.verifier_selector import VerifierSelector
    from app.selection.capabilities import CapabilityDescriptor
    from app.models.schemas import ValidationRequest
    from tests.test_game_foundation import analysis
    import random
    experiment = experiment_fixture(tmp_path)
    artifact = fit_upstream(experiment).artifact
    pool = [Checker('a'), Checker('b')]
    selector = VerifierSelector(verifiers=pool,
        capabilities={n: CapabilityDescriptor(('arithmetic',)) for n in ('a', 'b')},
        difficulty_range={'hard': (1, 1)})
    episode = DeploymentEpisode(episode_id='fixture', context=artifact.context, contract=artifact.contract,
                                execution_configuration_id=artifact.execution_configuration_id)
    runtime = GameRuntime(InMemoryPolicyProvider((artifact,)), episode, random.Random(42),
        allow_synthetic_for_tests=True, resource_observer=Observer(experiment.scenarios[0].intervention.altered_resources))
    a = analysis(); a.difficulty, a.difficulty_score = 'hard', .8
    result = runtime.run(selector, a, ValidationRequest(question='development question', answer='SYNTHETIC answer'), 'run')
    assert result.public_status == 'uncertain'
    assert not any(c.calls for c in pool)
    assert result.summary['selection_status'] == 'provenance_incompatible'
    assert result.summary['observed_resource_manifest_id'] == experiment.scenarios[0].intervention.altered_resources.manifest_id
    clean_runtime = GameRuntime(InMemoryPolicyProvider((artifact,)), episode, random.Random(42),
        allow_synthetic_for_tests=True, resource_observer=Observer(experiment.contract.resource_manifest))
    clean = clean_runtime.run(selector, a,
        ValidationRequest(question='development question', answer='SYNTHETIC answer'), 'clean-run')
    assert clean.summary['selection_status'] == 'selected'
    _, matrix, _, outcomes = construct_upstream_payoffs(experiment)
    retained = next(o for o in outcomes if o.strategy_id == clean.summary['selected_strategy_id']
                    and o.attack_id == matrix.attack_ids[0])
    assert clean.public_status == retained.public_status


def test_cli_fit_and_reload_uses_only_retained_synthetic_recordings(tmp_path, monkeypatch):
    from scripts.upstream_evidence_experiment import main
    experiment = experiment_fixture(tmp_path)
    path = tmp_path/'experiment.json'; path.write_text(experiment.model_dump_json())
    monkeypatch.setattr(Checker, 'verify', lambda *a, **k: pytest.fail('no fresh inference during fit'))
    monkeypatch.setattr(CorpusChecker, 'verify', lambda *a, **k: pytest.fail('no fresh inference during fit'))
    assert main(['validate', '--experiment', str(path)]) == 0
    assert main(['fit', '--experiment', str(path), '--output-dir', str(tmp_path/'output')]) == 0
    restored = UpstreamFit.model_validate_json((tmp_path/'output/fit.json').read_text())
    report = json.loads((tmp_path/'output/development.json').read_text())
    assert report['artifact_id'] == restored.artifact.artifact_id
    assert 'validation_loss' in report['policy_metrics'][0]
    assert 'mean_loss' in report['policy_metrics'][0]


def test_resource_intervention_cannot_hide_index_or_sampling_changes(tmp_path):
    from tests.preparation_fixtures import synthetic_adapter_file
    experiment = experiment_fixture(tmp_path)
    data = experiment.scenarios[0].intervention.model_dump(mode='json')
    for field in ('clean_resources', 'altered_resources'):
        data[field]['verifiers'][0]['resources'].append(dict(kind='index', resource_id='synthetic-index', sha256='a'*64))
    with pytest.raises(ValueError, match='rebuilt'):
        EvidenceIntervention.model_validate(data)
    data = experiment.scenarios[0].intervention.model_dump(mode='json')
    path, _ = synthetic_adapter_file(tmp_path)
    before = json.loads(path.read_text())
    after = {**before, 'corpus_path': 'SYNTHETIC/isolated/corpus.json', 'index_dir': 'SYNTHETIC/isolated/index'}
    excluded = {'embedding_snapshot', 'nli_snapshot', 'index_receipt', 'service_observation'}
    for field, config in [('clean_resources', before), ('altered_resources', after)]:
        for verifier in data[field]['verifiers']:
            for resource in verifier['resources']:
                if resource['kind'] == 'configuration':
                    resource['sha256'] = content_id({k: v for k, v in config.items() if k not in excluded})
    data.update(clean_adapter_json=json.dumps(before), altered_adapter_json=json.dumps(after),
                affected_verifiers=['a', 'b'])
    EvidenceIntervention.model_validate(data)
    after['temperature'] += .1
    data['altered_adapter_json'] = json.dumps(after)
    with pytest.raises(ValueError, match='sampling'):
        EvidenceIntervention.model_validate(data)


def test_scenario_request_requires_new_authority_and_preserves_independent_inputs(tmp_path):
    from app.game.offline.upstream import scenario_request
    experiment = experiment_fixture(tmp_path)
    request = scenario_request(experiment.clean.request, experiment.scenarios[0].bundle.observed_setup,
        name='predeclared fixture', preparation_authorization='NEW synthetic permission', study_approval=None)
    assert {e.role for e in request.examples} == {'development'}
    original = [e for e in experiment.clean.request.examples if e.role == 'development']
    for before, after in zip(original, request.examples):
        assert before.label == after.label
        assert before.split_identity == after.split_identity
        assert before.run_id != after.run_id
    assert request.preparation_authorization == 'NEW synthetic permission'
    with pytest.raises(ValueError, match='distinct altered resources'):
        scenario_request(experiment.clean.request, experiment.clean.observed_setup,
            name='fixture', preparation_authorization='NEW permission', study_approval=None)


def test_task_aware_contract_and_history_binding_are_retained(tmp_path):
    from app.game.offline.collection import export_training
    from app.game.task_conditioning import bind_task_history
    experiment = experiment_fixture(tmp_path)
    manifest = export_training(experiment.clean, experiment.context)
    context = bind_task_history(experiment.context, manifest)
    contract = ReplayContract.model_validate({**experiment.contract.model_dump(),
        'version': 'offline_public_decision_v4', 'coverage_version': 'task_output_contract_v2',
        'contributor_version': 'informative_history_influence_v1'})
    updated = UpstreamExperiment.model_validate({**experiment.model_dump(), 'context': context, 'contract': contract})
    result = fit_upstream(updated)
    assert result.artifact.context.task_conditioning_json == context.task_conditioning_json
    assert result.artifact.contract == contract
    assert result.artifact.context.plan.reputation_statistics == context.plan.reputation_statistics
    UpstreamFit.model_validate_json(result.model_dump_json())


def test_fitting_is_pure_no_final_payload_access_or_production_writes(tmp_path, monkeypatch):
    import builtins
    import pathlib
    experiment = experiment_fixture(tmp_path)
    expected = fit_upstream(experiment)  # Warm solver/import machinery before the IO guard.
    def forbidden(*args, **kwargs):
        pytest.fail('pure retained-record fitter attempted filesystem access')
    monkeypatch.setattr(builtins, 'open', forbidden)
    monkeypatch.setattr(pathlib.Path, 'open', forbidden)
    result = fit_upstream(experiment)
    assert result.artifact == expected.artifact
    assert result.artifact.context.plan.reputation_statistics == experiment.context.plan.reputation_statistics


def test_isolated_preparation_and_failure_before_output(tmp_path):
    from scripts.upstream_evidence_experiment import prepare
    from tests.preparation_fixtures import synthetic_adapter_file
    adapter, _ = synthetic_adapter_file(tmp_path)
    corpus = tmp_path/'original.json'
    corpus.write_text(json.dumps([dict(id='fixture', text='clean', url='https://example.invalid/')]))
    data = json.loads(adapter.read_text()); data['corpus_path'] = str(corpus)
    adapter.write_text(json.dumps(data))
    raw = corpus.read_bytes()
    spec = dict(version='isolated_corpus_replacements_v1', scope='fixture only', provenance='synthetic',
        timing='committed_before_collection_and_team_sampling',
        knowledge='public_questions_references_and_clean_resources_no_labels_no_sampled_team',
        clean_corpus_sha256=hashlib.sha256(raw).hexdigest(), replacements=[dict(record_id='fixture',
            expected_text_sha256=hashlib.sha256(b'clean').hexdigest(), replacement_text='altered')])
    alterations = tmp_path/'alterations.json'; alterations.write_text(json.dumps(spec))
    out = tmp_path/'isolated'
    receipt = prepare(adapter, alterations, out)
    assert corpus.read_bytes() == raw
    assert json.loads((out/'corpus.json').read_text())[0]['text'] == 'altered'
    assert receipt['clean_corpus_sha256'] != receipt['altered_corpus_sha256']
    spec['replacements'][0]['expected_text_sha256'] = '0'*64
    alterations.write_text(json.dumps(spec))
    with pytest.raises(ValueError, match='digest mismatch'):
        prepare(adapter, alterations, tmp_path/'must-not-exist')
    assert not (tmp_path/'must-not-exist').exists()


def test_unexecuted_returned_reports_are_not_fresh_scenario_recordings(tmp_path):
    from app.game.offline.collection import completeness
    experiment = experiment_fixture(tmp_path)
    data = experiment.scenarios[0].model_dump(mode='json')
    row = data['bundle']['attempts'][0]
    row.update(executed=False, duration_ms=None, timing_status=None, measurement=None,
               after_resources_json=None)
    # Establish the underlying schema gap without weakening the shared collector.
    bundle = RecordingBundle.model_validate(data['bundle'])
    assert completeness(bundle)['complete']
    with pytest.raises(ValueError, match='unexecuted outcomes'):
        ScenarioRecording.model_validate(data)


@pytest.mark.parametrize('duplicate', ['attempt', 'scenario'])
def test_duplicate_scenario_data_rejected(tmp_path, duplicate):
    data = experiment_fixture(tmp_path).model_dump(mode='json')
    if duplicate == 'attempt':
        data['scenarios'][0]['bundle']['attempts'].append(data['scenarios'][0]['bundle']['attempts'][0])
    else:
        data['scenarios'].append(data['scenarios'][0])
    with pytest.raises(ValueError, match='duplicate'):
        UpstreamExperiment.model_validate(data)


def test_changed_shared_configuration_cannot_be_presented_as_unaffected(tmp_path):
    from tests.preparation_fixtures import synthetic_adapter_file
    data = experiment_fixture(tmp_path).scenarios[0].intervention.model_dump(mode='json')
    path, _ = synthetic_adapter_file(tmp_path)
    before = json.loads(path.read_text())
    after = {**before, 'corpus_path': 'SYNTHETIC/other/corpus.json', 'index_dir': 'SYNTHETIC/other/index'}
    excluded = {'embedding_snapshot', 'nli_snapshot', 'index_receipt', 'service_observation'}
    digest = lambda c: content_id({k: v for k, v in c.items() if k not in excluded})
    for field in ('clean_resources', 'altered_resources'):
        for verifier in data[field]['verifiers']:
            for resource in verifier['resources']:
                if resource['kind'] == 'configuration':
                    resource['sha256'] = digest(after if field == 'altered_resources' and verifier['verifier_name'] == 'a' else before)
    data.update(clean_adapter_json=json.dumps(before), altered_adapter_json=json.dumps(after))
    with pytest.raises(ValueError, match='every project adapter entry'):
        EvidenceIntervention.model_validate(data)


@pytest.mark.parametrize('variant', ['coverage', 'reliability'])
def test_unsupported_objective_is_rejected_not_silently_replaced(tmp_path, variant):
    from app.game.offline.collection import export_training
    from app.game.offline.evaluation import bind_evaluation, construct_payoffs
    from app.game.offline.coverage import prepare_clean_coverage
    from app.game.offline.reliability import prepare_reliability_first
    experiment = experiment_fixture(tmp_path)
    contract = experiment.contract
    if variant == 'reliability':
        contract = ReplayContract.model_validate({**contract.model_dump(), 'version': 'offline_public_decision_v3',
            'contributor_version': 'informative_history_influence_v1'})
    manifest = export_training(experiment.clean, experiment.context)
    context = bind_evaluation(experiment.context, manifest, contract, experiment.report_attacks)
    evaluation = construct_payoffs(context, manifest, contract, experiment.report_attacks)
    prepare = prepare_clean_coverage if variant == 'coverage' else prepare_reliability_first
    constrained, _ = prepare(context, manifest, contract, experiment.report_attacks, evaluation, minimum=.25)
    with pytest.raises(ValueError, match='unpooled base objective'):
        UpstreamExperiment.model_validate({**experiment.model_dump(), 'context': constrained, 'contract': contract})


def test_scenario_failures_and_uncertainty_preserved_in_diagnostics(tmp_path):
    from app.game.execution import VerifierExecutionFailure
    experiment = experiment_fixture(tmp_path)
    scenario = experiment.scenarios[0]
    bundle = collect(scenario.bundle.request, [Checker('a', VerifierExecutionFailure('SYNTHETIC failure')), Checker('b')],
                     scenario.bundle.observed_setup, Observer(scenario.intervention.altered_resources))
    updated = UpstreamExperiment.model_validate({**experiment.model_dump(), 'scenarios': [
        dict(intervention=scenario.intervention, bundle=bundle)]})
    _, matrix, metrics, outcomes = construct_upstream_payoffs(updated)
    failed = [o for o in outcomes if o.attack_id == matrix.attack_ids[-1] and ('a', 'failed') in o.execution_states]
    assert failed and all(o.public_status == 'uncertain' and 'selected_execution_incomplete' in o.reasons for o in failed)
    assert any(m.uncertain for _, scenario_id, m in metrics if scenario_id == matrix.attack_ids[-1])
    fitted = fit_upstream(updated)
    assert len(fitted.artifact.policy.solution.probabilities) == len(matrix.strategy_ids)
    assert fitted.experiment.scenarios[0].bundle.attempts == bundle.attempts


def test_existing_clean_readiness_is_checked_when_specification_supplied(tmp_path):
    from app.game.offline.collection import export_training
    from app.game.offline.evaluation import bind_evaluation
    from app.game.research.specification import PolicyBuildSpecification
    from tests.test_game_research import study
    experiment = experiment_fixture(tmp_path)
    manifest = export_training(experiment.clean, experiment.context)
    bound = bind_evaluation(experiment.context, manifest, experiment.contract, experiment.report_attacks)
    original = study().model_dump()
    descriptions = {d['role']: d for d in original['datasets']}
    spec = PolicyBuildSpecification.model_validate({**original, 'version': 'offline_policy_build_v1',
        'manifest': manifest, 'context': bound, 'contract': experiment.contract, 'attacks': experiment.report_attacks,
        'code_revision': experiment.clean.observed_setup.code_revision,
        'datasets': [{**descriptions[role], 'dataset_id': manifest.partition(role).dataset_id}
                     for role in ('history', 'development', 'final_test')],
        'recording': {**original['recording'], 'execution_configuration_id': experiment.contract.execution_configuration_id}})
    updated = UpstreamExperiment.model_validate({**experiment.model_dump(), 'clean_build_specification': spec})
    assert fit_upstream(updated).experiment.clean_build_specification == spec
    bad = spec.model_dump(); bad['code_revision'] = '0'*40
    with pytest.raises(ValueError, match='readiness blocked.*code_revision_mismatch'):
        UpstreamExperiment.model_validate({**experiment.model_dump(), 'clean_build_specification': bad})


def test_claimed_empirical_inputs_cannot_bypass_readiness(tmp_path):
    """Negative schema test only: no artifact is fitted from this untrusted claim."""
    from app.game.offline.calibration import MeasurementSetup
    from app.game.models import PlanningContext
    experiment = experiment_fixture(tmp_path)
    clean_setup = MeasurementSetup.model_validate({**experiment.clean.observed_setup.model_dump(), 'evidence_kind': 'empirical'})
    clean_request = RecordingRequest.model_validate({**experiment.clean.request.model_dump(), 'expected_setup': clean_setup})
    clean = collect(clean_request, [CorpusChecker('a', tmp_path/'clean.txt'), Checker('b', VerificationResult(
        verifier_name='b', passed=True, score=1., metadata={'decision': 'SUPPORT'}))], clean_setup, Observer(clean_setup.resources))
    scenario = experiment.scenarios[0]
    altered_setup = MeasurementSetup.model_validate({**scenario.bundle.observed_setup.model_dump(), 'evidence_kind': 'empirical'})
    request = RecordingRequest.model_validate({**scenario.bundle.request.model_dump(), 'expected_setup': altered_setup})
    altered = collect(request, [CorpusChecker('a', tmp_path/'altered.txt'), Checker('b')], altered_setup, Observer(altered_setup.resources))
    context = PlanningContext.model_validate({**experiment.context.model_dump(), 'provenance': {
        **experiment.context.provenance.model_dump(), 'evidence_kind': 'empirical'}})
    with pytest.raises(ValueError, match='requires the clean PolicyBuildSpecification'):
        UpstreamExperiment(version='upstream_evidence_experiment_v1', clean=clean, context=context,
            contract=experiment.contract, report_attacks=experiment.report_attacks,
            scenarios=[dict(intervention={**scenario.intervention.model_dump(), 'request_id': request.request_id}, bundle=altered)])


def test_optional_evidence_validation_cannot_bind_unrelated_resources(tmp_path):
    from tests.test_game_evidence_validation import proof_data
    data = experiment_fixture(tmp_path).scenarios[0].model_dump(mode='json')
    data['evidence_validation'] = proof_data()  # Controlled doubles, never real NLI.
    with pytest.raises(ValueError, match='observed verifier resources differ'):
        ScenarioRecording.model_validate(data)


def test_project_factory_cannot_omit_isolated_path_configurations(tmp_path):
    experiment = experiment_fixture(tmp_path)
    scenario = experiment.scenarios[0]
    request = RecordingRequest.model_validate({**scenario.bundle.request.model_dump(),
        'factory': 'app.benchmark.project_adapter:create_recording_verifiers'})
    # No project factory is initialized: controlled adapters supply these negative-test calls.
    bundle = collect(request, [CorpusChecker('a', tmp_path/'altered.txt'), Checker('b')],
        scenario.bundle.observed_setup, Observer(scenario.intervention.altered_resources))
    with pytest.raises(ValueError, match='proving separate resource paths'):
        ScenarioRecording(intervention={**scenario.intervention.model_dump(), 'request_id': request.request_id}, bundle=bundle)
