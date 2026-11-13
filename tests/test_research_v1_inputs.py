"""Permitted Development question metadata; never source labels or verifier calls."""
import json
import os
from pathlib import Path

from pydantic import TypeAdapter, ValidationError
import pytest

from app.game.dependencies import identifier
from app.game.models import content_id
from app.game.offline.collection import PreparationExample, RecordingRequest
from app.game.offline.input_contract import QuestionText
from app.game.offline.records import Attempt, Example
from tests.test_game_collection import fixture

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'docs/research_v1-recording-handoff/development-verifier-inputs.source.json'
ROWS=json.loads(SOURCE.read_text()) if SOURCE.exists() else []
AFFECTED=[r for r in ROWS if r['question']!=r['question'].strip()]


def require_private_source():
    if not SOURCE.exists():
        if os.environ.get('RESEARCH_V1_REQUIRE_PRIVATE_INPUTS')=='1':
            pytest.fail('Required private Development metadata is absent; materialize approved artifacts first')
        pytest.skip('Private Development metadata is intentionally not published; no real-input validation claimed')


def test_all_affected_metadata_accounted_for():
    require_private_source()
    assert len(AFFECTED)==18
    assert len({r['related_group_id'] for r in AFFECTED})==9
    assert all(r['benchmark']=='HotpotQA' for r in AFFECTED)


@pytest.mark.parametrize('row',AFFECTED or [None],ids=lambda r:r['candidate_id'] if r else 'private-metadata-required')
def test_verbatim_question_survives_offline_schema_and_export(row):
    require_private_source()
    # Only the source tuple/IDs are used. No provisional label is promoted.
    request,*_=fixture(names=('a',))
    template=request.examples[1].model_dump(mode='json')
    template.update(example_id=row['candidate_id'],question_id=row['question_id'],
                    split_identity=row['related_group_id'],question=row['question'],
                    answer=row['candidate_answer'])
    parsed=PreparationExample.model_validate(template)
    restored=PreparationExample.model_validate_json(parsed.model_dump_json())
    assert restored.question.encode('utf-8')==row['question'].encode('utf-8')
    assert restored.answer.encode('utf-8')==row['candidate_answer'].encode('utf-8')
    assert restored.content_identity==content_id([row['question'],row['candidate_answer'],None])
    assert restored.content_identity!=content_id([row['question'].strip(),row['candidate_answer'],None])
    data=request.model_dump(mode='json');data['examples']=[restored.model_dump(mode='json')]
    assert RecordingRequest.model_validate(data).examples[0].question==row['question']
    attempt=Attempt(verifier_name='a',state='unavailable',execution_id=restored.run_id,
        configuration_id=request.execution_configuration_id,adapter='generic_v1',report_provenance='SYNTHETIC exclusion')
    exported=Example(example_id=restored.example_id,split_identity=restored.split_identity,
        question_id=restored.question_id,question=restored.question,answer=restored.answer,reference=None,
        domain='general',planning_category='SYNTHETIC',answer_is_correct=True,
        label_source='SYNTHETIC schema-only label; not a research correctness claim',
        label_method='independent_ground_truth',validation_id=restored.run_id,
        execution_configuration_id=request.execution_configuration_id,
        cache_contract='complete_team_independent_v1',attempts=(attempt,))
    assert Example.model_validate_json(exported.model_dump_json()).question==row['question']
    assert exported.content_identity==restored.content_identity
    with pytest.raises(ValueError):identifier(row['question'])  # identifier rules were not weakened


@pytest.mark.parametrize('value',['',' ','\n\t',42,None])
def test_invalid_question_is_still_rejected(value):
    with pytest.raises(ValidationError):TypeAdapter(QuestionText).validate_python(value)


def test_existing_question_identity_is_unchanged():
    text='A previously valid question?'
    assert TypeAdapter(QuestionText).validate_python(text)==identifier(text)
    assert content_id([text,'answer',None])==content_id([identifier(text),'answer',None])


def test_source_only_extractor_reproduces_raw_rosters_without_overwrite(tmp_path):
    require_private_source()
    import importlib.util
    import os
    path=ROOT/'docs/research_v1-recording-handoff/prepare_handoff.py'
    spec=importlib.util.spec_from_file_location('source_extractor',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    artifacts=Path(os.environ.get('RESEARCH_V1_ARTIFACT_DIR',Path.home()/'Downloads'))
    out=module.generate(artifacts,tmp_path/'new-source-only-output')
    expected=json.loads((ROOT/'docs/research_v1-recording-handoff/development-scope.json').read_text())
    actual=json.loads((out/'development-scope.json').read_text())
    assert actual['eligible_source_candidates_pending_approval']==expected['eligible_source_candidates_pending_approval']
    assert json.loads((out/'development-verifier-inputs.source.json').read_text())==ROWS
    assert json.loads((out/'history-source-roster.json').read_text())==json.loads((ROOT/'docs/research_v1-recording-handoff/history-source-roster.json').read_text())
    assert not json.loads((out/'source-derivation.json').read_text())['source_tuples_transformed']
    with pytest.raises(FileExistsError):module.generate(artifacts,out)
