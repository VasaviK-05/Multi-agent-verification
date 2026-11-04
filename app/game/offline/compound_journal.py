"""Fsynced journal/recovery wrapper over the existing collector, no inference logic."""
import json
import os
from pathlib import Path


def metadata_ceiling(prepared):
    # Existing collect observes every roster slot before planning, and observes
    # executed calls again afterward. Each service attestation uses two GETs.
    observations=sum(len(r.examples)*(len(r.candidates)+sum(c.registered for c in r.candidates)) for r in prepared.values())
    return 2*observations+32  # Fixed allowance for factory setup/attestation.


def record_requests(prepared,setup,verifiers,observer,directory,collector,*,resume_from=None):
    retained={}
    for cid,request in prepared.items():
        previous=()
        if resume_from is not None and (Path(resume_from)/cid).exists():
            prior=Path(resume_from)/cid
            CollectedAttempt=collector.CollectedAttempt
            validate_recording_request=collector.validate_recording_request
            if validate_recording_request(json.loads((prior/'request.json').read_text(encoding='utf-8')))!=request:raise ValueError('resume request differs')
            previous=tuple(CollectedAttempt.model_validate_json(line) for line in (prior/'attempts.jsonl').read_text(encoding='utf-8').splitlines())
            started={json.loads(line)['attempt_id'] for line in (prior/'started.jsonl').read_text(encoding='utf-8').splitlines()}
            if started-{a.attempt_id for a in previous if a.executed}:raise ValueError('ambiguous in-flight attempt; cannot retry')
            collector.RecordingBundle(request=request,observed_setup=setup,attempts=previous)
        retained[cid]=previous
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=False)
    bundles=[]
    for cid,request in prepared.items():
        previous=retained[cid]
        new_calls=[0]
        target=directory/cid;target.mkdir()
        (target/'request.json').write_text(request.model_dump_json(indent=2),encoding='utf-8')
        with (target/'started.jsonl').open('x',encoding='utf-8') as starts,(target/'attempts.jsonl').open('x',encoding='utf-8') as journal:
            for a in previous:
                if a.executed:starts.write(json.dumps(dict(attempt_id=a.attempt_id))+'\n')
            starts.flush();os.fsync(starts.fileno())
            def begin(identity):
                new_calls[0]+=1
                starts.write(json.dumps(dict(attempt_id=identity))+'\n');starts.flush();os.fsync(starts.fileno())
            def sink(attempt):
                journal.write(attempt.model_dump_json()+'\n');journal.flush();os.fsync(journal.fileno())
            active={c.verifier_name for c in request.candidates if c.registered}
            bundle=collector.collect(request,[v for v in verifiers if v.name in active],
                setup,observer,sink=sink,on_start=begin,completed=previous)
        (target/'bundle.json').write_text(bundle.model_dump_json(indent=2),encoding='utf-8')
        (target/'session-count.json').write_text(json.dumps(dict(new_invocations=new_calls[0],
            retained_executed_attempts=sum(a.executed for a in previous))),encoding='utf-8')
        bundles.append((cid,bundle))
    return tuple(bundles)
