"""Read-only completion audit: no inference, service requests or resource loads."""
import hashlib
import json
from pathlib import Path

from app.benchmark import project_adapter as a
from app.game.models import content_id
from scripts.verify_reconciliation_package import verify
from scripts.framework_acceptance import read_plan
from app.game.offline.singleton_compatibility import transfer_for

REVIEW_ID='a8bfc20323bae911ba4968fc7f060ad1c608d0c4d5eccc57708c569a36797cdd'


def audit_delivery():
    root=a.ROOT;sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    review=a.read_json(root/'reconciliation/framework-completion-review-v1.json')
    if review['review_id']!=REVIEW_ID or content_id({k:v for k,v in review.items() if k!='review_id'})!=REVIEW_ID:
        raise ValueError('unreviewed framework completion layer')
    if content_id(a.read_json(root/'reconciliation/main-merge-review-v1.json'))!=review['parent_merge_review_content_id']:
        raise ValueError('historical merge review changed')
    parent=a.read_json(root/'reconciliation/main-merge-review-v1.json')
    changes=review['publication_overlay_changes']
    if set(changes)!={'.gitattributes','app/game/execution.py'}:raise ValueError('unreviewed software overlay scope')
    expected={p:v['merged_checkout_sha256'] for p,v in parent['publication_source_overlays'].items()}
    for p,delta in changes.items():
        if expected[p]!=delta['parent_checkout_sha256']:raise ValueError('software overlay parent differs')
        expected[p]=delta['delivery_checkout_sha256']
    inventory=a.read_json(root/'artifacts/publication-v1/file-hashes-v3.json')
    differences=[]
    for p,old in inventory.items():
        actual=sha(root/p)
        if actual!=old['sha256']:
            differences.append(p)
            if expected.get(p)!=actual:raise ValueError('unreviewed publication change: '+p)
    if set(differences)!=set(expected):raise ValueError('publication overlay inventory differs')
    identities=verify()
    from scripts.reconciliation import load_bundle
    _,provider,_=load_bundle()
    for artifact in provider.snapshot()[:2]:transfer_for(artifact)
    plan=read_plan();evidence=a.read_json(root/'reconciliation/framework-native-evidence-v1.json')
    for p,digest in evidence['tested_execution_source_sha256'].items():
        if sha(root/p)!=digest:raise ValueError('execution code differs from native acceptance: '+p)
    if not evidence['complete'] or evidence['plan_id']!=plan['plan_id'] or evidence['native_calls_started']!=8 or evidence['native_calls_completed']!=8:
        raise ValueError('native campaign incomplete')
    if evidence['confidence_generations']!=0 or evidence['retries']!=0:raise ValueError('native campaign exceeded authorization')
    starts=[e for e in evidence['call_events'] if e['event']=='started'];ends=[e for e in evidence['call_events'] if e['event']=='completed']
    if [e['call_number'] for e in starts]!=list(range(1,9)) or [e['call_number'] for e in ends]!=list(range(1,9)):
        raise ValueError('native journal has a gap/duplicate')
    for category,number in [('arithmetic',2),('factual',2),('compound',4)]:
        if sum(e['category']==category for e in starts)!=number:raise ValueError('native category cap differs')
    for row,item in zip(evidence['requests'],plan['requests'],strict=True):
        if row['request_id']!=item['request_id'] or row['team']!=item['expected_team'] or row['native_calls']!=item['expected_native_calls']:
            raise ValueError('native routing/dispatch accounting differs')
        if not row['valid_execution'] or not row['after_proof_matches'] or row['after_manifest_id']!=row['proof']['observed_manifest_id']:
            raise ValueError('native proof/coverage checks incomplete')
        proof=row['proof']
        if proof['proof_id']!=content_id({k:v for k,v in proof.items() if k!='proof_id'}):raise ValueError('native proof identity differs')
        if row['public_status']!=('passed' if item['label']['answer_is_correct'] else 'failed'):
            raise ValueError('native directional result differs from independent label')
    ref=a.read_json(root/'reconciliation/framework-reference-binding-v1.json')
    if not ref['complete'] or ref['native_attempts']!=0 or ref['confidence_generations']!=0:
        raise ValueError('reference construction/binding incomplete')
    return dict(version='verified_framework_completion_v1',source_main=review['source_main'],
        original_publication_files=len(inventory),unchanged_original_files=len(inventory)-len(differences),
        canonical_whole_publication_unchanged=False,
        source_overlays=differences,frozen_publication_artifacts_unchanged=True,resource_fingerprint_pins_unchanged=True,
        singleton_transfer_id=review['singleton_transfer_id'],native_requests=6,native_calls_started=8,native_calls_completed=8,
        confidence_generations=0,retries=0,reference_construction_binding=True,
        fresh_reference_inference=False,api_deployment_validated=False)


if __name__=='__main__':print(json.dumps(audit_delivery(),indent=2))
