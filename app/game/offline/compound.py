"""Grouped empirical compound producer; never promotes diagnostics to training.

The existing collector, timing/resource checks, atomic history semantics, attack
adapters, component finalization and minimax certificates are reused verbatim.
"""
from decimal import Decimal, localcontext
import json
from pathlib import Path
from typing import Literal
from pydantic import Field, model_validator, model_serializer
from app.game.dependencies import FrozenModel, DependencyRegistry
from app.game.models import content_id, canonical_json, capture_context, LossConfiguration, PayoffMatrix
from app.game.component_sources import SourceManifest, VERSION, question_plan, bind_answer, validation_id,component_analysis
from app.game.component_execution import (ComponentContract, Obligation, ComponentPolicy,
    JointDevelopmentBinding, enumerate_component_strategies, finalize_component, join_components)
from app.game.offline.collection import (RecordingRequest, PreparationExample, HeldoutExample,
    HeldoutRecordingRequest, Candidate, IndependentLabel, RecordingBundle, collect, completeness)
from app.game.offline.records import ReservedExample, FinalTestReservation
from app.game.offline.calibration import MeasurementSetup
from app.game.offline.attacks import AttackSpecification, enumerate_attacks, transform
from app.game.execution_contract import ExecutionContract, TeamRequirements
from app.selection.capabilities import BUILTIN_CAPABILITIES


class SourceCapacityError(ValueError):pass


class PartitionSizes(FrozenModel):
    version: Literal['original_48_v1','amended_36_v1']
    history: int = Field(strict=True,ge=1)
    development: int = Field(strict=True,ge=1)
    final_test: int = Field(strict=True,ge=1)

    @model_validator(mode='after')
    def check(self):
        expected=16 if self.version=='original_48_v1' else 12
        if (self.history,self.development,self.final_test)!=(expected,)*3:
            raise ValueError('partition sizes differ from the explicitly versioned design')
        return self

    @property
    def total(self):return self.history+self.development+self.final_test


class Group(FrozenModel):
    source_id: str
    measure: Literal['area','population']
    role: Literal['history','development','final_test']
    increment: str


class Study(FrozenModel):
    version: Literal['grouped_compound_study_v2','grouped_compound_study_v3']='grouped_compound_study_v2'
    partition_sizes: PartitionSizes | None = None
    sources: SourceManifest
    groups: tuple[Group,...]
    loss: LossConfiguration
    dependencies: DependencyRegistry
    threshold: float = .55
    coverage_minimum: float = .9
    prior_alpha: float = 1.
    prior_beta: float = 1.
    budget_rule: Literal['sum_component_mean_history_development_attempt_ms_v1']='sum_component_mean_history_development_attempt_ms_v1'
    objective: Literal['worst_validation_then_equal_plan_cost_v1']='worst_validation_then_equal_plan_cost_v1'
    history_rule: Literal['first_directional_per_component_bound_input_v2']='first_directional_per_component_bound_input_v2'
    attack_specification: AttackSpecification
    authorization: str
    excluded_entities: tuple[str,...]=('BH','BE')
    source_files: tuple[tuple[str,str],...]=()

    @model_serializer(mode='wrap')
    def serialize_study(self,handler):
        data=handler(self)
        if self.partition_sizes is None:data.pop('partition_sizes',None)
        return data

    @property
    def sizes(self):
        return self.partition_sizes or PartitionSizes(version='original_48_v1',history=16,development=16,final_test=16)

    @model_validator(mode='after')
    def check(self):
        amended=self.partition_sizes is not None and self.partition_sizes.version=='amended_36_v1'
        if amended!=(self.version=='grouped_compound_study_v3'):
            raise ValueError('amended design requires its distinct study version')
        if self.sources.evidence_kind=='empirical':
            from app.game.component_sources import validate_source_material
            validate_source_material(self.sources,self.source_files)
        if (len(self.groups)!=self.sizes.total or any(sum(g.role==role for g in self.groups)!=getattr(self.sizes,role)
            for role in ('history','development','final_test'))):
            raise ValueError(f'study requires exactly{self.sizes.total} entity groups and{self.sizes.history} in each partition')
        ids=[g.source_id for g in self.groups]
        if len(set(ids))!=self.sizes.total or set(ids)&set(self.excluded_entities):
            raise ValueError('entity leakage, duplicate entity or explored-entity overlap')
        facts={(f.descriptor.source_id,f.descriptor.measure):f for f in self.sources.facts}
        entities=[];component_inputs={}
        for g in self.groups:
            if (g.source_id,g.measure) not in facts:raise ValueError('group lacks independently established source')
            fact=facts[g.source_id,g.measure];entities.append(fact.descriptor.entity.casefold())
            plan=question_plan(question(fact,g.increment),self.sources.catalog)
            for _,base,derived in answer_variants(fact.value,g.increment):
                for bound in bind_answer(plan,canonical_json(dict(base=format(base,'f'),derived=format(derived,'f')))):
                    key=(bound.component_id,bound.question)
                    if key in component_inputs and component_inputs[key]!=g.role:
                        raise ValueError('component input leakage across partitions; related checks must stay grouped')
                    component_inputs[key]=g.role
        if len(set(entities))!=self.sizes.total:raise ValueError('entity aliases cannot cross partitions')
        if (self.threshold!=.55 or self.coverage_minimum!=.9 or self.prior_alpha!=1. or self.prior_beta!=1.
            or self.loss.cost_units!='ms' or not self.authorization.strip()):
            raise ValueError('fixed study threshold/coverage/prior/units/authorization differs')
        return self

    @property
    def study_id(self):return content_id(self.model_dump(mode='json'))


def question(fact,increment):
    d=fact.descriptor;unit=' square kilometres' if d.measure=='area' else ''
    return f'What is the {d.measure} of {d.entity}, and what is that {d.measure} plus {increment}{unit}? Give both values.'


def answer_variants(value,increment):
    with localcontext() as ctx:
        ctx.prec=50;base=Decimal(value);inc=Decimal(increment)
        return (('correct',base,base+inc),('wrong_math',base,base+inc-1),
            ('wrong_base',base+1,base+1+inc),('both_wrong',base+1,base+inc))


def prepare(sources,loss,dependencies,authorization,*,excluded_entities=('BH','BE'),source_files=(),partition_sizes=None):
    sources=SourceManifest.model_validate(sources)
    # Commit source ordering before outcomes. Never create extra groups from measures/increments.
    available={}
    for f in sorted(sources.facts,key=lambda f:(f.descriptor.source_id,f.descriptor.measure)):
        if f.descriptor.source_id not in excluded_entities:available.setdefault(f.descriptor.source_id,f)
    sizes=PartitionSizes.model_validate(partition_sizes) if partition_sizes is not None else PartitionSizes(version='original_48_v1',history=16,development=16,final_test=16)
    if len(available)<sizes.total:
        raise SourceCapacityError(f'requires{sizes.total} independent entity groups; available={len(available)} after exclusions; no partition or inference authorized')
    chosen=sorted(available.values(),key=lambda f:content_id(['compound-study-v2',f.descriptor.source_id]))[:sizes.total]
    roles=('history','development','final_test')
    groups=tuple(Group(source_id=f.descriptor.source_id,measure=f.descriptor.measure,
        role=roles[0] if i<sizes.history else roles[1] if i<sizes.history+sizes.development else roles[2],
        increment='10' if f.descriptor.measure=='area' else '1000') for i,f in enumerate(chosen))
    return Study(version='grouped_compound_study_v3' if sizes.version=='amended_36_v1' else 'grouped_compound_study_v2',
        partition_sizes=partition_sizes,sources=sources,groups=groups,loss=loss,dependencies=dependencies,
        authorization=authorization,excluded_entities=excluded_entities,source_files=source_files,
        attack_specification=AttackSpecification(version='report_corruption_v1',suppression='unavailable'))


def examples(study,role):
    facts={(f.descriptor.source_id,f.descriptor.measure):f for f in study.sources.facts}
    result=[]
    for group in (g for g in study.groups if g.role==role):
        f=facts[group.source_id,group.measure]
        with localcontext() as ctx:
            ctx.prec=50;base=Decimal(f.value);inc=Decimal(group.increment)
            variants=answer_variants(f.value,group.increment)
            for variant,b,d in variants:
                answer=canonical_json(dict(base=format(b,'f'),derived=format(d,'f')))
                q=question(f,group.increment)
                identity=content_id([study.study_id,group.source_id,variant])
                result.append(dict(example_id=identity,group_id=group.source_id,variant=variant,
                    question=q,answer=answer,reference=None,
                    label=dict(base_fact=b==base,derived_sum=d==b+inc,whole=b==base and d==b+inc)))
    return tuple(result)


def _component_examples(study,role,component_id):
    from app.analysis.capability_probe_analyzer import CapabilityProbeAnalyzer
    result=[]
    for e in examples(study,role):
        bound=bind_answer(question_plan(e['question'],study.sources.catalog),e['answer'])
        b=next(b for b in bound if b.component_id==component_id)
        result.append(dict(example_id=e['example_id']+'-'+component_id,split_identity=e['group_id'],
            question_id=content_id([e['question'],component_id]),run_id=validation_id(e['example_id'],b),
            dataset_id=f'{study.study_id}-{role}-{component_id}',role=role,
            purpose='heldout' if role=='final_test' else 'calibration',question=b.question,answer=b.answer,
            reference=None,analysis=component_analysis(b),
            label=IndependentLabel(answer_is_correct=e['label'][component_id],
                label_source='independent-source-and-exact-decimal-v2',label_method='independent_ground_truth',
                provenance=canonical_json(dict(source_manifest_id=study.sources.manifest_id,
                    source_entity=e['group_id'],component_id=component_id,binding_id=b.binding_id)))))
    return result


def reservation(study,component_id):
    rows=_component_examples(study,'final_test',component_id)
    keys=tuple(sorted((ReservedExample(example_id=e['example_id'],split_identity=e['split_identity'],
        question_id=e['question_id'],content_identity=content_id([e['question'],e['answer'],None]),validation_id=e['run_id'])
        for e in rows),key=lambda e:e.example_id))
    return FinalTestReservation(version='final_test_reservation_v1',role='final_test',
        dataset_id=f'{study.study_id}-final_test-{component_id}',
        custody_record='predeclared-source-known-exploratory-reservation:'+study.study_id,examples=keys)


def requests(study,setup,role,*,freeze_id=None):
    study=Study.model_validate(study);setup=MeasurementSetup.model_validate(setup)
    if study.sources.evidence_kind!=setup.evidence_kind:raise ValueError('source/setup empirical custody differs')
    if not any(r.kind=='corpus' and r.sha256==study.sources.corpus_sha256
        for v in setup.resources.verifiers if v.verifier_name=='evidence' for r in v.resources):
        raise ValueError('actual Evidence corpus differs from validated source manifest')
    if role not in {'history','development','final_test'}:raise ValueError('invalid partition')
    if role=='final_test' and freeze_id is None:raise ValueError('reserved collection requires frozen candidate/code')
    result={}
    for cid,name in (('base_fact','evidence'),('derived_sum','rule')):
        rows=_component_examples(study,role,cid)
        cls=HeldoutRecordingRequest if role=='final_test' else RecordingRequest
        example_cls=HeldoutExample if role=='final_test' else PreparationExample
        kwargs=dict(version='offline_heldout_recording_v1' if role=='final_test' else 'offline_recording_request_v1',
            intended_use='heldout' if role=='final_test' else 'study',study_approval=study.authorization,
            preparation_authorization=study.authorization,cache_contract='complete_team_independent_v1',
            randomness_control='No generation; preserve every Evidence/Rule attempt; no selective retries',
            execution_configuration_id=setup.resources.manifest_id,
            factory='app.benchmark.project_adapter:create_recording_verifiers',expected_setup=setup,
            final_test_reservation=reservation(study,cid),
            permitted_datasets=((role,f'{study.study_id}-{role}-{cid}'),),
            # Preserve the collector's exact resource roster. Unassigned entries
            # are explicitly unregistered and receive no verifier invocation.
            candidates=tuple(Candidate(verifier_name=v.verifier_name,adapter=v.verifier_name+'_v1',registered=v.verifier_name==name,
                capability_source='builtin',capabilities=BUILTIN_CAPABILITIES[v.verifier_name]) for v in setup.resources.verifiers),
            examples=tuple(example_cls(**e) for e in rows))
        if role=='final_test':kwargs['freeze_id']=freeze_id
        result[cid]=cls(**kwargs)
    return result


class JointRecordings(FrozenModel):
    version: Literal['component_bound_recordings_v2']='component_bound_recordings_v2'
    study_id: str
    role: Literal['history','development','final_test']
    bundles: tuple[tuple[str,RecordingBundle],...]


def validate_recordings(study,recordings,setup,*,freeze_id=None):
    recordings=JointRecordings.model_validate(recordings)
    if recordings.study_id!=study.study_id:raise ValueError('recordings belong to another source/study')
    expected=requests(study,setup,recordings.role,freeze_id=freeze_id)
    if tuple(cid for cid,_ in recordings.bundles)!=tuple(expected):raise ValueError('complete ordered component recordings required')
    for cid,bundle in recordings.bundles:
        if bundle.request!=expected[cid] or not completeness(bundle)['complete']:
            raise ValueError('component identity, resource, timing or completeness validation failed')
        if bundle.observed_setup!=setup:raise ValueError('actual setup differs from study recording setup')
        inputs={e.run_id:e for e in bundle.request.examples}
        active={c.verifier_name for c in bundle.request.candidates if c.registered}
        for attempt in bundle.attempts:
            if attempt.executed!=(attempt.candidate in active):raise ValueError('actual component call assignment differs')
            row=attempt.attempt.report
            if row is None:continue
            if (attempt.returned_payload_json is None or canonical_json(json.loads(attempt.returned_payload_json))!=canonical_json(row.model_dump(mode='json'))):
                raise ValueError('recorded report differs from the retained actual returned payload')
            binding=json.loads(inputs[attempt.run_id].label.provenance)['binding_id']
            for key,value in (('component_id',cid),('binding_id',binding)):
                if key in (row.metadata or {}) and row.metadata[key]!=value:raise ValueError('recorded component/binding identity differs')
    return recordings


def collect_partition(study,setup,role,verifiers,observer,directory,*,freeze_id=None,frozen=None,resume_from=None):
    """Existing collect() recovery rules, with fsynced starts and full outcome journals."""
    from app.game.offline import collection as collector
    from app.game.offline.compound_journal import record_requests
    if role=='final_test':
        if frozen is None:raise ValueError('reserved collection requires the actual frozen candidate, not an arbitrary freeze ID')
        frozen=FrozenCandidate.model_validate(frozen);verify_code(frozen)
        if frozen.study!=study or frozen.setup!=setup:raise ValueError('reserved candidate study/setup differs')
        if freeze_id is not None and freeze_id!=frozen.freeze_id:raise ValueError('reserved freeze ID differs')
        freeze_id=frozen.freeze_id
    prepared=requests(study,setup,role,freeze_id=freeze_id)
    seal=Path(directory).with_name(Path(directory).name+'-predeclared');seal.mkdir(parents=True,exist_ok=False)
    (seal/'study.json').write_text(study.model_dump_json(indent=2),encoding='utf-8')
    (seal/'settings.json').write_text(canonical_json(dict(study_id=study.study_id,role=role,
        setup=setup.model_dump(mode='json'),request_ids={cid:r.request_id for cid,r in prepared.items()},
        frozen_candidate_id=freeze_id,source_hashes=source_hashes())),encoding='utf-8')
    bundles=record_requests(prepared,setup,verifiers,observer,directory,collector,resume_from=resume_from)
    result=JointRecordings(study_id=study.study_id,role=role,bundles=bundles)
    (Path(directory)/'joint.json').write_text(result.model_dump_json(indent=2),encoding='utf-8')
    return validate_recordings(study,result,setup,freeze_id=freeze_id)


class Training(FrozenModel):
    study: Study
    setup: MeasurementSetup
    history: JointRecordings
    development: JointRecordings

    @model_validator(mode='after')
    def check(self):
        if self.history.role!='history' or self.development.role!='development':raise ValueError('test/diagnostic recordings cannot enter training')
        validate_recordings(self.study,self.history,self.setup)
        validate_recordings(self.study,self.development,self.setup)
        return self

    @property
    def binding_id(self):return content_id(self.model_dump(mode='json'))


def build_contract(training,*,fitting_configuration=None):
    from app.analysis.capability_probe_analyzer import CapabilityProbeAnalyzer
    from app.reputation.reputation_manager import ReputationManager
    from app.selection.verifier_selector import VerifierSelector
    from app.verifiers.base_verifier import BaseVerifier
    from app.game.models import PayoffProvenance
    from app.game.question_routing import classify_question
    class Handle(BaseVerifier):
        def __init__(self,name):self._name=name
        @property
        def name(self):return self._name
        def verify(self,*args):raise AssertionError('no inference during fitting')
    study=training.study;costs={};obligations=[]
    for cid in ('base_fact','derived_sum'):
        name='evidence' if cid=='base_fact' else 'rule'
        rows=[a for partition in (training.history,training.development) for component,b in partition.bundles if component==cid for a in b.attempts if a.candidate==name]
        if not rows or any(not a.executed or a.duration_ms is None for a in rows):raise ValueError('per-attempt cost evidence incomplete')
        costs[name]=sum(a.duration_ms for a in rows)/len(rows)
    budget=sum(costs.values())
    from app.game.resource_provenance import ResourceManifest
    scoped_resources=ResourceManifest(verifiers=tuple(v for v in training.setup.resources.verifiers if v.verifier_name in {'evidence','rule'}))
    contract=ExecutionContract(version='offline_public_decision_v4',coverage_version='task_output_contract_v2',
        contributor_version='informative_history_influence_v1',threshold=study.threshold,
        failure_contract='all_selected_returned',execution_configuration_id=scoped_resources.manifest_id,
        history_prior_alpha=study.prior_alpha,history_prior_beta=study.prior_beta,resource_manifest=scoped_resources,
        team_requirements=TeamRequirements(minimum_selected=1,minimum_informative=1))
    first=examples(study,'history')[0];bound=bind_answer(question_plan(first['question'],study.sources.catalog),first['answer'])
    for component in bound:
        manager=ReputationManager(prior_alpha=1.,prior_beta=1.);seen=set()
        labels={e['example_id']:e for e in _component_examples(study,'history',component.component_id)}
        bundle=dict(training.history.bundles)[component.component_id]
        active_name='evidence' if component.component_id=='base_fact' else 'rule'
        for a in bundle.attempts:
            if a.candidate!=active_name:continue
            e=labels[a.example_id];row=a.attempt.report
            key=(component.component_id,e['question'],e['answer'])
            if key in seen or a.attempt.state!='directional':continue
            seen.add(key)
            manager.update_from_ground_truth(a.candidate,'general',row.passed,e['label'].answer_is_correct)
        names=('evidence','rule')
        selector=VerifierSelector(verifiers=[Handle(n) for n in names],
            reputation_manager=manager,capabilities={n:BUILTIN_CAPABILITIES[n] for n in names})
        context=capture_context(selector,component_analysis(component),context=None,
            attempt_costs=tuple(costs.items()),budget=float(budget),cost_units='ms',loss_configuration=study.loss,
            dependencies=study.dependencies,aggregation_versions=(('reputation_weighted','log_odds_v1'),('dependency_group','groups_v1')),
            provenance=PayoffProvenance(attack_specification=study.attack_specification.specification_id,
                history_dataset=study.study_id+'-history',development_dataset=study.study_id+'-development',
                final_test_dataset=study.study_id+'-reserved-test',matrix_version='compound_joint_v2',
                loss_configuration=study.loss.version,category='general',evidence_kind=study.sources.evidence_kind),
            execution_contract_json=contract.model_dump_json())
        obligations.append(Obligation(component_id=component.component_id,context=context,contract=contract))
    return ComponentContract(binding_version=VERSION,descriptor_catalog_json=canonical_json(study.sources.catalog.model_dump(mode='json')),
        component_assignments=(('base_fact',('evidence',)),('derived_sum',('rule',))),
        actual_resources=training.setup.resources,
        fitting_configuration=fitting_configuration,
        category='numeric_fact',question_signature=classify_question(first['question'],component_catalog=study.sources.catalog)[1],
        obligations=tuple(obligations),budget=float(budget))


def replay_example(study,contract,strategy,example,bundles,attack):
    """Apply one shared failure action to every affected identity on every component."""
    bound=bind_answer(question_plan(example['question'],study.sources.catalog),example['answer'])
    decisions=[];contributors=set();audits=[]
    for obligation,(_,atomic),component in zip(contract.obligations,strategy.components,bound):
        cid=validation_id(example['example_id'],component)
        bundle=dict(bundles)[component.component_id]
        recorded=[a for a in bundle.attempts if a.example_id==example['example_id']+'-'+component.component_id]
        rows=[];states=[]
        for name in atomic.verifiers:
            a=next(a for a in recorded if a.candidate==name)
            changed,audit=transform(a.attempt,attack,study.attack_specification)
            audits.append(audit.model_dump(mode='json'))
            if changed.report is not None:rows.append(changed.report)
            states.append((name,changed.state))
        decision,influential=finalize_component(obligation,atomic,component,rows,states,cid)
        decisions.append(decision);contributors.update(influential)
    status,reasons=join_components(contract,decisions,contributors)
    correct=example['label']['whole'];loss=study.loss
    value=(0. if (status=='passed')==correct else (loss.false_reject if correct else loss.false_accept)) if status!='uncertain' else loss.uncertain
    return dict(example_id=example['example_id'],group_id=example['group_id'],variant=example['variant'],
        strategy_id=strategy.strategy_id,attack_id=attack.attack_id,public_status=status,answer_is_correct=correct,
        validation_loss=value,total_loss=value+loss.resource_weight*strategy.estimated_cost,
        estimated_cost=strategy.estimated_cost,components=decisions,reasons=reasons,attack_audit=audits)


def construct_payoffs(training,contract=None,*,fitting_configuration=None):
    from app.game.coverage_contract import CleanCoverageConstraint
    training=Training.model_validate(training)
    if contract is not None:fitting_configuration=contract.fitting_configuration
    if fitting_configuration is not None and fitting_configuration.original_study_id!=training.study.study_id:
        raise ValueError('post-development fitting configuration belongs to another study')
    contract=contract or build_contract(training,fitting_configuration=fitting_configuration)
    if contract!=build_contract(training,fitting_configuration=fitting_configuration):raise ValueError('contract differs from exact history/cost/training inputs')
    strategies=enumerate_component_strategies(contract)
    # The genuine V2 set contains one distinct complete call plan and two
    # aggregations. Equal call costs make the secondary cost objective constant;
    # generic minimax therefore solves the primary validation objective exactly.
    # A future unequal-cost candidate set needs the existing two-stage objective
    # machinery extended to joint definitions, not a silent penalty trade-off.
    if len({s.estimated_cost for s in strategies})!=1:
        raise ValueError('V2 objective requires equal fixed-plan costs; unequal-cost plans need a new objective contract')
    attacks=enumerate_attacks(training.study.dependencies,training.study.attack_specification)
    outcomes=[];values=[];coverage=[]
    for strategy in strategies:
        row=[]
        for attack in attacks:
            cells=[replay_example(training.study,contract,strategy,e,training.development.bundles,attack)
                for e in examples(training.study,'development')]
            outcomes.extend(cells);row.append(sum(c['validation_loss'] for c in cells)/len(cells))
            if attack.kind=='clean':coverage.append((strategy.strategy_id,sum(c['public_status']!='uncertain' for c in cells)/len(cells)))
        values.append(tuple(row))
    parent=PayoffMatrix(compatibility_id=contract.compatibility_id,strategy_ids=tuple(s.strategy_id for s in strategies),
        attack_ids=tuple(a.attack_id for a in attacks),values=tuple(values))
    minimum=fitting_configuration.minimum_clean_coverage if fitting_configuration else .9
    constraint=CleanCoverageConstraint(version='finalized_clean_development_coverage_v1',minimum=minimum,
        strategy_coverage=tuple(coverage),parent_matrix_id=parent.matrix_id,training_binding_id=training.binding_id,
        source_evaluation_id=content_id(outcomes))
    matrix=PayoffMatrix(**{**parent.model_dump(),'clean_coverage':constraint})
    return contract,matrix,outcomes


def fit(training,*,fitting_configuration=None):
    from app.game.solver import solve_minimax
    training=Training.model_validate(training)
    contract,matrix,outcomes=construct_payoffs(training,fitting_configuration=fitting_configuration)
    solution=solve_minimax(matrix,tolerance=1e-8)
    if solution.status!='optimal':return dict(status=solution.status,contract=contract,matrix=matrix,solution=solution,outcomes=outcomes,policy=None)
    binding=JointDevelopmentBinding(binding_version=VERSION,contract_id=contract.compatibility_id,matrix_id=matrix.matrix_id,
        history_dataset_id=training.study.study_id+'-history',development_dataset_id=training.study.study_id+'-development',
        final_test_reservation_id=content_id([reservation(training.study,c).model_dump(mode='json') for c in ('base_fact','derived_sum')]),
        history_manifest_sha256=content_id(training.history.model_dump(mode='json')),
        development_manifest_sha256=content_id(training.development.model_dump(mode='json')),
        grouped_partition_sha256=content_id([g.model_dump(mode='json') for g in training.study.groups]),
        label_protocol_id='independent-source-and-exact-decimal-v2',attack_specification_id=training.study.attack_specification.specification_id)
    empirical=training.study.sources.evidence_kind=='empirical'
    policy=ComponentPolicy(contract=contract,matrix=matrix,solution=solution,evidence_kind=training.study.sources.evidence_kind,
        joint_evidence_id=binding.binding_id if empirical else 'synthetic-only:'+training.binding_id,
        joint_development=binding if empirical else None)
    return dict(status='optimal',contract=contract,matrix=matrix,solution=solution,outcomes=outcomes,policy=policy)


def source_hashes(extra_files=()):
    import hashlib
    app=Path(__file__).resolve().parents[2];root=app.parent
    files=set(app.rglob('*.py'))|set(Path(p).resolve() for p in extra_files)
    files.update((root/'scripts/compound_study.py',root/'scripts/collect_compound_partition.py'))
    return tuple((str(p.resolve()),hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted(files))


class FrozenCandidate(FrozenModel):
    version: Literal['frozen_compound_candidate_v2']='frozen_compound_candidate_v2'
    study: Study
    setup: MeasurementSetup
    training_binding_id: str
    policy: ComponentPolicy
    best_fixed_strategy_id: str
    source_hashes: tuple[tuple[str,str],...]
    bootstrap_seed: Literal[1102]=1102
    bootstrap_replicates: Literal[1000]=1000

    @model_validator(mode='after')
    def check(self):
        if (self.policy.contract.descriptor_catalog_json!=canonical_json(self.study.sources.catalog.model_dump(mode='json'))
            or self.policy.contract.binding_version!=VERSION
            or self.policy.evidence_kind!=self.study.sources.evidence_kind
            or self.policy.contract.actual_resources!=self.setup.resources
            or self.policy.matrix.clean_coverage.training_binding_id!=self.training_binding_id):
            raise ValueError('frozen source, resources, policy or training binding differs')
        if self.best_fixed_strategy_id not in self.policy.matrix.strategy_ids:raise ValueError('frozen fixed baseline absent')
        if not self.source_hashes:raise ValueError('frozen candidate requires evaluation code identities')
        return self

    @property
    def freeze_id(self):return content_id(self.model_dump(mode='json'))


def verify_code(frozen):
    import hashlib
    for path,digest in frozen.source_hashes:
        if hashlib.sha256(Path(path).read_bytes()).hexdigest()!=digest:raise ValueError('frozen evaluation code changed: '+path)


def export_candidate(training,result,directory,*,code_files=None):
    """Revalidate exact producer data/payoffs before publishing any empirical policy."""
    import hashlib
    training=Training.model_validate(training)
    policy=result.get('policy')
    if policy is None:raise ValueError('infeasible fit cannot export a diagnostic plan as a policy')
    policy=ComponentPolicy.model_validate(policy)
    contract,matrix,outcomes=construct_payoffs(training,contract=policy.contract)
    if (policy.matrix!=matrix or policy.contract!=contract or result['outcomes']!=outcomes
        or policy.evidence_kind!=training.study.sources.evidence_kind):
        raise ValueError('exported policy does not bind exact validated development payoffs')
    if training.study.sources.evidence_kind=='empirical':
        b=policy.joint_development
        if (b is None or b.history_manifest_sha256!=content_id(training.history.model_dump(mode='json'))
            or b.development_manifest_sha256!=content_id(training.development.model_dump(mode='json'))
            or b.grouped_partition_sha256!=content_id([g.model_dump(mode='json') for g in training.study.groups])
            or b.final_test_reservation_id!=content_id([reservation(training.study,c).model_dump(mode='json') for c in ('base_fact','derived_sum')])
            or b.attack_specification_id!=training.study.attack_specification.specification_id):
            raise ValueError('empirical source recording provenance differs')
    coverage=dict(matrix.clean_coverage.strategy_coverage)
    costs={s.strategy_id:s.estimated_cost for s in enumerate_component_strategies(contract)}
    eligible=[(max(row),costs[sid],sid) for sid,row in zip(matrix.strategy_ids,matrix.values) if coverage[sid]>=matrix.clean_coverage.minimum]
    fixed=min(eligible)[2]
    frozen=FrozenCandidate(study=training.study,setup=training.setup,training_binding_id=training.binding_id,
        policy=policy,best_fixed_strategy_id=fixed,
        source_hashes=source_hashes(code_files or ()))
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=False)
    for name,value in (('policy',policy),('contract',contract),('matrix',matrix),('freeze',frozen)):
        (directory/(name+'.json')).write_text(value.model_dump_json(indent=2),encoding='utf-8')
    (directory/'development-outcomes.json').write_text(json.dumps(outcomes,indent=2),encoding='utf-8')
    development={}
    probabilities=dict(policy.solution.probabilities)
    for attack_id in matrix.attack_ids:
        local={sid:metrics([r for r in outcomes if r['strategy_id']==sid and r['attack_id']==attack_id]) for sid in matrix.strategy_ids}
        development[attack_id]=dict(policy={key:sum(probabilities[sid]*m[key] for sid,m in local.items())
            for key in ('coverage','false_accepts','false_rejects','uncertainty','decision_loss','estimated_cost','mean_loss')},
            development_best_fixed=local[fixed])
    (directory/'development-results.json').write_text(json.dumps(development,indent=2),encoding='utf-8')
    inventory={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in directory.iterdir() if p.is_file()}
    (directory/'inventory.json').write_text(json.dumps(inventory,indent=2),encoding='utf-8')
    return frozen


def load_candidate(directory):
    import hashlib
    directory=Path(directory)
    inventory=json.loads((directory/'inventory.json').read_text())
    for name,digest in inventory.items():
        if Path(name).name!=name or hashlib.sha256((directory/name).read_bytes()).hexdigest()!=digest:
            raise ValueError('frozen export inventory differs')
    frozen=FrozenCandidate.model_validate_json((directory/'freeze.json').read_text())
    if ComponentPolicy.model_validate_json((directory/'policy.json').read_text())!=frozen.policy:
        raise ValueError('reloaded exported policy differs from freeze')
    verify_code(frozen)
    return frozen


def metrics(rows,*,status_key='public_status',label_key='answer_is_correct'):
    n=len(rows);decided=sum(r[status_key]!='uncertain' for r in rows)
    fa=sum(r[status_key]=='passed' and not r[label_key] for r in rows)
    fr=sum(r[status_key]=='failed' and r[label_key] for r in rows)
    return dict(examples=n,coverage=decided/n,false_accepts=fa,false_rejects=fr,
        uncertainty=(n-decided)/n,selective_risk=(fa+fr)/decided if decided else None,
        decision_loss=sum(r.get('validation_loss',0.) for r in rows)/n,
        mean_loss=sum(r.get('total_loss',r.get('validation_loss',0.)) for r in rows)/n,
        estimated_cost=sum(r.get('estimated_cost',0.) for r in rows)/n)


def evaluate_frozen(frozen,test):
    """The only consumer of reserved outcomes; no fitting or new cost/history update."""
    import random
    frozen=FrozenCandidate.model_validate(frozen);verify_code(frozen)
    test=validate_recordings(frozen.study,test,frozen.setup,freeze_id=frozen.freeze_id)
    if test.role!='final_test':raise ValueError('frozen evaluation requires reserved partition')
    study=frozen.study;contract=frozen.policy.contract
    strategies=enumerate_component_strategies(contract)
    attacks=enumerate_attacks(study.dependencies,study.attack_specification)
    result={};all_rows=[]
    probabilities=dict(frozen.policy.solution.probabilities)
    for attack in attacks:
        per_strategy={s.strategy_id:[replay_example(study,contract,s,e,test.bundles,attack)
            for e in examples(study,'final_test')] for s in strategies}
        all_rows.extend(row for rows in per_strategy.values() for row in rows)
        fixed=per_strategy[frozen.best_fixed_strategy_id]
        # Expected policy metrics, NOT resampling a favorable strategy per example.
        by_strategy={sid:metrics(rows) for sid,rows in per_strategy.items()}
        expected={key:sum(probabilities[sid]*value[key] for sid,value in by_strategy.items())
            for key in ('examples','coverage','false_accepts','false_rejects','uncertainty','decision_loss','estimated_cost','mean_loss')}
        decided=expected['examples']*expected['coverage']
        expected['selective_risk']=(expected['false_accepts']+expected['false_rejects'])/decided if decided else None
        component_metrics={}
        labels={e['example_id']:e['label'] for e in examples(study,'final_test')}
        for cid in ('base_fact','derived_sum'):
            values=[]
            for row in fixed:
                c=next(c for c in row['components'] if c['component_id']==cid)
                correct=labels[row['example_id']][cid];status=c['public_status']
                loss=study.loss.uncertain if status=='uncertain' else (0. if (status=='passed')==correct else study.loss.false_reject if correct else study.loss.false_accept)
                values.append(dict(public_status=status,answer_is_correct=correct,validation_loss=loss))
            component_metrics[cid]=metrics(values)
        groups=sorted({r['group_id'] for r in fixed});group_values={}
        for group in groups:
            group_values[group]=sum(probabilities[sid]*sum(r['validation_loss'] for r in rows if r['group_id']==group)/4
                for sid,rows in per_strategy.items())
        rng=random.Random(frozen.bootstrap_seed)
        boot=sorted(sum(group_values[rng.choice(groups)] for _ in groups)/len(groups) for _ in range(frozen.bootstrap_replicates))
        result[attack.kind+':'+attack.attack_id]=dict(policy=expected,development_best_fixed=metrics(fixed),
            component_metrics_fixed=component_metrics,
            variant_metrics_fixed={variant:metrics([r for r in fixed if r['variant']==variant]) for variant in ('correct','wrong_math','wrong_base','both_wrong')},
            group_bootstrap_decision_loss_95_percentile=(boot[24],boot[974]),groups=len(groups),
            bootstrap_limitation=f'Entity clusters;{len(groups)} known-source groups. Degenerate zero-error bootstrap is not proof of zero population risk.')
    return dict(freeze_id=frozen.freeze_id,policy_id=frozen.policy.policy_id,attacks=result,outcomes=all_rows,
        actual_test_calls=sum(a.executed for _,b in test.bundles for a in b.attempts),
        actual_upstream_failures=sum(a.executed and a.attempt.state in {'failed','unavailable'} for _,b in test.bundles for a in b.attempts),
        measured_test_attempt_ms={name:dict(count=len(durations),mean=sum(durations)/len(durations),total=sum(durations))
            for name in ('evidence','rule') if (durations:=[a.duration_ms for _,b in test.bundles for a in b.attempts if a.candidate==name and a.executed])},
        attack_type='simulated report corruption; not upstream failure evidence',
        singleton_baselines='infeasible: neither existing singleton covers both components',
        greedy_baseline='not included: no independently defined comparable component greedy executor',
        distinct_feasible_teams=[['evidence','rule']],strategic_team_selection_advantage_established=False)
