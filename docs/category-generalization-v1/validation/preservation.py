"""Stdlib-only frozen registration/source preservation; no verifier imports.

This byte/metadata audit does not substitute for executable routing regressions.
"""
import hashlib
import gzip
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
BASE = Path(__file__).with_name('preservation-before.json')
NEW = {'app/game/category_applicability.py', 'app/game/category_runtime.py'}


def snapshot():
    files = set()
    for folder in ('artifacts', 'reconciliation'):
        files.update(p for p in (ROOT/folder).rglob('*') if p.is_file())
    for folder in ('app', 'scripts'):
        files.update(p for p in (ROOT/folder).rglob('*.py') if p.relative_to(ROOT).as_posix() not in NEW)
    hashes = {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in sorted(files)}
    registrations = []
    for p in sorted(files):
        if p.suffix != '.json':
            continue
        try:
            value = json.loads(p.read_bytes())
        except (ValueError, UnicodeError):
            continue
        if not isinstance(value, dict):
            continue
        if 'allowed_questions' in value:
            registrations.append(dict(path=p.relative_to(ROOT).as_posix(),
                questions=sorted(value['allowed_questions']),
                # Full embedded artifacts include matrices/probabilities/resources/contracts.
                atomic_artifacts=value.get('atomic_artifacts'),
                compound_policy=value.get('compound_policy'), bundle_id=value.get('bundle_id')))
        if value.get('version') == 'prototype_manifest_v1' or ('entries' in value and 'files' in value):
            registrations.append(dict(path=p.relative_to(ROOT).as_posix(), manifest=value))
    return dict(version='category_preservation_v1', files=hashes, registrations=registrations,
        runtime_behavior_capture='BLOCKED: missing functional test dependencies; static bytes/metadata only')


def preservation_changes(before, current):
    # Keep the original 661-file inventory intact. Record upstream main source
    # transitions and exact additive code overlays separately, never reset pins.
    expected = dict(before['files'])
    transition = BASE.with_name('main-base-transition-v3.json')
    if transition.exists():
        for name, row in json.loads(transition.read_text())['files'].items():
            if name.startswith(('artifacts/', 'reconciliation/')) or expected.get(name) != row['original_sha256']:
                raise ValueError('invalid main-base transition')
            expected[name] = row['main_base_sha256']
    overlay = BASE.with_name('owned-source-overlay-v3.json')
    if overlay.exists():
        for name, row in json.loads(overlay.read_text())['files'].items():
            if name.startswith(('artifacts/', 'reconciliation/')) or expected.get(name) != row['base_sha256']:
                raise ValueError('invalid owned source overlay')
            expected[name] = row['category_sha256']
    return sorted(name for name, digest in expected.items() if current['files'].get(name) != digest)


def routing_status():
    first=BASE.with_name('exact-routing-before-v3.json')
    last=BASE.with_name('exact-routing-after-v3.json')
    def read(path):
        return path.read_bytes() if path.exists() else gzip.decompress(path.with_name(path.name+'.gz').read_bytes())
    if (first.exists() or first.with_name(first.name+'.gz').exists()) and (last.exists() or last.with_name(last.name+'.gz').exists()):
        before=json.loads(read(first));after=json.loads(read(last))
        if before==after and after.get('checks')==207 and after.get('questions')==69:
            return 'PASS: 69 questions / 207 identical route projections'
        return 'FAIL: route comparison differs'
    return 'BLOCKED: dynamic comparison unavailable'


if __name__ == '__main__':
    current = snapshot()
    if sys.argv[1:] == ['capture']:
        with BASE.open('x') as stream:
            json.dump(current, stream, sort_keys=True, indent=2)
        print('Captured', len(current['files']), 'files and', len(current['registrations']), 'registration inventories')
    else:
        before = json.loads(BASE.read_text())
        changes = preservation_changes(before, current)
        result = dict(preserved=not changes and current['registrations'] == before['registrations'],
            changed_existing_files=changes, registration_inventories=len(current['registrations']),
            dynamic_routing_regression_status=routing_status())
        print(json.dumps(result, indent=2))
        sys.exit(0 if result['preserved'] else 1)
