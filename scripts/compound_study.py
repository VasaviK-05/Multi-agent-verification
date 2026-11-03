"""Opt-in empirical producer CLI. Preparation refuses an undersized corpus.

Run as python -m scripts.compound_study from the feature worktree. Collection is
isolated in the resource-compatible original checkout; no API is activated.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from app.game.component_sources import source_manifest
from app.game.models import PlanningContext
from app.game.offline.compound import (prepare,SourceCapacityError,Study,Training,JointRecordings,
    requests,fit,export_candidate,load_candidate,evaluate_frozen,verify_code,source_hashes,PartitionSizes)
from app.game.offline.calibration import MeasurementSetup


def read(path):return json.loads(Path(path).read_text(encoding='utf-8'))
def save(path,value):
    if hasattr(value,'model_dump'):value=value.model_dump(mode='json')
    with Path(path).open('x',encoding='utf-8') as handle:json.dump(value,handle,indent=2,sort_keys=True)


def audit(source,output):
    output.mkdir(parents=True,exist_ok=False)
    paths=[source/'corpus.json',source/'sources/geonames-countryInfo.txt',source/'sources/countries.json']
    sources=source_manifest(*(p.read_bytes() for p in paths))
    save(output/'source-manifest.json',sources)
    eligible={f.descriptor.source_id for f in sources.facts}-{'BH','BE'}
    save(output/'capacity.json',dict(required_groups=48,required_partition_groups=dict(history=16,development=16,final_test=16),
        numeric_source_groups=len({f.descriptor.source_id for f in sources.facts}),eligible_groups=len(eligible),
        excluded_previously_explored_entities=['BH','BE'],eligible_source_ids=sorted(eligible),
        enough_groups=len(eligible)>=48,exploratory_source_known=True,
        source_files={str(p.resolve()):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
        inference_attempts=0,corpus_expansion=False,index_rebuild=False))
    # inspect_setup reads local source/model/index receipts and saved metadata only.
    original=source.parents[1]
    code='import json,sys; from app.benchmark.project_adapter import inspect_setup; print(json.dumps(inspect_setup(json.load(open(sys.argv[1])))))'
    result=subprocess.run([sys.executable,'-c',code,str((source/'adapter.json').resolve())],cwd=original,
        capture_output=True,text=True,encoding='utf-8',check=True)
    save(output/'local-resource-preflight.json',json.loads(result.stdout))
    return sources


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['audit','prepare','collect','fit','evaluate'])
    p.add_argument('--source',type=Path);p.add_argument('--audit',type=Path);p.add_argument('--study',type=Path)
    p.add_argument('--history',type=Path);p.add_argument('--development',type=Path);p.add_argument('--frozen',type=Path)
    p.add_argument('--test',type=Path);p.add_argument('--role',choices=['history','development','final_test'])
    p.add_argument('--resume-from',type=Path);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--design',choices=['original48','amended36'],default='original48')
    a=p.parse_args()
    if a.action=='audit':audit(a.source.resolve(),a.output);return 0
    if a.action=='prepare':
        from app.game.component_sources import SourceManifest
        sources=SourceManifest.model_validate(read(a.audit/'source-manifest.json'))
        capacity=read(a.audit/'capacity.json')
        for path,digest in capacity['source_files'].items():
            if hashlib.sha256(Path(path).read_bytes()).hexdigest()!=digest:raise ValueError('source material changed after audit')
        context=PlanningContext.model_validate_json((Path(__file__).resolve().parents[1]/'artifacts/flexible-teams-v1/arithmetic-minimum-1/context.json').read_text())
        a.output.mkdir(parents=True,exist_ok=False)
        sizes=PartitionSizes(version='amended_36_v1',history=12,development=12,final_test=12) if a.design=='amended36' else None
        count=36 if sizes else 48;per=12 if sizes else 16
        authorization=('User attachment 4976affc: amended36 exploratory study; maximum288 Evidence/Rule attempts; zero Confidence generations'
            if sizes else 'User attachment bc7596ea: bounded Evidence/Rule study; zero Confidence generations')
        save(a.output/'predeclared-intent.json',dict(source_manifest_id=sources.manifest_id,groups=count,
            partitions=dict(history=per,development=per,final_test=per),variants=['correct','wrong_math','wrong_base','both_wrong'],
            max_examples=count*4,max_attempts=288 if sizes else 768,planned_attempts_if_feasible=count*8,max_confidence_generations=0,
            candidate_assignments=dict(base_fact=['evidence'],derived_sum=['rule']),
            threshold=.55,coverage_minimum=.9,loss=context.loss_configuration.model_dump(mode='json'),
            dependencies=context.dependencies.model_dump(mode='json'),
            budget_rule='sum_component_mean_history_development_attempt_ms_v1',
            objective='worst_validation_then_equal_plan_cost_v1',
            whole_label='base_correct AND derived_equals_claimed_base_plus_increment',
            group_rule='all measures/increments/templates/variants sharing entity stay in one partition',
            exclusions=['BH','BE'],source_known_exploratory=True,
            authorization=authorization,amends='artifacts/compound-empirical-v2/preparation' if sizes else None,
            bootstrap_seed=1102,bootstrap_replicates=1000,partition_order_seed='compound-study-v2',
            baseline='development-best fixed Evidence-fact/Rule-calculation aggregation',
            scope='source-known exploratory; reduced precision with12 reserved entity groups' if sizes else 'source-known exploratory'))
        try:study=prepare(sources,context.loss_configuration,context.dependencies,
            authorization,partition_sizes=sizes,source_files=tuple(capacity['source_files'].items()))
        except SourceCapacityError as exc:
            save(a.output/'blocked.json',dict(status='insufficient_independent_groups',reason=str(exc),
                actual_attempts=0,policy_exported=False,partitions_assigned=False,study_shrunk=False))
            print(str(exc));return 2
        preflight=read(a.audit/'local-resource-preflight.json')
        if not preflight['ready']:raise ValueError(preflight['blockers'])
        save(a.output/'study.json',study);save(a.output/'setup.json',preflight['observed_setup']);return 0
    if a.action=='collect':
        study=Study.model_validate(read(a.study/'study.json'));setup=MeasurementSetup.model_validate(read(a.study/'setup.json'))
        frozen=load_candidate(a.frozen) if a.role=='final_test' else None
        if frozen is not None and (frozen.study!=study or frozen.setup!=setup):raise ValueError('candidate differs from reserved study/setup')
        prepared=requests(study,setup,a.role,freeze_id=frozen.freeze_id if frozen else None)
        # Persist all request identities before the resource-compatible bridge loads models.
        staging=a.output.with_name(a.output.name+'-prepared');staging.mkdir(parents=True,exist_ok=False)
        for cid,request in prepared.items():save(staging/(cid+'.json'),request)
        save(staging/'study.json',study)
        save(staging/'bridge.json',dict(study_id=study.study_id,role=a.role,
            setup=setup.model_dump(mode='json'),requests={cid:hashlib.sha256((staging/(cid+'.json')).read_bytes()).hexdigest() for cid in prepared},
            source_manifest_id=study.sources.manifest_id,freeze_id=frozen.freeze_id if frozen else None,
            study_sha256=hashlib.sha256((staging/'study.json').read_bytes()).hexdigest(),source_hashes=source_hashes()))
        original=a.source.resolve().parents[1]
        command=[sys.executable,str(Path(__file__).with_name('collect_compound_partition.py').resolve()),
            '--prepared',str(staging.resolve()),'--source',str(a.source.resolve()),'--output',str(a.output.resolve())]
        if a.resume_from:command+=['--resume-from',str(a.resume_from.resolve())]
        if a.frozen:command+=['--frozen',str(a.frozen.resolve())]
        subprocess.run(command,cwd=original,check=True);return 0
    if a.action=='fit':
        study=Study.model_validate(read(a.study/'study.json'));setup=MeasurementSetup.model_validate(read(a.study/'setup.json'))
        training=Training(study=study,setup=setup,history=read(a.history/'joint.json'),development=read(a.development/'joint.json'))
        result=fit(training)
        if result['policy'] is None:
            a.output.mkdir(parents=True,exist_ok=False)
            save(a.output/'infeasible.json',dict(status=result['status'],matrix=result['matrix'].model_dump(mode='json'),
                solution=result['solution'].model_dump(mode='json'),outcomes=result['outcomes'],threshold_changed=False,coverage_changed=False))
            return 2
        export_candidate(training,result,a.output);return 0
    frozen=load_candidate(a.frozen);test=JointRecordings.model_validate(read(a.test/'joint.json'))
    result=evaluate_frozen(frozen,test);a.output.mkdir(parents=True,exist_ok=False)
    save(a.output/'reserved-results.json',result);return 0


if __name__=='__main__':raise SystemExit(main())
