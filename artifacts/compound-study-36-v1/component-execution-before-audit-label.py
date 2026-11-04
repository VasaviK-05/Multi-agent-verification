"""Versioned complete-team composition of existing atomic decision contracts.

Atomic history supplies constituent decision weights, never compound payoffs.
The production entry point requires a separately fitted compound policy. The
explicit diagnostic entry point cannot be registered as an atomic policy.
"""
from dataclasses import dataclass
from itertools import product
import math
from time import perf_counter
from typing import Literal

from pydantic import Field, StrictFloat, model_validator, model_serializer
from app.game.dependencies import FrozenModel, identifier
from app.game.models import PlanningContext, Strategy, PayoffMatrix, SolverResult, content_id
from app.game.execution_contract import ExecutionContract
from app.game.resource_provenance import ResourceManifest
from app.game.strategies import enumerate_strategies
from app.game.component_binding import (VERSION, question_plan, bind_answer,
    component_validation_id, BindingError)


class Obligation(FrozenModel):
    component_id: Literal['base_fact', 'derived_sum']
    context: PlanningContext
    contract: ExecutionContract

    @model_validator(mode='after')
    def check(self):
        requirement = 'direct_fact' if self.component_id == 'base_fact' else 'arithmetic'
        if self.context.plan.requirements.requirements != (requirement,) or self.context.plan.requirements.unsupported:
            raise ValueError('component context must bind exactly its declared check')
        if (self.contract.contributor_version != 'informative_history_influence_v1'
            or self.contract.team_requirements is None
            or self.contract.resource_manifest is None
            or self.context.execution_contract_json is None
            or ExecutionContract.model_validate_json(self.context.execution_contract_json) != self.contract):
            raise ValueError('component requires bound informative, resource-checked execution semantics')
        self.contract.resource_manifest.require_candidates(c.verifier_name for c in self.context.plan.candidates)
        return self


class ComponentContract(FrozenModel):
    version: Literal['component_complete_team_v1'] = 'component_complete_team_v1'
    binding_version: Literal['fact_plus_sum_binding_v1','fact_plus_sum_binding_v2'] = VERSION
    descriptor_catalog_json: str | None = None
    component_assignments: tuple[tuple[str,tuple[str,...]],...] | None = None
    actual_resources: ResourceManifest | None = None
    category: Literal['area', 'population','numeric_fact']
    question_signature: tuple[str, str, float, bool]
    obligations: tuple[Obligation, ...]
    budget: StrictFloat = Field(ge=0)
    minimum_selected: int = Field(default=1, ge=1, le=4, strict=True)
    minimum_distinct_contributors: int = Field(default=1, ge=1, le=4, strict=True)
    # A contributor is an influential verifier identity, NOT an independent path.
    contributor_semantics: Literal['distinct_influential_verifier_union_v1'] = 'distinct_influential_verifier_union_v1'
    decision_semantics: Literal['all_required_pass_any_qualified_reject_v1'] = 'all_required_pass_any_qualified_reject_v1'

    @model_serializer(mode='wrap')
    def serialize_contract(self,handler):
        data=handler(self)
        if self.descriptor_catalog_json is None:data.pop('descriptor_catalog_json',None)
        if self.component_assignments is None:data.pop('component_assignments',None)
        if self.actual_resources is None:data.pop('actual_resources',None)
        return data

    @model_validator(mode='after')
    def check(self):
        if self.binding_version=='fact_plus_sum_binding_v2':
            from app.game.component_sources import Catalog
            from app.game.models import canonical_json
            catalog=Catalog.model_validate_json(self.descriptor_catalog_json or '{}')
            object.__setattr__(self,'descriptor_catalog_json',canonical_json(catalog.model_dump(mode='json')))
            if self.category!='numeric_fact':raise ValueError('V2 uses explicitly pooled numeric-fact requirements')
            if self.component_assignments!=(('base_fact',('evidence',)),('derived_sum',('rule',))):
                raise ValueError('V2 study authorizes Evidence fact and Rule arithmetic assignments only')
            if self.actual_resources is None:raise ValueError('V2 must bind the full actual resource observation')
            for obligation in self.obligations:
                scoped=obligation.contract.resource_manifest
                scoped.require_candidates(('evidence','rule'))
                for entry in scoped.verifiers:self.actual_resources.require_observation(entry)
        elif self.descriptor_catalog_json is not None or self.category=='numeric_fact' or self.component_assignments is not None or self.actual_resources is not None:
            raise ValueError('V1 cannot authorize V2 descriptors')
        if tuple(o.component_id for o in self.obligations) != ('base_fact', 'derived_sum'):
            raise ValueError('complete ordered obligations required')
        first, second = self.obligations
        if (first.context.dependencies != second.context.dependencies
            or first.contract.resource_manifest != second.contract.resource_manifest
            or first.context.cost_units != second.context.cost_units
            or first.context.plan.domain != second.context.plan.domain):
            raise ValueError('component resource, domain, dependency and cost units must agree')
        return self

    @property
    def compatibility_id(self):
        return content_id(self.model_dump(mode='json'))


class ComponentStrategy(FrozenModel):
    version: Literal['component_strategy_v1'] = 'component_strategy_v1'
    contract_id: str
    components: tuple[tuple[str, Strategy], ...]

    @property
    def strategy_id(self):
        return content_id(self.model_dump(mode='json'))

    @property
    def verifiers(self):
        return tuple(sorted({n for _, s in self.components for n in s.verifiers}))

    @property
    def estimated_cost(self):
        return math.fsum(s.estimated_cost for _, s in self.components)


def enumerate_component_strategies(contract):
    contract = ComponentContract.model_validate(contract)
    result = []
    for choices in product(*(enumerate_strategies(o.context).strategies for o in contract.obligations)):
        if contract.component_assignments is not None and any(s.verifiers!=names for s,(_,names) in zip(choices,contract.component_assignments)):
            continue
        # One aggregation rule for the whole planned team; never average components.
        if len({s.aggregation for s in choices}) != 1:
            continue
        strategy = ComponentStrategy(contract_id=contract.compatibility_id,
            components=tuple((o.component_id, s) for o, s in zip(contract.obligations, choices)))
        if (contract.minimum_selected <= len(strategy.verifiers) <= 4
            and strategy.estimated_cost <= contract.budget):
            result.append(strategy)
    return tuple(result)


class JointDevelopmentBinding(FrozenModel):
    """Deployment provenance from a separately reviewed joint development study.

    Like atomic task/history bindings, this is a frozen provenance declaration,
    not a proof that labels are correct. The offline study must validate/seal its
    source manifests before exporting it. Atomic provenance is not this type.
    """
    version: Literal['joint_component_development_v1'] = 'joint_component_development_v1'
    binding_version: Literal['fact_plus_sum_binding_v1','fact_plus_sum_binding_v2'] = VERSION
    contract_id: str = Field(pattern=r'^[0-9a-f]{64}$')
    matrix_id: str = Field(pattern=r'^[0-9a-f]{64}$')
    history_dataset_id: str
    development_dataset_id: str
    final_test_reservation_id: str
    history_manifest_sha256: str = Field(pattern=r'^[0-9a-f]{64}$')
    development_manifest_sha256: str = Field(pattern=r'^[0-9a-f]{64}$')
    grouped_partition_sha256: str = Field(pattern=r'^[0-9a-f]{64}$')
    label_protocol_id: str
    attack_specification_id: str
    collection_protocol: Literal['complete_bound_component_calls_v1'] = 'complete_bound_component_calls_v1'

    @model_validator(mode='after')
    def check(self):
        ids=(self.history_dataset_id,self.development_dataset_id,self.final_test_reservation_id)
        if len(set(ids))!=3:
            raise ValueError('joint history, development and reserved test must be distinct')
        for value in (*ids,self.label_protocol_id,self.attack_specification_id):
            identifier(value)
        return self

    @property
    def binding_id(self):
        return content_id(self.model_dump(mode='json'))


class ComponentPolicy(FrozenModel):
    """Joint compound game, not a product of independently sampled atomic policies.

    Generic minimax certificates are reused. No atomic recording-to-compound
    payoff conversion is provided. Empirical collection/fitting is a later study.
    """
    version: Literal['component_game_policy_v1'] = 'component_game_policy_v1'
    contract: ComponentContract
    matrix: PayoffMatrix
    solution: SolverResult
    evidence_kind: Literal['synthetic_test_fixture', 'empirical']
    # Explicit joint recording/partition provenance; a pointer alone is not validation.
    joint_evidence_id: str
    joint_development: JointDevelopmentBinding | None = None

    @model_validator(mode='after')
    def check(self):
        from app.game.solver import validate_solution
        strategies = enumerate_component_strategies(self.contract)
        if (self.matrix.compatibility_id != self.contract.compatibility_id
            or self.matrix.strategy_ids != tuple(s.strategy_id for s in strategies)
            or self.matrix.strategy_definitions or self.matrix.reliability_first):
            raise ValueError('compound matrix must bind the complete joint strategy axis and contract')
        if self.matrix.clean_coverage is not None:
            from app.game.models import PayoffMatrix
            coverage=self.matrix.clean_coverage
            parent=PayoffMatrix(**{**self.matrix.model_dump(),'clean_coverage':None})
            if (self.contract.binding_version!='fact_plus_sum_binding_v2' or coverage.minimum!=.9
                or coverage.parent_matrix_id!=parent.matrix_id):
                raise ValueError('V2 coverage must bind unchanged parent payoffs and fixed90% target')
        if not self.joint_evidence_id.strip():
            raise ValueError('explicit joint evidence provenance required')
        if self.evidence_kind=='empirical':
            binding=self.joint_development
            if (binding is None or binding.contract_id!=self.contract.compatibility_id
                or binding.matrix_id!=self.matrix.matrix_id or binding.binding_id!=self.joint_evidence_id):
                raise ValueError('empirical policy requires exact separately sealed joint development provenance')
            if binding.binding_version!=self.contract.binding_version:
                raise ValueError('joint development binding protocol differs')
            if self.contract.binding_version=='fact_plus_sum_binding_v2' and self.matrix.clean_coverage is None:
                raise ValueError('empirical V2 policy requires clean development coverage certificate')
        elif self.joint_development is not None:
            raise ValueError('synthetic fixtures cannot carry empirical joint development provenance')
        validate_solution(self.matrix, self.solution)
        return self

    @property
    def policy_id(self):
        return content_id(self.model_dump(mode='json'))


@dataclass(frozen=True)
class ComponentRun:
    public_status: str
    summary: dict


def unavailable(reason):
    code, _, explanation=reason.partition(': ')
    return ComponentRun('uncertain', dict(public_status='uncertain', selection_status=code,
        selection_reasons=[explanation or reason],
        attempts=[], components=[], termination='before_dispatch'))


def _snapshot_resources(observer, selector):
    # Compatible with upstream's active-instance attestation interface. Exact
    # manifest equality remains required; no implicit relocation authorization.
    snapshot_for=getattr(observer,'snapshot_for',None)
    return snapshot_for(selector) if snapshot_for is not None else observer.snapshot()


def bind_contract(contract,question,answer,reference):
    from app.game.question_routing import classify_question
    if contract.binding_version=='fact_plus_sum_binding_v2':
        from app.game.component_sources import Catalog,question_plan as v2_plan,validation_id
        catalog=Catalog.model_validate_json(contract.descriptor_catalog_json)
        plan=v2_plan(question,catalog)
        signature=classify_question(question,reference,component_catalog=catalog)[1]
        identity=validation_id
    else:
        plan=question_plan(question)
        signature=classify_question(question,reference)[1]
        identity=component_validation_id
        if plan.measure!=contract.category:raise BindingError('incompatible_policy: component category differs')
    if signature!=contract.question_signature:raise BindingError('incompatible_policy: question signature differs')
    return plan,bind_answer(plan,answer),identity


def scoped_component_selector(selector,contract):
    """Plan only assigned V2 identities; retain the original actual-resource observer.

    Lazy forwarding does not construct or run an unused verifier. Costs/history
    are needed only for the two assigned names, not unrelated factory entries.
    """
    if contract.binding_version!='fact_plus_sum_binding_v2':return selector
    from copy import copy
    from app.verifiers.base_verifier import BaseVerifier
    scoped=copy(selector)
    names=('evidence','rule')
    if selector._injected is not None:
        scoped._injected=[v for v in selector._injected if v.name in names]
    else:
        class Forward(BaseVerifier):
            def __init__(self,name):self._name=name
            @property
            def name(self):return self._name
            def verify(self,*args,**kwargs):return selector.resolve(self._name).verify(*args,**kwargs)
        scoped._injected=[Forward(n) for n in names]
    scoped._capabilities={n:c for n,c in selector._capabilities.items() if n in names}
    return scoped


def run_component_policy(policy, selector, question, answer, reference, validation_id, *,
                         rng, resource_observer, allow_synthetic_for_tests=False):
    """Production gate. Existing Policy/PolicyArtifact objects are rejected."""
    try:
        policy = ComponentPolicy.model_validate(policy)
        bind_contract(policy.contract,question,answer,reference)
    except BindingError as exc:
        return unavailable(str(exc))
    except ValueError as exc:
        return unavailable('incompatible_policy: ' + str(exc))
    if policy.evidence_kind != 'empirical' and not allow_synthetic_for_tests:
        return unavailable('incompatible_policy: synthetic fixtures require explicit test permission')
    draw = rng.random()
    if not math.isfinite(draw) or not 0 <= draw < 1:
        raise ValueError('rng must return a finite value in [0,1)')
    cumulative = 0.
    total = math.fsum(p for _,p in policy.solution.probabilities)
    selected = None
    for sid, probability in policy.solution.probabilities:
        cumulative += probability / total
        if draw < cumulative:
            selected = sid
            break
    if selected is None:
        selected=next(sid for sid,p in reversed(policy.solution.probabilities) if p>0)
    strategies = enumerate_component_strategies(policy.contract)
    strategy = next(s for s in strategies if s.strategy_id == selected)
    result = run_component_diagnostic(policy.contract, strategy, selector, question, answer,
        reference, validation_id, resource_observer=resource_observer)
    result.summary.update(policy_id=policy.policy_id, evidence_kind=policy.evidence_kind,
        execution_mode='synthetic_policy_test' if policy.evidence_kind=='synthetic_test_fixture' else 'component_policy',
        joint_evidence_id=policy.joint_evidence_id)
    return result


def run_component_diagnostic(contract, strategy, selector, question, answer, reference,
                             validation_id, *, resource_observer):
    """Explicit diagnostic harness. Does not fit, register or authorize a policy."""
    from app.analysis.capability_probe_analyzer import CapabilityProbeAnalyzer
    from app.game.frozen_planning import frozen_selector
    from app.game.models import capture_context
    from app.game.resource_provenance import ResourceManifest
    from app.game.finalization import finalize_decision, informative_contributor_count
    from app.game.execution import VerifierExecutionFailure
    from app.selection.models import VerifierUnavailable
    from app.decision.report_identity import canonical_reports
    from app.decision.vote_normalization import is_abstention
    try:
        contract = ComponentContract.model_validate(contract)
        strategy = ComponentStrategy.model_validate(strategy)
        plan,bound,identity = bind_contract(contract,question,answer,reference)
        if strategy not in enumerate_component_strategies(contract):
            return unavailable('incompatible_policy: plan or joint strategy differs')
        ids = tuple(identity(validation_id,b) for b in bound)
        # Freeze and validate all planning inputs BEFORE any selected call.
        selectors = []
        scope=scoped_component_selector(selector,contract)
        for obligation, component in zip(contract.obligations, bound):
            frozen = frozen_selector(scope, obligation.context)
            config = obligation.context.model_dump(exclude={'selection_json', 'analyzer_provenance'})
            if contract.binding_version=='fact_plus_sum_binding_v2':
                from app.game.component_sources import component_analysis
                analysis=component_analysis(component)
            else:analysis=CapabilityProbeAnalyzer().analyze(component.question)
            current = capture_context(frozen, analysis,
                context=reference, **config)
            if current.compatibility_id != obligation.context.compatibility_id:
                return unavailable('incompatible_policy: component planning inputs differ')
            selectors.append(frozen)
        expected = contract.actual_resources or contract.obligations[0].contract.resource_manifest
        if resource_observer is None or ResourceManifest.model_validate(_snapshot_resources(resource_observer,selector)) != expected:
            return unavailable('resource_incompatible: pre-dispatch observation differs')
    except ValueError as exc:
        return unavailable(str(exc))
    attempts, components, contributors = [], [], set()
    resource_drift = False
    for obligation, (_, atomic), component, cid, frozen in zip(
            contract.obligations, strategy.components, bound, ids, selectors):
        rows, states = [], []
        for name in atomic.verifiers:
            start = perf_counter()
            event = dict(component_id=component.component_id, verifier_name=name,
                validation_id=cid, binding_id=component.binding_id,
                call_id=content_id([cid, name]), question=component.question, answer=component.answer,
                estimated_cost=dict(obligation.context.attempt_costs)[name])
            try:
                raw = frozen.resolve(name).verify(component.question, component.answer, reference)
            except (VerifierUnavailable, VerifierExecutionFailure) as exc:
                state = 'unavailable' if isinstance(exc, VerifierUnavailable) else 'failed'
                event['error'] = str(exc)
            else:
                checked, _, _ = canonical_reports([raw], team=(name,), validation_id=cid, deduplicate=False)
                row = checked[0]
                for key, value in (('component_id', component.component_id), ('binding_id', component.binding_id)):
                    if key in (row.metadata or {}) and row.metadata[key] != value:
                        raise ValueError('report component/binding identity differs from planned call')
                row.metadata = {**(row.metadata or {}), 'validation_id': cid,
                    'component_id': component.component_id, 'binding_id': component.binding_id}
                rows.append(row)
                event['report'] = row.model_dump(mode='json')
                state = 'abstention' if is_abstention(row) else 'directional'
            event.update(state=state, elapsed_ms=(perf_counter()-start)*1000)
            attempts.append(event)
            states.append((name, state))
        decision, influential=finalize_component(obligation,atomic,component,rows,states,cid)
        contributors.update(influential)
        components.append(decision)
    try:
        resource_drift = ResourceManifest.model_validate(_snapshot_resources(resource_observer,selector)) != expected
    except ValueError:
        resource_drift = True
    status,reasons=join_components(contract,components,contributors,resource_drift=resource_drift)
    return ComponentRun(status, dict(public_status=status, execution_mode='diagnostic_no_policy',
        selection_status='diagnostic', contract_id=contract.compatibility_id,
        selected_strategy_id=strategy.strategy_id, plan_id=plan.plan_id,
        team=list(strategy.verifiers), attempts=attempts, components=components,
        contributors=sorted(contributors), contributor_count=len(contributors),
        dependency_assumptions=contract.obligations[0].context.dependencies.model_dump(mode='json'),
        estimated_selected_cost=strategy.estimated_cost,
        estimated_attempted_cost=math.fsum(a['estimated_cost'] for a in attempts),
        override_reasons=reasons, termination='complete_selected_team', early_stopping_enabled=False))


def finalize_component(obligation,atomic,component,rows,states,cid):
    """Shared pure finalization for runtime and genuine joint recorded payoffs."""
    from app.game.finalization import finalize_decision,informative_contributor_count
    decision=finalize_decision(obligation.context,atomic,obligation.contract,rows,states,cid)
    contributors={row.verifier_name for row in rows if informative_contributor_count(
        obligation.context,decision.detail,[row],atomic.aggregation)}
    return dict(component_id=component.component_id,validation_id=cid,
        binding_id=component.binding_id,depends_on=list(component.depends_on),
        public_status=decision.public_status,required=list(decision.required),achieved=list(decision.achieved),
        unresolved=list(decision.unresolved),reasons=list(decision.reasons),
        detail=decision.detail.to_dict(),states=list(states)),contributors


def join_components(contract,components,contributors,*,resource_drift=False):
    if tuple(c['component_id'] for c in components)!=tuple(o.component_id for o in contract.obligations):
        raise ValueError('complete ordered component decisions required')
    # A qualified rejection cannot be outvoted by another component's support.
    statuses = [c['public_status'] for c in components]
    status = 'failed' if 'failed' in statuses else ('passed' if all(s == 'passed' for s in statuses) else 'uncertain')
    reasons = []
    if len(contributors) < contract.minimum_distinct_contributors:
        reasons.append('minimum_distinct_contributors')
    if any(o.contract.failure_contract == 'all_selected_returned' and
           any(state in {'failed', 'unavailable'} for _, state in c['states'])
           for o, c in zip(contract.obligations, components)):
        reasons.append('selected_execution_incomplete')
    if resource_drift:
        reasons.append('resource_provenance_changed_during_execution')
    if reasons:
        status = 'uncertain'
    return status,reasons
