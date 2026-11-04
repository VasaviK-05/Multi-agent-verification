"""Conditional reserved preparation/evaluation after a feasible reference freeze."""
import argparse,hashlib,json,random,subprocess,sys
from pathlib import Path
from app.game.models import content_id,Strategy
from app.game.artifacts import PolicyArtifact
from app.game.offline.collection import RecordingBundle,HeldoutRecordingRequest
from app.game.offline.records import TrainingManifest,DatasetManifest
from app.game.offline.attacks import AttackSpecification,enumerate_attacks
from app.game.offline.evaluation import evaluate_final_test,summarize
from app.game.offline.replay import replay
from scripts.evaluate_flexible_heldout import export_final
from scripts.fit_reference_study import ROOT,read,save
def checked():
    freeze=read(ROOT/'fit/freeze.json')
    for path,digest in freeze['source_hashes'].items():
        if hashlib.sha256(Path(path).read_bytes()).hexdigest()!=digest:raise ValueError('frozen code differs')
    artifact=PolicyArtifact.model_validate(read(ROOT/'fit/policy.json'))
    if (artifact.artifact_id!=freeze['artifact_id'] or artifact.policy.policy_id!=freeze['policy_id']):raise ValueError('frozen policy differs')
    manifest=TrainingManifest.model_validate(read(ROOT/'fit/training-manifest.json'))
    if manifest.manifest_id!=freeze['training_manifest_id']:raise ValueError('frozen training differs')
    return freeze,artifact,manifest
def collect(source):
    freeze,artifact,manifest=checked();data=read(ROOT/'request.json')
    data.update(version='offline_heldout_recording_v1',intended_use='heldout',freeze_id=content_id(freeze),
        permitted_datasets=[['final_test','reference-fresh-v1-final_test']],examples=read(ROOT/'reserved-examples.json'))
    request=HeldoutRecordingRequest.model_validate(data)
    assert len(request.examples)==20 and request.final_test_reservation==manifest.final_test_reservation
    save(ROOT/'reserved-request.json',request)
    save(ROOT/'reserved-seal.json',dict(freeze_id=content_id(freeze),request_sha256=hashlib.sha256((ROOT/'reserved-request.json').read_bytes()).hexdigest(),
        freeze_sha256=hashlib.sha256((ROOT/'fit/freeze.json').read_bytes()).hexdigest()))
    subprocess.run([sys.executable,str(Path('scripts/collect_reference_reserved.py').resolve()),'--study',str(ROOT.resolve()),'--source',str(source.resolve()),'--output',str((ROOT/'test').resolve())],cwd=source.resolve().parents[1],check=True)
def evaluate():
    freeze,artifact,manifest=checked();bundle=RecordingBundle.model_validate(read(ROOT/'test/reference/bundle.json'))
    if bundle.request.freeze_id!=content_id(freeze):raise ValueError('test freeze differs')
    context=artifact.context;contract=artifact.contract;attacks=AttackSpecification(**freeze['protocol']['attacks'])
    final=export_final(bundle,context,manifest.final_test_reservation)
    DatasetManifest(version='reference-released-v1',evidence_kind='empirical',partitions=(*manifest.partitions,final))
    result=evaluate_final_test(artifact.policy,context,manifest,contract,attacks,final_partition=final)
    fixed=next(s for s in artifact.policy.strategies if s.strategy_id==freeze['best_fixed_strategy_id']);greedy=Strategy.model_validate(freeze['greedy_strategy'])
    actions=enumerate_attacks(context.dependencies,attacks);metrics={};clean={};baselines=[]
    for name,s in (('development_best_fixed',fixed),('coverage_aware_greedy',greedy)):
        metrics[name]={}
        for attack in actions:
            rows=[replay(context,s,attack,attacks,contract,e) for e in final.examples];m=summarize(tuple((o,1.) for o in rows),context.loss_configuration)
            metrics[name][attack.kind]=dict(**m.model_dump(mode='json'),decision_loss=m.validation_loss(context.loss_configuration))
            baselines.extend(dict(method=name,**o.model_dump(mode='json')) for o in rows)
            if attack.kind=='clean':clean[name]=[(o,1.) for o in rows]
    metrics['policy']={}
    for attack in actions:
        m=dict(result.attack_metrics)[attack.attack_id]
        metrics['policy'][attack.kind]=dict(**m.model_dump(mode='json'),decision_loss=m.validation_loss(context.loss_configuration))
    weights=dict(artifact.policy.solution.probabilities)
    clean['policy']=[(o,weights[o.strategy_id]) for o in result.outcomes if o.attack_id==actions[0].attack_id]
    groups=sorted({e.split_identity for e in final.examples});lookup={e.example_id:e.split_identity for e in final.examples};rng=random.Random(1103)
    draws=[[rng.choice(groups) for _ in groups] for _ in range(1000)];intervals={}
    for name,rows in clean.items():
        estimates=[]
        for draw in draws:
            selected=[(o,w) for g in draw for o,w in rows if lookup[o.example_id]==g]
            # Repeated groups use explicit sums; summarize requires unique examples.
            n=2*len(draw);dec=sum(w for o,w in selected if o.public_status!='uncertain');fa=sum(w for o,w in selected if o.public_status=='passed' and not o.answer_is_correct);fr=sum(w for o,w in selected if o.public_status=='failed' and o.answer_is_correct)
            estimates.append(dict(coverage=dec/n,decision_loss=(fa+fr+.2*(n-dec))/n,selective_risk=(fa+fr)/dec if dec else None))
        intervals[name]={}
        for key in ('coverage','decision_loss','selective_risk'):
            values=sorted(e[key] for e in estimates if e[key] is not None)
            intervals[name][key]=dict(interval95=[values[24],values[974]] if len(values)==1000 else None,undefined_fraction=1-len(values)/1000)
    output=ROOT/'evaluation';output.mkdir(exist_ok=False)
    save(output/'policy-evaluation.json',result);save(output/'baseline-outcomes.json',baselines);save(output/'final-partition.json',final)
    save(output/'results.json',dict(freeze_id=content_id(freeze),metrics=metrics,cluster_bootstrap=intervals,groups=10,seed=1103,resamples=1000,
        actual_attempts=sum(a.executed for a in bundle.attempts),measured_attempt_ms={n:dict(count=len(v),mean=sum(v)/len(v)) for n in ('semantic','evidence','rule','confidence') if (v:=[a.duration_ms for a in bundle.attempts if a.executed and a.candidate==n])},
        limitations='Ten procedurally reserved frame clusters; structural families shared. Zero empirical error is not population safety. No post-test refit or reputation updates.'))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['collect','evaluate']);p.add_argument('--source',type=Path);a=p.parse_args()
    collect(a.source) if a.action=='collect' else evaluate()
