"""Campaign accounting tests with a pure stub, zero native inference."""
from pathlib import Path
import pytest
from scripts.framework_acceptance import Journal,read_plan
from app.models.schemas import VerificationResult


class Stub:
    name='rule'
    def verify(self,*args,**kwargs):return VerificationResult(verifier_name='rule',score=1.,passed=True)


def test_plan_caps_sources_and_no_retry(tmp_path):
    plan=read_plan()
    assert len(plan['requests'])==6
    assert sum(r['expected_native_calls'] for r in plan['requests'])==8
    assert plan['maximum_confidence_generations']==0
    journal=Journal(tmp_path/'calls.jsonl');stub=Stub();journal.instrument(stub,'arithmetic')
    journal.request_id=plan['requests'][0]['request_id']
    stub.verify('synthetic question','synthetic answer',None)
    with pytest.raises(AssertionError,match='duplicate/retry'):stub.verify('synthetic question','synthetic answer',None)
    assert len(journal.started)==len(journal.completed)==1
    assert len((tmp_path/'calls.jsonl').read_text().splitlines())==2


def test_unplanned_candidate_does_not_start_call(tmp_path):
    journal=Journal(tmp_path/'calls.jsonl');stub=Stub();journal.instrument(stub,'compound')
    journal.request_id=read_plan()['requests'][0]['request_id']
    with pytest.raises(AssertionError,match='unplanned'):stub.verify('q','a',None)
    assert not journal.started


def test_retained_native_evidence_matches_current_execution_code():
    from scripts.verify_framework_delivery import audit_delivery
    result=audit_delivery()
    assert result['native_calls_started']==result['native_calls_completed']==8
    assert result['native_requests']==6 and result['confidence_generations']==0
    assert result['frozen_publication_artifacts_unchanged']
    assert not result['fresh_reference_inference']


def test_plan_labels_are_independent_source_and_exact_arithmetic():
    import json
    from app.benchmark.project_adapter import ROOT,file_digest
    plan=read_plan();path=ROOT/'artifacts/compound-study-36-v1/portable-inputs/geonames-countryInfo.txt'
    assert file_digest(path)==plan['independent_source_sha256']
    countries={line.split('\t')[0]:line.split('\t') for line in path.read_text(encoding='utf-8').splitlines()
        if line and not line.startswith('#')}
    for item in plan['requests']:
        if item['category']=='arithmetic':truth=int(item['answer'])==328+536
        elif item['category']=='factual':truth=item['answer']==f"The population of Belgium is {countries['BE'][7]}."
        else:
            submitted=json.loads(item['answer'])
            truth=int(submitted['base'])==int(countries['CM'][7]) and int(submitted['derived'])==int(submitted['base'])+1000
        assert truth==item['label']['answer_is_correct']
