"""Runnable direct-router example on retained component reports; zero inference."""
import json,random
from pathlib import Path
from types import SimpleNamespace
from app.models.schemas import ValidationRequest
from app.game.resource_provenance import ResourceManifest
from app.selection.verifier_selector import VerifierSelector
from app.selection.capabilities import BUILTIN_CAPABILITIES
from scripts.replay_remaining_policies import load_registry
from scripts.replay_compound_study_36 import RecordedVerifier
def main():
    repo=Path(__file__).resolve().parents[1];read=lambda p:json.loads(p.read_text(encoding='utf-8'))
    config,provider,_,_=load_registry(repo)
    source=repo/'artifacts/compound-study-36-v1';example=read(source/'examples.json')['development'][0]
    # answer is serialized JSON TEXT supplied by the caller/generation owner.
    request=ValidationRequest(question=example['question'],answer=example['answer'],context=None)
    bundles=dict(read(source/'development/joint.json')['bundles']);expected={}
    for component,name in (('base_fact','evidence'),('derived_sum','rule')):
        row=next(r for r in bundles[component]['attempts'] if r['example_id']==example['example_id']+'-'+component and r['candidate']==name)
        bound=next(e for e in bundles[component]['request']['examples'] if e['run_id']==row['run_id'])
        expected[name]=dict(question=bound['question'],answer=bound['answer'],reference=bound['reference'],report_json=row['attempt']['report_json'],execution_state=row['attempt']['state'])
    calls=[];selector=VerifierSelector(verifiers=[RecordedVerifier(n,calls,expected) for n in BUILTIN_CAPABILITIES],capabilities=BUILTIN_CAPABILITIES)
    resources=ResourceManifest.model_validate(bundles['base_fact']['observed_setup']['resources'])
    result=config.router().run(selector,request,example['example_id'],provider=provider,rng=random.Random(1103),resource_observer=SimpleNamespace(snapshot=lambda:resources))
    print(json.dumps(dict(request=request.model_dump(mode='json'),public_status=result.public_status,team=result.summary['team'],calls=len(calls),selection_status=result.summary['selection_status'],early_stopping_enabled=result.summary['early_stopping_enabled'],mode='retained development replay; zero native inference'),indent=2))
if __name__=='__main__':main()
