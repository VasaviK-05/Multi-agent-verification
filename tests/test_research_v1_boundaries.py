"""Actual collector/CLI boundaries with deterministic test adapters, never services."""
import json
from types import SimpleNamespace
import sys

import pytest

from app.game.offline.collection import collect, RecordingBundle, completeness, attempt_identity
from app.game.offline.collect import main, load_bundle
from app.game.offline import file_journal as journal_io
from app.game.offline.file_journal import AttemptJournal, recovery_state, RecoveryBlocked
from tests.test_game_collection import fixture


def test_durable_start_before_simulated_execution_and_terminal_before_progress(tmp_path):
    request,pool,setup,observer,*_=fixture(names=('a',))
    events=[];original=pool[0].verify
    with AttemptJournal(tmp_path) as journal:
        def begin(identity):
            journal.start(identity);events.append(('start_ack',identity))
        def simulated(question,answer,context=None):
            assert events[-1][0]=='start_ack'
            assert journal_io.read_jsonl(tmp_path/'started.jsonl')[-1]['attempt_id']==events[-1][1]
            events.append(('execute',events[-1][1]))
            return original(question,answer,context)
        pool[0].verify=simulated
        def terminal(row):
            assert events[-1]==('execute',row.attempt_id)
            journal.terminal(row.model_dump_json())
            assert row.attempt_id in journal.completed
            events.append(('terminal_ack',row.attempt_id))
        bundle=collect(request,pool,setup,observer,sink=terminal,on_start=begin)
    assert [e[0] for e in events]==['start_ack','execute','terminal_ack']*2
    assert completeness(bundle)['complete']
    assert len(recovery_state(tmp_path))==2
    assert RecordingBundle.model_validate_json(bundle.model_dump_json())==bundle


def test_start_failure_prevents_every_simulated_call():
    request,pool,setup,observer,*_=fixture()
    def fail(identity):raise OSError('no durable start acknowledgement')
    with pytest.raises(OSError,match='durable start'):
        collect(request,pool,setup,observer,on_start=fail)
    assert all(not p.calls for p in pool)


def test_completion_failure_stops_progress_and_blocks_ambiguous_resume(tmp_path):
    request,pool,setup,observer,*_=fixture()
    with AttemptJournal(tmp_path) as journal:
        def fail(row):raise OSError('completion persistence failed')
        with pytest.raises(OSError,match='completion persistence'):
            collect(request,pool,setup,observer,sink=fail,on_start=journal.start)
    assert len(pool[0].calls)==1 and not pool[1].calls
    with pytest.raises(RecoveryBlocked,match='do not retry'):recovery_state(tmp_path)


def test_duplicate_attempts_rejected_by_real_bundle():
    request,pool,setup,observer,*_=fixture()
    bundle=collect(request,pool,setup,observer)
    with pytest.raises(ValueError,match='duplicate recorded attempt'):
        RecordingBundle(request=request,observed_setup=setup,attempts=(*bundle.attempts,bundle.attempts[0]))


def test_whitespace_dispatch_is_verbatim_with_stable_provenance():
    request,pool,setup,observer,*_=fixture(names=('a',))
    data=request.model_dump(mode='json');data['examples'][1]['question']='  permitted content\t'
    request=type(request).model_validate(data)
    bundle=collect(request,pool,setup,observer)
    assert pool[0].calls[-1][0]=='  permitted content\t'
    row=bundle.attempts[-1]
    assert row.attempt_id==attempt_identity(request,request.examples[1],request.candidates[0])
    assert row.measurement.content_identity==request.examples[1].content_identity
    assert json.loads(row.attempt.report_provenance)['request_id']==request.request_id
    assert row.attempt.configuration_id==setup.resources.manifest_id


def test_cli_resume_retains_completed_calls_without_repeating(tmp_path,monkeypatch):
    request,pool,setup,observer,*_=fixture()
    monkeypatch.setitem(sys.modules,'synthetic_recording_factory',SimpleNamespace(create=lambda:(pool,setup,observer)))
    path=tmp_path/'request.json';path.write_text(request.model_dump_json())
    first=tmp_path/'first';second=tmp_path/'second'
    assert main(['collect',str(path),'--output-dir',str(first)])==0
    before=[len(p.calls) for p in pool]
    assert main(['collect',str(path),'--output-dir',str(second),'--resume-from',str(first)])==0
    assert [len(p.calls) for p in pool]==before
    assert [a.attempt_id for a in load_bundle(first).attempts]==[a.attempt_id for a in load_bundle(second).attempts]
    assert (second/'resume-provenance.json').is_file()
    assert len(recovery_state(second))==4


def test_missing_never_started_resumes_but_executed_missing_never_retries(tmp_path):
    request,pool,setup,observer,*_=fixture(names=('a',))
    pool[0].action=KeyboardInterrupt()
    bundle=collect(request,pool,setup,observer)
    assert [r.executed for r in bundle.attempts]==[True,False]
    assert all(r.attempt.state=='missing' for r in bundle.attempts)
    with AttemptJournal(tmp_path) as j:
        for row in bundle.attempts:
            if row.executed:j.start(row.attempt_id)
            j.terminal(row.model_dump_json())
    # Executed missing has a terminal row, but is retained as incomplete, not retried.
    assert len(recovery_state(tmp_path))==2
    pool[0].action=None;calls=len(pool[0].calls)
    resumed=collect(request,pool,setup,observer,completed=bundle.attempts)
    assert len(pool[0].calls)==calls+1
    assert resumed.attempts[0]==bundle.attempts[0]
    assert not completeness(resumed)['complete']


def test_cli_torn_resume_is_rejected_before_factory(tmp_path,monkeypatch):
    request,pool,setup,observer,*_=fixture()
    path=tmp_path/'request.json';path.write_text(request.model_dump_json())
    monkeypatch.setitem(sys.modules,'synthetic_recording_factory',SimpleNamespace(create=lambda:(pool,setup,observer)))
    first=tmp_path/'first'
    assert main(['collect',str(path),'--output-dir',str(first)])==0
    with (first/'attempts.jsonl').open('ab') as out:out.write(b'{partial')
    monkeypatch.setattr('app.game.offline.collect.importlib.import_module',lambda *a:pytest.fail('factory initialized during corrupt recovery'))
    assert main(['collect',str(path),'--output-dir',str(tmp_path/'second'),'--resume-from',str(first)])==2
    assert not (tmp_path/'second').exists()


def test_cli_snapshot_failure_resumes_acknowledged_rows(tmp_path,monkeypatch):
    import app.game.offline.collect as cli
    request,pool,setup,observer,*_=fixture()
    monkeypatch.setitem(sys.modules,'synthetic_recording_factory',SimpleNamespace(create=lambda:(pool,setup,observer)))
    path=tmp_path/'request.json';path.write_text(request.model_dump_json())
    original=cli.atomic_write_text
    def fail_snapshot(path,text,**kwargs):
        if path.name=='recordings.json':raise OSError('injected snapshot publication failure')
        return original(path,text,**kwargs)
    monkeypatch.setattr(cli,'atomic_write_text',fail_snapshot)
    first=tmp_path/'interrupted';second=tmp_path/'recovered'
    assert cli.main(['collect',str(path),'--output-dir',str(first)])==2
    assert not (first/'recordings.json').exists()
    assert len(recovery_state(first))==4
    before=[len(p.calls) for p in pool]
    monkeypatch.setattr(cli,'atomic_write_text',original)
    assert cli.main(['collect',str(path),'--output-dir',str(second),'--resume-from',str(first)])==0
    assert [len(p.calls) for p in pool]==before
    assert completeness(load_bundle(second))['complete']
