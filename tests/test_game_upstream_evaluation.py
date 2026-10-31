"""Frozen synthetic policies only: changed evidence is not empirical security evidence."""
import hashlib
import json
import math

import pytest

from app.game.artifacts import PolicyArtifact, DeploymentEpisode
from app.game.models import PlanningContext, capture_context, canonical_json
from app.game.offline.collection import RecordingRequest, collect, export_training
from app.game.offline.evaluation import bind_evaluation, construct_payoffs, export_artifact
from app.game.offline.records import history_reputation
from app.game.offline.upstream import ScenarioRecording, scenario_request
from app.game.offline.upstream_evaluation import (FrozenUpstreamEvaluationInput,
    FrozenUpstreamEvaluation, evaluate_frozen_upstream, unbound_replay_context)
from app.game.execution_contract import ExecutionContract
from app.game.resource_provenance import ResourceManifest
from app.models.schemas import VerificationResult
from app.selection.capabilities import CapabilityDescriptor
from app.selection.verifier_selector import VerifierSelector
from tests.test_game_collection import fixture, Checker, Observer


class EvidenceFixture(Checker):
    def __init__(self, name, path=None):
        super().__init__(name)
        self.path = path

    def verify(self, question, answer, context=None):
        self.calls.append((question, answer, context))
        text = None if self.path is None else self.path.read_text()
        neutral = text in {None, 'SYNTHETIC poisoned'}
        passed = answer == text
        return VerificationResult(verifier_name=self.name, passed=passed, score=1., metadata={
            'decision': 'UNSURE' if neutral else ('SUPPORT' if passed else 'REJECT'),
            'rule_kind': 'factual', 'rule': 'arithmetic_addition'})


def frozen_fixture(tmp_path, variant):
    """Construct the original fixture BEFORE the optimizer-blocking evaluation boundary."""
    names = ('a', 'b', 'c')
    caps = {n: CapabilityDescriptor(('arithmetic',), requires_reference=True) for n in names}
    request, _, setup, _, initial, attacks = fixture(names=names, capabilities=caps)
    clean_path, altered_path = tmp_path/'clean.txt', tmp_path/'altered.txt'
    clean_path.write_text('SYNTHETIC answer'); altered_path.write_text('SYNTHETIC poisoned')
    raw = setup.resources.model_dump(mode='json')
    for verifier in raw['verifiers']:
        if verifier['verifier_name'] in {'a', 'b'}:
            verifier['resources'].append(dict(kind='corpus', resource_id='shared-fixture-corpus',
                sha256=hashlib.sha256(clean_path.read_bytes()).hexdigest()))
    resources = ResourceManifest.model_validate(raw)
    setup = type(setup).model_validate({**setup.model_dump(), 'resources': resources})
    examples = [{**e.model_dump(), 'reference': 'SYNTHETIC fixed reference'} for e in request.examples]
    examples.append({**examples[-1], 'example_id': 'development-wrong', 'run_id': 'development-wrong',
        'answer': 'SYNTHETIC incorrect answer', 'label': {**examples[-1]['label'], 'answer_is_correct': False}})
    request = RecordingRequest.model_validate({**request.model_dump(), 'examples': examples,
        'expected_setup': setup, 'execution_configuration_id': resources.manifest_id})
    pool = [EvidenceFixture(n, clean_path if n != 'c' else None) for n in names]
    clean = collect(request, pool, setup, Observer(resources))
    configuration = initial.model_dump(exclude={'selection_json', 'analyzer_provenance'})
    def context(manager=None):
        selector = VerifierSelector(verifiers=pool, reputation_manager=manager, capabilities=caps,
            difficulty_range={'hard': (2, 2), 'easy': (2, 2)})
        return capture_context(selector, request.examples[0].analysis, context=examples[0]['reference'], **configuration)
    cold = context()
    manager = history_reputation(export_training(clean, cold), prior_alpha=1., prior_beta=1.)
    base = context(manager)
    manifest = export_training(clean, base)
    from app.game.task_conditioning import bind_task_history
    base = bind_task_history(base, manifest)
    contract = ExecutionContract(version='offline_public_decision_v4', coverage_version='task_output_contract_v2',
        contributor_version='informative_history_influence_v1', threshold=.55,
        failure_contract='all_selected_returned', history_prior_alpha=1., history_prior_beta=1.,
        execution_configuration_id=resources.manifest_id, resource_manifest=resources)
    bound = bind_evaluation(base, manifest, contract, attacks)
    evaluation = construct_payoffs(bound, manifest, contract, attacks)
    if variant == 'coverage':
        from app.game.offline.coverage import fit_clean_coverage
        covered, policy = fit_clean_coverage(bound, manifest, contract, attacks, evaluation, minimum=.5)
    else:
        from app.game.offline.reliability import fit_reliability_first
        covered, policy = fit_reliability_first(bound, manifest, contract, attacks, evaluation, minimum=.5)
    artifact = export_artifact(policy, covered, manifest, contract, attacks, applicable_domain='general')
    altered_raw = resources.model_dump(mode='json')
    for verifier in altered_raw['verifiers']:
        for resource in verifier['resources']:
            if resource['kind'] == 'corpus':
                resource['sha256'] = hashlib.sha256(altered_path.read_bytes()).hexdigest()
    altered_resources = ResourceManifest.model_validate(altered_raw)
    altered_setup = type(setup).model_validate({**setup.model_dump(), 'resources': altered_resources})
    altered_request = scenario_request(request, altered_setup, name='fixed synthetic poisoning',
        preparation_authorization='SYNTHETIC new collection permission', study_approval=None)
    altered = collect(altered_request, [EvidenceFixture(n, altered_path if n != 'c' else None) for n in names],
                      altered_setup, Observer(altered_resources))
    scenario = ScenarioRecording(intervention=dict(version='upstream_evidence_intervention_v1',
        name='fixed synthetic poisoning', affected_resource='shared-fixture-corpus',
        alteration='replace fixture corpus text by neutral sentinel', scope='prepared development only',
        provenance='SYNTHETIC separate files; no correctness labels supplied to intervention',
        clean_resources=resources, altered_resources=altered_resources, affected_verifiers=('a', 'b'),
        timing='committed_before_collection_and_team_sampling',
        knowledge='public_questions_references_and_clean_resources_no_labels_no_sampled_team',
        reuse_contract='complete_team_independent_within_fixed_scenario_v1',
        reuse_attestation='SYNTHETIC stateless adapters, full roster freshly called, no team input',
        request_id=altered_request.request_id), bundle=altered)
    return artifact, clean, attacks, scenario


def block_optimization(monkeypatch):
    import app.game.solver as solver
    import app.game.policy as policy
    import app.game.offline.upstream as upstream
    import app.game.offline.evaluation as evaluation
    import scipy.optimize
    def forbidden(*a, **k):
        pytest.fail('evaluation invoked an optimizer/fitter')
    for module, name in [(solver, 'linprog'), (solver, 'solve_minimax'), (solver, 'solve_reliability_first'),
                         (policy, 'solve_minimax'), (policy, 'build_policy'), (upstream, 'fit_upstream'),
                         (upstream, 'build_policy'), (evaluation, 'fit_policy'), (scipy.optimize, 'linprog')]:
        monkeypatch.setattr(module, name, forbidden)


@pytest.mark.parametrize('variant', ['coverage', 'reliability'])
def test_frozen_variant_evaluation_never_optimizes_or_changes_original(tmp_path, monkeypatch, variant):
    artifact, clean, attacks, scenario = frozen_fixture(tmp_path, variant)
    original = artifact.model_dump_json()
    probabilities = artifact.policy.solution.probabilities
    block_optimization(monkeypatch)
    inputs = FrozenUpstreamEvaluationInput(artifact=artifact, clean=clean, report_attacks=attacks, scenarios=(scenario,))
    result = evaluate_frozen_upstream(inputs)
    assert artifact.model_dump_json() == original
    assert result.strategy_probabilities == probabilities
    assert len(result.scenario_metrics[0].per_strategy_metrics) == len(artifact.policy.strategies)
    assert any(p == 0 for _, p in probabilities)
    baseline, altered = result.scenario_metrics
    assert baseline.metrics.decision_coverage >= .5 - 1e-8
    qs = dict(artifact.policy.matrix.clean_coverage.strategy_coverage)
    assert baseline.metrics.decision_coverage == pytest.approx(math.fsum(p * qs[s] for s, p in probabilities))
    assert baseline.metrics.estimated_resource_cost == pytest.approx(math.fsum(
        dict(probabilities)[s.strategy_id] * s.estimated_cost for s in artifact.policy.strategies))
    assert tuple(s for s, _ in altered.per_strategy_metrics) == artifact.policy.matrix.strategy_ids
    assert altered.metrics.decision_coverage == 0 < result.original_clean_coverage_floor
    assert altered.metrics.selective_risk is None
    assert altered.metrics.false_accept == altered.metrics.false_reject == 0
    assert altered.uncertainty_rate == 1
    assert all('minimum_contributors' in o.reasons and 'missing_achieved_coverage' in o.reasons
               for o in result.outcomes if o.attack_id == scenario.intervention.scenario_id)
    assert altered.validation_loss == pytest.approx(.2)
    assert altered.metrics.estimated_resource_cost == baseline.metrics.estimated_resource_cost
    assert all(o.answer_is_correct == (o.example_id != 'development-wrong') for o in result.outcomes)
    assert all(o.numerical_score == 0 for o in result.outcomes if o.attack_id == scenario.intervention.scenario_id)
    assert result.original_certificate_scope == 'original_fitted_problem_only'
    assert not result.new_scenario_optimality_claim
    PolicyArtifact.model_validate_json(original)  # Still valid, despite changed scenario outcomes.
    FrozenUpstreamEvaluation.model_validate_json(result.model_dump_json())
    with pytest.raises(ValueError):
        PolicyArtifact.model_validate(result.model_dump())
    temporary = unbound_replay_context(artifact, ExecutionContract.model_validate({**artifact.contract.model_dump(),
        'resource_manifest': scenario.intervention.altered_resources,
        'execution_configuration_id': scenario.intervention.altered_resources.manifest_id}))
    assert temporary.plan == artifact.context.plan
    assert temporary.attempt_costs == artifact.context.attempt_costs and temporary.budget == artifact.context.budget
    assert ExecutionContract.model_validate_json(temporary.execution_contract_json).threshold == artifact.contract.threshold
    with pytest.raises(ValueError, match='offline provenance'):
        DeploymentEpisode(episode_id='cannot-deploy', context=temporary,
            contract=ExecutionContract.model_validate_json(temporary.execution_contract_json),
            execution_configuration_id=scenario.intervention.altered_resources.manifest_id)
    with pytest.raises(ValueError, match='never decision semantics'):
        unbound_replay_context(artifact, ExecutionContract.model_validate({**artifact.contract.model_dump(), 'threshold': .6}))


@pytest.mark.parametrize('change', ['missing', 'resource', 'label', 'reference', 'scope', 'duplicate', 'probability', 'certificate'])
def test_frozen_evaluation_rejects_invalid_inputs(tmp_path, change):
    artifact, clean, attacks, scenario = frozen_fixture(tmp_path, 'coverage')
    data = dict(artifact=artifact.model_dump(mode='json'), clean=clean.model_dump(mode='json'),
                report_attacks=attacks.model_dump(mode='json'), scenarios=[scenario.model_dump(mode='json')])
    if change == 'missing':
        data['scenarios'][0]['bundle']['attempts'].pop()
    elif change == 'resource':
        data['scenarios'][0]['intervention']['clean_resources'] = data['scenarios'][0]['intervention']['altered_resources']
    elif change in {'label', 'reference'}:
        e = data['scenarios'][0]['bundle']['request']['examples'][0]
        if change == 'label': e['label']['answer_is_correct'] = not e['label']['answer_is_correct']
        else: e['reference'] = 'SYNTHETIC changed reference'
    elif change == 'scope':
        data['clean']['request']['examples'][1]['question'] = 'SYNTHETIC unseen question'
    elif change == 'duplicate':
        data['scenarios'].append(data['scenarios'][0])
    elif change == 'probability':
        data['artifact']['policy']['solution']['probabilities'][0][1] += .1
    else:
        data['artifact']['policy']['solution']['matrix_id'] = 'wrong'
    with pytest.raises(ValueError):
        evaluate_frozen_upstream(data)


def test_evaluate_cli_preserves_policy_bytes_and_writes_only_report(tmp_path, monkeypatch):
    from scripts.upstream_evidence_experiment import main
    artifact, clean, attacks, scenario = frozen_fixture(tmp_path, 'reliability')
    for name, value in [('original.json', artifact), ('clean.json', clean), ('attacks.json', attacks),
                        ('declaration.json', scenario.intervention), ('scenario.json', scenario.bundle)]:
        (tmp_path/name).write_text(value.model_dump_json(indent=2))
    original = (tmp_path/'original.json').read_bytes()
    block_optimization(monkeypatch)
    assert main(['evaluate', '--policy', str(tmp_path/'original.json'), '--clean-bundle', str(tmp_path/'clean.json'),
                 '--report-attacks', str(tmp_path/'attacks.json'), '--scenario', str(tmp_path/'declaration.json'),
                 str(tmp_path/'scenario.json'), '--output', str(tmp_path/'evaluation.json')]) == 0
    result = FrozenUpstreamEvaluation.model_validate_json((tmp_path/'evaluation.json').read_text())
    assert result.original_artifact_sha256 == hashlib.sha256(original).hexdigest()
    assert (tmp_path/'original.json').read_bytes() == original
    assert not (tmp_path/'policy.json').exists()


@pytest.mark.parametrize('change', ['question', 'reference', 'label'])
def test_valid_new_clean_recordings_cannot_expand_or_relabel_original_scope(tmp_path, change):
    from app.game.models import content_id
    artifact, clean, attacks, scenario = frozen_fixture(tmp_path, 'coverage')
    data = clean.request.model_dump(mode='json')
    for e in data['examples']:
        if e['role'] == 'development':
            if change == 'question':
                e['question'] = 'SYNTHETIC unseen question'; e['question_id'] = content_id(e['question'])
            elif change == 'reference':
                e['reference'] = 'SYNTHETIC new reference'
            else:
                e['label']['answer_is_correct'] = not e['label']['answer_is_correct']
    request = RecordingRequest.model_validate(data)
    changed = collect(request, [EvidenceFixture(n, tmp_path/'clean.txt' if n != 'c' else None) for n in ('a', 'b', 'c')],
                      clean.observed_setup, Observer(clean.observed_setup.resources))
    with pytest.raises(ValueError, match='original frozen training binding'):
        evaluate_frozen_upstream(dict(artifact=artifact, clean=changed, report_attacks=attacks, scenarios=(scenario,)))


def test_failures_unresolved_coverage_and_per_strategy_reasons_are_reported(tmp_path):
    from app.game.execution import VerifierExecutionFailure
    artifact, clean, attacks, scenario = frozen_fixture(tmp_path, 'coverage')
    bundle = collect(scenario.bundle.request,
        [Checker('a', VerifierExecutionFailure('SYNTHETIC retained failure')), EvidenceFixture('b'), EvidenceFixture('c')],
        scenario.bundle.observed_setup, Observer(scenario.intervention.altered_resources))
    altered = ScenarioRecording(intervention=scenario.intervention, bundle=bundle)
    result = evaluate_frozen_upstream(dict(artifact=artifact, clean=clean, report_attacks=attacks, scenarios=(altered,)))
    summary = result.scenario_metrics[-1]
    assert summary.expected_failed_attempts_per_example > 0
    assert summary.expected_unresolved_requirements_per_example > 0
    assert any('selected_execution_incomplete' in dict(reasons) for _, reasons in summary.per_strategy_reason_counts)
    assert summary.metrics.selective_risk is None


def test_prototype_cli_checks_layout_scope_and_original_ids(tmp_path, monkeypatch):
    from dataclasses import asdict
    from app.game.models import content_id
    from app.game.task_conditioning import TaskSnapshotBinding
    from app.game.prototype_bundle import PrototypeEntry, PrototypeManifest, BundleFile
    import app.game.prototype_bundle as package_module
    from scripts.upstream_evidence_experiment import main
    artifact, clean, attacks, scenario = frozen_fixture(tmp_path, 'coverage')
    episode = DeploymentEpisode(episode_id='SYNTHETIC', context=artifact.context, contract=artifact.contract,
                                execution_configuration_id=artifact.execution_configuration_id)
    payloads = {'policy.json': artifact.model_dump(mode='json'), 'episode.json': episode.model_dump(mode='json'),
        'reputation.json': [asdict(s) for s in artifact.context.plan.reputation_statistics],
        'costs.json': dict(calibration_id='SYNTHETIC', budget=artifact.context.budget,
                          attempt_costs=artifact.context.attempt_costs, units=artifact.context.cost_units),
        'resources.json': artifact.contract.resource_manifest.model_dump(mode='json'),
        'metrics.json': dict(artifact_id=artifact.artifact_id, all_strategies=[dict(**s.model_dump(mode='json'),
            probability=dict(artifact.policy.solution.probabilities)[s.strategy_id]) for s in artifact.policy.strategies])}
    package = tmp_path/'package'; package.mkdir()
    files = []
    for name, value in payloads.items():
        raw = json.dumps(value).encode(); (package/name).write_bytes(raw)
        files.append(BundleFile(path=name, sha256=hashlib.sha256(raw).hexdigest()))
    entry = PrototypeEntry(task='arithmetic', experimental=False, artifact_path='policy.json', episode_path='episode.json',
        reputation_path='reputation.json', costs_path='costs.json', resources_path='resources.json', metrics_path='metrics.json',
        artifact_id=artifact.artifact_id, compatibility_id=artifact.context.compatibility_id,
        task_id=TaskSnapshotBinding.model_validate_json(artifact.context.task_conditioning_json).identity.task_id,
        reputation_snapshot_id=artifact.context.reputation_snapshot_id, execution_configuration_id=artifact.execution_configuration_id,
        calibration_id='SYNTHETIC', expected_clean_coverage=.5,
        allowed_question_ids=tuple(sorted({content_id(e.question) for e in clean.request.examples})))
    manifest = PrototypeManifest(version='bounded_task_policy_bundle_v1', approval='SYNTHETIC fixture only',
                                 entries=(entry,), files=tuple(files))
    (package/'manifest.json').write_text(manifest.model_dump_json())
    for name, value in [('clean.json', clean), ('attacks.json', attacks), ('declaration.json', scenario.intervention),
                        ('altered.json', scenario.bundle)]:
        (tmp_path/name).write_text(value.model_dump_json())
    loader = package_module.load_prototype
    monkeypatch.setattr(package_module, 'load_prototype', lambda p: loader(p, allow_synthetic_for_tests=True))
    block_optimization(monkeypatch)
    args = ['evaluate', '--prototype-bundle', str(package), '--task', 'arithmetic', '--clean-bundle', str(tmp_path/'clean.json'),
            '--report-attacks', str(tmp_path/'attacks.json'), '--scenario', str(tmp_path/'declaration.json'),
            str(tmp_path/'altered.json'), '--output', str(tmp_path/'result.json')]
    assert main(args) == 0
    result = FrozenUpstreamEvaluation.model_validate_json((tmp_path/'result.json').read_text())
    assert result.prototype_bundle_id == manifest.bundle_id and result.original_artifact_id == artifact.artifact_id
    restricted = manifest.model_dump(mode='json')
    restricted['entries'][0]['allowed_question_ids'] = [content_id('SYNTHETIC other scope')]
    (package/'manifest.json').write_text(json.dumps(restricted))
    args[-1] = str(tmp_path/'must-not-exist.json')
    assert main(args) == 2
    assert not (tmp_path/'must-not-exist.json').exists()


def test_actual_altered_fixture_reports_produce_false_acceptance_and_rejection(tmp_path, monkeypatch):
    artifact, clean, attacks, scenario = frozen_fixture(tmp_path, 'coverage')
    altered_path = tmp_path/'false-evidence.txt'
    altered_path.write_text('SYNTHETIC incorrect answer')
    data = scenario.intervention.altered_resources.model_dump(mode='json')
    for verifier in data['verifiers']:
        for resource in verifier['resources']:
            if resource['kind'] == 'corpus':
                resource['sha256'] = hashlib.sha256(altered_path.read_bytes()).hexdigest()
    resources = ResourceManifest.model_validate(data)
    setup = type(clean.observed_setup).model_validate({**clean.observed_setup.model_dump(), 'resources': resources})
    request = scenario_request(clean.request, setup, name='predeclared false fixture text',
        preparation_authorization='SYNTHETIC independent run permission', study_approval=None)
    bundle = collect(request, [EvidenceFixture(n, altered_path if n != 'c' else None) for n in ('a', 'b', 'c')],
                     setup, Observer(resources))
    changed = ScenarioRecording(intervention={**scenario.intervention.model_dump(),
        'alteration': 'replace text by independently incorrect fixture answer',
        'request_id': request.request_id, 'altered_resources': resources}, bundle=bundle)
    block_optimization(monkeypatch)
    result = evaluate_frozen_upstream(dict(artifact=artifact, clean=clean, report_attacks=attacks, scenarios=(changed,)))
    baseline, altered = result.scenario_metrics
    assert baseline.metrics.false_accept == baseline.metrics.false_reject == 0
    assert altered.metrics.false_accept > 0 and altered.metrics.false_reject > 0
    assert altered.metrics.selective_risk == 1
    assert altered.validation_loss > baseline.validation_loss


@pytest.mark.parametrize('field', ['code_revision', 'application_source_digest', 'environment', 'dependency_versions'])
def test_fresh_incompatible_recording_setup_is_rejected(tmp_path, field):
    artifact, clean, attacks, scenario = frozen_fixture(tmp_path, 'coverage')
    data = scenario.bundle.observed_setup.model_dump(mode='json')
    if field == 'code_revision': data[field] = '0'*40
    elif field == 'application_source_digest': data[field] = 'e'*64
    else: data[field] = {**data[field], 'SYNTHETIC_changed': 'explicit different setup'}
    setup = type(clean.observed_setup).model_validate(data)
    request = RecordingRequest.model_validate({**scenario.bundle.request.model_dump(), 'expected_setup': setup})
    bundle = collect(request, [EvidenceFixture(n, tmp_path/'altered.txt' if n != 'c' else None) for n in ('a', 'b', 'c')],
                     setup, Observer(setup.resources))
    changed = ScenarioRecording(intervention={**scenario.intervention.model_dump(), 'request_id': request.request_id}, bundle=bundle)
    with pytest.raises(ValueError, match='scenario environment/code differs'):
        evaluate_frozen_upstream(dict(artifact=artifact, clean=clean, report_attacks=attacks, scenarios=(changed,)))


def test_new_evaluator_source_is_not_compared_to_old_collection_source(tmp_path, monkeypatch):
    import subprocess
    artifact, clean, attacks, scenario = frozen_fixture(tmp_path, 'reliability')
    block_optimization(monkeypatch)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(subprocess, 'check_output', lambda *a, **k: pytest.fail('evaluator consulted current Git/source instead of recorded provenance'))
    result = evaluate_frozen_upstream(dict(artifact=artifact, clean=clean, report_attacks=attacks, scenarios=(scenario,)))
    assert result.original_artifact_id == artifact.artifact_id


def test_source_audit_reads_actual_bytes_without_importing_candidate_app(tmp_path, monkeypatch):
    import subprocess
    from app.game.models import content_id
    from app.game.offline.upstream_evaluation import audit_collector_source
    from tests.test_game_collection import fixture
    _, _, setup, *_ = fixture()
    root = tmp_path/'collector'; (root/'app').mkdir(parents=True)
    path = root/'app/probe.py'; path.write_bytes(b'raise AssertionError("must not import candidate source")\r\n')
    digest = content_id([('app/probe.py', hashlib.sha256(path.read_bytes()).hexdigest())])
    setup = type(setup).model_validate({**setup.model_dump(), 'application_source_digest': digest})
    for key in ('GIT_DIR', 'GIT_WORK_TREE', 'GIT_INDEX_FILE'): monkeypatch.delenv(key, raising=False)
    monkeypatch.setattr(subprocess, 'check_output', lambda cmd, **kw: str(root) if cmd[-1]=='--show-toplevel' else setup.code_revision)
    report = audit_collector_source(setup, root)
    assert report['source_compatible'] and not report['ready_for_real_collection'] and not report['factory_initialized']
    path.write_bytes(path.read_bytes().replace(b'\r\n', b'\n'))
    assert 'collector_application_source_digest_mismatch' in audit_collector_source(setup, root)['gaps']
    different = type(setup).model_validate({**setup.model_dump(), 'code_revision': '0'*40})
    monkeypatch.setattr(subprocess, 'check_output', lambda cmd, **kw: str(root) if cmd[-1]=='--show-toplevel' else 'a'*40)
    assert 'collector_code_revision_mismatch' in audit_collector_source(different, root)['gaps']


def test_external_probe_payload_is_validated_by_new_schema_without_old_schema_import():
    from scripts.frozen_evidence_probes import probe_payload
    import tests.test_evidence_verifier as helpers
    from app.game.research.evidence_validation import EvidenceValidation
    from tests.test_game_evidence_validation import proof_data
    calls = []
    def synthetic_nli(inputs):
        calls.append(inputs)
        probabilities = (helpers.NEUTRAL if 'is a play' in inputs['text'] else
                         helpers.CONTRADICTS if 'Charles Dickens' in inputs['text_pair'] else helpers.ENTAILS)
        return helpers.FakeNLI({'': probabilities})(inputs)
    resource = proof_data()['before']
    payload = probe_payload(synthetic_nli, resource, helpers.EvidenceVerifier, vars(helpers))
    proof = EvidenceValidation.model_validate(payload)
    assert len(calls) == 3 and len(proof.probes) == 7
    assert {p.case_id for p in proof.probes} == set(__import__('app.game.research.evidence_validation', fromlist=['EXPECTED']).EXPECTED)


def test_external_probe_rejects_blocked_source_before_any_app_initialization(tmp_path, monkeypatch):
    from scripts.frozen_evidence_probes import main
    from tests.test_game_collection import fixture
    _, _, setup, *_ = fixture()
    clean = tmp_path/'clean.json'; clean.write_text(json.dumps(dict(observed_setup=setup.model_dump(mode='json'))))
    audit = tmp_path/'audit.json'; audit.write_text(json.dumps(dict(source_compatible=False)))
    adapter = tmp_path/'adapter.json'; adapter.write_text('{}')
    import subprocess
    monkeypatch.setattr(subprocess, 'check_output', lambda *a, **k: pytest.fail('blocked source should not inspect/initialize collector'))
    assert main(['--collector-root', str(tmp_path), '--clean-bundle', str(clean), '--adapter-config', str(adapter),
                 '--source-audit', str(audit), '--output-dir', str(tmp_path/'outputs'), '--authorization-record', 'SYNTHETIC permission']) == 2
    assert not (tmp_path/'outputs').exists()


def test_external_rehearsal_boundary_resumes_existing_journal_without_repeating_calls(tmp_path, monkeypatch):
    import sys
    from types import SimpleNamespace
    import app.game.offline.collect as cli
    from app.game.offline.collect import load_bundle
    from scripts.frozen_evidence_probes import bounded_collect
    from tests.test_game_collection import fixture
    request, pool, setup, observer, *_ = fixture()
    monkeypatch.setitem(sys.modules, 'synthetic_recording_factory', SimpleNamespace(create=lambda: (pool, setup, observer)))
    path = tmp_path/'request.json'; path.write_text(request.model_dump_json())
    original = cli.collect
    counter = dict(started=0, planned_stop=False)
    monkeypatch.setattr(cli, 'collect', bounded_collect(original, 2, counter))
    first = tmp_path/'first'
    assert cli.main(['collect', str(path), '--output-dir', str(first)]) == 130
    partial = load_bundle(first)
    assert len(partial.attempts) == 2 and counter == dict(started=2, planned_stop=True)
    ledger = [json.loads(line)['attempt_id'] for line in (first/'started.jsonl').read_text().splitlines()]
    assert set(ledger) == {a.attempt_id for a in partial.attempts if a.executed}
    monkeypatch.setattr(cli, 'collect', original)
    complete = tmp_path/'complete'
    assert cli.main(['collect', str(path), '--resume-from', str(first), '--output-dir', str(complete)]) == 0
    assert len(load_bundle(complete).attempts) == 4
    assert [len(v.calls) for v in pool] == [2, 2]
