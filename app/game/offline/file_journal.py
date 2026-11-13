"""Durable file primitives for the existing offline recording contract.

No verifiers, models, datasets, database or scientific settings are loaded here.
An acknowledgement follows file and directory synchronization. Unsupported sync
operations fail closed; physical media/controller guarantees remain external.
"""
from contextlib import ExitStack
import json
import os
from pathlib import Path
import sys
import tempfile


class RecoveryBlocked(ValueError):
    """Preserve ambiguous or damaged input for review; never infer a retry."""


def sync_directory(path):
    descriptor = os.open(path, os.O_RDONLY | getattr(os, 'O_DIRECTORY', 0))
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def sync_file(handle):
    handle.flush()
    os.fsync(handle.fileno())
    if sys.platform == 'darwin':
        import fcntl
        # macOS fsync alone need not flush drive caches. No silent fallback.
        fcntl.fcntl(handle.fileno(), fcntl.F_FULLFSYNC)


def create_run_directory(path):
    path = Path(path)
    if path.exists():
        raise FileExistsError(path)
    missing = []
    cursor = path
    while not cursor.exists():
        missing.append(cursor)
        cursor = cursor.parent
    for directory in reversed(missing):
        directory.mkdir(exist_ok=False)
        sync_directory(directory.parent)
        sync_directory(directory)


def atomic_write_text(path, text, *, replace=True):
    """Write UTF-8 completely before publishing; do not acknowledge failed sync."""
    path = Path(path)
    descriptor, temporary = tempfile.mkstemp(prefix='.' + path.name + '-', dir=path.parent)
    temporary = Path(temporary)
    try:
        with os.fdopen(descriptor, 'w', encoding='utf-8', newline='\n') as handle:
            handle.write(text)
            sync_file(handle)
        if replace:
            os.replace(temporary, path)
        else:
            # Atomic create-if-absent; an existing destination is never replaced.
            os.link(temporary, path)
            temporary.unlink()
        sync_directory(path.parent)
    finally:
        if temporary.exists():
            temporary.unlink()


def read_jsonl(path):
    """Strict recovery: a torn final line is not silently discarded or repaired."""
    path = Path(path)
    if not path.exists():
        return []
    raw = path.read_bytes()
    if raw and not raw.endswith(b'\n'):
        raise RecoveryBlocked('unterminated journal tail: ' + str(path))
    try:
        return [json.loads(line) for line in raw.decode('utf-8').splitlines() if line.strip()]
    except (UnicodeError, ValueError) as exc:
        raise RecoveryBlocked('invalid journal: ' + str(path)) from exc


def recovery_state(path):
    """Check lifecycle links before any factory import or resource construction."""
    path = Path(path)
    if not (path / 'started.jsonl').is_file():
        raise RecoveryBlocked('no start ledger: cannot safely infer unattempted work')
    starts = read_jsonl(path / 'started.jsonl')
    rows = read_jsonl(path / 'attempts.jsonl')
    try:
        start_ids = [row['attempt_id'] for row in starts]
        terminal_ids = [row['attempt_id'] for row in rows]
        executed = {row['attempt_id'] for row in rows if row['executed'] is True}
        if any(type(row['executed']) is not bool for row in rows):
            raise RecoveryBlocked('invalid executed flag')
        if any(not isinstance(i, str) or not i.strip() for i in start_ids + terminal_ids):
            raise RecoveryBlocked('invalid attempt identity')
        if len(start_ids) != len(set(start_ids)) or len(terminal_ids) != len(set(terminal_ids)):
            raise RecoveryBlocked('duplicate journal attempt identity')
        if executed - set(start_ids):
            raise RecoveryBlocked('executed completion has no durable start intent')
        if set(start_ids) & (set(terminal_ids) - executed):
            raise RecoveryBlocked('start intent contradicts unexecuted completion')
        inflight = set(start_ids) - executed
        if inflight:
            raise RecoveryBlocked('in-flight attempt lacks completion; do not retry: ' + str(sorted(inflight)))
    except (KeyError, TypeError) as exc:
        raise RecoveryBlocked('invalid lifecycle record') from exc
    return rows


class AttemptJournal:
    """Exclusive journals; stable attempt IDs and bodies are supplied unchanged."""
    def __init__(self, path):
        self.path = Path(path)
        self._stack = ExitStack()
        self.started, self.completed = set(), set()
        self._poisoned = False

    def __enter__(self):
        try:
            self._starts = self._stack.enter_context((self.path / 'started.jsonl').open('x', encoding='utf-8', newline='\n'))
            self._rows = self._stack.enter_context((self.path / 'attempts.jsonl').open('x', encoding='utf-8', newline='\n'))
            sync_file(self._starts)
            sync_file(self._rows)
            sync_directory(self.path)
        except BaseException:
            self._stack.close()
            raise
        return self

    def __exit__(self, *args):
        return self._stack.__exit__(*args)

    def _append(self, handle, text):
        if self._poisoned:
            raise RecoveryBlocked('journal write previously failed; do not continue')
        try:
            handle.write(text + '\n')
            sync_file(handle)
        except BaseException:
            self._poisoned = True
            raise

    def start(self, attempt_id):
        if not isinstance(attempt_id, str) or not attempt_id.strip():
            raise ValueError('nonblank attempt identity required')
        if attempt_id in self.started or attempt_id in self.completed:
            raise RecoveryBlocked('duplicate start; do not retry: ' + attempt_id)
        self._append(self._starts, json.dumps(dict(attempt_id=attempt_id)))
        self.started.add(attempt_id)

    def terminal(self, text):
        # One existing CollectedAttempt JSON object, including original payload,
        # timing status, report provenance and explicit executed flag.
        if '\n' in text or '\r' in text:
            raise ValueError('terminal record must be one JSON line')
        row = json.loads(text)
        attempt_id, executed = row['attempt_id'], row['executed']
        if not isinstance(attempt_id, str) or not attempt_id.strip() or type(executed) is not bool:
            raise ValueError('valid identity and explicit executed flag required')
        if attempt_id in self.completed:
            raise RecoveryBlocked('duplicate completion: ' + attempt_id)
        if executed != (attempt_id in self.started):
            raise RecoveryBlocked('completion/start lifecycle mismatch: ' + attempt_id)
        self._append(self._rows, text)
        self.completed.add(attempt_id)  # Only after durable acknowledgement.
