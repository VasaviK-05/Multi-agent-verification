"""Readiness/input metadata tests only. No fitting, replay or final payloads."""
import importlib.util
from pathlib import Path

import pytest

ROOT=Path(__file__).resolve().parents[1]


def assembler():
    spec=importlib.util.spec_from_file_location('phase_b_assembly',ROOT/'docs/experiment1/phase-b/assemble_inputs.py')
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_actual_metadata_assembly_blocks_missing_custody_without_final_reads(monkeypatch):
    import app.game.solver as solver
    import app.game.offline.replay as replay
    import app.game.offline.evaluation as evaluation
    import app.game.research.comparison as comparison
    def forbidden(*args,**kwargs):
        raise AssertionError('Phase B attempted scoring, fitting, or final payload access')
    for obj,name in ((solver,'linprog'),(solver,'solve_minimax'),(replay,'replay'),
                     (evaluation,'construct_payoffs'),(evaluation,'evaluate_final_test'),
                     (comparison,'prepare_comparison')):
        monkeypatch.setattr(obj,name,forbidden)
    actual=Path.read_bytes
    def guarded(path):
        relative=path.resolve().relative_to(ROOT) if path.resolve().is_relative_to(ROOT) else path
        text=str(relative).replace('\\','/')
        if '/test/' in text or text.endswith(('final-partition.json','heldout-results.json','replay-outcomes.json','reserved-request.json')):
            raise AssertionError('sealed final payload opened: '+text)
        return actual(path)
    monkeypatch.setattr(Path,'read_bytes',guarded)
    module=assembler()
    data=module.assemble()
    assert data['final_outcome_payloads_opened']==[] and data['final_scoring'] is False and data['optimization'] is False
    assert data['cohorts']['reference']['coverage_floor']==.5
    assert data['cohorts']['compound']['coverage_floor']==.85
    assert all(data['cohorts']['compound']['transfer_source_checks'].values())
    assert data['cohorts']['original_semantic']['minimum']==.9
    assert data['cohorts']['original_semantic']['probabilities']==()
    assert all(data['cohorts'][c]['blockers'] for c in ('arithmetic','factual','compound','reference'))
    assert len(data['cohorts']['arithmetic']['historical_comparison']['methods'])==3
    assert data['cohorts']['arithmetic']['historical_comparison']['statistics']['replicates']==10000
    assert data['cohorts']['reference']['historical_comparison']['statistics']['resamples']==1000
    assert all(not record['replacement_permitted'] for c in ('arithmetic','factual','compound','reference')
               for record in data['cohorts'][c]['missing'] if 'redacted_view' in record)
    for path in data['input_files']:
        assert '/test/' not in path and not path.endswith('final-partition.json')


@pytest.mark.parametrize('path',[
    'artifacts/flexible-heldout-v1/arithmetic/final-partition.json',
    'artifacts/remaining-category-studies-v1/reference-50-v1/test/reference/bundle.json',
    'artifacts/remaining-category-studies-v1/scoped-er-v1/test/joint.json',
    'artifacts/publication-v1/public-audit/artifacts/remaining-category-studies-v1/reference-50-v1/fit/freeze.json',
])
def test_no_general_payload_or_redaction_loader(path):
    with pytest.raises(ValueError,match='not an allowed readiness input'):
        assembler().load(path)
