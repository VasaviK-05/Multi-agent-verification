"""Plan preparation and execution interlock only; no native execution."""
import json
from pathlib import Path
import pytest
from scripts.reusable_native_smoke import prepare,execute


def test_prepare_seals_independent_references_and_native_caps(tmp_path,monkeypatch):
    import app.game.offline.singleton_compatibility as singleton
    import app.game.offline.reference_compatibility as reference
    def forbidden(*args,**kwargs):raise AssertionError('preparation constructed a native pool')
    monkeypatch.setattr(singleton,'create_singleton',forbidden)
    monkeypatch.setattr(reference,'create_reference',forbidden)
    output=tmp_path/'plans';rows=prepare(output)
    plans={row['kind']:json.loads(Path(row['path']).read_text()) for row in rows}
    arithmetic=plans['arithmetic']
    assert arithmetic['reference_receipt']['candidate_independent']
    assert [r['context'] for r in arithmetic['requests']]==['8','8']
    assert [r['answer'] for r in arithmetic['requests']]==['8','9']
    assert arithmetic['maximum_native_attempts']==2 and arithmetic['maximum_generations']==0
    assert arithmetic['execution_authorized'] is False and arithmetic['blockers']==[]
    assert plans['evidence']['blockers'] and plans['reference']['blockers']
    assert plans['reference']['maximum_generations']==5
    assert len([p for p in plans['reference']['probabilities'] if p[1]>0])==2


def test_execute_requires_explicit_separate_approval_before_reading_plan(tmp_path):
    with pytest.raises(ValueError,match='separate explicit owner approval'):
        execute(tmp_path/'does-not-exist.json','not-approved',tmp_path/'no-output')
    assert not (tmp_path/'no-output').exists()


def test_native_journal_rejects_zero_probability_and_duplicate_attempts(tmp_path):
    from scripts.reusable_native_smoke import NativeJournal
    plan=dict(artifact_id='artifact',policy_id='policy',strategies=[
        dict(strategy_id='allowed',verifiers=['rule'],aggregation='reputation_weighted'),
        dict(strategy_id='zero',verifiers=['rule'],aggregation='dependency_group')],
        probabilities=[['allowed',1.],['zero',0.]],maximum_native_attempts=2,
        allowed_native_names=['rule'],requests=[dict(question='Q',answer='A',context='R')])
    journal=NativeJournal(tmp_path,plan);journal.current=0
    with pytest.raises(ValueError,match='unchanged fitted distribution'):
        journal.set_plan(dict(strategy_id='zero',artifact_id='artifact',policy_id='policy',team=['rule'],aggregation='dependency_group'))
    journal.set_plan(dict(strategy_id='allowed',artifact_id='artifact',policy_id='policy',team=['rule'],aggregation='reputation_weighted'))
    journal.start_attempt(verifier_name='rule')
    with pytest.raises(ValueError,match='retry blocked'):journal.start_attempt(verifier_name='rule')
    assert len(journal.starts)==1
