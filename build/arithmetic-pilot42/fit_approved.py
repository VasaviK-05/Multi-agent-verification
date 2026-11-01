"""Fit the exact user-approved pilot specification; never read held-out payloads."""
import hashlib
import importlib.abc
import json
from pathlib import Path
import random
import sys
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[2]
DIRECTORY=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
CUSTODY=(DIRECTORY/'custody').resolve()

def audit(event,args):
    if event=='open' and isinstance(args[0],str):
        path=Path(args[0]).resolve()
        if path==CUSTODY or CUSTODY in path.parents:
            raise AssertionError('reserved final-test payload access forbidden')
    if event=='socket.connect':
        raise AssertionError('network access forbidden during offline fitting')
sys.addaudithook(audit)

class NoProductionImports(importlib.abc.MetaPathFinder):
    def find_spec(self,fullname,path=None,target=None):
        if fullname=='database' or fullname.startswith(('app.api','app.database','app.orchestration')):
            raise AssertionError('DB/API/orchestration import forbidden: '+fullname)
sys.meta_path.insert(0,NoProductionImports())

from app.game.models import content_id, canonical_json, capture_context
from app.game.artifacts import PolicyArtifact, InMemoryPolicyProvider, DeploymentEpisode
from app.game.execution import GameRuntime
from app.game.frozen_planning import frozen_selector
from app.game.policy import validate_policy, sample_policy
from app.game.solver import validate_solution
from app.game.offline.collection import RecordingBundle
from app.game.offline.calibration import CalibrationArtifact
from app.game.research.specification import PolicyBuildSpecification
from app.game.offline import build as builder, evaluation
from app.selection.verifier_selector import VerifierSelector
from app.selection.capabilities import BUILTIN_CAPABILITIES
from app.verifiers.base_verifier import BaseVerifier


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def persist_exact(path,payload):
    if path.exists():
        if canonical_json(json.loads(path.read_text(encoding='utf-8'))) != canonical_json(payload):
            raise ValueError('existing immutable output differs: '+str(path))
    else:
        with path.open('x',encoding='utf-8') as handle:
            json.dump(payload,handle,sort_keys=True,indent=2,allow_nan=False)


def forbidden(*args,**kwargs):
    raise AssertionError('recalibration or final evaluation forbidden')


def main():
    proposal_path=DIRECTORY/'proposed/fitting-proposal.UNAPPROVED.json'
    calibration_path=DIRECTORY/'calibration.json'
    recordings_path=DIRECTORY/'collection/recordings.json'
    original_hashes={str(p.relative_to(DIRECTORY)):digest(p)
                     for p in (proposal_path,calibration_path,recordings_path)}
    proposal=json.loads(proposal_path.read_text(encoding='utf-8'))
    payload=proposal['policy_build_specification']
    spec=PolicyBuildSpecification.model_validate(payload)
    configuration_digest=content_id(payload)
    assert spec.specification_id==configuration_digest
    assert canonical_json(payload)==canonical_json(spec.model_dump(mode='json'))
    calibration=CalibrationArtifact.model_validate_json(calibration_path.read_text(encoding='utf-8'))
    assert calibration.calibration_id==proposal['calibration_id']
    assert dict(spec.context.attempt_costs)=={r['verifier_name']:r['attempt_cost'] for r in calibration.result['estimates']}
    assert spec.context.budget==proposal['proposed_values']['budget_ms']
    assert spec.context.loss_configuration.resource_weight==proposal['proposed_values']['resource_weight_per_ms']
    assert spec.context.offline_evaluation_id is not None
    approval=dict(version='arithmetic_pilot_configuration_approval_v1',
        approval_date_local='2026-10-26',timezone='Asia/Calcutta',
        authorization_source='Explicit human user message in this chat',
        authorization='I approve the complete configuration in fitting-proposal.UNAPPROVED.json for this arithmetic engineering pilot only.',
        scope='Constructed, reference-assisted arithmetic engineering pilot only; history/development fitting; no final evaluation.',
        approved_configuration_digest=configuration_digest,digest_algorithm='SHA-256 of existing canonical_json UTF-8',
        original_proposal_sha256=original_hashes[str(proposal_path.relative_to(DIRECTORY))],
        original_proposal_canonical_digest=content_id(proposal),
        original_configuration_version=spec.configuration_version,
        configuration_version_preserved=True,settings_changed=False,
        original_recordings_sha256=original_hashes[str(recordings_path.relative_to(DIRECTORY))],
        calibration_id=calibration.calibration_id,
        calibration_sha256=original_hashes[str(calibration_path.relative_to(DIRECTORY))],
        recalibration_authorized=False,final_payload_access_authorized=False,final_evaluation_authorized=False)
    persist_exact(DIRECTORY/'approval.json',approval)
    # Preserve even the original version label; authorization is separate audit
    # metadata, so the approved scientific configuration digest remains identical.
    input_path=DIRECTORY/'approved-policy-input.json'
    persist_exact(input_path,payload)
    assert content_id(json.loads(input_path.read_text(encoding='utf-8')))==configuration_digest
    with patch('app.game.offline.calibration.calibrate',side_effect=forbidden), \
         patch('app.game.offline.calibration.apply_calibration',side_effect=forbidden), \
         patch.object(evaluation,'evaluate_final_test',side_effect=forbidden), \
         patch.object(evaluation,'evaluate_reserved_final',side_effect=forbidden):
        status=builder.main([str(input_path),'--output-dir',str(DIRECTORY/'fitted-policy')])
        if status:
            raise RuntimeError('approved builder returned '+str(status))
        artifact_path=DIRECTORY/'fitted-policy/policy.json'
        artifact=PolicyArtifact.model_validate_json(artifact_path.read_text(encoding='utf-8'))
        assert artifact.context==spec.context and artifact.contract==spec.contract
        validate_policy(artifact.policy,artifact.context)
        validate_solution(artifact.policy.matrix,artifact.policy.solution)
        provider=InMemoryPolicyProvider((artifact,))
        registered,=provider.snapshot()
        episode=DeploymentEpisode(episode_id='approved-arithmetic-pilot42-offline-check',
            context=registered.context,contract=registered.contract,
            execution_configuration_id=registered.execution_configuration_id)
        runtime=GameRuntime(provider,episode,random.Random(42))
        assert runtime.allow_synthetic_for_tests is False
        bundle=RecordingBundle.model_validate_json(recordings_path.read_text(encoding='utf-8'))
        class RecordedHandle(BaseVerifier):
            def __init__(self,name): self._name=name
            @property
            def name(self): return self._name
            def verify(self,*args,**kwargs): raise AssertionError('new verifier execution forbidden')
        plan=artifact.context.plan
        selector=VerifierSelector(verifiers=[RecordedHandle(c.verifier_name) for c in plan.candidates],
            capabilities={c.verifier_name:BUILTIN_CAPABILITIES[c.verifier_name] for c in plan.candidates},
            lambda_cost=plan.lambda_cost,lambda_latency=plan.lambda_latency,
            lambda_suitability=plan.lambda_suitability,type_mapping=dict(plan.type_mapping),
            verifier_profiles={c.verifier_name:dict(cost=c.cost,latency=c.latency) for c in plan.candidates},
            difficulty_range={band:(plan.minimum_count,plan.target_count) for band in ('easy','medium','hard')})
        frozen=frozen_selector(selector,artifact.context)
        first=bundle.request.examples[0]
        config=artifact.context.model_dump()
        config.pop('selection_json')
        config.pop('analyzer_provenance')
        captured=capture_context(frozen,first.analysis,context=first.reference,**config)
        assert captured.compatibility_id==artifact.context.compatibility_id
        selection=sample_policy(registered.policy,captured,rng=random.Random(42))
        assert selection.policy_id==artifact.policy.policy_id
        # Replay development only to audit per-row equivalence and separate metrics.
        evaluated=evaluation.construct_payoffs(artifact.context,spec.manifest,spec.contract,spec.attacks)
        assert evaluated.matrix==artifact.policy.matrix
        row_metrics=[]
        for strategy_id,attack_id,metrics in evaluated.metrics:
            row_metrics.append(dict(strategy_id=strategy_id,attack_id=attack_id,
                validation_loss=metrics.validation_loss(artifact.context.loss_configuration),
                cost_inclusive_objective=metrics.mean_loss,decision_coverage=metrics.decision_coverage,
                uncertainty_rate=metrics.uncertainty_rate,expected_estimated_cost_ms=metrics.estimated_resource_cost))
        actions=evaluation.enumerate_attacks(artifact.context.dependencies,spec.attacks)
        rows=artifact.policy.matrix.values
        differences=[abs(a-b) for a,b in zip(rows[0],rows[1])]
        max_difference=max(differences)
        report=json.loads((DIRECTORY/'fitted-policy/build-report.json').read_text(encoding='utf-8'))
        assert report['build_metadata']['input_digest']==configuration_digest
        for relative,before in original_hashes.items():
            assert digest(DIRECTORY/relative)==before
        audit_report=dict(status='complete',approval_record='approval.json',
            approval_record_sha256=digest(DIRECTORY/'approval.json'),
            approved_configuration_digest=configuration_digest,builder_input_digest=report['build_metadata']['input_digest'],
            configuration_unchanged=True,original_files_sha256=original_hashes,
            calibration_reused_unchanged=True,calibration_id=calibration.calibration_id,recalibrated=False,
            artifact_id=artifact.artifact_id,policy_id=artifact.policy.policy_id,
            matrix_id=artifact.policy.matrix.matrix_id,reputation_snapshot_id=artifact.context.reputation_snapshot_id,
            provider_reload_verified=True,episode_and_runtime_constructed=True,
            runtime_frozen_planning_compatible=True,policy_draw_verified=True,
            runtime_verifiers_executed=False,final_payload_access_guard='passed',
            final_evaluation_guard='passed',no_recalibration_guard='passed',
            db_api_import_guard='passed',network_access_guard='passed',
            strategy_probabilities=[dict(**s.model_dump(mode='json'),probability=dict(artifact.policy.solution.probabilities)[s.strategy_id])
                                    for s in artifact.policy.strategies],
            attack_definitions=[dict(attack_id=a.attack_id,**a.model_dump(mode='json')) for a in actions],
            per_strategy_development_metrics=row_metrics,
            payoff_equivalence=dict(exactly_equal=rows[0]==rows[1],absolute_tolerance=1e-12,
                relative_tolerance=0.,maximum_absolute_difference=max_difference,equivalent=max_difference<=1e-12),
            development=report['scientific_outputs']['development'],certificate=report['scientific_outputs']['certificate'],
            limitations=['Minimum two participants and two-candidate roster permit one team with two aggregation choices.',
                'This pilot cannot demonstrate adaptive team selection or cost optimization.',
                'Semantic supported all 80 collected candidates, including 40 incorrect answers.',
                'Results apply only to this constructed, reference-assisted arithmetic engineering pilot.',
                'Equivalent payoffs do not establish aggregation superiority; solver allocation is not scientific evidence.',
                'Development results only; no held-out evaluation or improvement claim.'])
        persist_exact(DIRECTORY/'fitted-policy/approval-and-validation.json',audit_report)
        print(json.dumps(dict(artifact_id=artifact.artifact_id,configuration_digest=configuration_digest,
            probabilities=audit_report['strategy_probabilities'],payoff_equivalence=audit_report['payoff_equivalence'],
            development=audit_report['development']),indent=2))


if __name__=='__main__': main()
