"""Freeze required-resource equivalence before reserved collection; no refit."""
import json,hashlib
from pathlib import Path
from app.game.offline.compound import load_candidate,requests
from app.game.offline.calibration import MeasurementSetup
from app.game.component_execution import ComponentPolicy
from app.game.models import content_id
ROOT=Path('artifacts/remaining-category-studies-v1')
def main():
    frozen=load_candidate(ROOT/'compound-85/candidate');target=ROOT/'scoped-er-v1'
    report=json.loads((target/'inspection.json').read_text(encoding='utf-8'));setup=MeasurementSetup.model_validate(report['observed_setup'])
    expected=tuple(v for v in frozen.setup.resources.verifiers if v.verifier_name in {'evidence','rule'})
    assert setup.resources.verifiers==expected
    assert ComponentPolicy.model_validate_json((ROOT/'compound-85/candidate/policy.json').read_text(encoding='utf-8'))==frozen.policy
    for cid,req in requests(frozen.study,setup,'final_test',freeze_id=frozen.freeze_id).items():
        with (target/(cid+'.json')).open('x',encoding='utf-8') as f:f.write(req.model_dump_json(indent=2))
    files=['scripts/scoped_er_adapter.py','scripts/scoped_compound_bridge.py','scripts/evaluate_scoped_compound.py','scripts/prepare_scoped_compound.py']
    transfer=dict(version='compound_required_resource_transfer_v1',original_freeze_id=frozen.freeze_id,original_policy_id=frozen.policy.policy_id,
        original_full_resource_id=frozen.setup.resources.manifest_id,scoped_resource_id=setup.resources.manifest_id,scoped_setup=setup.model_dump(mode='json'),
        study_id=frozen.study.study_id,required_entries_exactly_equal=True,policy_bytes_unchanged=True,decision_semantics_unchanged=True,
        no_refit=True,scope=['evidence','rule'],network_forbidden=True,history_development_provenance='Original full-roster recordings unchanged; new scoped final records validated separately.',
        code_hashes={p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in files},authorization='User attachment2ebba2cc: scoped Evidence/Rule correction and96 reserved calls, zero generations.')
    transfer['transfer_id']=content_id(transfer)
    with (target/'transfer.json').open('x',encoding='utf-8') as f:json.dump(transfer,f,indent=2)
    print('SCOPED_TRANSFER_FROZEN',transfer['transfer_id'],flush=True)
if __name__=='__main__':main()
