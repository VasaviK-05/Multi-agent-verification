"""One approved cost-only pass; audit limits outside the existing verify timer."""
import argparse
from contextlib import redirect_stdout, redirect_stderr
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import statistics
import traceback

ROOT = Path(__file__).resolve().parent
RUN = ROOT / 'run-20261028-01'


def now():
    return datetime.now(timezone.utc).isoformat()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, value):
    with Path(path).open('x', encoding='utf-8') as handle:
        json.dump(value, handle, indent=2, sort_keys=True, allow_nan=False)


class NetworkGuard:
    def __init__(self, url, handle):
        self.url, self.handle = url, handle
        base = url.rsplit('/api/generate', 1)[0]
        self.metadata = {base+'/api/tags', base+'/api/version'}
        self.counts = dict(generation=0, metadata=0, blocked=0)

    def call(self, original, session, method, url, *args, **kwargs):
        kind = ('generation' if method.upper() == 'POST' and url == self.url else
                'metadata' if method.upper() == 'GET' and url in self.metadata else None)
        if kind is None or self.counts[kind] >= (430 if kind == 'generation' else 4):
            self.counts['blocked'] += 1
            self.event(dict(state='blocked', method=method, kind=kind))
            raise RuntimeError('approved network limit/endpoint violation')
        self.counts[kind] += 1
        event = dict(kind=kind, ordinal=self.counts[kind], method=method.upper())
        self.event(dict(**event, state='started'))
        try:
            response = original(session, method, url, *args, **kwargs)
        except BaseException as exc:
            self.event(dict(**event, state='raised', error_type=type(exc).__name__))
            raise
        self.event(dict(**event, state='returned', status_code=response.status_code))
        return response

    def event(self, event):
        self.handle.write(json.dumps(dict(utc=now(), **event))+'\n')
        self.handle.flush()


def check_binding():
    from app.game.models import content_id
    from app.game.offline.calibration import read_json
    binding = read_json(ROOT/'approval-binding.json')
    actual = dict(design=read_json(ROOT/'design.json'), collection=read_json(ROOT/'collection.pending.json'),
        calibration=read_json(ROOT/'calibration.pending.json'), adapter=read_json(ROOT/'adapter.json'))
    assert actual == binding['proposed_binding']
    assert content_id(actual) == binding['proposal_id'] == '50b2f7523422fb868eaecf1e6fc8cd2d1ef1df90f0679fc02d901c37bcb769fb'
    roster = read_json(ROOT/'roster.json')
    assert len(roster) == len(actual['collection']['examples']) == 86
    for i, (row, e) in enumerate(zip(roster, actual['collection']['examples'])):
        assert row['order'] == i+1
        assert all(row[k] == v for k,v in e.items() if k != 'context')
        assert row['reference'] == e['context']
    assert actual['design']['maximum_attempts'] == 344
    assert actual['design']['maximum_local_generations'] == 430
    assert actual['design']['maximum_metadata_requests'] == 4
    assert all(e['purpose'] == 'calibration' for e in actual['collection']['examples'])
    return actual, binding['proposal_id']


def prepare():
    from pydantic import TypeAdapter
    from app.benchmark.collect_costs import CollectionRequest
    from app.benchmark.project_adapter import inspect_setup
    from app.game.offline.calibration import CalibrationRequest, MeasurementSetup
    actual, proposal_id = check_binding()
    RUN.mkdir(exist_ok=False)
    approval = dict(recorded_at_utc=now(), proposal_id=proposal_id,
        authority='Explicit human user approval in current chat: proceed with bound v2 proposal; preparation use and procedural reservation approved for this project cost-calibration campaign',
        scope='80 arithmetic + six factual preparation examples; existing splits and 44 final exclusions; one sequential CPU pass; approved seed/model settings; no warmups/retries; first calls and measured failures retained',
        limits=dict(attempts=344, local_generations=430, local_metadata=4,downloads=0,paid_services=0),
        custody='User-approved procedural project reservation; not independent third-party custody',
        freeze_authority='User explicitly instructs writing actual request, measurement, setup and relevant code/input digests after collection and before calibration',
        correctness_labels_approved=False, policy_fitting_approved=False,
        final_evaluation_approved=False, publication_claims_approved=False)
    save(RUN/'authorization.json', approval)
    request = actual['collection']
    request['preparation_authorization'] = 'Explicit human approval of bound v2 cost-calibration campaign; '+str(RUN/'authorization.json')
    request['final_test_reservation']['custody_record'] = 'Explicit user-adopted procedural reservation of existing grouped splits and 44 metadata-only exclusions; not independent third-party custody; '+str(RUN/'authorization.json')
    request = CollectionRequest.model_validate(request)
    preflight = inspect_setup(actual['adapter'])
    save(RUN/'resource-preflight.json',preflight)
    assert preflight['ready']
    assert MeasurementSetup.model_validate(preflight['observed_setup']) == request.setup
    # Validate every available calibration configuration field; actual measurements
    # and their freeze receipt do not exist yet and must never be synthesized.
    settings = actual['calibration']
    settings['final_test_reservation'] = request.final_test_reservation.model_dump(mode='json')
    for field in ('required_verifiers','include_warmups','final_test_reservation'):
        TypeAdapter(CalibrationRequest.model_fields[field].annotation).validate_python(settings[field])
    assert set(settings['required_verifiers']) == set(actual['design']['candidate_order'])
    assert settings['include_warmups'] is True
    save(RUN/'calibration.before-measurements.json', settings)
    save(RUN/'collection.authorized.json',request.model_dump(mode='json'))
    save(RUN/'preparation-validation.json',dict(valid=True,utc=now(),proposal_id=proposal_id,
        request_digest=__import__('app.game.models',fromlist=['content_id']).content_id(request.model_dump(mode='json')),
        setup_fingerprint=request.setup.fingerprint,roster_matches=True,
        split_and_final_exclusion_validated=True,example_runs=86,maximum_attempts=344,
        maximum_generations=430,maximum_metadata_requests=4,
        actual_measurements_and_freeze_pending=True,runner_sha256=sha(__file__)))
    print(json.dumps(dict(prepared=True,run=str(RUN),setup=request.setup.fingerprint)),flush=True)


def execute():
    from app.benchmark import collect_costs
    from app.game.offline.calibration import read_json
    from app.game.offline.timing import TimedVerifier
    check_binding()
    request = collect_costs.CollectionRequest.model_validate(read_json(RUN/'collection.authorized.json'))
    # Exclusive execution marker makes an accidental second invocation fail before initialization.
    save(RUN/'execution-start.json',dict(utc=now(),runner_sha256=sha(__file__)))
    os.environ.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',
        NO_PROXY='localhost,127.0.0.1,::1',no_proxy='localhost,127.0.0.1,::1',
        VERIFIER_COLLECTION_ADAPTER_CONFIG=str(ROOT/'adapter.json'))
    import requests
    import httpx
    original_http, original_httpx = requests.Session.request, httpx.Client.request
    original_verify = TimedVerifier.verify
    expected = [(e.run_id,name) for e in request.examples for name in ('semantic','evidence','rule','confidence')]
    attempted = 0
    error = None
    with (RUN/'network-events.jsonl').open('x',encoding='utf-8') as network, \
         (RUN/'attempt-journal.jsonl').open('x',encoding='utf-8') as journal, \
         (RUN/'collection.log').open('x',encoding='utf-8') as log:
        guard = NetworkGuard(read_json(ROOT/'adapter.json')['ollama_url'],network)
        def guarded_http(session,method,url,*a,**kw):
            return guard.call(original_http,session,method,url,*a,**kw)
        def deny_httpx(*a,**kw):
            guard.counts['blocked'] += 1
            raise RuntimeError('download/external HTTP client forbidden')
        def audited_verify(verifier,*args,**kwargs):
            nonlocal attempted
            key = verifier._measurement_metadata['run_id'],verifier.name
            if attempted >= 344 or expected[attempted] != key:
                raise RuntimeError('attempt limit/order violation before verify')
            attempted += 1
            size = len(verifier._measurements)
            try:
                return original_verify(verifier,*args,**kwargs)
            finally:
                # The same measurement produced by TimedVerifier, after its timer stopped.
                if len(verifier._measurements) == size+1:
                    journal.write(json.dumps(verifier._measurements[-1])+'\n')
                    journal.flush()
        requests.Session.request, httpx.Client.request = guarded_http,deny_httpx
        TimedVerifier.verify = audited_verify
        try:
            with redirect_stdout(log),redirect_stderr(log):
                collect_costs.main([str(RUN/'collection.authorized.json'),'--output',str(RUN/'measurements.json')])
        except BaseException as exc:
            error = dict(type=type(exc).__name__,message=str(exc),traceback=traceback.format_exc())
        finally:
            requests.Session.request,httpx.Client.request = original_http,original_httpx
            TimedVerifier.verify = original_verify
            save(RUN/'execution-result.json',dict(utc=now(),attempts_started=attempted,
                network=guard.counts,error=error,no_retries=True))
    print(json.dumps(dict(collection_finished=True,attempts_started=attempted,error=error)),flush=True)
    finish()


def finish():
    from app.benchmark.project_adapter import inspect_setup
    from app.game.models import content_id
    from app.game.offline.calibration import (read_json,MeasurementInput,AttemptMeasurement,CalibrationRequest,
        CalibrationArtifact,main as calibration_main)
    check_binding()
    request = read_json(RUN/'collection.authorized.json')
    measurements = MeasurementInput.model_validate(read_json(RUN/'measurements.json'))
    assert measurements.setup.model_dump(mode='json') == request['setup']
    journal = [json.loads(line) for line in (RUN/'attempt-journal.jsonl').read_text(encoding='utf-8').splitlines()]
    assert [AttemptMeasurement.model_validate(a) for a in journal] == list(measurements.attempts)
    expected = [(e['run_id'],name) for e in request['examples'] for name in ('semantic','evidence','rule','confidence')]
    assert [(a.run_id,a.verifier_name) for a in measurements.attempts] == expected[:len(measurements.attempts)]
    post = inspect_setup(read_json(ROOT/'adapter.json'))  # zero network requests
    save(RUN/'resource-postcheck.json',post)
    assert post['ready'] and post['observed_setup'] == request['setup'], 'setup drift; do not calibrate'
    result = read_json(RUN/'execution-result.json')
    assert len(measurements.attempts) == result['attempts_started'] <= 344
    assert result['network']['generation'] <= 430 and result['network']['metadata'] <= 4
    assert result['network']['blocked'] == 0
    required = read_json(ROOT/'calibration.pending.json')['required_verifiers']
    assert set(required) <= {a.verifier_name for a in measurements.attempts}, 'missing required verifier; no calibration'
    inputs = ['collection.authorized.json','measurements.json','attempt-journal.jsonl',
        'authorization.json','preparation-validation.json','execution-result.json',
        'resource-preflight.json','resource-postcheck.json','network-events.jsonl']
    freeze = dict(recorded_at_utc=now(),authority=str(RUN/'authorization.json'),
        custody='User-approved procedural project reservation, no third-party custody',
        proposal_id=read_json(ROOT/'approval-binding.json')['proposal_id'],
        request_digest=content_id(request),measurement_digest=content_id(measurements.model_dump(mode='json')),
        setup_fingerprint=measurements.setup.fingerprint,
        application_source_digest=measurements.setup.application_source_digest,
        code_revision=measurements.setup.code_revision,runner_sha256=sha(__file__),
        files={name:sha(RUN/name) for name in inputs},
        proposal_files={name:sha(ROOT/name) for name in ('approval-binding.json','roster.json','design.json','adapter.json')},
        included_attempts=[dict(run_id=a.run_id,verifier=a.verifier_name) for a in measurements.attempts],
        uncollected_attempts=[dict(run_id=run,verifier=name) for run,name in expected[len(measurements.attempts):]],
        exclusions=[],include_warmups=True,warmups=0,
        note='Freeze of actual measurement inputs before calibration; first calls and failures retained; no policy or final outcomes')
    save(RUN/'freeze-receipt.json',freeze)
    settings = read_json(RUN/'calibration.before-measurements.json')
    settings['freeze_record'] = str(RUN/'freeze-receipt.json')+' sha256='+sha(RUN/'freeze-receipt.json')
    CalibrationRequest.model_validate({**settings,'measurements':measurements.model_dump(mode='json')})
    save(RUN/'calibration.authorized.json',settings)
    assert calibration_main([str(RUN/'calibration.authorized.json'),'--measurements',str(RUN/'measurements.json'),
        '--output',str(RUN/'calibration-v1.json')]) == 0
    artifact = CalibrationArtifact.model_validate(read_json(RUN/'calibration-v1.json'))
    assert artifact.request.measurements == measurements
    assert artifact.request.final_test_reservation.model_dump(mode='json') == request['final_test_reservation']
    assert artifact.result['exclusions'] == []
    rows = []
    for row in artifact.result['estimates']:
        observed = [a for a in measurements.attempts if a.verifier_name == row['verifier_name']]
        durations = sorted(a.duration_ms for a in observed)
        assert row['mean_ms'] == statistics.mean(durations)
        assert row['median_ms'] == statistics.median(durations)
        assert row['p95_nearest_rank_ms'] == durations[math.ceil(.95*len(durations))-1]
        assert row['attempts'] == len(observed)
        assert row['failures'] == sum(a.status != 'returned' for a in observed)
        rows.append(dict(**row,returned=sum(a.status=='returned' for a in observed),
            timeouts=sum(a.status=='timeout' for a in observed),interruptions=sum(a.status=='interrupted' for a in observed),
            abstentions=None,report_payloads_retained=False))
    save(RUN/'calibration-validation.json',dict(reload_valid=True,utc=now(),
        calibration_id=artifact.calibration_id,input_digest=artifact.input_digest,
        setup_fingerprint=measurements.setup.fingerprint,calibration_sha256=sha(RUN/'calibration-v1.json'),
        measurements_sha256=sha(RUN/'measurements.json'),counts=len(measurements.attempts),
        complete=len(measurements.attempts)==344,network=result['network'],rows=rows,
        note='Applies to this arithmetic-heavy preparation sample and observed setup, not universal costs; no reports or abstention counts retained'))
    print(json.dumps(dict(calibration_created=True,calibration_id=artifact.calibration_id,
        counts=len(measurements.attempts),rows=rows)),flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('phase',choices=['prepare','execute'])
    phase = parser.parse_args().phase
    (prepare if phase == 'prepare' else execute)()
