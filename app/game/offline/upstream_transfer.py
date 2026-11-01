"""Explicit frozen-rule transfer evaluation, NOT a historical equivalence bridge."""
from typing import Literal

from pydantic import Field, model_validator

from app.game.artifacts import PolicyArtifact
from app.game.dependencies import FrozenModel
from app.game.execution_contract import ExecutionContract
from app.game.models import content_id
from app.game.offline.attacks import AttackSpecification
from app.game.offline.calibration import MeasurementSetup, Text
from app.game.offline.collection import (RecordingBundle, RecordingRequest, collection_plan, completeness)
from app.game.offline.upstream import (ScenarioRecording, require_execution_records,
    scientific_bundle_id, validate_scenario_links)
from app.game.offline.upstream_evaluation import (FrozenUpstreamEvaluation, evaluate_configurations,
    validate_original_recordings)
from app.game.research.evidence_validation import EvidenceValidation
from app.game.resource_provenance import ResourceManifest


def snapshot_collector(root, destination):
    """Freeze actual app source bytes, including dirty/untracked files; no models."""
    import hashlib
    import json
    import os
    from pathlib import Path
    import subprocess
    import zipfile
    if any(os.environ.get(k) for k in ('GIT_DIR', 'GIT_WORK_TREE', 'GIT_INDEX_FILE')):
        raise ValueError('unset Git source overrides before snapshotting the collector')
    root, destination = Path(root).resolve(), Path(destination).resolve()
    if destination.is_relative_to(root/'app'): raise ValueError('source snapshot must stay outside fingerprinted app/')
    top = Path(subprocess.check_output(['git', 'rev-parse', '--show-toplevel'], cwd=root, text=True).strip()).resolve()
    if top != root: raise ValueError('collector root must be its actual Git worktree')
    revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()
    status = subprocess.check_output(['git', 'status', '--porcelain=v1'], cwd=root, text=True)
    files = {p.relative_to(root).as_posix(): p.read_bytes() for p in sorted((root/'app').rglob('*.py'))}
    if not files: raise ValueError('no application source to snapshot')
    manifest = tuple((p, hashlib.sha256(raw).hexdigest()) for p, raw in files.items())
    destination.mkdir(parents=True, exist_ok=False)
    with zipfile.ZipFile(destination/'app-source.zip', 'x', compression=zipfile.ZIP_DEFLATED) as archive:
        for name, raw in files.items(): archive.writestr(name, raw)
    current = {p.relative_to(root).as_posix(): p.read_bytes() for p in sorted((root/'app').rglob('*.py'))}
    if current != files or subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip() != revision:
        raise ValueError('source changed during snapshot; partial archive is not approved for collection')
    (destination/'source-manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    receipt = dict(version='actual_collector_source_snapshot_v1', code_revision=revision,
        application_source_digest=content_id(manifest), working_tree_status=status,
        archive_sha256=hashlib.sha256((destination/'app-source.zip').read_bytes()).hexdigest(),
        note='Actual app bytes preserved; scripts/fixtures/approvals separately retained; no source equivalence claim.')
    (destination/'snapshot.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    return receipt


class ResourceTransition(FrozenModel):
    verifier_name: Text
    kind: Text
    resource_id: Text
    historical_sha256: str = Field(pattern=r'^[0-9a-f]{64}$')
    current_sha256: str = Field(pattern=r'^[0-9a-f]{64}$')


def resource_transitions(historical, current):
    """Initial transfer keeps logical topology; every changed content is explicit."""
    def flattened(manifest):
        return {(v.verifier_name, r.kind, r.resource_id): r.sha256 for v in manifest.verifiers for r in v.resources}
    before, after = flattened(historical), flattened(current)
    if before.keys() != after.keys():
        raise ValueError('transfer v1 cannot change verifier/resource topology; separately review that contract')
    return tuple(ResourceTransition(verifier_name=k[0], kind=k[1], resource_id=k[2],
        historical_sha256=before[k], current_sha256=after[k]) for k in sorted(before) if before[k] != after[k])


def decision_semantics_id(contract):
    return content_id(contract.model_dump(mode='json', exclude={'resource_manifest', 'execution_configuration_id'}))


class EvaluationTransferDeclaration(FrozenModel):
    version: Literal['frozen_policy_evaluation_transfer_v1']
    original_artifact_id: Text
    historical_recording_id: Text
    historical_setup_fingerprint: Text
    current_clean_setup: MeasurementSetup
    current_clean_request_id: Text
    current_source_files: tuple[tuple[Text, Text], ...] = Field(min_length=1)
    decision_semantics_id: Text
    report_contract: Literal['verification_result_existing_vote_adapters_v1']
    equivalence: Literal['not_established_original_source_unavailable']
    authorization_record: Text
    implementation_change_record: Text
    report_compatibility_record: Text
    source_snapshot_record: Text
    resource_changes: tuple[ResourceTransition, ...]
    scope: Literal['original_prepared_development_examples_only']
    historical_clean_use: Literal['separate_reference_never_new_clean_substitution']

    @model_validator(mode='after')
    def check_source(self):
        import re
        from pathlib import PurePosixPath
        paths = []
        for name, digest in self.current_source_files:
            p = PurePosixPath(name)
            if p.is_absolute() or '..' in p.parts or p.as_posix() != name or not name.startswith('app/') or not name.endswith('.py'):
                raise ValueError('source manifest requires safe relative app Python paths')
            if re.fullmatch('[0-9a-f]{64}', digest) is None: raise ValueError('source file requires actual SHA-256')
            paths.append(name)
        if len(paths) != len(set(paths)) or tuple(self.current_source_files) != tuple(sorted(self.current_source_files)):
            raise ValueError('source manifest requires unique sorted paths')
        if content_id(self.current_source_files) != self.current_clean_setup.application_source_digest:
            raise ValueError('current source manifest does not establish the declared new application digest')
        return self

    @property
    def declaration_id(self):
        return content_id(self.model_dump(mode='json'))


class FreshDevelopmentRecording(FrozenModel):
    bundle: RecordingBundle
    evidence_validation: EvidenceValidation | None = None

    @model_validator(mode='after')
    def check(self):
        request = self.bundle.request
        if type(request) is not RecordingRequest or request.intended_use == 'smoke':
            raise ValueError('fresh clean needs approved labelled pilot/study recordings')
        if any(e.role != 'development' for e in request.examples):
            raise ValueError('fresh clean collection must contain development only, never history/final-test')
        if self.bundle.observed_setup is None or request.expected_setup != self.bundle.observed_setup:
            raise ValueError('fresh clean requires exact expected and observed setup')
        report = completeness(self.bundle)
        if not report['complete']: raise ValueError('fresh clean recording incomplete: '+str(report['gaps']))
        require_execution_records(self.bundle)
        if self.evidence_validation is not None:
            self.evidence_validation.require_resources(self.bundle.observed_setup.resources)
        return self


def validate_collection_scope(historical, new):
    """Reject expanded/relabelled requests before any transfer collection calls."""
    old = historical.request
    if (new.candidates != old.candidates or new.factory != old.factory
            or new.randomness_control != old.randomness_control
            or new.final_test_reservation != old.final_test_reservation
            or new.permitted_datasets != old.permitted_datasets):
        raise ValueError('transfer roster/factory/randomness/reservation/dataset contract differs')
    expected = {e.example_id: e for e in old.examples if e.role == 'development'}
    if any(e.role != 'development' for e in new.examples):
        raise ValueError('transfer collection is development only')
    if {e.example_id for e in new.examples} != set(expected):
        raise ValueError('transfer must retain the exact original development scope')
    old_runs = {e.run_id for e in old.examples}
    for e in new.examples:
        left, right = e.model_dump(), expected[e.example_id].model_dump()
        left.pop('run_id'); right.pop('run_id')
        if left != right: raise ValueError('transfer question/answer/reference/independent label/grouping/analysis mismatch')
        if e.run_id in old_runs: raise ValueError('transfer clean requires fresh execution IDs, not historical reports')


def validate_fresh_scope(artifact, historical, fresh):
    """Keep all original inputs/labels/capabilities, changing only execution IDs/setup."""
    new = fresh.request
    validate_collection_scope(historical, new)
    for e in new.examples:
        # Recheck the actual planning/prerequisite information against the frozen plan.
        for recorded in collection_plan(new, e)['candidates']:
            candidate = next(c for c in artifact.context.plan.candidates if c.verifier_name == recorded['verifier_name'])
            if (candidate.eligible != recorded['eligible'] or candidate.prerequisite_status != recorded['prerequisite_status']
                    or candidate.exclusion_reason != recorded['exclusion_reason']):
                raise ValueError('current prerequisites/eligibility differ from the frozen decision scope')


def validate_report_contract(historical, recordings):
    """Reject changed score/decision interfaces, not changed verifier conclusions."""
    meanings, explicit_decisions = {}, {}
    for row in historical.attempts:
        report = row.attempt.report
        if report is None: continue
        metadata = report.metadata or {}
        meaning = metadata.get('score_meaning')
        if meaning is not None and not isinstance(meaning, str): raise ValueError('unsupported historical score-meaning contract')
        meanings.setdefault(row.candidate, set()).add(meaning)
        explicit_decisions.setdefault(row.candidate, []).append('decision' in metadata)
    for bundle in recordings:
        for row in bundle.attempts:
            report = row.attempt.report
            if report is None: continue
            metadata = report.metadata or {}
            meaning = metadata.get('score_meaning')
            if (meaning is not None and not isinstance(meaning, str)) or meaning not in meanings.get(row.candidate, set()):
                raise ValueError('unsupported current score-meaning/report contract for '+row.candidate)
            if all(explicit_decisions.get(row.candidate, [True])) and 'decision' not in metadata:
                raise ValueError('current report omitted the frozen authoritative decision contract')


class FrozenPolicyTransferInput(FrozenModel):
    version: Literal['frozen_policy_transfer_input_v1'] = 'frozen_policy_transfer_input_v1'
    declaration: EvaluationTransferDeclaration
    artifact: PolicyArtifact
    historical_clean: RecordingBundle
    current_clean: FreshDevelopmentRecording
    report_attacks: AttackSpecification
    scenarios: tuple[ScenarioRecording, ...] = Field(min_length=1)

    @model_validator(mode='after')
    def check(self):
        artifact, declaration = self.artifact, self.declaration
        validate_original_recordings(artifact, self.historical_clean, self.report_attacks)
        clean = self.current_clean.bundle
        historical = self.historical_clean
        if (declaration.original_artifact_id != artifact.artifact_id
                or declaration.historical_recording_id != scientific_bundle_id(historical)
                or declaration.historical_setup_fingerprint != historical.observed_setup.fingerprint):
            raise ValueError('transfer declaration differs from the original artifact/historical provenance')
        if clean.observed_setup != declaration.current_clean_setup or clean.request.request_id != declaration.current_clean_request_id:
            raise ValueError('fresh clean source/environment/request differs from explicit transfer declaration')
        if declaration.decision_semantics_id != decision_semantics_id(artifact.contract):
            raise ValueError('transfer cannot change frozen decision/report semantics')
        if clean.observed_setup.evidence_kind != historical.observed_setup.evidence_kind:
            raise ValueError('transfer cannot relabel synthetic evidence as empirical')
        expected = resource_transitions(artifact.contract.resource_manifest, clean.observed_setup.resources)
        if declaration.resource_changes != expected: raise ValueError('declare every historical/current resource change exactly')
        validate_fresh_scope(artifact, historical, clean)
        evidence = bool(set(artifact.context.plan.requirements.requirements) & {'direct_fact', 'evidence_retrieval'}) or any(
            c.adapter == 'evidence_v1' for c in clean.request.candidates)
        if clean.observed_setup.evidence_kind == 'empirical' and evidence and self.current_clean.evidence_validation is None:
            raise ValueError('current clean empirical Evidence setup requires its own resource-bound readiness proof')
        contract = ExecutionContract.model_validate({**artifact.contract.model_dump(),
            'resource_manifest': clean.observed_setup.resources,
            'execution_configuration_id': clean.observed_setup.resources.manifest_id})
        validate_scenario_links(clean, artifact.context, contract, self.scenarios)
        validate_report_contract(historical, (clean, *(s.bundle for s in self.scenarios)))
        historical_runs = {e.run_id for e in historical.request.examples}
        if any(e.run_id in historical_runs for s in self.scenarios for e in s.bundle.request.examples):
            raise ValueError('transfer altered condition cannot reuse historical execution IDs')
        return self


class TransferTiming(FrozenModel):
    condition: str
    rows: tuple[tuple[str, str, str, str, bool, float | None, str | None], ...]
    executed_calls: int
    unexecuted_outcomes: int
    executed_duration_sum_ms: float
    note: Literal['observed_attempt_times_not_request_latency_or_recalibrated_costs'] = 'observed_attempt_times_not_request_latency_or_recalibrated_costs'


class FrozenPolicyTransferEvaluation(FrozenUpstreamEvaluation):
    version: Literal['frozen_policy_transfer_development_v1'] = 'frozen_policy_transfer_development_v1'
    evidence_role: Literal['prepared_development_frozen_rule_transfer_only'] = 'prepared_development_frozen_rule_transfer_only'
    declaration_id: str
    historical_collector_setup: MeasurementSetup
    current_clean_collector_setup: MeasurementSetup
    historical_current_equivalence_established: Literal[False] = False
    timing: tuple[TransferTiming, ...]


def evaluate_frozen_transfer(inputs):
    """No optimizer, no new history reputation, no historical-as-current substitution."""
    import math
    inputs = FrozenPolicyTransferInput.model_validate(inputs)
    artifact = inputs.artifact
    manifest = validate_original_recordings(artifact, inputs.historical_clean, inputs.report_attacks)
    clean = inputs.current_clean.bundle
    def contract(resources):
        return ExecutionContract.model_validate({**artifact.contract.model_dump(),
            'resource_manifest': resources, 'execution_configuration_id': resources.manifest_id})
    configurations = [('historical_clean', inputs.historical_clean, artifact.contract),
                      ('current_clean', clean, contract(clean.observed_setup.resources))]
    configurations.extend((s.intervention.scenario_id, s.bundle, contract(s.intervention.altered_resources)) for s in inputs.scenarios)
    summaries, outcomes = evaluate_configurations(artifact, manifest, inputs.report_attacks, configurations)
    # A version claim is not permission to reinterpret the frozen decision rule.
    # Check retained-development parity, without claiming full source equivalence.
    original_cells = dict(summaries[0].per_strategy_metrics)
    tolerance = max(artifact.policy.solution.tolerance, 1e-12)
    coverage = (None if artifact.policy.matrix.clean_coverage is None
                else dict(artifact.policy.matrix.clean_coverage.strategy_coverage))
    for strategy, row in zip(artifact.policy.strategies, artifact.policy.matrix.values):
        metric = original_cells[strategy.strategy_id]
        if abs(metric.mean_loss-row[0]) > tolerance or (coverage is not None and
                abs(metric.decision_coverage-coverage[strategy.strategy_id]) > tolerance):
            raise ValueError('historical clean replay differs from the original frozen decision problem; unsupported decision semantics')
    timing = []
    for condition, bundle, _ in configurations:
        development = {e.example_id for e in bundle.request.examples if e.role == 'development'}
        rows = tuple((a.example_id, a.run_id, a.candidate, a.attempt_id, a.executed, a.duration_ms, a.timing_status)
                     for a in bundle.attempts if a.example_id in development)
        timing.append(TransferTiming(condition=condition, rows=rows, executed_calls=sum(r[4] for r in rows),
            unexecuted_outcomes=sum(not r[4] for r in rows),
            executed_duration_sum_ms=math.fsum(r[5] for r in rows if r[5] is not None)))
    input_id = content_id(dict(declaration=inputs.declaration.declaration_id,
        historical=scientific_bundle_id(inputs.historical_clean), current=scientific_bundle_id(clean),
        scenarios=[(s.intervention.scenario_id, scientific_bundle_id(s.bundle),
            None if s.evidence_validation is None else s.evidence_validation.validation_id) for s in inputs.scenarios],
        current_readiness=None if inputs.current_clean.evidence_validation is None else inputs.current_clean.evidence_validation.validation_id))
    return FrozenPolicyTransferEvaluation(evaluation_input_id=input_id, declaration_id=inputs.declaration.declaration_id,
        original_artifact_id=artifact.artifact_id, original_policy_id=artifact.policy.policy_id,
        original_compatibility_id=artifact.context.compatibility_id, original_policy_version=artifact.policy.version,
        evidence_kind=artifact.policy.provenance.evidence_kind,
        original_reputation_snapshot_id=artifact.context.reputation_snapshot_id, original_threshold=artifact.contract.threshold,
        original_minimum_participants=artifact.context.minimum_participant_count, configured_cost_units=artifact.context.cost_units,
        configured_resource_weight=artifact.context.loss_configuration.resource_weight, strategies=artifact.policy.strategies,
        strategy_probabilities=artifact.policy.solution.probabilities,
        original_clean_coverage_floor=None if artifact.policy.matrix.clean_coverage is None else artifact.policy.matrix.clean_coverage.minimum,
        historical_collector_setup=inputs.historical_clean.observed_setup, current_clean_collector_setup=clean.observed_setup,
        scenario_metrics=summaries, outcomes=outcomes, timing=tuple(timing))


def prepare_transfer(artifact, historical, report_attacks, current_setup, source_files, *, authorization_record,
                     implementation_change_record, report_compatibility_record, source_snapshot_record):
    """Metadata-only preparation. No fabricated reports, history or resource IDs."""
    artifact = PolicyArtifact.model_validate(artifact)
    historical = RecordingBundle.model_validate(historical)
    report_attacks = AttackSpecification.model_validate(report_attacks)
    current_setup = MeasurementSetup.model_validate(current_setup)
    validate_original_recordings(artifact, historical, report_attacks)
    if current_setup.evidence_kind != historical.observed_setup.evidence_kind:
        raise ValueError('transfer cannot relabel synthetic evidence as empirical')
    request = historical.request.model_dump()
    request.update(expected_setup=current_setup, execution_configuration_id=current_setup.resources.manifest_id,
        preparation_authorization=authorization_record, study_approval=authorization_record,
        examples=[{**e.model_dump(), 'run_id': content_id(['transfer_clean_run_v1', artifact.artifact_id,
            current_setup.fingerprint, authorization_record, e.run_id])} for e in historical.request.examples if e.role == 'development'])
    request = RecordingRequest.model_validate(request)
    declaration = EvaluationTransferDeclaration(version='frozen_policy_evaluation_transfer_v1',
        original_artifact_id=artifact.artifact_id, historical_recording_id=scientific_bundle_id(historical),
        historical_setup_fingerprint=historical.observed_setup.fingerprint, current_clean_setup=current_setup,
        current_clean_request_id=request.request_id, current_source_files=source_files,
        decision_semantics_id=decision_semantics_id(artifact.contract), report_contract='verification_result_existing_vote_adapters_v1',
        equivalence='not_established_original_source_unavailable', authorization_record=authorization_record,
        implementation_change_record=implementation_change_record, report_compatibility_record=report_compatibility_record,
        source_snapshot_record=source_snapshot_record, resource_changes=resource_transitions(artifact.contract.resource_manifest, current_setup.resources),
        scope='original_prepared_development_examples_only', historical_clean_use='separate_reference_never_new_clean_substitution')
    current_setup.resources.require_candidates(c.verifier_name for c in request.candidates)
    return declaration, request
