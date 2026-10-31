"""Authorized bounded three-cohort study using existing offline producers."""
import argparse
from dataclasses import asdict
import hashlib
import json
import math
import os
from pathlib import Path
import random
import re
import sys

ROOT=Path('build/multitask-policy42')
AUTHORITY='User request 40cf4c15-2260-48ef-b3a1-7154d0d47554: task-conditioned exploratory collection and reliability-first fits'
COHORTS=('arithmetic','semantic','factual')
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def save(p,value):
    with Path(p).open('x',encoding='utf-8') as f:json.dump(value,f,indent=2,ensure_ascii=False,allow_nan=False)

def save_checked(p,value):
    """Resume pure fitting only by verifying existing bytes' JSON meaning."""
    normalized=json.loads(json.dumps(value,ensure_ascii=False,allow_nan=False))
    if Path(p).exists():
        if read(p)!=normalized:raise ValueError('existing output differs; preserved without overwrite: '+str(p))
        return
    save(p,normalized)

def source_number(value):
    if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or value<=0:
        raise ValueError('finite positive published numeric value required')
    return str(value)

def prepare(*,adapter_config):
    from scripts.preparation_config import preparation_adapter
    config=preparation_adapter(adapter_config,ROOT).model_dump(mode='json')
    from app.analysis.task_analyzer import TaskQuestionAnalyzer
    from app.game.models import content_id
    from app.game.offline.collection import Candidate
    from app.game.offline.records import FinalTestReservation
    from app.selection.capabilities import BUILTIN_CAPABILITIES
    from app.game.task_conditioning import analysis_task
    old=Path('build/factual-policy42-20261029');countries=read(old/'sources/countries.json')
    geo={l.split('\t')[0]:l.split('\t') for l in (old/'sources/geonames-countryInfo.txt').read_text(encoding='utf-8').splitlines() if l and not l.startswith('#')}
    prior={r['iso'] for r in read(old/'dataset-audit.json')['rows'] if r['selected']}
    exclusions=[];eligible=[]
    from scripts.factual_policy42 import EXCLUDED
    for c in countries:
        iso=c['cca2'];reasons=[]
        if iso in prior:reasons.append('previous_capital_study_group')
        if iso in EXCLUDED:reasons.append('predeclared_transition_or_disputed_scope_exclusion')
        if not c.get('unMember') or not re.fullmatch('[A-Za-z]+',c['name']['common']):reasons.append('outside_single_token_country_scope')
        if iso not in geo or not geo[iso][7].isdigit():reasons.append('missing_structured_population')
        if len(c.get('currencies',{}))!=1 or iso not in geo or next(iter(c.get('currencies',{'?':None})))!=geo[iso][10]:reasons.append('currency_sources_disagree_or_multiple')
        if not isinstance(c.get('area'),(float,int)) or c['area']<=0:reasons.append('missing_area')
        exclusions.append(dict(iso=iso,reasons=reasons,selected=False))
        if not reasons:eligible.append(c)
    eligible.sort(key=lambda c:c['cca2']);random.Random(42).shuffle(eligible)
    n=min(60,3*(len(eligible)//3))
    if n<6:raise ValueError('insufficient independently sourced factual groups')
    eligible=eligible[:n];selected={c['cca2'] for c in eligible}
    for row in exclusions:
        row['selected']=row['iso'] in selected
        if not row['selected'] and not row['reasons']:row['reasons']=['outside_seed42_sample']
    ROOT.mkdir(exist_ok=False);(ROOT/'sources').mkdir()
    sources={}
    for name in ('countries.json','geonames-countryInfo.txt','LICENSE','countries-revision.json'):
        value=(old/'sources'/name).read_bytes();(ROOT/'sources'/name).write_bytes(value);sources[name]=hashlib.sha256(value).hexdigest()
    frames={cohort:[] for cohort in COHORTS}
    for i,c in enumerate(eligible):
        country=c['name']['common'];iso=c['cca2'];kind=('population','currency','area')[i%3]
        if kind=='population':value=int(geo[iso][7]);truth=f'The population of {country} is {value}.';wrong=f'The population of {country} is {value+12345}.'
        elif kind=='area':value=c['area'];truth=f'The area of {country} is {source_number(value)} square kilometres.';wrong=f'The area of {country} is {source_number(value+1000)} square kilometres.'
        else:
            code=next(iter(c['currencies']));value=c['currencies'][code]['name']
            alternative='Euro' if code=='USD' else 'United States dollar'
            truth=f'The currency of {country} is the {value}.';wrong=f'The currency of {country} is the {alternative}.'
        frames['factual'].append(dict(group=iso,question=f'What is the {kind} of {country}?',reference=truth,correct=truth,incorrect=wrong,
            provenance=dict(kind=kind,iso=iso,source_hashes=sources,value=value,source_snapshot_truth=True),
            index_included=(i%(n//3)!=0)))
    arithmetic=[]
    for i in range(n):
        left=307+i*7;right=503+i*11;value=left+right
        arithmetic.append(dict(group=f'addition-{left}-{right}',question=f'What is {left} + {right}?',reference=str(value),correct=str(value),incorrect=str(value+1),
            provenance=dict(method='independent exact integer addition',operands=[left,right],correct_integer=value)))
    random.Random(42).shuffle(arithmetic);frames['arithmetic']=arithmetic
    names='Alex Blair Casey Dana Ellis Finley Gray Harper Indigo Jules Kai Lane Morgan Noel Oakley Parker Quinn Reese Sage Taylor Val Wren Avery Bailey Cameron Drew Emery Frankie Gale Hayden Ira Jordan Kelly Logan Marley Nico Ocean Peyton Riley Sam Toby Uma Vic Wynn Ariel Blake Cody Devin Eden Flynn Glen Hollis Jamie Kelsey Lee Micah Robin Shawn Terry Winter Zane'.split()
    names=names[:60]
    if len(names)!=60 or len(set(names))!=60:raise ValueError('unique synthetic actor groups required')
    semantic=[]
    for i,name in enumerate(names[:n]):
        verb,obj,place=(('carried','parcel','library'),('delivered','letter','museum'),('brought','basket','station'))[i%3]
        truth=f'{name} {verb} a {obj} to the {place}.'
        semantic.append(dict(group='frame-'+name,question='Paraphrase this reference: '+truth,reference=truth,
            correct=f'A {obj} was {verb} to the {place} by {name}.',incorrect=f'{name} repaired a bicycle near the harbour.',
            provenance=dict(method='independent predicate/argument frame and active-passive identity',actor=name,verb=verb,object=obj,location=place,
                negative='different action, object and destination; not a verifier label')))
    random.Random(42).shuffle(semantic);frames['semantic']=semantic
    analyzer=TaskQuestionAnalyzer();audit=[]
    for cohort in COHORTS:
        directory=ROOT/cohort;directory.mkdir();(directory/'custody').mkdir();training=[];held=[];reserved=[]
        identities=set();analysis_signatures=set()
        for i,frame in enumerate(frames[cohort]):
            role=('history','development','final_test')[i//(n//3)];analysis=analyzer.analyze(frame['question'])
            identities.add(analysis_task(analysis).task_id)
            analysis_signatures.add((analysis.domain,analysis.domain_status,analysis.difficulty,analysis.difficulty_score,tuple(analysis.verification_types)))
            for correct in (True,False):
                answer=frame['correct'] if correct else frame['incorrect'];eid=frame['group']+('-correct' if correct else '-incorrect')
                e=dict(example_id=eid,split_identity='multitask42-'+cohort+'-'+frame['group'],question_id=content_id(frame['question']),run_id='multitask42-'+cohort+'-'+role+'-'+eid,
                    dataset_id='multitask42-'+cohort+'-'+role,role=role,purpose='calibration',question=frame['question'],answer=answer,reference=frame['reference'],analysis=asdict(analysis),
                    label=dict(answer_is_correct=correct,label_source='independent-'+cohort+'-frames-v1',label_method='independent_ground_truth',provenance=json.dumps(frame['provenance'],sort_keys=True)))
                if role=='final_test':
                    held.append(e);reserved.append(dict(example_id=eid,split_identity=e['split_identity'],question_id=e['question_id'],validation_id=e['run_id'],content_identity=content_id([e['question'],answer,e['reference']])))
                else:training.append(e)
        if len(identities)!=1 or len(analysis_signatures)!=1:raise ValueError('cohort requires separate planning contexts: '+str(analysis_signatures))
        reservation=FinalTestReservation(version='final_test_reservation_v1',role='final_test',dataset_id='multitask42-'+cohort+'-final_test',custody_record=AUTHORITY+'; procedural source-known reservation',examples=reserved)
        save(directory/'custody/final-prepared-payload.json',held)
        save(directory/'reservation.json',reservation.model_dump(mode='json'))
        save(directory/'preparation.json',dict(examples=training,candidates=[Candidate(verifier_name=name,adapter=name+'_v1',registered=True,capability_source='builtin',capabilities=BUILTIN_CAPABILITIES[name]).model_dump(mode='json') for name in ('semantic','evidence','rule','confidence')]))
        audit.append(dict(cohort=cohort,groups=n,groups_per_split=n//3,candidates_to_collect=len(training),attempts=len(training)*4,task_id=next(iter(identities)),planning_signature=list(next(iter(analysis_signatures)))))
    corpus=[dict(id=f['group'],title=f['group'],text=f['reference'],url='https://www.geonames.org/countries/'+f['group']+'/') for f in frames['factual'] if f['index_included']]
    save(ROOT/'corpus.json',corpus)
    save(ROOT/'adapter.json',config)
    save(ROOT/'study-audit.json',dict(authority=AUTHORITY,cohorts=audit,source_hashes=sources,factual_exclusions=exclusions,
        preparation_version='multitask_frames_v2_exact_source_numbers',
        pre_outcome_rule='Uniform n=min(60,3*floor(eligible-factual-groups/3)); seed42; no outcome-based exclusions',
        corpus_missing_evidence_rule='Omit first factual group of each split from retrieval index; keep independent labels and trusted reference',
        label_scope='Population/area/currency are source-snapshot facts, not claims of current census values; equivalence is constructed predicate-frame preservation, not truth verification',
        prior_overlap='Exclude all previous capital-study ISO groups. Public source files previously inspected, so reserved facts are not independently blinded unseen knowledge. Arithmetic uses distinct 3-digit operands; semantic frames are new.',
        final_custody='Procedural; final candidates prepared once, no later payload access',settings=dict(q_min=.90,epsilon=1e-8,losses=[1.,1.,.2],priors=[1.,1.],threshold=.55,seed=42),
        planned_candidates=sum(x['candidates_to_collect'] for x in audit),planned_attempts=sum(x['attempts'] for x in audit),max_generations=sum(x['candidates_to_collect'] for x in audit)*5))
    print('Prepared',audit,flush=True)

def collect_phase(cohort):
    import requests
    from scripts.run_factual_diagnostic import NetworkBudget
    from app.benchmark.project_adapter import AdapterConfiguration,observe_service,inspect_setup
    from app.game.offline.calibration import MeasurementSetup
    from app.game.offline.collection import RecordingRequest
    from app.game.offline.collect import main as collect_main
    directory=ROOT/cohort;config=AdapterConfiguration.model_validate(read(ROOT/'adapter.json'))
    handle=(directory/'network-audit.jsonl').open('x',encoding='utf-8')
    guard=NetworkBudget(config.ollama_url,handle,generation_limit=400,metadata_limit=1300)
    original=requests.Session.request
    requests.Session.request=lambda session,method,url,*args,**kw:guard.call(original,session,method,url,*args,**kw)
    if not (ROOT/'service-observation.json').exists():save(ROOT/'service-observation.json',observe_service(config).model_dump(mode='json'))
    preflight=inspect_setup(config);save(directory/'resource-preflight.json',preflight)
    if not preflight['ready']:raise ValueError(preflight['blockers'])
    setup=MeasurementSetup.model_validate(preflight['observed_setup']);prep=read(directory/'preparation.json')
    request=RecordingRequest(version='offline_recording_request_v1',intended_use='pilot',study_approval=AUTHORITY,preparation_authorization=AUTHORITY,
        cache_contract='complete_team_independent_v1',randomness_control='Split42; existing n5 provider seeds0..4 and temperature0.8; no deterministic generation claim',
        execution_configuration_id=setup.resources.manifest_id,factory='app.game.offline.recording_adapters:project_factory',expected_setup=setup,
        final_test_reservation=read(directory/'reservation.json'),permitted_datasets=tuple((role,'multitask42-'+cohort+'-'+role) for role in ('history','development')),
        candidates=prep['candidates'],examples=prep['examples'])
    save(directory/'request.json',request.model_dump(mode='json'))
    os.environ['VERIFIER_COLLECTION_ADAPTER_CONFIG']=str((ROOT/'adapter.json').resolve())
    result=collect_main(['collect',str(directory/'request.json'),'--output-dir',str(directory/'collection')])
    print('Cohort',cohort,'exit',result,'network',guard.counts,flush=True)
    if result:raise ValueError('collection checkpoint retained; inspect before any resume')


def validate_resources_phase():
    """Fixed software fixtures, not study candidates, collection or calibration."""
    import requests
    from scripts.run_factual_diagnostic import NetworkBudget
    from scripts.factual_policy42 import evidence_probes
    from app.game.offline.recording_adapters import project_factory
    from app.game.offline.collect import load_bundle
    from app.game.offline.collection import RecordingBundle, completeness, measurement_input
    integrity=[]
    freeze=read(ROOT/'preparation-freeze.json')
    for path,digest in freeze['frozen_preparation_sha256'].items():
        if hashlib.sha256(Path(path).read_bytes()).hexdigest()!=digest:
            raise ValueError('frozen preparation changed: '+path)
    for cohort in COHORTS:
        directory=ROOT/cohort/'collection'
        bundle=RecordingBundle.model_validate(read(directory/'recordings.json'))
        report=completeness(bundle)
        if not report['complete'] or report['executed_calls']!=320:
            raise ValueError('resource software checks require complete 320-attempt cohorts')
        if load_bundle(directory)!=bundle:raise ValueError('journal and exported recordings differ')
        starts=[json.loads(line)['attempt_id'] for line in (directory/'started.jsonl').read_text(encoding='utf-8').splitlines() if line.strip()]
        if len(starts)!=len(set(starts)) or set(starts)!={a.attempt_id for a in bundle.attempts if a.executed}:
            raise ValueError('start ledger has duplicates, ambiguous work or missing executions')
        if measurement_input(bundle).model_dump(mode='json')!=read(directory/'measurements.json'):
            raise ValueError('measurement export differs from retained attempts')
        integrity.append(dict(cohort=cohort,**report,unique_starts=len(starts),bundle_id=bundle.bundle_id,
            setup_fingerprint=bundle.observed_setup.fingerprint,request_id=bundle.request.request_id))
    save(ROOT/'collection-integrity.json',dict(cohorts=integrity,executed_study_calls=sum(r['executed_calls'] for r in integrity),
        frozen_preparation_unchanged=True,final_payloads_opened=False))
    os.environ['VERIFIER_COLLECTION_ADAPTER_CONFIG']=str((ROOT/'adapter.json').resolve())
    with (ROOT/'resource-validation-network.jsonl').open('x',encoding='utf-8') as audit:
        guard=NetworkBudget(read(ROOT/'adapter.json')['ollama_url'],audit,generation_limit=0,metadata_limit=30)
        original=requests.Session.request
        requests.Session.request=lambda session,method,url,*args,**kw:guard.call(original,session,method,url,*args,**kw)
        pool,setup,observer=project_factory()
        before=observer.snapshot()
        evidence=next(v for v in pool if v.name=='evidence')
        resource=next(v for v in before.verifiers if v.verifier_name=='evidence')
        proof=evidence_probes(evidence.nli,resource)
        if observer.snapshot()!=before:raise ValueError('software-probe resources changed')
        for cohort in COHORTS:
            bundle=RecordingBundle.model_validate(read(ROOT/cohort/'collection/recordings.json'))
            proof.require_resources(bundle.observed_setup.resources)
        save(ROOT/'evidence-validation.json',proof.model_dump(mode='json'))
        save(ROOT/'resource-validation-scope.json',dict(scope='Seven fixed software contract fixtures: four controlled and three installed-NLI; controlled retriever, not study candidates or an end-to-end retrieval-quality claim',
            validation_id=proof.validation_id,network_counts=guard.counts,study_collection_attempts=960,
            additional_study_candidates=0,additional_study_generations=0,used_in_calibration=False,
            validation_setup=setup.model_dump(mode='json')))
    print('Resource-bound software validation complete.',flush=True)


def fit_phase(cohort):
    save=save_checked
    from app.game.offline.collection import RecordingBundle, completeness, measurement_input, export_training
    from app.game.offline.calibration import CalibrationRequest, calibrate, apply_calibration
    from app.game.research.specification import RecordingConfiguration, PolicyBuildSpecification
    from app.game.research.readiness import require_ready
    from app.game.models import capture_context, content_id
    from app.game.task_conditioning import bind_task_history
    from app.game.execution_contract import ExecutionContract
    from app.game.offline.attacks import AttackSpecification, enumerate_attacks
    from app.game.offline.evaluation import bind_evaluation, construct_payoffs, export_artifact, summarize
    from app.game.offline.reliability import fit_reliability_first
    from app.game.offline.budget_sensitivity import restrict_budget_evaluation
    from app.game.offline.build import verify_equivalent, environment_versions
    from app.game.policy import build_policy
    from app.game.strategies import enumerate_strategies
    from app.game.artifacts import PolicyArtifact
    from app.selection.verifier_selector import VerifierSelector
    from app.selection.capabilities import BUILTIN_CAPABILITIES
    from app.reputation.reputation_manager import ReputationManager
    from app.verifiers.base_verifier import BaseVerifier
    from app.decision.decision_engine import log_odds_weight
    directory=ROOT/cohort;bundle=RecordingBundle.model_validate(read(directory/'collection/recordings.json'))
    integrity=completeness(bundle)
    if not integrity['complete']:
        save(directory/'missing-inputs.json',dict(status='blocked',gaps=integrity['gaps'],artifact_created=False))
        raise ValueError('incomplete cohort; no fit')
    measurements=measurement_input(bundle)
    calibration=calibrate(CalibrationRequest(measurements=measurements,final_test_reservation=bundle.request.final_test_reservation,
        required_verifiers=tuple(c.verifier_name for c in bundle.request.candidates),include_warmups=True,
        freeze_record=AUTHORITY+'; exact completed bundle '+bundle.bundle_id))
    save(directory/'calibration.json',calibration.model_dump(mode='json'))
    costs=tuple((row['verifier_name'],row['attempt_cost']) for row in calibration.result['estimates'])
    total=math.fsum(c for n,c in costs)
    if not math.isfinite(total) or total<=0:raise ValueError('measured full-roster budget must be finite and positive')
    manager=ReputationManager(prior_alpha=1.,prior_beta=1.)
    history={e.run_id:e for e in bundle.request.examples if e.role=='history'}
    for row in bundle.attempts:
        if row.run_id in history and row.attempt.state=='directional':
            e=history[row.run_id];manager.update_from_ground_truth(row.candidate,e.analysis.domain,row.attempt.report.passed,e.label.answer_is_correct)
    class Handle(BaseVerifier):
        def __init__(self,name):self._name=name
        @property
        def name(self):return self._name
        def verify(self,*args,**kw):raise RuntimeError('planning-only registration; no inference in fitting')
    names=tuple(c.verifier_name for c in bundle.request.candidates)
    selector=VerifierSelector(verifiers=[Handle(n) for n in names],reputation_manager=manager,capabilities={n:BUILTIN_CAPABILITIES[n] for n in names})
    resources=bundle.observed_setup.resources;first=bundle.request.examples[0]
    recording=RecordingConfiguration(execution_configuration_id=resources.manifest_id,
        model_fingerprints=tuple((v.verifier_name+':'+r.resource_id,r.sha256) for v in resources.verifiers for r in v.resources if r.kind=='model'),
        corpus_fingerprints=tuple((v.verifier_name+':'+r.resource_id,r.sha256) for v in resources.verifiers for r in v.resources if r.kind in {'corpus','index'}),
        prompt_and_adapter_fingerprints=tuple((v.verifier_name+':'+r.kind+':'+r.resource_id,r.sha256) for v in resources.verifiers for r in v.resources if r.kind in {'configuration','implementation','prompt'}),
        collection_protocol='complete_team_independent_v1',evidence_validation=read(ROOT/'evidence-validation.json'))
    contract=ExecutionContract(version='offline_public_decision_v4',coverage_version='task_output_contract_v2',contributor_version='informative_history_influence_v1',
        threshold=.55,failure_contract='all_selected_returned',execution_configuration_id=resources.manifest_id,resource_manifest=resources,history_prior_alpha=1.,history_prior_beta=1.)
    attacks=AttackSpecification(version='report_corruption_v1',suppression='unavailable')
    dependencies=[]
    for rid,affected in [('local-embedding-snapshot',('evidence','semantic')),('local-nli-snapshot',('evidence','confidence'))]:
        observed={r.sha256 for v in resources.verifiers if v.verifier_name in affected for r in v.resources if r.resource_id==rid}
        if len(observed)!=1:raise ValueError('unwitnessed shared dependency '+rid)
        dependencies.append(dict(resource_id=rid,compromise_pathway='shared actual installed model '+next(iter(observed)),verifiers=affected))
    def prepare_context(budget):
        context=capture_context(selector,first.analysis,context=first.reference,attempt_costs=costs,budget=float(budget),cost_units='ms',
            loss_configuration=dict(version='multitask-exploratory-loss-v1',false_accept=1.,false_reject=1.,uncertain=.2,resource_weight=.1/total,cost_units='ms'),
            dependencies=dict(version='multitask-observed-dependencies-v1',dependencies=dependencies,unresolved=names,unknown_treatment='shared_unknown'),
            aggregation_versions=(('reputation_weighted','log_odds_v1'),('dependency_group','groups_v1')),
            provenance=dict(attack_specification=attacks.specification_id,history_dataset='multitask42-'+cohort+'-history',development_dataset='multitask42-'+cohort+'-development',
                final_test_dataset='multitask42-'+cohort+'-final_test',matrix_version='multitask-finalized-development-v1',loss_configuration='multitask-exploratory-loss-v1',
                category=first.analysis.domain,evidence_kind='empirical'))
        manifest=export_training(bundle,context)
        context=apply_calibration(context,calibration,manifest=manifest,contract=contract,recording=recording,
            budget_ms=float(budget),resource_weight_per_ms=.1/total,expected_setup_fingerprint=bundle.observed_setup.fingerprint)
        context=bind_task_history(context,manifest)
        return bind_evaluation(context,manifest,contract,attacks),manifest
    full,manifest=prepare_context(total)
    def specification(context,training,primary_specification_id=None):
        return PolicyBuildSpecification(version='offline_policy_build_v1',study_id='multitask42-'+cohort,
            configuration_version='task-conditioned-exploratory-v1',code_revision=bundle.observed_setup.code_revision,
            setting_role='primary' if primary_specification_id is None else 'sensitivity',primary_specification_id=primary_specification_id,
            scientific_scope=read(ROOT/'study-audit.json')['label_scope']+'; task '+cohort+'; exploratory development only',
            primary_outcomes=('worst_case_expected_loss','decision_coverage'),
            sensitivity_plan=('Every distinct feasible team-cost breakpoint; fixed 90% coverage and reliability-first loss.',),
            matched_coverage_plan='Fixed finalized clean coverage floor 0.90; never relax after outcomes.',
            final_test_custody_and_freeze_protocol='Outcome-free procedural reservation metadata only; no final-test collection/evaluation.',
            datasets=tuple(dict(role=role,dataset_id='multitask42-'+cohort+'-'+role,version='multitask_frames_v2_exact_source_numbers',
                source='Retained pinned public sources or independent constructed frames; study-audit.json',
                independent_label_provenance='Independent structured source identity or exact arithmetic/frame labels, not verifier agreement',
                declared_label_sources=('independent-'+cohort+'-frames-v1',),grouping_protocol='All candidates grouped; seed42 twenty groups per partition')
                for role in ('history','development','final_test')),
            recording=recording,context=context,manifest=training,contract=contract,attacks=attacks,
            unknown_dependency_treatment='shared_unknown',greedy_aggregation='reputation_weighted',policy_sampling_seeds=(42,),policy_sampling_repetitions=1,
            uncertainty=dict(method='paired_split_identity_cluster_percentile_v1',resamples=2000,confidence_level=.95,seed=42),optimizer_tolerance=1e-8)
    spec=specification(full,manifest)
    readiness=require_ready(spec,actual_code_revision=bundle.observed_setup.code_revision)
    save(directory/'policy-input.json',spec.model_dump(mode='json'))
    save(directory/'readiness.json',readiness.model_dump(mode='json'))
    evaluation=construct_payoffs(full,manifest,contract,attacks)
    repeated_full,repeated_manifest=prepare_context(total)
    repeated_evaluation=construct_payoffs(repeated_full,repeated_manifest,contract,attacks)
    save(directory/'source-context.json',full.model_dump(mode='json'))
    save(directory/'training-manifest.json',manifest.model_dump(mode='json'))
    save(directory/'contract.json',contract.model_dump(mode='json'))
    save(directory/'development-evaluation.json',evaluation.model_dump(mode='json'))
    original=build_policy(full,evaluation.matrix,tolerance=1e-8)
    baseline=export_artifact(original,full,manifest,contract,attacks,applicable_domain=full.plan.domain)
    repeated_original=build_policy(repeated_full,repeated_evaluation.matrix,tolerance=1e-8)
    repeated_baseline=export_artifact(repeated_original,repeated_full,repeated_manifest,contract,attacks,applicable_domain=full.plan.domain)
    baseline_equivalence=verify_equivalent(baseline,repeated_baseline)
    base_dir=directory/'unconstrained-comparison';base_dir.mkdir(exist_ok=True)
    save(base_dir/'policy.json',baseline.model_dump(mode='json'))
    PolicyArtifact.model_validate_json((base_dir/'policy.json').read_text(encoding='utf-8'))
    baseline_probabilities=dict(original.solution.probabilities)
    baseline_scenarios=[]
    for attack in enumerate_attacks(full.dependencies,attacks):
        m=summarize(tuple((o,baseline_probabilities[o.strategy_id]) for o in evaluation.outcomes if o.attack_id==attack.attack_id),full.loss_configuration)
        baseline_scenarios.append(dict(attack=attack.kind,attack_id=attack.attack_id,group_id=attack.group_id,members=attack.members,
            metrics=m.model_dump(mode='json'),validation_loss=m.validation_loss(full.loss_configuration),uncertainty_rate=m.uncertainty_rate))
    save(base_dir/'report.json',dict(kind='unconstrained cost-inclusive diagnostic; not the 90%-coverage primary',
        artifact_id=baseline.artifact_id,probabilities=original.solution.probabilities,scenarios=baseline_scenarios,
        worst_case_validation_loss=max(s['validation_loss'] for s in baseline_scenarios),
        worst_case_cost_inclusive_objective=max(s['metrics']['mean_loss'] for s in baseline_scenarios),
        certificate=original.solution.model_dump(mode='json'),reproducibility=baseline_equivalence))
    budgets=sorted({s.estimated_cost for s in enumerate_strategies(full).strategies}|{total})
    reports=[]
    for index,budget in enumerate(budgets):
        primary=budget==total;target,target_manifest=(full,manifest) if primary else prepare_context(budget)
        target_spec=spec if primary else specification(target,target_manifest,spec.specification_id)
        target_readiness=require_ready(target_spec,actual_code_revision=bundle.observed_setup.code_revision)
        evaluated=evaluation if primary else restrict_budget_evaluation(full,manifest,target,target_manifest,contract,attacks,evaluation)
        clean_id=evaluated.matrix.attack_ids[0]
        qs={s:m.decision_coverage for s,a,m in evaluated.metrics if a==clean_id}
        max_coverage=max(qs.values(),default=0.)
        destination=directory/('budget-'+str(index).zfill(2));destination.mkdir(exist_ok=True)
        save(destination/'readiness.json',target_readiness.model_dump(mode='json'))
        strategies=enumerate_strategies(target)
        rows=[]
        for s in strategies.strategies:
            scenarios=[]
            for attack in enumerate_attacks(target.dependencies,attacks):
                m=next(m for sid,aid,m in evaluated.metrics if sid==s.strategy_id and aid==attack.attack_id)
                outcomes=[o for o in evaluated.outcomes if o.strategy_id==s.strategy_id and o.attack_id==attack.attack_id]
                scenarios.append(dict(attack=attack.kind,attack_id=attack.attack_id,group_id=attack.group_id,members=attack.members,metrics=m.model_dump(mode='json'),validation_loss=m.validation_loss(target.loss_configuration),
                    contributor_counts=dict(__import__('collections').Counter(o.contributors for o in outcomes)),reason_counts=dict(__import__('collections').Counter(r for o in outcomes for r in o.reasons))))
            rows.append(dict(**s.model_dump(mode='json'),scenarios=scenarios,
                worst_case_validation_loss=max(c['validation_loss'] for c in scenarios),
                worst_case_cost_inclusive_objective=max(c['metrics']['mean_loss'] for c in scenarios)))
        report=dict(cohort=cohort,budget_ms=budget,primary=primary,q_min=.90,maximum_achievable_clean_coverage=max_coverage,
            task_binding=json.loads(target.task_conditioning_json),history=[dict(**asdict(s),log_odds=log_odds_weight(s.posterior_mean),group_reliability=max(0.,2*s.posterior_mean-1)) for s in target.plan.reputation_statistics],
            eligible_candidates=[asdict(c) for c in target.plan.candidates],feasibility_rejections=[r.model_dump(mode='json') for r in strategies.rejected],
            strategies=rows,context_id=target.compatibility_id,calibration_id=calibration.calibration_id,
            status='infeasible_coverage' if max_coverage<.90 else 'pending',artifact_created=False)
        if max_coverage>=.90:
            bound,policy=fit_reliability_first(target,target_manifest,contract,attacks,evaluated,minimum=.90,epsilon=1e-8,tolerance=1e-8,cost_tolerance=1e-8)
            artifact=export_artifact(policy,bound,target_manifest,contract,attacks,applicable_domain=bound.plan.domain)
            repeat_cells=repeated_evaluation if primary else restrict_budget_evaluation(repeated_full,repeated_manifest,target,target_manifest,contract,attacks,repeated_evaluation)
            second_context,second_policy=fit_reliability_first(target,target_manifest,contract,attacks,repeat_cells,minimum=.90,epsilon=1e-8,tolerance=1e-8,cost_tolerance=1e-8)
            repeated=export_artifact(second_policy,second_context,target_manifest,contract,attacks,applicable_domain=bound.plan.domain)
            equivalence=verify_equivalent(artifact,repeated)
            save(destination/'policy.json',artifact.model_dump(mode='json'))
            loaded=PolicyArtifact.model_validate_json((destination/'policy.json').read_text(encoding='utf-8'))
            probs=dict(policy.solution.probabilities)
            scenarios=[]
            for attack in enumerate_attacks(bound.dependencies,attacks):
                m=summarize(tuple((o,probs[o.strategy_id]) for o in evaluated.outcomes if o.attack_id==attack.attack_id),bound.loss_configuration)
                scenarios.append(dict(attack=attack.kind,attack_id=attack.attack_id,group_id=attack.group_id,members=attack.members,
                    metrics=m.model_dump(mode='json'),validation_loss=m.validation_loss(bound.loss_configuration),uncertainty_rate=m.uncertainty_rate))
            worst=max(c['validation_loss'] for c in scenarios)
            report.update(status='complete',artifact_created=True,artifact_id=loaded.artifact_id,
                worst_case_validation_loss=worst,worst_case_scenarios=[c['attack_id'] for c in scenarios if abs(c['validation_loss']-worst)<=1e-12],
                worst_case_cost_inclusive_diagnostic=max(c['metrics']['mean_loss'] for c in scenarios),
                probabilities=policy.solution.probabilities,certificate=policy.solution.model_dump(mode='json'),scenarios=scenarios,reproducibility=equivalence,
                marginal_verifiers={n:math.fsum(probs[s.strategy_id] for s in policy.strategies if n in s.verifiers) for n in names},
                marginal_aggregations={a:math.fsum(probs[s.strategy_id] for s in policy.strategies if s.aggregation==a) for a in ('reputation_weighted','dependency_group')},
                zero_clean_coverage_probability=math.fsum(p for sid,p in policy.solution.probabilities if qs[sid]==0))
        else:
            summary='Coverage target 0.90 infeasible. Maximum finalized clean coverage: '+str(max_coverage)+'. No constrained PolicyArtifact created.\n'
            path=destination/'summary.txt'
            if path.exists() and path.read_text(encoding='utf-8')!=summary:raise ValueError('existing infeasibility summary differs; preserved')
            if not path.exists():path.write_text(summary,encoding='utf-8')
        save(destination/'report.json',report);reports.append(dict(directory=str(destination),**report))
        print(cohort,'budget',budget,'primary',primary,'status',report['status'],'maximum coverage',max_coverage,flush=True)
    save(directory/'budget-results.json',reports)
    save(directory/'fit-provenance.json',dict(authority=AUTHORITY,bundle_id=bundle.bundle_id,calibration_id=calibration.calibration_id,
        code_revision=__import__('subprocess').check_output(['git','rev-parse','HEAD'],text=True).strip(),
        configuration_digest=content_id(read(ROOT/'study-audit.json')),request_id=bundle.request.request_id,
        manifest_id=manifest.manifest_id,contract_id=content_id(contract.model_dump(mode='json')),
        producer_script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        repeat_build=baseline_equivalence,
        full_roster_budget_ms=total,source_setup=bundle.observed_setup.model_dump(mode='json'),
        current_application_source_digest=content_id([(p.as_posix(),hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted(Path('app').rglob('*.py'))]),
        environment={**environment_versions(),'linprog_options':dict(stage_a='SciPy defaults',stage_b=dict(primal_feasibility_tolerance=1e-10,dual_feasibility_tolerance=1e-10))},settings=dict(q_min=.90,epsilon=1e-8,cost_tolerance_ms=1e-8,loss_tolerance=1e-8,
            stage_b_options=dict(primal_feasibility_tolerance=1e-10,dual_feasibility_tolerance=1e-10)),
        note='All first/subsequent calls retained; summed attempt wall time is not request latency; history isolated by task; no development reputation updates'))


def runtime_phase():
    import requests
    from app.analysis.task_analyzer import TaskQuestionAnalyzer
    from app.game.task_conditioning import TaskPolicyRouter, analysis_signature, analysis_task
    from app.game.artifacts import PolicyArtifact, DeploymentEpisode, InMemoryPolicyProvider
    from app.game.models import PlanningContext, content_id
    from app.game.offline.collection import RecordingBundle, export_training
    from app.game.offline.recording_adapters import ProjectObserver
    from app.game.offline.replay import replay
    from app.game.offline.attacks import AttackSpecification, enumerate_attacks
    from app.game.execution import GameRun, VerifierExecutionFailure
    from app.decision.decision_engine import DecisionDetail
    from app.models.schemas import ValidationRequest
    from app.verifiers.base_verifier import BaseVerifier
    from app.selection.models import VerifierUnavailable
    from app.selection.verifier_selector import VerifierSelector
    from app.selection.capabilities import BUILTIN_CAPABILITIES
    from scripts.run_factual_diagnostic import NetworkBudget
    analyzer=TaskQuestionAnalyzer();routes=[];diagnostic_routes=[];artifacts=[];bundles={};scope=set();primary={}
    for cohort in COHORTS:
        directory=ROOT/cohort;bundle=RecordingBundle.model_validate(read(directory/'collection/recordings.json'));bundles[cohort]=bundle
        scope.update(e.question_id for e in bundle.request.examples)
        scope.update(e.question_id for e in bundle.request.final_test_reservation.examples)
        first=bundle.request.examples[0];signature=analysis_signature(analyzer.analyze(first.question),first.reference)
        for report in read(directory/'budget-results.json'):
            if report['artifact_created']:
                artifact=PolicyArtifact.model_validate_json((Path(report['directory'])/'policy.json').read_text(encoding='utf-8'))
                episode=DeploymentEpisode(episode_id='task-'+cohort+'-'+str(report['budget_ms']),context=artifact.context,contract=artifact.contract,execution_configuration_id=artifact.execution_configuration_id)
                artifacts.append(artifact)
            else:episode=None
            routes.append((signature,report['budget_ms'],report['primary'],episode,'90% coverage infeasible; maximum '+str(report['maximum_achievable_clean_coverage'])))
            if report['primary']:primary[cohort]=(report,episode)
        artifact=PolicyArtifact.model_validate_json((directory/'unconstrained-comparison/policy.json').read_text(encoding='utf-8'));artifacts.append(artifact)
        diagnostic_routes.append((signature,artifact.context.budget,True,DeploymentEpisode(episode_id='comparison-'+cohort,context=artifact.context,contract=artifact.contract,execution_configuration_id=artifact.execution_configuration_id),''))
    # Deliberately include the old capital artifact: task/context compatibility
    # must prevent accidental general-domain fallback to it.
    artifacts.append(PolicyArtifact.model_validate_json(Path('build/factual-policy42-20261029/fitted-policy/policy.json').read_text(encoding='utf-8')))
    provider=InMemoryPolicyProvider(tuple(artifacts));router=TaskPolicyRouter(routes);diagnostic=TaskPolicyRouter(diagnostic_routes)
    os.environ['VERIFIER_COLLECTION_ADAPTER_CONFIG']=str((ROOT/'adapter.json').resolve());observer=ProjectObserver()
    audit=(ROOT/'runtime-network.jsonl').open('x',encoding='utf-8');guard=NetworkBudget(read(ROOT/'adapter.json')['ollama_url'],audit,generation_limit=0,metadata_limit=200)
    original=requests.Session.request
    requests.Session.request=lambda session,method,url,*args,**kw:guard.call(original,session,method,url,*args,**kw)
    class Retained(BaseVerifier):
        def __init__(self,a):self.attempt=a
        @property
        def name(self):return self.attempt.verifier_name
        def verify(self,*args,**kw):
            if self.attempt.state=='unavailable':raise VerifierUnavailable('retained unavailable')
            if self.attempt.state=='failed':raise VerifierExecutionFailure('retained failure')
            return self.attempt.report
    class Draw:
        def __init__(self,value):self.value=value
        def random(self):return self.value
    def scoped(route,selector,analysis,request,run_id,draw,budget=None):
        try:analysis_task(analysis)
        except ValueError:pass # Let the public router report unknown requirements.
        else:
            if content_id(request.question) not in scope:
                return GameRun((),DecisionDetail(analysis.domain,'unknown',0.,0.,.55,'unknown',()),'uncertain',dict(selection_status='study_scope_mismatch',public_status='uncertain'))
        return route.run(selector,analysis,request,run_id,provider=provider,rng=Draw(draw),resource_observer=observer,budget=budget)
    checks=[]
    for cohort in COHORTS:
        bundle=bundles[cohort];first=bundle.request.examples[0];primary_report,episode=primary[cohort]
        for label,route,active_episode in [('primary',router,episode),('unconstrained_comparison',diagnostic,diagnostic_routes[COHORTS.index(cohort)][3])]:
            if active_episode is None:
                result=scoped(route,None,analyzer.analyze(first.question),ValidationRequest(question=first.question,answer=first.answer,context=first.reference),first.run_id,.5)
                assert result.summary['selection_status']=='task_infeasible'
                checks.append(dict(cohort=cohort,kind=label,summary=result.summary,dispatch=False));continue
            artifact=next(a for a in artifacts if a.context==active_episode.context)
            fresh=PlanningContext(**{**artifact.context.model_dump(),'offline_evaluation_id':None,'execution_contract_json':None,
                'clean_coverage_json':None,'reliability_first_json':None,'task_conditioning_json':None})
            manifest=export_training(bundle,fresh)
            probs=dict(artifact.policy.solution.probabilities);cumulative=0.
            for strategy in artifact.policy.strategies:
                p=probs[strategy.strategy_id];draw=cumulative+p/2;cumulative+=p
                if p==0:continue
                for correct in (True,False):
                    example=next(e for e in manifest.partition('development').examples if e.answer_is_correct==correct)
                    source=next(e for e in bundle.request.examples if e.run_id==example.validation_id)
                    actual_analysis=analyzer.analyze(source.question)
                    assert asdict(actual_analysis)==asdict(source.analysis)
                    selector=VerifierSelector(verifiers=[Retained(a) for a in example.attempts],capabilities={a.verifier_name:BUILTIN_CAPABILITIES[a.verifier_name] for a in example.attempts})
                    request=ValidationRequest(question=source.question,answer=source.answer,context=source.reference)
                    actual=scoped(route,selector,actual_analysis,request,source.run_id,draw)
                    attack=enumerate_attacks(artifact.context.dependencies,AttackSpecification(version='report_corruption_v1',suppression='unavailable'))[0]
                    expected=replay(artifact.context,strategy,attack,AttackSpecification(version='report_corruption_v1',suppression='unavailable'),artifact.contract,example)
                    assert actual.summary['selection_status']=='selected' and actual.summary['selected_strategy_id']==strategy.strategy_id
                    assert actual.public_status==expected.public_status and actual.detail.raw_score==expected.numerical_score and actual.summary['contributors']==expected.contributors
                    checks.append(dict(cohort=cohort,kind=label,example_id=example.example_id,parity=True,summary=actual.summary))
        # Explicit budget change: never borrow a policy from another breakpoint.
        bad=scoped(router,None,analyzer.analyze(first.question),ValidationRequest(question=first.question,answer=first.answer,context=first.reference),first.run_id,.5,budget=primary_report['budget_ms']+1.)
        assert bad.summary['selection_status']=='task_out_of_scope';checks.append(dict(cohort=cohort,kind='budget_mismatch',summary=bad.summary))
    unknown='Tell me a tale.'
    failure=scoped(router,None,analyzer.analyze(unknown),ValidationRequest(question=unknown,answer='story'),'unknown',.5)
    assert failure.summary['selection_status']=='task_unknown'
    outside='What is 999 + 1000?'
    failure2=scoped(router,None,analyzer.analyze(outside),ValidationRequest(question=outside,answer='1999',context='1999'),'outside',.5)
    assert failure2.summary['selection_status']=='study_scope_mismatch'
    semantic=bundles['semantic'].request.examples[0]
    failure3=scoped(router,None,analyzer.analyze(semantic.question),ValidationRequest(question=semantic.question,answer=semantic.answer),'missing-reference',.5)
    assert failure3.public_status=='uncertain'
    save(ROOT/'task-routing.json',dict(version='prepared_question_task_routes_v1',allowed_question_ids=sorted(scope),primary_routes=[dict(task_signature=list(s),budget=b,primary=p,compatible_episode=None if e is None else e.episode_id,reason=r) for s,b,p,e,r in routes],
        scope='Only prepared question identities, including outcome-free reserved metadata; no final execution performed'))
    save(ROOT/'runtime-validation.json',dict(scope='Retained-report execution through actual TaskQuestionAnalyzer, scoped task router, captured plans, provider and public finalizer; not fresh inference',
        checks=checks,unknown=failure.summary,outside=failure2.summary,missing_reference=failure3.summary,network_counts=guard.counts,final_payload_access_guard=True))
    print('Task routing/runtime validation complete.',flush=True)


def report_phase():
    from collections import Counter
    from app.game.models import content_id
    audit=read(ROOT/'study-audit.json');cohort_reports=[]
    lines=['# Task-conditioned engineering study','',
        'Exploratory history/development only; no held-out superiority or framework-wide coverage claim. No final-test verifier outcomes were collected or opened.',
        '', 'All task identities are derived from actual question requirements and subject-domain metadata. Subject domain remains general/unknown; histories and snapshots are separate by task.']
    for cohort in COHORTS:
        directory=ROOT/cohort;collection=read(directory/'collection/collection-report.json')
        bundle=read(directory/'collection/recordings.json');calibration=read(directory/'calibration.json');budgets=read(directory/'budget-results.json')
        state_counts=Counter((r['candidate'],r['attempt']['state']) for r in bundle['attempts'])
        hidden_failures=Counter()
        for row in bundle['attempts']:
            if row['attempt']['report_json']:
                m=json.loads(row['attempt']['report_json']).get('metadata') or {}
                if m.get('error'):hidden_failures[row['candidate']+':'+str(m.get('judgment_source',m.get('abstain_reason','error')))]+=1
        primary=next(r for r in budgets if r['primary'])
        baseline=read(directory/'unconstrained-comparison/report.json')
        cohort_reports.append(dict(cohort=cohort,collection=collection,states=[dict(verifier=n,state=s,count=c) for (n,s),c in state_counts.items()],
            returned_provider_errors=dict(hidden_failures),calibration_id=calibration['calibration_id'],cost_estimates=calibration['result']['estimates'],budgets=budgets,unconstrained_comparison=baseline))
        lines+=['',f'## {cohort}','',f"Collection: {collection['executed_calls']} executed / {collection['expected_attempts']} planned; complete={collection['complete']}; returned states {dict(state_counts)}.",
            f"Task: `{primary['task_binding']['identity']}`; primary budget {primary['budget_ms']:.9f} ms; maximum finalized clean coverage {primary['maximum_achievable_clean_coverage']:.6%}; primary status {primary['status']}.",
            '', 'Frozen history (directional observations only; no development updates):']
        for h in primary['history']:
            lines.append(f"- {h['verifier_name']}: n={h['observation_count']}, successes/failures {h['successes']}/{h['failures']}, Beta({h['alpha']},{h['beta']}), mean {h['posterior_mean']:.9f}, variance {h['posterior_variance']:.9f}, log-odds {h['log_odds']:.9f}, group reliability {h['group_reliability']:.9f}.")
        lines+=['','Measured costs (all first/subsequent attempts, including failures):']
        for cost in calibration['result']['estimates']:
            lines.append(f"- {cost['verifier_name']}: n={cost['attempts']}, mean {cost['mean_ms']:.9f} ms, median {cost['median_ms']:.9f}, p95 {cost['p95_nearest_rank_ms']:.9f}, failed attempts {cost['failures']}.")
        lines+=['','Unconstrained cost-inclusive comparison (not the primary coverage-constrained result):',
            'All strategy probabilities: '+str(baseline['probabilities']),
            f"Worst-case validation loss {baseline['worst_case_validation_loss']:.9f}; cost-inclusive objective {baseline['worst_case_cost_inclusive_objective']:.9f}.",
            'Repeated build: '+str(baseline['reproducibility'])]
        for cell in baseline['scenarios']:
            m=cell['metrics'];lines.append(f"- {cell['attack']}: coverage {m['decision_coverage']:.6%}; validation loss {cell['validation_loss']:.9f}; false accept/reject {m['false_accept']:.9g}/{m['false_reject']:.9g}; uncertainty {cell['uncertainty_rate']:.6%}; cost {m['estimated_resource_cost']:.9f} ms; cost-inclusive objective {m['mean_loss']:.9f}.")
        for report in budgets:
            lines+=['',f"### Budget {report['budget_ms']:.9f} ms ({'PRIMARY' if report['primary'] else 'DESCRIPTIVE SENSITIVITY'})",'',
                f"Status {report['status']}; maximum clean coverage {report['maximum_achievable_clean_coverage']:.6%}; target remains 90%.", 'Feasible strategies:']
            probabilities=dict(report.get('probabilities',[]))
            for row in report['strategies']:
                probability=probabilities.get(row['strategy_id'])
                lines.append(f"- {row['verifiers']} / {row['aggregation']}; estimated cost {row['estimated_cost']:.9f} ms; probability {'undefined (infeasible)' if probability is None else format(probability,'.12g')}; clean coverage {row['scenarios'][0]['metrics']['decision_coverage']:.6%}.")
                for cell in row['scenarios']:
                    m=cell['metrics'];lines.append(f"  - {cell['attack']}: validation loss {cell['validation_loss']:.9f}; coverage {m['decision_coverage']:.6%}; false accept/reject {m['false_accept']}/{m['false_reject']}; uncertainty {m['uncertain']}/{m['examples']}; informative contributor counts {cell['contributor_counts']}; reasons {cell['reason_counts']}.")
            if report['artifact_created']:
                lines+=['',f"Artifact `{report['artifact_id']}`; zero-clean-coverage probability {report['zero_clean_coverage_probability']:.12g}.",
                    f"Worst-case validation loss {report['worst_case_validation_loss']:.9f}; worst attack IDs {report['worst_case_scenarios']}; separate old cost-inclusive diagnostic {report['worst_case_cost_inclusive_diagnostic']:.9f}.",
                    'Marginal verifier probabilities: '+str(report['marginal_verifiers']), 'Marginal aggregation probabilities: '+str(report['marginal_aggregations'])]
                for cell in report['scenarios']:
                    m=cell['metrics'];lines.append(f"- POLICY {cell['attack']}: loss {cell['validation_loss']:.9f}, coverage {m['decision_coverage']:.6%}, false accept/reject {m['false_accept']:.9g}/{m['false_reject']:.9g}, uncertainty {cell['uncertainty_rate']:.6%}, cost {m['estimated_resource_cost']:.9f} ms, old cost-inclusive diagnostic {m['mean_loss']:.9f}.")
                lines+=['Stage-A/Stage-B certificate:','```json',json.dumps(report['certificate']['reliability_certificate'],indent=2),'```']
            else:lines+=['','No constrained policy or probabilities exist at this budget. This is not a zero-probability distribution, and the target was not relaxed.']
    runtime=read(ROOT/'runtime-validation.json')
    lines+=['','## Runtime and limitations','',runtime['scope'],
        'All primary outcomes and diagnostic baseline executions remain distinct. Infeasible primary routes fail safely; diagnostic unconstrained artifacts are not replacements for a 90%-coverage policy.',
        'The prepared-question scope uses training/reservation metadata only. Unknown, unsupported, outside-study, missing-reference and incompatible-budget cases fail without cross-task/capital-history fallback.',
        'Independent workers shared CPU/Ollama capacity. Costs are empirical summed verifier-attempt times, not money, isolated latency or a claim of efficiency improvement. Do not pool timing samples across cohorts.',
        'The corpus/source files were previously inspected, so reservations are procedural source-known evaluation groups, not independently blinded unseen knowledge. No final-test outcomes were accessed.',
        'Semantic similarity is not factual truth or a guarantee of equivalence. Confidence agreement is not independent evidence. All configured informative verifiers remain connected through actual shared models and conservative shared-unknown assumptions.',
        'No verifier use or aggregation allocation was forced. Infeasible targets show limitations of existing outputs/history/contributor rules, not permission to weaken guards or relabel data.',
        'All previous arithmetic, capital, coverage and reliability-first artifacts are preserved. No production integration, commit, push, merge or API activation occurred.']
    save(ROOT/'cross-context-results.json',dict(cohorts=cohort_reports,runtime=runtime,study=audit,source_scope='exploratory development only'))
    with (ROOT/'cross-context-results.md').open('x',encoding='utf-8') as f:f.write('\n'.join(lines)+'\n')
    save(ROOT/'final-summary.json',dict(attempts=sum(r['collection']['executed_calls'] for r in cohort_reports),
        primary=[dict(cohort=r['cohort'],**{k:next(b for b in r['budgets'] if b['primary'])[k] for k in ('status','artifact_created','maximum_achievable_clean_coverage','budget_ms')}) for r in cohort_reports],
        runtime_generation_calls=runtime['network_counts']['generation'],final_test_evaluation=False,
        source_digest=content_id([(p.as_posix(),hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted(Path('app').rglob('*.py'))])))
    print('Cross-context report complete.',flush=True)

def main(argv=None):
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['prepare','collect','validate-resources','fit','runtime','report']);p.add_argument('--cohort',choices=COHORTS)
    p.add_argument('--adapter-config',type=Path,help='Required for prepare: explicit reviewed adapter JSON')
    a=p.parse_args(argv)
    if a.phase=='prepare' and a.adapter_config is None:p.error('prepare requires --adapter-config PATH; no historical adapter is selected automatically')
    os.environ.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',HF_HUB_DISABLE_TELEMETRY='1')
    if a.phase!='prepare':
        def guard(event,args):
            if event=='open' and isinstance(args[0],str) and 'custody' in Path(args[0]).parts:raise AssertionError('final payload access forbidden')
        sys.addaudithook(guard)
    try:
        if a.phase=='prepare':
            try:prepare(adapter_config=a.adapter_config)
            except (ValueError,OSError) as exc:
                print(json.dumps(dict(status='preparation_input_error',message=str(exc),new_policy_created=False)));return 2
        elif a.phase=='collect':collect_phase(a.cohort)
        elif a.phase=='validate-resources':validate_resources_phase()
        elif a.phase=='fit':fit_phase(a.cohort)
        elif a.phase=='runtime':runtime_phase()
        else:report_phase()
    except (ValueError,OSError,TypeError) as exc:
        details=exc.errors(include_input=False,include_context=False,include_url=False) if hasattr(exc,'errors') else [dict(message=str(exc))]
        path=ROOT/('blocked-'+a.phase+'-'+str(a.cohort)+'-'+str(len(list(ROOT.glob('blocked-*.json'))))+'.json')
        ROOT.mkdir(parents=True,exist_ok=True)
        save(path,dict(status='blocked_phase',phase=a.phase,cohort=a.cohort,gaps=details,
            existing_artifact_paths=[str(p) for p in ROOT.glob('*/budget-*/policy.json')],new_policy_claim=False))
        path.with_suffix('.txt').write_text('Phase blocked; existing outputs preserved.\n'+str(exc)+'\n',encoding='utf-8')
        print('Phase blocked; see',path,flush=True);return 2
    return 0

if __name__=='__main__':raise SystemExit(main())
