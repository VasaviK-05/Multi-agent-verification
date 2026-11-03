"""Fresh-history, development-only reference fitting; never reads reserved payloads."""
import hashlib,json,math
from pathlib import Path
from collections import Counter
from app.game.models import capture_context,PlanningContext,canonical_json
from app.game.execution_contract import ExecutionContract,TeamRequirements
from app.game.offline.collection import RecordingBundle,completeness,export_training
from app.game.offline.attacks import AttackSpecification,enumerate_attacks
from app.game.offline.evaluation import bind_evaluation,construct_payoffs,summarize,export_artifact
from app.game.offline.reliability import prepare_reliability_first
from app.game.task_conditioning import bind_task_history
from app.game.strategies import enumerate_strategies
from app.game.solver import solve_minimax
from app.game.policy import build_policy
from app.game.artifacts import PolicyArtifact
from app.selection.verifier_selector import VerifierSelector
from app.selection.capabilities import BUILTIN_CAPABILITIES
from app.reputation.reputation_manager import ReputationManager
from app.verifiers.base_verifier import BaseVerifier
ROOT=Path('artifacts/remaining-category-studies-v1/reference-current-v1')
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def save(p,v):
    if hasattr(v,'model_dump'):v=v.model_dump(mode='json')
    with Path(p).open('x',encoding='utf-8') as f:json.dump(v,f,indent=2,sort_keys=True)
class Handle(BaseVerifier):
    def __init__(self,name):self._name=name
    @property
    def name(self):return self._name
    def verify(self,*a,**kw):raise AssertionError('no inference during fitting')
def main():
    bundle=RecordingBundle.model_validate(read(ROOT/'training/reference/bundle.json'))
    assert completeness(bundle)['complete']
    for path,digest in read(ROOT/'seal.json').items():
        assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==digest
    protocol=read(ROOT/'protocol.json');names=tuple(c.verifier_name for c in bundle.request.candidates)
    costs=tuple((n,math.fsum(a.duration_ms for a in bundle.attempts if a.candidate==n and a.executed)/sum(a.candidate==n and a.executed for a in bundle.attempts)) for n in names)
    total=math.fsum(v for _,v in costs);manager=ReputationManager(prior_alpha=1.,prior_beta=1.)
    history={e.run_id:e for e in bundle.request.examples if e.role=='history'}
    for a in bundle.attempts:
        if a.run_id in history and a.attempt.state=='directional':
            e=history[a.run_id];manager.update_from_ground_truth(a.candidate,e.analysis.domain,a.attempt.report.passed,e.label.answer_is_correct)
    selector=VerifierSelector(verifiers=[Handle(n) for n in names],reputation_manager=manager,capabilities={n:BUILTIN_CAPABILITIES[n] for n in names})
    first=bundle.request.examples[0];resources=bundle.observed_setup.resources
    contract=ExecutionContract(version='offline_public_decision_v4',coverage_version='task_output_contract_v2',contributor_version='informative_history_influence_v1',
        threshold=.55,failure_contract='all_selected_returned',execution_configuration_id=resources.manifest_id,resource_manifest=resources,
        history_prior_alpha=1.,history_prior_beta=1.,team_requirements=TeamRequirements(minimum_selected=1,minimum_informative=1))
    attacks=AttackSpecification(**protocol['attacks'])
    context=capture_context(selector,first.analysis,context=first.reference,attempt_costs=costs,budget=total,cost_units='ms',
        execution_contract_json=canonical_json(contract.model_dump(mode='json')),
        loss_configuration=dict(version='reference-fresh-loss-v1',**protocol['losses'],resource_weight=.1/total,cost_units='ms'),
        dependencies=protocol['dependencies'],aggregation_versions=(('reputation_weighted','log_odds_v1'),('dependency_group','groups_v1')),
        provenance=dict(attack_specification=attacks.specification_id,history_dataset='reference-fresh-v1-history',development_dataset='reference-fresh-v1-development',
            final_test_dataset='reference-fresh-v1-final_test',matrix_version='reference-fresh-finalized-development-v1',loss_configuration='reference-fresh-loss-v1',category=first.analysis.domain,evidence_kind='empirical'))
    manifest=export_training(bundle,context);context=bind_task_history(context,manifest);context=bind_evaluation(context,manifest,contract,attacks)
    evaluation=construct_payoffs(context,manifest,contract,attacks)
    fitted,matrix=prepare_reliability_first(context,manifest,contract,attacks,evaluation,minimum=.9)
    solution=solve_minimax(matrix,tolerance=1e-8)
    output=ROOT/'fit';output.mkdir(exist_ok=False)
    for name,value in (('context',fitted),('contract',contract),('matrix',matrix),('solution',solution),('training-manifest',manifest),('development-evaluation',evaluation),('enumeration',enumerate_strategies(fitted))):save(output/(name+'.json'),value)
    actions=enumerate_attacks(context.dependencies,attacks);rows=[]
    for strategy in enumerate_strategies(fitted).strategies:
        cells={}
        for attack in actions:
            outcomes=[o for o in evaluation.outcomes if o.strategy_id==strategy.strategy_id and o.attack_id==attack.attack_id]
            m=summarize(tuple((o,1.) for o in outcomes),context.loss_configuration)
            cells[attack.kind]=dict(**m.model_dump(mode='json'),decision_loss=m.validation_loss(context.loss_configuration),reasons=dict(Counter(r for o in outcomes for r in o.reasons)))
        rows.append(dict(strategy=strategy.model_dump(mode='json'),attacks=cells))
    save(output/'strategy-diagnostics.json',rows)
    summary=dict(status=solution.status,minimum=.9,maximum_clean_coverage=max(r['attacks']['clean']['decision_coverage'] for r in rows),
        actual_training_attempts=sum(a.executed for a in bundle.attempts),attempt_states=dict(Counter(a.attempt.state for a in bundle.attempts)),
        costs=costs,budget=total,history_statistics=[s.__dict__ for s in context.plan.reputation_statistics],
        reserved_collected=False,deployable_policy=False,route='missing_policy',no_target_relaxation=True)
    if solution.status=='optimal':
        policy=build_policy(fitted,matrix,tolerance=1e-8)
        artifact=export_artifact(policy,fitted,manifest,contract,attacks,applicable_domain=fitted.plan.domain)
        save(output/'policy.json',artifact);assert PolicyArtifact.model_validate(read(output/'policy.json'))==artifact
        eligible=[r for r in rows if r['attacks']['clean']['decision_coverage']>=.9]
        best_loss=min(max(v['decision_loss'] for v in r['attacks'].values()) for r in eligible)
        fixed=min((r for r in eligible if max(v['decision_loss'] for v in r['attacks'].values())<=best_loss+1e-8),key=lambda r:(r['strategy']['estimated_cost'],r['strategy']['strategy_id']))
        greedy=next((s for s in policy.strategies if s.verifiers==tuple(sorted(context.plan.initial_selected)) and s.aggregation=='reputation_weighted'),None)
        if greedy is None:raise ValueError('existing greedy does not define a compatible complete-team strategy')
        files=[p for p in Path('app').rglob('*.py')]+[Path(__file__),Path('scripts/transition_reference_current.py'),Path('scripts/reference_current_reserved.py'),Path('scripts/collect_reference_current_reserved.py')]
        freeze=dict(policy_id=policy.policy_id,artifact_id=artifact.artifact_id,best_fixed_strategy_id=fixed['strategy']['strategy_id'],
            greedy_strategy=greedy.model_dump(mode='json'),greedy_scope='Existing coverage-aware initial_selected, full team finalized under matching contract; no adaptive early stopping.',
            training_manifest_id=manifest.manifest_id,source_hashes={str(p.resolve()):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
            reservation=manifest.final_test_reservation.model_dump(mode='json'),protocol=protocol)
        from app.game.models import content_id
        save(output/'freeze.json',freeze);summary.update(deployable_policy=True,freeze_id=content_id(freeze),route='explicit opt-in only')
    else:save(output/'infeasible.json',dict(reason='No strategy mixture meets unchanged90% clean development coverage under genuine contributor/capability semantics.',solution=solution.model_dump(mode='json'),reserved_evaluation='correctly skipped; no test inference authorized for an infeasible candidate'))
    save(output/'summary.json',summary);print(json.dumps(summary),flush=True)
if __name__=='__main__':main()
