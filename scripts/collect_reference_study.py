"""Resource-compatible journalled bridge. Run from original checkout, not feature cwd."""
import argparse,hashlib,importlib.util,json,os,sys
from pathlib import Path
def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
def main():
    p=argparse.ArgumentParser();p.add_argument('--study',type=Path,required=True);p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--resume-from',type=Path);a=p.parse_args()
    sys.path.insert(0,str(Path.cwd()));read=lambda p:json.loads(Path(p).read_text(encoding='utf-8'))
    for path,digest in read(a.study/'seal.json').items():
        if hashlib.sha256(Path(path).read_bytes()).hexdigest()!=digest:raise ValueError('precollection seal differs: '+path)
    root=Path(__file__).resolve().parents[1]
    collector=load('reference_owned_collector',root/'app/game/offline/collection.py');journal=load('reference_owned_journal',root/'app/game/offline/compound_journal.py')
    request=collector.validate_recording_request(read(a.study/'request.json'))
    if len(request.examples)!=40 or len(request.candidates)!=4:raise ValueError('training cap differs')
    os.environ.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',NO_PROXY='localhost,127.0.0.1,::1',no_proxy='localhost,127.0.0.1,::1',VERIFIER_COLLECTION_ADAPTER_CONFIG=str((a.source/'adapter.json').resolve()))
    import requests
    from app.benchmark.project_adapter import AdapterConfiguration,inspect_setup,observe_service,create_recording_verifiers
    from scripts.run_factual_diagnostic import NetworkBudget
    config=AdapterConfiguration.model_validate(read(a.source/'adapter.json'));preflight=inspect_setup(config)
    if not preflight['ready'] or preflight['observed_setup']!=request.expected_setup.model_dump(mode='json'):raise ValueError('actual setup differs')
    with (a.study/'network.jsonl').open('x',encoding='utf-8') as network:
        guard=NetworkBudget(config.ollama_url,network,generation_limit=200,metadata_limit=journal.metadata_ceiling({'reference':request}))
        original=requests.Session.request;requests.Session.request=lambda session,method,url,*args,**kw:guard.call(original,session,method,url,*args,**kw)
        if observe_service(config).model_dump(mode='json')!=preflight['inventory']['service']:raise ValueError('live service differs')
        pool,setup,observer=create_recording_verifiers()
        if setup!=request.expected_setup:raise ValueError('factory setup differs')
        before=observer.snapshot()
        (a.study/'factory-provenance.json').write_text(json.dumps(dict(source_root=str(Path.cwd()),before=before.model_dump(mode='json'),labels_dispatched=False,active_instance_attestation=callable(getattr(observer,'snapshot_for',None))),indent=2),encoding='utf-8')
        if before!=setup.resources:raise ValueError('pre-dispatch resource drift')
        bundles=journal.record_requests({'reference':request},setup,pool,observer,a.output,collector,resume_from=a.resume_from)
        bundle=bundles[0][1];after=observer.snapshot();integrity=collector.completeness(bundle)
        integrity.update(network=guard.counts,resources_unchanged=before==after)
        (a.output/'collection-integrity.json').write_text(json.dumps(integrity,indent=2),encoding='utf-8')
        if not integrity['complete'] or before!=after:raise ValueError('preserve incomplete/drifted records; no automatic retries')
        print('COMPLETE',integrity,flush=True)
if __name__=='__main__':main()
