"""Explicit retrospective reporting API. Never fits or selects any baseline.

Final APIs require separately released recordings; readiness/CLI never call them.
"""
from app.game.models import canonical_json, content_id
from app.game.offline.attacks import enumerate_attacks
from app.game.offline.replay import replay
from app.game.research.comparison import comparison_examples, validate_frozen
from app.game.research.experiment1.manifest import (
    AtomicEntry, ComponentEntry, ExperimentManifest, readiness,
)
from app.game.research.experiment1.metrics import (
    Cube, Distribution, Execution, Outcome, point_report, bootstrap_report, paired_point_differences,
)


def _execution(call_id, state, recorded, audit):
    # Recording format has no structured exception field. State-only reasons are
    # explicitly labelled; report_provenance is retained, never guessed as cause.
    reason = audit.reason if audit.reason == 'suppressed' else 'recorded_state_only:' + recorded.state
    return Execution(call_id=call_id, state=state, recorded_state=recorded.state,
        reason=reason, provenance=recorded.report_provenance)


def atomic_cube(entry, role, *, final_partition=None):
    if role not in {'development', 'final_test'}:
        raise ValueError('only development or explicit final reporting supported')
    entry = AtomicEntry.model_validate(entry)
    spec, frozen = validate_frozen(entry.specification, entry.comparison,
        actual_code_revision=entry.specification.code_revision)
    examples = comparison_examples(spec, role, final_partition)
    actions = enumerate_attacks(spec.context.dependencies, spec.attacks)
    rows = []
    for strategy in frozen.full_artifact.policy.strategies:
        for action in actions:
            for example in examples:
                outcome = replay(spec.context, strategy, action, spec.attacks, spec.contract, example)
                original = {a.verifier_name: a for a in example.attempts}
                audits = {a.verifier_name: a for a in outcome.audit}
                rows.append(Outcome(example_id=example.example_id, group_id=example.split_identity,
                    strategy_id=strategy.strategy_id, attack_id=action.attack_id, correct=example.answer_is_correct,
                    status=outcome.public_status, estimated_cost=outcome.estimated_attempt_cost,
                    unresolved=outcome.unresolved, reasons=outcome.reasons,
                    executions=tuple(_execution(name, state, original[name], audits[name])
                        for name, state in outcome.execution_states)))
    loss = spec.context.loss_configuration
    return Cube(example_groups=tuple((e.example_id, e.split_identity) for e in examples),
        strategy_ids=frozen.full_artifact.policy.matrix.strategy_ids, attacks=actions, outcomes=tuple(rows),
        methods=tuple(Distribution(method=p.method, probabilities=p.probabilities,
            development_coverage=p.coverage_compliance) for p in frozen.policies),
        false_accept_penalty=loss.false_accept, false_reject_penalty=loss.false_reject,
        uncertainty_penalty=loss.uncertain, resource_coefficient=loss.resource_weight, cost_units=loss.cost_units)


def component_cube(entry, role, *, final_recordings=None):
    from app.game.offline.compound import examples, replay_example, validate_recordings
    from app.game.component_execution import enumerate_component_strategies
    from app.game.offline.calibration import MeasurementSetup
    from app.game.offline.attacks import AttackAudit
    entry = ComponentEntry.model_validate(entry)
    training, frozen = entry.training, entry.comparison
    if role == 'development':
        if final_recordings is not None:
            raise ValueError('final recordings cannot enter development reporting')
        records = training.development
    elif role == 'final_test':
        if final_recordings is None:
            raise ValueError('explicit separately released final recordings required')
        setup = training.setup if entry.resource_transfer is None else MeasurementSetup.model_validate(entry.resource_transfer['scoped_setup'])
        records = validate_recordings(training.study, final_recordings, setup, freeze_id=entry.original_freeze_id)
        if records.role != 'final_test':
            raise ValueError('final reporting requires the reserved final partition')
    else:
        raise ValueError('only development or explicit final reporting supported')
    policy = frozen.full_policy
    strategies = enumerate_component_strategies(policy.contract)
    actions = enumerate_attacks(training.study.dependencies, training.study.attack_specification)
    sample = examples(training.study, role)
    rows = []
    for strategy in strategies:
        for attack in actions:
            for example in sample:
                out = replay_example(training.study, policy.contract, strategy, example, records.bundles, attack)
                executions, unresolved, reasons = [], [], list(out['reasons'])
                for component in out['components']:
                    cid = component['component_id']
                    bundle = dict(records.bundles)[cid]
                    originals = {a.candidate: a.attempt for a in bundle.attempts
                        if a.example_id == example['example_id'] + '-' + cid}
                    audits = {a['verifier_name']: AttackAudit.model_validate(a) for a in out['attack_audit']
                        if a['validation_id'] == component['validation_id']}
                    executions.extend(_execution(cid + '/' + name, state, originals[name], audits[name])
                                      for name, state in component['states'])
                    unresolved.extend(cid + ':' + cap for cap in component['unresolved'])
                    reasons.extend(cid + ':' + reason for reason in component['reasons'])
                rows.append(Outcome(example_id=example['example_id'], group_id=example['group_id'],
                    strategy_id=strategy.strategy_id, attack_id=attack.attack_id, correct=out['answer_is_correct'],
                    status=out['public_status'], estimated_cost=out['estimated_cost'], unresolved=tuple(unresolved),
                    reasons=tuple(reasons), executions=tuple(executions), components_json=canonical_json(out['components'])))
    loss = training.study.loss
    return Cube(example_groups=tuple((e['example_id'], e['group_id']) for e in sample),
        strategy_ids=policy.matrix.strategy_ids, attacks=actions, outcomes=tuple(rows),
        methods=tuple(Distribution(method=p.method, probabilities=p.probabilities,
            development_coverage=p.coverage_compliance) for p in frozen.methods),
        false_accept_penalty=loss.false_accept, false_reject_penalty=loss.false_reject,
        uncertainty_penalty=loss.uncertain, resource_coefficient=loss.resource_weight, cost_units=loss.cost_units)


def report_cohort(manifest, cohort, *, actual_commit, actual_source_fingerprint,
                  role='development', released_final=None, source_root=None):
    """Separate explicit final release; no filesystem discovery or final-data reads.

    Source checks and complete manifest readiness precede replay. No optimizer is
    called. The caller must obtain approval before supplying empirical final data.
    """
    manifest = ExperimentManifest.model_validate(manifest)
    check = readiness(manifest, actual_commit=actual_commit, actual_source_fingerprint=actual_source_fingerprint, source_root=source_root)
    if not check['ready']:
        raise ValueError('experiment is not ready: ' + '; '.join(check['blockers']))
    entry = next(e for e in manifest.cohorts if e.cohort == cohort)
    if isinstance(entry, AtomicEntry):
        cube = atomic_cube(entry, role, final_partition=released_final)
        policy_id = entry.comparison.full_artifact.policy.policy_id
    elif isinstance(entry, ComponentEntry):
        cube = component_cube(entry, role, final_recordings=released_final)
        policy_id = entry.comparison.full_policy.policy_id
    else:
        return dict(manifest_id=manifest.manifest_id, cohort=cohort, disposition=entry.kind,
            explanation=getattr(entry, 'explanation', None), metrics=None)
    points = point_report(cube)
    return dict(version='retrospective_experiment1_report_v1', manifest_id=manifest.manifest_id,
        cohort=cohort, role=role, status=manifest.status, policy_id=policy_id,
        comparison_id=entry.comparison.comparison_id, cube_id=content_id(cube.model_dump(mode='json')),
        released_payload_id=content_id(released_final.model_dump(mode='json') if hasattr(released_final, 'model_dump') else released_final)
            if released_final is not None else None,
        reporting_environment=manifest.reporting_environment,
        execution_reason_contract='recorded_states_and_attack_audits_no_invented_exception_causes',
        cost_units=cube.cost_units, metrics=points, paired_differences=paired_point_differences(points), uncertainty=bootstrap_report(cube, manifest.statistics),
        unavailable_methods=[m.model_dump(mode='json') for m in entry.comparison.unavailable_methods],
        outcomes=[o.model_dump(mode='json') for o in cube.outcomes])
