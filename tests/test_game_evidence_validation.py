"""Synthetic resource-bound readiness evidence; no models or study outcomes."""
import json
import pytest
from app.game.research.evidence_validation import EvidenceValidation
from app.game.resource_provenance import VerifierResources, ResourceManifest
from app.verifiers.evidence_verifier import EvidenceVerifier
from tests.test_evidence_verifier import FakeRetriever, FakeNLI, chunk, ENTAILS, CONTRADICTS, NEUTRAL


def proof_data():
    resources=VerifierResources(verifier_name='evidence',resources=tuple(dict(
        kind=k,resource_id=k,sha256='a'*64) for k in ('implementation','configuration','model','corpus','index')))
    probes=[]
    for kind,probabilities in [('support',ENTAILS),('rejection',CONTRADICTS),('neutral',NEUTRAL)]:
        report=EvidenceVerifier(retriever=FakeRetriever([chunk('Hamlet','Shakespeare wrote Hamlet.',.9)]),
            nli=FakeNLI({'Shakespeare':probabilities})).verify('Who wrote Hamlet?','Shakespeare')
        for prefix in ('controlled','real_nli'):
            probes.append(dict(case_id=prefix+'_'+kind,report_json=report.model_dump_json()))
    report=EvidenceVerifier(retriever=FakeRetriever([chunk('Support','Shakespeare wrote Hamlet.',.9),
        chunk('Reject','Marlowe wrote Hamlet.',.9,1)]),nli=FakeNLI({'Shakespeare':ENTAILS,'Marlowe':CONTRADICTS})).verify('Who wrote Hamlet?','Shakespeare')
    probes.append(dict(case_id='controlled_conflict',report_json=report.model_dump_json()))
    return dict(version='evidence_public_contract_validation_v2',before=resources.model_dump(),after=resources.model_dump(),probes=probes)


def test_complete_proof_requires_identical_resources():
    data=proof_data();proof=EvidenceValidation(**data)
    proof.require_resources(ResourceManifest(verifiers=(proof.before,)))
    assert len(proof.validation_id)==64
    stale=proof.before.model_dump();stale['resources'][0]['sha256']='b'*64
    with pytest.raises(ValueError,match='differ'):
        proof.require_resources(ResourceManifest(verifiers=(VerifierResources(**stale),)))
    with pytest.raises(ValueError):proof.require_resources(None)


@pytest.mark.parametrize('tamper',['missing','duplicate','decision','coverage','changed_resource'])
def test_incomplete_or_failed_probe_cannot_clear_gate(tamper):
    data=proof_data()
    if tamper=='missing':data['probes'].pop()
    elif tamper=='duplicate':data['probes'][0]=data['probes'][1]
    elif tamper=='changed_resource':data['after']['resources'][0]['sha256']='b'*64
    else:
        row=json.loads(data['probes'][0]['report_json'])
        if tamper=='decision':row['metadata']['decision']='UNSURE'
        else:row['metadata']['supporting']=[]
        data['probes'][0]['report_json']=json.dumps(row)
    with pytest.raises(ValueError):EvidenceValidation(**data)


def test_legacy_recording_serialization_and_missing_gate_preserved():
    from tests.test_game_research import study, REVISION
    from app.game.research.readiness import check_readiness
    spec=study(labels=('direct_fact',),names=('evidence',))
    assert 'evidence_validation' not in spec.recording.model_dump(mode='json')
    result=check_readiness(spec,actual_code_revision=REVISION)
    assert 'known_evidence_contract_failures_require_repair_or_explicit_scope_revision' in result.blockers


def test_valid_probe_does_not_override_missing_recording_resources():
    from tests.test_game_research import study, REVISION
    from app.game.research.specification import ExperimentSpecification
    from app.game.research.readiness import check_readiness
    from app.game.execution_contract import ExecutionContract
    spec=study(labels=('direct_fact',),names=('evidence',))
    proof=EvidenceValidation(**proof_data())
    resources=ResourceManifest(verifiers=(proof.before,))
    contract=ExecutionContract(**{**spec.contract.model_dump(),'version':'offline_public_decision_v2',
        'execution_configuration_id':resources.manifest_id,'resource_manifest':resources})
    spec=ExperimentSpecification(**{**spec.model_dump(),'contract':contract,
        'recording':{**spec.recording.model_dump(),'execution_configuration_id':resources.manifest_id,'evidence_validation':proof}})
    result=check_readiness(spec,actual_code_revision=REVISION)
    assert result.evidence_validation_id==proof.validation_id
    assert 'known_evidence_contract_failures_require_repair_or_explicit_scope_revision' not in result.blockers
    assert not result.ready and result.resource_blockers


def test_explicit_network_ceiling_keeps_endpoint_and_redirect_protections():
    import io
    from types import SimpleNamespace
    from scripts.run_factual_diagnostic import NetworkBudget
    guard=NetworkBudget('http://localhost:11434/api/generate',io.StringIO(),generation_limit=2,metadata_limit=0)
    def call(*args,**kwargs):
        assert kwargs['allow_redirects'] is False
        return SimpleNamespace(status_code=200)
    for _ in range(2):guard.call(call,None,'POST','http://localhost:11434/api/generate')
    for method,url in [('POST','http://localhost:11434/api/generate'),('GET','http://localhost:11434/api/tags'),('POST','https://example.org/paid')]:
        with pytest.raises(RuntimeError):guard.call(call,None,method,url)
    with pytest.raises(ValueError):NetworkBudget('http://localhost:11434/api/generate',io.StringIO(),generation_limit=True)


def test_seeded_preparation_groups_variants_and_preserves_holdout(tmp_path):
    from scripts.factual_policy42 import prepare
    from app.game.offline.collection import RecordingRequest
    from app.game.offline.records import FinalTestReservation
    from tests.preparation_fixtures import synthetic_adapter_file
    adapter_config,_=synthetic_adapter_file(tmp_path)
    roots=[tmp_path/'one',tmp_path/'two']
    # Explicit synthetic source files; no real reserved payload is loaded by tests.
    for root in roots:
        (root/'sources').mkdir(parents=True)
        countries=[];lines=[]
        for i in range(120):
            token=chr(65+i//26)+chr(65+i%26)
            countries.append(dict(cca2=token,name=dict(common='Country'+token),capital=['City'+token],unMember=True))
            lines.append('\t'.join([token,'','','','Country'+token,'City'+token]))
        (root/'sources/countries.json').write_text(json.dumps(countries),encoding='utf-8')
        (root/'sources/geonames-countryInfo.txt').write_text('\n'.join(lines),encoding='utf-8')
        prepare(root,adapter_config=adapter_config)
    a=json.loads((roots[0]/'preparation.json').read_text(encoding='utf-8'))
    b=json.loads((roots[1]/'preparation.json').read_text(encoding='utf-8'))
    assert a==b and len(a['examples'])==80
    reservation=FinalTestReservation.model_validate_json((roots[0]/'reservation.json').read_text())
    assert len(reservation.examples)==40
    histories={e['split_identity'] for e in a['examples'] if e['role']=='history'}
    development={e['split_identity'] for e in a['examples'] if e['role']=='development'}
    reserved={e.split_identity for e in reservation.examples}
    assert len(histories)==len(development)==len(reserved)==20
    assert not(histories&development or histories&reserved or development&reserved)
    assert all(sum(e['split_identity']==g for e in a['examples'])==2 for g in histories|development)
