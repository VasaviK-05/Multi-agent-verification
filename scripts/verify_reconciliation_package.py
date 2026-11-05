"""Verify portable software/policy identities without external resources/services."""
import json
from pathlib import Path
from app.benchmark import project_adapter as a
from app.game.models import content_id
from app.game.offline.reconciled_resources import check_dependencies, CAPSULE_ID
from app.game.offline.policy_source_compatibility import check_capsule
from scripts.reconciliation import load_bundle, BUNDLE_SHA256


def verify():
    configuration,provider,compound=load_bundle()
    capsule=a.read_json(a.ROOT/'docs/policy-source-capsule-v2.json')
    check_capsule(capsule,a.ROOT,policy_id=compound.policy_id,observed_manifest_id=capsule['observed_manifest_id'])
    check_dependencies()
    reference=a.read_json(a.ROOT/'reconciliation/reference-source.json')
    from app.game.offline.reference_compatibility import CAPSULE_ID as REFERENCE_CAPSULE
    assert reference['capsule_id']==REFERENCE_CAPSULE
    assert content_id({k:v for k,v in reference.items() if k!='capsule_id'})==REFERENCE_CAPSULE
    shared=['app/verifiers/base_verifier.py','app/models/schemas.py','app/benchmark/project_adapter.py']
    files=dict(semantic=['app/verifiers/semantic_verifier.py','app/verifiers/claim_generator.py','app/verifiers/confidence_verifier.py'],
        evidence=['app/verifiers/evidence_verifier.py','app/verifiers/evidence_retriever.py','app/verifiers/claim_generator.py'],
        rule=['app/verifiers/rule_verifier.py'],confidence=['app/verifiers/confidence_verifier.py','app/verifiers/self_consistency.py',
        'app/verifiers/evidence_verifier.py','app/verifiers/claim_generator.py'])
    for name,paths in files.items():
        assert content_id([(p,reference['old_files'][p]) for p in shared+paths])==reference['transitions'][name]['old']
        assert content_id([(p,a.file_digest(a.ROOT/p)) for p in shared+paths])==reference['transitions'][name]['new']
    result=dict(version='reconciliation_package_identity_verification_v1',bundle_sha256=BUNDLE_SHA256,
        bundle_id=a.read_json(a.ROOT/'reconciliation/policies.json')['bundle_id'],
        compound=dict(policy_id=compound.policy_id,contract_id=compound.contract.compatibility_id,
            obligations=[dict(component_id=o.component_id,context_id=o.context.compatibility_id,
                contract_content_id=content_id(o.contract.model_dump(mode='json'))) for o in compound.contract.obligations]),
        atomic=[dict(artifact_id=v.artifact_id,policy_id=v.policy.policy_id,matrix_id=v.policy.matrix.matrix_id,
            context_id=v.context.compatibility_id,contract_content_id=content_id(v.contract.model_dump(mode='json')),
            historical_manifest_id=v.contract.resource_manifest.manifest_id) for v in provider.snapshot()],
        er_source_capsule_id=CAPSULE_ID,reference_source_capsule_id=REFERENCE_CAPSULE,
        deployment_active_metadata=False,activation_enforced_by_loader=False,
        native_attempts=0,confidence_generations=0,models_constructed=0,service_requests=0)
    return result


if __name__=='__main__':print(json.dumps(verify(),indent=2))
