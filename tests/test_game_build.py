"""Synthetic arithmetic fixtures only; no empirical claims."""
import json
from pathlib import Path
import subprocess

import pytest

from app.game.artifacts import PolicyArtifact
from app.game.offline.build import main, build, BuildInputError, development_diagnostics, verify_equivalent
from app.game.offline.evaluation import fit_policy, export_artifact, evaluate_final_test, evaluate_reserved_final
from app.game.offline.records import TrainingManifest, FinalTestReservation, ReservedExample, Partition
from app.game.research.specification import PolicyBuildSpecification
from app.game.models import PlanningContext, canonical_json
from tests.test_game_offline import fixture, unbind
from tests.test_game_research import study


def build_spec(*, names=('a',), context_update=None):
    """Custodian creates an outcome-free reservation; fitter receives no final data."""
    legacy = study(names=names)
    final = legacy.manifest.partition('final_test')
    reservation = FinalTestReservation(version='final_test_reservation_v1', role='final_test',
        dataset_id=final.dataset_id, custody_record='SYNTHETIC external witness only',
        examples=tuple(ReservedExample.from_example(e) for e in final.examples))
    training = TrainingManifest(version='game_training_manifest_v1',
        evidence_kind='synthetic_test_fixture',
        partitions=tuple(p for p in legacy.manifest.partitions if p.role != 'final_test'),
        final_test_reservation=reservation)
    context = unbind(legacy.context)
    if context_update:
        context = PlanningContext(**{**context.model_dump(), **context_update})
        from app.game.offline.replay import category_id
        data = training.model_dump()
        for p in data['partitions']:
            for e in p['examples']:
                e['planning_category'] = category_id(context)
        training = TrainingManifest.model_validate(data)
    data = {**legacy.model_dump(), 'version': 'offline_policy_build_v1',
        'manifest': training, 'context': context,
        'code_revision': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()}
    return PolicyBuildSpecification.model_validate(data), final


def test_failure_writes_all_gaps_before_nonzero_exit(tmp_path):
    config = tmp_path / 'input.json'
    config.write_text('{}', encoding='utf-8')
    output = tmp_path / 'output'
    assert main([str(config), '--output-dir', str(output)]) == 2
    report = json.loads((output / 'missing-inputs.json').read_text())
    assert len(report['missing_inputs']) > 10
    assert report['artifact_created'] is False
    assert report['scientific_outputs'] is None
    assert report['build_metadata']['environment']['highs']
    assert (output / 'summary.txt').read_text().startswith('Policy build blocked')
    assert sorted(p.name for p in output.iterdir()) == ['missing-inputs.json', 'summary.txt']


def test_bad_json_and_missing_file_reported(tmp_path):
    config = tmp_path / 'input.json'
    for content in (None, '{', '[]', '{"context":1,"context":2}'):
        if content is not None:
            config.write_text(content)
        output = tmp_path / 'output'
        assert main([str(config), '--output-dir', str(output)]) == 2
        assert json.loads((output / 'missing-inputs.json').read_text())['missing_inputs']


def test_final_records_not_deserialized(tmp_path, monkeypatch):
    from app.game.offline.records import DatasetManifest
    def forbidden(*args, **kwargs):
        pytest.fail('final-test manifest was deserialized')
    monkeypatch.setattr(DatasetManifest, 'model_validate', forbidden)
    config = tmp_path / 'input.json'
    config.write_text(json.dumps({'manifest': {'partitions': 'DO NOT VALIDATE'}}))
    assert main([str(config), '--output-dir', str(tmp_path / 'out')]) == 2


def test_synthetic_repeat_fit_reload_and_separate_losses():
    context, manifest, contract, attacks = fixture()
    artifacts = []
    for _ in range(2):
        policy, evaluation = fit_policy(context, manifest, contract, attacks)
        artifact = export_artifact(policy, context, manifest, contract, attacks, applicable_domain='general')
        artifacts.append(PolicyArtifact.model_validate_json(artifact.model_dump_json()))
    assert verify_equivalent(*artifacts)['equivalent']
    result = development_diagnostics(policy, evaluation, context)
    assert result['worst_case_scenarios']
    for row in result['scenarios']:
        assert row['development_game_objective'] == pytest.approx(
            row['development_validation_loss'] + context.loss_configuration.resource_weight * row['expected_estimated_cost'])
        assert row['uncertainty_rate'] + row['decision_coverage'] == pytest.approx(1.)
    with pytest.raises(ValueError, match='tolerance'):
        verify_equivalent(*artifacts, probability_atol=float('nan'))


@pytest.mark.parametrize('outcome_exists', [False, True])
def test_cli_end_to_end_never_opens_final_outcomes(tmp_path, monkeypatch, outcome_exists):
    spec, _ = build_spec(names=('a', 'b', 'c', 'd'))
    spec = PolicyBuildSpecification.model_validate({**spec.model_dump(), 'optimizer_tolerance': 2e-7})
    final_path = tmp_path / 'custodian-final-outcomes.json'
    if outcome_exists:
        final_path.write_text('UNREADABLE HELD-OUT PAYLOAD')
    config = tmp_path / 'build.json'
    config.write_text(spec.model_dump_json())
    output = tmp_path / 'output'
    original_open = Path.open
    def guarded_open(path, *args, **kwargs):
        if path == final_path:
            pytest.fail('fitter accessed held-out outcomes')
        return original_open(path, *args, **kwargs)
    monkeypatch.setattr(Path, 'open', guarded_open)
    monkeypatch.setattr(FinalTestReservation, 'validate_payload',
                        lambda *a: pytest.fail('fitter validated a held-out payload'))
    monkeypatch.setattr(ReservedExample, 'from_example',
                        lambda *a: pytest.fail('fitter converted a held-out outcome'))
    # Even a metadata-only access must not be interpreted as an outcome.
    original_get = ReservedExample.__getattribute__
    def guarded_get(self, name):
        if name in {'answer_is_correct', 'attempts', 'report', 'question', 'answer'}:
            pytest.fail('fitter accessed final outcome fields')
        return original_get(self, name)
    monkeypatch.setattr(ReservedExample, '__getattribute__', guarded_get)
    assert main([str(config), '--output-dir', str(output)]) == 0
    artifact = PolicyArtifact.model_validate_json((output / 'policy.json').read_text())
    report = json.loads((output / 'build-report.json').read_text())
    result = report['scientific_outputs']
    assert report['artifact_created'] and result['reproducibility']['equivalent']
    assert len(artifact.policy.strategies) == 30
    assert {len(s.verifiers) for s in artifact.policy.strategies} == {1, 2, 3, 4}
    assert {s.aggregation for s in artifact.policy.strategies} == {'reputation_weighted', 'dependency_group'}
    assert len(artifact.policy.solution.probabilities) == len(artifact.policy.strategies)
    assert any(p == 0. for _, p in artifact.policy.solution.probabilities)
    assert result['certificate']['tolerance'] == spec.optimizer_tolerance
    assert artifact.context.offline_evaluation_id


@pytest.mark.parametrize('key', ['example_id', 'split_identity', 'question_id', 'content_identity', 'validation_id'])
def test_reservation_cross_role_leakage(key):
    spec, _ = build_spec()
    data = spec.manifest.model_dump()
    source = spec.manifest.partition('history').examples[0]
    data['final_test_reservation']['examples'][0][key] = getattr(source, key)
    with pytest.raises(ValueError, match='split leakage'):
        TrainingManifest.model_validate(data)


@pytest.mark.parametrize('change', ['missing', 'empty', 'bad_digest', 'extra_label', 'duplicate', 'no_witness'])
def test_reservation_malformed_rejected(change):
    spec, _ = build_spec()
    data = spec.manifest.model_dump()
    reservation = data['final_test_reservation']
    if change == 'missing':
        del data['final_test_reservation']
    elif change == 'empty':
        reservation['examples'] = []
    elif change == 'bad_digest':
        reservation['examples'][0]['content_identity'] = 'not-a-digest'
    elif change == 'extra_label':
        reservation['examples'][0]['answer_is_correct'] = True
    elif change == 'duplicate':
        reservation['examples'] *= 2
    else:
        reservation['custody_record'] = ''
    with pytest.raises(ValueError):
        TrainingManifest.model_validate(data)


def test_related_questions_must_share_group_within_reservation():
    spec, _ = build_spec()
    data = spec.manifest.model_dump()
    first = data['final_test_reservation']['examples'][0]
    data['final_test_reservation']['examples'] += ({**first, 'example_id': 'other',
        'validation_id': 'other-run', 'split_identity': 'other-group'},)
    with pytest.raises(ValueError, match='related question'):
        TrainingManifest.model_validate(data)


def test_final_payload_evaluation_binding_and_no_refit(monkeypatch):
    spec, final = build_spec()
    artifact, _ = build(spec, actual_code_revision=spec.code_revision)
    import app.game.solver as solver
    monkeypatch.setattr(solver, 'linprog', lambda *a, **kw: pytest.fail('final evaluation fitted a policy'))
    result = evaluate_final_test(artifact.policy, artifact.context, spec.manifest, spec.contract,
                                 spec.attacks, final_partition=final)
    assert result.reservation_id == spec.manifest.final_test_reservation.reservation_id
    assert result.final_payload_id and result.manifest_id == spec.manifest.manifest_id
    for field, value in [('answer', 'changed content'), ('split_identity', 'other-group'),
                         ('validation_id', 'other-run')]:
        data = final.model_dump()
        data['examples'][0][field] = value
        if field == 'validation_id':
            for attempt in data['examples'][0]['attempts']:
                attempt['execution_id'] = value
                # report identity is added only during Attempt canonicalization
                attempt['report_json'] = None
                attempt['state'] = 'unavailable'
        with pytest.raises(ValueError, match='reservation'):
            evaluate_final_test(artifact.policy, artifact.context, spec.manifest, spec.contract,
                                spec.attacks, final_partition=Partition.model_validate(data))
    with pytest.raises(ValueError, match='separately released'):
        evaluate_final_test(artifact.policy, artifact.context, spec.manifest, spec.contract, spec.attacks)


def test_final_release_validates_label_provenance_and_separate_payload_identity(monkeypatch):
    spec, final = build_spec()
    artifact, _ = build(spec, actual_code_revision=spec.code_revision)
    import app.game.solver as solver
    monkeypatch.setattr(solver, 'linprog', lambda *a, **kw: pytest.fail('final evaluator refitted'))
    kwargs = dict(actual_code_revision=spec.code_revision, freeze_record='SYNTHETIC freeze witness')
    first = evaluate_reserved_final(artifact, spec, final, **kwargs)
    data = final.model_dump()
    data['examples'][0]['answer_is_correct'] = False
    second = evaluate_reserved_final(artifact, spec, Partition.model_validate(data), **kwargs)
    assert first.reservation_id == second.reservation_id
    assert first.final_payload_id != second.final_payload_id
    assert first.policy_id == second.policy_id
    assert first.freeze_record == kwargs['freeze_record']
    data['examples'][0]['label_source'] = 'undeclared-source'
    with pytest.raises(ValueError, match='undeclared independent label'):
        evaluate_reserved_final(artifact, spec, Partition.model_validate(data), **kwargs)


def test_final_records_are_rejected_before_attempt_parsing():
    spec, _ = build_spec()
    data = spec.manifest.model_dump()
    # An invalid final attempt is deliberately unparseable, but the training role
    # gate rejects it before any Example/Attempt validator can inspect it.
    data['partitions'] += ({'role': 'final_test', 'examples': 'FORBIDDEN'},)
    with pytest.raises(ValueError, match='outcomes are forbidden'):
        TrainingManifest.model_validate(data)


def test_minimum_budget_and_coverage_constraints():
    spec, _ = build_spec(names=('a', 'b', 'c', 'd'), context_update={'budget': 2.})
    artifact, _ = build(spec, actual_code_revision=spec.code_revision)
    assert {len(s.verifiers) for s in artifact.policy.strategies} == {1, 2}
    assert all(s.estimated_cost <= 2. for s in artifact.policy.strategies)
    selection = json.loads(spec.context.selection_json)
    selection['minimum_count'] = 2
    # Only 'a' supplies arithmetic; every admitted team must contain it.
    for c in selection['candidates']:
        if c['verifier_name'] != 'a':
            c['expected_capabilities'] = []
    modified, _ = build_spec(names=('a', 'b', 'c', 'd'), context_update={
        'budget': 2., 'selection_json': canonical_json(selection)})
    artifact, _ = build(modified, actual_code_revision=modified.code_revision)
    assert all(len(s.verifiers) == 2 and 'a' in s.verifiers for s in artifact.policy.strategies)


def test_reproducibility_and_runtime_provider_compatibility(monkeypatch):
    spec, _ = build_spec(names=('a', 'b', 'c'))
    first, _ = build(spec, actual_code_revision=spec.code_revision)
    second, _ = build(spec, actual_code_revision=spec.code_revision)
    assert verify_equivalent(first, second)['equivalent']
    assert first.artifact_id == second.artifact_id
    from tests.test_game_runtime import runtime_fixture
    from app.models.schemas import ValidationRequest
    from app.reputation.reputation_manager import ReputationManager
    import app.orchestration.validation_orchestrator as orchestration
    monkeypatch.setattr(orchestration, 'build_reputation_state', lambda: ReputationManager().export_state())
    monkeypatch.setattr(orchestration, 'save_reputation', lambda **kw: pytest.fail('production state write'))
    monkeypatch.setattr(orchestration.AutomaticGroundTruthEvaluator, 'evaluate',
                        lambda *a, **kw: pytest.fail('production ground truth access'))
    run, _, manager, _ = runtime_fixture(artifact=first)
    before = manager.export_state()
    response = run.validate(ValidationRequest(question='fixture question', answer='fixture answer'))
    assert response.execution_audit['policy_id'] == first.policy.policy_id
    assert manager.export_state() == before


def test_multiple_recording_gaps_are_reported_without_artifact(tmp_path):
    spec, _ = build_spec(names=('a', 'b'))
    payload = spec.model_dump(mode='json')
    for part in payload['manifest']['partitions']:
        part['examples'][0]['attempts'] = part['examples'][0]['attempts'][:1]
    config = tmp_path / 'missing.json'
    config.write_text(json.dumps(payload))
    out = tmp_path / 'out'
    assert main([str(config), '--output-dir', str(out)]) == 2
    report = json.loads((out / 'missing-inputs.json').read_text())
    assert sum('incomplete_candidate_recordings' in g['message'] for g in report['missing_inputs']) == 2
    assert not (out / 'policy.json').exists()


def test_pure_fitter_performs_no_file_access_or_production_state_write(monkeypatch):
    spec, _ = build_spec()
    from app.reputation.reputation_manager import ReputationManager
    live = ReputationManager()
    live.update_from_ground_truth('a', 'general', True, True)
    before = live.export_state()
    def forbidden(*args, **kwargs):
        pytest.fail('pure fitter attempted filesystem access')
    monkeypatch.setattr(Path, 'open', forbidden)
    monkeypatch.setattr('builtins.open', forbidden)
    artifact, _ = build(spec, actual_code_revision=spec.code_revision)
    assert artifact.context.plan.reputation_statistics[0].observation_count == 0
    assert live.export_state() == before


def test_publication_failure_reports_blocked_without_published_artifact(tmp_path, monkeypatch):
    spec, _ = build_spec()
    config = tmp_path / 'config.json'
    config.write_text(spec.model_dump_json())
    def blocked(*args, **kwargs):
        raise PermissionError('synthetic publication denial')
    monkeypatch.setattr(Path, 'replace', blocked)
    out = tmp_path / 'out'
    assert main([str(config), '--output-dir', str(out)]) == 2
    report = json.loads((out / 'missing-inputs.json').read_text())
    assert report['status'] == 'blocked' and not report['artifact_created']
    assert not (out / 'policy.json').exists()
