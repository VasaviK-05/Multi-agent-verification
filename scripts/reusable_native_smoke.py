"""Prepare sealed native smoke plans; execution requires a separate explicit flag.

No API/DB deployment, fitting, downloads, index rebuilds or service changes.
`prepare` constructs no verifier. `execute` must be separately approved by owner.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import random
import sys

ROOT=Path(__file__).resolve().parents[1]


def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def is_non_rule_native_call(frame,event):
    # Teardown may clear module globals. Unknown frames must not crash the
    # profiler while preserving the restriction for identified native verifiers.
    module=frame.f_globals.get('__name__')
    return (event=='call' and isinstance(module,str) and module.startswith('app.verifiers.')
        and module not in {'app.verifiers.rule_verifier','app.verifiers.base_verifier'}
        and frame.f_code.co_name in {'__init__','verify'})


def make_rule_native_boundary(reject):
    def boundary(frame,event,arg,_check=is_non_rule_native_call,_reject=reject):
        if _check(frame,event):
            _reject('non-Rule verifier construction/execution forbidden')
    return boundary


def enforce_output_only(event,args,output,violation):
    """Reject process launches and filesystem mutations outside the run receipt."""
    def writable(path):
        if not isinstance(path,(str,bytes,os.PathLike)):
            violation('unapproved file descriptor mutation')
        p=Path(os.fsdecode(path)).resolve()
        if p!=output and not p.is_relative_to(output):
            violation('write outside approved output directory')
    if event in {'subprocess.Popen','os.system','os.posix_spawn','os.fork','os.exec','pty.spawn'}:
        violation('child processes forbidden')
    if event=='open':
        path,mode,flags=args
        if ((isinstance(mode,str) and any(c in mode for c in 'wax+'))
            or (isinstance(flags,int) and flags & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC))):
            writable(path)
    if event in {'os.remove','os.rmdir','os.mkdir','os.chmod','os.chown','os.truncate','os.utime'}:
        writable(args[0])
    if event in {'os.rename','os.link','os.symlink'}:
        writable(args[0]);writable(args[1])


def source_inventory():
    paths=list((ROOT/'app').rglob('*.py'))+[Path(__file__).resolve()]
    return {p.relative_to(ROOT).as_posix():digest(p) for p in sorted(paths)}


def native_configuration(kind,path):
    from app.benchmark.project_adapter import AdapterConfiguration
    from app.game.offline.reconciled_resources import OLD_CONFIGURATION
    if path:return AdapterConfiguration.model_validate_json(Path(path).read_text()).model_dump(mode='json')
    if kind=='arithmetic':
        return AdapterConfiguration(**OLD_CONFIGURATION,embedding_snapshot=None,nli_snapshot=None,
            index_receipt=None,service_observation=None,resource_relocation_binding=None).model_dump(mode='json')
    return None


def prepare(output,evidence_configuration=None,reference_configuration=None):
    from decimal import Decimal
    from fractions import Fraction
    from app.game.models import content_id,capture_context
    from app.game.frozen_planning import frozen_selector
    from app.game.reusable_policy import ReusablePolicyScope,ReusablePolicyGameRuntime
    from app.selection.verifier_selector import VerifierSelector
    from app.selection.capabilities import BUILTIN_CAPABILITIES
    from scripts.reconciliation import load_bundle
    from app.game.offline.singleton_compatibility import transition,observe
    from app.benchmark.project_adapter import AdapterConfiguration,local_path
    assert str(Fraction(4)+Fraction(4))==str(Decimal('4')+Decimal('4'))=='8'
    output=Path(output);output.mkdir(parents=True,exist_ok=False)
    cfg,provider,_=load_bundle(); artifacts=provider.snapshot()
    cases={
        'arithmetic':[dict(question='What is 4 + 4?',answer='8',context='8',expected_public_status='passed'),
                      dict(question='What is 4 + 4?',answer='9',context='8',expected_public_status='failed')],
        'evidence':[dict(question='what is the population of Belgium?',answer='The population of Belgium is 11941781.',
                         context='The population of Belgium is 11941781.',expected_public_status='passed')],
        'reference':[dict(question='Paraphrase this reference: Mira delivered twelve parcels to Noor.',
            answer='Twelve parcels were delivered to Noor by Mira.',context='Mira delivered twelve parcels to Noor.',expected_public_status=None)]}
    configurations={'arithmetic':None,'evidence':evidence_configuration,'reference':reference_configuration}
    summaries=[]
    for index,kind in enumerate(('arithmetic','evidence','reference')):
        artifact=artifacts[index];scope=ReusablePolicyScope(artifact_id=artifact.artifact_id,
            compatibility_id=artifact.context.compatibility_id,question_rules_version=json.loads(artifact.context.task_conditioning_json)['identity']['question_rules_version'],
            question_pattern=r'.+',maximum_question_chars=300,
            review_basis='Proposed bounded native readiness smoke only; execution approval and independent certification not supplied')
        runtime=ReusablePolicyGameRuntime([artifact],[scope],rng=random.Random(1103),resource_observer=None)
        configuration=native_configuration(kind,configurations[kind]);blockers=[];compatibility=[]
        for case in cases[kind]:
            assert case['question'] not in cfg.allowlist,'smoke must be outside historical exact allowlist'
            resolved,failed=runtime.resolve(case['question'],case['context'])
            if resolved is None:raise ValueError(str(failed.summary))
            analysis=resolved[3]
            # Metadata-only full-roster planning, not a native pool or fake report.
            captured=capture_context(frozen_selector(VerifierSelector(capabilities=BUILTIN_CAPABILITIES),artifact.context),analysis,context=case['context'],
                **artifact.context.model_dump(exclude={'selection_json','analyzer_provenance'}))
            compatibility.append(captured.compatibility_id==artifact.context.compatibility_id)
        if not all(compatibility):raise ValueError('prepared question differs from real fitted compatibility')
        if kind=='arithmetic':
            binding,_,intermediate=transition(artifact,AdapterConfiguration.model_validate(configuration))
            observed,_,_=observe(AdapterConfiguration.model_validate(configuration),intermediate,binding['selected'])
            resource_check=dict(mode='source/configuration hashes only; no native instance constructed',observed_manifest_id=observed.manifest_id)
        else:
            resource_check=dict(mode='local path presence only; model/index/service identities NOT attested')
            if configuration is None:blockers.append('approved route-specific native configuration absent')
            else:
                for field in ('embedding_snapshot','nli_snapshot','corpus_path','index_dir','index_receipt'):
                    value=configuration.get(field)
                    if not value or not local_path(value).exists():blockers.append('missing '+field)
            blockers.append('exact native resource/instance attestation pending execution approval')
        reference_receipt=(dict(method='independent Fraction and Decimal exact arithmetic, computed before candidates',value='8',candidate_independent=True)
            if kind=='arithmetic' else dict(method='pinned source-snapshot fact, not current-population claim',
                source='reconciliation/local-acceptance-plan-v1.json',source_sha256=digest(ROOT/'reconciliation/local-acceptance-plan-v1.json'),
                corpus_sha256='28e6241079b1afab419ebdbaea580510796c648d1855dcc91759ab3d8950b95a',source_value=11941781,
                actual_corpus_row_confirmation_pending=True) if kind=='evidence' else
                dict(method='explicit supplied fictional comparison reference; no world-truth claim',value=cases[kind][0]['context']))
        plan=dict(version='reusable_native_readiness_smoke_v1',kind=kind,artifact_id=artifact.artifact_id,
            policy_id=artifact.policy.policy_id,policy_version=artifact.policy.version,compatibility_id=artifact.context.compatibility_id,
            probabilities=artifact.policy.solution.probabilities,strategies=[s.model_dump(mode='json') for s in artifact.policy.strategies],
            original_resource_manifest_id=artifact.contract.resource_manifest.manifest_id,budget=artifact.context.budget,
            cost_units=artifact.context.cost_units,scope=scope.model_dump(mode='json'),configuration=configuration,
            requests=cases[kind],reference_receipt=reference_receipt,seed=1103,
            maximum_native_attempts=2 if kind!='evidence' else 1,maximum_generations=5 if kind=='reference' else 0,
            maximum_metadata_requests=20 if kind=='reference' else 0,maximum_wall_seconds=600 if kind=='reference' else 120,
            allowed_native_names=['confidence','semantic'] if kind=='reference' else ['rule'] if kind=='arithmetic' else ['evidence'],
            resource_preparation=resource_check,blockers=blockers,source_files=source_inventory(),
            bundle_sha256=digest(ROOT/'reconciliation/policies.json'),execution_authorized=False)
        plan['plan_id']=content_id(plan)
        path=output/(kind+'.json');path.write_text(json.dumps(plan,indent=2))
        summaries.append(dict(kind=kind,plan_id=plan['plan_id'],path=str(path),blockers=blockers))
    (output/'summary.json').write_text(json.dumps(summaries,indent=2))
    return summaries


class NativeJournal:
    def __init__(self,output,plan):self.output,self.plan,self.starts,self.ends,self.current=output,plan,[],[],None
    def append(self,event):
        with (self.output/'native-calls.jsonl').open('a') as stream:
            stream.write(json.dumps(event)+'\n');stream.flush();os.fsync(stream.fileno())
    def set_plan(self,selected):
        strategy=next((s for s in self.plan['strategies'] if s['strategy_id']==selected['strategy_id']),None)
        if (selected['artifact_id']!=self.plan['artifact_id'] or selected['policy_id']!=self.plan['policy_id']
            or strategy is None or dict(self.plan['probabilities']).get(selected['strategy_id'],0)<=0
            or selected['team']!=strategy['verifiers'] or selected['aggregation']!=strategy['aggregation']):
            raise ValueError('selected team differs from unchanged fitted distribution')
        self.team=selected['team'];self.append(dict(event='selection',selection=selected))
    def start_attempt(self,**kwargs):
        name=kwargs['verifier_name'];identity=(self.current,name)
        if (len(self.starts)>=self.plan['maximum_native_attempts'] or name not in self.plan['allowed_native_names']
            or name not in self.team or identity in self.starts):raise ValueError('unplanned native call/retry blocked')
        attempt=dict(attempt_id=str(len(self.starts)+1),request_index=self.current,verifier_name=name)
        self.starts.append(identity);self.append(dict(event='started',request=self.plan['requests'][self.current],**attempt));return attempt
    def complete_attempt(self,attempt,**kwargs):self.ends.append(attempt);self.append(dict(event='completed',attempt=attempt,**kwargs))
    def failed_attempt(self,attempt,**kwargs):self.append(dict(event='failed',attempt=attempt,error=str(kwargs)))
    def unavailable_attempt(self,attempt,**kwargs):self.append(dict(event='unavailable',attempt=attempt,reason=str(kwargs)))


def execute(plan_path,expected_id,output,approved=False):
    if not approved:raise ValueError('native execution requires separate explicit owner approval')
    sys.dont_write_bytecode=True
    import signal
    from urllib.parse import urlsplit
    from app.game.models import content_id
    plan=json.loads(Path(plan_path).read_text());provided=plan.pop('plan_id')
    if provided!=expected_id or content_id(plan)!=expected_id:raise ValueError('approved plan bytes differ')
    if plan['source_files']!=source_inventory() or plan['bundle_sha256']!=digest(ROOT/'reconciliation/policies.json'):
        raise ValueError('reviewed source/bundle changed; prepare and review a new plan')
    if plan['configuration'] is None:raise ValueError('approved native configuration required; no downloads or substitutes')
    output=Path(output).resolve();output.mkdir(parents=True,exist_ok=False)
    (output/'plan.json').write_text(json.dumps(dict(plan,plan_id=provided),indent=2))
    journal=NativeJournal(output,plan);result=dict(plan_id=provided,native_smoke_complete=False,requests=[],generations=0,metadata_requests=0)
    # Whole-process time bound, not an early successful selected-team decision.
    class SmokeDeadline(BaseException):pass
    signal.signal(signal.SIGALRM,lambda *args: (_ for _ in ()).throw(SmokeDeadline('native smoke outer deadline')))
    signal.alarm(plan['maximum_wall_seconds'])
    import requests
    original=requests.sessions.Session.request
    def violation(reason):
        result['guard_violation']=reason
        raise RuntimeError(reason)
    cfg=plan['configuration'];url=cfg['ollama_url'];base=url.rsplit('/api/generate',1)[0]
    def http(session,method,address,**kwargs):
        if plan['kind']!='reference':violation('native smoke forbids HTTP')
        if method.upper()=='POST' and address==url:
            if result['generations']>=plan['maximum_generations']:violation('generation cap reached')
            from app.verifiers.self_consistency import SHORT_ANSWER_PROMPT
            body=kwargs.get('json',{})
            if body.get('model')!=cfg['ollama_model'] or body.get('prompt')!=SHORT_ANSWER_PROMPT.format(question=plan['requests'][journal.current]['question'].strip()):
                violation('unapproved model/prompt')
            result['generations']+=1
        elif method.upper()=='GET' and address in {base+'/api/version',base+'/api/tags'}:
            if result['metadata_requests']>=plan['maximum_metadata_requests']:violation('metadata request cap reached')
            result['metadata_requests']+=1
        else:violation('HTTP outside exact frozen service contract')
        return original(session,method,address,**kwargs)
    requests.sessions.Session.request=http
    def audit(event,args):
        enforce_output_only(event,args,output,violation)
        if event in {'socket.connect','socket.getaddrinfo'}:
            target=args[1] if event=='socket.connect' else args
            if (plan['kind']!='reference' or not isinstance(target,tuple) or target[0] not in {'localhost','127.0.0.1','::1'}
                or target[1]!=(urlsplit(url).port or 80)):violation('non-approved network target')
        if event=='open':
            path,mode,flags=args
            if isinstance(path,(str,bytes,os.PathLike)) and ((isinstance(mode,str) and any(c in mode for c in 'wax+')) or flags & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC)):
                p=Path(path).resolve();protected=[ROOT/'artifacts',ROOT/'reconciliation']
                protected += [Path(value).resolve() if Path(value).is_absolute() else (ROOT/value).resolve() for key,value in cfg.items()
                    if key in {'corpus_path','index_dir','embedding_snapshot','nli_snapshot','index_receipt'} and value]
                if any(p==v or p.is_relative_to(v) for v in protected):violation('historical resource write forbidden')
    sys.addaudithook(audit)
    if plan['kind']=='arithmetic':
        sys.setprofile(make_rule_native_boundary(violation))
    import app.game.solver as solver, app.game.policy as policy
    import app.game.offline.evaluation as fitting
    from app.selection.verifier_selector import VerifierSelector
    def forbidden(*args,**kwargs):
        result['forbidden_action_attempted']=True
        raise RuntimeError('fitting/greedy substitution forbidden')
    solver.solve_minimax=policy.solve_minimax=policy.build_policy=fitting.fit_policy=forbidden
    VerifierSelector.select=VerifierSelector.iter_ranked=forbidden
    try:
        from app.benchmark.project_adapter import AdapterConfiguration
        from scripts.reconciliation import load_bundle,selector_for
        from app.game.reusable_policy import ReusablePolicyScope,ReusablePolicyGameRuntime
        from app.models.schemas import ValidationRequest
        _,provider,_=load_bundle();artifact=next(a for a in provider.snapshot() if a.artifact_id==plan['artifact_id'])
        configuration=AdapterConfiguration.model_validate(cfg)
        if plan['kind']=='reference':
            from app.game.offline.reference_compatibility import create_reference
            pool,observer=create_reference(configuration,artifact);selector=selector_for(pool)
        else:
            from app.game.offline.singleton_compatibility import create_singleton
            selector,observer=create_singleton(configuration,artifact)
        runtime=ReusablePolicyGameRuntime([artifact],[ReusablePolicyScope.model_validate(plan['scope'])],rng=random.Random(plan['seed']),resource_observer=observer)
        for i,case in enumerate(plan['requests']):
            journal.current=i
            run=runtime.run(selector,None,ValidationRequest(**{k:case[k] for k in ('question','answer','context')}),
                'native-reuse-smoke-'+str(i),execution_journal=journal)
            result['requests'].append(dict(public_status=run.public_status,summary=run.summary))
        result['native_smoke_complete']=(not result.get('guard_violation') and not result.get('forbidden_action_attempted')
            and len(journal.starts)==len(journal.ends)>0 and all(
            r['summary'].get('selection_status')=='selected' and r['summary'].get('termination')=='complete_selected_team'
            and not any('resource' in reason for reason in r['summary'].get('override_reasons',[])) for r in result['requests']))
        result['policy_identity_preserved']=all(r['summary'].get('policy_id')==plan['policy_id']
            and r['summary'].get('artifact_id')==plan['artifact_id']
            and r['summary'].get('fitted_compatibility_id')==plan['compatibility_id']
            and r['summary'].get('fitted_policy_version')==plan['policy_version']
            and [list(row) for row in r['summary'].get('fitted_strategy_probabilities',[])]==plan['probabilities']
            for r in result['requests'])
        result['coverage_and_contributors_ready']=all(not r['summary'].get('unresolved')
            and r['summary'].get('contributors',0)>=r['summary'].get('minimum_contributors',1) for r in result['requests'])
        result['expected_decisions_observed']=all(case['expected_public_status'] is None or case['expected_public_status']==row['public_status']
            for case,row in zip(plan['requests'],result['requests']))
    except BaseException as exc:result.update(error_type=type(exc).__name__,error=str(exc))
    finally:
        signal.alarm(0);result.update(native_starts=len(journal.starts),native_completions=len(journal.ends))
        (output/'result.json').write_text(json.dumps(result,indent=2))
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='action',required=True)
    p=sub.add_parser('prepare');p.add_argument('--output',type=Path,required=True)
    p.add_argument('--evidence-configuration',type=Path);p.add_argument('--reference-configuration',type=Path)
    p=sub.add_parser('execute');p.add_argument('--plan',type=Path,required=True);p.add_argument('--plan-id',required=True)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--execute-approved',action='store_true')
    args=parser.parse_args()
    if args.action=='prepare':print(json.dumps(prepare(args.output,args.evidence_configuration,args.reference_configuration),indent=2));return 0
    result=execute(args.plan,args.plan_id,args.output,args.execute_approved)
    print(json.dumps(result,indent=2))
    return 0 if result.get('native_smoke_complete') and result.get('policy_identity_preserved') and result.get('expected_decisions_observed') else 1


if __name__=='__main__':raise SystemExit(main())
