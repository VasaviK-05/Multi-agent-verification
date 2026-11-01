"""Prepare immutable approval inputs; no model loading or verifier execution."""
import copy
import json
from pathlib import Path
from types import SimpleNamespace
from app.benchmark.collect_costs import CollectionRequest, validate_preparation
from app.game.models import content_id
from app.game.offline.calibration import CalibrationRequest, read_json
from app.game.offline.collection import RecordingRequest

source = Path(__file__).parent
root = Path('build/verifier-cost-calibration-proposal-20261028-v2')
root.mkdir(exist_ok=False)
def save(name, data):
    with (root/name).open('x', encoding='utf-8') as f:
        json.dump(data, f, sort_keys=True, indent=2)

cost = read_json(source/'cost-request.pending.json')
settings = read_json(source/'calibration-settings.pending.json')
adapter = read_json(source/'adapter.json')
save('collection.pending.json', cost)
save('calibration.pending.json', settings)
save('adapter.json', adapter)
save('roster.json', read_json(source/'roster.json'))
# Run the existing split validator directly with the outcome-free reservation
# metadata. No synthetic custody or execution permission is inserted.
validate_preparation(SimpleNamespace(examples=[SimpleNamespace(**e) for e in cost['examples']],
    permitted_datasets=tuple(map(tuple,cost['permitted_datasets'])),
    final_test_reservation=SimpleNamespace(dataset_id=cost['final_test_reservation']['dataset_id'],
        examples=[SimpleNamespace(**r) for r in cost['final_test_reservation']['examples']])))
def errors(schema, payload):
    try:
        schema.model_validate(payload)
    except ValueError as exc:
        return [dict(path=list(e['loc']), type=e['type'], message=e['msg']) for e in exc.errors()]
    return []
collection_errors = errors(CollectionRequest,cost)
assert {tuple(e['path']) for e in collection_errors} == {
    ('preparation_authorization',),('final_test_reservation','custody_record')}
calibration_errors = errors(CalibrationRequest,settings)
assert {tuple(e['path']) for e in calibration_errors} == {
    ('measurements',),('freeze_record',),('final_test_reservation','custody_record')}
recording = read_json(source/'recording-request.pending.json')
recording.update(version='offline_recording_request_v1',cache_contract='complete_team_independent_v1')
recording['final_test_reservation'] = cost['final_test_reservation']
recording_errors = errors(RecordingRequest, recording)
assert sum(e['path'][-1] == 'label' for e in recording_errors) == 86
design = dict(version='verifier_cost_measurement_design_v2',
    population='Convenience sample: 80 reference-assisted constructed arithmetic plus six short factual preparation examples; not representative project-wide',
    categories=dict(add=14,subtract=24,multiply=22,divide=20,factual=6),
    roles=dict(history=43,development=43), runs=86,repetitions=1,warmups=0,
    include_warmups=True, retain_first_calls=True,include_all_measured_failures=True,
    example_order_seed=20261028,candidate_order=['semantic','evidence','rule','confidence'],
    execution='sequential CPU; existing caches; factory initialization outside timer',
    confidence=dict(samples=5,temperature=0.8,seeds=[0,1,2,3,4],timeout_seconds=60),
    maximum_attempts=344,maximum_local_generations=430,maximum_metadata_requests=4,
    metadata_scope='two tags/version pairs in factory; no per-attempt live observer',
    downloads=0,paid_services=0, automatic_retries=0,
    retained='MeasurementInput, attempt statuses, monotonic durations, factory-observed setup and input identities; no returned report payloads',
    failure_behavior='First raised exception stops existing cost collector after preserving measured partial rows; later attempts are absent; missing required verifiers block calibration',
    estimator='mean_attempt_wall_time_ms_v1',units='ms',
    freeze_procedure='Approve design and outcome-free exclusion roster before collection; record immutable input/setup/request digests after collection and before calibration; retain all measured failures and all scheduled first calls; never inspect final outcomes',
    scientific_scope='Cost estimation only. No correctness adjudication, policy fitting, final evaluation or publication claims',
    setup_fingerprint=content_id(cost['setup']))
binding = dict(design=design,collection=cost,calibration=settings,adapter=adapter)
save('design.json',design)
save('approval-binding.json',dict(proposal_id=content_id(binding),
    digest_definition='content_id of {design,collection,calibration,adapter}; pending nulls intentionally included',
    proposed_binding=binding,approved=False))
save('validation.json',dict(split_validation_passed=True,final_metadata_entries=len(cost['final_test_reservation']['examples']),
    collection_errors=collection_errors,calibration_errors=calibration_errors,
    report_preserving_path_errors=recording_errors,new_verifier_attempts=0,
    new_generations=0,new_live_metadata_requests=0,approvals_invented=False))
print(json.dumps(dict(output=str(root),proposal_id=content_id(binding),validation='only genuine authority records and future measurements missing')))
