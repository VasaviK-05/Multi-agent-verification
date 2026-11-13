"""Extend the existing Phase C audit without replay, fitting, or reserved reads."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))


def git(*args, binary=False):
    return subprocess.check_output(['git', *args], cwd=ROOT, text=not binary)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def save(name, value):
    (OUT/name).write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False)+'\n')


def paths_at(revision):
    return {line.split('\t', 1)[1]: line.split()[2]
            for line in git('ls-tree', '-r', revision).splitlines()
            if '\t' in line and line.split('\t', 1)[1].endswith('.py')
            and (line.split('\t', 1)[1].startswith('app/') or
                 line.split('\t', 1)[1].startswith('scripts/') and line.split('\t', 1)[1].count('/') == 1)}


def fingerprint(items):
    encoded = json.dumps(sorted(items.items()), sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False)
    return sha(encoded.encode())


def main():
    previous = json.loads((OUT/'audit-results.json').read_text())
    targets = {row['path']: dict(row) for row in previous['missing_register']}
    custody = json.loads((ROOT/'artifacts/compound-study-36-v1/execution-source-custody.json').read_text())
    targets[previous['additional_missing_source_archive']] = dict(
        path=previous['additional_missing_source_archive'], expected_original_sha256=custody['archive_sha256'])
    basenames = {Path(p).name for p in targets}
    # Discovery opens directory entries only. No research/final payloads are read.
    roots = [ROOT, Path('/Users/vasavi/Documents'), Path('/Users/vasavi/Downloads'),
             Path('/Users/vasavi/Desktop'), Path('/Users/vasavi/.Trash'),
             Path('/Users/vasavi/.codex/attachments'), Path('/private/tmp')]
    skip = {'.git', 'node_modules', '__pycache__', '.venv', 'venv', 'site-packages',
            'plugins', '.cache', 'pip-cache'}
    candidates, archives, repositories, errors = set(), set(), set(), []
    for root in roots:
        if not root.exists(): continue
        for parent, dirs, files in os.walk(root, onerror=lambda error: errors.append(str(error))):
            if '.git' in dirs or '.git' in files: repositories.add(parent)
            dirs[:] = [d for d in dirs if d not in skip]
            for name in files:
                p = Path(parent)/name
                if name in basenames: candidates.add(p)
                if name.lower().endswith('.zip'): archives.add(p)
    object_names = git('rev-list', '--all', '--reflog', '--objects').splitlines()
    named_objects = []
    for row in object_names:
        oid, _, path = row.partition(' ')
        if Path(path).name in basenames: named_objects.append(dict(object_id=oid, path=path))
    fsck = subprocess.run(['git', 'fsck', '--full', '--no-reflogs', '--unreachable'], cwd=ROOT,
                          text=True, capture_output=True)
    tree_hits, tree_count = [], 0
    for line in fsck.stdout.splitlines():
        parts = line.split()
        if len(parts) != 3 or parts[1] != 'tree': continue
        tree_count += 1
        for entry in git('ls-tree', '-r', parts[2]).splitlines():
            if '\t' not in entry: continue
            path = entry.split('\t', 1)[1]
            if Path(path).name in basenames:
                tree_hits.append(dict(tree=parts[2], path=path, object_id=entry.split()[2]))
    archive_records = []
    for path in sorted(archives):
        record = dict(path=str(path))
        try:
            h = hashlib.sha256()
            with path.open('rb') as stream:
                for chunk in iter(lambda: stream.read(1024*1024), b''): h.update(chunk)
            record['archive_sha256'] = h.hexdigest()  # Raw container only, no decompression.
            with zipfile.ZipFile(path) as archive:
                record['candidate_member_names'] = [i.filename.replace('\\', '/') for i in archive.infolist()
                    if Path(i.filename.replace('\\', '/')).name in basenames]
            record['exact_execution_custody_container_hash_match'] = h.hexdigest() == custody['archive_sha256']
            record['member_payloads_opened'] = False
        except (OSError, zipfile.BadZipFile) as error: record['error'] = str(error)
        archive_records.append(record)
    for relative, row in targets.items():
        row['authentic_original_found'] = False
        row['source_location_commit_or_archive'] = None
        row['found_sha256'] = None
        row['provenance_authenticated'] = False
        row['current_canonical_path_exists'] = (ROOT/relative).is_file()
        row['exact_path_commits_including_reflogs'] = git('log', '--all', '--reflog', '--format=%H', '--', relative).splitlines()
        row['named_git_candidates'] = [r for r in named_objects if r['path'] == relative or r['path'].endswith('/'+relative)]
        row['unreachable_tree_candidates'] = [r for r in tree_hits if r['path'] == relative or r['path'].endswith('/'+relative)]
        row['disk_name_candidates'] = [str(p) for p in sorted(candidates) if p.name == Path(relative).name]
        row['archive_name_candidates'] = [dict(archive=a['path'], member=n)
             for a in archive_records for n in a.get('candidate_member_names', []) if Path(n).name == Path(relative).name]
        row['producer_custodian'] = 'Original training producer / research lead custodian' if relative.startswith('build/') else 'Original study/publication custodian; Tanmayee coordinates execution-source custody' if relative.endswith('.zip') else 'Original study/publication custodian / research lead'
    # Authenticate precise historical training/Development objects, not lookalike files.
    from app.game.offline.records import TrainingManifest
    from app.game.offline.evaluation import Evaluation, bind_evaluation
    from app.game.models import PlanningContext, content_id
    from app.game.execution_contract import ExecutionContract
    from app.game.offline.attacks import AttackSpecification
    recovery_revision = '1277e9d3ce91f1395e3deed7e7202748a5a04672'
    for cohort in ('arithmetic', 'factual'):
        recorded = previous['cohorts'][cohort]
        training_path = f'build/multitask-policy42/{cohort}/training-manifest.json'
        development_path = f'build/multitask-policy42/{cohort}/development-evaluation.json'
        train_bytes = git('show', recovery_revision+':'+training_path, binary=True)
        dev_bytes = git('show', recovery_revision+':'+development_path, binary=True)
        training = TrainingManifest.model_validate_json(train_bytes)
        development = Evaluation.model_validate_json(dev_bytes)
        context = PlanningContext.model_validate_json((ROOT/recorded['paths']['context']).read_bytes())
        contract = ExecutionContract.model_validate_json((ROOT/recorded['paths']['contract']).read_bytes())
        attack = AttackSpecification.model_validate_json((ROOT/recorded['paths']['attacks']).read_bytes())
        policy = json.loads((ROOT/recorded['paths']['policy']).read_bytes())
        assert sha(train_bytes) == recorded['locator_only_training_sha256']
        assert training.manifest_id == recorded['locator_only_training_manifest_id'] == development.manifest_id
        assert {p.role for p in training.partitions} == {'history', 'development'}
        assert training.final_test_reservation.reservation_id == recorded['reservation_id']
        assert bind_evaluation(context, training, contract, attack) == context
        assert development.role == 'development' and development.attacks == attack
        source_evaluation_id = content_id(development.model_dump(mode='json'))
        expected_development_id = policy['matrix']['clean_coverage']['source_evaluation_id']
        development_matches = development.contract == contract and source_evaluation_id == expected_development_id
        for path, payload in ((training_path, train_bytes), (development_path, dev_bytes)):
            exact = path == training_path or development_matches
            targets[path].update(authentic_original_found=exact,
                source_location_commit_or_archive=recovery_revision+':'+path,
                found_git_blob=git('rev-parse', recovery_revision+':'+path).strip(),
                found_sha256=sha(payload), provenance_authenticated=exact,
                candidate_is_authentic_historical_record=True, required_current_policy_equivalent=exact,
                expected_policy_development_content_id=expected_development_id,
                candidate_development_contract_matches=(development.contract == contract),
                non_equivalence_reason=None if exact else 'Older Development contract lacks minimum-one team_requirements; content ID differs from current policy clean_coverage.source_evaluation_id',
                authentication_scope='Git publication object; training matches exact locator hash and typed training/reservation/history-resource binding. Older Development must independently match current policy; whole-freeze custody remains unauthenticated.',
                producer_custodian='Commit author Vasavi Gayathri Kasina is identifiable as publisher; original producer/custodian assignment still requires research-lead confirmation',
                training_manifest_id=training.manifest_id, development_content_id=source_evaluation_id,
                history_development_counts={p.role:len(p.examples) for p in training.partitions},
                copied_to_canonical_working_path=False)
    save('recovery-investigation.json', dict(targets=list(targets.values()), search_roots=list(map(str,roots)),
         excluded_directory_names=sorted(skip), inaccessible_paths=errors, discovered_repositories=sorted(repositories),
         git_named_object_count=len(object_names), named_objects_with_required_basenames=named_objects,
         unreachable_trees_checked=tree_count, unreachable_tree_basename_hits=tree_hits,
         fsck_exit_code=fsck.returncode, fsck_stderr=fsck.stderr, archives=archive_records,
         notes=['Candidates are discovery hits, not recovered originals. Public-audit views and research_v1 remain non-equivalent.',
                'Anonymous unreachable blobs were not opened: they lack path/role identity and could contain restricted data.',
                'ZIP files were hashed as raw containers and only directory names inspected; no member payloads opened in this extension.',
                'No external network search, fetch or teammate contact performed.']))

    manifest = json.loads((ROOT/'docs/experiment1/phase-b/experiment1-candidate.json').read_text())
    expected_rev = manifest['source_commit']; actual_rev = git('rev-parse', 'HEAD').strip()
    # Fingerprints bind checkout bytes, including the reviewed CRLF attributes.
    # Raw Git blobs alone would falsely label clean CRLF files as edits.
    all_paths = sorted(set(paths_at(expected_rev)) | set(paths_at(actual_rev)))
    attrs = git('check-attr', 'eol', 'filter', '--', *all_paths).splitlines()
    crlf_paths = {line.rsplit(': ',2)[0] for line in attrs if line.endswith(': eol: crlf')}
    filters = [line for line in attrs if ': filter: ' in line and not line.endswith(': unspecified')]
    assert not filters, 'Custom checkout filters require separate inspection'
    raw_committed = {}
    committed = {}
    for rev in (expected_rev, actual_rev):
        mapping = paths_at(rev)
        raw = {p:git('cat-file','blob',oid,binary=True) for p,oid in mapping.items()}
        raw_committed[rev] = {p:sha(value) for p,value in raw.items()}
        committed[rev] = {p:sha(value.replace(b'\r\n', b'\n').replace(b'\n', b'\r\n') if p in crlf_paths else value) for p,value in raw.items()}
    current = {p.relative_to(ROOT).as_posix():sha(p.read_bytes())
               for p in sorted([*(ROOT/'app').rglob('*.py'), *(ROOT/'scripts').glob('*.py')])}
    expected_files = committed[expected_rev]
    changes=[]
    for path in sorted(set(expected_files)|set(current)):
        if expected_files.get(path) != current.get(path):
            changes.append(dict(path=path, expected_sha256=expected_files.get(path),
                 head_sha256=committed[actual_rev].get(path), observed_sha256=current.get(path),
                 status='added_untracked' if path not in committed[actual_rev] else 'modified_working_tree' if committed[actual_rev].get(path)!=current.get(path) else 'committed_revision_change'))
    from app.game.research.experiment1.manifest import reporting_environment
    save('mismatch-investigation.json', dict(expected_commit=expected_rev, observed_commit=actual_rev,
         expected_fingerprint=manifest['source_fingerprint'], observed_fingerprint=fingerprint(current),
         expected_revision_fingerprint=fingerprint(expected_files), head_revision_fingerprint=fingerprint(committed[actual_rev]),
         raw_git_blob_fingerprint=fingerprint(raw_committed[expected_rev]), crlf_checkout_paths=sorted(crlf_paths),
         changed_source_files=changes, expected_reporting_environment=manifest['reporting_environment'],
         observed_reporting_environment=reporting_environment(),
         committed_diff=git('diff','--stat',expected_rev,actual_rev),
         original_collection_source_revision=custody['source_revision'],
         original_execution_source_digest=custody['application_source_digest'],
         original_execution_custody_archive_sha256=custody['archive_sha256'],
         resource_status='Recorded fingerprints validate; actual models/services not inspected or attested. Unknown current compatibility, not a measured resource failure.'))

    spec=importlib.util.spec_from_file_location('phase_b_existing',ROOT/'docs/experiment1/phase-b/assemble_inputs.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    data=module.assemble()
    fresh=[]
    plan=json.loads((ROOT/'docs/experiment1/phase-b/readiness-inputs.json').read_text())
    for name in plan['candidates']:
        command=[sys.executable,'-B','-m','app.game.research.experiment1','readiness','docs/experiment1/phase-b/'+name]
        run=subprocess.run(command,cwd=ROOT,text=True,capture_output=True)
        if run.returncode not in (0,2): raise RuntimeError(run.stderr)
        report=json.loads(run.stdout);assert report['final_payloads_read'] is False
        fresh.append(dict(candidate=name,exit_code=run.returncode,report=report,command=command))
    save('readiness-current.json',dict(results=fresh,allowed_inputs=data['input_files'],
        changes_since_phase_b=[p for p,r in data['input_files'].items() if r['sha256']!=previous['metadata_training_revalidation']['input_files'][p]['sha256']],
        source_commit=data['assembly_source_commit'],source_fingerprint=data['source_fingerprint'],
        final_payloads_read=False,inference_calls=0,optimization_calls=0))
    # Numeric contracts from genuine policy metadata, never final outcomes.
    summary={}
    for c in ('arithmetic','factual','reference'):
        e=data['cohorts'][c]
        policy=json.loads((ROOT/e['paths']['policy']).read_text())
        if 'policy' in policy: policy=policy['policy']
        defs={s['strategy_id']:s for s in e['feasible_strategies']}
        positive=[dict(strategy_id=s,probability=p,definition=defs[s]) for s,p in e['probabilities'] if p>0]
        matrix=policy['matrix']
        summary[c]=dict(policy_id=e['policy_id'],positive_probabilities=positive,coverage_floor=e['coverage_floor'],
            threshold=e['threshold'],team_requirements=e['team_requirements'],budget=e['budget'],loss=e['loss'],
            feasible_strategy_count=len(defs),feasible_strategies=e['feasible_strategies'],
            clean_coverage=matrix.get('clean_coverage'),reliability_first=matrix.get('reliability_first'),
            historical_comparison=e['historical_comparison'],retrospective_comparison=e['retrospective_comparison'])
    e=data['cohorts']['compound']; policy=json.loads((ROOT/e['paths']['policy']).read_text())
    from app.game.component_execution import ComponentStrategy
    defs={ComponentStrategy.model_validate(s).strategy_id:s for s in e['strategies']}
    summary['compound']=dict(policy_id=e['policy_id'],positive_probabilities=[dict(strategy_id=s,probability=p,definition=defs[s]) for s,p in e['probabilities'] if p>0],
         coverage_floor=e['coverage_floor'],component_contracts=e['obligations'],
         feasible_strategies=e['strategies'],clean_coverage=policy['matrix']['clean_coverage'],
         historical_comparison=e['historical_comparison'],retrospective_comparison=e['retrospective_comparison'])
    save('comparison-contract-audit.json',dict(cohorts=summary,
         classification='Existing contracts only, not a newly authored scientific comparison specification',
         historical_chronology_limit='Protocol/amendment metadata names pre-final freezes; missing canonical seals prevent complete independent chronology authentication.',
         no_fitting=True,no_final_payload_reads=True))
    print(json.dumps(dict(targets=len(targets),archives=len(archive_records),unreachable_trees=tree_count,
        changed_sources=changes,expected_fingerprint=manifest['source_fingerprint'],actual_fingerprint=fingerprint(current),
        readiness_exits=[r['exit_code'] for r in fresh]),indent=2))

if __name__=='__main__': main()
