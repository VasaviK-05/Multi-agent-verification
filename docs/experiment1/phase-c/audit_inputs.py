"""Resume Phase B in memory; inventory ZIPs without opening reserved payloads."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT, text=True).strip()

def main():
    old = json.loads((ROOT/'docs/experiment1/phase-b/input-inventory.json').read_text())
    missing = {r['path']: dict(r) for c in old['cohorts'].values() for r in c.get('missing', [])}
    for path, record in missing.items():
        record['exists_now'] = (ROOT/path).is_file()
        record['local_git_commits_now'] = git('log', '--all', '--format=%H', '--', path).splitlines()
        record['responsible_owner_role'] = ('Original multitask-policy42 training producer/custodian' if path.startswith('build/') else 'Original publication custodian / study producer')
        record['named_individual_assignment'] = 'Not established by available custody records; research lead must confirm'
    requested = ['artifacts(1).zip', 'person3-prerequisite-artifacts(1).zip',
        'research_v1_development_rehearsal_662bd5c(1).zip',
        'research_v1_exploratory_v1_source_package(1).zip',
        'research-v1-development-cost-calibration-v1(1).zip']
    search_roots = [Path('/Users/vasavi/Downloads'), Path('/Users/vasavi/Documents'), Path('/private/tmp')]
    exact = {name: [] for name in requested}
    # Filename discovery only: no files are opened by this traversal.
    import os
    for root in search_roots:
        for parent, dirs, files in os.walk(root):
            dirs[:] = [d for d in dirs if d not in {'.git', 'node_modules', '__pycache__', '.venv'}]
            for name in set(files).intersection(requested):
                exact[name].append(str(Path(parent)/name))
    archives = []
    names = [n.replace('(1)', '') for n in requested] + ['compound-study-36-v1.zip']
    for name in names:
        path = Path('/Users/vasavi/Downloads')/name
        if not path.is_file():
            archives.append(dict(path=str(path), accessible=False)); continue
        with zipfile.ZipFile(path) as archive:
            members = [dict(path=i.filename.replace('\\', '/'), bytes=i.file_size, crc=i.CRC) for i in archive.infolist() if not i.is_dir()]
        matches = {p:[m['path'] for m in members if m['path'] == p or m['path'].endswith('/'+p) or m['path'] == p.removeprefix('artifacts/')] for p in missing}
        archives.append(dict(path=str(path), accessible=True, bytes=path.stat().st_size,
            members=members, exact_canonical_path_matches={p:v for p,v in matches.items() if v},
            payload_members_opened=False, archive_identity_equivalence_to_requested_suffix_variant='not established'))
    spec = importlib.util.spec_from_file_location('existing_phase_b', ROOT/'docs/experiment1/phase-b/assemble_inputs.py')
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    current = module.assemble()  # Existing typed checks, no write_outputs / fitting / replay.
    reads = current['input_files']
    changed_inputs = [p for p,r in reads.items() if p not in old['input_files'] or r['sha256'] != old['input_files'][p]['sha256']]
    # Compare only the existing Phase B allowlist. Never inspect sealed members.
    for archive_record in archives:
        if not archive_record['accessible']: continue
        checked = []
        with zipfile.ZipFile(archive_record['path']) as archive:
            for member in archive.infolist():
                normalized = member.filename.replace('\\', '/')
                for relative, record in reads.items():
                    canonical = relative.removeprefix('artifacts/')
                    reference_prefix = 'remaining-category-studies-v1/reference-50-v1/'
                    reference_short = canonical.removeprefix(reference_prefix) if canonical.startswith(reference_prefix) else None
                    match = normalized == canonical or normalized.endswith('/'+canonical)
                    if Path(archive_record['path']).name == 'person3-prerequisite-artifacts.zip' and reference_short:
                        match = match or normalized == reference_short
                    if match:
                        payload = archive.read(member)
                        checked.append(dict(member=normalized, canonical_path=relative,
                            sha256=hashlib.sha256(payload).hexdigest(),
                            matches_phase_b=hashlib.sha256(payload).hexdigest()==record['sha256']))
        archive_record['allowed_metadata_training_comparisons'] = checked
        archive_record['payload_members_opened'] = bool(checked)
        archive_record['reserved_payload_members_opened'] = False
    results = []
    plan = json.loads((ROOT/'docs/experiment1/phase-b/readiness-inputs.json').read_text())
    for name in plan['candidates']:
        command = [sys.executable, '-B', '-m', 'app.game.research.experiment1', 'readiness', 'docs/experiment1/phase-b/'+name]
        run = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
        if run.returncode not in (0,2): raise RuntimeError(run.stderr)
        report = json.loads(run.stdout)
        assert report['final_payloads_read'] is False
        results.append(dict(candidate=name, command=command, exit_code=run.returncode, report=report))
    output = dict(version='experiment1_phase_c_resumption_audit_v1', audit_date_local='2026-11-13',
        repository=dict(root=str(ROOT), branch=git('branch','--show-current'), head=git('rev-parse','HEAD'),
            status_before_audit_output=git('status','--short','--branch'), worktrees=git('worktree','list','--porcelain'),
            refs=git('show-ref'), remotes=git('remote','-v')),
        archive_search_roots=list(map(str,search_roots)), requested_exact_filenames=exact, accessible_variants=archives,
        missing_register=list(missing.values()), additional_missing_source_archive='artifacts/compound-study-36-v1/local-custody/original-execution-source.zip',
        metadata_training_revalidation=dict(input_files=reads, changed_since_phase_b=changed_inputs,
            current_source_commit=current['assembly_source_commit'], current_source_fingerprint=current['source_fingerprint'],
            historical_source_commit=old['assembly_source_commit'], historical_source_fingerprint=old['source_fingerprint'],
            publication_content_commit_available=current['publication_content_commit_available']),
        cohorts=current['cohorts'], readiness_results=results, final_payloads_opened=[], scoring=False, optimization=False,
        limitations=['ZIP directories inspected; only explicitly allowlisted Phase B metadata/History/Development members opened for byte comparison; no extraction or reserved payload access.',
            'No equality of differently named ZIP archive bytes is asserted.',
            'Existing candidates preserved; current source mismatches are reported, not repaired by rewriting history.',
            'No network fetch, verifier collection or database modification.'])
    (OUT/'audit-results.json').write_text(json.dumps(output, indent=2, sort_keys=True, allow_nan=False)+'\n')
    print(json.dumps(dict(missing=sum(not r['exists_now'] for r in missing.values()),
        archives=len(archives), allowed_inputs=len(reads), changed_inputs=changed_inputs,
        readiness=[dict(candidate=r['candidate'],exit_code=r['exit_code'],blockers=r['report']['blockers']) for r in results]),indent=2))

if __name__ == '__main__': main()
