"""Read-only local and live service readiness; no generations or model loading.
Run from the original resource-compatible checkout.
"""
import argparse,json,os,sys
from pathlib import Path

def main():
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();sys.path.insert(0,str(Path.cwd()))
    os.environ.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',NO_PROXY='localhost,127.0.0.1,::1',no_proxy='localhost,127.0.0.1,::1')
    import requests
    from app.benchmark.project_adapter import AdapterConfiguration,inspect_setup,observe_service
    from scripts.run_factual_diagnostic import NetworkBudget
    config=AdapterConfiguration.model_validate_json((a.source/'adapter.json').read_text(encoding='utf-8'))
    a.output.mkdir(parents=True,exist_ok=False)
    save=lambda name,v:(a.output/name).write_text(json.dumps(v,indent=2,sort_keys=True),encoding='utf-8')
    local=inspect_setup(config);save('local.json',local)
    if not local['ready']:raise ValueError(local['blockers'])
    with (a.output/'network.jsonl').open('x',encoding='utf-8') as network:
        guard=NetworkBudget(config.ollama_url,network,generation_limit=0,metadata_limit=8)
        original=requests.Session.request
        requests.Session.request=lambda session,method,url,*args,**kw:guard.call(original,session,method,url,*args,**kw)
        actual=observe_service(config).model_dump(mode='json');expected=local['inventory']['service']
        differences={k:dict(expected=expected.get(k),actual=actual.get(k)) for k in set(expected)|set(actual) if expected.get(k)!=actual.get(k)}
        save('live.json',dict(ready=not differences,expected=expected,actual=actual,differences=differences,network_counts=guard.counts,verifier_attempts=0))
        if differences:raise ValueError('live service identity differs; no expected hashes changed')
    print('LOCAL_AND_LIVE_READY',flush=True)

if __name__=='__main__':main()
