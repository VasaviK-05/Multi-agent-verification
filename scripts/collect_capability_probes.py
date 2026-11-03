"""One fixed bounded diagnostic recording pass; no fitting, labels or policy dispatch.
Run from the original resource-compatible checkout. The prepared analyzer output
is metadata; every verifier receives only question, answer and fixed reference.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys


def main():
    p=argparse.ArgumentParser();p.add_argument('--study',type=Path,required=True);p.add_argument('--source',type=Path,required=True);p.add_argument('--resume-from',type=Path);a=p.parse_args()
    sys.path.insert(0,str(Path.cwd()))
    os.environ.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',NO_PROXY='localhost,127.0.0.1,::1',no_proxy='localhost,127.0.0.1,::1',VERIFIER_COLLECTION_ADAPTER_CONFIG=str((a.source/'adapter.json').resolve()))
    import requests
    from app.benchmark.project_adapter import AdapterConfiguration,inspect_setup,observe_service,create_recording_verifiers
    from app.game.offline.calibration import MeasurementSetup
    from scripts.run_factual_diagnostic import NetworkBudget
    read=lambda p:json.loads(Path(p).read_text(encoding='utf-8'))
    sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
    save=lambda p,d:Path(p).write_text(json.dumps(d,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    protocol=read(a.study/'protocol.json');seal=read(a.study/'pre-execution-seal.json')
    for name,digest in seal['files'].items():
        if sha(name)!=digest:raise ValueError('prepared diagnostic inputs/code changed: '+name)
    for name,digest in protocol['source_hashes'].items():
        if sha(name)!=digest:raise ValueError('fixed resources changed')
    target=a.study/('collection' if a.resume_from is None else 'collection-resumed');target.mkdir(exist_ok=False)
    module_path=Path(__file__).resolve().parents[1]/'app/game/offline/collection.py'
    spec=importlib.util.spec_from_file_location('capability_probe_collection',module_path);module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
    config=AdapterConfiguration.model_validate(read(a.source/'adapter.json'));preflight=inspect_setup(config);save(target/'resource-preflight.json',preflight)
    if not preflight['ready']:raise ValueError(preflight['blockers'])
    setup=MeasurementSetup.model_validate(preflight['observed_setup'])
    expected=read(a.source/'arithmetic/contract.json')
    if setup.resources.manifest_id!=expected['execution_configuration_id']:raise ValueError('resources differ from the retained model/source configuration')
    examples=read(a.study/'examples.json')
    assert len(examples)==24 and all(e['label'] is None for e in examples)
    request=module.DiagnosticRecordingRequest(version='offline_diagnostic_recording_v1',preparation_authorization='User request 330cdf57: at most24 diagnostic examples/96 verifier calls/120 local generations; no retraining or deployment',randomness_control='Existing temperature0.8, n5 seeds0..4; no deterministic generation claim',execution_configuration_id=setup.resources.manifest_id,factory='app.benchmark.project_adapter:create_recording_verifiers',expected_setup=setup,final_test_reservation=read(a.study/'exclusions.json'),permitted_datasets=(('development','capability-probes-v1-diagnostic'),),candidates=read(a.study/'candidates.json'),examples=examples)
    assert len(request.examples)*len(request.candidates)==96
    save(target/'request.json',request.model_dump(mode='json'));save(target/'observed-setup.json',setup.model_dump(mode='json'))
    prior=()
    if a.resume_from:
        if module.validate_recording_request(read(a.resume_from/'request.json'))!=request:raise ValueError('resume request changed')
        prior=tuple(module.CollectedAttempt.model_validate_json(x) for x in (a.resume_from/'attempts.jsonl').read_text().splitlines() if x.strip())
        started={json.loads(x)['attempt_id'] for x in (a.resume_from/'started.jsonl').read_text().splitlines() if x.strip()}
        if started-{r.attempt_id for r in prior if r.executed}:raise ValueError('ambiguous in-flight attempt: no retry permitted')
    with (target/'network-audit.jsonl').open('x',encoding='utf-8') as network:
        guard=NetworkBudget(config.ollama_url,network,generation_limit=120,metadata_limit=430)
        original=requests.Session.request;requests.Session.request=lambda session,method,url,*args,**kw:guard.call(original,session,method,url,*args,**kw)
        if observe_service(config).model_dump(mode='json')!=preflight['inventory']['service']:raise ValueError('live local model/version changed')
        verifiers,actual,observer=create_recording_verifiers()
        if actual!=setup:raise ValueError('factory setup differs from preflight')
        save(target/'collector-provenance.json',dict(collector_path=str(module_path),collector_sha256=sha(module_path),runner_sha256=sha(__file__),verifier_source_root=str(Path.cwd()),resource_id=setup.resources.manifest_id,labels_dispatched=False,exploratory_only=True))
        with (target/'attempts.jsonl').open('x',encoding='utf-8') as journal,(target/'started.jsonl').open('x',encoding='utf-8') as starts:
            for row in prior:
                if row.executed:starts.write(json.dumps(dict(attempt_id=row.attempt_id))+'\n')
            starts.flush();os.fsync(starts.fileno());count=[0]
            def begin(identity):starts.write(json.dumps(dict(attempt_id=identity))+'\n');starts.flush();os.fsync(starts.fileno())
            def sink(row):journal.write(row.model_dump_json()+'\n');journal.flush();os.fsync(journal.fileno());count[0]+=1;print(count[0],row.example_id,row.candidate,row.attempt.state,flush=True)
            bundle=module.collect(request,verifiers,actual,observer,sink=sink,completed=prior,on_start=begin)
        save(target/'recordings.json',bundle.model_dump(mode='json'));integrity=module.completeness(bundle);integrity['network_counts']=guard.counts;save(target/'collection-report.json',integrity)
        if not integrity['complete']:raise ValueError('Incomplete diagnostic collection: preserve journals and inspect; no replacement or ambiguous retry')
        print('COMPLETE',integrity['executed_calls'],guard.counts,flush=True)

if __name__=='__main__':main()
