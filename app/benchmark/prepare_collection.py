"""Prepare label-free collection requests from custodian-approved preparation data."""
import argparse
import json
from pathlib import Path
from typing import Literal

from pydantic import Field, model_validator

from app.benchmark.collect_costs import CollectionExample, CollectionRequest, validate_preparation
from app.benchmark.project_adapter import AdapterConfiguration, FACTORY, inspect_setup, error_reason
from app.game.dependencies import FrozenModel
from app.game.offline.calibration import MeasurementSetup, Text, read_json
from app.game.offline.records import FinalTestReservation


class PreparationInput(FrozenModel):
    version: Literal['approved_collection_preparation_v1'] = 'approved_collection_preparation_v1'
    final_test_reservation: FinalTestReservation
    permitted_datasets: tuple[tuple[Literal['history', 'development'], Text], ...] = Field(min_length=1)
    preparation_authorization: Text
    examples: tuple[CollectionExample, ...] = Field(min_length=1)

    @model_validator(mode='after')
    def check(self):
        return validate_preparation(self)


def attempt_counts(preparation, n_samples):
    from app.verifiers.confidence_verifier import parse_judgment_list
    preparation = PreparationInput.model_validate(preparation)
    warmup = sum(e.purpose == 'warmup' for e in preparation.examples)
    calls = sum(parse_judgment_list(e.context) is None for e in preparation.examples) * n_samples
    return dict(example_runs=len(preparation.examples), unique_examples=len({
        (e.role, e.dataset_id, e.example_id) for e in preparation.examples}),
        warmup_runs=warmup, calibration_runs=len(preparation.examples)-warmup,
        intended_attempts=4*len(preparation.examples), warmup_attempts=4*warmup,
        calibration_attempts=4*(len(preparation.examples)-warmup),
        intended_generation_requests_if_all_reached=calls,
        generation_request_range=[0, calls],
        explanation='N requests per confidence call unless context is explicit judgment labels; failures stop collection, provider failures can stop sampling early')


def prepare(configuration, preparation):
    preparation = PreparationInput.model_validate(preparation)
    report = inspect_setup(configuration)
    if not report['ready']:
        raise ValueError('resource preflight blocked: ' + json.dumps(report['blockers']))
    return CollectionRequest(setup=MeasurementSetup.model_validate(report['observed_setup']),
        final_test_reservation=preparation.final_test_reservation,
        permitted_datasets=preparation.permitted_datasets,
        preparation_authorization=preparation.preparation_authorization,
        factory=FACTORY, examples=preparation.examples)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('configuration', type=Path)
    parser.add_argument('preparation', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        request = prepare(AdapterConfiguration.model_validate(read_json(args.configuration)), read_json(args.preparation))
        with args.output.open('x', encoding='utf-8') as handle:
            handle.write(request.model_dump_json(indent=2))
    except (ValueError, OSError) as exc:
        print(json.dumps(dict(ready=False, blocker=error_reason(exc))))
        return 2
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
