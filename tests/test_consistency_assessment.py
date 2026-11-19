"""Fabricated native-shaped reports only: zero verifier/provider/model calls."""
from copy import deepcopy
from collections import Counter
import pytest
from app.models.schemas import VerificationResult
from app.game.consistency_assessment import (ConsistencyAssessmentContract,
    completed_consistency, consistency_capabilities)

CONTRACT = ConsistencyAssessmentContract(n_samples=5, generator_model='SYNTHETIC-ONLY', temperature=.8)


def report(labels=('support',)*5, **changes):
    counts = Counter(labels)
    largest = max(counts.values())
    leaders = [key for key, count in counts.items() if count == largest]
    leader = leaders[0] if len(leaders)==1 else 'tie'
    metadata = dict(method='self_consistency', judgment_source='self_consistency',
        generator_model='SYNTHETIC-ONLY', temperature=.8, n_samples=5,
        stable_answer=largest>len(labels)/2, claim='SYNTHETIC candidate claim',
        judgments=list(labels), judgment_counts=dict(counts), agreement_count=largest,
        total_judgments=len(labels), majority_label=leader,
        samples=[dict(sample='8' if label=='support' else '9', label=label, method='numeric') for label in labels],
        decision='SUPPORT' if leader=='support' else 'REJECT' if leader=='reject' else 'UNSURE')
    metadata.update(changes)
    return VerificationResult(verifier_name='confidence', passed=leader=='support',
        score=largest/len(labels), metadata=metadata)


@pytest.mark.parametrize('labels',[('support',)*5, ('reject',)*5, ('support',)*3+('reject',)*2])
def test_completed_native_assessment_has_only_consistency_coverage(labels):
    assert consistency_capabilities(report(labels), CONTRACT)=={'consistency'}


def test_stable_but_objectively_wrong_is_consistency_not_truth():
    row = report()  # Imagined model consistently says 8 for a case whose truth is 9.
    assert completed_consistency(row, CONTRACT)
    assert not consistency_capabilities(row, CONTRACT) & {'arithmetic','direct_fact','semantic_comparison'}


@pytest.mark.parametrize('changes', [dict(judgment_source='context'), dict(judgment_source='argument'),
    dict(judgment_source='provider_unavailable'), dict(n_samples=4), dict(n_samples=True),
    dict(generator_model='changed'), dict(temperature=.7), dict(stable_answer=False),
    dict(judgment_counts={'support':4}), dict(total_judgments=4), dict(agreement_count=True),
    dict(samples=[]), dict(claim=''), dict(decision='UNSURE'), dict(majority_label='reject')])
def test_bad_trace_cannot_establish_coverage(changes):
    assert not completed_consistency(report(**changes), CONTRACT)


@pytest.mark.parametrize('key',['samples','generator_model','n_samples','temperature','stable_answer','judgments','judgment_counts'])
def test_missing_sampling_metadata_rejected(key):
    row = report(); row.metadata.pop(key)
    assert not completed_consistency(row, CONTRACT)


@pytest.mark.parametrize('labels',[('support','support','reject','reject','unsure'),
    ('support','support','reject','unsure','unsure'), ('unsure',)*5])
def test_low_agreement_tie_and_abstention_do_not_cover(labels):
    assert not completed_consistency(report(labels), CONTRACT)


@pytest.mark.parametrize('state',['timeout','unavailable_model','failure'])
def test_native_failure_abstention_does_not_cover(state):
    row = VerificationResult(verifier_name='confidence', passed=False, score=0.,
        metadata={'decision':'UNSURE','judgment_source':'provider_unavailable','error':state,'judgments':[]})
    assert not completed_consistency(row, CONTRACT)


def test_zero_confidence_wrong_identity_and_malformed_sample():
    row = report(); row.score=0.
    assert not completed_consistency(row, CONTRACT)
    row = report(); row.verifier_name='evidence'
    assert not completed_consistency(row, CONTRACT)
    row = report(); row.metadata['samples'][0]['label']='reject'
    assert not completed_consistency(row, CONTRACT)


def test_duplicate_and_conflicting_report_identities_are_not_extra_contributors():
    from app.decision.report_identity import canonical_reports
    row = report()
    assert len(canonical_reports([row, row], validation_id='SYNTHETIC', deduplicate=True)[0])==1
    with pytest.raises(ValueError, match='duplicate'):
        canonical_reports([row,row], validation_id='SYNTHETIC', deduplicate=False)
    with pytest.raises(ValueError, match='conflicting'):
        canonical_reports([row,report(('reject',)*5)], validation_id='SYNTHETIC', deduplicate=True)


@pytest.mark.parametrize('change',['bad_score_type','bad_passed_type','unhashable_method'])
def test_malformed_unvalidated_objects_fail_closed(change):
    row = report()
    if change=='bad_score_type': row = row.model_copy(update={'score':'bad'})
    elif change=='bad_passed_type': row = row.model_copy(update={'passed':1})
    else: row.metadata['samples'][0]['method']=[]
    assert not completed_consistency(row, CONTRACT)
