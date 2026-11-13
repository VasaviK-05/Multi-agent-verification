"""Ownership remains enforced for committed and dirty feature branches."""
import importlib.util
from pathlib import Path

import pytest

path = Path(__file__).resolve().parents[1]/'docs/research_v1-recording-handoff/ownership.py'
spec = importlib.util.spec_from_file_location('research_ownership', path)
own = importlib.util.module_from_spec(spec)
spec.loader.exec_module(own)


@pytest.mark.parametrize('tracked,untracked,expected', [
    (b'',b'',[]),
    (b'app/game/offline/collect.py\0',b'', ['app/game/offline/collect.py']),
    (b'app/game/offline/collect.py\0',b'docs/research_v1-recording-handoff/README.md\0',
     ['app/game/offline/collect.py','docs/research_v1-recording-handoff/README.md']),
])
def test_clean_committed_and_untracked_diff(monkeypatch, tracked, untracked, expected):
    responses=iter([b'merge-base-fixture\n',tracked,untracked])
    monkeypatch.setattr(own.subprocess,'check_output',lambda *a,**kw:next(responses))
    assert own.changed_paths(Path('unused-fixture'), 'pinned-base') == expected


@pytest.mark.parametrize('path', ['app/verifiers/evidence_verifier.py','app/models/schemas.py',
                                 'database.py','tests/preparation_fixtures.py','research/experiment1.json'])
def test_teammate_and_unrelated_changes_fail(path):
    manifest={'allowed_files':['app/game/offline/collect.py'],
              'allowed_prefixes':['docs/research_v1-recording-handoff/']}
    assert own.unexpected_changes([path],manifest)==[path]


def test_current_checkout_scope():
    assert isinstance(own.check(),list)
