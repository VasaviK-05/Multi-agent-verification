"""Wait for the single reserved pass, validate ceilings, then evaluate once."""
import time,json,subprocess,sys
from pathlib import Path
def main():
    root=Path(__file__).resolve().parents[1];folder=root/'artifacts/remaining-category-studies-v1/reference-50-v1'
    deadline=time.monotonic()+3600
    while not (folder/'test/collection-integrity.json').exists():
        if time.monotonic()>deadline:raise TimeoutError('inspect retained journals; no retry')
        time.sleep(2)
    integrity=json.loads((folder/'test/collection-integrity.json').read_text())
    if not integrity['complete'] or not integrity['resources_unchanged'] or integrity['executed_calls']>80 or integrity['network']['generation']>100:raise ValueError('reserved integrity/caps failed')
    subprocess.run([sys.executable,'-m','scripts.reference_50_reserved','evaluate'],cwd=root,check=True)
if __name__=='__main__':main()
