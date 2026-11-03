"""One bounded current-service transition; retains original journals unchanged."""
import argparse,hashlib,importlib.util,json,os,sys
from pathlib import Path
def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def save(p,v):
    if hasattr(v,'model_dump'):v=v.model_dump(mode='json')
    with Path(p).open('x',encoding='utf-8') as f:json.dump(v,f,indent=2,sort_keys=True)
def main():
    sys.path.insert(0,str(Path.cwd()));root=Path(__file__).resolve().parents[1]
    target=root/'artifacts/remaining-category-studies-v1/reference-current-v1';old=target.parent/'reference'
    target.mkdir(exist_ok=False)
    collector=load('current_ref_collector',root/'app/game/offline/collection.py');journal=load('current_ref_journal',root/'app/game/offline/compound_journal.py')
    from app.benchmark.project_adapter import AdapterConfiguration,observe_service,inspect_setup,create_recording_verifiers
    from app.game.models import content_id,canonical_json
    from scripts.run_factual_diagnostic import NetworkBudget
    os.environ.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',NO_PROXY='localhost,127.0.0.1,::1',no_proxy='localhost,127.0.0.1,::1')
    source=Path('build/multitask-policy42');config=AdapterConfiguration.model_validate(read(source/'adapter.json'))
    service=observe_service(config);save(target/'service-observation.json',service)
    config=config.model_copy(update={'service_observation':str(target/'service-observation.json')})
    save(target/'adapter.json',config);os.environ['VERIFIER_COLLECTION_ADAPTER_CONFIG']=str(target/'adapter.json')
    report=inspect_setup(config)
    if not report['ready']:raise ValueError(report['blockers'])
    save(target/'inspection.json',report)
    original=collector.validate_recording_request(read(old/'request.json'))
    from app.game.offline.calibration import MeasurementSetup
    setup=MeasurementSetup.model_validate(report['observed_setup'])
    before={v.verifier_name:v for v in original.expected_setup.resources.verifiers};after={v.verifier_name:v for v in setup.resources.verifiers}
    for name in ('semantic','evidence','rule'):
        if before[name]!=after[name]:raise ValueError('non-Confidence transitive resource change: '+name)
    # Confidence differs ONLY in its service entry; models/prompts/config/code remain exact.
    if tuple(r for r in before['confidence'].resources if r.kind!='service')!=tuple(r for r in after['confidence'].resources if r.kind!='service'):raise ValueError('additional Confidence resource change')
    prior=[collector.CollectedAttempt.model_validate_json(line) for line in (old/'training/reference/attempts.jsonl').read_text(encoding='utf-8').splitlines()]
    starts=[json.loads(line)['attempt_id'] for line in (old/'training/reference/started.jsonl').read_text().splitlines()]
    network=[json.loads(line) for line in (old/'network.jsonl').read_text().splitlines()]
    generations=sum(v.get('kind')=='generation' and v.get('state')=='started' for v in network)
    ambiguous=set(starts)-{r.attempt_id for r in prior}
    if len(starts)!=60 or len(prior)!=59 or generations!=72 or len(ambiguous)!=1:raise ValueError('actual cumulative inventory differs from authorization')
    data=original.model_dump(mode='json');data.update(expected_setup=setup.model_dump(mode='json'),execution_configuration_id=setup.resources.manifest_id,
        study_approval='User attachment a58ea544: current-service transition; cumulative255 verifier starts/372 generation requests; no additional retries.')
    request=collector.RecordingRequest.model_validate(data);save(target/'request.json',request)
    lookup={e.run_id:e for e in request.examples};candidates={c.verifier_name:c for c in request.candidates};derived=[];links=[]
    for row in prior:
        if row.candidate=='confidence':continue
        e=lookup[row.run_id];d=row.model_dump(mode='json')
        d['attempt_id']=collector.attempt_identity(request,e,candidates[row.candidate]);d['planning_json']=canonical_json(collector.collection_plan(request,e))
        d['attempt']['configuration_id']=setup.resources.manifest_id
        d['attempt']['report_provenance']=canonical_json(dict(version='scoped_nonconfidence_transfer_v1',original_attempt_id=row.attempt_id,original_request_id=original.request_id,new_request_id=request.request_id,per_verifier_resources_unchanged=True))
        d['measurement']['setup_fingerprint']=setup.fingerprint
        derived.append(collector.CollectedAttempt.model_validate(d))
        links.append(dict(original_attempt_id=row.attempt_id,derived_attempt_id=d['attempt_id'],original_payload_sha256=content_id(row.model_dump(mode='json')),report_and_timing_unchanged=True))
    if len(derived)!=45:raise ValueError('reuse inventory differs')
    collector.RecordingBundle(request=request,observed_setup=setup,attempts=tuple(derived))
    resume=target/'transferred/reference';resume.mkdir(parents=True)
    save(resume/'request.json',request)
    (resume/'attempts.jsonl').write_text('\n'.join(r.model_dump_json() for r in derived)+'\n',encoding='utf-8')
    (resume/'started.jsonl').write_text('\n'.join(json.dumps(dict(attempt_id=r.attempt_id)) for r in derived)+'\n',encoding='utf-8')
    for filename in ('groups.json','reserved-examples.json'):save(target/filename,read(old/filename))
    protocol=read(old/'protocol.json');protocol.update(resource_transition='current_reference_service_v1; resumed exploratory study, not uninterrupted campaign',cumulative_caps=dict(verifier_starts=255,generation_requests=372),authorization=data['study_approval'])
    save(target/'protocol.json',protocol)
    replacement=next(e for e in request.examples if e.example_id=='reference-fresh-11-equivalent')
    amendment=dict(version='current_reference_service_transition_v1',original_resource_id=original.execution_configuration_id,current_resource_id=setup.resources.manifest_id,
        current_setup=setup.model_dump(mode='json'),service=service.model_dump(mode='json'),nonconfidence_transfers=links,
        historical_only_confidence_attempt_ids=[r.attempt_id for r in prior if r.candidate=='confidence'],interrupted_original_attempt_id=next(iter(ambiguous)),original_duration_ms=None,
        replacement_attempt_id=collector.attempt_identity(request,replacement,candidates['confidence']),
        cumulative_before=dict(starts=60,completions=59,generation_starts=72),planned_new_training=dict(starts=115,generations=200),maximum_if_reserved=dict(starts=255,generations=372),
        original_journal_sha256={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (old/'training/reference/attempts.jsonl',old/'training/reference/started.jsonl',old/'network.jsonl')},
        semantics='Old Confidence reports historical only; all40 fitting Confidence reports use current service.45 non-Confidence rows derived through exact per-verifier equivalence; original observations/report/timing remain preserved. No favorable outcome selection or automatic retries.')
    save(target/'amendment.json',amendment)
    files=[target/n for n in ('request.json','protocol.json','groups.json','reserved-examples.json','adapter.json','service-observation.json','amendment.json')]+[Path(__file__),root/'scripts/fit_reference_current.py',root/'scripts/reference_current_reserved.py',root/'scripts/collect_reference_current_reserved.py']
    save(target/'seal.json',{str(p.resolve()):hashlib.sha256(p.read_bytes()).hexdigest() for p in files})
    import requests
    with (target/'network.jsonl').open('x',encoding='utf-8') as network_file:
        guard=NetworkBudget(config.ollama_url,network_file,generation_limit=200,metadata_limit=journal.metadata_ceiling({'reference':request}))
        raw=requests.Session.request;requests.Session.request=lambda session,method,url,*args,**kw:guard.call(raw,session,method,url,*args,**kw)
        pool,actual,observer=create_recording_verifiers()
        if actual!=setup:raise ValueError('factory setup changed')
        save(target/'factory-provenance.json',dict(instances=[dict(name=v.name,type=v.__class__.__module__+'.'+v.__class__.__qualname__) for v in pool],actual_resources=observer.snapshot().model_dump(mode='json'),labels_dispatched=False))
        bundles=journal.record_requests({'reference':request},setup,pool,observer,target/'training',collector,resume_from=target/'transferred')
        integrity=collector.completeness(bundles[0][1]);integrity.update(network=guard.counts,resources_unchanged=observer.snapshot()==setup.resources,new_actual_starts=115,cumulative_starts=175,cumulative_generation_starts=72+guard.counts['generation'])
        save(target/'training/collection-integrity.json',integrity)
        if not integrity['complete'] or not integrity['resources_unchanged']:raise ValueError('preserve incomplete/drifted transition; no retries')
        print('TRANSITION_TRAINING_COMPLETE',integrity,flush=True)
if __name__=='__main__':main()
