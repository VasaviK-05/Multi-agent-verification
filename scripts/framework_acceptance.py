"""One fixed six-request/eight-call local campaign; no retries or generations."""
import argparse
import json
import os
from pathlib import Path
import random
import time

PLAN_ID='da850b53f862eb590b9dd3185da035f8aa9a95ec0a9fdcf286941a27856a3017'


def read_plan():
    from app.benchmark.project_adapter import ROOT,read_json
    from app.game.models import content_id
    plan=read_json(ROOT/'reconciliation/local-acceptance-plan-v1.json')
    if plan.get('plan_id')!=PLAN_ID or content_id({k:v for k,v in plan.items() if k!='plan_id'})!=PLAN_ID:
        raise ValueError('unreviewed native acceptance plan')
    if len(plan['requests'])!=6 or sum(r['expected_native_calls'] for r in plan['requests'])!=8:
        raise ValueError('native campaign cap differs')
    return plan


class Journal:
    def __init__(self,path):
        self.path=path;self.started=[];self.completed=[];self.request_id=None
        self.plan={r['request_id']:r for r in read_plan()['requests']}

    def append(self,event):
        with self.path.open('a',encoding='utf-8') as handle:
            handle.write(json.dumps(event,ensure_ascii=False)+'\n');handle.flush();os.fsync(handle.fileno())

    def instrument(self,native,category):
        original=native.verify
        def verify(*args,**kwargs):
            if len(self.started)>=8:raise AssertionError('native call budget exhausted before dispatch')
            request=self.plan.get(self.request_id)
            if request is None or request['category']!=category or native.name not in request['expected_team']:
                raise AssertionError('unplanned native dispatch blocked')
            if any(e['request_id']==self.request_id and e['verifier_name']==native.name for e in self.started):
                raise AssertionError('native duplicate/retry blocked before dispatch')
            limit={'arithmetic':2,'factual':2,'compound':4}[category]
            if sum(e['category']==category for e in self.started)>=limit:
                raise AssertionError('category native call budget exhausted')
            event=dict(event='started',call_number=len(self.started)+1,category=category,
                request_id=self.request_id,verifier_name=native.name,question=args[0],answer=args[1],
                reference=args[2] if len(args)>2 else kwargs.get('context'))
            self.started.append(event);self.append(event)
            before=time.perf_counter()
            try:
                report=original(*args,**kwargs)
                done=dict(event='completed',call_number=event['call_number'],category=category,
                    request_id=self.request_id,verifier_name=native.name,
                    duration_ms=(time.perf_counter()-before)*1000,report=report.model_dump(mode='json'))
                self.completed.append(done);self.append(done)
                return report
            except BaseException as exc:
                self.append(dict(event='raised',call_number=event['call_number'],error_type=type(exc).__name__,error=str(exc)))
                raise
        native.verify=verify


def validate_outcome(item,result,actual_calls):
    summary=result.summary
    if summary.get('selection_status')!='selected' or summary.get('team')!=item['expected_team']:
        return False,'routing/selection failed'
    if actual_calls!=item['expected_native_calls']:
        return False,'native dispatch count differs'
    attempts=summary.get('attempts',[])
    if len(attempts)!=actual_calls or any(a['state'] not in {'directional','abstention'} for a in attempts):
        return False,'incomplete verifier execution'
    if any('resource' in r for r in summary.get('override_reasons',[])):
        return False,'resource/instance drift'
    if item['category']=='compound':
        if [c['component_id'] for c in summary.get('components',[])]!=['base_fact','derived_sum']:
            return False,'component identity differs'
        if summary.get('resource_compatibility')!=summary.get('resource_compatibility_after'):
            return False,'compound proof drift'
    elif summary.get('singleton_resource_compatibility')!=summary.get('singleton_resource_compatibility_after'):
        return False,'singleton proof drift'
    expected='passed' if item['label']['answer_is_correct'] else 'failed'
    if result.public_status not in {expected,'uncertain'}:
        return False,'directional outcome disagrees with independent label'
    if result.public_status=='uncertain':
        return True,'legitimate unresolved/abstaining result; inspect retained coverage and reasons'
    if item['category']=='compound':
        if any(c.get('unresolved') for c in summary['components']):return False,'missing required component coverage'
    elif summary.get('unresolved'):return False,'missing required coverage'
    return True,'complete expected directional decision'


def run(configuration,out):
    from scripts.reconciliation import load_bundle,selector_for
    from app.game.offline.singleton_compatibility import create_singleton,settings
    from app.game.offline.reconciled_resources import create_scoped,instance_settings
    from app.models.schemas import ValidationRequest
    plan=read_plan()
    (out/'plan.json').write_text(json.dumps(plan,indent=2),encoding='utf-8')
    import requests
    def forbidden(*args,**kwargs):raise AssertionError('campaign forbids every HTTP/service request')
    requests.sessions.Session.request=forbidden
    routes,provider,compound=load_bundle()
    journal=Journal(out/'calls.jsonl')
    result=dict(version='bounded_framework_acceptance_result_v1',plan_id=PLAN_ID,requests=[],
        maximum_native_calls=8,confidence_generations=0,retries=0,complete=False)
    (out/'result.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    pools={}
    try:
        # Construct/bind all three native contexts before ANY verifier attempt.
        for index,category in enumerate(('arithmetic','factual')):
            selector,observer=create_singleton(configuration,provider.snapshot()[index])
            journal.instrument(observer.native,category)
            observer.settings=settings(observer.native)
            observer.snapshot_for(selector)
            pools[category]=(selector,observer)
        pool,observer=create_scoped(configuration,compound)
        for native in pool:journal.instrument(native,'compound')
        observer.settings=instance_settings(pool)
        selector=selector_for(pool);observer.snapshot_for(selector)
        pools['compound']=(selector,observer)
        # Validate route signatures and answer binding for the entire fixed plan.
        for item in plan['requests']:
            kind,_,resolved=routes.router().resolve(item['question'],item['reference'])
            if resolved is None or kind!=('component' if item['category']=='compound' else 'atomic'):
                raise ValueError('fixed acceptance request is outside its original route')
            if kind=='component':
                from app.game.component_execution import bind_contract
                bind_contract(compound.contract,item['question'],item['answer'],item['reference'])
            else:
                from app.game.frozen_planning import frozen_selector
                from app.game.models import capture_context
                artifact=provider.snapshot()[0 if item['category']=='arithmetic' else 1]
                selector,_=pools[item['category']]
                values=artifact.context.model_dump(exclude={'selection_json','analyzer_provenance'})
                captured=capture_context(frozen_selector(selector,artifact.context),resolved[1],context=item['reference'],**values)
                if captured.compatibility_id!=artifact.context.compatibility_id:
                    raise ValueError('native singleton planning context differs before execution')
        for item in plan['requests']:
            selector,observer=pools[item['category']]
            journal.request_id=item['request_id'];before=len(journal.started)
            execution=routes.router().run(selector,ValidationRequest(question=item['question'],answer=item['answer'],context=item['reference']),
                'native-acceptance-'+item['request_id'],provider=provider,rng=random.Random(1103),resource_observer=observer)
            count=len(journal.started)-before
            valid,explanation=validate_outcome(item,execution,count)
            row=dict(request_id=item['request_id'],category=item['category'],public_status=execution.public_status,
                expected_label=item['label']['answer_is_correct'],native_calls=count,valid_execution=valid,
                explanation=explanation,summary=execution.summary)
            result['requests'].append(row)
            (out/'result.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
            # No retries or adaptive replacement. Retain all six planned outcomes.
        result['complete']=len(result['requests'])==6 and all(r['valid_execution'] for r in result['requests'])
    except BaseException as exc:
        result.update(error_type=type(exc).__name__,error=str(exc))
    finally:
        result.update(native_calls_started=len(journal.started),native_calls_completed=len(journal.completed))
        (out/'result.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--configuration',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    args=p.parse_args();args.output.mkdir(parents=True,exist_ok=False)
    os.environ.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',HF_HUB_DISABLE_TELEMETRY='1')
    from scripts.reconciliation import configuration
    result=run(configuration(args.configuration),args.output)
    print(json.dumps({k:v for k,v in result.items() if k!='requests'}))
    return 0 if result['complete'] else 2


if __name__=='__main__':raise SystemExit(main())
