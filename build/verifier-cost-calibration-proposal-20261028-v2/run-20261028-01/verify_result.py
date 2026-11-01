"""Independent read-only artifact/audit checks, plus new result exports."""
import csv
import hashlib
import json
from pathlib import Path
from collections import Counter
from app.game.models import content_id
from app.game.offline.calibration import read_json,CalibrationArtifact,MeasurementInput

root = Path(__file__).parent
artifact = CalibrationArtifact.model_validate(read_json(root/'calibration-v1.json'))
measurements = MeasurementInput.model_validate(read_json(root/'measurements.json'))
assert artifact.request.measurements == measurements
freeze = read_json(root/'freeze-receipt.json')
sha = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
for name,digest in freeze['files'].items():
    assert sha(root/name) == digest
for name,digest in freeze['proposal_files'].items():
    assert sha(root.parent/name) == digest
assert sha(root.parent/'execute_authorized.py') == freeze['runner_sha256']
assert artifact.request.freeze_record == str((root/'freeze-receipt.json').resolve())+' sha256='+sha(root/'freeze-receipt.json')
assert content_id(measurements.model_dump(mode='json')) == freeze['measurement_digest']
assert artifact.request.measurements.setup.fingerprint == freeze['setup_fingerprint']
events = [json.loads(line) for line in (root/'network-events.jsonl').read_text(encoding='utf-8').splitlines()]
counts = Counter((e['kind'],e['state']) for e in events)
assert counts == Counter({('generation','started'):430,('generation','returned'):430,
                         ('metadata','started'):4,('metadata','returned'):4})
assert all(e.get('status_code')==200 for e in events if e['state']=='returned')
assert Counter(a.verifier_name for a in measurements.attempts) == dict(semantic=86,evidence=86,rule=86,confidence=86)
assert all(a.status=='returned' and a.purpose=='calibration' for a in measurements.attempts)
assert len(freeze['included_attempts'])==344 and not freeze['uncollected_attempts'] and not freeze['exclusions']
request = read_json(root/'collection.authorized.json')
assert len(request['examples'])==86 and len(request['final_test_reservation']['examples'])==44
assert request['final_test_reservation'] == artifact.request.final_test_reservation.model_dump(mode='json')
validation = read_json(root/'calibration-validation.json')
assert validation['reload_valid'] and validation['complete']
oldroot = Path('build/factual-diagnostic-20261026-01')
for entry in read_json(oldroot/'diagnostic-summary.json')['artifacts']:
    assert sha(oldroot/entry['path']) == entry['sha256']
with (root/'timings.csv').open('x',encoding='utf-8',newline='') as f:
    fields=['verifier_name','attempts','returned','mean_ms','median_ms','p95_nearest_rank_ms','failures','timeouts','interruptions','abstentions']
    writer=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore')
    writer.writeheader()
    writer.writerows(validation['rows'])
receipt=dict(valid=True,calibration_id=artifact.calibration_id,input_digest=artifact.input_digest,
    setup_fingerprint=measurements.setup.fingerprint,
    actual_measured_attempts=344,actual_generation_requests=430,actual_metadata_requests=4,
    all_http_requests_returned_200=True,zero_raised_failures=True,exclusions=0,missing_attempts=0,
    freeze_files_verified=True,request_and_reservation_match=True,
    diagnostic_artifacts_unchanged=True,proposal_files_unchanged=True,
    reports_retained=False,abstention_counts_available=False,
    calibration_sha256=sha(root/'calibration-v1.json'),measurements_sha256=sha(root/'measurements.json'))
with (root/'independent-validation.json').open('x',encoding='utf-8') as f:
    json.dump(receipt,f,indent=2)
print(json.dumps(receipt))
