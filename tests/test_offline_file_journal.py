"""Filesystem-only fault tests. No verifier construction, dispatch, data or models."""
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from app.game.offline import file_journal as io


def terminal(identity='stable-id', *, executed=True, state='directional', timing='returned'):
    report = '{"verifier_name":"fixture","reasoning":"original body"}' if state in {'directional','abstention'} else None
    return json.dumps(dict(attempt_id=identity, executed=executed, timing_status=timing if executed else None,
        attempt=dict(state=state, report_json=report), returned_payload_json=report))


def test_atomic_snapshot_and_exclusive_creation(tmp_path):
    path=tmp_path/'request.json'
    io.atomic_write_text(path,'original',replace=False)
    with pytest.raises(FileExistsError):
        io.atomic_write_text(path,'overwrite',replace=False)
    assert path.read_text()=='original'
    io.atomic_write_text(path,'replacement')
    assert path.read_text()=='replacement'
    assert sorted(p.name for p in tmp_path.iterdir())==['request.json']


def test_publish_failure_preserves_old_snapshot(tmp_path,monkeypatch):
    path=tmp_path/'recordings.json';path.write_text('old')
    def fail(*args):raise OSError('replace failed')
    monkeypatch.setattr(io.os,'replace',fail)
    with pytest.raises(OSError):io.atomic_write_text(path,'new')
    assert path.read_text()=='old'
    assert sorted(p.name for p in tmp_path.iterdir())==['recordings.json']


def test_file_sync_failure_does_not_publish(tmp_path,monkeypatch):
    def fail(handle):raise OSError('fsync failed')
    monkeypatch.setattr(io,'sync_file',fail)
    with pytest.raises(OSError):io.atomic_write_text(tmp_path/'request.json','new')
    assert list(tmp_path.iterdir())==[]


def test_directory_sync_failure_is_not_acknowledged(tmp_path,monkeypatch):
    def fail(path):raise OSError('unsupported directory sync')
    monkeypatch.setattr(io,'sync_directory',fail)
    with pytest.raises(OSError,match='directory sync'):io.atomic_write_text(tmp_path/'request.json','new')
    # Publication may already be visible, but the caller receives no success.
    assert (tmp_path/'request.json').read_text()=='new'


def test_nested_run_directory_is_synced_and_exclusive(tmp_path,monkeypatch):
    seen=[];monkeypatch.setattr(io,'sync_directory',lambda p:seen.append(Path(p)))
    path=tmp_path/'parent'/'run';io.create_run_directory(path)
    assert path.is_dir() and path in seen and path.parent in seen and tmp_path in seen
    with pytest.raises(FileExistsError):io.create_run_directory(path)


@pytest.mark.parametrize('state,timing', [('directional','returned'),('abstention','returned'),
    ('failed','failure'),('failed','timeout'),('unavailable','failure'),('missing','interrupted')])
def test_terminal_roundtrip_preserves_state_timing_and_original_body(tmp_path,state,timing):
    body=terminal(state=state,timing=timing)
    with io.AttemptJournal(tmp_path) as journal:
        journal.start('stable-id');journal.terminal(body)
        assert journal.completed=={'stable-id'}
    rows=io.recovery_state(tmp_path)
    assert rows==[json.loads(body)]
    assert (tmp_path/'attempts.jsonl').read_text()==body+'\n'


def test_no_dispatch_exclusion_needs_no_start(tmp_path):
    body=terminal(executed=False,state='unavailable')
    with io.AttemptJournal(tmp_path) as journal:journal.terminal(body)
    assert io.recovery_state(tmp_path)==[json.loads(body)]


def test_no_completion_or_duplicate_start_can_bypass_lifecycle(tmp_path):
    with io.AttemptJournal(tmp_path) as journal:
        with pytest.raises(io.RecoveryBlocked):journal.terminal(terminal())
        journal.start('stable-id')
        with pytest.raises(io.RecoveryBlocked):journal.start('stable-id')
        with pytest.raises(io.RecoveryBlocked):journal.terminal(terminal(executed=False))
        journal.terminal(terminal())
        with pytest.raises(io.RecoveryBlocked):journal.terminal(terminal())
        with pytest.raises(io.RecoveryBlocked):journal.start('stable-id')
    assert len(io.recovery_state(tmp_path))==1


def test_terminal_sync_precedes_ack_and_failure_poisons_writer(tmp_path,monkeypatch):
    with io.AttemptJournal(tmp_path) as journal:
        journal.start('stable-id');original=io.sync_file
        def fail(handle):
            assert journal.completed==set()
            original(handle)
            raise OSError('uncertain completion acknowledgement')
        monkeypatch.setattr(io,'sync_file',fail)
        with pytest.raises(OSError):journal.terminal(terminal())
        assert journal.completed==set()
        with pytest.raises(io.RecoveryBlocked,match='previously failed'):journal.terminal(terminal())
    # If bytes survived, recovery retains them; absence of ack never triggers retry.
    assert len(io.recovery_state(tmp_path))==1


@pytest.mark.parametrize('cut', ['before_start','after_start','after_terminal'])
def test_process_exit_cutpoints_without_verifier_execution(tmp_path,cut):
    script='''import os,sys
from pathlib import Path
from app.game.offline.file_journal import AttemptJournal
with AttemptJournal(Path(sys.argv[1])) as j:
 if sys.argv[2]=='before_start': os._exit(0)
 j.start('stable-id')
 if sys.argv[2]=='after_start': os._exit(0)
 j.terminal(sys.argv[3])
 os._exit(0)
'''
    subprocess.run([sys.executable,'-c',script,str(tmp_path),cut,terminal()],check=True)
    if cut=='after_start':
        with pytest.raises(io.RecoveryBlocked,match='do not retry'):io.recovery_state(tmp_path)
    else:
        assert len(io.recovery_state(tmp_path))==(1 if cut=='after_terminal' else 0)


@pytest.mark.parametrize('tail',[b'{"attempt_id":"partial"}', b'{bad}\n', b'\xff\n'])
def test_torn_or_invalid_tail_is_blocked_unchanged(tmp_path,tail):
    path=tmp_path/'attempts.jsonl';path.write_bytes(tail)
    with pytest.raises(io.RecoveryBlocked):io.read_jsonl(path)
    assert path.read_bytes()==tail


@pytest.mark.parametrize('kind',['duplicate_start','duplicate_terminal','no_start','contradictory'])
def test_recovery_rejects_corrupt_lifecycle(tmp_path,kind):
    start='{"attempt_id":"stable-id"}\n'
    (tmp_path/'started.jsonl').write_text(start*2 if kind=='duplicate_start' else '' if kind=='no_start' else start)
    body=terminal(executed=kind!='contradictory')+'\n'
    (tmp_path/'attempts.jsonl').write_text(body*2 if kind=='duplicate_terminal' else body)
    with pytest.raises(io.RecoveryBlocked):io.recovery_state(tmp_path)


def test_existing_journal_is_never_overwritten(tmp_path):
    (tmp_path/'started.jsonl').write_text('preserved')
    with pytest.raises(FileExistsError):
        with io.AttemptJournal(tmp_path):pass
    assert (tmp_path/'started.jsonl').read_text()=='preserved'


def test_multiline_terminal_cannot_corrupt_jsonl(tmp_path):
    with io.AttemptJournal(tmp_path) as journal:
        journal.start('stable-id')
        with pytest.raises(ValueError,match='one JSON line'):
            journal.terminal(json.dumps(json.loads(terminal()),indent=2))
        assert (tmp_path/'attempts.jsonl').read_text()==''
        journal.terminal(terminal())
    assert len(io.recovery_state(tmp_path))==1


def test_start_sync_failure_never_acknowledges_dispatch_intent(tmp_path,monkeypatch):
    with io.AttemptJournal(tmp_path) as journal:
        def fail(handle):raise OSError('start synchronization failed')
        monkeypatch.setattr(io,'sync_file',fail)
        with pytest.raises(OSError,match='start synchronization'):journal.start('stable-id')
        assert journal.started==set()
        assert journal.completed==set()
        with pytest.raises(io.RecoveryBlocked,match='previously failed'):journal.start('another-id')
    with pytest.raises(io.RecoveryBlocked,match='do not retry'):io.recovery_state(tmp_path)
