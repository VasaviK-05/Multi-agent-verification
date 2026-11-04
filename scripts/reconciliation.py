"""Opt-in reconciliation CLI. Inspect/capture do not construct models or generate."""
import argparse
import json
import os
from pathlib import Path
import random
import subprocess
import time

BUNDLE_SHA256 = '3ab4040b7df7b86eaa0b914459429bceefb129790073b60657ceb54ebffad184'


def load_bundle():
    from app.benchmark.project_adapter import ROOT, file_digest
    from scripts.policy_package import load
    path = ROOT / 'reconciliation/policies.json'
    if file_digest(path) != BUNDLE_SHA256:
        raise ValueError('frozen policy bundle bytes differ')
    return load(path)


def configuration(path):
    from app.benchmark.project_adapter import AdapterConfiguration, read_json
    return AdapterConfiguration.model_validate(read_json(path))


def selector_for(pool):
    from app.selection.verifier_selector import VerifierSelector
    from app.selection.capabilities import BUILTIN_CAPABILITIES
    return VerifierSelector(verifiers=pool,capabilities={v.name:BUILTIN_CAPABILITIES[v.name] for v in pool})


def capture(config):
    from app.benchmark import project_adapter as a
    from app.game.offline.reconciled_resources import source_transition, inspect_required
    from urllib.parse import urlsplit, urlunsplit
    root = a.ROOT
    def git(*args):
        return subprocess.check_output(['git','-C',str(root),*args],text=True).rstrip('\r\n')
    url = urlsplit(git('remote','get-url','origin'))
    remote = urlunsplit((url.scheme, url.netloc.rsplit('@',1)[-1], url.path, '', ''))
    capsule = a.read_json(root / 'docs/policy-source-capsule-v2.json')
    files = set(capsule['target_files']) | {'app/game/component_execution.py', 'app/game/execution.py',
        'app/game/offline/reconciled_resources.py','app/game/offline/reference_compatibility.py',
        'app/game/question_routing.py','app/game/offline/recording_adapters.py','app/selection/verifier_selector.py'}
    result = dict(mode='metadata capture; no native inference or active-instance claim',
        checkout=str(root),head=git('rev-parse','HEAD'),branch=git('branch','--show-current'),remote=remote,
        dirty=git('status','--porcelain=v1'), source_hashes={p:a.file_digest(root/p) for p in sorted(files)},
        configuration=config.model_dump(mode='json'), verifier_attempts=0, confidence_generations=0)
    _,_,policy = load_bundle()
    try:
        historical, intermediate = source_transition(policy.policy_id,policy.contract.actual_resources,config,capsule)
        observed, relocation, _ = inspect_required(config,intermediate)
        result.update(historical_scope_id=historical.manifest_id,intermediate_manifest_id=intermediate.manifest_id,
            observed_manifest=observed.model_dump(mode='json'), relocation=relocation,resource_validation_passed=True)
    except (ValueError,OSError,TypeError) as exc:
        result.update(resource_validation_passed=False,resource_error=str(exc))
    result.update(policy_id=policy.policy_id,compound_contract_id=policy.contract.compatibility_id,bundle_sha256=BUNDLE_SHA256)
    result['model_files']={}
    for name in ('embedding_snapshot','nli_snapshot'):
        try:
            directory=a.local_path(getattr(config,name))
            result['model_files'][name]=[dict(path=p.relative_to(directory).as_posix(),sha256=a.file_digest(p),bytes=p.stat().st_size)
                for p in sorted(directory.rglob('*')) if p.is_file()]
        except (ValueError,OSError,TypeError) as exc:result['model_files'][name]=dict(error_type=type(exc).__name__)
    result['file_hashes']={}
    for name in ('corpus_path','index_receipt'):
        try:result['file_hashes'][name]=a.file_digest(a.local_path(getattr(config,name)))
        except (ValueError,OSError,TypeError) as exc:result['file_hashes'][name]=dict(error_type=type(exc).__name__)
    for name in ('faiss.index','chunks.json','manifest.json'):
        try:result['file_hashes'][name]=a.file_digest(a.local_path(config.index_dir)/name)
        except (ValueError,OSError,TypeError) as exc:result['file_hashes'][name]=dict(error_type=type(exc).__name__)
    try:result['service_metadata']=a.observe_service(config).model_dump(mode='json')
    except Exception as exc:result['service_metadata']=dict(error_type=type(exc).__name__)
    return result


def compound(config, out):
    # This plan is persisted before construction or inference. One try only.
    question='What is the population of Cameroon, and what is that population plus 1000? Give both values.'
    answer='{"base":"29879337","derived":"29880337"}'
    plan=dict(question=question,answer=answer,maximum_examples=1,maximum_native_attempts=2,
        maximum_generations=0,expected_obligations=['base_fact:evidence','derived_sum:rule'],
        expected_finalization='all component passes accept; failure rejects; abstention may remain uncertain')
    (out/'plan.json').write_text(json.dumps(plan,indent=2),encoding='utf-8')
    import requests
    def forbidden(*args,**kwargs):
        raise AssertionError('compound acceptance forbids all HTTP requests')
    requests.sessions.Session.request=forbidden
    from app.game.offline.reconciled_resources import create_scoped
    from app.selection.verifier_selector import VerifierSelector
    from app.selection.capabilities import BUILTIN_CAPABILITIES
    from app.models.schemas import ValidationRequest
    configuration,provider,policy=load_bundle()
    pool,observer=create_scoped(config,policy)
    selector=selector_for(pool)
    journal=[]
    # Wrap the two bound native verify methods only to persist starts/outcomes.
    # The observer sees and binds these exact wrappers before dispatch.
    for verifier in pool:
        native=verifier.verify
        def call(*args,_native=native,_name=verifier.name,**kwargs):
            event=dict(name=_name,state='started');journal.append(event)
            (out/'calls.json').write_text(json.dumps(journal,indent=2))
            if len(journal)>2:raise AssertionError('native attempt cap exceeded')
            try:
                report=_native(*args,**kwargs)
                event.update(state='returned',report=report.model_dump(mode='json'))
                return report
            except BaseException as exc:
                event.update(state='raised',error_type=type(exc).__name__);raise
            finally:
                (out/'calls.json').write_text(json.dumps(journal,indent=2))
        verifier.verify=call
    from app.game.offline.reconciled_resources import instance_settings
    observer.settings=instance_settings(pool)
    result=configuration.router().run(selector,ValidationRequest(question=question,answer=answer),
        'bounded-reconciliation-compound-v1',provider=provider,rng=random.Random(1103),resource_observer=observer)
    summary=result.summary
    complete=(summary.get('selection_status')=='selected' and len(summary.get('attempts',[]))==2
        and [v['component_id'] for v in summary.get('components',[])]==['base_fact','derived_sum']
        and all(v['state']=='returned' for v in journal) and len(journal)==2
        and not any('resource' in reason for reason in summary.get('override_reasons',[])))
    return dict(mode='native complete-policy acceptance; no API/DB persistence',complete=complete,
        public_status=result.public_status,summary=summary,native_attempts=len(journal),confidence_generations=0)


def reference(config):
    from app.game.offline.reference_compatibility import create_reference
    from app.selection.verifier_selector import VerifierSelector
    from app.selection.capabilities import BUILTIN_CAPABILITIES
    _,provider,_=load_bundle()
    artifact=next(v for v in provider.snapshot() if v.artifact_id=='ee32392c870fba30b08b4f7509af645019d9f8b92dc7c39bafeceb8207745c8f')
    pool,observer=create_reference(config,artifact)
    selector=selector_for(pool)
    before=observer.snapshot_for(selector); proof=observer.authorize_artifact(artifact,before)
    after=observer.snapshot_for(selector)
    return dict(mode='native reference construction/binding only',complete=before==after and proof==observer.last_proof,
        proof=proof,after_manifest_id=after.manifest_id,native_attempts=0,confidence_generations=0)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('action',choices=['inspect','capture','prepare-relocation','compound','reference'])
    p.add_argument('--configuration',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    args.output.mkdir(parents=True,exist_ok=False)
    os.environ.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',HF_HUB_DISABLE_TELEMETRY='1')
    result=dict(action=args.action,complete=False,native_attempts=0,confidence_generations=0)
    try:
        config=configuration(args.configuration)
        if args.action=='inspect':
            from app.game.offline.reconciled_resources import source_transition,inspect_required
            from app.benchmark import project_adapter as a
            _,_,policy=load_bundle();capsule=a.read_json(a.ROOT/'docs/policy-source-capsule-v2.json')
            historical,intermediate=source_transition(policy.policy_id,policy.contract.actual_resources,config,capsule)
            observed,proof,_=inspect_required(config,intermediate)
            result.update(complete=True,historical_scope_id=historical.manifest_id,
                intermediate_manifest_id=intermediate.manifest_id,observed_manifest_id=observed.manifest_id,relocation=proof)
        elif args.action=='capture':result.update(capture(config),complete=True)
        elif args.action=='prepare-relocation':
            from app.game.offline.reconciled_resources import prepare_relocation
            from app.benchmark.project_adapter import local_path
            if not config.resource_relocation_binding or local_path(config.resource_relocation_binding) != (args.output/'binding.json').resolve():
                raise ValueError('configure resource_relocation_binding to this fresh output/binding.json')
            _,_,policy=load_bundle();binding,proof=prepare_relocation(config,policy)
            (args.output/'binding.json').write_text(binding.model_dump_json(indent=2))
            result.update(complete=True,binding_id=binding.binding_id,relocation=proof)
        elif args.action=='compound':result.update(compound(config,args.output))
        else:result.update(reference(config))
    except BaseException as exc:
        result.update(error_type=type(exc).__name__,error=str(exc))
        calls=args.output/'calls.json'
        if calls.exists():result['native_attempts']=len(json.loads(calls.read_text()))
    (args.output/'result.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result,default=str))
    return 0 if result['complete'] else 2


if __name__=='__main__':raise SystemExit(main())
