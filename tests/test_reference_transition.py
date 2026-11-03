"""Validate the empirical transfer chain, without new inference or outcomes tuning."""
import hashlib,json
from pathlib import Path
from app.game.models import content_id
from app.game.offline.collection import validate_recording_request,CollectedAttempt,RecordingBundle
ROOT=Path('artifacts/remaining-category-studies-v1')
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def test_nonconfidence_transfer_preserves_authentic_report_timing_and_observation():
    target=ROOT/'reference-current-v1';proof=read(target/'amendment.json')
    prior={r['attempt_id']:r for r in map(json.loads,(ROOT/'reference/training/reference/attempts.jsonl').read_text().splitlines())}
    derived={r['attempt_id']:r for r in map(json.loads,(target/'transferred/reference/attempts.jsonl').read_text().splitlines())}
    req=validate_recording_request(read(target/'request.json'))
    RecordingBundle(request=req,observed_setup=req.expected_setup,attempts=tuple(CollectedAttempt.model_validate(r) for r in derived.values()))
    assert len(derived)==len(proof['nonconfidence_transfers'])==45
    for link in proof['nonconfidence_transfers']:
        old=prior[link['original_attempt_id']];new=derived[link['derived_attempt_id']]
        assert content_id(old)==link['original_payload_sha256']
        assert old['candidate']!='confidence'
        for field in ('returned_payload_json','duration_ms','timing_status','after_resources_json','achieved_capabilities','issues'):
            assert old[field]==new[field]
        for field in ('report_json','observed_resources_json','state','execution_id'):
            assert old['attempt'][field]==new['attempt'][field]
        assert old['attempt_id']!=new['attempt_id']
    assert not set(proof['historical_only_confidence_attempt_ids'])&set(derived)
    assert proof['replacement_attempt_id']!=proof['interrupted_original_attempt_id']
    assert proof['original_duration_ms'] is None
    for path,digest in proof['original_journal_sha256'].items():assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==digest

def test_category_frames_and_labels_unchanged_and_cumulative_budget_includes_discarded_work():
    old=ROOT/'reference';new=ROOT/'reference-current-v1'
    for file in ('groups.json','reserved-examples.json'):assert read(old/file)==read(new/file)
    oldreq=validate_recording_request(read(old/'request.json'));newreq=validate_recording_request(read(new/'request.json'))
    assert oldreq.examples==newreq.examples and oldreq.final_test_reservation==newreq.final_test_reservation
    proof=read(new/'amendment.json');assert len(proof['historical_only_confidence_attempt_ids'])==14
    assert 60+(160-45)+80==255
    assert 72+40*5+20*5==372
    assert read(new/'protocol.json')['minimum_clean_development_coverage']==.9
