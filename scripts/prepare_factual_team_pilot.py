"""Prepare one review-only factual team pilot with existing public offline contracts.

No verifier calls, outcome-based filtering, collection, calibration, fit or release.
Only the six already separated preparation rows and metadata reservation are read.
"""
import argparse
from copy import deepcopy
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from app.analysis.question_analyzer import QuestionAnalyzer
from app.benchmark.project_adapter import inspect_setup, local_path
from app.game.dependencies import DependencyRegistry
from app.game.models import LossConfiguration, PayoffProvenance, capture_context, content_id
from app.game.offline.attacks import AttackSpecification, enumerate_attacks
from app.game.offline.calibration import CalibrationArtifact, MeasurementSetup, read_json
from app.game.offline.collection import PreparationExample, RecordingRequest
from app.game.strategies import enumerate_strategies
from app.reputation.reputation_manager import ReputationManager
from app.selection.verifier_selector import VerifierSelector

ROOT=Path(__file__).resolve().parents[1]
STUDY='factual-team-selection-v1'
SOURCES={
 'germany':dict(url='https://www.berlin.de/en/',excerpt='Capital of Germany',correct='Berlin',wrong='Hamburg'),
 'india':dict(url='https://www.cgibrisbane.gov.in/page/know-your-india/',excerpt='New Delhi is the capital of India.',correct='New Delhi',wrong='Mumbai'),
}


def cohort_key(e):
    """The analysis/reference fields checked by the existing first-export contract."""
    a=e['analysis']; r=a.get('research_context') or {}
    return content_id([a['domain'],a['domain_status'],a['analysis_method'],a['difficulty'],a['difficulty_score'],
        r.get('context_version'),r.get('scoring_version'),r, bool(e['reference'] and e['reference'].strip())])


def package(draft, calibration, preflight):
    calibration=CalibrationArtifact.model_validate(calibration)
    if not preflight['ready']:
        raise ValueError('resource preflight blocked; no collection authorized')
    analyzer=QuestionAnalyzer(mode='heuristic',environ={})
    costs={r['verifier_name']:r['attempt_cost'] for r in calibration.result['estimates']}
    if set(costs)!={c['verifier_name'] for c in draft['candidates']}:
        raise ValueError('historical cost roster differs from proposed roster')
    # Classification consumes only preparation inputs and actual analyzer metadata.
    # No recordings/outcome file is an input to this function.
    rows=[]; audit=[]; cohorts={}
    for original in draft['examples']:
        e=deepcopy(original)
        actual=asdict(analyzer.analyze(e['question']))
        if actual!=e['analysis']:
            raise ValueError('analyzer changed; review original cohort proposal without rewriting captured analysis')
        key=cohort_key(e)
        cohorts.setdefault(key,[]).append(e['example_id'])
        known=actual['research_context']['requirements_known']
        selected=known and actual['verification_types']==['direct_fact']
        audit.append(dict(example_id=e['example_id'],role=e['role'],analysis=actual,cohort_key=key,
            selected=selected,reason='known_direct_fact_capital_cohort' if selected else 'requirements_unknown',
            predicate_inputs='question, actual analyzer output; no report, correctness flag or timing',
            retained_in_original_draft=True))
        if selected: rows.append(e)
    if {e['example_id'] for e in rows}!={'factual-feasibility-draft-v1-e02','factual-feasibility-draft-v1-e03'}:
        raise ValueError('fixed review proposal requires original Germany-history and India-development rows')
    examples=[]; labels=[]
    for e in rows:
        key='germany' if e['role']=='history' else 'india'
        source=SOURCES[key]
        if e['answer']!=f"The capital of {key.title()} is {source['correct']}.":
            raise ValueError('source answer changed; do not inherit its adjudication')
        for correct in (True,False):
            row=deepcopy(e)
            row['example_id']=e['example_id']+('-positive' if correct else '-negative')
            row['run_id']=STUDY+'-'+row['example_id']
            # Preserve original related-group/question identity and partition.
            if not correct: row['answer']=e['answer'].replace(source['correct'],source['wrong'])
            adjudication=dict(example_id=row['example_id'],answer=row['answer'],proposed_correct=correct,
                source_url=source['url'],source_excerpt=source['excerpt'],accessed_date='2026-10-28',
                method='independent_ground_truth',human_approval=None,
                basis='Unique current capital named by official source; alternate city is a constructed incorrect candidate.',
                framework_outcomes_used=False,constructed_candidate=not correct)
            row['label']=dict(answer_is_correct=correct,label_source=STUDY+'-official-'+key,
                label_method='independent_ground_truth',provenance=json.dumps(adjudication,sort_keys=True))
            examples.append(PreparationExample.model_validate(row).model_dump(mode='json'))
            labels.append(adjudication)
    request=deepcopy(draft)
    request.update(examples=examples,intended_use='pilot',study_approval=None,preparation_authorization=None,
        expected_setup=preflight['observed_setup'],execution_configuration_id=MeasurementSetup.model_validate(preflight['observed_setup']).resources.manifest_id,
        randomness_control='One pass; zero warmups/retries; fixed candidate order from draft; confidence seeds 0..4, n=5, temperature .8, timeout 60s. No global determinism claim.')
    request['final_test_reservation']['custody_record']=None
    resources={v['verifier_name']:{r['resource_id']:r for r in v['resources']} for v in preflight['observed_setup']['resources']['verifiers']}
    deps=[]
    for rid,names in [('local-embedding-snapshot',('semantic','evidence')),('local-nli-snapshot',('evidence','confidence'))]:
        digests={resources[n][rid]['sha256'] for n in names}
        if len(digests)!=1: raise ValueError('shared resource relationship is not supported by observed hashes')
        deps.append(dict(resource_id=rid+':'+next(iter(digests)),verifiers=names,
            compromise_pathway='Proposed report-level shared-model compromise assumption, not measured independence.'))
    dependencies=DependencyRegistry(version=STUDY+'-proposed-v1',dependencies=deps,unresolved=tuple(costs))
    attack=AttackSpecification(version='report_corruption_v1',suppression='unavailable')
    loss=LossConfiguration(version=STUDY+'-proposed-loss-v1',false_accept=1.,false_reject=1.,uncertain=.2,
        resource_weight=.00001,cost_units='ms')
    provenance=PayoffProvenance(attack_specification=attack.specification_id,
        history_dataset=next(e['dataset_id'] for e in examples if e['role']=='history'),
        development_dataset=next(e['dataset_id'] for e in examples if e['role']=='development'),
        final_test_dataset=request['final_test_reservation']['dataset_id'],matrix_version=STUDY+'-matrix-v1',
        loss_configuration=loss.version,category='general',evidence_kind='empirical')
    selector=VerifierSelector(reputation_manager=ReputationManager(prior_alpha=1.,prior_beta=1.))
    config=dict(attempt_costs=tuple(costs.items()),budget=30000.,cost_units='ms',loss_configuration=loss,
        dependencies=dependencies,aggregation_versions=(('reputation_weighted','log_odds_v1'),('dependency_group','groups_v1')),
        provenance=provenance)
    context=capture_context(selector,analyzer.analyze(examples[0]['question']),context=examples[0]['reference'],**config)
    assert all(capture_context(selector,analyzer.analyze(e['question']),context=e['reference'],**config).compatibility_id==context.compatibility_id for e in examples)
    enumeration=enumerate_strategies(context)
    teams={s.verifiers:s.estimated_cost for s in enumeration.strategies}
    errors=[]
    try: RecordingRequest.model_validate(request)
    except ValueError as exc: errors=exc.errors(include_input=False,include_url=False)
    if {tuple(e['loc']) for e in errors}!={('preparation_authorization',),('final_test_reservation','custody_record')}:
        raise ValueError('unexpected request errors: '+str(errors))
    return {
      'recording-request.pending.json':request,
      'label-review.pending.json':dict(status='source_grounded_proposals_not_human_approved',labels=labels),
      'exclusions.json':dict(rule='known direct_fact analyzer cohort, fixed before new verifier execution; no observed accuracy predicate',rows=audit,cohorts=cohorts),
      'final-reservation.pending.json':request['final_test_reservation'],
      'planning-context.review-only.json':dict(status='not_fit_context; prior-only enumeration with historical sample-specific costs; replace with history snapshot and approved fresh calibration',context=context.model_dump(mode='json')),
      'teams.json':dict(status='conditional_structural_feasibility_not_research_readiness',strategies=enumeration.model_dump(mode='json'),
          teams=[dict(verifiers=k,size=len(k),historical_estimated_cost_ms=v) for k,v in teams.items()],
          participant_floor=context.minimum_participant_count,history_observations=0,
          dependency_groups=[g.model_dump(mode='json') for g in dependencies.groups(costs)],
          attacks=[a.model_dump(mode='json') for a in enumerate_attacks(dependencies,attack)]),
      'settings.pending.json':dict(status='unapproved',budget_ms=30000.,resource_weight_per_ms=.00001,
          loss=loss.model_dump(mode='json'),history_prior_alpha=1.,history_prior_beta=1.,threshold=.55,
          failure_contract='all_selected_returned',minimum_participants=context.minimum_participant_count,
          aggregations=['reputation_weighted','dependency_group'],dependencies=dependencies.model_dump(mode='json'),
          attacks=attack.model_dump(mode='json'),optimizer_tolerance=1e-8,scientific_reproducibility_atol=1e-12,
          sampling_seed=20261028,fit_authorized=False,freeze_record=None),
      'calibration-settings.pending.json':dict(measurements=None,final_test_reservation=request['final_test_reservation'],
          required_verifiers=list(costs),include_warmups=False,freeze_record=None),
      'readiness.json':dict(ready=False,policy_created=False,new_collection_executed=False,
          proposed_examples=4,history=dict(groups=1,examples=2,positive=1,negative=1),development=dict(groups=1,examples=2,positive=1,negative=1),
          reserved_metadata_entries=len(request['final_test_reservation']['examples']),excluded_existing_preparation_rows=4,
          verifier_attempts=16,local_generations_max=20,local_metadata_gets_max=68,downloads=0,paid_services=0,
          generation_timeouts_sum_seconds=1200,attempt_observation_model_hash_passes=34,
          new_index_jobs=0,warmups=0,retries=0,passes=1,
          request_validation_errors=errors,historical_calibration_id=calibration.calibration_id,
          historical_setup_matches_current=calibration.request.measurements.setup.model_dump(mode='json')==preflight['observed_setup'],
          costs_for_review_only=True,approval_required=['new narrowed capital scope and constructed negative candidates; labels and rubric','preparation execution permission for 16 calls/20 local generations/68 metadata GETs','metadata reservation witness and measurement freeze','proposed game settings before fitting'],
          owner_blockers=['evidence/retrieval: three reproduced existing contract probe failures','offline research readiness: evidence gate remains until reviewed repair','study owner: proposed scope/labels/run/settings are unapproved','custodian: witness procedural reservation and freeze actual measurements','collector/calibration producer: fresh complete reports and sample-specific costs','history reputation producer: derive counts only from new labelled history'],
          informative_contributors='Potential evidence+semantic or evidence+confidence; cannot certify frozen informative weights before new history. Rule supplies no factual check for these questions.',
          held_out_evidence=False),
    }


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir',type=Path,required=True)
    parser.add_argument('--study-dir',type=Path,required=True)
    parser.add_argument('--calibration',type=Path,required=True)
    parser.add_argument('--adapter-config',type=Path,required=True)
    parser.add_argument('--index-receipt',type=Path,required=True)
    args=parser.parse_args(argv)
    if args.output_dir.exists(): raise FileExistsError('preserve original proposal; output directory must be new')
    # Reject custody or original mixed candidate-file access from any imported path.
    def guard(event,arguments):
        if event=='socket.connect': raise AssertionError('no network in preparation')
        if event=='open' and isinstance(arguments[0],str):
            p=Path(arguments[0]).resolve()
            if 'custody' in p.parts or p==ROOT/'data/test_benchmark.jsonl':
                raise AssertionError('final/mixed candidate payload may not be opened')
    sys.addaudithook(guard)
    paths=[(args.study_dir/'recording-request.draft.json').resolve(),args.adapter_config.resolve(),
           args.calibration.resolve(),args.index_receipt.resolve()]
    before={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    adapter=read_json(paths[1])
    if local_path(adapter['index_receipt']) != paths[3]:
        raise ValueError('explicit index receipt must match the adapter configuration')
    preflight=inspect_setup(adapter)
    data=package(read_json(paths[0]),read_json(paths[2]),preflight)
    data['resource-preflight.json']=preflight
    data['provenance.json']=dict(input_sha256=before,revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        no_verifier_inference=True,no_calibration_run=True,no_fit=True,final_payload_guard=True,
        original_cost_campaign='Historical cost-only approval does not authorize this study or supply labels/reports',
        proposal_date='2026-10-28',producer_source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    data['approval-binding.pending.json']=dict(approved=False,proposal_digest=content_id(data),
        bound_files=sorted(data), digest_definition='content_id of {name: parsed JSON for name in bound_files}; pending nulls intentionally included')
    args.output_dir.mkdir(parents=True)
    for name,value in data.items():
        with (args.output_dir/name).open('x',encoding='utf-8') as f: json.dump(value,f,indent=2,sort_keys=True,allow_nan=False)
    assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in before.items())
    print(json.dumps(dict(status='prepared_pending_approval_and_evidence_repair',output=str(args.output_dir),
        proposal_digest=data['approval-binding.pending.json']['proposal_digest'],teams=len(data['teams.json']['teams']),attempts=16)))

if __name__=='__main__':
    main()
