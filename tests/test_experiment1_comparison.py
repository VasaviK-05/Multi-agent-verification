"""Phase 1 synthetic compatibility checks. Never open empirical final payloads."""
import pytest

from app.game.models import PlanningContext, PayoffMatrix, SolverResult, canonical_json
from app.game.offline.evaluation import bind_evaluation, construct_payoffs, export_artifact
from app.game.offline.records import TrainingManifest
from app.game.offline.reliability import prepare_reliability_first
from app.game.policy import build_policy
from app.game.research.comparison import (
    FrozenComparison, deterministic_id, prepare_comparison,
    restricted_matrix, score_development_pilot, score_frozen_final,
)
from app.game.research.specification import PolicyBuildSpecification
from app.game.solver import solve_minimax, validate_solution
from tests.test_game_research import study, frozen_study, REVISION
from tests.test_game_reliability_first import full_fixture, lex_matrix


def latest_fixture():
    """Synthetic v4 minimum-one policy with a noncompliant uniform baseline."""
    from app.game.execution_contract import ExecutionContract, TeamRequirements
    from app.game.offline.replay import category_id
    from app.game.task_conditioning import bind_task_history
    context, manifest, contract, attacks, _, _ = full_fixture()
    contract = ExecutionContract(**{**contract.model_dump(), 'version': 'offline_public_decision_v4',
        'coverage_version': 'task_output_contract_v2',
        'team_requirements': TeamRequirements(minimum_selected=1, minimum_informative=1)})
    context = PlanningContext(**{**context.model_dump(), 'offline_evaluation_id': None,
        'execution_contract_json': canonical_json(contract.model_dump(mode='json'))})
    data = manifest.model_dump()
    from tests.test_game_offline import report
    for partition in data['partitions']:
        for example in partition['examples']:
            example['planning_category'] = category_id(context)
            if partition['role'] == 'development':
                example['attempts'][1]['report_json'] = report('b', passed=False).model_dump_json()
    manifest = TrainingManifest(**data)
    context = bind_task_history(context, manifest)
    context = bind_evaluation(context, manifest, contract, attacks)
    development = construct_payoffs(context, manifest, contract, attacks)
    bound, matrix = prepare_reliability_first(context, manifest, contract, attacks, development, minimum=.9)
    policy = build_policy(bound, matrix)
    artifact = export_artifact(policy, bound, manifest, contract, attacks, applicable_domain='general')
    template = study(names=('a', 'b')).model_dump()
    template['recording']['execution_configuration_id'] = contract.execution_configuration_id
    spec = PolicyBuildSpecification(**{**template, 'version': 'offline_policy_build_v1',
        'manifest': manifest, 'context': bound, 'contract': contract, 'attacks': attacks})
    return spec, development, artifact


def test_latest_training_only_comparison_no_full_refit_or_final_payload(monkeypatch):
    spec, dev, artifact = latest_fixture()
    original = artifact.model_dump_json()
    import app.game.policy as policy_module
    import app.game.offline.records as records
    def forbidden(*args, **kwargs):
        raise AssertionError('full policy refit or reserved payload access')
    monkeypatch.setattr(policy_module, 'build_policy', forbidden)
    monkeypatch.setattr(records.FinalTestReservation, 'validate_payload', forbidden)
    frozen = prepare_comparison(spec, dev, artifact, freeze_record='SYNTHETIC phase1', actual_code_revision=REVISION)
    assert frozen.full_artifact.model_dump_json() == original
    assert next(p for p in frozen.policies if p.method == 'full_minimax').probabilities == artifact.policy.solution.probabilities
    assert FrozenComparison.model_validate_json(frozen.model_dump_json()) == frozen
    uniform = next(p for p in frozen.policies if p.method == 'uniform')
    assert uniform.coverage_compliance['satisfies'] is False
    assert all(p == 1 / len(artifact.policy.strategies) for _, p in uniform.probabilities)
    fixed = next(p for p in frozen.policies if p.method == 'deterministic_minimax')
    assert fixed.coverage_compliance['satisfies'] is True
    for p in frozen.policies:
        if p.method.startswith('fixed_'):
            assert p.development_matrix.clean_coverage.minimum == .9
            assert p.development_matrix.reliability_first.epsilon == artifact.policy.matrix.reliability_first.epsilon
            validate_solution(p.development_matrix, p.certificate)
    with pytest.raises(ValueError, match='released final partition'):
        score_frozen_final(spec, frozen, actual_code_revision=REVISION)
    with pytest.raises(ValueError, match='development'):
        prepare_comparison(spec, dev.model_copy(update={'role': 'final_test'}), artifact,
            freeze_record='SYNTHETIC invalid', actual_code_revision=REVISION)


def test_restricted_objective_keeps_validation_first_coverage_and_cost():
    matrix = lex_matrix()
    for aggregation in ('reputation_weighted', 'dependency_group'):
        indices = [i for i, s in enumerate(matrix.strategy_definitions) if s.aggregation == aggregation]
        if not indices:
            continue
        restricted = restricted_matrix(matrix, aggregation)
        assert restricted.clean_coverage.minimum == matrix.clean_coverage.minimum
        assert restricted.clean_coverage.source_evaluation_id == matrix.clean_coverage.source_evaluation_id
        assert restricted.reliability_first.validation_values == tuple(matrix.reliability_first.validation_values[i] for i in indices)
        assert restricted.reliability_first.cost_tolerance == matrix.reliability_first.cost_tolerance
        result = solve_minimax(restricted)
        assert result.status == 'optimal'
        validate_solution(restricted, result)
        assert deterministic_id(restricted, clean=False) == 1  # expensive lower-validation-loss row


def test_fixed_selection_does_not_trade_validation_loss_for_resource_penalty():
    matrix = lex_matrix()
    assert deterministic_id(matrix, clean=False) == 1
    data = matrix.model_dump()
    data['clean_coverage']['strategy_coverage'] = tuple((s, .1) for s in matrix.strategy_ids)
    impossible = PayoffMatrix(**data)
    assert deterministic_id(impossible, clean=False) is None
    assert solve_minimax(impossible).status == 'infeasible'


def test_full_distribution_retains_tiny_nonzero_probability():
    from app.game.offline.evaluation import fit_policy
    from app.game.solver import solution_diagnostics
    spec = study()
    policy, development = fit_policy(spec.context, spec.manifest, spec.contract, spec.attacks)
    weights = (1e-10, 1. - 1e-10)
    solution = policy.solution
    diagnostics = solution_diagnostics(policy.matrix, weights,
        tuple(p for _, p in solution.attack_probabilities), solution.tolerance)
    solution = SolverResult(**{**solution.model_dump(), **diagnostics,
        'probabilities': tuple(zip(policy.matrix.strategy_ids, weights))})
    policy = policy.model_copy(update={'solution': solution})
    artifact = export_artifact(policy, spec.context, spec.manifest, spec.contract, spec.attacks, applicable_domain='general')
    frozen = prepare_comparison(spec, development, artifact, freeze_record='SYNTHETIC tiny', actual_code_revision=REVISION)
    assert next(p for p in frozen.policies if p.method == 'full_minimax').probabilities == solution.probabilities
    assert dict(solution.probabilities)[policy.matrix.strategy_ids[0]] == 1e-10


def test_synthetic_final_cube_same_examples_attacks_and_protections(monkeypatch):
    spec = study(names=('a', 'b'))
    frozen, _, _ = frozen_study(spec)
    import app.game.research.comparison as comparison
    actual = comparison.replay
    calls = []
    def observed(context, strategy, attack, attacks, contract, example):
        calls.append((strategy.strategy_id, attack.attack_id, example.example_id, contract.threshold, contract.failure_contract))
        return actual(context, strategy, attack, attacks, contract, example)
    monkeypatch.setattr(comparison, 'replay', observed)
    result = score_frozen_final(spec, frozen, actual_code_revision=REVISION)
    assert len(calls) == len(frozen.full_artifact.policy.strategies) * 5
    assert {c[2] for c in calls} == {'final_test'}  # synthetic only
    assert {c[3:] for c in calls} == {(.55, 'all_selected_returned')}
    assert len({tuple(a for a, _ in method.attack_metrics) for method in result.methods}) == 1
    assert all(m.examples == 1 for method in result.methods for _, m in method.attack_metrics)


@pytest.mark.parametrize('state', ['unavailable', 'abstention', 'failed'])
def test_nondirectional_attempts_remain_uncertain_and_costed(state):
    from app.game.offline.records import DatasetManifest
    from app.game.offline.evaluation import fit_policy
    from tests.test_game_offline import attempt, unbind
    spec = study()
    data = spec.model_dump()
    for part in data['manifest']['partitions']:
        if part['role'] == 'development':
            part['examples'][0]['attempts'] = [attempt(state=state).model_dump()]
    manifest = DatasetManifest(**data['manifest'])
    context = bind_evaluation(unbind(spec.context), manifest, spec.contract, spec.attacks)
    spec = type(spec)(**{**data, 'manifest': manifest, 'context': context})
    policy, dev = fit_policy(context, manifest, spec.contract, spec.attacks)
    artifact = export_artifact(policy, context, manifest, spec.contract, spec.attacks, applicable_domain='general')
    frozen = prepare_comparison(spec, dev, artifact, freeze_record='SYNTHETIC states', actual_code_revision=REVISION)
    result = score_development_pilot(spec, frozen, actual_code_revision=REVISION)
    for method in result.methods:
        for _, metric in method.attack_metrics:
            assert metric.uncertain == 1 and metric.selective_risk is None
            assert metric.estimated_resource_cost == 1.


def test_drift_and_changed_protections_reject():
    spec, dev, artifact = latest_fixture()
    data = spec.model_dump()
    data['manifest']['partitions'][0]['examples'][0]['attempts'][0]['observed_resources_json'] = None
    with pytest.raises(ValueError):
        prepare_comparison(PolicyBuildSpecification(**data), dev, artifact,
            freeze_record='SYNTHETIC drift', actual_code_revision=REVISION)
    data = spec.model_dump()
    data['contract']['threshold'] = .6
    with pytest.raises(ValueError):
        prepare_comparison(PolicyBuildSpecification(**data), dev, artifact,
            freeze_record='SYNTHETIC threshold drift', actual_code_revision=REVISION)


def test_infeasible_restriction_is_reported_without_distribution():
    # One aggregation cannot meet Q; the full mixed game remains feasible.
    spec, dev, artifact = latest_fixture()
    from app.game.research.comparison import UnavailableMethod
    matrix = artifact.policy.matrix
    restricted = restricted_matrix(matrix, 'dependency_group')
    data = restricted.model_dump()
    data['clean_coverage']['strategy_coverage'] = tuple((s, 0.) for s in restricted.strategy_ids)
    impossible = PayoffMatrix(**data)
    result = solve_minimax(impossible)
    unavailable = UnavailableMethod(method='fixed_dependency_group', status=result.status,
        reason=result.message, development_matrix=impossible, solver_result=result)
    assert unavailable.status == 'infeasible' and unavailable.solver_result.probabilities == ()


# This fixture collects only synthetic history/development using report doubles.
from tests.test_compound_empirical import recorded


def test_component_comparison_preserves_obligations_and_reports_greedy_unavailable(recorded, monkeypatch):
    from app.game.offline.compound import fit, examples, replay_example
    from app.game.offline.attacks import enumerate_attacks
    from app.game.research.component_comparison import prepare_component_comparison, FrozenComponentComparison
    _, training, _, _ = recorded
    policy = fit(training)['policy']  # synthetic fixture creation only
    original = policy.model_dump_json()
    import app.game.offline.compound as compound
    import app.game.research.component_comparison as comparison
    def forbidden(*args, **kwargs):
        raise AssertionError('comparison attempted full component refit')
    monkeypatch.setattr(compound, 'fit', forbidden)
    actual_solve = comparison.solve_minimax
    def restricted_only(matrix, **kwargs):
        assert matrix.strategy_ids != policy.matrix.strategy_ids
        return actual_solve(matrix, **kwargs)
    monkeypatch.setattr(comparison, 'solve_minimax', restricted_only)
    frozen = prepare_component_comparison(policy, training, freeze_record='SYNTHETIC component freeze')
    assert FrozenComponentComparison.model_validate_json(frozen.model_dump_json()) == frozen
    assert policy.model_dump_json() == original
    assert frozen.full_policy.contract.obligations == policy.contract.obligations
    assert [(m.method, m.status) for m in frozen.unavailable_methods] == [('coverage_aware_greedy', 'unavailable')]
    assert next(m for m in frozen.methods if m.method == 'full_minimax').probabilities == policy.solution.probabilities
    assert all(m.coverage_compliance['satisfies'] for m in frozen.methods)
    strategy = __import__('app.game.component_execution', fromlist=['enumerate_component_strategies']).enumerate_component_strategies(policy.contract)[0]
    action = enumerate_attacks(training.study.dependencies, training.study.attack_specification)[0]
    group = examples(training.study, 'development')[0]['group_id']
    rows = [replay_example(training.study, policy.contract, strategy, e, training.development.bundles, action)
            for e in examples(training.study, 'development') if e['group_id'] == group]
    assert {r['variant']: r['public_status'] for r in rows} == {
        'correct': 'passed', 'wrong_math': 'failed', 'wrong_base': 'failed', 'both_wrong': 'failed'}
    assert all(len(r['components']) == 2 for r in rows)


def test_component_comparison_rejects_test_role_and_resource_drift(recorded):
    from app.game.offline.compound import fit
    from app.game.research.component_comparison import prepare_component_comparison
    _, training, _, _ = recorded
    policy = fit(training)['policy']
    data = training.model_dump()
    data['development']['role'] = 'final_test'
    with pytest.raises(ValueError, match='cannot enter training'):
        prepare_component_comparison(policy, data, freeze_record='SYNTHETIC invalid role')
    data = training.model_dump()
    # No saved scope can stand in for actual recorded resource observations.
    data['development']['bundles'][0][1]['attempts'][0]['attempt']['observed_resources_json'] = None
    with pytest.raises(ValueError):
        prepare_component_comparison(policy, data, freeze_record='SYNTHETIC drift')


def test_failed_restricted_solve_does_not_become_a_policy(monkeypatch):
    import app.game.research.comparison as comparison
    from app.game.offline.evaluation import fit_policy
    spec = study()
    policy, dev = fit_policy(spec.context, spec.manifest, spec.contract, spec.attacks)
    artifact = export_artifact(policy, spec.context, spec.manifest, spec.contract, spec.attacks, applicable_domain='general')
    def failed(matrix, *, tolerance):
        return SolverResult(status='solver_failure', message='SYNTHETIC solver failure',
            matrix_id=matrix.matrix_id, tolerance=tolerance)
    monkeypatch.setattr(comparison, 'solve_minimax', failed)
    frozen = prepare_comparison(spec, dev, artifact, freeze_record='SYNTHETIC failed restriction', actual_code_revision=REVISION)
    assert len(frozen.unavailable_methods) == 2
    assert all(m.status == 'solver_failure' and m.solver_result.probabilities == () for m in frozen.unavailable_methods)
    assert all(not p.method.startswith('fixed_') for p in frozen.policies)
    assert FrozenComparison.model_validate_json(frozen.model_dump_json()) == frozen
    data = frozen.model_dump()
    missing = data['unavailable_methods'][0]
    missing['status'] = missing['solver_result']['status'] = 'infeasible'
    with pytest.raises(ValueError, match='coverage is feasible'):
        FrozenComparison(**data)
    data = frozen.model_dump()
    data['policies'] = (*data['policies'], data['policies'][0])
    with pytest.raises(ValueError, match='exactly once'):
        FrozenComparison(**data)


def test_legacy_freeze_serialization_does_not_add_empty_availability_field():
    frozen, _, _ = frozen_study(study())
    assert 'unavailable_methods' not in frozen.model_dump()
    assert FrozenComparison.model_validate_json(frozen.model_dump_json()).comparison_id == frozen.comparison_id
