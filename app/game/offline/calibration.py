"""Offline engineering estimates: summed verifier-attempt wall times, never prices."""
import argparse
import json
import math
import statistics
from pathlib import Path
from typing import Annotated, Literal

from pydantic import AfterValidator, Field, StrictBool, StrictFloat, model_validator

from app.game.dependencies import FrozenModel, identifier
from app.game.models import PlanningContext, content_id
from app.game.resource_provenance import ResourceManifest
from app.game.offline.records import FinalTestReservation

Text = Annotated[str, AfterValidator(identifier)]


class MeasurementSetup(FrozenModel):
    resources: ResourceManifest
    environment: dict[Text, Text] = Field(min_length=1)
    dependency_versions: dict[Text, Text] = Field(min_length=1)
    code_revision: Text = Field(pattern=r'^[0-9a-f]{40}$')
    application_source_digest: Text = Field(pattern=r'^[0-9a-f]{64}$')
    evidence_kind: Literal['empirical', 'synthetic_test_fixture']

    @property
    def fingerprint(self):
        return content_id(self.model_dump(mode='json'))


class AttemptMeasurement(FrozenModel):
    version: Literal['verifier_attempt_wall_time_v1'] = 'verifier_attempt_wall_time_v1'
    run_id: Text
    example_id: Text
    split_identity: Text
    question_id: Text
    content_identity: Text = Field(pattern=r'^[0-9a-f]{64}$')
    dataset_id: Text
    role: Literal['history', 'development']
    purpose: Literal['warmup', 'calibration']
    verifier_name: Text
    setup_fingerprint: Text
    verifier_fingerprint: Text
    duration_ms: StrictFloat = Field(ge=0)
    status: Literal['returned', 'failure', 'timeout', 'interrupted']


class MeasurementInput(FrozenModel):
    version: Literal['verifier_measurements_v1'] = 'verifier_measurements_v1'
    setup: MeasurementSetup
    permitted_datasets: tuple[tuple[Literal['history', 'development'], Text], ...] = Field(min_length=1)
    preparation_authorization: Text
    attempts: tuple[AttemptMeasurement, ...] = Field(min_length=1)

    @model_validator(mode='after')
    def check(self):
        if (len(set(self.permitted_datasets)) != len(self.permitted_datasets) or
                len({d for _, d in self.permitted_datasets}) != len(self.permitted_datasets)):
            raise ValueError('permitted datasets must be distinct with distinct roles')
        keys = set()
        groups, runs = {}, {}
        for a in self.attempts:
            key = a.run_id, a.verifier_name
            if key in keys:
                raise ValueError('duplicate verifier attempt identity')
            keys.add(key)
            identity = tuple(getattr(a, field) for field in ('example_id', 'split_identity',
                'question_id', 'content_identity', 'dataset_id', 'role', 'purpose'))
            if a.run_id in runs and runs[a.run_id] != identity:
                raise ValueError('measurement run identity differs between verifiers')
            runs[a.run_id] = identity
            if (a.role, a.dataset_id) not in self.permitted_datasets:
                raise ValueError('measurement dataset not explicitly permitted')
            if a.setup_fingerprint != self.setup.fingerprint:
                raise ValueError('incompatible environment/configuration; separate measurements')
            resource = next((v for v in self.setup.resources.verifiers if v.verifier_name == a.verifier_name), None)
            if resource is None or a.verifier_fingerprint != content_id(resource.model_dump(mode='json')):
                raise ValueError('incompatible verifier fingerprint')
            for kind in ('example_id', 'split_identity', 'question_id', 'content_identity', 'run_id'):
                identity = kind, getattr(a, kind)
                if identity in groups and groups[identity] != (a.role, a.dataset_id):
                    raise ValueError('measurement split leakage')
                groups[identity] = a.role, a.dataset_id
        return self


class CalibrationRequest(FrozenModel):
    measurements: MeasurementInput
    final_test_reservation: FinalTestReservation
    required_verifiers: tuple[Text, ...] = Field(min_length=1)
    include_warmups: StrictBool
    freeze_record: Text

    @model_validator(mode='after')
    def check(self):
        if len(set(self.required_verifiers)) != len(self.required_verifiers):
            raise ValueError('duplicate required verifier')
        if any(d == self.final_test_reservation.dataset_id for _, d in self.measurements.permitted_datasets):
            raise ValueError('final-test dataset forbidden')
        for a in self.measurements.attempts:
            for e in self.final_test_reservation.examples:
                if any(getattr(a, f) == getattr(e, f) for f in
                       ('example_id', 'split_identity', 'question_id', 'content_identity')) or a.run_id == e.validation_id:
                    raise ValueError('final-test measurement forbidden')
        return self


def estimates(request):
    """Mean includes every measured failure; p95 is nearest rank ceil(.95*n)."""
    rows, exclusions = [], []
    for name in sorted(request.required_verifiers):
        all_rows = [a for a in request.measurements.attempts if a.verifier_name == name]
        included = [a for a in all_rows if request.include_warmups or a.purpose != 'warmup']
        if not included:
            raise ValueError('missing required-verifier measurements: ' + name)
        durations = sorted(a.duration_ms for a in included)
        mean = statistics.mean(durations)
        if not math.isfinite(mean):
            raise ValueError('nonfinite estimated cost')
        rows.append(dict(verifier_name=name, attempt_cost=mean, attempts=len(included),
            failures=sum(a.status != 'returned' for a in included),
            mean_ms=mean, median_ms=statistics.median(durations),
            p95_nearest_rank_ms=durations[math.ceil(.95 * len(durations)) - 1]))
    for a in request.measurements.attempts:
        reason = ('not_required' if a.verifier_name not in request.required_verifiers else
                  'warmup_excluded' if a.purpose == 'warmup' and not request.include_warmups else None)
        if reason:
            exclusions.append(dict(run_id=a.run_id, verifier_name=a.verifier_name, reason=reason))
    return dict(estimates=rows, exclusions=exclusions)


class CalibrationArtifact(FrozenModel):
    version: Literal['verifier_cost_calibration_v1'] = 'verifier_cost_calibration_v1'
    method: Literal['mean_attempt_wall_time_ms_v1'] = 'mean_attempt_wall_time_ms_v1'
    cost_units: Literal['ms'] = 'ms'
    request: CalibrationRequest
    input_digest: Text
    result: dict
    calibration_id: Text

    @model_validator(mode='after')
    def check(self):
        result = estimates(self.request)
        digest = content_id(self.request.model_dump(mode='json'))
        if self.input_digest != digest or self.result != result:
            raise ValueError('calibration input/result digest mismatch')
        if self.calibration_id != content_id([self.version, self.method, self.cost_units, digest, result]):
            raise ValueError('calibration identity mismatch')
        return self


def calibrate(request):
    request = CalibrationRequest.model_validate(request)
    result = estimates(request)
    digest = content_id(request.model_dump(mode='json'))
    return CalibrationArtifact(request=request, input_digest=digest, result=result,
        calibration_id=content_id(['verifier_cost_calibration_v1', 'mean_attempt_wall_time_ms_v1', 'ms', digest, result]))


def apply_calibration(context, artifact, *, manifest, contract, recording,
                      budget_ms, resource_weight_per_ms, expected_setup_fingerprint):
    """Return a new context; preserve custody checks and require explicit ms settings."""
    artifact = CalibrationArtifact.model_validate(artifact)
    context = PlanningContext.model_validate(context)
    setup = artifact.request.measurements.setup
    if expected_setup_fingerprint != setup.fingerprint:
        raise ValueError('calibration environment/configuration setup fingerprint mismatch')
    names = {c.verifier_name for c in context.plan.candidates}
    if set(artifact.request.required_verifiers) != names:
        raise ValueError('calibration must cover every captured candidate exactly')
    if (contract.resource_manifest != setup.resources or
            recording.execution_configuration_id != setup.resources.manifest_id or
            setup.evidence_kind != manifest.evidence_kind):
        raise ValueError('calibration configuration/evidence mismatch')
    # Check split keys against preparation records, never final outcomes. Reservation
    # keys are checked independently to catch mislabeled held-out measurements.
    reserved = manifest.final_test_reservation
    if reserved != artifact.request.final_test_reservation:
        raise ValueError('calibration final-test reservation mismatch')
    for a in artifact.request.measurements.attempts:
        for e in reserved.examples:
            if any(getattr(a, f) == getattr(e, f) for f in
                   ('example_id', 'split_identity', 'question_id', 'content_identity')) or a.run_id == e.validation_id:
                raise ValueError('final-test measurement forbidden')
        part = manifest.partition(a.role)
        example = next((e for e in part.examples if e.example_id == a.example_id), None)
        if (part.dataset_id != a.dataset_id or example is None or any(
                getattr(a, f) != getattr(example, f) for f in
                ('split_identity', 'question_id', 'content_identity'))):
            raise ValueError('measurement preparation provenance mismatch')
    if context.offline_evaluation_id is not None or context.pooling_contract_json is not None:
        raise ValueError('calibrate a fresh unbound context before evaluation/pooling')
    loss = {**context.loss_configuration.model_dump(), 'cost_units': 'ms',
            'resource_weight': resource_weight_per_ms}
    return PlanningContext(**{**context.model_dump(), 'attempt_costs': tuple(
        (r['verifier_name'], r['attempt_cost']) for r in artifact.result['estimates']),
        'budget': budget_ms, 'cost_units': 'ms', 'loss_configuration': loss})


def read_json(path):
    from app.game.research.__main__ import _object, _nonfinite
    return json.loads(Path(path).read_text(encoding='utf-8'), object_pairs_hook=_object, parse_constant=_nonfinite)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('request', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--measurements', type=Path, help='Supply collected bundle separately from approved settings')
    args = parser.parse_args(argv)
    try:
        payload = read_json(args.request)
        if args.measurements:
            if payload.get('measurements') is not None:
                raise ValueError('measurements supplied twice')
            payload['measurements'] = read_json(args.measurements)
        artifact = calibrate(payload)
        with args.output.open('x', encoding='utf-8') as handle:
            handle.write(artifact.model_dump_json(indent=2))
    except (ValueError, OSError) as exc:
        print(json.dumps(dict(status='blocked', missing_inputs=str(exc), artifact_created=False)))
        return 2
    print(artifact.calibration_id)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
