"""Synthetic cost inputs only; tests make no verifier calls or research claims."""
from copy import deepcopy
import json
from pathlib import Path

import pytest

from app.game.models import content_id
from app.game.offline.calibration import MeasurementSetup, calibrate
from app.game.offline.collection import RecordingRequest
from app.game.resource_provenance import ResourceManifest
from scripts.prepare_factual_team_pilot import package
from tests.test_cost_calibration import request


@pytest.fixture(scope='module')
def inputs():
    from tests.factual_fixtures import draft_request
    draft=draft_request()
    base=request()
    names=('semantic','evidence','rule','confidence')
    manifest=ResourceManifest(verifiers=[dict(verifier_name=n,resources=[
        dict(kind='implementation',resource_id=n+'-source',sha256=content_id(n)),
        dict(kind='configuration',resource_id=n+'-config',sha256=content_id(['config',n])),
        *[dict(kind=k,resource_id=n+'-'+k,sha256=content_id(['SYNTHETIC',n,k])) for k in ({'corpus','index'} if n=='evidence' else {'prompt','service'} if n=='confidence' else set())],
        *([dict(kind='model',resource_id='local-embedding-snapshot',sha256='e'*64)] if n in {'semantic','evidence'} else []),
        *([dict(kind='model',resource_id='local-nli-snapshot',sha256='f'*64)] if n in {'evidence','confidence'} else [])]) for n in names])
    setup=MeasurementSetup(**{**base['measurements']['setup'].model_dump(),'resources':manifest})
    template=base['measurements']['attempts'][0]
    attempts=[]
    for v in manifest.verifiers:
        attempts.append({**template,'verifier_name':v.verifier_name,'setup_fingerprint':setup.fingerprint,
            'verifier_fingerprint':content_id(v.model_dump(mode='json'))})
    base['measurements'].update(setup=setup,attempts=attempts)
    base['required_verifiers']=names
    return draft,calibrate(base),dict(ready=True,observed_setup=setup.model_dump(mode='json'))


def test_public_enumeration_multiple_teams_both_aggregations_without_construction(inputs,monkeypatch):
    import app.selection.verifier_selector as selection
    def forbidden(*a,**kw): pytest.fail('planning must not initialize a verifier')
    monkeypatch.setattr(selection,'_build_default_verifier',forbidden)
    p=package(*inputs)
    teams=p['teams.json']
    assert len(teams['teams'])==7 and len(teams['strategies']['strategies'])==14
    assert teams['participant_floor']==2 and teams['history_observations']==0
    assert all('evidence' in t['verifiers'] and t['size']>=2 for t in teams['teams'])
    assert {s['aggregation'] for s in teams['strategies']['strategies']}=={'reputation_weighted','dependency_group'}


def test_balanced_constructed_candidates_keep_original_groups_and_independent_labels(inputs):
    p=package(*inputs)
    rows=p['recording-request.pending.json']['examples']
    assert len(rows)==4
    for role in ('history','development'):
        group=[e for e in rows if e['role']==role]
        assert len({e['question_id'] for e in group})==len({e['split_identity'] for e in group})==1
        assert sorted(e['label']['answer_is_correct'] for e in group)==[False,True]
        assert all(e['label']['label_method']=='independent_ground_truth' for e in group)
    assert not {e['split_identity'] for e in rows if e['role']=='history'} & {e['split_identity'] for e in rows if e['role']=='development'}


def test_reservation_is_metadata_only_and_no_approval_invented(inputs):
    p=package(*inputs)
    request=p['recording-request.pending.json']
    assert request['preparation_authorization'] is None
    assert request['final_test_reservation']['custody_record'] is None
    with pytest.raises(ValueError): RecordingRequest.model_validate(request)
    assert len(request['final_test_reservation']['examples'])==4
    forbidden={'question','answer','reference','label','reports','attempts','answer_is_correct'}
    assert all(not forbidden & set(e) for e in request['final_test_reservation']['examples'])
    assert p['settings.pending.json']['fit_authorized'] is False
    assert p['calibration-settings.pending.json']['freeze_record'] is None


def test_unknown_rows_retained_in_exclusion_audit_not_relabelled(inputs):
    p=package(*inputs)
    excluded=[e for e in p['exclusions.json']['rows'] if not e['selected']]
    assert len(excluded)==4
    assert all(e['reason']=='requirements_unknown' and not e['analysis']['verification_types'] for e in excluded)
    assert all(e['retained_in_original_draft'] for e in excluded)


def test_changed_source_or_analyzer_requires_readjudication(inputs):
    draft,calibration,preflight=inputs
    for field,value in [('answer','An unrelated answer'),('question','Who developed relativity?')]:
        changed=deepcopy(draft)
        changed['examples'][0][field]=value
        with pytest.raises(ValueError): package(changed,calibration,preflight)


def test_unproven_shared_resource_and_resource_blocker_reject(inputs):
    draft,calibration,preflight=inputs
    with pytest.raises(ValueError,match='preflight'): package(draft,calibration,{'ready':False})
    changed=deepcopy(preflight)
    evidence=next(v for v in changed['observed_setup']['resources']['verifiers'] if v['verifier_name']=='evidence')
    next(r for r in evidence['resources'] if r['resource_id']=='local-embedding-snapshot')['sha256']='1'*64
    with pytest.raises(ValueError,match='shared resource'): package(draft,calibration,changed)
