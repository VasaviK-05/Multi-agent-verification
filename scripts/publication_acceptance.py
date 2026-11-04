"""Native-report router replay; seeded selection audit is not new inference."""
import json,random,hashlib,argparse
from collections import Counter
from pathlib import Path
from types import SimpleNamespace
from scripts.replay_remaining_policies import load_registry
from scripts.replay_compound_study_36 import RecordedVerifier
from app.game.resource_provenance import ResourceManifest
from app.selection.verifier_selector import VerifierSelector
from app.selection.capabilities import BUILTIN_CAPABILITIES
def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    repo=Path(__file__).resolve().parents[1];folder=repo/'artifacts/remaining-category-studies-v1/reference-50-v1'
    spec=json.loads((folder/'selection-audit-spec.json').read_text(encoding='utf-8'))
    if hashlib.sha256(Path(__file__).read_bytes()).hexdigest()!=spec['driver_sha256']:raise ValueError('pre-outcome selection audit code differs')
    config,provider,compound,artifacts=load_registry(repo);router=config.router()
    bundle=json.loads((folder/'test/reference/bundle.json').read_text(encoding='utf-8'));resources=ResourceManifest.model_validate(bundle['observed_setup']['resources'])
    rng=random.Random(spec['seed']);rows=[]
    for example in bundle['request']['examples']:
        expected={r['candidate']:dict(question=example['question'],answer=example['answer'],reference=example['reference'],report_json=r['attempt']['report_json'],execution_state=r['attempt']['state']) for r in bundle['attempts'] if r['run_id']==example['run_id']}
        calls=[];selector=VerifierSelector(verifiers=[RecordedVerifier(n,calls,expected) for n in BUILTIN_CAPABILITIES],capabilities=BUILTIN_CAPABILITIES)
        result=router.run(selector,SimpleNamespace(question=example['question'],answer=example['answer'],context=example['reference']),example['run_id'],provider=provider,rng=rng,resource_observer=SimpleNamespace(snapshot=lambda:resources))
        if result.summary.get('selection_status')!='selected':raise ValueError('reference policy replay did not select')
        rows.append(dict(example_id=example['example_id'],public_status=result.public_status,summary=result.summary,replayed_calls=calls,new_native_calls=0))
    counts=Counter(','.join(sorted(row['summary']['team'])) for row in rows)
    a.output.mkdir(parents=True,exist_ok=False)
    (a.output/'reference-routing.json').write_text(json.dumps(dict(seed=spec['seed'],team_counts=dict(counts),rows=rows,mode='retained reserved report replay; not native collection or API activation',new_verifier_calls=0,real_triple=any(len(row['summary']['team'])==3 for row in rows)),indent=2),encoding='utf-8')
    print('ACTUAL_REPLAY_TEAM_COUNTS',dict(counts),flush=True)
if __name__=='__main__':main()
