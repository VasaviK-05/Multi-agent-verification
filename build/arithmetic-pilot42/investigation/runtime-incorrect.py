"""Read-only fitted-artifact and historical-runtime-replay checks; no new inference."""
import json
import math
from pathlib import Path
import random
import runpy
import sys
from unittest.mock import patch

DIRECTORY=Path(__file__).resolve().parents[1]
ROOT=DIRECTORY.parents[1]
sys.path.insert(0,str(ROOT))
# Install the same final-custody, network and production-import guards without
# rerunning approval creation or fitting.
runpy.run_path(str(DIRECTORY/'fit_approved.py'),run_name='validation_import')

from app.game.artifacts import PolicyArtifact, InMemoryPolicyProvider, DeploymentEpisode
from app.game.execution import GameRuntime
from app.game.models import PlanningContext, canonical_json, content_id
from app.game.offline.collection import RecordingBundle, export_training
from app.game.offline import evaluation
from app.game.research.specification import PolicyBuildSpecification
from app.game.resource_provenance import ResourceManifest
from app.models.schemas import ValidationRequest
from app.selection.verifier_selector import VerifierSelector
from app.selection.capabilities import BUILTIN_CAPABILITIES
from app.verifiers.base_verifier import BaseVerifier

def forbidden(*a,**kw): raise AssertionError('verification may not fit/recalibrate/score final')

with patch('app.game.solver.linprog',side_effect=forbidden), \
     patch('app.game.offline.calibration.calibrate',side_effect=forbidden), \
     patch('app.game.offline.calibration.apply_calibration',side_effect=forbidden), \
     patch.object(evaluation,'evaluate_final_test',side_effect=forbidden), \
     patch.object(evaluation,'evaluate_reserved_final',side_effect=forbidden):
    proposal=json.loads((DIRECTORY/'proposed/fitting-proposal.UNAPPROVED.json').read_text())
    approved=json.loads((DIRECTORY/'approved-policy-input.json').read_text())
    approval=json.loads((DIRECTORY/'approval.json').read_text())
    assert canonical_json(approved)==canonical_json(proposal['policy_build_specification'])
    assert content_id(approved)==approval['approved_configuration_digest']
    spec=PolicyBuildSpecification.model_validate(approved)
    bundle=RecordingBundle.model_validate_json((DIRECTORY/'collection/recordings.json').read_text())
    assert bundle.bundle_id==proposal['source_bundle_id']
    unbound=PlanningContext(**{**spec.context.model_dump(),'offline_evaluation_id':None})
    assert export_training(bundle,unbound)==spec.manifest
    artifact=PolicyArtifact.model_validate_json((DIRECTORY/'fitted-policy/policy.json').read_text())
    evaluated=evaluation.construct_payoffs(spec.context,spec.manifest,spec.contract,spec.attacks)
    assert evaluated.matrix==artifact.policy.matrix
    reasons=[]
    for strategy in artifact.policy.strategies:
        for attack_id in artifact.policy.matrix.attack_ids:
            rows=[o for o in evaluated.outcomes if o.strategy_id==strategy.strategy_id and o.attack_id==attack_id]
            counts={reason:sum(reason in o.reasons for o in rows) for reason in sorted({r for o in rows for r in o.reasons})}
            reasons.append(dict(strategy_id=strategy.strategy_id,attack_id=attack_id,examples=len(rows),reason_counts=counts))
    e=next(x for x in bundle.request.examples if x.role=='development' and not x.label.answer_is_correct)
    collected={a.candidate:a for a in bundle.attempts if a.run_id==e.run_id}
    class ReplayHandle(BaseVerifier):
        def __init__(self,name): self._name=name; self.calls=0
        @property
        def name(self): return self._name
        def verify(self,question,answer,context=None):
            assert (question,answer,context)==(e.question,e.answer,e.reference)
            self.calls+=1
            return collected[self.name].attempt.report.model_copy(deep=True)
    class RecordedSnapshots:
        def __init__(self): self.calls=0
        def snapshot(self):
            field='observed_resources_json' if self.calls==0 else 'after_resources_json'
            self.calls+=1
            payloads=[json.loads(getattr(a.attempt,field) if field=='observed_resources_json' else getattr(a,field))
                      for a in collected.values()]
            return ResourceManifest(verifiers=tuple(payloads))
    plan=artifact.context.plan
    handles=[ReplayHandle(c.verifier_name) for c in plan.candidates]
    selector=VerifierSelector(verifiers=handles,capabilities={c.verifier_name:BUILTIN_CAPABILITIES[c.verifier_name] for c in plan.candidates},
        lambda_cost=plan.lambda_cost,lambda_latency=plan.lambda_latency,lambda_suitability=plan.lambda_suitability,
        type_mapping=dict(plan.type_mapping),
        verifier_profiles={c.verifier_name:dict(cost=c.cost,latency=c.latency) for c in plan.candidates},
        difficulty_range={band:(plan.minimum_count,plan.target_count) for band in ('easy','medium','hard')})
    provider=InMemoryPolicyProvider((artifact,))
    episode=DeploymentEpisode(episode_id='historical-recording-runtime-parity',context=artifact.context,
        contract=artifact.contract,execution_configuration_id=artifact.execution_configuration_id)
    observer=RecordedSnapshots()
    runtime=GameRuntime(provider,episode,random.Random(42),resource_observer=observer)
    run=runtime.run(selector,e.analysis,ValidationRequest(question=e.question,answer=e.answer,context=e.reference),e.run_id)
    assert run.summary['selection_status']=='selected'
    selected=run.summary['selected_strategy_id']
    reference=next(o for o in evaluated.outcomes if o.example_id==e.example_id and o.strategy_id==selected
                   and o.attack_id==artifact.policy.matrix.attack_ids[0])
    assert run.public_status==reference.public_status
    assert canonical_json(run.detail.to_dict())==reference.decision_json
    assert observer.calls==2 and sum(h.calls for h in handles)==2
    for _,_,m in evaluated.metrics:
        assert math.isclose(m.mean_loss,m.validation_loss(artifact.context.loss_configuration)+
                            artifact.context.loss_configuration.resource_weight*m.estimated_resource_cost,rel_tol=0.,abs_tol=1e-12)
    records=[x for x in bundle.request.examples]
    semantic=[a for a in bundle.attempts if a.candidate=='semantic']
    lookup={x.run_id:x for x in records}
    assert len(semantic)==80 and all(a.attempt.report.metadata['decision']=='SUPPORT' for a in semantic)
    assert sum(not lookup[a.run_id].label.answer_is_correct for a in semantic)==40
    result=dict(status='passed',approved_configuration_digest=approval['approved_configuration_digest'],
        source_bundle_and_manifest_match=True,certificate_reloaded_by_artifact=True,
        historical_runtime_replay_matches_offline_replay=True,
        recorded_reports_replayed=2,new_verifier_inference_calls=0,
        runtime_resource_snapshots='Actual retained pre/post observations replayed for compatibility only; no new live resource claim.',
        final_payload_guard='passed',no_optimizer_guard='passed',no_recalibration_guard='passed',
        semantic_supports=80,semantic_incorrect_answers_supported=40,per_strategy_replay_reasons=reasons)
    with (DIRECTORY/'investigation/runtime-incorrect.json').open('x',encoding='utf-8') as handle:
        json.dump(result,handle,indent=2)
    print(json.dumps({k:v for k,v in result.items() if k!='per_strategy_replay_reasons'},indent=2))
