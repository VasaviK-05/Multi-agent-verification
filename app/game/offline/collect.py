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
                ledger=args.resume_from/'started.jsonl'
                if not ledger.exists():raise ValueError('no start ledger: cannot safely infer unattempted work')
                started={json.loads(line)['attempt_id'] for line in ledger.read_text(encoding='utf-8').splitlines() if line.strip()}
                recorded={a.attempt_id for a in prior.attempts if a.executed}
                if started-recorded:raise ValueError('in-flight attempt lacks completion; do not retry: '+str(sorted(started-recorded)))
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
            if prior is not None:
                from app.game.offline.calibration import MeasurementSetup
                if setup is None or prior.observed_setup!=MeasurementSetup.model_validate(setup):
                    raise ValueError('resume resource/setup fingerprint changed')
            observer = loaded[2] if len(loaded) == 3 else None
            (destination / 'observed-setup.json').write_text(
                'null' if setup is None else json.dumps(setup.model_dump(mode='json')
                    if hasattr(setup, 'model_dump') else setup, indent=2), encoding='utf-8')
            with (destination / 'attempts.jsonl').open('x', encoding='utf-8') as journal, (destination/'started.jsonl').open('x',encoding='utf-8') as starts:
                import os
                if prior is not None:
                    (destination/'resume-provenance.json').write_text(json.dumps(dict(prior_path=str(args.resume_from),prior_bundle_id=prior.bundle_id)),encoding='utf-8')
                    for a in prior.attempts:
                        if a.executed:starts.write(json.dumps(dict(attempt_id=a.attempt_id))+'\n')
                    starts.flush();os.fsync(starts.fileno())
                def begin(identity):
                    starts.write(json.dumps(dict(attempt_id=identity))+'\n');starts.flush();os.fsync(starts.fileno())
                def save(row):
                    journal.write(row.model_dump_json() + '\n')
                    journal.flush()
                bundle = collect(request, list(verifiers), setup, observer, sink=save,
                    completed=() if prior is None else prior.attempts,on_start=begin)
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
