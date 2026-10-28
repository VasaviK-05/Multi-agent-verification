"""Labelled preparation collection without fitting settings or live state.

Factory/observer adapters supply actual resources; unknown observations remain
explicit and cannot be exported as empirical replay or calibration evidence.
"""
from dataclasses import asdict
from typing import Literal

from pydantic import Field, StrictBool, model_validator

from app.analysis.models import QuestionAnalysis
from app.decision.coverage import factual_capabilities
from app.decision.report_identity import canonical_reports
from app.decision.vote_normalization import is_abstention
from app.game.dependencies import FrozenModel
from app.game.models import PlanningContext, canonical_json, content_id, requirement_signature
from app.game.offline.calibration import Text, MeasurementSetup, MeasurementInput, AttemptMeasurement
from app.game.offline.records import Attempt, Example, Partition, TrainingManifest, FinalTestReservation, ReservedExample
from app.game.offline.replay import category_id
from app.game.offline.timing import TimedVerifier
from app.game.resource_provenance import ResourceManifest
from app.models.schemas import VerificationResult
from app.selection.capabilities import CapabilityDescriptor, BUILTIN_CAPABILITIES, prerequisite_status
from app.selection.models import VerifierUnavailable
from app.selection.requirements import requirement_inputs


class IndependentLabel(FrozenModel):
    answer_is_correct: StrictBool
    label_source: Text
    label_method: Literal['independent_human', 'independent_ground_truth']
    provenance: Text


class Candidate(FrozenModel):
    verifier_name: Text
    adapter: Literal['generic_v1', 'rule_v1', 'evidence_v1', 'confidence_v1', 'semantic_v1']
    registered: StrictBool
    capability_source: Literal['builtin', 'explicit']
    capabilities: CapabilityDescriptor

    @model_validator(mode='after')
    def check(self):
        if self.capability_source == 'builtin' and BUILTIN_CAPABILITIES.get(self.verifier_name) != self.capabilities:
            raise ValueError('builtin capability declaration differs from the existing contract')
        return self


class PreparationExample(FrozenModel):
    example_id: Text
    split_identity: Text
    question_id: Text
    run_id: Text
    dataset_id: Text
    role: Literal['history', 'development']
    purpose: Literal['warmup', 'calibration']
    question: Text
    answer: str
    reference: str | None
    analysis: QuestionAnalysis
    label: IndependentLabel

    @property
    def content_identity(self):
        return content_id([self.question, self.answer, self.reference])


class RecordingRequest(FrozenModel):
    version: Literal['offline_recording_request_v1']
    intended_use: Literal['smoke', 'pilot', 'study']
    study_approval: Text | None
    preparation_authorization: Text
    cache_contract: Literal['complete_team_independent_v1']
    randomness_control: Text
    execution_configuration_id: Text
    factory: Text
    expected_setup: MeasurementSetup | None
    final_test_reservation: FinalTestReservation
    permitted_datasets: tuple[tuple[Literal['history', 'development'], Text], ...] = Field(min_length=1)
    candidates: tuple[Candidate, ...] = Field(min_length=1)
    examples: tuple[PreparationExample, ...] = Field(min_length=1)

    @model_validator(mode='after')
    def check(self):
        if self.factory.count(':') != 1 or not all(self.factory.split(':')):
            raise ValueError('factory must be module:function')
        if self.intended_use == 'study' and self.study_approval is None:
            raise ValueError('study collection requires explicit study approval')
        if len({c.verifier_name for c in self.candidates}) != len(self.candidates):
            raise ValueError('duplicate candidate')
        if (len(set(self.permitted_datasets)) != len(self.permitted_datasets)
                or len({d for _, d in self.permitted_datasets}) != len(self.permitted_datasets)):
            raise ValueError('permitted dataset roles/identities must be distinct')
        if len({e.run_id for e in self.examples}) != len(self.examples):
            raise ValueError('duplicate run ID')
        if len({(e.role, e.example_id) for e in self.examples}) != len(self.examples):
            raise ValueError('duplicate example in a partition; use a separate warmup request')
        seen, groups = {}, {}
        reservation = self.final_test_reservation
        for e in self.examples:
            if (e.role, e.dataset_id) not in self.permitted_datasets:
                raise ValueError('dataset not permitted')
            if e.dataset_id == reservation.dataset_id:
                raise ValueError('final-test collection forbidden')
            for r in reservation.examples:
                if (any(getattr(e, f) == getattr(r, f) for f in
                        ('example_id', 'split_identity', 'question_id', 'content_identity'))
                        or e.run_id == r.validation_id):
                    raise ValueError('final-test collection forbidden')
            for field in ('example_id', 'split_identity', 'question_id', 'content_identity'):
                key = field, getattr(e, field)
                if key in seen and seen[key] != (e.role, e.dataset_id):
                    raise ValueError('collection split leakage')
                seen[key] = e.role, e.dataset_id
                if field in {'question_id', 'content_identity'}:
                    if key in groups and groups[key] != e.split_identity:
                        raise ValueError('related examples must share one split identity')
                    groups[key] = e.split_identity
        if self.expected_setup is not None:
            if self.execution_configuration_id != self.expected_setup.resources.manifest_id:
                raise ValueError('execution configuration must identify the declared resource manifest')
            self.expected_setup.resources.require_candidates(c.verifier_name for c in self.candidates)
        return self

    @property
    def request_id(self):
        return content_id(self.model_dump(mode='json'))


class DiagnosticExclusionRoster(FrozenModel):
    """Unwitnessed outcome-free exclusions; never a scientific reservation."""
    version: Literal['diagnostic_exclusion_roster_v1']
    role: Literal['final_test']
    dataset_id: Text
    examples: tuple[ReservedExample, ...] = Field(min_length=1)

    @model_validator(mode='after')
    def check(self):
        for field in ('example_id', 'validation_id'):
            if len({getattr(e, field) for e in self.examples}) != len(self.examples):
                raise ValueError('exclusion roster requires unique examples/runs')
        return self


class DiagnosticExample(PreparationExample):
    label: None = None


class DiagnosticRecordingRequest(RecordingRequest):
    """Same dispatch/recording, with no ground truth or custody approval claim."""
    version: Literal['offline_diagnostic_recording_v1']
    intended_use: Literal['smoke'] = 'smoke'
    study_approval: None = None
    cache_contract: Literal['diagnostic_observation_only'] = 'diagnostic_observation_only'
    final_test_reservation: DiagnosticExclusionRoster
    examples: tuple[DiagnosticExample, ...] = Field(min_length=1)


def validate_recording_request(value):
    version = value.get('version') if isinstance(value, dict) else getattr(value, 'version', None)
    schema = DiagnosticRecordingRequest if version == 'offline_diagnostic_recording_v1' else RecordingRequest
    return schema.model_validate(value)


def collection_plan(request, example):
    """Capture existing requirement/prerequisite semantics, with no reputation read."""
    candidates = []
    for candidate in request.candidates:
        status, reason = prerequisite_status(candidate.capabilities, example.reference)
        if not candidate.registered:
            reason = 'not registered'
        candidates.append(dict(**candidate.model_dump(mode='json'),
            prerequisite_status=status, exclusion_reason=reason,
            eligible=candidate.registered and reason is None))
    return dict(analysis=asdict(example.analysis),
                requirements=asdict(requirement_inputs(example.analysis)), candidates=candidates)


class CollectedAttempt(FrozenModel):
    attempt_id: Text
    example_id: Text
    run_id: Text
    candidate: Text
    planning_json: Text
    attempt: Attempt
    executed: StrictBool
    duration_ms: float | None = Field(default=None, ge=0)
    timing_status: Literal['returned', 'failure', 'timeout', 'interrupted'] | None = None
    measurement: AttemptMeasurement | None = None
    after_resources_json: str | None = None
    returned_payload_json: str | None = None
    achieved_capabilities: tuple[str, ...] = ()
    issues: tuple[str, ...] = ()


class RecordingBundle(FrozenModel):
    version: Literal['offline_recording_bundle_v1'] = 'offline_recording_bundle_v1'
    request: RecordingRequest | DiagnosticRecordingRequest
    observed_setup: MeasurementSetup | None
    attempts: tuple[CollectedAttempt, ...]

    @model_validator(mode='after')
    def check_links(self):
        setup = self.observed_setup
        if self.request.expected_setup is not None and self.request.expected_setup != setup:
            raise ValueError('bundle setup differs from the collection request')
        if setup is not None:
            setup.resources.require_candidates(c.verifier_name for c in self.request.candidates)
            if setup.resources.manifest_id != self.request.execution_configuration_id:
                raise ValueError('bundle execution/resource identity mismatch')
        request_id = self.request.request_id
        expected = {attempt_identity(self.request, e, c, request_id=request_id): (e, c)
                    for e in self.request.examples for c in self.request.candidates}
        if len({a.attempt_id for a in self.attempts}) != len(self.attempts):
            raise ValueError('duplicate recorded attempt')
        for a in self.attempts:
            if a.attempt_id not in expected:
                raise ValueError('unknown attempt identity')
            e, c = expected[a.attempt_id]
            if (a.example_id != e.example_id or a.run_id != e.run_id or a.candidate != c.verifier_name
                    or a.attempt.verifier_name != c.verifier_name or a.attempt.adapter != c.adapter
                    or a.attempt.execution_id != e.run_id
                    or a.attempt.configuration_id != self.request.execution_configuration_id
                    or a.planning_json != canonical_json(collection_plan(self.request, e))):
                raise ValueError('recording identity/planning link mismatch')
            if a.executed != (a.duration_ms is not None):
                raise ValueError('only executed calls may contain timings')
            if a.executed != (a.timing_status is not None):
                raise ValueError('only executed calls may contain timing status')
            planning = collection_plan(self.request, e)
            eligible = next(p['eligible'] for p in planning['candidates'] if p['verifier_name'] == c.verifier_name)
            if a.executed and not eligible:
                raise ValueError('ineligible candidate was executed')
            expected_achieved = () if a.attempt.report is None else tuple(sorted(factual_capabilities(a.attempt.report)))
            if a.achieved_capabilities != expected_achieved:
                raise ValueError('achieved-capability audit differs from the actual report')
            if a.measurement is not None:
                m = a.measurement
                if (self.observed_setup is None or m.run_id != e.run_id or m.example_id != e.example_id
                        or m.verifier_name != c.verifier_name or m.duration_ms != a.duration_ms
                        or m.status != a.timing_status
                        or m.content_identity != e.content_identity or m.question_id != e.question_id
                        or m.split_identity != e.split_identity or m.dataset_id != e.dataset_id
                        or m.role != e.role or m.purpose != e.purpose):
                    raise ValueError('measurement/report link mismatch')
                MeasurementInput(setup=setup, permitted_datasets=self.request.permitted_datasets,
                    preparation_authorization=self.request.preparation_authorization, attempts=(m,))
        return self

    @property
    def bundle_id(self):
        # Incidental durations make this an audit payload identity, not a stable run ID.
        return content_id(self.model_dump(mode='json'))


def attempt_identity(request, example, candidate, *, request_id=None):
    return content_id(['offline_attempt_v1', request.request_id if request_id is None else request_id,
                       example.run_id, candidate.verifier_name])


def completeness(bundle):
    bundle = RecordingBundle.model_validate(bundle)
    lookup = {a.attempt_id: a for a in bundle.attempts}
    request_id = bundle.request.request_id
    gaps = []
    for e in bundle.request.examples:
        for c in bundle.request.candidates:
            row = lookup.get(attempt_identity(bundle.request, e, c, request_id=request_id))
            reasons = ('not_attempted',) if row is None else row.issues
            if row is not None and row.attempt.state == 'missing':
                reasons = (*reasons, 'missing_recording')
            if row is not None and row.attempt.observed_resources_json is None:
                reasons = (*reasons, 'unknown_resources')
            if row is not None and row.attempt.observed_resources_json is not None:
                from app.game.resource_provenance import VerifierResources
                try:
                    if bundle.observed_setup is None:
                        raise ValueError('setup unknown')
                    bundle.observed_setup.resources.require_observation(
                        VerifierResources.model_validate_json(row.attempt.observed_resources_json))
                    if row.executed:
                        if row.after_resources_json is None:
                            raise ValueError('post-attempt observation missing')
                        after = VerifierResources.model_validate_json(row.after_resources_json)
                        if after.verifier_name != row.candidate:
                            raise ValueError('post-attempt observation candidate differs')
                        bundle.observed_setup.resources.require_observation(after)
                        if row.measurement is None:
                            raise ValueError('linked timing missing')
                except ValueError as exc:
                    reasons = (*reasons, 'resource_or_timing_incompatible:' + str(exc))
            if reasons:
                gaps.append(dict(example_id=e.example_id, verifier_name=c.verifier_name,
                                 reasons=sorted(set(reasons))))
    return dict(complete=not gaps, intended_use=bundle.request.intended_use,
        study_approval=bundle.request.study_approval, gaps=gaps,
        expected_attempts=len(bundle.request.examples)*len(bundle.request.candidates),
        recorded_outcomes=len(bundle.attempts), executed_calls=sum(a.executed for a in bundle.attempts),
        note='Complete collection is not approval of scientific settings or evidence of improvement.')


def collect(request, verifiers, observed_setup, observer, *, sink=None):
    """Execute every eligible candidate once; retain failures and continue offline."""
    request = validate_recording_request(request)
    request_id = request.request_id
    setup = None if observed_setup is None else MeasurementSetup.model_validate(observed_setup)
    if request.expected_setup is not None and setup != request.expected_setup:
        raise ValueError('factory observed setup differs from approved collection setup')
    if setup is not None:
        setup.resources.require_candidates(c.verifier_name for c in request.candidates)
        if setup.resources.manifest_id != request.execution_configuration_id:
            raise ValueError('factory execution/resource identity mismatch')
    verifiers = list(verifiers)
    pool = {v.name: v for v in verifiers}
    if len(pool) != len(verifiers) or set(pool) - {c.verifier_name for c in request.candidates if c.registered}:
        raise ValueError('factory returned duplicate or undeclared candidates')
    results, interrupted = [], False
    def observe(name):
        if observer is None or setup is None:
            raise ValueError('resource observer/setup unavailable; resources unknown')
        actual = ResourceManifest.model_validate(observer.snapshot())
        entry = next((r for r in actual.verifiers if r.verifier_name == name), None)
        if entry is None:
            raise ValueError('observed candidate resources unavailable')
        # Preserve changed bytes too; they are genuine observations, not unknown
        # resources. The mismatch blocks verified timing and training export.
        return entry, (None if actual == setup.resources else 'resource manifest changed or differs from observed setup')
    for e in request.examples:
        plan = collection_plan(request, e)
        for c, planned in zip(request.candidates, plan['candidates']):
            issues, pre, post, payload, row = [], None, None, None, None
            pre_issue = post_issue = None
            state, executed, achieved = 'missing', False, ()
            durations, measurements = [], []
            reason = None
            if interrupted:
                issues.append('not_attempted_after_interrupt')
            else:
                try:
                    pre, pre_issue = observe(c.verifier_name)
                    if pre_issue is not None:
                        issues.append('pre_observation:' + pre_issue)
                except Exception as exc:
                    issues.append('pre_observation:' + type(exc).__name__ + ':' + str(exc))
                if not planned['eligible']:
                    state, reason = 'unavailable', planned['exclusion_reason']
                elif c.verifier_name not in pool:
                    state, reason = 'unavailable', 'registered adapter unavailable from factory'
                else:
                    executed = True
                    metadata = dict(run_id=e.run_id, example_id=e.example_id, split_identity=e.split_identity,
                        question_id=e.question_id, content_identity=e.content_identity, dataset_id=e.dataset_id,
                        role=e.role, purpose=e.purpose,
                        setup_fingerprint=setup.fingerprint if setup else 'unknown',
                        verifier_fingerprint=content_id(pre.model_dump(mode='json')) if pre else 'unknown')
                    try:
                        raw = TimedVerifier(pool[c.verifier_name], durations,
                            measurement_metadata=metadata, measurements=measurements).verify(e.question, e.answer, e.reference)
                    except (KeyboardInterrupt, SystemExit):
                        interrupted = True
                        issues.append('interrupted_attempt')
                    except (VerifierUnavailable, TimeoutError) as exc:
                        state = 'unavailable' if isinstance(exc, VerifierUnavailable) else 'failed'
                        reason = type(exc).__name__ + ':' + str(exc)
                    except Exception as exc:
                        state, reason = 'failed', type(exc).__name__ + ':' + str(exc)
                        # Production distinguishes explicitly translated execution
                        # failures from unexpected programming/configuration errors.
                        from app.game.execution import VerifierExecutionFailure
                        if not isinstance(exc, VerifierExecutionFailure):
                            issues.append('unexpected_exception_requires_adapter_review:' + reason)
                    else:
                        try:
                            if isinstance(raw, VerificationResult):
                                payload = raw.model_dump_json()
                            elif isinstance(raw, (dict, list, str, int, float, bool)) or raw is None:
                                payload = canonical_json(raw)
                            checked, _, _ = canonical_reports([raw], team=(c.verifier_name,),
                                validation_id=e.run_id, deduplicate=False)
                            row = checked[0]
                            state = 'abstention' if is_abstention(row) else 'directional'
                            achieved = tuple(sorted(factual_capabilities(row)))
                        except Exception as exc:
                            issues.append('invalid_returned_report:' + type(exc).__name__ + ':' + str(exc))
                    try:
                        post, post_issue = observe(c.verifier_name)
                        if post_issue is not None:
                            issues.append('post_observation:' + post_issue)
                    except Exception as exc:
                        issues.append('post_observation:' + type(exc).__name__ + ':' + str(exc))
            # Preserve all failure/prerequisite details in the sidecar, without
            # fabricating an absent report or a zero-duration unattempted call.
            provenance = canonical_json(dict(request_id=request_id, intended_use=request.intended_use,
                error_or_unavailability=reason, label_provenance_separate=True))
            attempt = Attempt(verifier_name=c.verifier_name, state=state,
                report_json=None if row is None else row.model_dump_json(), execution_id=e.run_id,
                configuration_id=request.execution_configuration_id, report_provenance=provenance,
                adapter=c.adapter, observed_resources_json=None if pre is None else pre.model_dump_json())
            from app.game.offline.attacks import adapter_incompatibility
            incompatible = adapter_incompatibility(attempt)
            if incompatible is not None:
                issues.append('incompatible_attack_adapter:' + incompatible.expected_adapter)
            measured = (AttemptMeasurement.model_validate(measurements[0])
                        if measurements and pre is not None and post is not None
                        and pre_issue is None and post_issue is None else None)
            result = CollectedAttempt(attempt_id=attempt_identity(request, e, c, request_id=request_id), example_id=e.example_id,
                run_id=e.run_id, candidate=c.verifier_name, planning_json=canonical_json(plan), attempt=attempt,
                executed=executed, duration_ms=durations[0] if durations else None,
                timing_status=measurements[0]['status'] if measurements else None,
                measurement=measured, after_resources_json=None if post is None else post.model_dump_json(),
                returned_payload_json=payload, achieved_capabilities=achieved, issues=tuple(issues))
            results.append(result)
            if sink is not None:
                sink(result)
    return RecordingBundle(request=request, observed_setup=setup, attempts=tuple(results))


def measurement_input(bundle):
    bundle = RecordingBundle.model_validate(bundle)
    if isinstance(bundle.request, DiagnosticRecordingRequest):
        raise ValueError('diagnostic-only timings remain in linked attempts; study custody and calibration freeze are not approved')
    if bundle.observed_setup is None or any(a.executed and a.measurement is None for a in bundle.attempts):
        raise ValueError('timings lack verified setup/resource observations; raw durations remain in bundle')
    from app.game.resource_provenance import VerifierResources
    for attempt in bundle.attempts:
        if not attempt.executed:
            continue
        try:
            for raw in (attempt.attempt.observed_resources_json, attempt.after_resources_json):
                observed = VerifierResources.model_validate_json(raw)
                if observed.verifier_name != attempt.candidate:
                    raise ValueError('resource observation candidate differs')
                bundle.observed_setup.resources.require_observation(observed)
        except ValueError as exc:
            raise ValueError('timings lack verified setup/resource observations; raw durations remain in bundle') from exc
    rows = tuple(a.measurement for a in bundle.attempts if a.measurement is not None)
    return MeasurementInput(setup=bundle.observed_setup, permitted_datasets=bundle.request.permitted_datasets,
        preparation_authorization=bundle.request.preparation_authorization, attempts=rows)


def export_training(bundle, context):
    """Bind only after explicit fit settings/history snapshot are available."""
    bundle = RecordingBundle.model_validate(bundle)
    context = PlanningContext.model_validate(context)
    if not completeness(bundle)['complete']:
        raise ValueError('collection incomplete; retain/review every example before export')
    if context.offline_evaluation_id is not None or context.pooling_contract_json is not None:
        raise ValueError('export requires a fresh unbound planning context')
    if any(e.purpose == 'warmup' for e in bundle.request.examples):
        raise ValueError('warmup examples are not automatically training data; collect separately')
    if bundle.request.intended_use == 'smoke':
        raise ValueError('smoke collections cannot be promoted to fitting inputs')
    candidates = {c.verifier_name: c for c in context.plan.candidates}
    if set(candidates) != {c.verifier_name for c in bundle.request.candidates}:
        raise ValueError('context candidate roster differs from recorded collection')
    if context.execution_contract_json is not None:
        from app.game.execution_contract import ExecutionContract
        contract = ExecutionContract.model_validate_json(context.execution_contract_json)
        if (contract.execution_configuration_id != bundle.request.execution_configuration_id
                or contract.resource_manifest != bundle.observed_setup.resources):
            raise ValueError('context execution contract differs from observed collection')
    lookup = {(a.run_id, a.candidate): a for a in bundle.attempts}
    parts = []
    for role in ('history', 'development'):
        examples = []
        for e in (e for e in bundle.request.examples if e.role == role):
            if (e.analysis.domain != context.plan.domain
                    or e.analysis.domain_status != context.plan.domain_status
                    or e.analysis.analysis_method != context.plan.analysis_method
                    or e.analysis.difficulty != context.plan.difficulty
                    or e.analysis.difficulty_score != context.plan.difficulty_score
                    or getattr(e.analysis.research_context, 'context_version', None) != context.plan.context_version
                    or getattr(e.analysis.research_context, 'scoring_version', None) != context.plan.scoring_version
                    or requirement_signature(requirement_inputs(e.analysis)) != context.requirement_signature
                    or bool(e.reference and e.reference.strip()) != context.plan.reference_available):
                raise ValueError('context domain/requirements/reference differs from recorded planning')
            for recorded in collection_plan(bundle.request, e)['candidates']:
                target = candidates[recorded['verifier_name']]
                descriptor = recorded['capabilities']
                if (target.registered != recorded['registered'] or target.eligible != recorded['eligible']
                        or target.prerequisite_status != recorded['prerequisite_status']
                        or target.exclusion_reason != recorded['exclusion_reason']
                        or set(target.expected_capabilities) != set(descriptor['expected_capabilities'])
                        or target.requires_reference != descriptor['requires_reference']
                        or target.configured_readiness != descriptor['readiness']
                        or tuple(target.limitations) != tuple(descriptor['limitations'])):
                    raise ValueError('context eligibility/capabilities differ from collected prerequisites')
            examples.append(Example(example_id=e.example_id, split_identity=e.split_identity,
                question_id=e.question_id, question=e.question, answer=e.answer, reference=e.reference,
                domain=e.analysis.domain, planning_category=category_id(context),
                answer_is_correct=e.label.answer_is_correct, label_source=e.label.label_source,
                label_method=e.label.label_method, validation_id=e.run_id,
                execution_configuration_id=bundle.request.execution_configuration_id,
                cache_contract=bundle.request.cache_contract,
                attempts=tuple(lookup[e.run_id, c].attempt for c in candidates)))
        datasets = {e.dataset_id for e in bundle.request.examples if e.role == role}
        if len(datasets) != 1:
            raise ValueError('export requires exactly one nonempty history and development dataset')
        parts.append(Partition(role=role, dataset_id=next(iter(datasets)), examples=tuple(examples)))
    return TrainingManifest(version='game_training_manifest_v1', evidence_kind=bundle.observed_setup.evidence_kind,
        partitions=tuple(parts), final_test_reservation=bundle.request.final_test_reservation)
