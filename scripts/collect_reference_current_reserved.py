"""Exactly80 reserved native attempts/100 generations, only after checked freeze."""
import argparse,hashlib,importlib.util,json,os,sys
from pathlib import Path
def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
def main():
    p=argparse.ArgumentParser();p.add_argument('--study',type=Path,required=True);p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    sys.path.insert(0,str(Path.cwd()));read=lambda p:json.loads(Path(p).read_text(encoding='utf-8'))
    seal=read(a.study/'reserved-seal.json');freeze=read(a.study/'fit/freeze.json')
    from app.game.models import content_id
    if content_id(freeze)!=seal['freeze_id'] or hashlib.sha256((a.study/'reserved-request.json').read_bytes()).hexdigest()!=seal['request_sha256']:raise ValueError('reserved seal differs')
    for path,digest in freeze['source_hashes'].items():
        if hashlib.sha256(Path(path).read_bytes()).hexdigest()!=digest:raise ValueError('frozen code differs')
    root=Path(__file__).resolve().parents[1];collector=load('reference_reserved_collector',root/'app/game/offline/collection.py');journal=load('reference_reserved_journal',root/'app/game/offline/compound_journal.py')
    req=collector.validate_recording_request(read(a.study/'reserved-request.json'))
    if len(req.examples)!=20 or len(req.candidates)!=4 or req.freeze_id!=seal['freeze_id']:raise ValueError('reserved count/freeze differs')
    os.environ.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',NO_PROXY='localhost,127.0.0.1,::1',no_proxy='localhost,127.0.0.1,::1',VERIFIER_COLLECTION_ADAPTER_CONFIG=str((a.study/'adapter.json').resolve()))
    import requests
    from app.benchmark.project_adapter import AdapterConfiguration,inspect_setup,observe_service,create_recording_verifiers
    from scripts.run_factual_diagnostic import NetworkBudget
    config=AdapterConfiguration.model_validate(read(a.study/'adapter.json'));preflight=inspect_setup(config)
    if not preflight['ready'] or preflight['observed_setup']!=req.expected_setup.model_dump(mode='json'):raise ValueError('actual setup differs')
    with (a.study/'reserved-network.jsonl').open('x',encoding='utf-8') as network:
        guard=NetworkBudget(config.ollama_url,network,generation_limit=100,metadata_limit=journal.metadata_ceiling({'reference':req}))
        original=requests.Session.request;requests.Session.request=lambda session,method,url,*args,**kw:guard.call(original,session,method,url,*args,**kw)
        if observe_service(config).model_dump(mode='json')!=preflight['inventory']['service']:raise ValueError('live service differs')
        pool,setup,observer=create_recording_verifiers();before=observer.snapshot()
        if setup!=req.expected_setup or before!=setup.resources:raise ValueError('factory drift')
        bundles=journal.record_requests({'reference':req},setup,pool,observer,a.output,collector)
        integrity=collector.completeness(bundles[0][1]);after=observer.snapshot();integrity.update(network=guard.counts,resources_unchanged=before==after)
        (a.output/'collection-integrity.json').write_text(json.dumps(integrity,indent=2),encoding='utf-8')
        if not integrity['complete'] or before!=after:raise ValueError('preserve incomplete/drifted journals, no retry')
        print('REFERENCE_RESERVED_COMPLETE',integrity,flush=True)
if __name__=='__main__':main()
