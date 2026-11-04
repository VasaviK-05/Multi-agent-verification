"""Seal a new prepared evaluation, or verify an existing seal. No inference."""
import argparse
import hashlib
import json
from pathlib import Path


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def write_new(p,d):
    with Path(p).open('x',encoding='utf-8') as stream:json.dump(d,stream,indent=2,sort_keys=True);stream.write('\n')


def main():
    p=argparse.ArgumentParser();p.add_argument('--frozen',type=Path,required=True);p.add_argument('--verify',action='store_true');a=p.parse_args()
    root=Path(__file__).resolve().parents[1];out=a.frozen.resolve();freeze=read(out/'freeze-manifest.json')
    for name,digest in freeze['frozen_file_hashes'].items():
        if sha(out/name)!=digest:raise ValueError('candidate files differ from freeze')
    if a.verify:
        for name,digest in read(out/'precollection-seal.json')['files'].items():
            if sha(name)!=digest:raise ValueError('precollection seal differs: '+name)
        original=read(out/'evaluation-code-seal.json')['evaluator_sha256']
        actual=sha(root/'scripts/evaluate_flexible_heldout.py')
        if actual!=original:
            correction=read(out/'evaluation-code-correction-v2.json')
            parent=read(out/'evaluation-code-correction.json')
            if (correction['original_evaluator_sha256']!=original or correction['corrected_evaluator_sha256']!=actual or correction['parent_corrected_sha256']!=parent['corrected_evaluator_sha256']):raise ValueError('evaluation correction chain changed')
        print('Existing candidate/specification/collector/evaluation seals verified');return
    if any((out/c/'collection').exists() for c in ('arithmetic','factual')):
        raise ValueError('cannot create a precollection seal after collection has started')
    paths=[out/'freeze-manifest.json',out/'evaluation-specification.json',root/'app/game/offline/collection.py',root/'scripts/collect_flexible_heldout.py',root/'scripts/flexible_heldout.py']
    write_new(out/'precollection-seal.json',dict(version='heldout_precollection_seal_v1',files={str(p):sha(p) for p in paths},note='Sealed before test payload/outcome access. Verifiers load from the explicitly resource-compatible checkout; collector is an owned opt-in extension.'))
    write_new(out/'evaluation-code-seal.json',dict(version='heldout_analysis_code_seal_v1',evaluator_sha256=sha(root/'scripts/evaluate_flexible_heldout.py'),note='Sealed implementation of the predeclared evaluation specification; no fitting.'))
    print('New precollection and evaluation-code seals created:',freeze['freeze_id'])

if __name__=='__main__':main()
