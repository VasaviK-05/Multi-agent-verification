"""Synthetic transfer contracts only; no source equivalence or security evidence."""
import json

import pytest

from app.game.models import content_id
from app.game.offline.collection import collect
from app.game.offline.upstream import ScenarioRecording, scenario_request
from app.game.offline.upstream_evaluation import evaluate_frozen_upstream
from app.game.offline.upstream_transfer import (prepare_transfer, FrozenPolicyTransferInput,
    FrozenPolicyTransferEvaluation, evaluate_frozen_transfer)
from app.game.resource_provenance import ResourceManifest
from tests.test_game_upstream_evaluation import frozen_fixture, EvidenceFixture, block_optimization
from tests.test_game_collection import Observer


def transfer_fixture(tmp_path, variant='coverage', *, current_neutral=False, change_resources=True):
    artifact, historical, attacks, _ = frozen_fixture(tmp_path, variant)
    data = historical.observed_setup.resources.model_dump(mode='json')
    if change_resources:
        for verifier in data['verifiers']:
            for r in verifier['resources']:
                if r['kind'] == 'implementation': r['sha256'] = content_id(['SYNTHETIC current implementation', verifier['verifier_name']])
    resources = ResourceManifest.model_validate(data)
    files = (('app/current_fixture.py', content_id('SYNTHETIC current source bytes')),)
    setup = type(historical.observed_setup).model_validate({**historical.observed_setup.model_dump(),
        'resources': resources, 'code_revision': 'c'*40, 'application_source_digest': content_id(files),
        'dependency_versions': {'python': 'SYNTHETIC explicitly new'}, 'environment': {'host': 'SYNTHETIC new environment'}})
    declaration, request = prepare_transfer(artifact, historical, attacks, setup, files,
        authorization_record='SYNTHETIC new paired transfer authority', implementation_change_record='SYNTHETIC current code, equivalence unknown',
        report_compatibility_record='SYNTHETIC existing adapters/decision contracts', source_snapshot_record='SYNTHETIC archived new source')
    clean = collect(request, [EvidenceFixture(n, tmp_path/'clean.txt' if n != 'c' and not current_neutral else None)
                             for n in ('a', 'b', 'c')], setup, Observer(resources))
    altered_data = resources.model_dump(mode='json')
    import hashlib
    for verifier in altered_data['verifiers']:
        for r in verifier['resources']:
            if r['kind'] == 'corpus': r['sha256'] = hashlib.sha256((tmp_path/'altered.txt').read_bytes()).hexdigest()
    altered_resources = ResourceManifest.model_validate(altered_data)
    altered_setup = type(setup).model_validate({**setup.model_dump(), 'resources': altered_resources})
    altered_request = scenario_request(request, altered_setup, name='SYNTHETIC fixed paired intervention',
        preparation_authorization='SYNTHETIC paired alteration approval', study_approval=None)
    bundle = collect(altered_request, [EvidenceFixture(n, tmp_path/'altered.txt' if n != 'c' else None) for n in ('a', 'b', 'c')],
                     altered_setup, Observer(altered_resources))
    scenario = ScenarioRecording(intervention=dict(version='upstream_evidence_intervention_v1',
        name='SYNTHETIC paired alteration', affected_resource='shared-fixture-corpus', alteration='SYNTHETIC neutral text',
        scope='original prepared development only', provenance='SYNTHETIC separate current corpus; labels unchanged',
        clean_resources=resources, altered_resources=altered_resources, affected_verifiers=('a', 'b'),
        timing='committed_before_collection_and_team_sampling',
        knowledge='public_questions_references_and_clean_resources_no_labels_no_sampled_team',
        reuse_contract='complete_team_independent_within_fixed_scenario_v1', reuse_attestation='SYNTHETIC fixed stateless scenario',
        request_id=altered_request.request_id), bundle=bundle)
    return FrozenPolicyTransferInput(declaration=declaration, artifact=artifact, historical_clean=historical,
        current_clean=dict(bundle=clean), report_attacks=attacks, scenarios=(scenario,))


@pytest.mark.parametrize('variant', ['coverage', 'reliability'])
def test_transfer_preserves_frozen_rule_without_optimizing(tmp_path, monkeypatch, variant):
    inputs = transfer_fixture(tmp_path, variant)
    raw = inputs.artifact.model_dump_json()
    block_optimization(monkeypatch)
    result = evaluate_frozen_transfer(inputs)
    assert inputs.artifact.model_dump_json() == raw
    assert result.strategy_probabilities == inputs.artifact.policy.solution.probabilities
    assert result.strategies == inputs.artifact.policy.strategies
    assert result.original_threshold == inputs.artifact.contract.threshold
    assert result.original_certificate_scope == 'original_fitted_problem_only' and not result.new_scenario_optimality_claim
    assert not result.historical_current_equivalence_established
    assert result.historical_collector_setup != result.current_clean_collector_setup
    assert [m.scenario_id for m in result.scenario_metrics[:2]] == ['historical_clean', 'current_clean']
    assert result.scenario_metrics[-1].metrics.decision_coverage == 0 < result.original_clean_coverage_floor
    assert result.scenario_metrics[-1].metrics.selective_risk is None
    assert result.scenario_metrics[-1].uncertainty_rate == 1
    assert len(result.scenario_metrics[-1].per_strategy_metrics) == len(result.strategies)
    assert all('minimum_contributors' in o.reasons and 'missing_achieved_coverage' in o.reasons
               for o in result.outcomes if o.attack_id == inputs.scenarios[0].intervention.scenario_id)
    assert all(t.executed_calls == len(inputs.current_clean.bundle.attempts) for t in result.timing)
    assert all(t.executed_duration_sum_ms >= 0 for t in result.timing)
    FrozenPolicyTransferEvaluation.model_validate_json(result.model_dump_json())
    from app.game.artifacts import PolicyArtifact
    with pytest.raises(ValueError): PolicyArtifact.model_validate(result.model_dump())


def test_strict_mode_still_rejects_same_resource_but_mixed_collector(tmp_path):
    inputs = transfer_fixture(tmp_path, change_resources=False)
    with pytest.raises(ValueError, match='scenario environment/code differs'):
        evaluate_frozen_upstream(dict(artifact=inputs.artifact, clean=inputs.historical_clean,
            report_attacks=inputs.report_attacks, scenarios=inputs.scenarios))
    assert evaluate_frozen_transfer(inputs).historical_current_equivalence_established is False


def test_historical_clean_cannot_be_substituted_for_new_clean(tmp_path):
    inputs = transfer_fixture(tmp_path, current_neutral=True)
    result = evaluate_frozen_transfer(inputs)
    assert result.scenario_metrics[0].metrics.decision_coverage >= .5-1e-8
    assert result.scenario_metrics[1].metrics.decision_coverage == 0
    assert result.scenario_metrics[0].recording_id != result.scenario_metrics[1].recording_id
    data = inputs.model_dump(mode='json')
    data['current_clean']['bundle'] = data['historical_clean']
    with pytest.raises(ValueError, match='development only'):
        evaluate_frozen_transfer(data)


def test_collection_scope_guard_rejects_well_formed_contaminated_labels(tmp_path):
    from app.game.offline.collection import RecordingRequest
    from app.game.offline.upstream_transfer import validate_collection_scope
    inputs = transfer_fixture(tmp_path)
    request = inputs.current_clean.bundle.request
    validate_collection_scope(inputs.historical_clean, request)
    validate_collection_scope(inputs.historical_clean, inputs.scenarios[0].bundle.request)
    data = request.model_dump(mode='json')
    data['examples'][0]['label']['answer_is_correct'] = not data['examples'][0]['label']['answer_is_correct']
    contaminated = RecordingRequest.model_validate(data)
    with pytest.raises(ValueError, match='independent label'):
        validate_collection_scope(inputs.historical_clean, contaminated)


@pytest.mark.parametrize('change', ['declaration', 'equivalence', 'decision', 'adapter', 'source_manifest', 'source_pair',
                                   'missing_clean', 'missing_altered', 'label', 'resource', 'topology', 'duplicate'])
def test_transfer_rejects_missing_or_mismatched_inputs(tmp_path, change):
    data = transfer_fixture(tmp_path).model_dump(mode='json')
    if change == 'declaration': data.pop('declaration')
    elif change == 'equivalence': data['declaration']['equivalence'] = 'equivalent'
    elif change == 'decision': data['declaration']['decision_semantics_id'] = 'wrong'
    elif change == 'adapter': data['declaration']['report_contract'] = 'unknown_v2'
    elif change == 'source_manifest': data['declaration']['current_source_files'][0][1] = '0'*64
    elif change == 'source_pair': data['scenarios'][0]['bundle']['observed_setup']['code_revision'] = '0'*40
    elif change == 'missing_clean': data['current_clean']['bundle']['attempts'].pop()
    elif change == 'missing_altered': data['scenarios'][0]['bundle']['attempts'].pop()
    elif change == 'label': data['current_clean']['bundle']['request']['examples'][0]['label']['answer_is_correct'] = False
    elif change == 'resource': data['declaration']['resource_changes'].pop()
    elif change == 'topology': data['declaration']['current_clean_setup']['resources']['verifiers'][0]['resources'][0]['resource_id'] = 'different'
    else: data['scenarios'].append(data['scenarios'][0])
    with pytest.raises(ValueError): evaluate_frozen_transfer(data)


def test_transfer_cli_preparation_and_evaluation_without_inference(tmp_path, monkeypatch):
    from scripts.upstream_evidence_experiment import main
    inputs = transfer_fixture(tmp_path, 'reliability')
    source = inputs.declaration.current_source_files
    files = [('original.json', inputs.artifact), ('historical.json', inputs.historical_clean),
             ('attacks.json', inputs.report_attacks), ('current.json', inputs.current_clean.bundle),
             ('transfer.json', inputs.declaration), ('scenario.json', inputs.scenarios[0].bundle),
             ('intervention.json', inputs.scenarios[0].intervention)]
    for name, value in files: (tmp_path/name).write_text(value.model_dump_json(indent=2))
    (tmp_path/'preflight.json').write_text(json.dumps(dict(observed_setup=inputs.declaration.current_clean_setup.model_dump(mode='json'))))
    (tmp_path/'source.json').write_text(json.dumps(source))
    original = (tmp_path/'original.json').read_bytes()
    block_optimization(monkeypatch)
    assert main(['prepare-transfer', '--policy', str(tmp_path/'original.json'), '--historical-clean', str(tmp_path/'historical.json'),
        '--report-attacks', str(tmp_path/'attacks.json'), '--current-preflight', str(tmp_path/'preflight.json'),
        '--source-manifest', str(tmp_path/'source.json'), '--authorization-record', 'SYNTHETIC authority',
        '--implementation-change-record', 'SYNTHETIC current implementation', '--report-compatibility-record', 'SYNTHETIC adapters',
        '--source-snapshot-record', 'SYNTHETIC snapshot', '--output-dir', str(tmp_path/'prepared')]) == 0
    assert main(['evaluate-transfer', '--policy', str(tmp_path/'original.json'), '--historical-clean', str(tmp_path/'historical.json'),
        '--fresh-clean', str(tmp_path/'current.json'), '--report-attacks', str(tmp_path/'attacks.json'),
        '--transfer-declaration', str(tmp_path/'transfer.json'), '--scenario', str(tmp_path/'intervention.json'),
        str(tmp_path/'scenario.json'), '--output', str(tmp_path/'result.json')]) == 0
    result = FrozenPolicyTransferEvaluation.model_validate_json((tmp_path/'result.json').read_text())
    assert result.version == 'frozen_policy_transfer_development_v1'
    assert main(['assemble-transfer', '--policy', str(tmp_path/'original.json'), '--historical-clean', str(tmp_path/'historical.json'),
        '--fresh-clean', str(tmp_path/'current.json'), '--report-attacks', str(tmp_path/'attacks.json'),
        '--transfer-declaration', str(tmp_path/'transfer.json'), '--scenario', str(tmp_path/'intervention.json'),
        str(tmp_path/'scenario.json'), '--output', str(tmp_path/'assembled.json')]) == 0
    assembled = FrozenPolicyTransferInput.model_validate_json((tmp_path/'assembled.json').read_text())
    assert evaluate_frozen_transfer(assembled).scenario_metrics == result.scenario_metrics
    assert (tmp_path/'original.json').read_bytes() == original
    assert not (tmp_path/'policy.json').exists()


def test_changed_decision_replay_is_rejected_even_with_an_old_version_claim(tmp_path, monkeypatch):
    inputs = transfer_fixture(tmp_path)
    import app.game.offline.upstream_evaluation as evaluation
    original = evaluation.replay
    def incompatible(*args, **kwargs):
        result = original(*args, **kwargs)
        return result.model_copy(update={'public_status': 'uncertain'})
    monkeypatch.setattr(evaluation, 'replay', incompatible)
    with pytest.raises(ValueError, match='unsupported decision semantics'):
        evaluate_frozen_transfer(inputs)


def test_incompatible_score_interface_is_rejected(tmp_path):
    inputs = transfer_fixture(tmp_path)
    clean = inputs.current_clean.bundle
    request = clean.request
    class ChangedReport(EvidenceFixture):
        def verify(self, *args, **kwargs):
            result = super().verify(*args, **kwargs)
            result.metadata['score_meaning'] = 'SYNTHETIC incompatible correctness probability'
            return result
    bundle = collect(request, [ChangedReport(n, tmp_path/'clean.txt' if n!='c' else None) for n in ('a','b','c')],
                     clean.observed_setup, Observer(clean.observed_setup.resources))
    data = inputs.model_dump(); data['current_clean'] = dict(bundle=bundle)
    with pytest.raises(ValueError, match='score-meaning/report contract'):
        evaluate_frozen_transfer(data)


def test_source_snapshot_preserves_dirty_and_untracked_actual_bytes(tmp_path, monkeypatch):
    import hashlib, subprocess, zipfile
    from app.game.offline.upstream_transfer import snapshot_collector
    for key in ('GIT_DIR', 'GIT_WORK_TREE', 'GIT_INDEX_FILE'): monkeypatch.delenv(key, raising=False)
    root = tmp_path/'collector'; (root/'app').mkdir(parents=True)
    (root/'app/a.py').write_bytes(b'# SYNTHETIC dirty source\r\n')
    (root/'app/untracked.py').write_bytes(b'# SYNTHETIC untracked source\n')
    def git(command, **kwargs):
        if command[-1]=='--show-toplevel': return str(root)
        if command[-1]=='HEAD': return 'c'*40
        return ' M app/a.py\n?? app/untracked.py\n'
    monkeypatch.setattr(subprocess, 'check_output', git)
    destination = tmp_path/'snapshot'
    receipt = snapshot_collector(root, destination)
    manifest = json.loads((destination/'source-manifest.json').read_text())
    assert receipt['application_source_digest'] == content_id(manifest)
    with zipfile.ZipFile(destination/'app-source.zip') as archive:
        assert set(archive.namelist()) == {'app/a.py', 'app/untracked.py'}
        for name, digest in manifest:
            assert hashlib.sha256(archive.read(name)).hexdigest() == digest
            assert archive.read(name) == (root/name).read_bytes()


def test_source_snapshot_rejects_git_override_before_output(tmp_path, monkeypatch):
    from app.game.offline.upstream_transfer import snapshot_collector
    monkeypatch.setenv('GIT_DIR', str(tmp_path/'different-git'))
    with pytest.raises(ValueError, match='Git source overrides'):
        snapshot_collector(tmp_path, tmp_path/'must-not-exist')
    assert not (tmp_path/'must-not-exist').exists()


def test_transfer_runner_cannot_use_a_strict_source_audit(tmp_path, monkeypatch):
    from scripts.frozen_evidence_probes import main
    import subprocess
    inputs = transfer_fixture(tmp_path)
    for name, value in [('historical.json', inputs.historical_clean), ('transfer.json', inputs.declaration)]:
        (tmp_path/name).write_text(value.model_dump_json())
    (tmp_path/'audit.json').write_text(json.dumps(dict(version='frozen_collector_source_audit_v1', source_compatible=True)))
    monkeypatch.setattr(subprocess, 'check_output', lambda *a, **k: pytest.fail('wrong-mode audit must reject before collection'))
    assert main(['--collector-root', str(tmp_path), '--clean-bundle', str(tmp_path/'historical.json'),
        '--evaluation-transfer', str(tmp_path/'transfer.json'), '--adapter-config', str(tmp_path/'adapter.json'),
        '--source-audit', str(tmp_path/'audit.json'), '--authorization-record', 'SYNTHETIC',
        '--output-dir', str(tmp_path/'must-not-exist')]) == 2
    assert not (tmp_path/'must-not-exist').exists()
