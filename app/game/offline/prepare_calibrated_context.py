"""Prepare a new context/category using public calibration; never rewrite recordings."""
import argparse
import json
from pathlib import Path

from pydantic import Field, StrictFloat

from app.game.dependencies import FrozenModel
from app.game.offline.calibration import CalibrationArtifact, Text, apply_calibration, read_json
from app.game.offline.replay import category_id
from app.game.research.specification import PolicyBuildSpecification
from app.game.models import PlanningContext
from app.game.execution_contract import ExecutionContract
from app.game.research.specification import RecordingConfiguration
from app.game.offline.attacks import AttackSpecification


class MillisecondSettings(FrozenModel):
    budget_ms: StrictFloat = Field(ge=0)
    resource_weight_per_ms: StrictFloat = Field(ge=0)
    expected_setup_fingerprint: Text


class CollectedContextInput(FrozenModel):
    context: dict
    contract: ExecutionContract
    recording: RecordingConfiguration
    attacks: AttackSpecification


def prepare_collected_context(configuration, bundle, calibration, settings):
    """Initial export from detached raw reports, not relabeling an existing manifest."""
    from app.game.offline.collection import RecordingBundle, export_training
    configuration = CollectedContextInput.model_validate(configuration)
    bundle = RecordingBundle.model_validate(bundle)
    calibration = CalibrationArtifact.model_validate(calibration)
    settings = MillisecondSettings.model_validate(settings)
    raw = configuration.context
    if not isinstance(raw.get('loss_configuration'), dict):
        raise ValueError('explicit loss_configuration required')
    # The complete original context remains intact. Only fields explicitly supplied
    # by the artifact/settings are populated; stale bindings are never cleared.
    context = PlanningContext(**{**raw, 'attempt_costs': tuple(
        (r['verifier_name'], r['attempt_cost']) for r in calibration.result['estimates']),
        'budget': settings.budget_ms, 'cost_units': 'ms', 'loss_configuration': {
            **raw['loss_configuration'], 'cost_units': 'ms', 'resource_weight': settings.resource_weight_per_ms}})
    manifest = export_training(bundle, context)
    checked = apply_calibration(context, calibration, manifest=manifest,
        contract=configuration.contract, recording=configuration.recording, **settings.model_dump())
    if checked.compatibility_id != context.compatibility_id:
        raise ValueError('calibration changed the initially exported context')
    from app.game.offline.evaluation import bind_evaluation
    validated = bind_evaluation(checked, manifest, configuration.contract, configuration.attacks)
    return dict(version='calibrated_collected_context_v1', context=checked.model_dump(mode='json'),
        manifest=manifest.model_dump(mode='json'), source_bundle_id=bundle.bundle_id,
        source_request_id=bundle.request.request_id, calibration_id=calibration.calibration_id,
        validated_evaluation_binding_id=validated.offline_evaluation_id,
        planning_category=category_id(checked), recordings_rewritten=False,
        export_kind='initial_training_export_from_detached_reports')


def prepare_context(specification, calibration, settings):
    spec = PolicyBuildSpecification.model_validate(specification)
    calibration = CalibrationArtifact.model_validate(calibration)
    settings = MillisecondSettings.model_validate(settings)
    context = apply_calibration(spec.context, calibration, manifest=spec.manifest,
        contract=spec.contract, recording=spec.recording, **settings.model_dump())
    category = category_id(context)
    incompatible = [dict(role=p.role, example_id=e.example_id,
        recorded_category=e.planning_category, required_category=category)
        for p in spec.manifest.partitions for e in p.examples if e.planning_category != category]
    return dict(version='calibrated_context_preparation_v1', context=context.model_dump(mode='json'),
        planning_category=category, source_specification_id=spec.specification_id,
        source_training_manifest_id=spec.manifest.manifest_id,
        calibration_id=calibration.calibration_id,
        final_test_reservation_id=spec.manifest.final_test_reservation.reservation_id,
        incompatible_recordings=incompatible, recordings_rewritten=False,
        next_action=('recording producer must recollect under the new category or supply a separately reviewed provenance-preserving category contract'
                     if incompatible else 'validate the complete specification with the existing builder'))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('specification', type=Path)
    parser.add_argument('--calibration', type=Path, required=True)
    parser.add_argument('--settings', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--collection-bundle', type=Path,
                        help='Initial export from immutable raw collection; input contains context/contract/recording/attacks')
    args = parser.parse_args(argv)
    try:
        if args.collection_bundle:
            result = prepare_collected_context(read_json(args.specification), read_json(args.collection_bundle),
                read_json(args.calibration), read_json(args.settings))
        else:
            result = prepare_context(read_json(args.specification), read_json(args.calibration), read_json(args.settings))
        with args.output.open('x', encoding='utf-8') as handle:
            json.dump(result, handle, sort_keys=True, indent=2, allow_nan=False)
    except (ValueError, OSError) as exc:
        from app.benchmark.project_adapter import error_reason
        print(json.dumps(dict(ready=False, blocker=error_reason(exc))))
        return 2
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
