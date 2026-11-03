"""Evaluate frozen candidates; never fits policies or updates reputation."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import numpy as np
from app.game.models import PlanningContext,Strategy,content_id,requirement_signature
from app.game.policy import Policy,validate_policy
from app.game.execution_contract import ExecutionContract
from app.game.offline.collection import RecordingBundle,completeness,HeldoutRecordingRequest,collection_plan
from app.game.offline.records import TrainingManifest,Example,Partition,DatasetManifest
from app.game.offline.attacks import AttackSpecification,enumerate_attacks
from app.game.offline.replay import replay,category_id
from app.game.offline.evaluation import summarize
from app.selection.requirements import requirement_inputs


def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def save(p,d):Path(p).write_text(json.dumps(d,indent=2,sort_keys=True)+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def validate_frozen_sources(freeze):
    for name,digest in freeze['source_hashes'].items():
        # The collector extension is separately sealed before collection. All
        # decision and other source files must still match their original freeze.
        if Path(name).as_posix()!='app/game/offline/collection.py' and sha(name)!=digest:
            raise ValueError('frozen decision/source code changed: '+name)


def export_final(bundle,context,reservation):
    bundle=RecordingBundle.model_validate(bundle)
    if not isinstance(bundle.request,HeldoutRecordingRequest) or not completeness(bundle)['complete']:
        raise ValueError('complete evaluation-only recordings required')
    lookup={(row.run_id,row.candidate):row.attempt for row in bundle.attempts}
    rows=[]
    for e in bundle.request.examples:
        plan=context.plan
        if (e.analysis.domain!=plan.domain or e.analysis.domain_status!=plan.domain_status
            or e.analysis.difficulty!=plan.difficulty or e.analysis.difficulty_score!=plan.difficulty_score
            or e.analysis.analysis_method!=plan.analysis_method
            or getattr(e.analysis.research_context,'context_version',None)!=plan.context_version
            or getattr(e.analysis.research_context,'scoring_version',None)!=plan.scoring_version
            or requirement_signature(requirement_inputs(e.analysis))!=context.requirement_signature
            or bool(e.reference and e.reference.strip())!=plan.reference_available):
            raise ValueError('final planning requirements/provenance differ from frozen context')
        targets={c.verifier_name:c for c in plan.candidates}
        captured=collection_plan(bundle.request,e)['candidates']
        if set(targets)!={c['verifier_name'] for c in captured}:raise ValueError('final candidate roster differs')
        for row in captured:
            target=targets[row['verifier_name']];cap=row['capabilities']
            if (target.eligible!=row['eligible'] or target.registered!=row['registered']
                or target.prerequisite_status!=row['prerequisite_status']
                or target.exclusion_reason!=row['exclusion_reason']
                or set(target.expected_capabilities)!=set(cap['expected_capabilities'])
                or target.requires_reference!=cap['requires_reference']
                or target.configured_readiness!=cap['readiness']
                or tuple(target.limitations)!=tuple(cap['limitations'])):
                raise ValueError('final candidate capabilities/prerequisites differ')
        rows.append(Example(example_id=e.example_id,split_identity=e.split_identity,question_id=e.question_id,
            question=e.question,answer=e.answer,reference=e.reference,domain=e.analysis.domain,
            planning_category=category_id(context),answer_is_correct=e.label.answer_is_correct,
            label_source=e.label.label_source,label_method=e.label.label_method,validation_id=e.run_id,
            execution_configuration_id=bundle.request.execution_configuration_id,cache_contract=bundle.request.cache_contract,
            attempts=tuple(lookup[e.run_id,c.verifier_name] for c in bundle.request.candidates)))
    return reservation.validate_payload(Partition(role='final_test',dataset_id=reservation.dataset_id,examples=rows))


def describe(outcomes,context):
    m=summarize(tuple((o,1.) for o in outcomes),context.loss_configuration);n=m.examples
    correct=sum(o.answer_is_correct for o in outcomes);incorrect=n-correct
    return dict(**m.model_dump(mode='json'),accepts=sum(o.public_status=='passed' for o in outcomes),rejects=sum(o.public_status=='failed' for o in outcomes),uncertainties=sum(o.public_status=='uncertain' for o in outcomes),decision_loss=m.validation_loss(context.loss_configuration),uncertainty_rate=m.uncertain/n,false_accept_rate_all=m.false_accept/n,false_reject_rate_all=m.false_reject/n,false_accept_rate_incorrect=m.false_accept/incorrect if incorrect else None,false_reject_rate_correct=m.false_reject/correct if correct else None,correct_examples=correct,incorrect_examples=incorrect,execution_failure_attempts=sum(state in {'failed','unavailable'} for o in outcomes for name,state in o.execution_states),cases_with_execution_failure=sum(any(state in {'failed','unavailable'} for name,state in o.execution_states) for o in outcomes),uncertainty_reasons=dict(Counter(r for o in outcomes if o.public_status=='uncertain' for r in o.reasons)),contributor_counts=dict(Counter(o.contributors for o in outcomes)))


def bootstrap(methods,examples):
    # Every resample preserves both answer variants and paired methods.
    groups=sorted({e.split_identity for e in examples});lookup={e.example_id:e.split_identity for e in examples}
    rng=np.random.default_rng(20261102);draws=rng.integers(0,len(groups),size=(10000,len(groups)))
    estimates={};result={}
    for name,outcomes in methods.items():
        grouped=[]
        for group in groups:
            rows=[o for o in outcomes if lookup[o.example_id]==group]
            grouped.append([len(rows),sum(o.public_status in {'passed','failed'} for o in rows),sum(o.public_status=='passed' and not o.answer_is_correct for o in rows),sum(o.public_status=='failed' and o.answer_is_correct for o in rows),sum(o.public_status=='uncertain' for o in rows),sum(o.answer_is_correct for o in rows),sum(not o.answer_is_correct for o in rows)])
        counts=np.asarray(grouped,dtype=float)[draws].sum(axis=1);n,dec,fa,fr,unc,correct,incorrect=counts.T
        measures=dict(coverage=dec/n,false_accept_rate_all=fa/n,false_reject_rate_all=fr/n,decision_loss=(fa+fr+.2*unc)/n,uncertainty_rate=unc/n)
        measures['false_accept_rate_incorrect']=np.divide(fa,incorrect,out=np.full_like(fa,np.nan),where=incorrect>0)
        measures['false_reject_rate_correct']=np.divide(fr,correct,out=np.full_like(fr,np.nan),where=correct>0)
        measures['selective_risk']=np.divide(fa+fr,dec,out=np.full_like(dec,np.nan),where=dec>0)
        estimates[name]=measures;result[name]={}
        for metric,values in measures.items():
            undefined=float(np.isnan(values).mean())
            result[name][metric]=dict(interval95=None if undefined else np.quantile(values,[.025,.975]).tolist(),undefined_resample_fraction=undefined)
    paired={}
    for other in ('development_best_fixed','coverage_aware_greedy'):
        paired['frozen_flexible-minus-'+other]={}
        for metric,values in estimates['frozen_flexible'].items():
            delta=values-estimates[other][metric];bad=float(np.isnan(delta).mean())
            paired['frozen_flexible-minus-'+other][metric]=dict(interval95=None if bad else np.quantile(delta,[.025,.975]).tolist(),undefined_resample_fraction=bad)
    return dict(method='10000 paired cluster bootstrap resamples of 20 groups; percentile intervals; seed20261102; not blinded; zero observed error can give degenerate intervals and is not a guarantee',methods=result,paired_differences=paired)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--source',type=Path,required=True);parser.add_argument('--frozen',type=Path,required=True);a=parser.parse_args()
    freeze=read(a.frozen/'freeze-manifest.json');seal=read(a.frozen/'precollection-seal.json')
    evaluation_seal=read(a.frozen/'evaluation-code-seal.json')
    if sha(__file__)!=evaluation_seal['evaluator_sha256']:raise ValueError('sealed evaluation code changed')
    for name,digest in freeze['source_hashes'].items():
        if name!='app/game/offline/collection.py' and sha(name)!=digest:raise ValueError('frozen decision/source code changed: '+name)
    for name,digest in seal['files'].items():
        if sha(name)!=digest:raise ValueError('precollection seal changed')
    for name,digest in freeze['frozen_file_hashes'].items():
        if sha(a.frozen/name)!=digest:raise ValueError('frozen files changed')
    report=[]
    for cohort in ('arithmetic','factual'):
        directory=a.frozen/cohort
        c=PlanningContext.model_validate(read(directory/'context.json'));k=ExecutionContract.model_validate(read(directory/'contract.json'))
        p=validate_policy(Policy.model_validate(read(directory/'policy.json')),c)
        expected=next(row for row in freeze['candidates'] if row['cohort']==cohort)
        if sha(a.source/cohort/'training-manifest.json')!=expected['training_sha256']:raise ValueError('frozen training bytes changed')
        m=TrainingManifest.model_validate(read(a.source/cohort/'training-manifest.json'))
        attacks=AttackSpecification.model_validate(read(directory/'attacks.json'))
        bundle=RecordingBundle.model_validate(read(directory/'collection/recordings.json'))
        if bundle.request.freeze_id!=freeze['freeze_id']:raise ValueError('collection freeze differs')
        final=export_final(bundle,c,m.final_test_reservation)
        DatasetManifest(version='released_flexible_heldout_v1',evidence_kind=m.evidence_kind,partitions=(*m.partitions,final))
        save(directory/'final-partition.json',final.model_dump(mode='json'))
        baselines=read(directory/'baselines.json');weights=dict(p.solution.probabilities)
        chosen=[s for s in p.strategies if weights[s.strategy_id]>0]
        if len(chosen)!=1 or weights[chosen[0].strategy_id]!=1.:raise ValueError('frozen evaluation expects the declared deterministic candidate')
        methods=dict(frozen_flexible=chosen[0],development_best_fixed=Strategy.model_validate(baselines['development_best']),coverage_aware_greedy=Strategy.model_validate(baselines['greedy']))
        actions=enumerate_attacks(c.dependencies,attacks);all_rows=[];metrics={};clean={}
        cache={}
        for method,strategy in methods.items():
            metrics[method]={}
            for action in actions:
                key=(strategy.strategy_id,action.attack_id)
                if key not in cache:cache[key]=[replay(c,strategy,action,attacks,k,e) for e in final.examples]
                rows=cache[key];metrics[method][action.kind]=describe(rows,c)
                if action.kind=='clean':clean[method]=rows
                all_rows.extend(dict(method=method,**o.model_dump(mode='json')) for o in rows)
        two=PlanningContext.model_validate(read(a.frozen.parent/'flexible-teams-v1'/(cohort+'-minimum-2')/'context.json'))
        two_contract=ExecutionContract.model_validate_json(two.execution_contract_json)
        ablation={}
        for action in actions:
            rows=[replay(two,methods['coverage_aware_greedy'],action,attacks,two_contract,e) for e in final.examples]
            ablation[action.kind]=describe(rows,two)
            all_rows.extend(dict(method='greedy_minimum_two_contract_ablation',**o.model_dump(mode='json')) for o in rows)
        costs={}
        for name in freeze['candidates'][0]['roster']:
            rows=[r for r in bundle.attempts if r.candidate==name and r.executed]
            durations=sorted(r.duration_ms for r in rows)
            costs[name]=dict(executed=len(rows),mean_ms=float(np.mean(durations)),p95_nearest_rank_ms=durations[int(np.ceil(.95*len(durations)))-1],includes_failures=True)
        development={}
        diagnostics=read(a.frozen.parent/'flexible-teams-v1'/(cohort+'-minimum-1')/'strategy-diagnostics.json')
        for method,strategy in methods.items():
            row=next(r for r in diagnostics if r['strategy']['strategy_id']==strategy.strategy_id)
            development[method]={key.split(':')[0]:cell['metrics'] for key,cell in row['attacks'].items()}
        result=dict(development_metrics=development,cohort=cohort,freeze_id=freeze['freeze_id'],policy_id=p.policy_id,final_partition_id=content_id(final.model_dump(mode='json')),collection_integrity=completeness(bundle),fixed_equals_flexible=baselines['fixed_equals_flexible'],metrics=metrics,minimum_two_fixed_greedy_ablation=ablation,team_size_probabilities={method:{str(size):float(len(s.verifiers)==size) for size in range(1,5)} for method,s in methods.items()},actual_selection_counts={method:{','.join(s.verifiers):len(final.examples)} for method,s in methods.items()},measured_attempt_costs=costs,cost_limitation='Full-roster individual call timings, excluding initialization. Not singleton end-to-end deployment latency.',bootstrap=bootstrap(clean,final.examples))
        save(directory/'heldout-results.json',result);save(directory/'replay-outcomes.json',all_rows);report.append(result)
        print('Evaluated',cohort,metrics['frozen_flexible']['clean'],flush=True)
    for path,digest in freeze['prior_artifact_hashes'].items():
        if sha(path)!=digest:raise ValueError('original development artifact changed')
    save(a.frozen/'heldout-results.json',dict(version='frozen_flexible_heldout_results_v1',freeze_id=freeze['freeze_id'],cohorts=report,prior_artifacts_unchanged=True,refitting_performed=False,reputation_updated=False,activated=False))
    write_report(a.frozen,freeze,report)

def write_report(directory,freeze,cohorts):
    lines=['# Frozen flexible-team held-out evaluation','',
        'Freeze ID: `'+freeze['freeze_id']+'`. Candidates, history, probabilities, thresholds, contributor/coverage contracts, budgets and attacks were frozen before opening test payloads or collecting reports.',
        '', 'Each cohort contains 40 examples in 20 paired groups (20 correct and 20 incorrect). TrainingManifest and released DatasetManifest enforce example, group, question, content and run exclusions. These are source-known procedural reservations, not blinded unseen-source tests. The prepared corpus already contains most retained test facts and permitted references were fixed before outcomes; this is not an unseen-document or reference-free test.',
        '', 'Methods: frozen flexible policy; development-best fixed strategy satisfying the same 90% development coverage floor and reliability-first ranking; existing coverage-aware selector initial team with reputation-weighted aggregation. All three use the matching minimum-one finalization and resources. Greedy is a complete-team selection baseline, not the legacy adaptive stopping pipeline.',
        '', 'Minimum-two is reported only as the same fixed greedy team finalized under its original minimum-two contract. All minimum-two fits were infeasible; no minimum-two policy/probabilities were fabricated.',
        '', 'FA/FR rates below divide by all 40 examples; conditional FA divides by the 20 incorrect examples and conditional FR by the 20 correct examples. Selective risk divides errors by decided cases and is undefined at zero coverage. Decision loss excludes cost and is (FA+FR+0.2*uncertain)/40.']
    for r in cohorts:
        lines+=['','## '+r['cohort'],'','Policy ID: `'+r['policy_id']+'`. Final partition ID: `'+r['final_partition_id']+'`.',
            '', 'Collection: '+str(r['collection_integrity']['executed_calls'])+' verifier calls; complete='+str(r['collection_integrity']['complete'])+'.',
            '', 'The fitted flexible policy equals the development-best fixed strategy: '+str(r['fixed_equals_flexible'])+'. This comparison shows equivalence, not a game-theory advantage.']
        for name,attacks in r['metrics'].items():
            m=attacks['clean'];d=r['development_metrics'][name]['clean']
            lines+=['',name+': accepts '+str(m['accepts'])+', rejects '+str(m['rejects'])+', uncertain '+str(m['uncertainties'])+'; coverage '+str(m['decision_coverage'])+'; FA '+str(m['false_accept'])+'/40, FR '+str(m['false_reject'])+'/40; conditional FA '+str(m['false_accept_rate_incorrect'])+', conditional FR '+str(m['false_reject_rate_correct'])+'; decision loss '+str(m['decision_loss'])+'; selective risk '+str(m['selective_risk'])+'.',
                'Development -> held-out coverage: '+str(d['decision_coverage'])+' -> '+str(m['decision_coverage'])+'; decision loss: '+str(d['decision_loss'])+' -> '+str(m['decision_loss'])+'.',
                'Selection counts (offline replay): '+str(r['actual_selection_counts'][name])+'. Size probabilities: '+str(r['team_size_probabilities'][name])+'. Historical selected-team cost estimate '+str(m['estimated_resource_cost'])+' ms.',
                'Selected failures/unavailable attempts: '+str(m['execution_failure_attempts'])+'; affected cases '+str(m['cases_with_execution_failure'])+'. Uncertainty reasons: '+str(m['uncertainty_reasons'])+'.',
                '95% paired-group bootstrap intervals (10000 resamples, seed20261102): '+json.dumps(r['bootstrap']['methods'][name],sort_keys=True)+'.']
        lines+=['','Paired flexible-minus-baseline intervals: '+json.dumps(r['bootstrap']['paired_differences'],sort_keys=True)+'.',
            '', 'Minimum-two fixed greedy contract ablation: '+json.dumps(r['minimum_two_fixed_greedy_ablation']['clean'],sort_keys=True)+'.',
            '', 'Measured individual call costs: '+json.dumps(r['measured_attempt_costs'],sort_keys=True)+'. Full-roster recording excludes initialization and resource-observer overhead from these call timers. It does not measure singleton deployment end-to-end latency.',
            '', 'Simulated report-level attacks (flexible candidate):']
        for attack,m in r['metrics']['frozen_flexible'].items():
            if attack=='clean':continue
            lines+=['- '+attack+': coverage '+str(m['decision_coverage'])+', FA '+str(m['false_accept'])+', FR '+str(m['false_reject'])+', uncertainty '+str(m['uncertainties'])+', decision loss '+str(m['decision_loss'])+', selective risk '+str(m['selective_risk'])+'.']
    lines+=['','## Interpretation and handoff','',
        'The 90% development constraint was not assumed to hold on test. Shared dependencies connect the declared failure group across selected verifiers: adding team members does not establish independent protection. Report corruption is simulated and is not an actual upstream compromise experiment.',
        '', 'Percentile bootstrap intervals preserve paired answers and paired methods. With only 20 source-known groups, zero observed errors can produce a degenerate zero-width interval; that is not a guarantee of zero population error. Results support only the narrow retained arithmetic/factual cohorts, with one local generation realization and the recorded corpus snapshot.',
        '', 'Recommendation: retain these as offline candidates and collect broader independently grouped and source-independent evidence before general adoption. A minimum-two contract can reduce decisions but its infeasible fit supplies no deployable fallback policy. This study does not establish minimax superiority or broad domain/difficulty adaptation.',
        '', 'Reproduce preparation with scripts.flexible_heldout, collection with scripts/collect_flexible_heldout.py from the resource-compatible original checkout, then evaluation with scripts.evaluate_flexible_heldout. All paths and exact IDs are in freeze-manifest.json, precollection-seal.json, per-cohort collector-provenance.json, and heldout-results.json. The final partitions remain evaluation-only: never pass them into fitting or reputation updates.',
        '', 'Later integration must keep each frozen policy/context/contract together, validate actual resource identity and explicitly review this limited evidence. No semantic cohort was collected. No policy was refitted, no reputation updated, and nothing committed, pushed, merged or activated.']
    (directory/'report.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')


if __name__=='__main__':main()
