"""Read-only development diagnosis. Never dispatch, fit, calibrate or evaluate final."""
import hashlib
import json
import math
from pathlib import Path
import runpy
import sys
from collections import Counter
from unittest.mock import patch

D=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(D.parents[1]))
runpy.run_path(str(D/'fit_approved.py'),run_name='diagnostic_import')
from app.game.artifacts import PolicyArtifact
from app.game.models import canonical_json, content_id
from app.game.research.specification import PolicyBuildSpecification
from app.game.offline.evaluation import construct_payoffs
from app.game.finalization import finalize_decision
from app.decision.vote_normalization import vote_confidence, signed_mass


def forbidden(*args, **kwargs):
    raise AssertionError('No optimization, calibration or final evaluation in diagnosis')

with patch('app.game.solver.linprog',side_effect=forbidden), patch('app.game.offline.calibration.calibrate',side_effect=forbidden), patch('app.game.offline.evaluation.evaluate_final_test',side_effect=forbidden), patch('app.game.offline.evaluation.evaluate_reserved_final',side_effect=forbidden):
    originals=[D/'approval.json',D/'approved-policy-input.json',D/'calibration.json',D/'collection/recordings.json',D/'proposed/fitting-proposal.UNAPPROVED.json',*sorted((D/'fitted-policy').glob('*.json'))]
    hashes={str(p.relative_to(D)):hashlib.sha256(p.read_bytes()).hexdigest() for p in originals}
    approved=json.loads((D/'approved-policy-input.json').read_text())
    approval=json.loads((D/'approval.json').read_text())
    assert content_id(approved)==approval['approved_configuration_digest']
    assert canonical_json(approved)==canonical_json(json.loads((D/'proposed/fitting-proposal.UNAPPROVED.json').read_text())['policy_build_specification'])
    spec=PolicyBuildSpecification.model_validate(approved)
    artifact=PolicyArtifact.model_validate_json((D/'fitted-policy/policy.json').read_text())
    result=construct_payoffs(spec.context,spec.manifest,spec.contract,spec.attacks)
    assert result.matrix==artifact.policy.matrix
    examples={e.example_id:e for p in spec.manifest.partitions if p.role=='development' for e in p.examples}
    traces=[]
    clean_id=result.matrix.attack_ids[0]
    for strategy in artifact.policy.strategies:
        for out in result.outcomes:
            if out.strategy_id!=strategy.strategy_id or out.attack_id!=clean_id: continue
            e=examples[out.example_id]
            rows=[a.report for a in e.attempts if a.verifier_name in strategy.verifiers and a.report is not None]
            states=tuple((n,next(a.state for a in e.attempts if a.verifier_name==n)) for n in strategy.verifiers)
            f=finalize_decision(spec.context,strategy,spec.contract,rows,states,e.validation_id)
            assert canonical_json(f.detail.to_dict())==out.decision_json
            detail=f.detail.to_dict()
            normalized=[dict(report=r.model_dump(),confidence=vote_confidence(r),signed_mass=signed_mass(r)) for r in rows]
            if strategy.aggregation=='reputation_weighted':
                numerator=math.fsum(v.weight*signed_mass(next(r for r in rows if r.verifier_name==v.verifier_name)) for v in f.detail.votes)
                denominator=math.fsum(abs(v.weight) for v in f.detail.votes)
                assert math.isclose(numerator/denominator,f.detail.raw_score,abs_tol=1e-12)
            else:
                numerator=math.fsum(g.contribution for g in f.detail.groups)
                denominator=math.fsum(g.influence for g in f.detail.groups)
                assert math.isclose(numerator/denominator,f.detail.raw_score,abs_tol=1e-12)
                for g in f.detail.groups:
                    members=[v for v in f.detail.votes if v.verifier_name in g.active_members]
                    inner_numerator=math.fsum(v.reliability_strength*v.normalized_strength for v in members)
                    inner_denominator=math.fsum(v.reliability_strength for v in members)
                    assert math.isclose(inner_numerator/inner_denominator,g.score,abs_tol=1e-12)
                    next(x for x in detail['groups'] if x['group_id']==g.group_id).update(numerator=inner_numerator,denominator=inner_denominator)
            traces.append(dict(example=e.model_dump(exclude={'attempts'}),aggregation=strategy.aggregation,raw_and_normalized=normalized,detail=detail,numerator=numerator,denominator=denominator,public_outcome=out.model_dump()))
    metrics=[]
    for sid,aid,m in result.metrics:
        strategy=next(s for s in artifact.policy.strategies if s.strategy_id==sid)
        metrics.append(dict(aggregation=strategy.aggregation,attack_id=aid,metrics=m.__dict__,validation_loss=m.validation_loss(spec.context.loss_configuration)))
    summary=dict(configuration_digest=content_id(approved),original_hashes=hashes,context=spec.context.model_dump(),execution_contract=spec.contract.model_dump(),probabilities=artifact.policy.solution.probabilities,metrics=metrics,clean_reason_counts={s.aggregation:dict(Counter(r for t in traces if t['aggregation']==s.aggregation for r in t['public_outcome']['reasons'])) for s in artifact.policy.strategies},traces=traces,originals_preserved=True,semantics_changed=False)
    assert all(hashlib.sha256(p.read_bytes()).hexdigest()==hashes[str(p.relative_to(D))] for p in originals)
    (D/'investigation/traces.json').write_text(json.dumps(summary,indent=2,default=str)+'\n',encoding='utf-8')
    print(json.dumps(dict(traces=len(traces),reason_counts=summary['clean_reason_counts'],metrics=metrics),indent=2,default=str))
