"""Fit/export a recorded offline policy without access to final-test outcomes."""

import argparse
from copy import deepcopy
import importlib.metadata
import json
import math
from pathlib import Path
import platform
import random
import subprocess

from pydantic import ValidationError

from app.game.models import content_id, PlanningContext
from app.game.artifacts import PolicyArtifact, DeploymentEpisode, InMemoryPolicyProvider
from app.game.policy import sample_policy
from app.game.solver import validate_solution
from app.game.research.__main__ import _object, _nonfinite
from app.game.research.specification import PolicyBuildSpecification
from app.game.research.readiness import check_readiness
from app.game.offline.evaluation import summarize, bind_evaluation, fit_policy, export_artifact


def environment_versions():
    versions = {name: importlib.metadata.version(name) for name in ('numpy', 'scipy', 'pydantic')}
    versions['python'] = platform.python_version()
    versions['platform'] = platform.platform()
    versions['architecture'] = platform.machine()
    versions['python_implementation'] = platform.python_implementation()
    try:
        from scipy.optimize._highspy import _core
        versions['highs'] = '.'.join(str(getattr(_core, 'HIGHS_VERSION_' + p))
                                     for p in ('MAJOR', 'MINOR', 'PATCH'))
    except (ImportError, AttributeError):
        versions['highs'] = 'unavailable; bundled with recorded scipy version'
    versions['solver_method'] = 'scipy.optimize.linprog:highs'
    versions['linprog_options'] = 'SciPy defaults; no custom LP options'
    return versions


def development_diagnostics(policy, evaluation, context):
    """Integrate recorded development outcomes over the full fitted distribution."""
    if evaluation.role != 'development' or policy.matrix != evaluation.matrix:
        raise ValueError('diagnostics require the fitted development evaluation')
    probabilities = dict(policy.solution.probabilities)
    scenarios = []
    for attack_id in evaluation.matrix.attack_ids:
        weighted = tuple((o, probabilities[o.strategy_id]) for o in evaluation.outcomes
                         if o.attack_id == attack_id)
        metrics = summarize(weighted, context.loss_configuration)
        scenarios.append(dict(attack_id=attack_id,
            development_validation_loss=metrics.validation_loss(context.loss_configuration),
            development_game_objective=metrics.mean_loss,
            uncertainty_rate=metrics.uncertainty_rate, decision_coverage=metrics.decision_coverage,
            expected_estimated_cost=metrics.estimated_resource_cost))
    worst = max(s['development_game_objective'] for s in scenarios)
    return dict(evidence_role='development', scenarios=scenarios,
        worst_case_scenarios=[s['attack_id'] for s in scenarios if s['development_game_objective'] == worst],
        clean_scenario=scenarios[0],
        worst_validation_loss=max(s['development_validation_loss'] for s in scenarios))


def verify_equivalent(first, second, *, matrix_atol=1e-12, reputation_atol=1e-12, probability_atol=1e-12):
    """Compare scientific outputs, excluding paths, timestamps and solver messages."""
    for tolerance in (matrix_atol, reputation_atol, probability_atol):
        if not math.isfinite(tolerance) or tolerance < 0:
            raise ValueError('invalid numerical tolerance')
    def close(a, b, tolerance):
        return len(a) == len(b) and all(math.isclose(x, y, rel_tol=0., abs_tol=tolerance)
                                       for x, y in zip(a, b))
    a, b = first.policy, second.policy
    if first.context.compatibility_id != second.context.compatibility_id or first.contract != second.contract:
        raise ValueError('fitting contexts or execution contracts differ')
    if a.matrix.strategy_definitions != b.matrix.strategy_definitions or a.matrix.attack_ids != b.matrix.attack_ids:
        raise ValueError('matrix axes differ')
    if not close([v for row in a.matrix.values for v in row],
                 [v for row in b.matrix.values for v in row], matrix_atol):
        raise ValueError('payoff matrices differ')
    # Snapshot records include discrete counts and priors; exact equality is stronger
    # than the declared absolute tolerance and avoids ignoring a provenance field.
    if first.context.plan.reputation_statistics != second.context.plan.reputation_statistics:
        raise ValueError('reputation snapshots differ')
    if (tuple(k for k, _ in a.solution.probabilities) != tuple(k for k, _ in b.solution.probabilities)
        or not close([p for _, p in a.solution.probabilities],
                     [p for _, p in b.solution.probabilities], probability_atol)):
        raise ValueError('policy probabilities differ')
    return dict(equivalent=True, matrix_atol=matrix_atol, reputation_atol=reputation_atol,
                probability_atol=probability_atol, relative_tolerance=0.)


class BuildInputError(ValueError):
    def __init__(self, readiness):
        self.readiness = readiness
        super().__init__('; '.join(readiness.blockers))


def build(specification, *, actual_code_revision, calibration=None,
          budget_ms=None, resource_weight_per_ms=None, expected_setup_fingerprint=None):
    """Pure fit/repeat/export/reload; no file, provider or production-state writes."""
    if calibration is not None:
        from app.game.offline.calibration import CalibrationArtifact, apply_calibration
        calibration = CalibrationArtifact.model_validate(calibration)
        if budget_ms is None or resource_weight_per_ms is None or expected_setup_fingerprint is None:
            raise ValueError('calibration requires explicit budget_ms, resource_weight_per_ms and expected_setup_fingerprint')
        if isinstance(specification, dict):
            # Populate absent costs before full validation; no guessed placeholder
            # costs are needed to represent an as-yet uncalibrated build input.
            specification = deepcopy(specification)
            context = specification.get('context')
            if not isinstance(context, dict) or not isinstance(context.get('loss_configuration'), dict):
                raise ValueError('calibration requires context and loss_configuration objects')
            context.update(attempt_costs=[(r['verifier_name'], r['attempt_cost'])
                for r in calibration.result['estimates']], budget=budget_ms, cost_units='ms')
            context['loss_configuration'].update(cost_units='ms', resource_weight=resource_weight_per_ms)
    spec = PolicyBuildSpecification.model_validate(specification)
    if calibration is not None:
        calibrated = apply_calibration(spec.context, calibration, manifest=spec.manifest,
            contract=spec.contract, recording=spec.recording, budget_ms=budget_ms,
            resource_weight_per_ms=resource_weight_per_ms,
            expected_setup_fingerprint=expected_setup_fingerprint)
        spec = PolicyBuildSpecification.model_validate({**spec.model_dump(), 'context': calibrated})
    elif budget_ms is not None or resource_weight_per_ms is not None or expected_setup_fingerprint is not None:
        raise ValueError('millisecond settings require a calibration artifact')
    # Do not repair a stale supplied snapshot or overwrite an existing binding.
    # bind_evaluation recomputes the complete snapshot using history alone.
    try:
        bound = bind_evaluation(spec.context, spec.manifest, spec.contract, spec.attacks)
    except ValueError:
        bound = spec.context  # readiness retains this error plus independent gaps
    spec = PolicyBuildSpecification.model_validate({**spec.model_dump(), 'context': bound})
    readiness = check_readiness(spec, actual_code_revision=actual_code_revision)
    if not readiness.ready:
        raise BuildInputError(readiness)

    def fit_and_export():
        policy, evaluation = fit_policy(spec.context, spec.manifest, spec.contract, spec.attacks,
                                        tolerance=spec.optimizer_tolerance)
        validate_solution(evaluation.matrix, policy.solution)
        artifact = export_artifact(policy, spec.context, spec.manifest, spec.contract, spec.attacks,
                                   applicable_domain=spec.context.plan.domain)
        return PolicyArtifact.model_validate_json(artifact.model_dump_json()), evaluation

    artifact, evaluation = fit_and_export()
    repeated, _ = fit_and_export()
    equivalence = verify_equivalent(artifact, repeated)
    # Exercise the existing provider and deployment compatibility contracts, with
    # local instances only. No verifier execution or application wiring occurs.
    provider = InMemoryPolicyProvider((artifact,))
    registered, = provider.snapshot()
    episode = DeploymentEpisode(episode_id='offline_reload_check', context=registered.context,
        contract=registered.contract, execution_configuration_id=registered.execution_configuration_id)
    sample_policy(registered.policy, episode.context, rng=random.Random(spec.policy_sampling_seeds[0]))
    probabilities = dict(artifact.policy.solution.probabilities)
    totals = {}
    positive = []
    for strategy in artifact.policy.strategies:
        p = probabilities[strategy.strategy_id]
        size = str(len(strategy.verifiers))
        totals.setdefault(size, []).append(p)
        if p > 0:
            positive.append(dict(**strategy.model_dump(mode='json'), probability=p))
    certificate = artifact.policy.solution.model_dump(mode='json')
    certificate.pop('message')  # diagnostic prose is incidental solver metadata
    scientific = dict(
        evidence_kind=spec.manifest.evidence_kind, artifact_id=artifact.artifact_id,
        policy_id=artifact.policy.policy_id, matrix_id=evaluation.matrix.matrix_id,
        reputation_snapshot_id=bound.reputation_snapshot_id,
        training_manifest_id=spec.manifest.manifest_id,
        reservation_id=spec.manifest.final_test_reservation.reservation_id,
        fitted_specification_id=spec.specification_id,
        applicability=dict(domain=bound.plan.domain, planning_category=readiness.planning_category,
                           compatibility_id=bound.compatibility_id,
                           execution_configuration_id=spec.contract.execution_configuration_id),
        budget=bound.budget, cost_units=bound.cost_units,
        loss_configuration=bound.loss_configuration.model_dump(mode='json'),
        dependencies=bound.dependencies.model_dump(mode='json'), attacks=spec.attacks.model_dump(mode='json'),
        feasible_strategies=len(artifact.policy.strategies), positive_probability_strategies=positive,
        probability_by_team_size={k: math.fsum(v) for k, v in totals.items()},
        probabilities=artifact.policy.solution.probabilities,
        concentration=('one strategy has probability one' if any(p == 1. for p in probabilities.values())
                       else 'multiple strategies have positive probability'),
        development=development_diagnostics(artifact.policy, evaluation, bound),
        certificate=certificate, reproducibility=equivalence,
        seeds=spec.policy_sampling_seeds, sampling_repetitions=spec.policy_sampling_repetitions,
        uncertainty_design=spec.uncertainty.model_dump(mode='json'),
        fitting_randomness='none: exact LP; seeds reserved for sampling/uncertainty, not extra evidence',
        provider_reload_verified=True,
        calibration=None if calibration is None else dict(
            calibration_id=calibration.calibration_id, input_digest=calibration.input_digest,
            method=calibration.method, cost_units=calibration.cost_units,
            freeze_record=calibration.request.freeze_record,
            estimated_quantity='sum of verifier-attempt wall times'))
    return artifact, scientific


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('configuration', type=Path)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--calibration', type=Path)
    parser.add_argument('--budget-ms', type=float)
    parser.add_argument('--resource-weight-per-ms', type=float)
    parser.add_argument('--measurement-setup-fingerprint')
    args = parser.parse_args(argv)
    gaps = []
    digest = None
    artifact = scientific = None
    root = Path(__file__).resolve().parents[3]
    revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()
    status = subprocess.check_output(['git', 'status', '--porcelain=v1'], cwd=root, text=True)
    sources = content_id([(p.relative_to(root).as_posix(), p.read_text(encoding='utf-8'))
                          for p in sorted((root / 'app').rglob('*.py'))])
    try:
        payload = json.loads(args.configuration.read_text(encoding='utf-8'),
                             object_pairs_hook=_object, parse_constant=_nonfinite)
        digest = content_id(payload)
        if not isinstance(payload, dict):
            raise ValueError('configuration must be a JSON object')
        spec = payload if args.calibration else PolicyBuildSpecification.model_validate(payload)
        if (args.output_dir / 'policy.json').exists():
            raise ValueError('output directory already contains policy.json; use a new build directory')
        calibration = None
        if args.calibration:
            from app.game.offline.calibration import read_json
            calibration = read_json(args.calibration)
        artifact, scientific = build(spec, actual_code_revision=revision, calibration=calibration,
            budget_ms=args.budget_ms, resource_weight_per_ms=args.resource_weight_per_ms,
            expected_setup_fingerprint=args.measurement_setup_fingerprint)
    except ValidationError as exc:
        gaps.extend(dict(code='invalid_input', location=list(e['loc']), message=e['msg'],
                         producer='dataset custodian / recording producer / study configuration owner')
                    for e in exc.errors(include_url=False))
    except BuildInputError as exc:
        gaps.extend(dict(code='readiness_blocker', location=[], message=message,
                         producer='recording producer / study configuration owner')
                    for message in exc.readiness.blockers)
    except (OSError, ValueError) as exc:
        gaps.append(dict(code='build_blocker', location=[], message=str(exc),
                         producer='study configuration owner'))
    success = artifact is not None and not gaps
    report = dict(status='complete' if success else 'blocked', artifact_created=success, missing_inputs=gaps,
                  scientific_outputs=scientific if success else None,
                  build_metadata=dict(input_digest=digest, code_revision=revision,
                                      application_source_digest=sources, working_tree_clean=not bool(status),
                                      environment=environment_versions()))
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / ('build-report.json' if success else 'missing-inputs.json')).write_text(
        json.dumps(report, indent=2, sort_keys=True, allow_nan=False), encoding='utf-8')
    summary = 'Policy build blocked. No PolicyArtifact created.\n\n' + '\n'.join(
        f"- {'.'.join(map(str, g['location'])) or 'configuration'}: {g['message']} Producer: {g['producer']}."
        for g in gaps) + '\n'
    if success:
        summary = (f"Policy build complete ({scientific['evidence_kind']}).\n"
            f"Artifact: {artifact.artifact_id}\nFeasible strategies: {scientific['feasible_strategies']}\n"
            f"Domain: {artifact.applicable_domain}; budget: {artifact.context.budget} {artifact.context.cost_units}.\n"
            f"Positive strategies: {json.dumps(scientific['positive_probability_strategies'])}\n"
            f"Probability by team size: {json.dumps(scientific['probability_by_team_size'])}\n"
            f"{scientific['concentration']}. This is the fitted solution; no causal explanation is inferred.\n"
            "All metrics below are development results, not held-out evidence.\n"
            + json.dumps(scientific['development'], indent=2, sort_keys=True) + '\n')
    (args.output_dir / 'summary.txt').write_text(summary, encoding='utf-8')
    if success:
        temporary = args.output_dir / 'policy.json.tmp'
        try:
            temporary.write_text(artifact.model_dump_json(indent=2), encoding='utf-8')
            # Verify actual saved bytes before publishing the artifact filename.
            PolicyArtifact.model_validate_json(temporary.read_text(encoding='utf-8'))
            temporary.replace(args.output_dir / 'policy.json')
        except (OSError, ValueError) as exc:
            report.update(status='blocked', artifact_created=False, scientific_outputs=None,
                missing_inputs=[dict(code='artifact_publication_failed', location=['output_dir'],
                                     message=str(exc), producer='build environment owner')])
            failure = json.dumps(report, indent=2, sort_keys=True, allow_nan=False)
            (args.output_dir / 'build-report.json').write_text(failure, encoding='utf-8')
            (args.output_dir / 'missing-inputs.json').write_text(failure, encoding='utf-8')
            summary = 'Policy publication failed. No PolicyArtifact published.\n' + str(exc) + '\n'
            (args.output_dir / 'summary.txt').write_text(summary, encoding='utf-8')
            print(summary)
            return 2
    print(summary)
    return 0 if success else 2


if __name__ == '__main__':
    raise SystemExit(main())
