"""Evaluate once under the pre-outcome transfer; never fit or edit policies."""
import hashlib,json
from pathlib import Path
from app.game.offline.compound import load_candidate,JointRecordings
from app.game.offline.calibration import MeasurementSetup
from scripts.evaluate_scoped_compound import evaluate_scoped
def main():
    root=Path('artifacts/remaining-category-studies-v1');folder=root/'scoped-er-v1'
    read=lambda p:json.loads(Path(p).read_text(encoding='utf-8'))
    proof=read(folder/'transfer.json')
    for path,digest in proof['code_hashes'].items():
        if hashlib.sha256(Path(path).read_bytes()).hexdigest()!=digest:raise ValueError('scoped evaluation freeze changed')
    frozen=load_candidate(root/'compound-85/candidate')
    if frozen.freeze_id!=proof['original_freeze_id']:raise ValueError('original freeze differs')
    test=JointRecordings.model_validate(read(folder/'test/joint.json'));setup=MeasurementSetup.model_validate(proof['scoped_setup'])
    result=evaluate_scoped(frozen,test,setup)
    result.update(transfer_id=proof['transfer_id'],original_policy_unchanged=True,scoped_resource_id=setup.resources.manifest_id,
        interpretation='Original policy evaluated using exact required-resource equivalence proof; actual scoped recordings retained unchanged. No refit or historical relabeling.')
    with (folder/'reserved-results.json').open('x',encoding='utf-8') as f:json.dump(result,f,indent=2)
    print(json.dumps({k:v for k,v in result.items() if k in ('actual_test_calls','measured_test_attempt_ms')}),flush=True)
if __name__=='__main__':main()
