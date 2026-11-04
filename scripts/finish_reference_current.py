"""Continue only completed transition data; conditionally collect untouched test."""
import json,subprocess,sys,time
from pathlib import Path
def main():
    root=Path(__file__).resolve().parents[1];folder=root/'artifacts/remaining-category-studies-v1/reference-current-v1'
    deadline=time.monotonic()+7200
    while not (folder/'training/collection-integrity.json').exists():
        if time.monotonic()>deadline:raise TimeoutError('preserve incomplete transition; no retry')
        time.sleep(2)
    integrity=json.loads((folder/'training/collection-integrity.json').read_text(encoding='utf-8'))
    if not integrity['complete'] or not integrity['resources_unchanged']:raise ValueError('transition integrity blocked')
    subprocess.run([sys.executable,'-m','scripts.fit_reference_current'],cwd=root,check=True)
    summary=json.loads((folder/'fit/summary.json').read_text(encoding='utf-8'))
    if not summary['deployable_policy']:
        print('REFERENCE_CURRENT_INFEASIBLE_RESERVED_SKIPPED',flush=True);return
    subprocess.run([sys.executable,'-m','scripts.reference_current_reserved','collect','--source',str(root.parent/'multitask-policy42')],cwd=root,check=True)
    subprocess.run([sys.executable,'-m','scripts.reference_current_reserved','evaluate'],cwd=root,check=True)
if __name__=='__main__':main()
