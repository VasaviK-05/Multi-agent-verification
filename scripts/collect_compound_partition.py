"""Resource-compatible bridge, only prepared Evidence/Rule collector requests."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys


def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec)
    sys.modules[name]=module;spec.loader.exec_module(module);return module


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--prepared',type=Path,required=True)
    p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--resume-from',type=Path)
    p.add_argument('--frozen',type=Path)
    a=p.parse_args();sys.path.insert(0,str(Path.cwd()))
    root=Path(__file__).resolve().parents[1]
    collector=load('compound_owned_collector',root/'app/game/offline/collection.py')
    journal=load('compound_owned_journal',root/'app/game/offline/compound_journal.py')
    read=lambda path:json.loads(Path(path).read_text(encoding='utf-8'))
    bridge=read(a.prepared/'bridge.json');prepared={}
    from app.game.models import content_id
    if hashlib.sha256((a.prepared/'study.json').read_bytes()).hexdigest()!=bridge['study_sha256']:
        raise ValueError('predeclared study changed')
    study=read(a.prepared/'study.json')
    sizes=study.get('partition_sizes')
    if sizes is None:
        counts=dict(history=16,development=16,final_test=16)
        if study['version']!='grouped_compound_study_v2':raise ValueError('legacy study version differs')
    else:
        amended=sizes['version']=='amended_36_v1'
        per=12 if amended else 16
        counts={role:sizes[role] for role in ('history','development','final_test')}
        if any(n!=per for n in counts.values()) or study['version']!=('grouped_compound_study_v3' if amended else 'grouped_compound_study_v2'):
            raise ValueError('explicit partition design/version differs')
    total=sum(counts.values())
    if content_id(study)!=bridge['study_id'] or len(study['groups'])!=total or len({g['source_id'] for g in study['groups']})!=total:
        raise ValueError('study identity or independent group count differs')
    for role in ('history','development','final_test'):
        if sum(g['role']==role for g in study['groups'])!=counts[role]:raise ValueError('partition group count differs')
    for path,digest in bridge['source_hashes']:
        if hashlib.sha256(Path(path).read_bytes()).hexdigest()!=digest:raise ValueError('prepared code changed')
    if bridge['role']=='final_test':
        if a.frozen is None:raise ValueError('actual candidate freeze required before reserved collection')
        frozen=read(a.frozen/'freeze.json')
        if content_id(frozen)!=bridge['freeze_id'] or frozen['study']!=study:raise ValueError('reserved candidate/study freeze differs')
        for name,digest in read(a.frozen/'inventory.json').items():
            if Path(name).name!=name or hashlib.sha256((a.frozen/name).read_bytes()).hexdigest()!=digest:raise ValueError('candidate inventory changed')
        for path,digest in frozen['source_hashes']:
            if hashlib.sha256(Path(path).read_bytes()).hexdigest()!=digest:raise ValueError('frozen evaluation code changed')
    for cid,digest in bridge['requests'].items():
        path=a.prepared/(cid+'.json')
        if hashlib.sha256(path.read_bytes()).hexdigest()!=digest:raise ValueError('prepared request changed')
        prepared[cid]=collector.validate_recording_request(read(path))
    if set(prepared)!={'base_fact','derived_sum'}:raise ValueError('complete component plan required')
    for cid,name in (('base_fact','evidence'),('derived_sum','rule')):
        req=prepared[cid]
        if {c.verifier_name for c in req.candidates if c.registered}!={name} or len(req.examples)!=4*counts[bridge['role']]:
            raise ValueError('bounded registered assignments/partition size differs')
        if req.expected_setup.model_dump(mode='json')!=bridge['setup']:raise ValueError('prepared setup differs')
        if bridge['role']=='final_test' and getattr(req,'freeze_id',None)!=bridge['freeze_id']:raise ValueError('reserved freeze identity differs')
    os.environ.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',NO_PROXY='localhost,127.0.0.1,::1',no_proxy='localhost,127.0.0.1,::1',
        VERIFIER_COLLECTION_ADAPTER_CONFIG=str((a.source/'adapter.json').resolve()))
    import requests
    from app.benchmark.project_adapter import AdapterConfiguration,inspect_setup,create_recording_verifiers
    from scripts.run_factual_diagnostic import NetworkBudget
    config=AdapterConfiguration.model_validate(read(a.source/'adapter.json'));preflight=inspect_setup(config)
    if not preflight['ready'] or preflight['observed_setup']!=bridge['setup']:raise ValueError('actual local resources/setup differ')
    # Network guard precedes model/factory initialization. No Confidence verify is reachable.
    log=a.prepared/'network.jsonl'
    with log.open('x',encoding='utf-8') as network:
        guard=NetworkBudget(config.ollama_url,network,generation_limit=0,metadata_limit=journal.metadata_ceiling(prepared))
        original=requests.Session.request
        requests.Session.request=lambda session,method,url,*args,**kw:guard.call(original,session,method,url,*args,**kw)
        pool,setup,observer=create_recording_verifiers()
        if setup.model_dump(mode='json')!=bridge['setup']:raise ValueError('factory resource setup differs')
        before=observer.snapshot()
        provenance=dict(factory='app.benchmark.project_adapter:create_recording_verifiers',source_root=str(Path.cwd()),
            assigned_instances=[dict(name=v.name,implementation=v.__class__.__module__+'.'+v.__class__.__qualname__) for v in pool if v.name in {'evidence','rule'}],
            active_instance_attestation_hook=callable(getattr(observer,'snapshot_for',None)),
            before_resources=before.model_dump(mode='json'),labels_dispatched=False,confidence_verify_called=False)
        (a.prepared/'factory-provenance.json').write_text(json.dumps(provenance,indent=2),encoding='utf-8')
        if before!=setup.resources:raise ValueError('factory pre-dispatch resource drift')
        bundles=journal.record_requests(prepared,setup,[v for v in pool if v.name in {'evidence','rule'}],observer,a.output,collector,resume_from=a.resume_from)
        data=dict(version='component_bound_recordings_v2',study_id=bridge['study_id'],role=bridge['role'],
            bundles=[(cid,b.model_dump(mode='json')) for cid,b in bundles])
        (a.output/'joint.json').write_text(json.dumps(data,indent=2),encoding='utf-8')
        after=observer.snapshot()
        (a.output/'resources-after.json').write_text(after.model_dump_json(indent=2),encoding='utf-8')
        counts=dict(actual_attempts=sum(row.executed for _,b in bundles for row in b.attempts),network=guard.counts,
            new_invocations_this_session=sum(read(a.output/cid/'session-count.json')['new_invocations'] for cid in prepared),
            complete=all(collector.completeness(b)['complete'] for _,b in bundles) and before==after)
        (a.output/'collection-integrity.json').write_text(json.dumps(counts,indent=2),encoding='utf-8')
        if not counts['complete']:raise ValueError('preserve incomplete journals; never retry ambiguous starts')


if __name__=='__main__':main()
