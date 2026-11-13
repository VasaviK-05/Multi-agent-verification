"""Validate, collect, recover/check and export offline verifier recordings."""
import argparse
import importlib
import json
from pathlib import Path

from pydantic import ValidationError

from app.game.offline.file_journal import (AttemptJournal, atomic_write_text,
    create_run_directory, read_jsonl, recovery_state)

from app.game.models import PlanningContext
from app.game.offline.calibration import read_json
from app.game.offline.collection import (RecordingRequest, RecordingBundle, CollectedAttempt,
    collect, completeness, measurement_input, export_training, validate_recording_request)


def load_bundle(path):
    path = Path(path)
    if path.is_file():
        return RecordingBundle.model_validate(read_json(path))
    # Recover from the flushed journal, including interrupted collection. No
    # factory, verifier, final payload, or database is accessed during checking.
    request = validate_recording_request(read_json(path / 'request.json'))
    setup = read_json(path / 'observed-setup.json') if (path / 'observed-setup.json').exists() else None
    rows = []
    journal = path / 'attempts.jsonl'
    if journal.exists():
        for row in read_jsonl(journal):
            rows.append(CollectedAttempt.model_validate(row))
    return RecordingBundle(request=request, observed_setup=setup, attempts=tuple(rows))


def validate_factory_prerequisites(request):
    """Known eager adapters must fail before loading a prerequisite-less Semantic.

    This is a factory limitation, not an Evidence eligibility rule. Other factories
    retain their existing zero-argument API and construction responsibilities.
    """
    if request.factory not in {
        'app.game.offline.recording_adapters:project_factory',
        'app.game.offline.recording_adapters:arithmetic_factory',
    }:return
    from app.selection.capabilities import BUILTIN_CAPABILITIES,prerequisite_status
    missing=[e.example_id for e in request.examples
        if prerequisite_status(BUILTIN_CAPABILITIES['semantic'],e.reference)[1] is not None]
    if missing:
        raise ValueError('eager reference-assisted factory cannot omit Semantic before construction; '
            'use a prerequisite-aware partial-roster factory. Evidence does not require user reference. '
            'Unavailable reference examples: '+', '.join(missing))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('validate', 'collect', 'check', 'export'))
    parser.add_argument('input', type=Path)
    parser.add_argument('--output-dir', type=Path)
    parser.add_argument('--context', type=Path)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--resume-from',type=Path,help='Prior journal; preserve it and use a fresh output directory')
    args = parser.parse_args(argv)
    destination = None
    try:
        if args.command in {'validate', 'collect'}:
            request = validate_recording_request(read_json(args.input))
            validate_factory_prerequisites(request)
            prior=None
            if args.resume_from is not None:
                prior=load_bundle(args.resume_from)
                if prior.request!=request:raise ValueError('resume request identity changed')
                recovery_state(args.resume_from)
            if args.command == 'validate':
                print(json.dumps(dict(valid=True, request_id=request.request_id,
                    intended_use=request.intended_use, examples=len(request.examples),
                    candidate_outcomes=len(request.examples)*len(request.candidates),
                    factory_initialized=False)))
                return 0
            if args.output_dir is None:
                raise ValueError('collect requires --output-dir (new directory)')
            create_run_directory(args.output_dir)
            destination = args.output_dir
            atomic_write_text(destination / 'request.json', request.model_dump_json(indent=2), replace=False)
            module, separator, function = request.factory.partition(':')
            if not separator or not module or not function:
                raise ValueError('factory must be module:function')
            loaded = getattr(importlib.import_module(module), function)()
            if len(loaded) not in {2, 3}:
                raise ValueError('factory returns (verifiers, observed_setup[, resource_observer])')
            verifiers, setup = loaded[:2]
            if prior is not None:
                from app.game.offline.calibration import MeasurementSetup
                if setup is None or prior.observed_setup!=MeasurementSetup.model_validate(setup):
                    raise ValueError('resume resource/setup fingerprint changed')
            observer = loaded[2] if len(loaded) == 3 else None
            atomic_write_text(destination / 'observed-setup.json',
                'null' if setup is None else json.dumps(setup.model_dump(mode='json')
                    if hasattr(setup, 'model_dump') else setup, indent=2), replace=False)
            with AttemptJournal(destination) as journal:
                if prior is not None:
                    atomic_write_text(destination / 'resume-provenance.json', json.dumps(dict(
                        prior_path=str(args.resume_from), prior_bundle_id=prior.bundle_id)), replace=False)
                    retained = [row for row in prior.attempts
                                if row.executed or row.attempt.state != 'missing']
                    for row in retained:
                        if row.executed:
                            journal.start(row.attempt_id)
                        journal.terminal(row.model_dump_json())
                copied = set() if prior is None else {row.attempt_id for row in retained}
                def save(row):
                    if row.attempt_id not in copied:
                        journal.terminal(row.model_dump_json())
                bundle = collect(request, list(verifiers), setup, observer, sink=save,
                    completed=() if prior is None else prior.attempts, on_start=journal.start)
            atomic_write_text(destination / 'recordings.json', bundle.model_dump_json(indent=2), replace=False)
            report = completeness(bundle)
            report['request_id'], report['bundle_id'] = request.request_id, bundle.bundle_id
            try:
                measurements = measurement_input(bundle)
            except ValueError as exc:
                report['measurement_export_blocker'] = str(exc)
            else:
                atomic_write_text(destination / 'measurements.json', measurements.model_dump_json(indent=2), replace=False)
            atomic_write_text(destination / 'collection-report.json', json.dumps(report, indent=2))
        elif args.command == 'check':
            report = completeness(load_bundle(args.input))
        else:
            if args.context is None or args.output is None:
                raise ValueError('export requires --context and --output')
            bundle = load_bundle(args.input)
            manifest = export_training(bundle, PlanningContext.model_validate(read_json(args.context)))
            atomic_write_text(args.output, manifest.model_dump_json(indent=2), replace=False)
            report = dict(complete=True, manifest_id=manifest.manifest_id,
                evidence_kind=manifest.evidence_kind, output=str(args.output), policy_created=False)
        print(json.dumps(report, indent=2))
        return 0 if report['complete'] else 2
    except (Exception, KeyboardInterrupt) as exc:
        report = dict(complete=False, error_type=type(exc).__name__, message=str(exc),
                      policy_created=False, recordings_preserved_in=None if destination is None else str(destination))
        if isinstance(exc, ValidationError):
            report['input_errors'] = exc.errors(include_url=False, include_input=False, include_context=False)
        if destination is not None:
            atomic_write_text(destination / 'collection-report.json', json.dumps(report, indent=2))
        print(json.dumps(report, indent=2))
        return 130 if isinstance(exc, KeyboardInterrupt) else 2


if __name__ == '__main__':
    raise SystemExit(main())
