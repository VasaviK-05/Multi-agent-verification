"""Verify existing frozen fits, without native inference or held-out payloads.

Run from the repository root. Output is exclusive-create; historical files are
never written. Reference payoffs are replayed from training records. Compound
cells are reconstructed from sealed finalized development outcomes; a full
raw-record refit requires the custodian's unpublished canonical study inputs.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path


ROOT = Path('artifacts/remaining-category-studies-v1')


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def verify():
    from app.game.artifacts import PolicyArtifact
    from app.game.component_execution import ComponentPolicy, enumerate_component_strategies
    from app.game.models import PlanningContext, content_id
    from app.game.offline.attacks import AttackSpecification
    from app.game.offline.collection import RecordingBundle, completeness, export_training
    from app.game.offline.evaluation import construct_payoffs, summarize
    from app.game.offline.reliability import prepare_reliability_first
    from app.game.policy import validate_policy
    from app.game.solver import validate_solution
    from app.game.strategies import enumerate_strategies

    compound_dir = ROOT / 'compound-85/candidate'
    compound = ComponentPolicy.model_validate(read(compound_dir / 'policy.json'))
    outcomes = read(compound_dir / 'development-outcomes.json')
    assert content_id(outcomes) == compound.matrix.clean_coverage.source_evaluation_id
    inventory = read(compound_dir / 'inventory.json')
    checked = []
    for name, digest in inventory.items():
        path = compound_dir / name
        if path.exists():
            assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, name
            checked.append(name)
    for i, sid in enumerate(compound.matrix.strategy_ids):
        for j, aid in enumerate(compound.matrix.attack_ids):
            cell = [o for o in outcomes if o['strategy_id'] == sid and o['attack_id'] == aid]
            assert len(cell) == 48 and len({o['example_id'] for o in cell}) == 48
            value = sum(o['validation_loss'] for o in cell) / len(cell)
            assert math.isclose(value, compound.matrix.values[i][j], rel_tol=0, abs_tol=1e-12)
            if j == 0:
                coverage = sum(o['public_status'] != 'uncertain' for o in cell) / len(cell)
                assert coverage == dict(compound.matrix.clean_coverage.strategy_coverage)[sid]
    validate_solution(compound.matrix, compound.solution)

    reference_dir = ROOT / 'reference-50-v1'
    artifact = PolicyArtifact.model_validate(read(reference_dir / 'fit/policy.json'))
    validate_policy(artifact.policy, artifact.context)
    bundle = RecordingBundle.model_validate(read(reference_dir / 'training/reference/bundle.json'))
    assert completeness(bundle)['complete']
    # Remove only the two fitting overlays to recover the original replay context.
    data = artifact.context.model_dump()
    data.update(clean_coverage_json=None, reliability_first_json=None)
    original = PlanningContext.model_validate(data)
    fresh = original.model_dump()
    fresh.update(offline_evaluation_id=None, task_conditioning_json=None)
    manifest = export_training(bundle, PlanningContext.model_validate(fresh))
    assert manifest.model_dump(mode='json') == read(reference_dir / 'fit/training-manifest.json')
    attacks = AttackSpecification(**read(reference_dir / 'protocol.json')['attacks'])
    evaluation = construct_payoffs(original, manifest, artifact.contract, attacks)
    assert evaluation.model_dump(mode='json') == read(reference_dir / 'fit/development-evaluation.json')
    fitted, matrix = prepare_reliability_first(original, manifest, artifact.contract, attacks, evaluation, minimum=.5)
    assert fitted == artifact.context and matrix == artifact.policy.matrix
    validate_solution(matrix, artifact.policy.solution)
    old = ROOT / 'reference-current-v1/fit'
    for name in ('training-manifest', 'development-evaluation', 'contract'):
        assert read(old / (name + '.json')) == read(reference_dir / ('fit/' + name + '.json'))
    assert read(old / 'matrix.json')['values'] == matrix.model_dump(mode='json')['values']

    def summary(policy, strategies):
        probabilities = dict(policy.solution.probabilities)
        assert abs(math.fsum(probabilities.values()) - 1) <= 1e-12
        return dict(policy_id=policy.policy_id, matrix_id=policy.matrix.matrix_id,
                    dimensions=[len(policy.matrix.strategy_ids), len(policy.matrix.attack_ids)],
                    selected=[dict(strategy=s.model_dump(mode='json'), probability=probabilities[s.strategy_id])
                              for s in strategies if probabilities[s.strategy_id] > 0],
                    solution=policy.solution.model_dump(mode='json'))

    clean = evaluation.matrix.attack_ids[0]
    weights = dict(artifact.policy.solution.probabilities)
    metrics = summarize(tuple((o, weights[o.strategy_id]) for o in evaluation.outcomes if o.attack_id == clean), original.loss_configuration)
    return dict(version='compound_reference_existing_fit_audit_v1',
                compound=dict(**summary(compound, enumerate_component_strategies(compound.contract)),
                              matrix_reconstruction='sealed finalized development outcomes',
                              checked_inventory_files=checked,
                              unavailable_canonical_inputs=['preparation/study.json', 'candidate/freeze.json']),
                reference=dict(**summary(artifact.policy, enumerate_strategies(fitted).strategies),
                               artifact_id=artifact.artifact_id, matrix_reconstruction='training-record replay',
                               clean_metrics=metrics.model_dump(mode='json'),
                               clean_validation_loss=metrics.validation_loss(original.loss_configuration)),
                native_verifier_calls=0, generations=0, heldout_payloads_read=False,
                live_activation_proven=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = verify()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, indent=2, sort_keys=True)
    print('Verified existing Compound and Reference fits; zero native calls.')


if __name__ == '__main__':
    main()
