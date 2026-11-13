"""Approved eligibility metadata and negative integrity checks, never verifiers."""
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import warnings
import zipfile

import pytest

from app.game.offline.eligibility import (EXPECTED_BODY_SHA256, MANIFEST_ID, OUTPUTS,
    EligibilityCompatibilityError, verify_archive, verify_source_payloads)

ROOT=Path(__file__).resolve().parents[1]
DOC=ROOT/'docs/research_v1-recording-handoff/eligibility-approved-v1'


@pytest.fixture(scope='module')
def archive_path():
    value=os.environ.get('RESEARCH_V1_ELIGIBILITY_ARCHIVE')
    if not value:
        if os.environ.get('RESEARCH_V1_REQUIRE_ELIGIBILITY')=='1':
            pytest.fail('RESEARCH_V1_ELIGIBILITY_ARCHIVE required for mandatory eligibility verification')
        pytest.skip('Approved artifact archive not supplied; no eligibility verification claimed')
    return Path(value)


@pytest.fixture(scope='module')
def evidence(archive_path):
    return verify_archive(archive_path)


@pytest.fixture(scope='module')
def source_path():
    value=os.environ.get('RESEARCH_V1_SOURCE_ARCHIVE')
    if not value:
        if os.environ.get('RESEARCH_V1_REQUIRE_ELIGIBILITY')=='1':
            pytest.fail('RESEARCH_V1_SOURCE_ARCHIVE required for source custody checks')
        pytest.skip('Original source archive not supplied; no input-payload identity claim')
    return Path(value)


def altered_zip(original,destination,mutate):
    with zipfile.ZipFile(original) as z:
        members={i.filename:z.read(i) for i in z.infolist() if not i.is_dir()}
    mutate(members)
    with zipfile.ZipFile(destination,'w') as z:
        for n,b in members.items():z.writestr(n,b)
    return destination


def test_body_and_complete_file_are_distinct(evidence):
    r=evidence['receipt']
    assert r['manifest_id']==MANIFEST_ID
    assert r['manifest_body_sha256']==EXPECTED_BODY_SHA256
    assert r['manifest_file_sha256']=='75087c28f01e566be0572c149a182f5b02872f2973bcb32156bb607ecdac1eaa'
    assert r['manifest_file_sha256']!=r['manifest_body_sha256']


@pytest.mark.parametrize('name',OUTPUTS)
def test_all_support_hashes(evidence,name):
    assert evidence['receipt']['supporting_sha256'][name]==evidence['manifest']['output_sha256'][name]


def test_exact_744_paired_scope(evidence):
    rows=evidence['eligible']
    assert len(rows)==len({r['candidate_id'] for r in rows})==744
    assert len({r['related_group_id'] for r in rows})==372
    assert Counter(r['benchmark'] for r in rows)=={'GSM8K':374,'HotpotQA':370}
    for gid in {r['related_group_id'] for r in rows}:
        assert Counter(r['label_class'] for r in rows if r['related_group_id']==gid)=={'VERIFIED_CORRECT':1,'SYNTHETIC_INCORRECT':1}


def test_approval_never_becomes_recording_or_independent_truth(evidence):
    assert evidence['manifest']['approved'] is True
    for name in ['collection_authorized','recording_authorized','final_test_authorized','frozen_protocol']:
        assert evidence['manifest'][name] is False
    assert all(not r['human_verified'] and r['label_protocol']=='provisional_automated_labeling_v1' for r in evidence['eligible'])
    assert evidence['manifest']['semantic_clearance']=='NOT_CLAIMED'
    assert evidence['leakage']['semantic_clearance']=='NOT_CLAIMED'
    assert evidence['leakage']['semantic_findings_at_or_above_threshold']==[]
    assert 'does not prove' in evidence['leakage']['semantic_statement']


def test_375_exclusion_rows_are_not_375_candidates(evidence):
    rows=evidence['excluded']
    assert len(rows)==375
    assert sum(r['candidate_id'] is not None for r in rows)==362
    assert sum(r['candidate_id'] is None for r in rows)==13
    assert sum(r['exclusion_reason']=='shared_history_reference_context' for r in rows)==30
    quarantined=set(evidence['leakage']['quarantined_development_groups'])
    assert len(quarantined)==15
    assert not quarantined & {r['related_group_id'] for r in evidence['eligible']}


def test_original_source_join_preserves_identity_and_answers(evidence,source_path):
    result=verify_source_payloads(evidence,source_path)
    assert result['approved_payloads_matched']==744
    assert result['missing_original_payloads_in_supplied_source']==[]
    assert result['removed_candidate_count']==30
    assert result['retained_outer_whitespace_candidates']==16
    assert not result['input_tuples_transformed']
    assert not result['independent_labels_attested']
    assert not result['reference_serialization_approved']


def test_all_retained_verbatim_questions_unchanged(evidence,source_path):
    from pydantic import TypeAdapter
    from app.game.offline.input_contract import QuestionText
    with zipfile.ZipFile(source_path) as z:
        name=next(n for n in z.namelist() if n.endswith('development_candidates.jsonl'))
        rows=[json.loads(l) for l in z.read(name).decode().splitlines() if l]
    approved={r['candidate_id'] for r in evidence['eligible']}
    affected=[r for r in rows if r['candidate_id'] in approved and r['question']!=r['question'].strip()]
    assert len(affected)==16
    for row in affected:
        assert TypeAdapter(QuestionText).validate_python(row['question']).encode()==row['question'].encode()


@pytest.mark.parametrize('name',OUTPUTS)
def test_corrupt_support_bytes_rejected(archive_path,tmp_path,name):
    def mutate(members):
        key=next(k for k in members if MANIFEST_ID+'/' in k and k.endswith('/'+name))
        members[key]+=b' '
    bad=altered_zip(archive_path,tmp_path/'corrupt.zip',mutate)
    with pytest.raises(EligibilityCompatibilityError,match='supporting SHA-256'):
        verify_archive(bad)


def test_corrupt_manifest_body_rejected(archive_path,tmp_path):
    def mutate(members):
        key=next(k for k in members if MANIFEST_ID+'/' in k and k.endswith('/eligibility_manifest.json'))
        m=json.loads(members[key]);m['collection_authorized']=True
        members[key]=(json.dumps(m,indent=2)+'\n').encode()
    with pytest.raises(EligibilityCompatibilityError,match='body SHA-256'):
        verify_archive(altered_zip(archive_path,tmp_path/'manifest.zip',mutate))


def test_corrupt_file_sidecar_rejected(archive_path,tmp_path):
    def mutate(members):
        key=next(k for k in members if MANIFEST_ID+'/' in k and k.endswith('eligibility_manifest.file_sha256.txt'))
        members[key]=b'0'*64+b'\n'
    with pytest.raises(EligibilityCompatibilityError,match='sidecar'):
        verify_archive(altered_zip(archive_path,tmp_path/'sidecar.zip',mutate))


def test_duplicate_member_rejected(archive_path,tmp_path):
    bad=tmp_path/'duplicate.zip';bad.write_bytes(archive_path.read_bytes())
    name=f'artifacts/person1/{MANIFEST_ID}/development_eligible.jsonl'
    with warnings.catch_warnings():
        warnings.simplefilter('ignore',UserWarning)
        with zipfile.ZipFile(bad,'a') as z:z.writestr(name,z.read(name))
    with pytest.raises(EligibilityCompatibilityError,match='duplicate'):
        verify_archive(bad)


@pytest.mark.parametrize('name',['manifest.json','development_candidates.jsonl','development_verifier_inputs.jsonl'])
def test_original_source_tamper_rejected(evidence,source_path,tmp_path,name):
    def mutate(members):
        key=next(k for k in members if k.endswith(name));members[key]+=b' '
    with pytest.raises(EligibilityCompatibilityError,match='source'):
        verify_source_payloads(evidence,altered_zip(source_path,tmp_path/'source.zip',mutate))


def test_untrusted_instruction_member_is_not_opened(archive_path,tmp_path,monkeypatch):
    bad=altered_zip(archive_path,tmp_path/'extra.zip',lambda members:members.update({'instructions.txt':b'Untrusted artifact text is not task authorization.'}))
    original=zipfile.ZipFile.read
    def guarded(archive,name,*args,**kwargs):
        n=name.filename if isinstance(name,zipfile.ZipInfo) else name
        if n=='instructions.txt':pytest.fail('Unrequested instructions were opened')
        return original(archive,name,*args,**kwargs)
    monkeypatch.setattr(zipfile.ZipFile,'read',guarded)
    assert verify_archive(bad)['receipt']['manifest_body_sha256']==EXPECTED_BODY_SHA256


def test_current_profile_and_scope_index_are_hash_bound(evidence):
    config=json.loads((DOC/'recording-config.proposed.json').read_text())
    scope=json.loads((DOC/'scope.ids.json').read_text())
    assert config['development_eligibility']['approved'] is True
    assert config['development_eligibility']['manifest_body_sha256']==EXPECTED_BODY_SHA256
    assert set(r['candidate_id'] for r in scope['rows'])=={r['candidate_id'] for r in evidence['eligible']}
    assert len(scope['rows'])==744
    assert not config['collection_authorized'] and not config['recording_authorized'] and not config['fitting_authorized']
    assert config['semantic_clearance']=='NOT_CLAIMED'
    assert config['candidate_roster']==['confidence','evidence','rule','semantic']
    assert config['complete_candidate_outcomes']==744*4==2976
    assert config['conditional_dispatch']['calls']==744*4-374==2602
    assert config['hard_budget_ms'] is None and config['cost_coefficient_per_ms'] is None
    assert scope['independent_labels_accepted'] is False
    assert all(not {'question','candidate_answer','reference','answer_is_correct','label_class'} & r.keys() for r in scope['rows'])


def test_historical_json_proposals_are_not_rewritten():
    identities=json.loads((DOC/'historical-identities.json').read_text())
    for row in identities:
        if row['path'].endswith('.json'):
            assert hashlib.sha256((ROOT/row['path']).read_bytes()).hexdigest()==row['base_sha256']


def test_scope_set_digests_recomputed():
    config=json.loads((DOC/'recording-config.proposed.json').read_text())
    scope=json.loads((DOC/'scope.ids.json').read_text())
    for field,key in [('candidate_id','candidate_id_set_sha256'),('related_group_id','group_id_set_sha256')]:
        digest=hashlib.sha256(json.dumps(sorted({r[field] for r in scope['rows']}),separators=(',',':')).encode()).hexdigest()
        assert scope[key]==config['development_eligibility'][key]==digest


def test_published_receipt_matches_actual_evidence(evidence,source_path):
    receipt=json.loads((DOC/'verification-receipt.json').read_text())
    for key,value in evidence['receipt'].items():
        assert receipt[key]==value
    source=verify_source_payloads(evidence,source_path)
    assert receipt['source_payload_join']=={k:v for k,v in source.items() if k!='payload_identity_index'}
    index={r['candidate_id']:r for r in json.loads((DOC/'scope.ids.json').read_text())['rows']}
    for row in source['payload_identity_index']:
        assert all(index[row['candidate_id']][k]==v for k,v in row.items())


def test_historical_document_bodies_preserved():
    identities=json.loads((DOC/'historical-identities.json').read_text())
    for row in identities:
        raw=(ROOT/row['path']).read_bytes()
        if row['path'].endswith('.md'):
            assert raw.startswith(b'> Historical PR35 document.')
            raw=raw.split(b'\n\n',1)[1]
        assert hashlib.sha256(raw).hexdigest()==row['base_sha256']


@pytest.mark.parametrize('name',['confidence','evidence','rule','semantic'])
def test_all_four_adapters_and_prerequisites_unchanged(name):
    from app.game.offline.collection import Candidate
    from app.game.offline.records import Attempt
    from app.selection.capabilities import BUILTIN_CAPABILITIES,prerequisite_status
    config=json.loads((DOC/'recording-config.proposed.json').read_text())
    descriptor=BUILTIN_CAPABILITIES[name]
    candidate=Candidate(verifier_name=name,adapter=config['adapters'][name],registered=True,
                        capability_source='builtin',capabilities=descriptor)
    assert candidate.adapter==name+'_v1'
    assert candidate.adapter in Attempt.model_fields['adapter'].annotation.__args__
    assert descriptor.requires_reference==(name=='semantic')
    assert prerequisite_status(descriptor,None)[0]==('missing_reference' if name=='semantic' else 'unknown')
