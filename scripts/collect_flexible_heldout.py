"""Bounded held-out extension of the existing collector and checkpoint journals.
Execute from the original resource-compatible checkout. Verifier imports resolve
there; only this owned collector extension is loaded from the feature worktree.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys


def main():
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--frozen',type=Path,required=True);p.add_argument('--cohort',choices=['arithmetic','factual'],required=True);p.add_argument('--resume-from',type=Path);a=p.parse_args()
    sys.path.insert(0,str(Path.cwd()))
    os.environ.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',NO_PROXY='localhost,127.0.0.1,::1',no_proxy='localhost,127.0.0.1,::1',VERIFIER_COLLECTION_ADAPTER_CONFIG=str((a.source/'adapter.json').resolve()))
    from app.benchmark.project_adapter import AdapterConfiguration,inspect_setup,observe_service,create_recording_verifiers
    from app.game.offline.calibration import MeasurementSetup
    from app.game.models import content_id
    from scripts.run_factual_diagnostic import NetworkBudget
    import requests
    read=lambda p:json.loads(Path(p).read_text(encoding='utf-8'))
    save=lambda p,d:Path(p).write_text(json.dumps(d,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
    seal=read(a.frozen/'precollection-seal.json')
    for name,digest in seal['files'].items():
        if sha(Path(name))!=digest:raise ValueError('precollection seal changed: '+name)
    frozen=read(a.frozen/'freeze-manifest.json')
    for name,digest in frozen['frozen_file_hashes'].items():
        if sha(a.frozen/name)!=digest:raise ValueError('frozen candidate bytes changed: '+name)
    target=a.frozen/a.cohort/('collection' if a.resume_from is None else 'collection-resumed')
    target.mkdir(exist_ok=False)
    module_path=Path(__file__).resolve().parents[1]/'app/game/offline/collection.py'
    spec=importlib.util.spec_from_file_location('flexible_heldout_collection',module_path);module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
    config=AdapterConfiguration.model_validate(read(a.source/'adapter.json'))
    report=inspect_setup(config);save(target/'resource-preflight.json',report)
    if not report['ready']:raise ValueError(report['blockers'])
    contract=read(a.frozen/a.cohort/'contract.json')
    setup=MeasurementSetup.model_validate(report['observed_setup'])
    if setup.resources.manifest_id!=contract['execution_configuration_id']:raise ValueError('resource manifest differs from frozen contract')
    with (target/'network-audit.jsonl').open('x',encoding='utf-8') as network:
        guard=NetworkBudget(config.ollama_url,network,generation_limit=200,metadata_limit=700)
        original=requests.Session.request
        requests.Session.request=lambda session,method,url,*args,**kw:guard.call(original,session,method,url,*args,**kw)
        if observe_service(config).model_dump(mode='json')!=report['inventory']['service']:raise ValueError('live model/service mismatch')
        save(target/'collector-provenance.json',dict(freeze_id=frozen['freeze_id'],collector_extension_path=str(module_path),collector_extension_sha256=sha(module_path),runner_sha256=sha(__file__),verifier_source_root=str(Path.cwd()),resource_id=setup.resources.manifest_id,software_versions=setup.dependency_versions,prepared_payload_sha256=sha(a.source/a.cohort/'custody/final-prepared-payload.json')))
        # Open only the authorized cohort after candidate/spec freeze and resource gate.
        payload=read(a.source/a.cohort/'custody/final-prepared-payload.json')
        for row in payload:row['purpose']='heldout'
        request=module.HeldoutRecordingRequest(version='offline_heldout_recording_v1',freeze_id=frozen['freeze_id'],study_approval=frozen['authorization'],preparation_authorization=frozen['authorization'],cache_contract='complete_team_independent_v1',randomness_control='Frozen temperature0.8; n5 existing sampler seeds0..4; no deterministic generation claim',execution_configuration_id=setup.resources.manifest_id,factory='app.benchmark.project_adapter:create_recording_verifiers',expected_setup=setup,final_test_reservation=read(a.frozen/a.cohort/'reservation.json'),permitted_datasets=(('final_test',read(a.frozen/a.cohort/'reservation.json')['dataset_id']),),candidates=read(a.source/a.cohort/'preparation.json')['candidates'],examples=sorted(payload,key=lambda e:e['example_id']))
        save(target/'request.json',request.model_dump(mode='json'))
        prior=()
        if a.resume_from:
            if module.validate_recording_request(read(a.resume_from/'request.json'))!=request:raise ValueError('resume request changed')
            prior=tuple(module.CollectedAttempt.model_validate_json(line) for line in (a.resume_from/'attempts.jsonl').read_text().splitlines() if line.strip())
            started={json.loads(line)['attempt_id'] for line in (a.resume_from/'started.jsonl').read_text().splitlines() if line.strip()}
            if started-{row.attempt_id for row in prior if row.executed}:raise ValueError('ambiguous in-flight attempts: no retry permitted')
        verifiers,actual,observer=create_recording_verifiers()
        if actual!=setup:raise ValueError('factory setup changed')
        save(target/'observed-setup.json',actual.model_dump(mode='json'))
        with (target/'attempts.jsonl').open('x',encoding='utf-8') as journal,(target/'started.jsonl').open('x',encoding='utf-8') as starts:
            for row in prior:
                if row.executed:starts.write(json.dumps(dict(attempt_id=row.attempt_id))+'\n')
            starts.flush();os.fsync(starts.fileno())
            def begin(identity):starts.write(json.dumps(dict(attempt_id=identity))+'\n');starts.flush();os.fsync(starts.fileno())
            def sink(row):journal.write(row.model_dump_json()+'\n');journal.flush();os.fsync(journal.fileno());print(a.cohort,len_done[0]+1,row.candidate,row.attempt.state,flush=True);len_done[0]+=1
            len_done=[0]
            bundle=module.collect(request,verifiers,actual,observer,sink=sink,completed=prior,on_start=begin)
        save(target/'recordings.json',bundle.model_dump(mode='json'));integrity=module.completeness(bundle);integrity['network_counts']=guard.counts;save(target/'collection-report.json',integrity)
        if not integrity['complete']:raise ValueError('collection integrity failed; preserve every journal and inspect before resume')
        print('COMPLETE',a.cohort,integrity['executed_calls'],guard.counts,flush=True)

if __name__=='__main__':main()
