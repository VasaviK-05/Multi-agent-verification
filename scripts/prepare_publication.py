"""Explicit owned-file publication plan; preserve canonical local audit originals."""
import json,hashlib,re,os,argparse
from pathlib import Path
ROOT=Path('artifacts/remaining-category-studies-v1')
PUBLIC=Path('artifacts/publication-v1')
PRIVATE=re.compile(r'[A-Za-z]:[/\\]+Users[/\\]+[^/\\\s"<>]+')
SECRET=re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|\bghp_[A-Za-z0-9]{30,}|\bgithub_pat_[A-Za-z0-9_]{30,}|\bsk-[A-Za-z0-9]{32,}')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    PUBLIC.mkdir(parents=True,exist_ok=False)
    old=json.loads((ROOT/'publication-inventory-final-reference-v3.json').read_text(encoding='utf-8'))
    paths={Path(row['path']) for row in old['files']}
    paths.update(p for p in (ROOT/'reference-50-v1').rglob('*') if p.is_file())
    paths.update(p for p in (ROOT/'prototype-policy-package-v1').rglob('*') if p.is_file())
    paths.update(Path(p) for p in ['scripts/fit_reference_50.py','scripts/reference_50_reserved.py','scripts/collect_reference_50_reserved.py','scripts/publication_acceptance.py','scripts/prepare_publication.py','scripts/publication_report.py','scripts/direct_router_example.py','scripts/finish_reference_50.py','scripts/verify_publication.py','tests/test_reference_50.py','docs/THIRD_PARTY_NOTICES.md'])
    paths.update([ROOT/'atomic-public-identities.json'])
    paths={p for p in paths if p.is_file() and '__pycache__' not in p.parts and 'local-custody' not in p.parts}
    mappings={};records=[];texts={}
    for p in sorted(paths):
        if p.suffix.lower() not in {'.json','.jsonl','.txt','.md','.py','.yaml','.yml'}:continue
        text=p.read_text(encoding='utf-8')
        if SECRET.search(text):raise ValueError('potential credential in publication input: '+str(p))
        texts[p]=text
        historical_doc=p.parent==Path('docs') and p.name not in {'supported_category_policy_integration.md','THIRD_PARTY_NOTICES.md'}
        if PRIVATE.search(text) or historical_doc:
            if p.name in {'policy.json','context.json','contract.json','matrix.json','policies.json'}:
                raise ValueError('identity-bearing deployment artifact has personal paths; do not redact silently: '+str(p))
            mappings[p]=PUBLIC/('historical-documents' if historical_doc else 'public-audit')/p
    def rewrite_links(text,source,destination):
        def replace(match):
            value=match.group(1)
            if '<LOCAL_USER_HOME>' in value:return '] (external canonical audit input; acquire from the experiment custodian)'
            if '://' in value or value.startswith('#'):return match.group(0)
            path=value.split('#')[0];anchor=('#'+value.split('#',1)[1]) if '#' in value else ''
            absolute=(source.parent/path).resolve()
            try:relative=absolute.relative_to(Path.cwd()).as_posix()
            except ValueError:return match.group(0)
            mapped=mappings.get(Path(relative),Path(relative))
            return ']('+Path(os.path.relpath(mapped,destination.parent)).as_posix()+anchor+')'
        return re.sub(r'\]\(([^)]+)\)',replace,text)
    for source,destination in mappings.items():
        destination.parent.mkdir(parents=True,exist_ok=True)
        text=PRIVATE.sub('<LOCAL_USER_HOME>',texts[source])
        if source.suffix=='.md':text=rewrite_links(text,source,destination)
        destination.write_text(text,encoding='utf-8')
        records.append(dict(original_path=source.as_posix(),original_sha256=sha(source),public_path=destination.as_posix(),public_sha256=sha(destination),
            effects='Derived audit/document view only; whole-file/content identities change. Original canonical bytes preserved locally and not staged. Policy/matrix/report payload identities are not substituted by this view. Full canonical freeze verification requires the custodian original.'))
    primary=Path('docs/supported_category_policy_integration.md')
    primary.write_text(rewrite_links(primary.read_text(encoding='utf-8'),primary,primary),encoding='utf-8')
    publication=(paths-set(mappings))|set(mappings.values())
    attributes=Path('.gitattributes')
    if attributes.exists():raise ValueError('review existing attributes before changing byte preservation')
    attribute_paths=publication|{attributes,PUBLIC/'owned-files.json',PUBLIC/'file-hashes.json',PUBLIC/'stage-paths.txt'}
    attributes.write_text('# Exact bytes for explicitly owned policy/audit publication files.\nartifacts/publication-v1/** -text\ndocs/PUBLICATION.md -text\n'+'\n'.join(p.as_posix()+' -text' for p in sorted(attribute_paths))+'\n',encoding='utf-8')
    publication.add(attributes)
    plan=dict(version='owned_publication_plan_v1',remote_visibility='public',branch='codex/flexible-verifier-teams',
        distributable_files=sorted(p.as_posix() for p in publication),derived_public_views=records,
        excluded=['local-custody original-execution archive','model caches/weights','index directories','Ollama installation','environments','DB/user data','unrelated original-checkout changes'],
        canonical_audit_acquisition='Request exact canonical originals from the experiment custodian using original relative path and SHA256 in this manifest; resolve original source/resource locations through reviewed mappings. Redacted views cannot reproduce original whole-freeze IDs. Portable policy/certificate loading and retained-report replay do not require these canonical private-path files.')
    (PUBLIC/'owned-files.json').write_text(json.dumps(plan,indent=2),encoding='utf-8')
    publication.add(PUBLIC/'owned-files.json')
    manifest={p.as_posix():dict(sha256=sha(p),bytes=p.stat().st_size) for p in sorted(publication)}
    (PUBLIC/'file-hashes.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    publication.add(PUBLIC/'file-hashes.json')
    (PUBLIC/'stage-paths.txt').write_text('\n'.join(p.as_posix() for p in sorted(publication))+'\n',encoding='utf-8')
    print('EXPLICIT_PUBLICATION_FILES',len(publication),'DERIVED_VIEWS',len(records),flush=True)
if __name__=='__main__':main()
