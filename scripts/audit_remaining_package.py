"""Read-only byte preservation and publication inventory; no original paths changed."""
import hashlib,json,re,subprocess
from pathlib import Path
ROOT=Path('artifacts/remaining-category-studies-v1')
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,v):
    with Path(p).open('x',encoding='utf-8') as f:json.dump(v,f,indent=2,sort_keys=True)
def main():
    before=read(ROOT/'preservation-before.json')
    changed=[name for name,digest in before.items() if not Path(name).is_file() or sha(name)!=digest]
    paths={Path(row['path']) for row in read('artifacts/compound-study-36-v1/publication-inventory.json')['files']}
    paths.update(Path(p) for p in subprocess.check_output(['git','diff','--name-only','HEAD'],text=True).splitlines())
    paths.update(ROOT.rglob('*'))
    paths.update(Path(p) for p in ('scripts/transition_reference_current.py','scripts/fit_reference_current.py',
        'scripts/reference_current_reserved.py','scripts/collect_reference_current_reserved.py','scripts/finish_reference_current.py',
        'scripts/policy_package.py','scripts/finalize_reference_handoff.py','tests/test_reference_transition.py','tests/test_policy_package.py'))
    paths.update(Path(p) for p in ('scripts/scoped_er_adapter.py','scripts/scoped_compound_bridge.py',
        'scripts/evaluate_scoped_compound.py','scripts/prepare_scoped_compound.py','scripts/finish_scoped_compound.py','tests/test_scoped_er_adapter.py'))
    paths.update(Path(p) for p in ('app/analysis/reference_study_analyzer.py','docs/supported_category_policy_integration.md',
        'scripts/fit_compound_85.py','scripts/reference_study.py','scripts/collect_reference_study.py','scripts/fit_reference_study.py',
        'scripts/reference_reserved.py','scripts/collect_reference_reserved.py','scripts/collect_remaining_compound.py',
        'scripts/replay_remaining_policies.py','scripts/audit_remaining_package.py','scripts/summarize_remaining_studies.py','scripts/finish_reference_study.py','tests/test_reference_study.py'))
    excluded=[str(p) for p in paths if 'local-custody' in p.parts]
    paths={p for p in paths if 'local-custody' not in p.parts and p.is_file() and '__pycache__' not in p.parts}
    files=[];identity_paths=[];suspects=[]
    secret=re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|\bghp_[A-Za-z0-9]{30,}|\bgithub_pat_[A-Za-z0-9_]{30,}|\bsk-[A-Za-z0-9]{32,}')
    for path in sorted(paths):
        files.append(dict(path=path.as_posix(),sha256=sha(path),bytes=path.stat().st_size))
        if path.suffix.lower() in {'.json','.jsonl','.py','.md','.txt','.yaml','.yml'}:
            text=path.read_text(encoding='utf-8')
            if secret.search(text):suspects.append(path.as_posix())
            if re.search(r'[A-Za-z]:[/\\]+Users[/\\]+[^/\\\s"<>]+',text,re.I):identity_paths.append(path.as_posix())
    missing=[]
    for doc in [Path('docs/supported_category_policy_integration.md'),*ROOT.rglob('*.md')]:
        for target in re.findall(r'\]\(([^)]+)\)',doc.read_text(encoding='utf-8')):
            if '://' in target or target.startswith('#'):continue
            relative=target.split('#')[0]
            if not (doc.parent/relative).exists() and not relative.endswith(('publication-inventory-final-reference.json','publication-inventory-final-reference-v2.json','publication-inventory-final-reference-v3.json')):
                missing.append(dict(document=doc.as_posix(),target=target))
    result=dict(version='remaining_categories_publication_v1',branch=subprocess.check_output(['git','branch','--show-current'],text=True).strip(),
        base=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),files=files,required_baseline_checkout=True,
        historical_files_checked=len(before),historical_artifacts_changed=changed,primary_handoff_missing_references=missing,
        likely_secret_matches=suspects,intentional_original_identity_path_files=identity_paths,
        identity_disclosure_review_required=bool(identity_paths),
        excluded=dict(local_custody=excluded,external='Model weights/cache, index, Ollama, venv, DB/user data, credentials; exact external resource inventory retained.',
            original_checkout='All unrelated original-checkout dirty owner files and local-custody source archive excluded.'),
        publication_scope='Reviewable owned package on recorded baseline; no commit or activation. Historical source/manifest bytes kept even when original local paths require disclosure review.',
        portable_loading_replay='scripts.replay_remaining_policies uses repository-relative files; original audit paths remain unchanged.',
        ready_for_review=not(changed or missing or suspects))
    import sys
    destination=ROOT/('publication-inventory-final-reference-v3.json' if '--final-reference-v3' in sys.argv else 'publication-inventory-final-reference-v2.json' if '--final-reference-v2' in sys.argv else 'publication-inventory-final-reference.json' if '--final-reference' in sys.argv else 'publication-inventory-owned.json' if '--owned' in sys.argv else 'publication-inventory-recovery.json' if '--recovery' in sys.argv else 'publication-inventory.json')
    if any(flag in sys.argv for flag in ('--final-reference','--final-reference-v2','--final-reference-v3')):
        completed=[row for row in read(ROOT/'publication-inventory-owned.json')['files'] if row['path'].startswith('artifacts/')]
        completed_changed=[row['path'] for row in completed if not Path(row['path']).is_file() or sha(row['path'])!=row['sha256']]
        result.update(completed_artifact_files_checked=len(completed),completed_artifacts_changed=completed_changed)
        if completed_changed:raise ValueError('completed artifact bytes changed')
    save(destination,result)
    print(json.dumps({k:v for k,v in result.items() if k in ('historical_files_checked','historical_artifacts_changed','primary_handoff_missing_references','likely_secret_matches','ready_for_review')}),flush=True)
    if changed or missing or suspects:raise ValueError('preserve findings; resolve package issue without rewriting history')
if __name__=='__main__':main()
