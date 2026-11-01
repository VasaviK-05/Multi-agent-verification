"""Reproduce this diagnostic's descriptive timing summary; no calibration or fitting."""
import csv
import hashlib
import json
import math
import os
from pathlib import Path
import statistics

os.environ.update(HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1')
from app.game.offline.collect import load_bundle
from app.game.offline.collection import completeness, DiagnosticRecordingRequest

root = Path(__file__).resolve().parent
bundle = load_bundle(root / 'collection')
assert isinstance(bundle.request, DiagnosticRecordingRequest)
assert all(e.label is None for e in bundle.request.examples)
network = json.loads((root / 'network-counts.json').read_text())
assert network['generation'] <= 30 and network['metadata'] <= 100 and network['blocked'] == 0
rows = []
for candidate in bundle.request.candidates:
    attempts = [a for a in bundle.attempts if a.candidate == candidate.verifier_name]
    executed = [a for a in attempts if a.executed]
    durations = sorted(a.duration_ms for a in executed if a.duration_ms is not None)
    if any(not math.isfinite(d) or d < 0 for d in durations):
        raise ValueError('invalid measured duration; do not silently exclude it')
    rows.append(dict(verifier=candidate.verifier_name, intended=len(bundle.request.examples),
        attempted=len(executed), returned=sum(a.timing_status == 'returned' for a in executed),
        failures=sum(a.timing_status == 'failure' for a in executed),
        timeouts=sum(a.timing_status == 'timeout' for a in executed),
        interruptions=sum(a.timing_status == 'interrupted' for a in executed),
        abstentions=sum(a.attempt.state == 'abstention' for a in attempts),
        missing_measurements=len(bundle.request.examples)-len(durations),
        unverified_measured_attempts=sum(a.measurement is None for a in executed),
        mean_ms=statistics.mean(durations) if durations else None,
        median_ms=statistics.median(durations) if durations else None,
        p95_nearest_rank_ms=durations[math.ceil(.95*len(durations))-1] if durations else None,
        included_attempt_ids=[a.attempt_id for a in executed], durations_ms=durations))
paths = ['authorization.json','request.json','resource-preflight.json','preparation-validation.json',
    'network-counts.json','network-events.jsonl','collection/request.json','collection/observed-setup.json',
    'collection/recordings.json','collection/attempts.jsonl','collection/collection-report.json','collection.log']
summary = dict(version='provisional_diagnostic_timings_v1',
    interpretation='Provisional diagnostic timings from six examples; not representative project-wide costs',
    units='ms', quantity='per-verifier attempt wall time; not CPU time, money or elapsed request latency',
    estimator='Arithmetic mean and median of all executed measured attempts, including raised failures/timeouts; no exclusions',
    upper_percentile='nearest rank p95: sorted duration at one-based ceil(.95*n); n=6 makes this the sample maximum',
    warmups=0, repeats=1, initialization_and_resource_observation='outside verify timer',
    completeness=completeness(bundle), network=network,
    setup_fingerprint=bundle.observed_setup.fingerprint,
    execution_configuration_id=bundle.request.execution_configuration_id,
    request_id=bundle.request.request_id, bundle_id=bundle.bundle_id,
    code_revision=bundle.observed_setup.code_revision,
    application_source_digest=bundle.observed_setup.application_source_digest,
    rows=rows, labels_used=False, settings_chosen=False, final_outcomes_accessed=False,
    scientific_reservation_created=False, calibration_created=False,
    calibration_blocker='Diagnostic request has no scientific custody or calibration freeze approval; linked measurements retained without calibration export',
    training_export_allowed=False, policy_fitted=False,
    unknown_requirement_examples=[e.example_id for e in bundle.request.examples
        if not e.analysis.research_context.requirements_known],
    artifacts=[dict(path=p, sha256=hashlib.sha256((root/p).read_bytes()).hexdigest()) for p in paths])
with (root / 'diagnostic-summary.json').open('x', encoding='utf-8') as handle:
    json.dump(summary, handle, indent=2, sort_keys=True, allow_nan=False)
fields = ['verifier','intended','attempted','returned','failures','timeouts','interruptions','abstentions',
    'missing_measurements','unverified_measured_attempts','mean_ms','median_ms','p95_nearest_rank_ms']
with (root / 'timings.csv').open('x', newline='', encoding='utf-8') as handle:
    writer = csv.DictWriter(handle, fieldnames=fields, extrasaction='ignore')
    writer.writeheader()
    writer.writerows(rows)
print(json.dumps({k:summary[k] for k in ['setup_fingerprint','completeness','network','calibration_created']}, indent=2))
