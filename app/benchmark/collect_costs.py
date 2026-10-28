"""Opt-in, label-free measurement collection. Factory owns verifier setup/resources."""
import argparse
import importlib
from pathlib import Path
from typing import Literal

from pydantic import Field, model_validator

from app.game.dependencies import FrozenModel
from app.game.models import content_id
from app.game.offline.calibration import (Text, MeasurementSetup, MeasurementInput,
    AttemptMeasurement, read_json)
from app.game.offline.records import FinalTestReservation


class CollectionExample(FrozenModel):
    example_id: Text
    split_identity: Text
    question_id: Text
    run_id: Text
    dataset_id: Text
    role: Literal['history', 'development']
    purpose: Literal['warmup', 'calibration']
    question: Text
    answer: str
    context: str | None


def validate_preparation(preparation):
    """Shared label-free custody gate, usable before resource setup is available."""
    examples = preparation.examples
    permitted = preparation.permitted_datasets
    reservation = preparation.final_test_reservation
    if len({e.run_id for e in examples}) != len(examples):
        raise ValueError('collection run IDs must be unique')
    if any((e.role, e.dataset_id) not in permitted for e in examples):
        raise ValueError('collection dataset not permitted')
    if len({d for _, d in permitted}) != len(permitted):
        raise ValueError('collection dataset identities must be distinct')
    identities, groups, runs = {}, {}, {}
    for e in examples:
        digest = content_id([e.question, e.answer, e.context])
        if e.dataset_id == reservation.dataset_id:
            raise ValueError('final-test collection forbidden')
        for reserved in reservation.examples:
            if (any(getattr(e, f) == getattr(reserved, f) for f in
                    ('example_id', 'split_identity', 'question_id')) or
                    digest == reserved.content_identity or e.run_id == reserved.validation_id):
                raise ValueError('final-test collection forbidden')
        for kind, value in (('example', e.example_id), ('split', e.split_identity),
                            ('question', e.question_id), ('content', digest)):
            if (kind, value) in identities and identities[kind, value] != (e.role, e.dataset_id):
                raise ValueError('collection split leakage')
            identities[kind, value] = e.role, e.dataset_id
            if kind in {'question', 'content', 'example'}:
                if (kind, value) in groups and groups[kind, value] != e.split_identity:
                    raise ValueError('related question/content/example must share one split identity')
                groups[kind, value] = e.split_identity
        identity = e.role, e.dataset_id, e.example_id
        content = e.question_id, digest, e.split_identity
        if identity in runs and runs[identity] != content:
            raise ValueError('repeated example identity has inconsistent content')
        runs[identity] = content
    return preparation


class CollectionRequest(FrozenModel):
    setup: MeasurementSetup
    final_test_reservation: FinalTestReservation
    permitted_datasets: tuple[tuple[Literal['history', 'development'], Text], ...] = Field(min_length=1)
    preparation_authorization: Text
    factory: Text  # module:function returning (verifiers, observed MeasurementSetup)
    examples: tuple[CollectionExample, ...] = Field(min_length=1)

    @model_validator(mode='after')
    def check(self):
        return validate_preparation(self)


def collect(request, verifiers, observed_setup, attempts):
    """Record attempts in caller-owned list even if verify raises; never retry."""
    from app.game.offline.timing import TimedVerifier
    request = CollectionRequest.model_validate(request)
    observed_setup = MeasurementSetup.model_validate(observed_setup)
    if observed_setup != request.setup:
        raise ValueError('observed setup differs from approved collection setup')
    pool = list(verifiers)
    request.setup.resources.require_candidates(v.name for v in pool)
    if len({v.name for v in pool}) != len(pool):
        raise ValueError('duplicate verifier identity')
    for example in request.examples:
        for verifier in pool:
            resource = next(r for r in request.setup.resources.verifiers if r.verifier_name == verifier.name)
            metadata = {k: getattr(example, k) for k in ('run_id', 'example_id', 'split_identity',
                'question_id', 'dataset_id', 'role', 'purpose')}
            metadata.update(content_identity=content_id([example.question, example.answer, example.context]),
                setup_fingerprint=request.setup.fingerprint,
                verifier_fingerprint=content_id(resource.model_dump(mode='json')))
            TimedVerifier(verifier, [], measurement_metadata=metadata, measurements=attempts).verify(
                example.question, example.answer, example.context)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('request', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    request = CollectionRequest.model_validate(read_json(args.request))
    # Reserve a fresh output before initializing potentially expensive models.
    with args.output.open('x', encoding='utf-8') as handle:
        module, function = request.factory.split(':')
        verifiers, observed_setup = getattr(importlib.import_module(module), function)()
        attempts = []
        try:
            collect(request, verifiers, observed_setup, attempts)
        finally:
            # A failure propagates after preserving all attempts so far; later
            # verifiers have no rows and cannot be mistaken for failed attempts.
            if attempts:
                bundle = MeasurementInput(setup=request.setup, permitted_datasets=request.permitted_datasets,
                    preparation_authorization=request.preparation_authorization,
                    attempts=tuple(AttemptMeasurement.model_validate(a) for a in attempts))
                handle.write(bundle.model_dump_json(indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
