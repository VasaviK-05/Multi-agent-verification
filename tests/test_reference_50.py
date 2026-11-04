import json
from pathlib import Path
from app.game.artifacts import PolicyArtifact
ROOT=Path('artifacts/remaining-category-studies-v1')
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def test_post_development_floor_only_changes_fitting_coverage():
    old=ROOT/'reference-current-v1';new=ROOT/'reference-50-v1'
    artifact=PolicyArtifact.model_validate(read(new/'fit/policy.json'))
    assert artifact.policy.matrix.clean_coverage.minimum==.5
    assert read(old/'fit/matrix.json')['clean_coverage']['minimum']==.9
    assert artifact.policy.matrix.values==tuple(tuple(row) for row in read(old/'fit/matrix.json')['values'])
    assert artifact.contract.model_dump(mode='json')==read(old/'fit/contract.json')
    assert read(old/'fit/training-manifest.json')==read(new/'fit/training-manifest.json')
    assert read(old/'fit/development-evaluation.json')==read(new/'fit/development-evaluation.json')
    assert artifact.policy.solution.status=='optimal'
    assert read(new/'amendment.json')['chosen_after_development'] is True
    assert not (old/'fit/policy.json').exists()
