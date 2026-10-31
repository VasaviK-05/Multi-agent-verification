"""Explicitly synthetic package fixtures; no project recordings or model calls."""
from dataclasses import asdict
import hashlib
import json
from types import SimpleNamespace
import pytest
from app.game.prototype_bundle import BundleFile,PrototypeEntry,PrototypeManifest,load_prototype,safe_payload
from app.game.models import PlanningContext,content_id
from app.game.artifacts import DeploymentEpisode
from app.game.task_conditioning import bind_task_history,TaskSnapshotBinding

@pytest.fixture(scope='module')
def synthetic():
    from tests.test_game_reliability_first import full_fixture
    from app.game.execution_contract import ExecutionContract
    from app.game.offline.evaluation import bind_evaluation,construct_payoffs,export_artifact
    from app.game.offline.reliability import fit_reliability_first
    c,m,k,a,*_=full_fixture()
    from app.game.models import canonical_json
    from app.game.offline.replay import category_id
    from app.game.offline.records import TrainingManifest
    plan=json.loads(c.selection_json);plan['reference_available']=True
    c=PlanningContext(**{**c.model_dump(),'selection_json':canonical_json(plan),'offline_evaluation_id':None,'execution_contract_json':None})
    records=m.model_dump()
    for partition in records['partitions']:
        for e in partition['examples']:e.update(reference='SYNTHETIC reference',planning_category=category_id(c))
    m=TrainingManifest.model_validate(records);c=bind_task_history(c,m)
    k=ExecutionContract(**{**k.model_dump(),'version':'offline_public_decision_v4','coverage_version':'task_output_contract_v2'})
    c=bind_evaluation(c,m,k,a);e=construct_payoffs(c,m,k,a)
    c,p=fit_reliability_first(c,m,k,a,e,minimum=.5)
    artifact=export_artifact(p,c,m,k,a,applicable_domain='general')
    episode=DeploymentEpisode(episode_id='SYNTHETIC package',context=c,contract=k,execution_configuration_id=k.execution_configuration_id)
    payloads={'policy.json':artifact.model_dump(mode='json'),'episode.json':episode.model_dump(mode='json'),
        'reputation.json':[asdict(s) for s in c.plan.reputation_statistics],
        'costs.json':dict(calibration_id='SYNTHETIC cost reference',budget=c.budget,units=c.cost_units,attempt_costs=c.attempt_costs),
        'resources.json':k.resource_manifest.model_dump(mode='json'),'metrics.json':dict(artifact_id=artifact.artifact_id,
            all_strategies=[dict(**s.model_dump(mode='json'),probability=dict(p.solution.probabilities)[s.strategy_id]) for s in p.strategies])}
    b=TaskSnapshotBinding.model_validate_json(c.task_conditioning_json)
    entry=PrototypeEntry(task='arithmetic',experimental=False,artifact_path='policy.json',episode_path='episode.json',
        reputation_path='reputation.json',costs_path='costs.json',resources_path='resources.json',metrics_path='metrics.json',
        artifact_id=artifact.artifact_id,compatibility_id=c.compatibility_id,task_id=b.identity.task_id,
        reputation_snapshot_id=c.reputation_snapshot_id,execution_configuration_id=k.execution_configuration_id,
        calibration_id='SYNTHETIC cost reference',expected_clean_coverage=.5,allowed_question_ids=(content_id('SYNTHETIC question'),))
    return payloads,entry

def write_package(root,synthetic):
    payloads,entry=synthetic
    for name,value in payloads.items():(root/name).write_text(json.dumps(value),encoding='utf-8')
    return seal(root,entry)

def seal(root,entry):
    files=tuple(BundleFile(path=p.name,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted(root.iterdir()) if p.name!='manifest.json')
    manifest=PrototypeManifest(version='bounded_task_policy_bundle_v1',approval='SYNTHETIC fixture',entries=(entry,),files=files)
    (root/'manifest.json').write_text(manifest.model_dump_json(),encoding='utf-8');return manifest

def test_reload_exact_identities_and_no_synthetic_production_permission(tmp_path,synthetic):
    m=write_package(tmp_path,synthetic)
    with pytest.raises(ValueError,match='test-only'):load_prototype(tmp_path)
    loaded=load_prototype(tmp_path,allow_synthetic_for_tests=True)
    assert loaded.manifest.bundle_id==m.bundle_id
    assert loaded.artifacts[0].artifact_id==m.entries[0].artifact_id
    assert len(loaded.provider().snapshot())==1

@pytest.mark.parametrize('path',['../policy.json','/policy.json','C:/private.json','a\\b.json','a/../b.json'])
def test_relative_paths_cannot_escape(path):
    with pytest.raises(ValueError):BundleFile(path=path,sha256='a'*64)

@pytest.mark.parametrize('name',['costs.json','resources.json','reputation.json','episode.json','metrics.json'])
def test_cross_file_contracts_reject_even_when_rehashed(tmp_path,synthetic,name):
    _,entry=synthetic;write_package(tmp_path,synthetic)
    data=json.loads((tmp_path/name).read_text())
    if name=='costs.json':data['budget']+=1
    elif name=='resources.json':data['verifiers'][0]['resources'][0]['sha256']='b'*64
    elif name=='reputation.json':data[0]['posterior_mean']=.01
    elif name=='metrics.json':data['all_strategies'][0]['probability']=.123
    else:data['execution_configuration_id']='SYNTHETIC incompatible'
    (tmp_path/name).write_text(json.dumps(data));seal(tmp_path,entry)
    with pytest.raises(ValueError):load_prototype(tmp_path,allow_synthetic_for_tests=True)

def test_corruption_and_unlisted_private_files_reject(tmp_path,synthetic):
    write_package(tmp_path,synthetic)
    policy=tmp_path/'policy.json';original=policy.read_bytes();policy.write_bytes(original+b' ')
    with pytest.raises(ValueError,match='digest'):load_prototype(tmp_path,allow_synthetic_for_tests=True)
    policy.write_bytes(original);(tmp_path/'private-recordings.json').write_text('{}')
    with pytest.raises(ValueError,match='unlisted'):load_prototype(tmp_path,allow_synthetic_for_tests=True)

def test_privacy_scan_keeps_urls_but_rejects_private_paths():
    safe_payload(b'{"url":"http://localhost:11434/api/generate"}')
    for value in (b'C:/Users/private/model',b'/home/user/token',b'Bearer secret-token'):
        with pytest.raises(ValueError):safe_payload(value)

def test_outside_prototype_scope_fails_before_dispatch(tmp_path,synthetic):
    from tests.test_game_foundation import analysis
    write_package(tmp_path,synthetic);loaded=load_prototype(tmp_path,allow_synthetic_for_tests=True)
    result=loaded.router().run(None,analysis(),SimpleNamespace(question='Outside synthetic scope',context=None),'SYNTHETIC',
        provider=None,rng=None,resource_observer=None)
    assert result.summary['selection_status']=='study_scope_mismatch' and result.public_status=='uncertain'
