"""Constructed engineering-pilot preparation tests; no empirical improvement claims."""
from fractions import Fraction
import json
from types import SimpleNamespace

import pytest

from app.game.offline.arithmetic_pilot import constructed_groups, preparation_rows, decimal_text, prepare


def test_sixty_seed42_groups_exact_labels_and_disjoint_splits():
    groups=constructed_groups()
    rows=preparation_rows()
    assert rows == preparation_rows()
    assert len(groups)==60 and len({g['question'] for g in groups})==60
    expected={g['group_id']:Fraction(g['expected_numerator'],g['expected_denominator']) for g in groups}
    memberships={}
    for role in ('history','development','final_test'):
        part=[e for e in rows if e['role']==role]
        assert len(part)==40 and len({e['split_identity'] for e in part})==20
        assert sum(e['label']['answer_is_correct'] for e in part)==20
        for e in part:
            assert memberships.setdefault(e['split_identity'],role)==role
            assert e['label']['answer_is_correct'] == (Fraction(e['answer'])==expected[e['split_identity']])
            assert json.loads(e['label']['provenance'])['framework_verifiers_used'] is False
    for g in groups:
        assert Fraction(g['incorrect'])-Fraction(g['expected']) == 1
    assert len({e['run_id'] for e in rows})==120


def test_decimal_formatter_uses_exact_finite_division():
    assert decimal_text(Fraction(11,8))=='1.375'
    assert decimal_text(Fraction(-3,4))=='-0.75'
    assert decimal_text(Fraction(8,2))=='4'
    with pytest.raises(ValueError,match='finite decimal'):
        decimal_text(Fraction(1,3))


def snapshot(tmp_path):
    path=tmp_path/'SYNTHETIC-model-files'
    path.mkdir()
    for name,body in [('config.json','{}'),('modules.json','[]'),('tokenizer.json','{}'),
                      ('model.safetensors','SYNTHETIC test bytes, not usable model weights')]:
        (path/name).write_text(body)
    return path


@pytest.mark.parametrize('project_ready', [False, True])
def test_prepare_keeps_final_labels_separate_and_has_no_fit_settings(tmp_path,monkeypatch,project_ready):
    import app.benchmark.project_adapter as project
    from app.game.offline.collection import RecordingRequest
    path=snapshot(tmp_path)
    monkeypatch.setattr(project,'inspect_setup',lambda c:dict(ready=project_ready,blockers=[] if project_ready else [{'resource':'index_provenance'}]))
    config=dict(embedding_snapshot=str(path),nli_snapshot=None,corpus_path='unused',index_dir='unused',
                index_receipt=None,service_observation=None)
    output=tmp_path/'pilot'
    summary=prepare(output,config,preparation_authorization='SYNTHETIC permission',
                custody_record='SYNTHETIC custody',freeze_record='SYNTHETIC freeze')
    request=RecordingRequest.model_validate_json((output/'inputs/recording-request.json').read_text())
    final=[json.loads(line) for line in (output/'custody/final-examples.jsonl').read_text().splitlines()]
    assert summary['held_out_examples']==40 and len(request.examples)==80
    assert summary['excluded_verifiers']['evidence']=='Outside arithmetic-only roster; no retrieval/corpus adapter used'
    assert summary['full_project_ready'] is project_ready
    assert not {e['example_id'] for e in final}&{e.example_id for e in request.examples}
    assert {e['example_id'] for e in final}=={e.example_id for e in request.final_test_reservation.examples}
    assert all(e.role in {'history','development'} for e in request.examples)
    assert all(e.analysis.verification_types==['arithmetic'] for e in request.examples)
    assert {e.analysis.difficulty for e in request.examples}=={'easy'}  # never relabel to hard for a smaller team
    assert json.loads((output/'inputs/calibration-settings.json').read_text())['include_warmups'] is True
    assert not {'budget','threshold','history_prior_alpha'} & set(request.model_dump())
    with pytest.raises(FileExistsError):
        prepare(output,config,preparation_authorization='SYNTHETIC permission',
                custody_record='SYNTHETIC custody',freeze_record='SYNTHETIC freeze')


def test_narrow_factory_uses_only_local_embedding_and_real_project_constructors(tmp_path,monkeypatch):
    import torch
    import sentence_transformers
    import app.benchmark.project_adapter as project
    import app.game.offline.recording_adapters as adapters
    path=snapshot(tmp_path)
    config=tmp_path/'adapter.json'
    config.write_text(json.dumps(dict(embedding_snapshot=str(path),torch_num_threads=2)))
    monkeypatch.setenv('VERIFIER_ARITHMETIC_ADAPTER_CONFIG',str(config))
    calls=[]
    monkeypatch.setattr(sentence_transformers,'SentenceTransformer',lambda *a,**kw:(calls.append((a,kw)) or object()))
    monkeypatch.setattr(torch,'set_num_threads',lambda n:calls.append(('threads',n)))
    monkeypatch.setattr(torch,'get_num_threads',lambda:2)
    pool,setup,observer=adapters.arithmetic_factory()
    assert [v.name for v in pool]==['rule','semantic']
    assert calls[0]==('threads',2)
    assert calls[1][1]==dict(device='cpu',local_files_only=True)
    assert setup.resources==observer.snapshot()
    assert set(v.verifier_name for v in setup.resources.verifiers)=={'rule','semantic'}
    assert all(r.kind not in {'index','corpus','service'} for v in setup.resources.verifiers for r in v.resources)


def test_preparation_requires_new_authority_before_resource_access(tmp_path):
    with pytest.raises(ValueError, match='preparation_authorization'):
        prepare(tmp_path/'not-created', {}, preparation_authorization='',
                custody_record='SYNTHETIC', freeze_record='SYNTHETIC')
    assert not (tmp_path/'not-created').exists()
