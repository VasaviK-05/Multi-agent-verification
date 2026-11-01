"""External seven-case Evidence rehearsal for a restored collector checkout.

Run with that checkout's Python. This file stays OUTSIDE its app/ tree. The default
operation is seven software probes. Optional bounded collection forwards to the
existing collector CLI/journals, never a new collector. Both require new authority.
No fitting, calibration, artifact export or activation is provided.
Strict mode requires the historical setup. An explicit evaluation-transfer
declaration instead requires its identified current setup, without equivalence.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import runpy
import subprocess
import sys


def probe_payload(nli, resource, verifier_class, helpers):
    """Same fixed cases as factual_policy42.evidence_probes, plain interchange JSON.

    Plain JSON avoids requiring the newer proof schema inside the historical app.
    The new evaluator must validate this against EvidenceValidation afterwards.
    """
    retriever, fake_nli, chunk = (helpers[k] for k in ('FakeRetriever', 'FakeNLI', 'chunk'))
    probes = []
    for case, probabilities in [('controlled_support', helpers['ENTAILS']),
                                ('controlled_rejection', helpers['CONTRADICTS']),
                                ('controlled_neutral', helpers['NEUTRAL'])]:
        report = verifier_class(retriever=retriever([chunk('Hamlet', 'Shakespeare wrote Hamlet.', .9)]),
            nli=fake_nli({'Shakespeare': probabilities})).verify('Who wrote Hamlet?', 'Shakespeare')
        probes.append(dict(case_id=case, report_json=report.model_dump_json()))
    report = verifier_class(retriever=retriever([chunk('Support', 'Shakespeare wrote Hamlet.', .9),
        chunk('Reject', 'Marlowe wrote Hamlet.', .9, 1)]),
        nli=fake_nli({'Shakespeare': helpers['ENTAILS'], 'Marlowe': helpers['CONTRADICTS']})).verify('Who wrote Hamlet?', 'Shakespeare')
    probes.append(dict(case_id='controlled_conflict', report_json=report.model_dump_json()))
    for case, answer, text in [('real_nli_support', 'Shakespeare', 'Shakespeare wrote Hamlet.'),
                               ('real_nli_rejection', 'Charles Dickens', 'Shakespeare wrote Hamlet.'),
                               ('real_nli_neutral', 'Shakespeare', 'Hamlet is a play.')]:
        report = verifier_class(retriever=retriever([chunk('Hamlet', text, .9)]), nli=nli).verify('Who wrote Hamlet?', answer)
        probes.append(dict(case_id=case, report_json=report.model_dump_json()))
    return dict(version='evidence_public_contract_validation_v2', before=resource, after=resource, probes=probes)


def bounded_collect(original, maximum, counter):
    """Stop before recording/starting the next call, using the public callback."""
    def collect(*args, on_start=None, **kwargs):
        def begin(attempt_id):
            if maximum is not None and counter['started'] >= maximum:
                counter['planned_stop'] = True
                raise KeyboardInterrupt('authorized rehearsal boundary before new attempt')
            if on_start is not None: on_start(attempt_id)
            counter['started'] += 1
        return original(*args, on_start=begin, **kwargs)
    return collect


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--collector-root', required=True, type=Path)
    parser.add_argument('--clean-bundle', required=True, type=Path)
    parser.add_argument('--adapter-config', required=True, type=Path)
    parser.add_argument('--source-audit', required=True, type=Path)
    parser.add_argument('--output-dir', required=True, type=Path)
    parser.add_argument('--authorization-record', required=True)
    parser.add_argument('--evaluation-transfer', type=Path,
                        help='Explicit frozen_policy_evaluation_transfer_v1 declaration; never a strict-mode bypass')
    parser.add_argument('--operation', choices=('evidence-probes', 'collect'), default='evidence-probes')
    parser.add_argument('--request', type=Path)
    parser.add_argument('--resume-from', type=Path)
    parser.add_argument('--stop-after', type=int)
    parser.add_argument('--generation-limit', type=int)
    parser.add_argument('--metadata-limit', type=int, default=30)
    args = parser.parse_args(argv)
    output = args.output_dir.resolve()
    adapter = args.adapter_config.resolve()
    self_path = Path(__file__).resolve()
    request_path = None if args.request is None else args.request.resolve()
    resume = None if args.resume_from is None else args.resume_from.resolve()
    audit_output = output if args.operation == 'evidence-probes' else output.with_name(output.name+'-runner-audit')
    destination_created = False
    try:
        if not args.authorization_record.strip(): raise ValueError('nonblank new probe authorization required')
        if args.metadata_limit < 0 or (args.generation_limit is not None and args.generation_limit < 0):
            raise ValueError('network ceilings must be nonnegative')
        if args.stop_after is not None and args.stop_after < 1: raise ValueError('stop-after must be positive')
        if args.operation == 'collect' and (request_path is None or args.generation_limit is None):
            raise ValueError('collect requires an unchanged full request and explicit generation limit')
        if args.operation == 'evidence-probes' and (args.request is not None or args.resume_from is not None
                or args.stop_after is not None or args.generation_limit not in (None, 0)):
            raise ValueError('evidence probes cannot collect study records or authorize generation')
        root = args.collector_root.resolve()
        historical_document = json.loads(args.clean_bundle.read_text(encoding='utf-8'))
        clean = historical_document['observed_setup']
        transfer_payload = None
        if args.evaluation_transfer is not None:
            transfer_payload = json.loads(args.evaluation_transfer.read_text(encoding='utf-8'))
            if transfer_payload.get('version') != 'frozen_policy_evaluation_transfer_v1':
                raise ValueError('unsupported evaluation-transfer contract')
            clean = transfer_payload['current_clean_setup']
        audit = json.loads(args.source_audit.read_text(encoding='utf-8'))
        if not audit.get('source_compatible'): raise ValueError('source audit is blocked; do not initialize models')
        if (transfer_payload is None) != (audit.get('version') != 'frozen_transfer_collector_source_audit_v1'):
            raise ValueError('strict and transfer source-audit modes cannot be mixed')
        if any(os.environ.get(k) for k in ('GIT_DIR', 'GIT_WORK_TREE', 'GIT_INDEX_FILE')):
            raise ValueError('unset Git source overrides')
        revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()
        rows = [(p.relative_to(root).as_posix(), hashlib.sha256(p.read_bytes()).hexdigest())
                for p in sorted((root/'app').rglob('*.py'))]
        digest = hashlib.sha256(json.dumps(rows, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
        if (revision != clean['code_revision'] or digest != clean['application_source_digest']
                or digest != audit.get('actual_application_source_digest')):
            raise ValueError('collector source no longer matches the explicitly required setup/source audit')
        os.chdir(root); sys.path.insert(0, str(root))
        import app
        if Path(app.__file__).resolve().parent != root/'app':
            raise ValueError('wrong app imported; use a fresh original-environment Python process')
        transfer_id = None
        if transfer_payload is not None:
            from app.game.offline.upstream_transfer import EvaluationTransferDeclaration
            from app.game.offline.collection import RecordingBundle
            from app.game.offline.upstream import scientific_bundle_id
            declaration = EvaluationTransferDeclaration.model_validate(transfer_payload)
            historical = RecordingBundle.model_validate(historical_document)
            if (declaration.historical_recording_id != scientific_bundle_id(historical)
                    or declaration.historical_setup_fingerprint != historical.observed_setup.fingerprint):
                raise ValueError('transfer historical provenance differs from the actual retained bundle')
            transfer_id = declaration.declaration_id
            if audit.get('transfer_declaration_id') != transfer_id:
                raise ValueError('transfer audit/declaration identity mismatch')
        os.environ.update(HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', HF_HUB_DISABLE_TELEMETRY='1',
                          VERIFIER_COLLECTION_ADAPTER_CONFIG=str(adapter))
        # External helpers are versioned/audited separately; never copy them into app/.
        external = self_path.parents[1]
        network_path = external/'scripts/run_factual_diagnostic.py'
        helper_path = external/'tests/test_evidence_verifier.py'
        budget_class = runpy.run_path(str(network_path), run_name='external_network_budget')['NetworkBudget']
        helpers = (runpy.run_path(str(helper_path), run_name='external_controlled_evidence_fixtures')
                   if args.operation == 'evidence-probes' else None)
        from app.game.offline.recording_adapters import project_factory
        from app.verifiers.evidence_verifier import EvidenceVerifier
        from app.benchmark.project_adapter import AdapterConfiguration, inspect_setup
        import requests
        config = AdapterConfiguration.model_validate(json.loads(
            Path(os.environ['VERIFIER_COLLECTION_ADAPTER_CONFIG']).read_text(encoding='utf-8'))).model_dump(mode='json')
        if output.exists(): raise ValueError('output must be a new directory')
        audit_output.mkdir(parents=True, exist_ok=False); destination_created = True
        (audit_output/'authorization.json').write_text(json.dumps(dict(record=args.authorization_record, operation=args.operation,
            evaluation_mode='strict_historical' if transfer_id is None else 'frozen_rule_transfer', transfer_declaration_id=transfer_id,
            scope=('seven fixed software cases; three local NLI calls; no study candidates/generation'
                   if args.operation == 'evidence-probes' else 'existing full-request collector; retained failures; no fitting'),
            external_sources={p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in
                              (self_path, network_path, helper_path)}), indent=2), encoding='utf-8')
        with (audit_output/'network.jsonl').open('x', encoding='utf-8') as journal:
            budget = budget_class(config['ollama_url'], journal, generation_limit=args.generation_limit or 0,
                                  metadata_limit=args.metadata_limit)
            original = requests.Session.request
            requests.Session.request = lambda session, method, url, *a, **k: budget.call(original, session, method, url, *a, **k)
            try:
                preflight = inspect_setup(AdapterConfiguration.model_validate(config))
                if not preflight['ready']: raise ValueError('original-environment resource preflight is blocked')
                for field in ('code_revision', 'application_source_digest', 'dependency_versions', 'environment', 'evidence_kind'):
                    if preflight['observed_setup'][field] != clean[field]:
                        raise ValueError('approved collector preflight mismatch: '+field)
                if args.operation == 'collect':
                    request = json.loads(request_path.read_text(encoding='utf-8'))
                    if request['expected_setup'] != preflight['observed_setup']:
                        raise ValueError('request differs from actual original-environment preflight')
                    if transfer_payload is not None:
                        from app.game.offline.collection import RecordingRequest
                        from app.game.offline.upstream_transfer import validate_collection_scope
                        checked_request = RecordingRequest.model_validate(request)
                        validate_collection_scope(historical, checked_request)
                        if (checked_request.expected_setup.resources == declaration.current_clean_setup.resources
                                and checked_request.request_id != declaration.current_clean_request_id):
                            raise ValueError('clean collection request differs from transfer declaration')
                    import app.game.offline.collect as cli
                    import inspect
                    if 'on_start' not in inspect.signature(cli.collect).parameters:
                        raise ValueError('restored collector lacks public durable on_start support')
                    original_collect = cli.collect
                    counter = dict(started=0, planned_stop=False)
                    cli.collect = bounded_collect(original_collect, args.stop_after, counter)
                    try:
                        arguments = ['collect', str(request_path), '--output-dir', str(output)]
                        if resume is not None: arguments += ['--resume-from', str(resume)]
                        status = cli.main(arguments)
                    finally:
                        cli.collect = original_collect
                    (audit_output/'scope.json').write_text(json.dumps(dict(network_counts=budget.counts,
                        limits=budget.limits, **counter, collector_exit_status=status,
                        source_digest=digest, request_unchanged=True), indent=2), encoding='utf-8')
                    return status
                pool, setup, observer = project_factory()
                actual = setup.model_dump(mode='json')
                if actual != preflight['observed_setup']: raise ValueError('factory setup changed after preflight')
                for field in ('code_revision', 'application_source_digest', 'dependency_versions', 'environment', 'evidence_kind'):
                    if actual[field] != clean[field]: raise ValueError('original collector setup mismatch: '+field)
                before = observer.snapshot()
                if before != setup.resources: raise ValueError('factory resource observation changed')
                resource = next(v for v in before.verifiers if v.verifier_name == 'evidence')
                evidence = next(v for v in pool if v.name == 'evidence')
                payload = probe_payload(evidence.nli, resource.model_dump(mode='json'), EvidenceVerifier, helpers)
                after = observer.snapshot()
                if after != before: raise ValueError('resources changed during software probes')
            finally:
                requests.Session.request = original
        (output/'evidence-validation.json').write_text(json.dumps(payload, indent=2), encoding='utf-8')
        (output/'scope.json').write_text(json.dumps(dict(observed_setup=actual, network_counts=budget.counts,
            study_candidates=0, used_in_calibration=False, schema_validation_required_in_evaluator=True), indent=2), encoding='utf-8')
        print(json.dumps(dict(produced=True, schema_validation_required_in_evaluator=True, study_candidates=0)))
        return 0
    except (Exception, KeyboardInterrupt) as exc:
        report = dict(blocked=True, error_type=type(exc).__name__, message=str(exc), new_policy_created=False)
        if destination_created: (audit_output/'probe-error.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
        print(json.dumps(report)); return 2


if __name__ == '__main__':
    raise SystemExit(main())
