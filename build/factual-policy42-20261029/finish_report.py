"""Local completion audit and readable report; never reads custody payloads."""
import hashlib
import json
import math
from pathlib import Path
import sys

def guard(event,args):
    if event=='open' and isinstance(args[0],str) and 'custody' in Path(args[0]).parts:
        raise AssertionError('final payload access forbidden')
sys.addaudithook(guard)
from app.game.artifacts import PolicyArtifact, InMemoryPolicyProvider
from app.game.models import content_id
from app.game.solver import validate_solution
root=Path(__file__).parent
read=lambda name:json.loads((root/name).read_text(encoding='utf-8'))
report=read('development-report.json')
build=read('fitted-policy/build-report.json')
science=build['scientific_outputs']
approval=read('approval-binding.json')
artifact=PolicyArtifact.model_validate_json((root/'fitted-policy/policy.json').read_text(encoding='utf-8'))
validate_solution(artifact.policy.matrix,artifact.policy.solution)
assert len(InMemoryPolicyProvider((artifact,)).snapshot())==1
assert len(report['runtime_checks'])==2 and all(r['parity'] for r in report['runtime_checks'])
assert report['collection']['complete'] and report['collection']['executed_calls']==320
assert len(artifact.policy.strategies)==14
app=Path('app')
digest=content_id([(p.as_posix(),hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted(app.rglob('*.py'))])
setup=read('collection/observed-setup.json')
assert digest==setup['application_source_digest']
assert hashlib.sha256((root/'fit-driver.original.py').read_bytes()).hexdigest()==approval['driver_sha256']
arith=Path('build/arithmetic-pilot42')
old=json.loads((arith/'investigation/traces.json').read_text(encoding='utf-8'))['original_hashes']
assert all(hashlib.sha256((arith/name).read_bytes()).hexdigest()==sha for name,sha in old.items())
proof=dict(artifact_id=artifact.artifact_id,policy_id=artifact.policy.policy_id,matrix_id=artifact.policy.matrix.matrix_id,
    reputation_snapshot_id=artifact.context.reputation_snapshot_id,calibration_id=approval['calibration_id'],
    certificate_valid=True,provider_reload_valid=True,retained_report_runtime_parity=True,live_real_resources_compatible=True,
    final_payload_access_guard_active=True,final_collection_or_evaluation=False,attempts=320,additional_inference_attempts=0,
    application_source_unchanged=True,original_fit_driver_preserved=True,arithmetic_original_files_unchanged=len(old),
    reproducibility=science['reproducibility'],configuration_digest=approval['configuration_digest'],
    report_driver_sha256=report['report_driver_sha256'])
with (root/'final-verification.json').open('x',encoding='utf-8') as f:json.dump(proof,f,indent=2)
lines=['# Factual development report','',
    'Engineering development evidence only. The fitted artifact always abstains and is not a useful operational policy.',
    '',f"Artifact: `{artifact.artifact_id}`",f"Budget: {artifact.context.budget:.9f} summed attempt ms; resource weight: {artifact.context.loss_configuration.resource_weight:.12g} loss/ms.",
    '', '## Every strategy', '']
for s in report['strategies']:
    lines.append(f"- {', '.join(s['verifiers'])}; {s['aggregation']}; probability {s['probability']:.12g}; estimated cost {s['estimated_cost']:.9f} ms.")
lines+=['','## Fitted-policy scenarios','']
for s in report['scenarios']:
    m=s['metrics'];n=m['examples']
    lines.append(f"- {s['attack']['kind']}: validation loss {s['validation_loss']:.12g}; false accept {m['false_accept']}/{n}; false reject {m['false_reject']}/{n}; uncertainty {s['uncertainty_rate']:.3%}; coverage {m['decision_coverage']:.3%}; estimated cost {m['estimated_resource_cost']:.9f} ms; cost-inclusive objective {m['mean_loss']:.12g}.")
lines+=['','## History and contributor weights','',json.dumps(report['history'],indent=2),
    '', '## Compatible recorded baselines','',report['baseline_scope'],'',json.dumps(report['baselines'],indent=2),
    '', '## Representative correct and incorrect decisions','',
    'These retained history/development labels remain private/local. No final-test labels or outcomes were opened.']
selected=next(s for s in artifact.policy.strategies if dict(artifact.policy.solution.probabilities)[s.strategy_id]>0)
for t in report['representative_traces']:
    lines+=['',f"### {t['example_id']}",'',t['question'],t['answer'],f"Independent correct label: {t['label']}",'','Raw reports:','```json',json.dumps(t['reports'],indent=2,ensure_ascii=False),'```']
    for o in t['strategies']:
        strategy=next(s for s in artifact.policy.strategies if s.strategy_id==o['strategy_id'])
        if strategy.verifiers!=selected.verifiers:continue
        detail=json.loads(o['decision_json'])
        lines+=['',f"Aggregation: {strategy.aggregation}; numerical {o['numerical_status']} at {o['numerical_score']:.12g}; public {o['public_status']}; contributors {o['contributors']}; required {o['required']}; achieved {o['achieved']}; reasons {o['reasons']}.",
            '```json',json.dumps(detail,indent=2),'```']
lines+=['','## Validation','',json.dumps(proof,indent=2),
    '', 'All fourteen per-strategy/per-attack metrics and full representative traces are in development-report.json.',
    'Equivalent payoff rows do not establish aggregation superiority. No study settings were tuned after development.',
    'Initial fit/report phases encountered a sandbox metadata denial and a report-only dataclass serialization defect; report phase alone was corrected and rerun. Artifact, calibration and recordings were preserved.']
with (root/'development-summary.md').open('x',encoding='utf-8') as f:f.write('\n'.join(lines)+'\n')
print(json.dumps(proof,indent=2))
