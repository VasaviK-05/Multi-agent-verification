"""Test draft preparation only: no empirical calls, costs or approval claims."""
import copy
import json
from pathlib import Path

import pytest

from app.game.models import content_id
from app.game.offline.records import ReservedExample
from scripts.prepare_factual_study_draft import (draft_package, validate_package,
    observed_recording_references, bind_inspected_resources)


def inputs():
    from tests.factual_fixtures import candidate_inputs
    return candidate_inputs()


def test_fixed_group_allocation_and_metadata_only_final():
    rows, adapter = inputs()
    package = draft_package(rows, adapter, source_digest='SYNTHETIC_INPUT_DIGEST_FOR_TEST')
    roster = package['roster.draft.json']
    assert roster['allocation'] == dict(germany='history', ai_ml='history', python='development',
        india='development', relativity='development', wwii='final_test', usa='final_test', france_paris='final_test')
    reservation = package['final-reservation.draft.json']
    assert reservation['custody_record'] is None
    assert len(reservation['examples']) == 4
    assert all(set(e) == set(ReservedExample.model_fields) for e in reservation['examples'])
    ids = {e['example_id'] for e in reservation['examples']}
    assert not ids & {e['example_id'] for e in package['recording-request.draft.json']['examples']}
    assert not ids & {e['example_id'] for e in package['label-review.draft.json']['preparation_labels']}
    assert len(package['recording-request.draft.json']['examples']) == 6


def test_benchmark_flags_never_used_for_labels_or_allocation():
    rows, adapter = inputs()
    original = draft_package(rows, adapter, source_digest='SYNTHETIC_FIXED_DIGEST')
    class ForbiddenFlag:
        def __bool__(self):
            pytest.fail('benchmark flag used')
    for row in rows:
        row['answer_is_correct'] = ForbiddenFlag()
    assert original == draft_package(rows, adapter, source_digest='SYNTHETIC_FIXED_DIGEST')
    assert all(e['status'] == 'draft_source_grounded_not_approved'
        and e['human_approval'] is None and e['benchmark_flags_used'] is False
        for e in original['label-review.draft.json']['preparation_labels'])


def test_analyzer_and_capabilities_are_actual_producer_outputs(monkeypatch):
    from app.analysis.question_analyzer import QuestionAnalyzer
    from dataclasses import asdict
    import requests
    def forbidden(*a, **kw):
        pytest.fail('network/provider request from draft preparation')
    monkeypatch.setattr(requests.Session, 'request', forbidden)
    rows, adapter = inputs()
    package = draft_package(rows, adapter, source_digest='SYNTHETIC_FIXED_DIGEST')
    analyzer = QuestionAnalyzer(mode='heuristic', environ={})
    for example in package['recording-request.draft.json']['examples']:
        assert example['analysis'] == asdict(analyzer.analyze(example['question']))
    assert sum(e['analysis']['research_context']['requirements_known']
               for e in package['recording-request.draft.json']['examples']) == 2


def test_drafts_fail_closed_until_real_permissions_resources_freeze_exist():
    rows, adapter = inputs()
    validation = validate_package(draft_package(rows, adapter, source_digest='SYNTHETIC_FIXED_DIGEST'))
    assert validation['contracts']['adapter.draft.json']['valid']
    assert validation['contracts']['dependencies.proposed.json']['valid']
    assert validation['contracts']['attacks.proposed.json']['valid']
    assert not validation['contracts']['recording-request.draft.json']['valid']
    assert not validation['contracts']['final-reservation.draft.json']['valid']
    assert not validation['contracts']['execution-contract.draft.json']['valid']
    locations = {tuple(e['location']) for e in validation['contracts']['recording-request.draft.json']['unresolved_fields']}
    assert ('preparation_authorization',) in locations
    assert ('execution_configuration_id',) in locations
    assert ('final_test_reservation', 'custody_record') in locations


def test_resource_workload_and_no_budget_before_measurements():
    rows, adapter = inputs()
    package = draft_package(rows, adapter, source_digest='SYNTHETIC_FIXED_DIGEST')
    plan = package['resource-plan.json']
    assert plan['expected_chunks'] == 10 and plan['verifier_attempts'] == 24
    assert plan['generation_requests_if_all_reached'] == 30
    assert plan['total_intended_metadata_get_requests'] == 100
    assert plan['generation_timeout_upper_bound_seconds'] == 1800.
    losses = package['loss-settings.proposed.json']
    assert losses['budget'] is None and losses['resource_weight'] is None
    assert package['calibration-settings.draft.json']['freeze_record'] is None


def test_preparation_is_reproducible_and_does_not_mutate_inputs():
    rows, adapter = inputs()
    before = copy.deepcopy((rows, adapter))
    first = draft_package(rows, adapter, source_digest='SYNTHETIC_FIXED_DIGEST')
    second = draft_package(rows, adapter, source_digest='SYNTHETIC_FIXED_DIGEST')
    assert content_id(first) == content_id(second)
    assert before == (rows, adapter)


def test_changed_candidate_cannot_inherit_unrelated_source_label():
    rows, adapter = inputs()
    rows[1]['answer'] = 'SYNTHETIC changed candidate with no evidence'
    with pytest.raises(ValueError, match='re-adjudicate'):
        draft_package(rows, adapter, source_digest='SYNTHETIC_FIXED_DIGEST')


def test_recording_references_copy_only_observed_fingerprints():
    references = observed_recording_references(dict(embedding_snapshot={'sha256': 'a'*64},
        service={'model_digest': 'sha256:'+'b'*64}))
    assert references['execution_configuration_id'] is None
    assert references['model_fingerprints'] == [('embedding_snapshot', 'sha256:'+'a'*64),
                                              ('ollama_model', 'sha256:'+'b'*64)]
    assert references['corpus_fingerprints'] == []
    assert all(len(digest.removeprefix('sha256:')) == 64 for _, digest in
               references['prompt_and_adapter_fingerprints'])


def test_roster_shape_passes_real_contract_with_test_only_witnesses():
    from app.game.offline.collection import RecordingRequest
    rows, adapter = inputs()
    draft = draft_package(rows, adapter, source_digest='SYNTHETIC_FIXED_DIGEST')['recording-request.draft.json']
    checked = copy.deepcopy(draft)
    checked['preparation_authorization'] = 'SYNTHETIC TEST ONLY permission'
    checked['execution_configuration_id'] = 'SYNTHETIC TEST ONLY configuration'
    checked['final_test_reservation']['custody_record'] = 'SYNTHETIC TEST ONLY witness'
    result = RecordingRequest.model_validate(checked)
    assert len(result.examples) == 6
    assert draft['preparation_authorization'] is None
    assert draft['final_test_reservation']['custody_record'] is None
    checked['examples'][0]['split_identity'] = checked['final_test_reservation']['examples'][0]['split_identity']
    with pytest.raises(ValueError, match='final-test'):
        RecordingRequest.model_validate(checked)


def test_actual_resource_binding_does_not_fill_permission_or_witness():
    from tests.test_cost_calibration import request as synthetic_request
    rows, adapter = inputs()
    package = draft_package(rows, adapter, source_digest='SYNTHETIC_FIXED_DIGEST')
    setup = synthetic_request()['measurements']['setup']
    result = bind_inspected_resources(package, dict(ready=True, inventory={},
        observed_setup=setup.model_dump(mode='json')))
    assert result['recording-request.draft.json']['execution_configuration_id'] == setup.resources.manifest_id
    assert result['execution-contract.draft.json']['resource_manifest'] == setup.resources.model_dump(mode='json')
    assert result['recording-request.draft.json']['preparation_authorization'] is None
    assert result['final-reservation.draft.json']['custody_record'] is None
    assert package['recording-request.draft.json']['expected_setup'] is None


def test_package_fixture_never_opens_mixed_reserved_source(monkeypatch):
    original = Path.read_text
    def guarded(path, *args, **kwargs):
        if (path.resolve() == Path('data/test_benchmark.jsonl').resolve()
                or ('studies' in path.parts and path.suffix == '.json')):
            pytest.fail('test fixture opened mixed source containing reserved payloads')
        return original(path, *args, **kwargs)
    monkeypatch.setattr(Path, 'read_text', guarded)
    rows, adapter = inputs()
    result = draft_package(rows, adapter, source_digest='SYNTHETIC_FIXED_DIGEST')
    assert len(result['recording-request.draft.json']['examples']) == 6
    assert len(result['final-reservation.draft.json']['examples']) == 4
