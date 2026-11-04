"""Descriptive full-team replay of fixed capability probes. No fitting or oracle routing."""
import argparse
from collections import Counter,defaultdict
from dataclasses import asdict
from itertools import combinations
import hashlib
import json
from pathlib import Path
from app.analysis.models import QuestionAnalysis
from pydantic import TypeAdapter
from app.game.models import PlanningContext,capture_context,canonical_json
from app.game.execution_contract import ExecutionContract,TeamRequirements
from app.game.frozen_planning import FrozenPlanningReputation
from app.game.strategies import enumerate_strategies
from app.game.finalization import finalize_decision,informative_contributor_count
from app.game.decision_inputs import FrozenReputationSnapshot
from app.game.offline.collection import RecordingBundle,completeness,DiagnosticRecordingRequest
from app.decision.coverage import task_capabilities
from app.decision.decision_engine import DecisionEngine
from app.decision.vote_normalization import is_abstention
from app.selection.verifier_selector import VerifierSelector
from app.selection.capabilities import BUILTIN_CAPABILITIES
from app.verifiers.base_verifier import BaseVerifier


def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,d):Path(p).write_text(json.dumps(d,indent=2,sort_keys=True)+'\n',encoding='utf-8')


class PlanningHandle(BaseVerifier):
    def __init__(self,name):self._name=name
    @property
    def name(self):return self._name
    def verify(self,*args,**kwargs):raise AssertionError('No verifier inference during team evaluation')


def diagnostic_context(source,family,analysis,reference,resource_id):
    # A fixed historical-weight scenario, not a compatible fitted policy for new questions.
    base=PlanningContext.model_validate(read(source/family/'source-context.json'))
    if analysis.domain!=base.plan.domain:raise ValueError('No task-family snapshot for this subject domain')
    names=[r.verifier_name for r in base.plan.candidates]
    selector=VerifierSelector(verifiers=[PlanningHandle(n) for n in names],reputation_manager=FrozenPlanningReputation(base),capabilities={n:BUILTIN_CAPABILITIES[n] for n in names})
    old=ExecutionContract.model_validate_json(base.execution_contract_json)
    contract=ExecutionContract(**{**old.model_dump(),'team_requirements':TeamRequirements(minimum_selected=1,minimum_informative=1)})
    if contract.execution_configuration_id!=resource_id:raise ValueError('Recorded resources differ from historical-weight scenario')
    data=base.model_dump(exclude={'selection_json','analyzer_provenance'})
    data.update(offline_evaluation_id=None,execution_contract_json=contract.model_dump_json(),pooling_contract_json=None,clean_coverage_json=None,reliability_first_json=None,task_conditioning_json=None)
    context=capture_context(selector,analysis,context=reference,**data)
    assert context.reputation_snapshot_id==base.reputation_snapshot_id
    return context,contract,base


def loss(status,correct):
    return .2 if status=='uncertain' else float((status=='passed')!=correct)


def metrics(rows):
    n=len(rows);decided=sum(r['status']!='uncertain' for r in rows)
    fa=sum(r['status']=='passed' and not r['answer_is_correct'] for r in rows)
    fr=sum(r['status']=='failed' and r['answer_is_correct'] for r in rows)
    return dict(examples=n,accepts=sum(r['status']=='passed' for r in rows),rejects=sum(r['status']=='failed' for r in rows),uncertain=n-decided,coverage=decided/n,false_accept=fa,false_reject=fr,decision_loss=sum(r['loss'] for r in rows)/n,selective_risk=(fa+fr)/decided if decided else None,estimated_team_cost_ms=rows[0]['estimated_cost_ms'],uncertainty_reasons=dict(Counter(reason for r in rows for reason in r['reasons'])),context_ids=sorted({r['context_id'] for r in rows}))


def evaluate(study,source):
    protocol=read(study/'protocol.json')
    for path,digest in read('artifacts/flexible-teams-v1/input-hashes.json').items():
        if sha(path)!=digest:raise ValueError('Original task-family history/context input changed: '+path)
    for path,digest in protocol['prior_artifact_hashes'].items():
        if sha(path)!=digest:raise ValueError('Prior frozen artifact changed: '+path)
    for path,digest in read(study/'pre-execution-seal.json')['files'].items():
        if sha(path)!=digest:raise ValueError('Predeclared probe inputs/collector changed')
    bundle=RecordingBundle.model_validate(read(study/'collection/recordings.json'))
    if not isinstance(bundle.request,DiagnosticRecordingRequest) or not completeness(bundle)['complete']:raise ValueError('Complete diagnostic-only bundle required')
    labels=read(study/'labels.json');groups={g['group_id']:g for g in read(study/'groups.json')}
    lookup={(r.run_id,r.candidate):r for r in bundle.attempts}
    outcomes=[];individuals=[];blocked=[];contexts={};enumerations={};additions=[]
    for e in bundle.request.examples:
        gold=labels[e.example_id];family=gold['family'];group=groups[gold['group_id']]
        # Mixed has no compatible history. A factual snapshot is used solely to
        # construct the blocked expected-capability audit; no mixed verdict is scored.
        context,contract,base=diagnostic_context(source,'factual' if family=='mixed' else family,e.analysis,e.reference,bundle.request.execution_configuration_id)
        contexts[e.example_id]=context.model_dump(mode='json');enum=enumerate_strategies(context);enumerations[e.example_id]=enum.model_dump(mode='json')
        required=tuple(gold['required_checks']);attempts={c.verifier_name:lookup[e.run_id,c.verifier_name].attempt for c in bundle.request.candidates}
        for name,attempt in attempts.items():
            row=attempt.report;recorded=lookup[e.run_id,name]
            record=dict(example_id=e.example_id,group_id=gold['group_id'],family=family,verifier=name,answer_is_correct=gold['answer_is_correct'],state=attempt.state,duration_ms=recorded.duration_ms,required=required,achieved=sorted(task_capabilities(row,requirements=required,reference_available=bool(e.reference))) if row else [],informative_in_frozen_family_scenario=None)
            if row is not None:
                meta=row.metadata or {};record.update(passed=row.passed,score=row.score,decision=meta.get('decision'),abstained=is_abstention(row),metadata=meta)
                if family!='mixed':
                    detail=DecisionEngine(threshold=contract.threshold).decide_detailed([row],domain=context.plan.domain,snapshot=FrozenReputationSnapshot.from_planning_context(context),aggregation='reputation_weighted',team=(name,),validation_id=e.run_id)
                    record.update(reputation=detail.votes[0].reputation,weight=detail.votes[0].weight,numerical_status=detail.status,informative_in_frozen_family_scenario=informative_contributor_count(context,detail,[row],'reputation_weighted'))
            individuals.append(record)
        if family=='mixed':
            abstract=[]
            eligible=[c for c in context.plan.candidates if c.eligible]
            for size in range(1,len(eligible)+1):
                for team in combinations(eligible,size):
                    if set(required)<={cap for c in team for cap in c.expected_capabilities}:abstract.append(sorted(c.verifier_name for c in team))
            achieved=sorted({cap for r in individuals if r['example_id']==e.example_id for cap in r['achieved']})
            blocked.append(dict(example_id=e.example_id,required=required,achieved_unbound_report_capabilities=achieved,missing_actual_checks=sorted(set(required)-set(achieved)),expected_union_teams=abstract,enumeration_status=enum.status,reasons=[r for rejected in enum.rejected for r in rejected.reasons],public_status='uncertain',limitation='Expected union is not compound coverage. No component binding or mixed history/policy; no compound acceptance or decision-loss comparison is manufactured.'))
            continue
        local={}
        for s in enum.strategies:
            selected=[attempts[n] for n in s.verifiers]
            finalized=finalize_decision(context,s,contract,[a.report for a in selected if a.report is not None],tuple((a.verifier_name,a.state) for a in selected),e.run_id)
            result=dict(example_id=e.example_id,group_id=gold['group_id'],family=family,team=list(s.verifiers),aggregation=s.aggregation,strategy_id=s.strategy_id,context_id=context.compatibility_id,answer_is_correct=gold['answer_is_correct'],status=finalized.public_status,numerical_status=finalized.detail.status,contributors=finalized.contributors,required=finalized.required,achieved=finalized.achieved,unresolved=finalized.unresolved,reasons=finalized.reasons,estimated_cost_ms=s.estimated_cost,loss=loss(finalized.public_status,gold['answer_is_correct']),decision=finalized.detail.to_dict())
            outcomes.append(result);local[(s.verifiers,s.aggregation)]=result
        for (team,aggregation),parent in local.items():
            for candidate in attempts:
                if candidate in team:continue
                larger=tuple(sorted((*team,candidate)));child=local.get((larger,aggregation))
                if child is None:continue
                change='helps' if child['loss']<parent['loss'] else 'hurts' if child['loss']>parent['loss'] else 'same_loss'
                additions.append(dict(example_id=e.example_id,family=family,aggregation=aggregation,parent=list(team),added=candidate,child=list(larger),before=parent['status'],after=child['status'],loss_before=parent['loss'],loss_after=child['loss'],change=change,additional_estimated_cost_ms=child['estimated_cost_ms']-parent['estimated_cost_ms'],note='Post-hoc diagnostic comparison only; unavailable as a pre-dispatch selection rule.'))
    aggregated=defaultdict(list)
    for row in outcomes:aggregated[(row['family'],tuple(row['team']),row['aggregation'])].append(row)
    team_metrics=[dict(family=family,team=team,aggregation=aggregation,**metrics(rows)) for (family,team,aggregation),rows in aggregated.items()]
    save(study/'diagnostic-contexts.json',contexts);save(study/'enumerations.json',enumerations);save(study/'individual-findings.json',individuals);save(study/'team-outcomes.json',outcomes);save(study/'team-metrics.json',team_metrics);save(study/'compound-blockers.json',blocked);save(study/'all-addition-comparisons.json',additions)
    summary=dict(version='capability_probe_diagnostics_v1',exploratory_only=True,recordings_complete=True,examples=len(bundle.request.examples),attempts=len(bundle.attempts),supported_atomic_examples=len({r['example_id'] for r in outcomes}),compound_examples_blocked=len(blocked),evaluated_team_example_rows=len(outcomes),addition_change_counts=dict(Counter(r['change'] for r in additions)),cautions=['No new policy was fitted or selected.','These are fixed historical task-family weight scenarios; new contrasts/operations are not validated by that history.','Factual examples reuse history-source facts, not unseen accuracy evidence.','Semantic coverage is a similarity measurement, not logical entailment.','Related factual/compound probes share source entities; 12 groups are not 12 independent benchmark clusters.','Old held-out results were not used to fit or select these examples.'],policy_probabilities_changed=False,reputation_updated=False,corpus_changed=False,activated=False)
    save(study/'summary.json',summary)
    write_report(study,groups,individuals,team_metrics,blocked,additions,summary)
    for path,digest in protocol['prior_artifact_hashes'].items():
        if sha(path)!=digest:raise ValueError('Prior artifact changed during evaluation')
    print(json.dumps(summary,indent=2),flush=True)


def write_report(study,groups,individuals,team_metrics,blocked,additions,summary):
    lines=['# Capability probes: exploratory diagnostics','',
        'Fixed 12 groups / 24 answers / 96 existing-verifier calls, at most 120 local generations. No policies were fitted, probabilities changed or reputations updated. This is not held-out evidence.',
        '', 'Earlier baseline pairs came from the selector count defaults and coverage/ranking fill, plus the execution floor. Every selected verifier still received the whole question, answer and context. Evidence internally splits some claims; that is not a cross-verifier component-binding protocol.',
        '', 'The flexible engine enumerates all eligible nonempty teams and checks actual informative contributions, coverage and thresholds. Routing and fitted policy selection are separate; none of these diagnostic results registers a new policy or expands the prototype allowlist.',
        '', 'The opt-in CapabilityProbeAnalyzer recognizes the exact Rule-supported word-difference template missed by the legacy analyzer. Existing atomic analysis is unchanged. Two explicit mixed templates retain both requirements and an unsupported component-binding requirement, so they fail closed instead of silently becoming only factual.',
        '', 'All weighting uses unchanged existing arithmetic/factual/semantic task-family history as a limited diagnostic scenario. It is not reliability calibration for new contrasts or wordings. Mixed inputs have no compatible history or policy and receive no fabricated team verdict. Semantic measures resemblance, not a logical-equivalence certificate.']
    for gid,g in groups.items():
        lines+=['','## '+gid,'',g['question'],'','Reference: '+g['reference'],'','Required checks: '+str(g['required_checks'])+'. Eligible by prerequisites: '+str(g['expected_eligible'])+'.',
            'Why extra checking might help: '+g['why_additional_checking_might_help'],
            'Interface support: '+g['input_support'],
            'Correct answer: '+g['answers'][0]['answer'],
            'Deliberately incorrect answer: '+g['answers'][1]['answer'],
            'Independent label provenance: '+json.dumps(g['independent_label_provenance'],sort_keys=True),
            'Legacy requirements: '+str(g['legacy_requirements']['requirements'])+'; opt-in requirements: '+str(g['owned_requirements']['requirements'])+'; unsupported: '+str(g['owned_requirements']['unsupported'])+'.']
        for row in (r for r in individuals if r['group_id']==gid):
            lines+=['',row['example_id']+' / '+row['verifier']+': '+row['state']+'; decision '+str(row.get('decision'))+'; score '+str(row.get('score'))+'; achieved '+str(row['achieved'])+'; informative under frozen family history '+str(row['informative_in_frozen_family_scenario'])+'; measured call '+str(row['duration_ms'])+' ms.']
    lines+=['','## Team summaries','', 'All eligible singles/pairs/triples/quads and both aggregations are retained. Counts below are over six arithmetic, six factual or eight reference examples. Multiple context identities in a family are descriptive pooling only, not one compatible policy or a payoff fit. Historical team costs are estimates, not measured deployment latency.']
    for m in team_metrics:
        lines+=['',m['family']+' / '+','.join(m['team'])+' / '+m['aggregation']+': coverage '+str(m['coverage'])+', false accept '+str(m['false_accept'])+', false reject '+str(m['false_reject'])+', uncertainty '+str(m['uncertain'])+', loss '+str(m['decision_loss'])+', selective risk '+str(m['selective_risk'])+', estimated cost '+str(m['estimated_team_cost_ms'])+' ms.']
    lines+=['','## Adding one verifier','', 'These exhaustive post-hoc comparisons are diagnostics, not an oracle available to routing. Counts: '+str(summary['addition_change_counts'])+'.']
    for kind in ('helps','hurts'):
        examples=[r for r in additions if r['change']==kind]
        lines+=['',kind+':']
        if not examples:lines+=['No observed cases.']
        for row in examples[:8]:lines+=['- '+json.dumps(row,sort_keys=True)]
    lines+=['','## Compound support','']
    for row in blocked:lines+=[json.dumps(row,sort_keys=True),'']
    lines+=['## Limits and next step','',
        'Abstention and missing/unsupported coverage remain uncertainty. No report identities or verifier algorithms were changed. No independent failure paths are inferred from different names; the original shared-unknown dependency registry is retained. No new attack campaign was run.',
        '', 'See raw collection/recordings.json and individual-findings.json for all findings, including unsuccessful probes. Team-outcomes.json retains contributors, achieved/missing checks and reasons; all-addition-comparisons.json includes negative and unchanged outcomes.',
        '', 'Any future policy fit needs fresh grouped history/development/test partitions after question-only categories, component contracts and baselines are predeclared. Do not reuse the completed held-out outcomes or these explored probes as a new untouched test set. A legitimate fit may still select only singletons or report infeasibility.']
    (study/'report.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--study',type=Path,default=Path('artifacts/capability-probes-v1'));p.add_argument('--source',type=Path,required=True);a=p.parse_args();evaluate(a.study,a.source)
