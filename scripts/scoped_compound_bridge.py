"""Owned scope inspector/collector, executed against unchanged native source."""
import argparse,importlib.util,json,sys,os,hashlib
from pathlib import Path
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
def main():
    p=argparse.ArgumentParser();p.add_argument('action',choices=['inspect','collect']);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    sys.path.insert(0,str(Path.cwd()));root=Path(__file__).resolve().parents[1]
    os.environ.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1')
    import requests
    def forbidden(*args,**kwargs):raise AssertionError('scoped E/R forbids network/service requests')
    requests.Session.request=forbidden
    adapter=load('owned_scoped_er',root/'scripts/scoped_er_adapter.py')
    read=lambda p:json.loads(Path(p).read_text(encoding='utf-8-sig'))
    original=read(root/'artifacts/remaining-category-studies-v1/compound-85/candidate/freeze.json')
    config=adapter.AdapterConfiguration.model_validate(read('build/multitask-policy42/adapter.json'))
    report=adapter.inspect_setup(config)
    if not report['ready']:raise ValueError(report['blockers'])
    adapter.require_equivalent(original['setup']['resources'],report['observed_setup']['resources'])
    if a.action=='inspect':
        a.output.mkdir(parents=True,exist_ok=False)
        (a.output/'inspection.json').write_text(json.dumps(report,indent=2),encoding='utf-8');return
    seal=read(a.output.parent/'transfer.json')
    for path,digest in seal['code_hashes'].items():
        if hashlib.sha256((root/path).read_bytes()).hexdigest()!=digest:raise ValueError('scoped bridge freeze differs')
    if report['observed_setup']!=seal['scoped_setup']:raise ValueError('scoped setup changed')
    pool,setup,observer=adapter.create_scoped(config,original['setup']['resources'])
    collector=load('scoped_collector',root/'app/game/offline/collection.py');journal=load('scoped_journal',root/'app/game/offline/compound_journal.py')
    prepared={cid:collector.validate_recording_request(read(a.output.parent/(cid+'.json'))) for cid in ('base_fact','derived_sum')}
    if any(len(r.examples)!=48 for r in prepared.values()):raise ValueError('reserved cap differs')
    bundles=journal.record_requests(prepared,setup,pool,observer,a.output,collector)
    observer.snapshot()
    data=dict(version='component_bound_recordings_v2',study_id=seal['study_id'],role='final_test',bundles=[(cid,b.model_dump(mode='json')) for cid,b in bundles])
    (a.output/'joint.json').write_text(json.dumps(data,indent=2),encoding='utf-8')
    (a.output/'integrity.json').write_text(json.dumps(dict(actual_attempts=sum(r.executed for _,b in bundles for r in b.attempts),complete=all(collector.completeness(b)['complete'] for _,b in bundles),network_requests=0,confidence_generations=0),indent=2),encoding='utf-8')
if __name__=='__main__':main()
