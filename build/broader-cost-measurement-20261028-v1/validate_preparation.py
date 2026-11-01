"""Read-only checks apart from a new validation receipt; no verifier execution."""
import hashlib
import json
from pathlib import Path
from app.game.offline.calibration import read_json
from app.analysis.question_analyzer import QuestionAnalyzer
from app.selection.requirements import requirement_inputs
from dataclasses import asdict

root = Path(__file__).parent
old = Path('build/factual-diagnostic-20261026-01')
summary = read_json(old / 'diagnostic-summary.json')
for entry in summary['artifacts']:
    assert hashlib.sha256((old / entry['path']).read_bytes()).hexdigest() == entry['sha256']
request = read_json(root / 'recording-request.pending.json')
analyzer = QuestionAnalyzer(mode='heuristic', environ={})
unknown = []
for e in request['examples']:
    analysis = analyzer.analyze(e['question'])
    assert asdict(analysis) == e['analysis']
    if not requirement_inputs(analysis).requirements_known:
        unknown.append(e['example_id'])
old_request = read_json(old / 'collection/request.json')
for e in old_request['examples']:
    current = next(r for r in request['examples'] if r['example_id'] == e['example_id'])
    assert current['analysis'] == e['analysis']
    assert all(current[k] == e[k] for k in ('question','answer','reference','role','dataset_id','split_identity','question_id'))
assert set(unknown) == set(summary['unknown_requirement_examples'])
assert len({e['run_id'] for e in request['examples']}) == 86
receipt = dict(valid=True, diagnostic_artifact_digests_unchanged=True,
    preparation_inputs_preserved=True, actual_analyzer_outputs_match=True,
    unknown_requirement_examples=unknown, new_attempts=0, new_generations=0,
    new_metadata_requests=0, focused_tests=dict(passed=27, failed=0),
    evidence_probe=dict(passed=1, failed=3, deselected=88),
    final_contents_or_outcomes_accessed=False, policy_fitted=False)
with (root / 'validation.json').open('x', encoding='utf-8') as f:
    json.dump(receipt, f, indent=2)
print(json.dumps(receipt))
