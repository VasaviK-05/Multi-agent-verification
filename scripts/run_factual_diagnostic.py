"""One authorized factual diagnostic pass through the existing recording CLI."""
import argparse
from contextlib import redirect_stdout, redirect_stderr
from dataclasses import asdict
import json
import os
from pathlib import Path
from urllib.parse import urlsplit


class NetworkBudget:
    """Transparent request audit with hard local-only generation/metadata ceilings."""
    def __init__(self, generate_url, handle):
        target = urlsplit(generate_url)
        if (target.scheme not in {'http', 'https'} or target.hostname not in {'localhost', '127.0.0.1', '::1'}
                or target.username or target.password or target.query or target.fragment or target.path != '/api/generate'):
            raise ValueError('diagnostic endpoint must be a credential-free loopback /api/generate URL')
        self.generate_url = generate_url
        self.base = generate_url.rsplit('/api/generate', 1)[0]
        self.handle = handle
        self.counts = {'generation': 0, 'metadata': 0, 'blocked': 0}

    def call(self, original, session, method, url, *args, **kwargs):
        method = method.upper()
        kind = ('generation' if method == 'POST' and url == self.generate_url else
                'metadata' if method == 'GET' and url in {self.base+'/api/version', self.base+'/api/tags'} else None)
        limit = 30 if kind == 'generation' else 100
        if kind is None or self.counts[kind] >= limit:
            self.counts['blocked'] += 1
            self.handle.write(json.dumps(dict(state='blocked', method=method, path=urlsplit(url).path))+'\n')
            self.handle.flush()
            raise RuntimeError('diagnostic network authorization limit or endpoint violation')
        self.counts[kind] += 1
        event = dict(kind=kind, ordinal=self.counts[kind], method=method, path=urlsplit(url).path)
        self.handle.write(json.dumps(dict(**event, state='started'))+'\n')
        self.handle.flush()
        try:
            kwargs['allow_redirects'] = False  # Never let an allowed loopback call redirect outside its budget.
            response = original(session, method, url, *args, **kwargs)
        except BaseException as exc:
            self.handle.write(json.dumps(dict(**event, state='raised', error_type=type(exc).__name__))+'\n')
            raise
        else:
            self.handle.write(json.dumps(dict(**event, state='returned', status_code=response.status_code))+'\n')
            return response
        finally:
            self.handle.flush()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--study-dir', type=Path, required=True)
    parser.add_argument('--authorization-record', required=True, help='Reference to new explicit execution permission; historical approval is not replayable')
    args = parser.parse_args(argv)
    if not args.authorization_record.strip():
        parser.error('nonblank authorization record required')
    root = Path(__file__).resolve().parents[1]
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=False)
    os.environ.update(HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1',
                      NO_PROXY='localhost,127.0.0.1,::1', no_proxy='localhost,127.0.0.1,::1')
    def save(name, value):
        with (output / name).open('x', encoding='utf-8') as handle:
            json.dump(value, handle, sort_keys=True, indent=2, allow_nan=False)
    save('authorization.json', dict(source=args.authorization_record,
        use='one local diagnostic pass over six preparation examples', max_attempts=24,
        max_local_generations=30, max_metadata_requests=100, warmups=0, downloads_allowed=False,
        paid_services_allowed=False, labels_approved=False, fitting_settings_approved=False,
        scientific_custody_approved=False, calibration_freeze_approved=False))
    from app.game.offline.calibration import read_json
    from app.game.offline.collection import DiagnosticRecordingRequest, collection_plan
    from app.benchmark.project_adapter import AdapterConfiguration, inspect_setup
    from app.analysis.question_analyzer import QuestionAnalyzer
    from app.game.offline.collect import main as recording_main
    study = args.study_dir.resolve()
    config_path = study / 'adapter.draft.json'
    config = AdapterConfiguration.model_validate(read_json(config_path))
    if config.n_samples != 5 or config.device != 'cpu':
        raise ValueError('prepared configuration changed: require five confidence samples and CPU execution')
    preflight = inspect_setup(config)
    save('resource-preflight.json', preflight)
    if not preflight['ready']:
        raise ValueError('resource preflight blocked; no attempts executed')
    data = read_json(study / 'recording-request.draft.json')
    data.update(version='offline_diagnostic_recording_v1', intended_use='smoke', study_approval=None,
        cache_contract='diagnostic_observation_only', preparation_authorization='User diagnostic authorization; see authorization.json; no label/study/freeze approval',
        expected_setup=preflight['observed_setup'])
    from app.game.offline.calibration import MeasurementSetup
    setup = MeasurementSetup.model_validate(preflight['observed_setup'])
    data['execution_configuration_id'] = setup.resources.manifest_id
    data['final_test_reservation'].pop('custody_record', None)
    data['final_test_reservation']['version'] = 'diagnostic_exclusion_roster_v1'
    analyzer = QuestionAnalyzer(mode='heuristic', environ={})
    for example in data['examples']:
        example['label'] = None
        if example['analysis'] != asdict(analyzer.analyze(example['question'])):
            raise ValueError('captured analyzer output changed; do not replace it manually')
        if example['purpose'] != 'calibration':
            raise ValueError('warmups are not authorized')
    request = DiagnosticRecordingRequest.model_validate(data)
    roster = read_json(study / 'roster.draft.json')
    expected_ids = {r['example_id'] for r in roster['rows'] if r['role'] in {'history', 'development'}}
    if len(request.examples) != 6 or {e.example_id for e in request.examples} != expected_ids:
        raise ValueError('six authorized preparation identities required exactly once')
    if [c.verifier_name for c in request.candidates] != ['semantic','evidence','rule','confidence']:
        raise ValueError('prepared verifier roster changed')
    plans = [collection_plan(request, e) for e in request.examples]
    eligible = sum(p['eligible'] for plan in plans for p in plan['candidates'])
    if eligible > 24:
        raise ValueError('attempt budget exceeded before execution')
    save('request.json', request.model_dump(mode='json'))
    save('preparation-validation.json', dict(valid=True, examples=6, candidate_outcomes=24,
        eligible_attempts=eligible, max_generations=30, max_metadata_requests=100,
        no_warmups=True, final_identities_disjoint=True, analyzer_outputs_unchanged=True,
        labels_present=False, scientific_reservation_created=False, setup_fingerprint=setup.fingerprint))
    os.environ['VERIFIER_COLLECTION_ADAPTER_CONFIG'] = str(config_path)
    import requests
    import httpx
    original = requests.Session.request
    original_httpx = httpx.Client.request
    with (output / 'network-events.jsonl').open('x', encoding='utf-8') as network:
        budget = NetworkBudget(config.ollama_url, network)
        def guarded(session, method, url, *a, **kw):
            return budget.call(original, session, method, url, *a, **kw)
        def no_httpx(*a, **kw):
            raise RuntimeError('external/download HTTP clients are not authorized in this local diagnostic')
        requests.Session.request = guarded
        httpx.Client.request = no_httpx
        try:
            with (output / 'collection.log').open('x', encoding='utf-8') as log, redirect_stdout(log), redirect_stderr(log):
                result = recording_main(['collect', str(output / 'request.json'), '--output-dir', str(output / 'collection')])
        finally:
            requests.Session.request = original
            httpx.Client.request = original_httpx
            save('network-counts.json', budget.counts)
    print(json.dumps(dict(collector_exit_code=result, output=str(output), network=budget.counts)))
    return result


if __name__ == '__main__':
    raise SystemExit(main())
