"""Analytical zero-payoff synthetic fixtures. No fitting/LP or native calls.

The matrix is identically zero, so every simplex distribution is minimax with a
zero primal/dual gap. Hand-selected test distributions exercise execution only;
they are never empirical policies or scientific certification.
"""
import hashlib
import json
from types import SimpleNamespace
from collections import Counter
from app.game.category_runtime import CategoryInputContract, ReviewedCategory, CategoryBinding, CategoryGameRuntime
from app.game.category_applicability import CategoryApplicability
from app.game.consistency_assessment import ConsistencyAssessmentContract
from app.game.artifacts import PolicyArtifact
from app.game.execution_contract import ExecutionContract, TeamRequirements
from app.game.models import (capture_context, canonical_json, content_id, LossConfiguration,
    PayoffProvenance, PlanningContext, PayoffMatrix, SolverResult)
from app.game.dependencies import DependencyRegistry
from app.game.resource_provenance import ResourceManifest
from app.game.task_conditioning import TaskSnapshotBinding, analysis_task
from app.game.policy import Policy
from app.game.solver import solution_diagnostics, OPTIMALITY_BASIS
from app.game.strategies import enumerate_strategies
from app.selection.verifier_selector import VerifierSelector
from app.selection.capabilities import BUILTIN_CAPABILITIES
from app.reputation.reputation_manager import ReputationManager
from app.verifiers.base_verifier import BaseVerifier
from app.models.schemas import VerificationResult, ValidationRequest

NAMES = ('confidence','evidence','rule','semantic')


def output(name, passed=True):
    decision = 'SUPPORT' if passed else 'REJECT'
    if name=='rule':
        return VerificationResult(verifier_name=name, passed=passed, score=float(passed),
            metadata=dict(decision=decision, rule_kind='factual', rule='arithmetic_addition'))
    if name=='evidence':
        label='entailment' if passed else 'contradiction'
        return VerificationResult(verifier_name=name, passed=passed, score=.9,
            metadata=dict(decision=decision, nli_label=label, unsure_reason=None,
                supporting=[dict(nli_label=label, document='SYNTHETIC')] if passed else [],
                contradicting=[] if passed else [dict(nli_label=label, document='SYNTHETIC')],
                claim_decisions=[dict(decision=decision)]))
    if name=='semantic':
        from app.verifiers.semantic_verifier import SemanticVerifier
        return VerificationResult(verifier_name=name, passed=passed, score=.9,
            metadata=dict(decision=decision, comparison_method='answer_vs_context',
                compared_text='SYNTHETIC', model='SYNTHETIC', raw_similarity=.9,
                thresholds_calibrated=False, score_meaning=SemanticVerifier.SCORE_MEANING))
    label = 'support' if passed else 'reject'
    return VerificationResult(verifier_name=name, passed=passed, score=1., metadata=dict(
        decision=decision, method='self_consistency', judgment_source='self_consistency',
        n_samples=5, generator_model='SYNTHETIC-ONLY', temperature=.8,
        claim='SYNTHETIC claim', stable_answer=True, judgments=[label]*5,
        majority_label=label, agreement_count=5, total_judgments=5, judgment_counts={label:5},
        samples=[dict(sample='SYNTHETIC', label=label, method='string_match') for _ in range(5)]))


class Checker(BaseVerifier):
    def __init__(self, name):
        self._name, self.calls, self.behavior = name, [], output(name)
    @property
    def name(self):
        return self._name
    def verify(self, question, answer, context=None):
        self.calls.append((question, answer, context))
        if isinstance(self.behavior, Exception): raise self.behavior
        return self.behavior.model_copy(deep=True)


class RNG:
    def __init__(self, draw=.5): self.calls, self.draw = 0, draw
    def random(self): self.calls += 1; return self.draw


class Observer:
    def __init__(self, resources): self.resources, self.calls = resources, 0
    def snapshot_for(self, selector): self.calls += 1; return self.resources


def fixture(requirements=('arithmetic',), team=('rule',), aggregation='reputation_weighted',
            reference=False, minimum=1, informative=1, budget=4., neutral=False,
            assessment=False, pattern=None, build_runtime=True):
    scope = CategoryInputContract(name='SYNTHETIC-ONLY',
        question_pattern=pattern or (r'Paraphrase this reference: .+' if 'semantic_comparison' in requirements
            else r'What is the capital of [A-Za-z]+\?' if 'direct_fact' in requirements
            else r'What is \d+ \+ \d+\?'),
        maximum_question_chars=200, requirements=tuple(sorted(requirements)),
        reference_required=reference, answer_contract='SYNTHETIC; wrong candidates remain eligible',
        domain='general', domain_status='unknown', difficulty='easy', difficulty_score=.1)
    analysis=scope.analyze('Paraphrase this reference: Mira carried twelve parcels.' if 'semantic_comparison' in requirements
        else 'What is the capital of Bhutan?' if 'direct_fact' in requirements else 'What is 4 + 4?')
    pool=[Checker(name) for name in NAMES]
    manager=ReputationManager()
    # Explicit synthetic history for test-only informative contributors. Never
    # change live reputation, historical snapshots or production priors.
    if not neutral:
        for name in NAMES:
            for _ in range(4): manager.update_reputation(name,'general',True)
    selector=VerifierSelector(verifiers=pool, reputation_manager=manager,
        capabilities={name:BUILTIN_CAPABILITIES[name] for name in NAMES})
    resources=ResourceManifest(verifiers=tuple(dict(verifier_name=name, resources=[
        dict(kind=kind,resource_id=name+'-'+kind,sha256=hashlib.sha256(('SYNTHETIC:'+name+kind).encode()).hexdigest())
        for kind in sorted({'implementation','configuration'} | {
            'confidence':{'model','prompt','service'},'evidence':{'model','corpus','index'},
            'semantic':{'model'}}.get(name,set()))]) for name in NAMES))
    contract_data=dict(version='offline_public_decision_v5' if assessment else 'offline_public_decision_v4',
        coverage_version='game_assessment_output_v3' if assessment else 'task_output_contract_v2',
        contributor_version='informative_history_influence_v1',threshold=.55,
        failure_contract='all_selected_returned', execution_configuration_id=resources.manifest_id,
        history_prior_alpha=1.,history_prior_beta=1., resource_manifest=resources,
        team_requirements=TeamRequirements(minimum_selected=minimum,minimum_informative=informative))
    if assessment:
        contract_data['consistency_assessment']=ConsistencyAssessmentContract(n_samples=5,
            generator_model='SYNTHETIC-ONLY',temperature=.8)
    contract=ExecutionContract(**contract_data)
    context=capture_context(selector,analysis,context='SYNTHETIC reference' if reference else None,
        attempt_costs=tuple((name,1.) for name in NAMES),budget=float(budget),cost_units='synthetic_units',
        dependencies=DependencyRegistry(version='synthetic_dependencies_v1',unresolved=NAMES),
        loss_configuration=LossConfiguration(version='synthetic_loss_v1',false_accept=1.,false_reject=1.,
            uncertain=.2,resource_weight=0.,cost_units='synthetic_units'),
        aggregation_versions=(('reputation_weighted','log_odds_v1'),('dependency_group','groups_v1')),
        provenance=PayoffProvenance(attack_specification='SYNTHETIC',history_dataset='SYNTHETIC-history',
            development_dataset='SYNTHETIC-development',final_test_dataset='SYNTHETIC-test',
            matrix_version='SYNTHETIC-zero-game',loss_configuration='synthetic_loss_v1',
            category='general',evidence_kind='synthetic_test_fixture'),
        offline_evaluation_id='SYNTHETIC-TEST-ONLY',execution_contract_json=canonical_json(contract.model_dump(mode='json')))
    binding=TaskSnapshotBinding(identity=analysis_task(analysis),history_dataset_id='SYNTHETIC-history',
        history_partition_digest='a'*64)
    context=PlanningContext(**(context.model_dump() | dict(task_conditioning_json=binding.model_dump_json())))
    strategies=enumerate_strategies(context).strategies
    if not strategies: raise ValueError('SYNTHETIC no feasible strategy')
    selected=next(s for s in strategies if s.verifiers==team and s.aggregation==aggregation)
    matrix=PayoffMatrix(strategy_ids=tuple(s.strategy_id for s in strategies),strategy_definitions=strategies,
        attack_ids=('SYNTHETIC-clean',),values=tuple((0.,) for _ in strategies),compatibility_id=context.compatibility_id)
    probabilities=tuple(1. if s==selected else 0. for s in strategies)
    diagnostics=solution_diagnostics(matrix,probabilities,(1.,),1e-8)
    solution=SolverResult(status='optimal',message='SYNTHETIC analytical zero game; no LP/fitting',tolerance=1e-8,
        probabilities=tuple(zip(matrix.strategy_ids,probabilities)),attack_probabilities=(('SYNTHETIC-clean',1.),),
        matrix_id=matrix.matrix_id,optimality_basis=OPTIMALITY_BASIS,**diagnostics)
    policy=Policy(version='game_policy_informative_v1',compatibility_id=context.compatibility_id,
        provenance=context.provenance,matrix=matrix,solution=solution,strategies=strategies)
    artifact=PolicyArtifact(version='deployable_game_policy_informative_v1',policy=policy,context=context,
        contract=contract,execution_configuration_id=contract.execution_configuration_id,applicable_domain='general')
    reports={};digests={}
    for role in ('development','held_out','baseline'):
        raw=json.dumps(dict(version='category_evaluation_report_v2',role=role,
            artifact_id=artifact.artifact_id,input_contract_id=scope.contract_id,
            dataset_id='SYNTHETIC-'+role,strategy_ids=matrix.strategy_ids)).encode()
        digest=hashlib.sha256(raw).hexdigest();reports[digest]=raw;digests[role]=digest
    declaration=CategoryApplicability(artifact_id=artifact.artifact_id,task_id=analysis_task(analysis).task_id,
        supported_distribution='SYNTHETIC ONLY; NOT CERTIFIED',exclusions=('ALL empirical claims',),reviewed_by='TEST FIXTURE',
        development_report=digests['development'],held_out_report=digests['held_out'],baseline_report=digests['baseline'],
        evaluated_scenarios=('correct','incorrect','uncertain','unsupported','resource_unavailable'),
        evaluated_teams=tuple(sorted({s.verifiers for s in strategies})),
        semantic_contradictions=('numbers','negation','entities','relationships'))
    reviewed=ReviewedCategory(inputs=scope,declaration=declaration)
    observer,rng=Observer(resources),RNG()
    runtime=CategoryGameRuntime([CategoryBinding(reviewed,artifact)],reports=reports,rng=rng,
        resource_observer=observer,allow_synthetic_for_tests=True) if build_runtime else None
    question='Paraphrase this reference: Mira carried twelve parcels.' if 'semantic_comparison' in requirements else 'What is the capital of Bhutan?' if 'direct_fact' in requirements else 'What is 4 + 4?'
    request=ValidationRequest(question=question,answer='SYNTHETIC candidate',
        context='Mira carried twelve parcels.' if 'semantic_comparison' in requirements else 'SYNTHETIC reference' if reference else None)
    return SimpleNamespace(runtime=runtime,selector=selector,pool={p.name:p for p in pool},observer=observer,rng=rng,
        artifact=artifact,scope=scope,reports=reports,reviewed=reviewed,request=request,selected=selected)
