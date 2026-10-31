"""Authorized seed-42 factual engineering study, reusing public offline producers.

Outputs are local/private. No API/DB wiring, verifier changes or final evaluation.
"""
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
import unicodedata

from app.game.models import content_id

STUDY='factual-capitals42-v1'
EXCLUDED={'BO','ZA','LK','NL','SZ','MY','TZ','BI','ID','GQ','MM','KZ','IL','PS','YE','SD','SS','LY','UA','RU','CG','CD','KR','KP'}
AUTHORITY='User engineering-study request attachment a20fd956-2750-40a2-9ef1-0bf06d958844: bounded collection, labels/preparation, procedural reservation and explicit settings'

def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))

def save(path,value):
    with Path(path).open('x',encoding='utf-8') as f:json.dump(value,f,indent=2,ensure_ascii=False,allow_nan=False)

def norm(s):return unicodedata.normalize('NFKC',s).casefold().strip()

def prepare(root):
    from app.analysis.question_analyzer import QuestionAnalyzer
    from app.game.offline.collection import Candidate
    from app.game.offline.records import FinalTestReservation
    from app.selection.capabilities import BUILTIN_CAPABILITIES
    countries=read(root/'sources/countries.json')
    geo={r[0]:r for line in (root/'sources/geonames-countryInfo.txt').read_text(encoding='utf-8').splitlines()
         if line and not line.startswith('#') for r in [line.split('\t')]}
    audit=[];eligible=[]
    for c in countries:
        iso=c['cca2'];country=c['name']['common'];caps=c['capital'];reasons=[]
        if not c.get('unMember'):reasons.append('not_declared_UN_member')
        if not re.fullmatch('[A-Za-z]+',country):reasons.append('outside_single_token_ASCII_country_scope')
        if len(caps)!=1:reasons.append('multiple_or_missing_capitals')
        if iso in EXCLUDED:reasons.append('predeclared_ambiguous_disputed_or_transition_scope_exclusion')
        if iso not in geo or len(caps)!=1 or norm(caps[0])!=norm(geo[iso][5]):reasons.append('sources_do_not_agree_exactly_after_NFKC_casefold')
        audit.append(dict(iso=iso,country=country,reasons=reasons,selected=False))
        if not reasons:eligible.append(dict(iso=iso,country=country,capital=caps[0]))
    eligible.sort(key=lambda x:x['iso']);random.Random(42).shuffle(eligible)
    chosen=eligible[:60]
    if len(chosen)!=60 or len({norm(x['capital']) for x in chosen})!=60:raise ValueError('60 distinct eligible facts and capital names required')
    selected={r['iso'] for r in chosen}
    for a in audit:
        if a['iso'] in selected:a['selected']=True
        elif not a['reasons']:a['reasons']=['not_in_seed42_first60_prespecified_sample']
    analyzer=QuestionAnalyzer(mode='heuristic',environ={});training=[];reserved=[];final=[];corpus=[]
    source_hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (root/'sources').iterdir() if p.is_file()}
    for i,fact in enumerate(chosen):
        role=('history','development','final_test')[i//20]
        question=f"What is the capital of {fact['country']}?"
        reference=f"The capital of {fact['country']} is {fact['capital']}."
        analysis=asdict(analyzer.analyze(question))
        if analysis['verification_types']!=['direct_fact'] or not analysis['research_context']['requirements_known']:raise ValueError('scope did not yield actual known direct_fact requirements')
        # Background reference corpus contains facts, not final candidate labels or outcomes.
        corpus.append(dict(id=fact['iso'],title=fact['country'],url='https://www.geonames.org/countries/'+fact['iso']+'/',text=reference))
        other=chosen[(i//20)*20+(i+1)%20]
        if norm(other['capital'])==norm(fact['capital']):raise ValueError('negative must be a different city')
        for correct in (True,False):
            city=fact['capital'] if correct else other['capital'];answer=f"The capital of {fact['country']} is {city}."
            label=dict(answer_is_correct=correct,label_source='geonames-and-mledoze-pinned-capital-v1',label_method='independent_ground_truth',
                provenance=json.dumps(dict(sources=source_hashes,iso=fact['iso'],expected_capital=fact['capital'],candidate_city=city,
                    rule='Exact structured capital identity, not substring matching or verifier agreement',constructed_negative=not correct,
                    independent_of_framework=True,source_lineages_may_overlap=True),sort_keys=True))
            e=dict(example_id=fact['iso']+('-correct' if correct else '-incorrect'),split_identity=STUDY+'-'+fact['iso'],question_id=content_id(question),
                run_id=STUDY+'-'+role+'-'+fact['iso']+('-correct' if correct else '-incorrect'),dataset_id=STUDY+'-'+role,
                role=role,purpose='calibration',question=question,answer=answer,reference=reference,analysis=analysis,label=label)
            if role=='final_test':
                final.append(e)
                reserved.append(dict(example_id=e['example_id'],split_identity=e['split_identity'],question_id=e['question_id'],validation_id=e['run_id'],content_identity=content_id([question,answer,reference])))
            else:training.append(e)
    (root/'custody').mkdir()
    save(root/'custody/final-prepared-payload.json',dict(procedural=True,examples=final))
    reservation=FinalTestReservation(version='final_test_reservation_v1',role='final_test',dataset_id=STUDY+'-final_test',
        custody_record=AUTHORITY+'; procedural seed42 holdout, no third-party blinding',examples=reserved)
    save(root/'reservation.json',reservation.model_dump(mode='json'))
    save(root/'preparation.json',dict(examples=training,candidates=[Candidate(verifier_name=n,adapter=n+'_v1',registered=True,capability_source='builtin',capabilities=BUILTIN_CAPABILITIES[n]).model_dump(mode='json') for n in ('semantic','evidence','rule','confidence')]))
    save(root/'corpus.json',corpus)
    save(root/'dataset-audit.json',dict(source_hashes=source_hashes,sources=['https://download.geonames.org/export/dump/countryInfo.txt','https://github.com/mledoze/countries'],
        licences=['GeoNames CC-BY; see source header','mledoze ODbL-1.0; retained LICENSE'],rows=audit,eligible=len(eligible),groups=60,training_candidates=len(training),reserved_candidates=len(reserved),
        protocol='Sort ISO, shuffle seed42, first60, twenty groups per role; negatives rotate capital names only within their role; all alternatives grouped by country',
        corpus_scope='Known-corpus, reference-assisted facts for all sixty countries; background corpus is not a final outcome payload',custody='procedural; public sources and deterministic preparation are not independent blinding'))
    adapter=read(Path('docs/studies/factual-feasibility-draft-v1/adapter.draft.json'))
    adapter.update(corpus_path=str(root/'corpus.json'),index_dir=str(root/'index-v2'),index_receipt=str(root/'index-receipt.json'),service_observation=str(root/'service-observation.json'))
    save(root/'adapter.json',adapter)
    save(root/'authority.json',dict(source=AUTHORITY,max_candidates=200,max_attempts=800,actual_candidates=80,actual_attempts=320,max_generations=400,
        approved_losses=[1.,1.,.2],prior=[1.,1.],threshold=.55,budget='sum of all eligible measured costs',resource_weight='0.1/B',no_final_evaluation=True))
    print('Prepared 60 groups / 80 history-development candidates and 40 reserved candidates; no verifier outcomes inspected.')


def evidence_probes(nli,resources):
    from app.verifiers.evidence_verifier import EvidenceVerifier
    from tests.test_evidence_verifier import FakeRetriever,FakeNLI,chunk,ENTAILS,CONTRADICTS,NEUTRAL
    from app.game.research.evidence_validation import EvidenceValidation
    probes=[]
    for case,probs in [('controlled_support',ENTAILS),('controlled_rejection',CONTRADICTS),('controlled_neutral',NEUTRAL)]:
        row=EvidenceVerifier(retriever=FakeRetriever([chunk('Hamlet','Shakespeare wrote Hamlet.',.9)]),nli=FakeNLI({'Shakespeare':probs})).verify('Who wrote Hamlet?','Shakespeare')
        probes.append(dict(case_id=case,report_json=row.model_dump_json()))
    row=EvidenceVerifier(retriever=FakeRetriever([chunk('Support','Shakespeare wrote Hamlet.',.9),chunk('Reject','Marlowe wrote Hamlet.',.9,1)]),nli=FakeNLI({'Shakespeare':ENTAILS,'Marlowe':CONTRADICTS})).verify('Who wrote Hamlet?','Shakespeare')
    probes.append(dict(case_id='controlled_conflict',report_json=row.model_dump_json()))
    for case,answer,text in [('real_nli_support','Shakespeare','Shakespeare wrote Hamlet.'),('real_nli_rejection','Charles Dickens','Shakespeare wrote Hamlet.'),('real_nli_neutral','Shakespeare','Hamlet is a play.')]:
        row=EvidenceVerifier(retriever=FakeRetriever([chunk('Hamlet',text,.9)]),nli=nli).verify('Who wrote Hamlet?',answer)
        print(case,row.metadata.get('decision'),row.score,flush=True)
        probes.append(dict(case_id=case,report_json=row.model_dump_json()))
    return EvidenceValidation(version='evidence_public_contract_validation_v2',before=resources,after=resources,probes=probes)


def collect_phase(root):
    import requests
    from scripts.run_factual_diagnostic import NetworkBudget
    from app.benchmark.project_adapter import AdapterConfiguration,observe_service,inspect_setup
    from app.game.offline.collection import RecordingRequest
    from app.game.offline.calibration import MeasurementSetup
    from app.game.offline.collect import main as collect_main
    config=AdapterConfiguration.model_validate(read(root/'adapter.json'))
    audit_path=root/'network-audit.jsonl'
    if audit_path.exists():
        if (root/'recording-request.json').exists():raise ValueError('existing collection request: inspect checkpoint; no retries')
        audit_path=root/('network-audit-preflight-'+str(len(list(root.glob('network-audit*.jsonl'))))+'.jsonl')
    audit_handle=audit_path.open('x',encoding='utf-8')
    guard=NetworkBudget(config.ollama_url,audit_handle,generation_limit=400,metadata_limit=1300)
    original=requests.Session.request
    requests.Session.request=lambda session,method,url,*a,**kw:guard.call(original,session,method,url,*a,**kw)
    if not (root/'service-observation.json').exists():save(root/'service-observation.json',observe_service(config).model_dump(mode='json'))
    preflight=inspect_setup(config);save(root/'resource-preflight.json',preflight)
    if not preflight['ready']:raise ValueError(preflight['blockers'])
    setup=MeasurementSetup.model_validate(preflight['observed_setup']);prep=read(root/'preparation.json')
    request=RecordingRequest(version='offline_recording_request_v1',intended_use='pilot',study_approval=AUTHORITY,preparation_authorization=AUTHORITY,
        cache_contract='complete_team_independent_v1',randomness_control='Split/policy seed42; existing provider per-call generation seeds0..4, n5 temperature0.8; no deterministic generation claim',
        execution_configuration_id=setup.resources.manifest_id,factory='scripts.factual_policy42:validated_factory',expected_setup=setup,
        final_test_reservation=read(root/'reservation.json'),permitted_datasets=(('history',STUDY+'-history'),('development',STUDY+'-development')),
        candidates=prep['candidates'],examples=prep['examples'])
    save(root/'recording-request.json',request.model_dump(mode='json'))
    os.environ['VERIFIER_COLLECTION_ADAPTER_CONFIG']=str((root/'adapter.json').resolve())
    os.environ['FACTUAL_STUDY_ROOT']=str(root.resolve())
    result=collect_main(['collect',str(root/'recording-request.json'),'--output-dir',str(root/'collection')])
    if result:raise ValueError('collection incomplete; checkpoint journal retained; do not retry or overwrite')


def validated_factory():
    # Existing real factory and observer; probes use its actual installed NLI.
    from app.game.offline.recording_adapters import project_factory
    root=Path(os.environ['FACTUAL_STUDY_ROOT']);pool,setup,observer=project_factory()
    evidence=next(v for v in pool if v.name=='evidence')
    before=observer.snapshot()
    resource=next(v for v in before.verifiers if v.verifier_name=='evidence')
    proof=evidence_probes(evidence.nli,resource)
    if observer.snapshot()!=before:raise ValueError('resources changed during readiness probes')
    save(root/'evidence-validation.json',proof.model_dump(mode='json'))
    return pool,setup,observer


def fit_phase(root):
    from app.game.offline.collection import RecordingBundle, completeness, measurement_input, export_training
    from app.game.offline.calibration import calibrate, CalibrationRequest
    from app.game.models import capture_context
    from app.game.execution_contract import ExecutionContract
    from app.game.offline.attacks import AttackSpecification
    from app.game.research.specification import PolicyBuildSpecification
    from app.game.offline.build import main as build_main
    from app.reputation.reputation_manager import ReputationManager
    from app.selection.verifier_selector import VerifierSelector
    from app.selection.capabilities import BUILTIN_CAPABILITIES
    from app.verifiers.base_verifier import BaseVerifier
    bundle=RecordingBundle.model_validate(read(root/'collection/recordings.json'))
    if not completeness(bundle)['complete']:raise ValueError('incomplete actual collection; fitting blocked')
    measurements=measurement_input(bundle)
    calibration=calibrate(CalibrationRequest(measurements=measurements,
        final_test_reservation=bundle.request.final_test_reservation,required_verifiers=tuple(c.verifier_name for c in bundle.request.candidates),
        include_warmups=True,freeze_record=AUTHORITY+'; freeze actual complete collection '+bundle.bundle_id))
    save(root/'calibration.json',calibration.model_dump(mode='json'))
    budget=math.fsum(r['attempt_cost'] for r in calibration.result['estimates'])
    manager=ReputationManager(prior_alpha=1.,prior_beta=1.)
    history={e.run_id:e for e in bundle.request.examples if e.role=='history'}
    for row in bundle.attempts:
        if row.run_id in history and row.attempt.state=='directional':
            e=history[row.run_id]
            manager.update_from_ground_truth(row.candidate,e.analysis.domain,row.attempt.report.passed,e.label.answer_is_correct)
    class Handle(BaseVerifier):
        def __init__(self,name):self._name=name
        @property
        def name(self):return self._name
        def verify(self,*a,**kw):raise RuntimeError('planning-only registration; use retained recordings')
    names=tuple(c.verifier_name for c in bundle.request.candidates)
    selector=VerifierSelector(verifiers=[Handle(n) for n in names],reputation_manager=manager,
        capabilities={n:BUILTIN_CAPABILITIES[n] for n in names})
    first=bundle.request.examples[0];resources=bundle.observed_setup.resources
    attacks=AttackSpecification(version='report_corruption_v1',suppression='unavailable')
    dependencies=[]
    for resource_id,affected in [('local-embedding-snapshot',('semantic','evidence')),('local-nli-snapshot',('evidence','confidence'))]:
        actual={r.sha256 for v in resources.verifiers if v.verifier_name in affected for r in v.resources if r.resource_id==resource_id}
        if len(actual)!=1:raise ValueError('shared dependency not witnessed: '+resource_id)
        dependencies.append(dict(resource_id=resource_id,compromise_pathway='shared installed model snapshot '+next(iter(actual)),verifiers=affected))
    context=capture_context(selector,first.analysis,context=first.reference,
        attempt_costs=tuple((r['verifier_name'],r['attempt_cost']) for r in calibration.result['estimates']),budget=budget,cost_units='ms',
        loss_configuration=dict(version='approved-factual-engineering-v1',false_accept=1.,false_reject=1.,uncertain=.2,resource_weight=.1/budget,cost_units='ms'),
        dependencies=dict(version='observed-shared-models-and-unresolved-v1',dependencies=dependencies,unresolved=names,unknown_treatment='shared_unknown'),
        aggregation_versions=(('reputation_weighted','log_odds_v1'),('dependency_group','groups_v1')),
        provenance=dict(attack_specification=attacks.specification_id,history_dataset=STUDY+'-history',development_dataset=STUDY+'-development',
            final_test_dataset=STUDY+'-final_test',matrix_version='factual-capitals-development-v1',loss_configuration='approved-factual-engineering-v1',
            category=first.analysis.domain,evidence_kind='empirical'))
    manifest=export_training(bundle,context)
    contract=ExecutionContract(version='offline_public_decision_v2',coverage_version='factual_output_contract_v1',contributor_version='baseline_log_odds_active_group_v1',
        threshold=.55,failure_contract='all_selected_returned',execution_configuration_id=bundle.request.execution_configuration_id,
        resource_manifest=resources,history_prior_alpha=1.,history_prior_beta=1.)
    descriptions=tuple(dict(role=role,dataset_id=STUDY+'-'+role,version='public-capitals-constructed-variants-v1',
        source='Pinned mledoze countries and retained GeoNames countryInfo; see dataset-audit.json',
        independent_label_provenance='Exact structured capital agreement, independent of framework; possible shared source lineage',
        declared_label_sources=('geonames-and-mledoze-pinned-capital-v1',),grouping_protocol='Country ISO group; seed42 twenty groups per split; all variants grouped')
        for role in ('history','development','final_test'))
    spec=PolicyBuildSpecification(version='offline_policy_build_v1',study_id=STUDY,configuration_version='user-approved-engineering-v1',
        code_revision=bundle.observed_setup.code_revision,setting_role='primary',primary_specification_id=None,
        scientific_scope='Constructed reference-assisted public capital facts, single-token country scope; procedural holdout; development engineering evidence only',
        primary_outcomes=('worst_case_expected_loss','decision_coverage'),sensitivity_plan=('No tuning or sensitivity selection in this authorized engineering run.',),
        matched_coverage_plan='Fixed signed threshold 0.55; no matched coverage or superiority claim.',
        final_test_custody_and_freeze_protocol='Metadata-only procedural seed42 reservation; no held-out payload access after preparation; no final evaluation.',
        datasets=descriptions,recording=dict(execution_configuration_id=contract.execution_configuration_id,
            model_fingerprints=tuple((v.verifier_name+':'+r.resource_id,r.sha256) for v in resources.verifiers for r in v.resources if r.kind=='model'),
            corpus_fingerprints=tuple((v.verifier_name+':'+r.resource_id,r.sha256) for v in resources.verifiers for r in v.resources if r.kind in {'corpus','index'}),
            prompt_and_adapter_fingerprints=tuple((v.verifier_name+':'+r.kind+':'+r.resource_id,r.sha256) for v in resources.verifiers for r in v.resources if r.kind in {'implementation','configuration','prompt'}),
            collection_protocol='complete_team_independent_v1',evidence_validation=read(root/'evidence-validation.json')),
        context=context,manifest=manifest,contract=contract,attacks=attacks,unknown_dependency_treatment='shared_unknown',greedy_aggregation='reputation_weighted',
        policy_sampling_seeds=(42,),policy_sampling_repetitions=1,
        uncertainty=dict(method='paired_split_identity_cluster_percentile_v1',resamples=2000,confidence_level=.95,seed=42),optimizer_tolerance=1e-8)
    save(root/'policy-input.json',spec.model_dump(mode='json'))
    save(root/'approval-binding.json',dict(authority=AUTHORITY,configuration_digest=spec.specification_id,calibration_id=calibration.calibration_id,
        bundle_id=bundle.bundle_id,driver_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),budget_ms=budget,resource_weight_per_ms=.1/budget))
    result=build_main([str(root/'policy-input.json'),'--calibration',str(root/'calibration.json'),'--budget-ms',str(budget),
        '--resource-weight-per-ms',str(.1/budget),'--measurement-setup-fingerprint',bundle.observed_setup.fingerprint,'--output-dir',str(root/'fitted-policy')])
    if result:raise ValueError('public builder rejected inputs; see structured report')
    report_phase(root)


def report_phase(root):
    from collections import Counter
    from app.game.artifacts import PolicyArtifact, InMemoryPolicyProvider, DeploymentEpisode
    from app.game.offline.evaluation import construct_payoffs, summarize
    from app.game.offline.collection import RecordingBundle, completeness
    from app.game.offline.replay import replay
    from app.game.offline.attacks import enumerate_attacks
    from app.game.research.specification import PolicyBuildSpecification
    from app.game.execution import GameRuntime, VerifierExecutionFailure
    from app.game.offline.recording_adapters import ProjectObserver
    from app.models.schemas import ValidationRequest
    from app.selection.verifier_selector import VerifierSelector
    from app.selection.models import VerifierUnavailable
    from app.selection.capabilities import BUILTIN_CAPABILITIES
    from app.verifiers.base_verifier import BaseVerifier
    from app.decision.decision_engine import log_odds_weight
    artifact=PolicyArtifact.model_validate_json((root/'fitted-policy/policy.json').read_text(encoding='utf-8'))
    spec=PolicyBuildSpecification.model_validate(read(root/'policy-input.json'))
    bundle=RecordingBundle.model_validate(read(root/'collection/recordings.json'))
    evaluation=construct_payoffs(artifact.context,spec.manifest,spec.contract,spec.attacks)
    probabilities=dict(artifact.policy.solution.probabilities)
    attacks=enumerate_attacks(artifact.context.dependencies,spec.attacks)
    scenarios=[]
    for attack in attacks:
        m=summarize(tuple((o,probabilities[o.strategy_id]) for o in evaluation.outcomes if o.attack_id==attack.attack_id),artifact.context.loss_configuration)
        scenarios.append(dict(attack=attack.model_dump(mode='json'),metrics=m.model_dump(mode='json'),
            validation_loss=m.validation_loss(artifact.context.loss_configuration),uncertainty_rate=m.uncertainty_rate))
    strategies=[]
    for s in artifact.policy.strategies:
        cells=[dict(attack_id=a,metrics=m.model_dump(mode='json'),validation_loss=m.validation_loss(artifact.context.loss_configuration))
            for sid,a,m in evaluation.metrics if sid==s.strategy_id]
        strategies.append(dict(**s.model_dump(mode='json'),probability=probabilities[s.strategy_id],scenarios=cells))
    # Explicit development comparisons: same recorded full-team finalization, no production early stopping.
    baseline_teams={'captured_greedy':tuple(sorted(artifact.context.plan.initial_selected))}
    baselines={}
    for name,team in baseline_teams.items():
        match=next((s for s in artifact.policy.strategies if s.verifiers==team and s.aggregation==spec.greedy_aggregation),None)
        baselines[name]=None if match is None else next(s for s in strategies if s['strategy_id']==match.strategy_id)
    baselines['uniform_feasible']=[]
    for attack in attacks:
        m=summarize(tuple((o,1./len(strategies)) for o in evaluation.outcomes if o.attack_id==attack.attack_id),artifact.context.loss_configuration)
        baselines['uniform_feasible'].append(dict(attack_id=attack.attack_id,metrics=m.model_dump(mode='json'),validation_loss=m.validation_loss(artifact.context.loss_configuration)))
    clean=attacks[0];traces=[]
    for correct in (True,False):
        example=next(e for e in spec.manifest.partition('development').examples if e.answer_is_correct==correct)
        source=next(e for e in bundle.request.examples if e.run_id==example.validation_id)
        rows=[]
        for s in artifact.policy.strategies:
            o=replay(artifact.context,s,clean,spec.attacks,spec.contract,example)
            rows.append(o.model_dump(mode='json'))
        traces.append(dict(example_id=example.example_id,question=source.question,answer=source.answer,label=correct,
            reports=[dict(verifier_name=a.verifier_name,state=a.state,report=None if a.report is None else a.report.model_dump(mode='json')) for a in example.attempts],strategies=rows))
    # Public runtime with retained real reports and a live real-resource observer.
    # This checks dispatch/compatibility/finalization without repeating collection.
    os.environ['VERIFIER_COLLECTION_ADAPTER_CONFIG']=str((root/'adapter.json').resolve())
    observer=ProjectObserver();runtime_checks=[]
    class Retained(BaseVerifier):
        def __init__(self,attempt):self.attempt=attempt
        @property
        def name(self):return self.attempt.verifier_name
        def verify(self,*a,**kw):
            if self.attempt.state=='unavailable':raise VerifierUnavailable('retained unavailable execution')
            if self.attempt.state=='failed':raise VerifierExecutionFailure('retained failed execution')
            return self.attempt.report
    for correct in (True,False):
        e=next(e for e in spec.manifest.partition('development').examples if e.answer_is_correct==correct)
        source=next(x for x in bundle.request.examples if x.run_id==e.validation_id)
        selector=VerifierSelector(verifiers=[Retained(a) for a in e.attempts],capabilities={a.verifier_name:BUILTIN_CAPABILITIES[a.verifier_name] for a in e.attempts})
        episode=DeploymentEpisode(episode_id='retained-development-runtime-check',context=artifact.context,contract=artifact.contract,
            execution_configuration_id=artifact.execution_configuration_id)
        run=GameRuntime(InMemoryPolicyProvider((artifact,)),episode,random.Random(42),resource_observer=observer).run(selector,source.analysis,
            ValidationRequest(question=source.question,answer=source.answer,context=source.reference),e.validation_id)
        if run.summary['selection_status']!='selected':raise ValueError('runtime compatibility failed: '+str(run.summary))
        strategy=next(s for s in artifact.policy.strategies if s.strategy_id==run.summary['selected_strategy_id'])
        expected=replay(artifact.context,strategy,clean,spec.attacks,spec.contract,e)
        if run.public_status!=expected.public_status or run.detail.raw_score!=expected.numerical_score:raise ValueError('runtime/replay mismatch')
        runtime_checks.append(dict(example_id=e.example_id,summary=run.summary,parity=True))
    clean_outcomes=[o for o in evaluation.outcomes if o.attack_id==clean.attack_id and probabilities[o.strategy_id]>0]
    save(root/'development-report.json',dict(scope=spec.scientific_scope,collection=completeness(bundle),
        attempt_states=dict(Counter(a.attempt.state for a in bundle.attempts)),issues=dict(Counter(i for a in bundle.attempts for i in a.issues)),
        history=[dict(**asdict(s),log_odds_weight=log_odds_weight(s.posterior_mean)) for s in artifact.context.plan.reputation_statistics],
        strategies=strategies,scenarios=scenarios,baselines=baselines,
        baseline_scope='Recorded complete teams and identical public guards; not equivalent to production feedback or early stopping',
        clean_reason_counts=dict(Counter(reason for o in clean_outcomes for reason in o.reasons)),
        representative_traces=traces,runtime_checks=runtime_checks,
        runtime_scope='Retained real development reports through public runtime; live ProjectObserver, no new inference',
        report_driver_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        equivalent_payoff_groups=[[a['strategy_id'],b['strategy_id']] for i,a in enumerate(strategies) for b in strategies[i+1:]
            if all(abs(x['metrics']['mean_loss']-y['metrics']['mean_loss'])<=1e-12 for x,y in zip(a['scenarios'],b['scenarios']))],
        timing_boundary='Only verifier.verify wall time; model initialization and pre/post resource hashing outside timer; all measured calls retained; no warmup exclusions',
        limitations=['Development only; procedural custody; no held-out evaluation','Known-corpus reference-assisted constructed capital pairs; source lineages may overlap',
            'Shared-unknown dependency connects every verifier; no independence claim','Solver allocation among equivalent payoff rows is not aggregation superiority']))


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('phase',choices=['prepare','collect','fit','report']);p.add_argument('--root',type=Path,required=True);a=p.parse_args(argv)
    root=a.root
    os.environ.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',HF_HUB_DISABLE_TELEMETRY='1')
    if a.phase!='prepare':
        def audit(event,args):
            if event=='open' and isinstance(args[0],str) and 'custody' in Path(args[0]).parts:raise AssertionError('final payload open forbidden')
        sys.addaudithook(audit)
    if a.phase=='prepare':prepare(root)
    elif a.phase=='collect':collect_phase(root)
    elif a.phase=='fit':fit_phase(root)
    else:report_phase(root)

if __name__=='__main__':main()
