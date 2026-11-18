"""Offline definition and no-reapplication tests; all catalog responses are fake."""
from copy import deepcopy
from unittest.mock import Mock, MagicMock
from types import SimpleNamespace
import pytest
from scripts import run_migrations as runner, reconcile_migration_history as reconciler
from scripts.migration_013_schema import MIGRATION_013, generated_answer_session_problems

GOOD = [
    ('uuid', 'YES', 'pg_catalog', 'uuid'),
    (['session_id'], 'public', 'sessions', ['session_id'], 'n', True),
    (True, True, 'btree', False, 3, 3, True, True, ['session_id', 'created_at', 'id']),
]


def cursor_for(rows=None):
    cursor = Mock()
    cursor.fetchone.side_effect = deepcopy(GOOD if rows is None else rows)
    return cursor


def verify(module, cursor, monkeypatch):
    if module is runner:
        for name in ('get_existing_columns', 'get_existing_column_types'):
            monkeypatch.setattr(runner, name, lambda c: {})
        for name in ('get_existing_constraints', 'get_existing_indexes'):
            monkeypatch.setattr(runner, name, lambda c: set())
        runner.verify_migration_schema(cursor, MIGRATION_013)
        return []
    return reconciler.verify_migration(MIGRATION_013, {}, set(), set(), {}, cursor=cursor)


@pytest.mark.parametrize('module', [runner, reconciler])
def test_013_recognized_in_order_and_not_applyable(module):
    names = runner.MIGRATIONS if module is runner else reconciler.MIGRATION_FILES
    assert names[-2:] == ['012_report_validation_id_text.sql', MIGRATION_013]
    assert len(names) == len(set(names)) == 13
    assert module.unknown_migration_records({MIGRATION_013}) == set()
    assert MIGRATION_013 not in runner.APPLYABLE_MIGRATIONS


@pytest.mark.parametrize('module', [runner, reconciler])
def test_valid_definition_accepted(module, monkeypatch):
    cursor = cursor_for()
    assert verify(module, cursor, monkeypatch) == []
    assert cursor.execute.call_count == 3
    assert all(call.args[0].strip().startswith('SELECT') for call in cursor.execute.call_args_list)


BAD = [
    (0, None), (0, ('text','YES','pg_catalog','text')),
    (0, ('uuid','NO','pg_catalog','uuid')),
    (0, ('uuid','YES','other','uuid')),
    (1, None),
    (1, (['other'],'public','sessions',['session_id'],'n',True)),
    (1, (['session_id'],'other','sessions',['session_id'],'n',True)),
    (1, (['session_id'],'public','other',['session_id'],'n',True)),
    (1, (['session_id'],'public','sessions',['other'],'n',True)),
    (1, (['session_id'],'public','sessions',['session_id'],'c',True)),
    (1, (['session_id'],'public','sessions',['session_id'],'n',False)),
    (2, None),
]
for field, value in [(0,False),(1,False),(2,'hash'),(3,True),(4,2),(5,4),(6,False),(7,False),
                     (8,['created_at','session_id','id']),(8,['session_id DESC','created_at','id'])]:
    row=list(GOOD[2]);row[field]=value;BAD.append((2,tuple(row)))


@pytest.mark.parametrize('module', [runner, reconciler])
@pytest.mark.parametrize('position,bad_row', BAD)
def test_missing_or_incorrect_definition_rejected(module, position, bad_row, monkeypatch):
    rows=deepcopy(GOOD);rows[position]=bad_row
    cursor=cursor_for(rows)
    if module is runner:
        with pytest.raises(RuntimeError, match='schema checks failed'):
            verify(module,cursor,monkeypatch)
    else:
        assert verify(module,cursor,monkeypatch)


def test_reconciler_without_definition_cursor_fails_closed():
    assert reconciler.verify_migration(MIGRATION_013,{},set(),set(),{})


@pytest.mark.parametrize('valid', [True,False])
def test_recorded_013_never_executes_migration_or_history_write(monkeypatch, valid):
    rows=deepcopy(GOOD)
    if not valid:rows[0]=None
    cursor=cursor_for(rows)
    for name in ('get_existing_columns','get_existing_column_types'):
        monkeypatch.setattr(runner,name,lambda c:{})
    for name in ('get_existing_constraints','get_existing_indexes'):
        monkeypatch.setattr(runner,name,lambda c:set())
    if valid:
        runner.process_migration(cursor,MIGRATION_013,{MIGRATION_013},allow_apply=True)
    else:
        with pytest.raises(RuntimeError):
            runner.process_migration(cursor,MIGRATION_013,{MIGRATION_013},allow_apply=True)
    assert all(call.args[0].strip().startswith('SELECT') for call in cursor.execute.call_args_list)


def test_missing_unrecorded_013_cannot_be_applied(monkeypatch):
    cursor=Mock()
    monkeypatch.setattr(runner,'verify_migration_schema',Mock(side_effect=RuntimeError('schema missing')))
    with pytest.raises(RuntimeError,match='Refusing to rerun'):
        runner.process_migration(cursor,MIGRATION_013,set(),allow_apply=MIGRATION_013 in runner.APPLYABLE_MIGRATIONS)
    cursor.execute.assert_not_called()


def test_reconciler_main_checks_recorded_013_without_writing(monkeypatch):
    cursor=MagicMock()
    cursor.fetchone.return_value=('questions_answers',)
    cursor.fetchall.return_value=[(name,) for name in reconciler.MIGRATION_FILES]
    connection=MagicMock()
    connection.__enter__.return_value=connection
    connection.cursor.return_value.__enter__.return_value=cursor
    monkeypatch.setattr(reconciler.psycopg2,'connect',lambda **kwargs:connection)
    monkeypatch.setattr(reconciler,'load_dotenv',lambda *args:None)
    monkeypatch.setattr(reconciler,'read_schema_inventory',lambda c:({}, {}, set(), set()))
    original=reconciler.verify_migration
    def checked(name,*args,**kwargs):
        return original(name,*args,**kwargs) if name == MIGRATION_013 else []
    monkeypatch.setattr(reconciler,'verify_migration',checked)
    definitions=Mock(return_value=[])
    monkeypatch.setattr(reconciler,'generated_answer_session_problems',definitions)
    # main checks credential presence only; avoid environment changes.
    monkeypatch.setattr(reconciler,'os',SimpleNamespace(getenv=lambda *args: 'offline-fixture'))
    reconciler.main()
    definitions.assert_called_once_with(cursor)
    assert not any('INSERT INTO schema_migrations' in call.args[0] for call in cursor.execute.call_args_list)
    assert not any('ALTER TABLE' in call.args[0] for call in cursor.execute.call_args_list)
