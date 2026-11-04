"""Explicit post-development amendment; reuse recordings without inference."""
import json
from pathlib import Path
from app.game.component_execution import CompoundFittingConfiguration
from app.game.offline.compound import Training,fit,export_candidate,load_candidate

ROOT=Path('artifacts/remaining-category-studies-v1')
OLD=Path('artifacts/compound-study-36-v1')
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def main():
    training=Training(study=read(OLD/'preparation/study.json'),setup=read(OLD/'preparation/setup.json'),
        history=read(OLD/'history/joint.json'),development=read(OLD/'development/joint.json'))
    config=CompoundFittingConfiguration(original_study_id=training.study.study_id,
        authorization='User attachment 9d033868: separately versioned 85% exploratory configuration chosen after development; only coverage constraint changes.')
    original=fit(training)
    revised=fit(training,fitting_configuration=config)
    assert original['policy'] is None and original['matrix'].clean_coverage.minimum==.9
    assert revised['matrix'].clean_coverage.minimum==.85
    assert original['outcomes']==revised['outcomes'] or [
        {k:v for k,v in o.items() if k!='strategy_id'} for o in original['outcomes']]==[
        {k:v for k,v in o.items() if k!='strategy_id'} for o in revised['outcomes']]
    assert original['matrix'].values==revised['matrix'].values
    assert revised['policy'] is not None
    frozen=export_candidate(training,revised,ROOT/'compound-85/candidate',code_files=(Path(__file__),))
    assert load_candidate(ROOT/'compound-85/candidate')==frozen
    (ROOT/'compound-85/amendment.json').write_text(json.dumps(dict(configuration=config.model_dump(mode='json'),
        original_status=original['status'],revised_status=revised['status'],freeze_id=frozen.freeze_id,
        unchanged_payoffs=True,unchanged_validation_values=True,original_matrix_id=original['matrix'].matrix_id,
        original_artifact='artifacts/compound-study-36-v1/candidate/infeasible.json',
        reserved_outcomes_absent_before_freeze=not (OLD/'test').exists(),new_attempts=0),indent=2),encoding='utf-8')
    print('FROZEN',frozen.freeze_id,flush=True)
if __name__=='__main__':main()
