"""Verify retained raw/exported payload identity, without importing or dispatching verifiers."""
import hashlib
import json
from pathlib import Path
import runpy
D=Path(__file__).resolve().parents[1]
runpy.run_path(str(D/'fit_approved.py'),run_name='fidelity_guard_import')
b=json.loads((D/'collection/recordings.json').read_text())
s=json.loads((D/'approved-policy-input.json').read_text())
t=json.loads((D/'investigation/traces.json').read_text())
plan=json.loads(s['context']['selection_json'])
rows={ (e['validation_id'],a['verifier_name']):a for p in s['manifest']['partitions'] for e in p['examples'] for a in e['attempts']}
checks=[]
for a in b['attempts']:
    raw=json.loads(a['returned_payload_json'])
    normalized=json.loads(a['attempt']['report_json'])
    assert raw==normalized
    assert json.loads(rows[(a['run_id'],a['candidate'])]['report_json'])==normalized
    checks.append(dict(run_id=a['run_id'],candidate=a['candidate'],raw_equals_attempt_equals_export=True,achieved_capabilities=a['achieved_capabilities'],planning=json.loads(a['planning_json'])))
assert len(checks)==160
assert all(hashlib.sha256((D/p).read_bytes()).hexdigest()==digest for p,digest in t['original_hashes'].items())
result=dict(status='passed',rows=checks,frozen_plan=plan,calibration_id=json.loads((D/'calibration.json').read_text())['calibration_id'],original_hashes_preserved=True,final_payload_access='blocked by audit hook',no_dispatch=True)
(D/'investigation/fidelity.json').write_text(json.dumps(result,indent=2)+'\n')
print('160 raw/attempt/export payloads identical; originals unchanged; no final payload access')
