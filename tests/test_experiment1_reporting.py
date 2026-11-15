"""Synthetic expectations/statistics only; no empirical outcomes are loaded."""
from copy import deepcopy

import numpy as np
import pytest

from app.game.dependencies import DependencyRegistry
from app.game.offline.attacks import AttackSpecification, enumerate_attacks
from app.game.research.experiment1.metrics import (
    Cube, Distribution, Execution, Outcome, Statistics, bootstrap_report, point_report, paired_point_differences,
)


def cube_fixture(*, groups=2, multiple_failure_groups=False, tiny=False):
    if multiple_failure_groups:
        registry = DependencyRegistry(version='SYNTHETIC', dependencies=(
            dict(resource_id='model-a', compromise_pathway='SYNTHETIC a', verifiers=('a',)),
            dict(resource_id='model-b', compromise_pathway='SYNTHETIC b', verifiers=('b',))))
    else:
        registry = DependencyRegistry(version='SYNTHETIC', unresolved=('a', 'b'))
    actions = enumerate_attacks(registry, AttackSpecification(version='report_corruption_v1', suppression='unavailable'))
    examples = tuple((f'e{i}', f'g{i//2}') for i in range(groups * 2))
    outcomes = []
    for strategy in ('singleton', 'pair'):
        for action in actions:
            for i, (eid, gid) in enumerate(examples):
                correct = i % 2 == 0
                status = ('passed' if correct else 'failed') if strategy == 'singleton' else 'uncertain'
                if action.kind == 'forced_support': status = 'passed'
                if action.kind == 'forced_rejection': status = 'failed'
                if action.kind == 'suppression': status = 'uncertain'
                states = tuple(Execution(call_id=name,
                    state='unavailable' if action.kind == 'suppression' else 'directional',
                    recorded_state='directional', reason='suppressed' if action.kind == 'suppression' else 'recorded_state_only:directional',
                    provenance='SYNTHETIC report') for name in (('a',) if strategy == 'singleton' else ('a', 'b')))
                outcomes.append(Outcome(example_id=eid, group_id=gid, strategy_id=strategy, attack_id=action.attack_id,
                    correct=correct, status=status, estimated_cost=1. if strategy == 'singleton' else 3.,
                    unresolved=('arithmetic',) if status == 'uncertain' else (),
                    reasons=('missing_achieved_coverage',) if status == 'uncertain' else (), executions=states))
    probability = 1e-10 if tiny else .25
    return Cube(example_groups=examples, strategy_ids=('singleton', 'pair'), attacks=actions, outcomes=tuple(outcomes),
        methods=(Distribution(method='full_minimax', probabilities=(('singleton', probability), ('pair', 1. - probability)), development_coverage={}),
                 Distribution(method='uniform', probabilities=(('singleton', .5), ('pair', .5)), development_coverage={}),
                 Distribution(method='deterministic_minimax', probabilities=(('singleton', 1.), ('pair', 0.)), development_coverage={})),
        false_accept_penalty=1., false_reject_penalty=1., uncertainty_penalty=.2, resource_coefficient=.1, cost_units='ms')


def test_exact_mixed_metrics_and_correct_worst_case_order():
    cube = cube_fixture()
    before = cube.model_dump_json()
    points = point_report(cube)
    full = points[0]
    clean = full['attacks'][0]['metrics']
    assert clean['correct_accept'] == .5 and clean['correct_reject'] == .5
    assert clean['false_accept'] == clean['false_reject'] == 0.
    assert clean['uncertainty_rate'] == .75 and clean['decision_coverage'] == .25
    assert clean['selective_risk'] == 0.
    assert clean['validation_loss'] == pytest.approx(.15)
    assert clean['estimated_attempt_cost'] == 2.5 and clean['total_loss'] == pytest.approx(.4)
    assert full['worst_case_expected_loss'] == .5  # NOT mean(per-example worst)=1
    assert full['worst_case_total_loss'] == .75
    assert len(full['worst_case_attack_ids']) == 2
    assert {a['attack_kind'] for a in full['attacks']} == {'clean', 'forced_support', 'forced_rejection', 'confidence_inflation', 'suppression'}
    difference = paired_point_differences(points)[1]
    assert difference['attacks'][0]['metrics']['validation_loss'] == pytest.approx(.15)
    assert cube.model_dump_json() == before


def test_group_attack_identities_do_not_collapse_same_kind():
    cube = cube_fixture(multiple_failure_groups=True)
    report = point_report(cube)
    assert len(report[0]['attacks']) == 9
    support = [a for a in report[0]['attacks'] if a['attack_kind'] == 'forced_support']
    assert len({a['attack_id'] for a in support}) == len({a['dependency_group_id'] for a in support}) == 2


def test_suppression_zero_decisions_and_failure_reason_counts():
    full = point_report(cube_fixture())[0]
    suppressed = next(a for a in full['attacks'] if a['attack_kind'] == 'suppression')
    m = suppressed['metrics']
    assert m['selective_risk'] is None and m['decision_coverage'] == 0.
    assert m['validation_loss'] == .2 and m['unresolved_coverage_rate'] == 1.
    assert m['execution_failure_attempts'] == 7.  # 4 * (.25*1 + .75*2)
    assert m['recorded_execution_failure_attempts'] == 0.
    assert m['cases_with_execution_failure'] == 4.
    assert suppressed['execution_failure_reasons']['a:unavailable:suppressed'] == 4.
    assert suppressed['unresolved_reasons']['missing_achieved_coverage'] == 4.


def test_failed_recorded_attempts_and_tiny_probabilities_are_retained():
    cube = cube_fixture(tiny=True)
    data = cube.model_dump()
    o = data['outcomes'][0]
    o['executions'][0].update(state='failed', recorded_state='failed', reason='recorded_state_only:failed')
    o.update(status='uncertain', unresolved=('arithmetic',), reasons=('selected_execution_incomplete',))
    report = point_report(Cube(**data))[0]
    assert report['probabilities'][0][1] == 1e-10
    assert report['attacks'][0]['metrics']['recorded_execution_failure_attempts'] == 1e-10


@pytest.mark.parametrize('change', ['missing_zero_probability_row', 'duplicate', 'truth', 'group', 'cost'])
def test_cube_integrity_includes_all_methods_examples_attacks(change):
    data = cube_fixture().model_dump()
    if change == 'missing_zero_probability_row': data['outcomes'] = data['outcomes'][:-1]
    if change == 'duplicate': data['outcomes'] = (*data['outcomes'], data['outcomes'][0])
    if change == 'truth': data['outcomes'][1]['correct'] = not data['outcomes'][1]['correct']
    if change == 'group': data['outcomes'][0]['group_id'] = 'not-a-group'
    if change == 'cost': data['outcomes'][0]['estimated_cost'] = 77.
    with pytest.raises(ValueError): Cube(**data)


def test_paired_group_bootstrap_reproducibility_undefined_risk_and_differences():
    cube = cube_fixture()
    stats = Statistics(resamples=40)
    first = bootstrap_report(cube, stats)
    assert first == bootstrap_report(cube, stats)
    clean = cube.attacks[0].attack_id
    difference = next(i for i in first['intervals'] if i['method'] == 'full_minimax-minus-deterministic_minimax'
        and i['attack_id'] == clean and i['metric'] == 'validation_loss')
    assert difference['interval95'] == pytest.approx([.15, .15])
    suppression = cube.attacks[-1].attack_id
    undefined = next(i for i in first['intervals'] if i['method'] == 'full_minimax' and i['attack_id'] == suppression and i['metric'] == 'selective_risk')
    assert undefined['interval95'] is None and undefined['defined_resamples'] == 0
    assert undefined['undefined_fraction'] == 1.
    assert any(i['metric'] == 'worst_case_expected_loss' and i['attack_id'] == 'complete_attack_set' for i in first['intervals'])


def test_bootstrap_keeps_whole_groups_and_pairing_for_unequal_group_sizes():
    cube = cube_fixture()
    data = cube.model_dump()
    # One three-example group and one single-example group.
    data['example_groups'] = tuple((f'e{i}', 'big' if i < 3 else 'small') for i in range(4))
    for row in data['outcomes']: row['group_id'] = 'small' if row['example_id'] == 'e3' else 'big'
    cube = Cube(**data)
    config = Statistics(resamples=60)
    result = bootstrap_report(cube, config)
    rng = np.random.default_rng(config.seed)
    draws = rng.integers(0, 2, size=(config.resamples, 2))  # sorted big, small
    expected = np.asarray([sum(3 if i == 0 else 1 for i in draw) for draw in draws])
    interval = next(i for i in result['intervals'] if i['method'] == 'full_minimax'
        and i['attack_id'] == cube.attacks[0].attack_id and i['metric'] == 'examples')
    assert interval['interval95'] == np.quantile(expected, [.025, .975]).tolist()
    diffs = [i for i in result['intervals'] if i['method'] == 'full_minimax-minus-uniform' and i['metric'] == 'examples']
    assert all(i['interval95'] == [0., 0.] for i in diffs)


def test_single_group_no_population_interval_and_fixed_defaults():
    result = bootstrap_report(cube_fixture(groups=1), Statistics(resamples=3))
    assert result['intervals'] == [] and result['reason']
    assert Statistics().resamples == 5000 and Statistics().seed == 20261112
    assert Statistics().confidence_level == .95


def test_original_semantic_infeasibility_and_manifest_defaults():
    from tests.test_game_clean_coverage import covered_matrix
    from app.game.solver import solve_minimax
    from app.game.research.experiment1.manifest import InfeasibleEntry, ExperimentManifest
    matrix = covered_matrix(.9, (.0, .575))
    result = solve_minimax(matrix)
    entry = InfeasibleEntry(matrix=matrix, solution=result, explanation='SYNTHETIC original 90% infeasible')
    assert entry.solution.probabilities == ()
    data = entry.model_dump()
    data['solution']['status'] = 'optimal'
    with pytest.raises(ValueError): InfeasibleEntry(**data)
    with pytest.raises(ValueError):
        ExperimentManifest(experiment_id='SYNTHETIC', source_commit='a'*40, source_fingerprint='b'*64,
            status='confirmatory', cohorts=(entry,))


def test_schema_and_readiness_cli_are_read_only_and_cannot_score(tmp_path, capsys, monkeypatch):
    import json
    from app.game.research.experiment1.__main__ import main
    from app.game.research.experiment1.manifest import ExperimentManifest, BlockedEntry, COHORTS
    import app.game.research.experiment1.runner as runner
    def forbidden(*args, **kwargs): raise AssertionError('CLI attempted replay or scoring')
    monkeypatch.setattr(runner, 'atomic_cube', forbidden)
    monkeypatch.setattr(runner, 'component_cube', forbidden)
    assert main(['schema']) == 0
    schema = json.loads(capsys.readouterr().out)
    assert schema['properties']['status']['const'] == 'retrospective_exploratory'
    manifest = ExperimentManifest(experiment_id='SYNTHETIC BLOCKED', source_commit='a'*40, source_fingerprint='b'*64,
        cohorts=tuple(BlockedEntry(cohort=n, reason='SYNTHETIC absent inputs') for n in COHORTS))
    path = tmp_path / 'manifest.json'
    path.write_text(manifest.model_dump_json())
    before = path.read_bytes()
    assert main(['readiness', str(path)]) == 2
    output = json.loads(capsys.readouterr().out)
    assert not output['ready'] and output['final_payloads_read'] is False
    assert path.read_bytes() == before and len(list(tmp_path.iterdir())) == 1
    with pytest.raises(SystemExit): main(['score', str(path)])
    path.write_text('{"experiment_id":"a","experiment_id":"b"}')
    assert main(['readiness', str(path)]) == 2
    assert 'duplicate JSON key' in capsys.readouterr().out


def test_any_undefined_resample_omits_unconditional_risk_interval():
    data = cube_fixture().model_dump()
    for row in data['outcomes']:
        if row['group_id'] == 'g1':
            row['status'] = 'uncertain'
    cube = Cube(**data)
    result = bootstrap_report(cube, Statistics(resamples=80))
    interval = next(i for i in result['intervals'] if i['method'] == 'deterministic_minimax'
        and i['attack_id'] == cube.attacks[0].attack_id and i['metric'] == 'selective_risk')
    assert interval['interval95'] is None
    assert 0 < interval['defined_resamples'] < interval['total_resamples']


def test_bootstrap_recomputes_complete_attack_maximum_in_each_resample():
    data = cube_fixture().model_dump()
    actions = {a.attack_id: a.kind for a in cube_fixture().attacks}
    for row in data['outcomes']:
        row['correct'] = row['group_id'] == 'g0'
        kind = actions[row['attack_id']]
        if kind in {'clean', 'confidence_inflation'} and row['strategy_id'] == 'singleton':
            row['status'] = 'passed' if row['correct'] else 'failed'
    cube = Cube(**data)
    result = bootstrap_report(cube, Statistics(resamples=80))
    interval = next(i for i in result['intervals'] if i['method'] == 'full_minimax'
        and i['metric'] == 'worst_case_expected_loss')
    assert interval['interval95'] == [.5, 1.]
    assert point_report(cube)[0]['worst_case_expected_loss'] == .5


def test_reporting_environment_is_frozen_separately_from_collection():
    from app.game.research.experiment1.manifest import ExperimentManifest, BlockedEntry, readiness, reporting_environment, COHORTS
    manifest = ExperimentManifest(experiment_id='SYNTHETIC runtime binding', source_commit='a'*40,
        source_fingerprint='b'*64, cohorts=tuple(BlockedEntry(cohort=c, reason='SYNTHETIC') for c in COHORTS))
    assert manifest.reporting_environment == reporting_environment()
    data = manifest.model_dump()
    data['reporting_environment']['numpy'] = 'different'
    result = readiness(ExperimentManifest(**data), actual_commit='a'*40, actual_source_fingerprint='b'*64)
    assert 'reporting_environment_mismatch' in result['blockers']
