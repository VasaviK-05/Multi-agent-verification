"""One authorized diagnostic pass, <=8 examples/16 attempts, no retries.

Run from the original resource-compatible checkout. Only the owned pure binding
adapter is loaded from this worktree; verifier implementations stay unchanged.
"""
import argparse
from dataclasses import asdict
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
from time import perf_counter


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--study',type=Path,required=True)
    parser.add_argument('--source',type=Path,required=True)
    args=parser.parse_args()
    sys.path.insert(0,str(Path.cwd()))
    read=lambda p:json.loads(Path(p).read_text(encoding='utf-8'))
    save=lambda p,v:Path(p).write_text(json.dumps(v,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    protocol=read(args.study/'protocol.json')
    for path,digest in protocol['sealed_inputs'].items():
        if hashlib.sha256(Path(path).read_bytes()).hexdigest()!=digest:
            raise ValueError('predeclared input changed: '+path)
    examples=read(args.study/'examples.json')  # Labels deliberately never loaded.
    if not 1<=len(examples)<=8 or len({e['example_id'] for e in examples})!=len(examples):
        raise ValueError('bounded unique smoke examples required')
    target=args.study/'live';target.mkdir(exist_ok=False)
    path=Path(__file__).resolve().parents[1]/'app/game/component_binding.py'
    spec=importlib.util.spec_from_file_location('owned_component_binding',path)
    binding=importlib.util.module_from_spec(spec);sys.modules[spec.name]=binding;spec.loader.exec_module(binding)
    # Validate ALL answers before initializing resources; every example has exactly two planned calls.
    prepared=[(e,binding.bind_answer(binding.question_plan(e['question']),e['answer'])) for e in examples]
    os.environ.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',
        NO_PROXY='localhost,127.0.0.1,::1',no_proxy='localhost,127.0.0.1,::1',
        VERIFIER_COLLECTION_ADAPTER_CONFIG=str((args.source/'adapter.json').resolve()))
    import requests
    from app.benchmark.project_adapter import AdapterConfiguration,inspect_setup,create_recording_verifiers
    from scripts.run_factual_diagnostic import NetworkBudget
    config=AdapterConfiguration.model_validate(read(args.source/'adapter.json'))
    preflight=inspect_setup(config);save(target/'resource-preflight.json',preflight)
    if not preflight['ready']:raise ValueError(preflight['blockers'])
    if preflight['observed_setup']['resources'] != protocol['expected_resources']:
        raise ValueError('resources differ from predeclared retained configuration')
    with (target/'network.jsonl').open('x',encoding='utf-8') as network:
        guard=NetworkBudget(config.ollama_url,network,generation_limit=0,metadata_limit=100)
        original=requests.Session.request
        requests.Session.request=lambda session,method,url,*a,**kw:guard.call(original,session,method,url,*a,**kw)
        pool,setup,observer=create_recording_verifiers()
        selected={v.name:v for v in pool if v.name in {'evidence','rule'}}
        if set(selected)!={'evidence','rule'}:raise ValueError('required verifier interfaces unavailable')
        before=observer.snapshot();save(target/'resources-before.json',before.model_dump(mode='json'))
        if before.model_dump(mode='json')!=protocol['expected_resources']:raise ValueError('resource mismatch')
        with (target/'started.jsonl').open('x',encoding='utf-8') as started, (target/'attempts.jsonl').open('x',encoding='utf-8') as journal:
            count=0
            for example,components in prepared:
                for component,name in zip(components,('evidence','rule')):
                    cid=binding.component_validation_id(example['example_id'],component)
                    event=dict(example_id=example['example_id'],verifier_name=name,
                        component=asdict(component),validation_id=cid,call_id=binding.digest([cid,name]))
                    started.write(json.dumps(event)+'\n');started.flush();os.fsync(started.fileno())
                    start=perf_counter()
                    try:
                        report=selected[name].verify(component.question,component.answer,example['reference'])
                    except Exception as exc:
                        event.update(state='failed',error_type=type(exc).__name__,error=str(exc))
                    else:
                        event.update(state='returned',report=report.model_dump(mode='json'))
                    event['elapsed_ms']=(perf_counter()-start)*1000
                    journal.write(json.dumps(event,allow_nan=False)+'\n');journal.flush();os.fsync(journal.fileno())
                    count+=1;print(count,example['example_id'],name,event['state'],flush=True)
        after=observer.snapshot();save(target/'resources-after.json',after.model_dump(mode='json'))
        save(target/'summary.json',dict(attempts=count,expected_attempts=2*len(examples),
            resources_unchanged=before==after,network_counts=guard.counts,
            execution_mode='diagnostic_no_policy',labels_dispatched=False,retries=0,
            verifier_source_root=str(Path.cwd()),binding_sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
        if count!=2*len(examples) or before!=after:raise ValueError('smoke incomplete or resource drift; preserve all journals')


if __name__=='__main__':main()
