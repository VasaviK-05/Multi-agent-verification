"""Record actual CLI return statuses without collecting or fabricating inputs."""
from contextlib import redirect_stdout
import io
import json
from pathlib import Path

from pydantic import ValidationError
from app.benchmark.collect_costs import CollectionRequest
from app.game.offline import build, calibration

root = Path.cwd()
out = root / 'build/empirical-policy-attempt'
report_path = root / 'docs/game_empirical_build_audit.json'
report = json.loads(report_path.read_text(encoding='utf-8'))
attempts = {}
for name, entry, args in (
    ('policy_build', build.main, ['docs/game_policy_build.template.json', '--output-dir', str(out)]),
    ('cost_calibration', calibration.main, ['docs/verifier_cost_calibration.template.json', '--output', str(out/'verifier-costs.json')]),
):
    buffer = io.StringIO()
    with redirect_stdout(buffer):
        status = entry(args)
    (out / (name + '.log')).write_text(buffer.getvalue(), encoding='utf-8')
    attempts[name] = dict(main_return_status=status, arguments=args, stdout_log=str(out/(name+'.log')))
try:
    CollectionRequest.model_validate(calibration.read_json(root/'docs/verifier_cost_collection.template.json'))
except ValidationError as exc:
    attempts['collection_request_validation'] = dict(ready=False, factory_initialized=False,
        errors=[dict(location=list(e['loc']), message=e['msg']) for e in exc.errors(include_url=False)])
baseline = json.loads((out/'evidence-baseline.json').read_text(encoding='utf-8'))
assert baseline['returncode'] == 1 and '3 failed, 1 passed' in baseline['stdout']
assert not (out/'policy.json').exists() and not (out/'verifier-costs.json').exists()
report['attempts'] = attempts
report['environment'] = build.environment_versions()
report['validation'] = dict(working_tree=dict(passed=49, failed=3, deselected=88,
    command='.venv/Scripts/python.exe -m pytest tests/test_game_build.py tests/test_cost_calibration.py tests/test_adaptive_pipeline.py -k "test_game_build or test_cost_calibration or test_actual_evidence_output_contract_is_consumed_without_models or test_actual_conflicting_evidence_cannot_cover_factual_request" -q -p no:cacheprovider'),
    pristine_head_evidence=dict(passed=1, failed=3, deselected=88,
        evidence='build/empirical-policy-attempt/evidence-baseline.json'),
    new_failures=0)
report_path.write_text(json.dumps(report, indent=2), encoding='utf-8')
print(json.dumps(dict(outcome=report['outcome'], attempt_statuses={k:v.get('main_return_status')
    for k,v in attempts.items()}, empirical_artifact_created=False), indent=2))
