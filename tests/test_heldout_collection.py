"""Held-out opt-in keeps existing recording/calibration exclusion semantics."""
import pytest
from app.game.models import content_id
from app.game.offline.collection import HeldoutRecordingRequest,collect,completeness,measurement_input,export_training,RecordingRequest
from app.game.offline.records import FinalTestReservation,ReservedExample
from tests.test_game_collection import fixture


def request_fixture():
    request,pool,setup,observer,*_=fixture()
    data=request.model_dump();e=data['examples'][0];e.update(role='final_test',purpose='heldout',dataset_id='synthetic-final')
    reservation=FinalTestReservation(version='final_test_reservation_v1',role='final_test',dataset_id='synthetic-final',custody_record='synthetic',examples=(ReservedExample(example_id=e['example_id'],split_identity=e['split_identity'],question_id=e['question_id'],content_identity=content_id([e['question'],e['answer'],e['reference']]),validation_id=e['run_id']),))
    data.update(version='offline_heldout_recording_v1',intended_use='heldout',study_approval='synthetic test authorization',freeze_id='a'*64,permitted_datasets=(('final_test','synthetic-final'),),examples=[e],final_test_reservation=reservation)
    return HeldoutRecordingRequest(**data),pool,setup,observer


def test_heldout_collect_retains_timings_but_cannot_calibrate_or_fit():
    request,pool,setup,observer=request_fixture()
    rows=[];starts=[]
    b=collect(request,pool,setup,observer,sink=rows.append,on_start=starts.append)
    assert completeness(b)['complete']
    assert rows and all(r.measurement.role=='final_test' for r in rows)
    assert len(starts)==len(rows)
    with pytest.raises(ValueError,match='cannot enter calibration'):measurement_input(b)
    with pytest.raises(ValueError,match='cannot enter fitting'):export_training(b,None)
    with pytest.raises(ValueError):RecordingRequest.model_validate(request.model_dump())


def test_exact_reservation_is_enforced_before_dispatch():
    request,*_=request_fixture();data=request.model_dump();data['examples'][0]['answer']='tampered'
    with pytest.raises(ValueError,match='exact frozen reservation'):HeldoutRecordingRequest(**data)


def test_labels_are_never_dispatched_and_resume_does_not_repeat():
    request,pool,setup,observer=request_fixture()
    b=collect(request,pool,setup,observer)
    calls=[len(v.calls) for v in pool]
    assert all(v.calls==[(request.examples[0].question,request.examples[0].answer,request.examples[0].reference)] for v in pool)
    resumed=collect(request,pool,setup,observer,completed=b.attempts)
    assert [len(v.calls) for v in pool]==calls and resumed.attempts==b.attempts


def test_grouped_bootstrap_preserves_paired_method_equivalence():
    from types import SimpleNamespace as N
    from scripts.evaluate_flexible_heldout import bootstrap
    examples=[N(example_id=str(i),split_identity=str(i//2)) for i in range(8)]
    rows=[N(example_id=str(i),public_status='passed' if i%2==0 else 'failed',answer_is_correct=i%2==0) for i in range(8)]
    methods={name:rows for name in ('frozen_flexible','development_best_fixed','coverage_aware_greedy')}
    result=bootstrap(methods,examples)
    assert result['paired_differences']['frozen_flexible-minus-development_best_fixed']['coverage']['interval95']==[0.,0.]
    for r in rows:r.public_status='uncertain'
    result=bootstrap(methods,examples)
    assert result['methods']['frozen_flexible']['selective_risk']['interval95'] is None
    assert result['methods']['frozen_flexible']['selective_risk']['undefined_resample_fraction']==1.


def test_final_export_checks_analysis_against_frozen_planning():
    import json
    from app.game.models import PlanningContext
    from scripts.evaluate_flexible_heldout import export_final
    request,pool,setup,observer=request_fixture()
    context=fixture()[-2];data=context.model_dump();plan=json.loads(data['selection_json'])
    plan.update(difficulty='hard',difficulty_score=.8);data['selection_json']=json.dumps(plan)
    matching=PlanningContext(**data);bundle=collect(request,pool,setup,observer)
    final=export_final(bundle,matching,request.final_test_reservation)
    assert len(final.examples)==1 and final.role=='final_test'
    plan.update(difficulty='easy',difficulty_score=.1);data['selection_json']=json.dumps(plan)
    incompatible=PlanningContext(**data)
    with pytest.raises(ValueError,match='planning requirements'):export_final(bundle,incompatible,request.final_test_reservation)


def test_windows_source_hash_gate_allows_only_separately_sealed_collector(tmp_path,monkeypatch):
    import hashlib
    from scripts.evaluate_flexible_heldout import validate_frozen_sources
    monkeypatch.chdir(tmp_path)
    folder=tmp_path/'app'/'game'/'offline';folder.mkdir(parents=True)
    (folder/'collection.py').write_text('explicit opt-in collector extension')
    decision=tmp_path/'app'/'game'/'finalization.py';decision.write_text('frozen decision code')
    expected=hashlib.sha256(decision.read_bytes()).hexdigest()
    freeze={'source_hashes':{r'app\game\offline\collection.py':'old collector hash',r'app\game\finalization.py':expected}}
    validate_frozen_sources(freeze)
    decision.write_text('unexpected decision change')
    with pytest.raises(ValueError,match='source code changed'):validate_frozen_sources(freeze)
