"""Serialize authorized collections to avoid overlapping verifier timing samples."""
import json,subprocess,sys,time
from pathlib import Path
def main():
    root=Path(__file__).resolve().parents[1]
    reference=root/'artifacts/remaining-category-studies-v1/reference/training/collection-integrity.json'
    # This wait reads no outcomes; only completed collection status. No retries.
    deadline=time.monotonic()+7200
    while not reference.exists():
        if time.monotonic()>deadline:raise TimeoutError('reference collection incomplete; run compound independently after inspecting journals')
        time.sleep(2)
    if not json.loads(reference.read_text(encoding='utf-8'))['complete']:raise ValueError('reference collection incomplete; no automatic retry')
    command=[sys.executable,'-m','scripts.compound_study','collect','--source',str(root.parent/'multitask-policy42'),
        '--study','artifacts/compound-study-36-v1/preparation','--frozen','artifacts/remaining-category-studies-v1/compound-85/candidate',
        '--role','final_test','--output','artifacts/remaining-category-studies-v1/compound-85/test']
    subprocess.run(command,cwd=root,check=True)
    subprocess.run([sys.executable,'-m','scripts.compound_study','evaluate','--frozen','artifacts/remaining-category-studies-v1/compound-85/candidate',
        '--test','artifacts/remaining-category-studies-v1/compound-85/test','--output','artifacts/remaining-category-studies-v1/compound-85/evaluation'],cwd=root,check=True)
if __name__=='__main__':main()
