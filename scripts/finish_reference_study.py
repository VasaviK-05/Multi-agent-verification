"""Wait for completed training; fit once; conditionally release reserved partition."""
import json,subprocess,sys,time
from pathlib import Path
def wait(path):
    deadline=time.monotonic()+7200
    while not path.exists():
        if time.monotonic()>deadline:raise TimeoutError('collection incomplete; inspect retained journals, no automatic retry')
        time.sleep(2)
    if not json.loads(path.read_text(encoding='utf-8'))['complete']:raise ValueError('incomplete collection; retain journals')
def main():
    root=Path(__file__).resolve().parents[1];base=root/'artifacts/remaining-category-studies-v1'
    wait(base/'reference/training/collection-integrity.json')
    subprocess.run([sys.executable,'-m','scripts.fit_reference_study'],cwd=root,check=True)
    summary=json.loads((base/'reference/fit/summary.json').read_text(encoding='utf-8'))
    if not summary['deployable_policy']:
        print('REFERENCE_INFEASIBLE_RESERVED_CORRECTLY_SKIPPED',flush=True);return
    wait(base/'compound-85/test/collection-integrity.json')
    subprocess.run([sys.executable,'-m','scripts.reference_reserved','collect','--source',str(root.parent/'multitask-policy42')],cwd=root,check=True)
    subprocess.run([sys.executable,'-m','scripts.reference_reserved','evaluate'],cwd=root,check=True)
if __name__=='__main__':main()
