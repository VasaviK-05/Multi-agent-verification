"""Offline published-byte and typed-policy checks; no model/service requests."""
import hashlib,json
from pathlib import Path
from scripts.policy_package import load
def main():
    folder=Path('artifacts/publication-v1')
    manifest=folder/'file-hashes-v2.json'
    if not manifest.exists():manifest=folder/'file-hashes.json'
    rows=json.loads(manifest.read_text(encoding='utf-8'));bad=[]
    for name,expected in rows.items():
        path=Path(name)
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=expected['sha256']:bad.append(name)
    if bad:raise ValueError('published byte verification failed: '+repr(bad))
    config,provider,compound=load('artifacts/remaining-category-studies-v1/prototype-policy-package-v1/policies.json')
    assert config.router().resolve('Explain quantum gravity.')[0]=='unsupported_category'
    print('VERIFIED_PUBLICATION',len(rows),'files;',len(provider.snapshot()),'atomic artifacts; compound',compound.policy_id,flush=True)
if __name__=='__main__':main()
