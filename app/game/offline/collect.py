"""Validate, collect, recover/check and export offline verifier recordings."""
import argparse
import importlib
import json
from pathlib import Path

from pydantic import ValidationError

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
        for line in journal.read_text(encoding='utf-8').splitlines():
            if line.strip():
                rows.append(CollectedAttempt.model_validate_json(line))
    return RecordingBundle(request=request, observed_setup=setup, attempts=tuple(rows))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('validate', 'collect', 'check', 'export'))
    parser.add_argument('input', type=Path)
    parser.add_argument('--output-dir', type=Path)
    parser.add_argument('--context', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args(argv)
    destination = None
    try:
        if args.command in {'validate', 'collect'}:
            request = validate_recording_request(read_json(args.input))
            if args.command == 'validate':
                print(json.dumps(dict(valid=True, request_id=request.request_id,
                    intended_use=request.intended_use, examples=len(request.examples),
                    candidate_outcomes=len(request.examples)*len(request.candidates),
                    factory_initialized=False)))
                return 0
            if args.output_dir is None:
                raise ValueError('collect requires --output-dir (new directory)')
            args.output_dir.mkdir(parents=True, exist_ok=False)
            destination = args.output_dir
            (destination / 'request.json').write_text(request.model_dump_json(indent=2), encoding='utf-8')
            module, separator, function = request.factory.partition(':')
            if not separator or not module or not function:
                raise ValueError('factory must be module:function')
            loaded = getattr(importlib.import_module(module), function)()
            if len(loaded) not in {2, 3}:
                raise ValueError('factory returns (verifiers, observed_setup[, resource_observer])')
            verifiers, setup = loaded[:2]
            observer = loaded[2] if len(loaded) == 3 else None
            (destination / 'observed-setup.json').write_text(
                'null' if setup is None else json.dumps(setup.model_dump(mode='json')
                    if hasattr(setup, 'model_dump') else setup, indent=2), encoding='utf-8')
            with (destination / 'attempts.jsonl').open('x', encoding='utf-8') as journal:
                def save(row):
                    journal.write(row.model_dump_json() + '\n')
                    journal.flush()
                bundle = collect(request, list(verifiers), setup, observer, sink=save)
            (destination / 'recordings.json').write_text(bundle.model_dump_json(indent=2), encoding='utf-8')
            report = completeness(bundle)
            report['request_id'], report['bundle_id'] = request.request_id, bundle.bundle_id
            try:
                measurements = measurement_input(bundle)
            except ValueError as exc:
                report['measurement_export_blocker'] = str(exc)
            else:
                (destination / 'measurements.json').write_text(measurements.model_dump_json(indent=2), encoding='utf-8')
            (destination / 'collection-report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
        elif args.command == 'check':
            report = completeness(load_bundle(args.input))
        else:
            if args.context is None or args.output is None:
                raise ValueError('export requires --context and --output')
            bundle = load_bundle(args.input)
            manifest = export_training(bundle, PlanningContext.model_validate(read_json(args.context)))
            with args.output.open('x', encoding='utf-8') as handle:
                handle.write(manifest.model_dump_json(indent=2))
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
            (destination / 'collection-report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
        print(json.dumps(report, indent=2))
        return 130 if isinstance(exc, KeyboardInterrupt) else 2


if __name__ == '__main__':
    raise SystemExit(main())
