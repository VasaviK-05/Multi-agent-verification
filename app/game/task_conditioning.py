"""Additive task-isolated history snapshots and label-free episode routing."""
from dataclasses import asdict
from typing import Literal
from pydantic import Field
from app.game.dependencies import FrozenModel
from app.selection.requirements import requirement_inputs

class TaskIdentity(FrozenModel):
    version: Literal['domain_requirements_task_v1']='domain_requirements_task_v1'
    subject_domain: str
    domain_status: str
    requirements: tuple[str,...]
    question_rules_version: str

    @property
    def task_id(self):
        from app.game.models import content_id
        return content_id(self.model_dump(mode='json'))

def analysis_task(analysis):
    requirements=requirement_inputs(analysis)
    if requirements.status!='known' or requirements.unsupported:
        raise ValueError('task routing requires supported known question requirements')
    return TaskIdentity(subject_domain=analysis.domain,domain_status=analysis.domain_status,
        requirements=tuple(sorted(requirements.requirements)),question_rules_version=analysis.research_context.scoring_version)

def context_task(context):
    plan=context.plan
    if plan.requirements.status!='known' or plan.requirements.unsupported:
        raise ValueError('task binding requires known supported requirements')
    return TaskIdentity(subject_domain=plan.domain,domain_status=plan.domain_status,
        requirements=tuple(sorted(plan.requirements.requirements)),question_rules_version=plan.scoring_version)

class TaskSnapshotBinding(FrozenModel):
    version: Literal['task_isolated_history_v1']='task_isolated_history_v1'
    identity: TaskIdentity
    history_dataset_id: str
    history_partition_digest: str = Field(pattern=r'^[0-9a-f]{64}$')
    sparse_history: Literal['isolated_beta_prior_no_pooling']='isolated_beta_prior_no_pooling'

def bind_task_history(context,manifest):
    from app.game.models import PlanningContext, canonical_json, content_id
    from app.game.offline.replay import category_id
    if context.pooling_contract_json is not None:raise ValueError('task-isolated history cannot be pooled')
    history=manifest.partition('history')
    if any(e.planning_category!=category_id(context) for p in manifest.partitions for e in p.examples):
        raise ValueError('cross-task or incompatible planning recordings')
    binding=TaskSnapshotBinding(identity=context_task(context),history_dataset_id=history.dataset_id,
        history_partition_digest=content_id(history.model_dump(mode='json')))
    return PlanningContext(**{**context.model_dump(),'task_conditioning_json':canonical_json(binding.model_dump(mode='json'))})

def validate_task_history(context,manifest):
    from app.game.models import content_id
    from app.game.offline.replay import category_id
    if context.task_conditioning_json is None:return
    binding=TaskSnapshotBinding.model_validate_json(context.task_conditioning_json)
    history=manifest.partition('history')
    if (binding.identity!=context_task(context) or binding.history_dataset_id!=history.dataset_id
        or binding.history_partition_digest!=content_id(history.model_dump(mode='json'))
        or any(e.planning_category!=category_id(context) for p in manifest.partitions for e in p.examples)):
        raise ValueError('task-conditioned history or planning identity mismatch')

def analysis_signature(analysis,reference):
    return (analysis_task(analysis).task_id,analysis.difficulty,analysis.difficulty_score,bool(reference and reference.strip()))

class TaskPolicyRouter:
    """Caller supplies approved primary episodes and explicit infeasibility records.

    Snapshot statistics remain keyed by subject domain inside the old decision
    interface, but each immutable episode has a separate task/history binding.
    No fallback to another task's general-domain history is allowed.
    """
    def __init__(self,routes):
        # (question-derived signature, budget, primary, episode-or-None, reason)
        self.routes=tuple(routes)
        keys=[(signature,budget) for signature,budget,primary,episode,reason in self.routes]
        if len(keys)!=len(set(keys)):raise ValueError('duplicate task/budget route')
        for signature,budget,primary,episode,reason in self.routes:
            if episode is not None:
                binding=TaskSnapshotBinding.model_validate_json(episode.context.task_conditioning_json or '{}')
                plan=episode.context.plan
                if (signature!=(binding.identity.task_id,plan.difficulty,plan.difficulty_score,plan.reference_available)
                    or episode.context.budget!=budget):
                    raise ValueError('route differs from bound task/budget')
    def run(self,selector,analysis,request,validation_id,*,provider,rng,resource_observer,budget=None,allow_synthetic_for_tests=False):
        from app.game.execution import GameRuntime, GameRun
        from app.decision.decision_engine import DecisionDetail
        def failed(code,reason):
            return GameRun((),DecisionDetail(analysis.domain,'unknown',0.,0.,.55,'unknown',()),'uncertain',
                dict(selection_status=code,selection_reasons=[reason],public_status='uncertain'))
        try:signature=analysis_signature(analysis,request.context)
        except ValueError as exc:return failed('task_unknown',str(exc))
        if ('semantic_comparison' in analysis_task(analysis).requirements
            and request.question.strip().casefold().startswith('paraphrase this reference: ')
            and request.context!=request.question.strip().partition(': ')[2]):
            return failed('task_reference_mismatch','comparison reference differs from the question source')
        matching=[r for r in self.routes if r[0]==signature and (r[2] if budget is None else r[1]==budget)]
        if len(matching)!=1:return failed('task_out_of_scope','no unique explicit task/context/budget route')
        _,_,_,episode,reason=matching[0]
        if episode is None:return failed('task_infeasible',reason)
        result=GameRuntime(provider,episode,rng,allow_synthetic_for_tests=allow_synthetic_for_tests,resource_observer=resource_observer).run(selector,analysis,request,validation_id)
        result.summary.update(task_id=signature[0],task_route='domain_requirements_task_v1')
        return result
