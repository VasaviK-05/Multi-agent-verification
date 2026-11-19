"""Opt-in reuse of an unchanged fitted policy across compatible question instances.

A scope is installation metadata, not a new task identity or a performance
certificate. Question/answer instance IDs never enter the fitted policy's key.
Historical exact routes are still protected by ExactFirstCategoryDispatcher.
"""
from typing import Literal
import re
from pydantic import Field, model_validator
from app.game.dependencies import FrozenModel
from app.game.category_runtime import CategoryGameRuntime


class ReusablePolicyScope(FrozenModel):
    version: Literal['reusable_policy_scope_v1'] = 'reusable_policy_scope_v1'
    artifact_id: str = Field(pattern=r'^[0-9a-f]{64}$')
    compatibility_id: str = Field(pattern=r'^[0-9a-f]{64}$')
    question_pattern: str = Field(min_length=1, max_length=2000)
    maximum_question_chars: int = Field(gt=0, le=10000)
    question_rules_version: str = Field(min_length=1)
    review_basis: str = Field(min_length=1)
    # Scope approval authorizes compatibility-based execution. Independent
    # population performance beyond the old evaluation is not inferred from it.
    evaluation_status: Literal['historical_evaluation_unchanged'] = 'historical_evaluation_unchanged'

    @model_validator(mode='after')
    def check(self):
        re.compile(self.question_pattern)
        return self

    @property
    def scope_id(self):
        from app.game.models import content_id
        return content_id(self.model_dump(mode='json'))

    def matches(self, question):
        return (isinstance(question,str) and len(question)<=self.maximum_question_chars
            and re.fullmatch(self.question_pattern,question) is not None)


class ReusablePolicyGameRuntime(CategoryGameRuntime):
    """Reuse fitted mixtures, never a greedy fallback or per-question fitter.

    Server configuration supplies immutable scopes/artifacts and actual resource
    observation. Full GameRuntime recapture remains authoritative for candidate,
    requirement, reputation, dependency, budget, execution and resource identity.
    This deliberately does not demand exact surface difficulty-score equality:
    GameRuntime rejects changes whenever they alter the real planning contract.
    """
    def __init__(self, artifacts, scopes, *, rng, resource_observer,
                 allow_synthetic_for_tests=False):
        from app.game.artifacts import PolicyArtifact, DeploymentEpisode, InMemoryPolicyProvider
        from app.game.task_conditioning import TaskSnapshotBinding
        from app.analysis.task_analyzer import RULE_VERSION
        from app.analysis.capability_probe_analyzer import VERSION as PROBE_VERSION
        from app.analysis.reference_study_analyzer import VERSION as REFERENCE_VERSION
        if type(allow_synthetic_for_tests) is not bool:
            raise TypeError('test-only permission must be an explicit boolean')
        captured=tuple(PolicyArtifact.model_validate(a) for a in artifacts)
        scopes=tuple(ReusablePolicyScope.model_validate(s) for s in scopes)
        by_id={a.artifact_id:a for a in captured}
        if not captured or len(by_id)!=len(captured) or {s.artifact_id for s in scopes}!=set(by_id):
            raise ValueError('explicit scope required for each distinct fitted artifact')
        if len(scopes)!=len(captured):
            raise ValueError('one unambiguous scope per fitted artifact')
        entries=[]
        for scope in scopes:
            artifact=by_id[scope.artifact_id]
            if scope.compatibility_id!=artifact.context.compatibility_id:
                raise ValueError('scope differs from frozen policy compatibility contract')
            if artifact.policy.provenance.evidence_kind!='empirical' and not allow_synthetic_for_tests:
                raise ValueError('synthetic policies require explicit test-only permission')
            if (artifact.contract.version not in {'offline_public_decision_v4','offline_public_decision_v5'}
                    or artifact.contract.resource_manifest is None):
                raise ValueError('reuse requires task-aware, resource-bound policy')
            identity=TaskSnapshotBinding.model_validate_json(artifact.context.task_conditioning_json or '{}').identity
            if (scope.question_rules_version!=identity.question_rules_version
                    or scope.question_rules_version not in {RULE_VERSION,PROBE_VERSION,REFERENCE_VERSION}):
                raise ValueError('no unchanged supported analyzer for this fitted task identity')
            episode=DeploymentEpisode(episode_id='reuse-v1-'+artifact.artifact_id,
                context=artifact.context,contract=artifact.contract,
                execution_configuration_id=artifact.execution_configuration_id)
            entries.append((scope,artifact,identity,episode))
        self._entries=tuple(entries)
        self._provider=InMemoryPolicyProvider(captured)
        self._rng,self._observer=rng,resource_observer
        self._allow_synthetic_for_tests=allow_synthetic_for_tests

    def resolve(self, question, reference=None):
        from app.game.component_execution import unavailable
        from app.game.question_routing import classify_question
        from app.game.task_conditioning import analysis_task
        from app.analysis.reference_study_analyzer import VERSION as REFERENCE_VERSION
        from app.verifiers.confidence_verifier import parse_judgment_list
        candidates=[e for e in self._entries if e[0].matches(question)]
        matched=[]; reasons=[]
        for scope,artifact,identity,episode in candidates:
            try:
                kind,_,analysis=classify_question(question,reference,
                    reference_question_version=REFERENCE_VERSION if scope.question_rules_version==REFERENCE_VERSION else None)
                if kind!='atomic' or analysis_task(analysis)!=identity:
                    reasons.append('requirements/analyzer task differs from fitted policy'); continue
                if bool(reference and reference.strip())!=artifact.context.plan.reference_available:
                    reasons.append('reference presence differs from fitted policy');continue
                if parse_judgment_list(reference) is not None:
                    reasons.append('judgment-label context is outside native scope');continue
                if 'semantic_comparison' in identity.requirements and question.startswith('Paraphrase this reference: '):
                    if reference!=question.partition(': ')[2]:
                        reasons.append('comparison reference differs from question source');continue
                if 'arithmetic' in identity.requirements:
                    from app.verifiers.rule_verifier import ARITHMETIC_PATTERNS, WORD_ARITHMETIC_PATTERNS
                    patterns=tuple(ARITHMETIC_PATTERNS)+tuple(p for _,p in WORD_ARITHMETIC_PATTERNS)
                    if not any(p.fullmatch(question.strip()) for p in patterns):
                        reasons.append('no implemented arithmetic parser pattern');continue
            except ValueError as exc:
                reasons.append(str(exc));continue
            matched.append((scope,artifact,episode,analysis))
        if len(matched)!=1:
            reason='ambiguous compatible scopes' if len(matched)>1 else '; '.join(reasons) or 'no declared compatible task scope'
            return None, unavailable('policy_scope_incompatible: '+reason)
        return matched[0], None

    def run(self, selector, analysis, request, validation_id, *, execution_journal=None):
        from app.game.execution import GameRuntime
        resolved,failed=self.resolve(request.question,request.context)
        if resolved is None:return failed
        scope,artifact,episode,current_analysis=resolved
        result=GameRuntime(self._provider,episode,self._rng,
            allow_synthetic_for_tests=self._allow_synthetic_for_tests,
            resource_observer=self._observer).run(selector,current_analysis,request,validation_id,
                execution_journal=execution_journal)
        result.summary.update(category_runtime_version='reusable_policy_runtime_v1',
            reusable_policy_scope_id=scope.scope_id,
            applicability_evaluation_status=scope.evaluation_status,
            question_instance_changes_policy=False,
            fitted_compatibility_id=artifact.context.compatibility_id,
            fitted_policy_version=artifact.policy.version,
            fitted_strategy_probabilities=list(artifact.policy.solution.probabilities))
        return result
