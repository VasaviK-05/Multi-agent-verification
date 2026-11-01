"""Development-only evaluation of a frozen policy; no fitting or deployment export."""
from collections import Counter
import math
from typing import Literal

from pydantic import Field, model_validator

from app.game.artifacts import PolicyArtifact
from app.game.dependencies import FrozenModel
from app.game.execution_contract import ExecutionContract
from app.game.models import PlanningContext, Strategy, canonical_json, content_id
from app.game.offline.attacks import AttackSpecification, enumerate_attacks
from app.game.offline.collection import RecordingBundle, export_training
from app.game.offline.evaluation import Metrics, bind_evaluation, summarize
from app.game.offline.records import Example
from app.game.offline.replay import ReplayOutcome, replay
from app.game.offline.upstream import (ScenarioRecording, require_execution_records,
    scientific_bundle_id, validate_scenario_links)


def audit_collector_source(expected_setup, collector_root):
    """Read-only source rehearsal; no imports from the candidate app or resources.

    This is not a resource preflight or permission to collect. Hash actual source
    bytes (including dirty/untracked .py files), exactly as the project adapter does.
    """
    import hashlib
    import os
    from pathlib import Path
    import subprocess
    from app.game.offline.calibration import MeasurementSetup
    expected_setup = MeasurementSetup.model_validate(expected_setup)
    root = Path(collector_root).resolve()
    gaps = []
    revision = None
    if any(os.environ.get(k) for k in ('GIT_DIR', 'GIT_WORK_TREE', 'GIT_INDEX_FILE')):
        raise ValueError('unset Git directory/worktree/index overrides before auditing the actual collector checkout')
    try:
        top = Path(subprocess.check_output(['git', 'rev-parse', '--show-toplevel'], cwd=root,
                                         text=True, stderr=subprocess.PIPE).strip()).resolve()
        if top != root:
            gaps.append('collector_root_is_not_its_own_git_worktree')
        revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root,
                                           text=True, stderr=subprocess.PIPE).strip()
    except (OSError, subprocess.CalledProcessError):
        gaps.append('collector_git_revision_unavailable')
    if revision != expected_setup.code_revision:
        gaps.append('collector_code_revision_mismatch')
    files = []
    if not (root / 'app').is_dir():
        gaps.append('collector_application_source_unavailable')
    else:
        for path in sorted((root / 'app').rglob('*.py')):
            files.append((path.relative_to(root).as_posix(), hashlib.sha256(path.read_bytes()).hexdigest()))
    digest = content_id(files)
    if digest != expected_setup.application_source_digest:
        gaps.append('collector_application_source_digest_mismatch')
    return dict(version='frozen_collector_source_audit_v1', source_compatible=not gaps,
        ready_for_real_collection=False, factory_initialized=False, gaps=gaps,
        expected_code_revision=expected_setup.code_revision, actual_code_revision=revision,
        expected_application_source_digest=expected_setup.application_source_digest,
        actual_application_source_digest=digest, source_files=files,
        required_environment=expected_setup.environment, required_dependency_versions=expected_setup.dependency_versions,
        remaining_checks=['matching environment/dependencies and original clean resource preflight',
                          'isolated altered-resource preflight and resource-bound Evidence probes',
                          'study authorization, declaration and full-roster collection rehearsal'])


def unbound_replay_context(artifact, contract):
    """Drop fitting obligations only in a temporary, non-deployable replay view.

    Per-example decision inputs (plan, reputation, threshold, contributors,
    coverage semantics, costs/budget) are retained. No policy is built for this view.
    """
    contract = ExecutionContract.model_validate(contract)
    resource_fields = {'resource_manifest', 'execution_configuration_id'}
    if contract.model_dump(exclude=resource_fields) != artifact.contract.model_dump(exclude=resource_fields):
        raise ValueError('experimental replay may change only execution resource identities, never decision semantics')
    return PlanningContext.model_validate({**artifact.context.model_dump(),
        'clean_coverage_json': None, 'reliability_first_json': None,
        'offline_evaluation_id': None,
        'execution_contract_json': canonical_json(contract.model_dump(mode='json'))})


def validate_original_recordings(artifact, clean, report_attacks):
    """Reconstruct the original training binding without optimizing or altering it."""
    if artifact.context.pooling_contract_json is not None:
        raise ValueError('pooled frozen evaluation requires an explicit multi-context evaluation contract')
    if artifact.contract.resource_manifest is None:
        raise ValueError('frozen upstream evaluation requires resource-bound execution')
    base = unbound_replay_context(artifact, artifact.contract)
    manifest = export_training(clean, base)
    require_execution_records(clean)
    try:
        bound = bind_evaluation(base, manifest, artifact.contract, report_attacks)
    except ValueError as exc:
        raise ValueError('clean recordings differ from the original frozen training binding: ' + str(exc)) from exc
    expected = PlanningContext.model_validate({**artifact.context.model_dump(),
        'clean_coverage_json': None, 'reliability_first_json': None})
    if bound != expected:
        raise ValueError('clean recordings differ from the original frozen training binding; scope cannot expand')
    actions = enumerate_attacks(base.dependencies, report_attacks)
    if artifact.policy.matrix.attack_ids != tuple(a.attack_id for a in actions):
        raise ValueError('original report-attack specification differs from frozen artifact')
    return manifest


class FrozenUpstreamEvaluationInput(FrozenModel):
    version: Literal['frozen_upstream_development_input_v1'] = 'frozen_upstream_development_input_v1'
    artifact: PolicyArtifact
    clean: RecordingBundle
    report_attacks: AttackSpecification
    scenarios: tuple[ScenarioRecording, ...] = Field(min_length=1)

    @model_validator(mode='after')
    def check(self):
        validate_original_recordings(self.artifact, self.clean, self.report_attacks)
        artifact = self.artifact
        validate_scenario_links(self.clean, artifact.context, artifact.contract, self.scenarios)
        return self

    @property
    def evaluation_input_id(self):
        return content_id(dict(version=self.version, artifact_id=self.artifact.artifact_id,
            clean=scientific_bundle_id(self.clean), report_attacks=self.report_attacks.model_dump(mode='json'),
            scenarios=[dict(intervention=s.intervention.model_dump(mode='json'), bundle=scientific_bundle_id(s.bundle),
                            evidence_validation_id=None if s.evidence_validation is None else s.evidence_validation.validation_id)
                       for s in self.scenarios]))


class FrozenScenarioMetrics(FrozenModel):
    scenario_id: str
    resource_manifest_id: str
    request_id: str
    recording_id: str
    metrics: Metrics
    validation_loss: float
    uncertainty_rate: float
    # Diagnostic only, including for lexicographic/reliability-first originals.
    configured_cost_inclusive_diagnostic: float
    expected_failed_attempts_per_example: float
    expected_unavailable_attempts_per_example: float
    expected_unresolved_requirements_per_example: float
    expected_reason_counts: tuple[tuple[str, float], ...]
    per_strategy_metrics: tuple[tuple[str, Metrics], ...]
    per_strategy_validation_loss: tuple[tuple[str, float], ...]
    per_strategy_reason_counts: tuple[tuple[str, tuple[tuple[str, int], ...]], ...]


class FrozenUpstreamEvaluation(FrozenModel):
    version: Literal['frozen_upstream_development_evaluation_v1'] = 'frozen_upstream_development_evaluation_v1'
    evidence_role: Literal['prepared_development_only'] = 'prepared_development_only'
    evaluation_input_id: str
    original_artifact_id: str
    original_policy_id: str
    original_compatibility_id: str
    original_policy_version: str
    evidence_kind: str
    original_reputation_snapshot_id: str
    original_threshold: float
    original_minimum_participants: int
    configured_cost_units: str
    configured_resource_weight: float
    original_certificate_scope: Literal['original_fitted_problem_only'] = 'original_fitted_problem_only'
    original_certificate_validated: Literal[True] = True
    new_scenario_optimality_claim: Literal[False] = False
    strategy_probabilities: tuple[tuple[str, float], ...]
    strategies: tuple[Strategy, ...]
    original_clean_coverage_floor: float | None
    original_artifact_sha256: str | None = None  # Supplied by the CLI from original input bytes.
    prototype_bundle_id: str | None = None
    scenario_metrics: tuple[FrozenScenarioMetrics, ...]
    outcomes: tuple[ReplayOutcome, ...]


def evaluate_configurations(artifact, manifest, report_attacks, configurations):
    """Shared pure replay; callers validate condition identity/provenance first."""
    probabilities = dict(artifact.policy.solution.probabilities)
    base = unbound_replay_context(artifact, artifact.contract)
    clean_action = enumerate_attacks(base.dependencies, report_attacks)[0]
    summaries, outcomes = [], []
    for scenario_id, bundle, contract in configurations:
        # No evaluated offline binding: DeploymentEpisode explicitly rejects this
        # context. The original policy/context/certificate remain unchanged.
        context = unbound_replay_context(artifact, contract)
        examples = {e.example_id: e for e in bundle.request.examples if e.role == 'development'}
        attempts = {}
        for row in bundle.attempts:
            if row.example_id in examples:
                attempts.setdefault(row.example_id, []).append(row.attempt)
        weighted, per_strategy, per_reasons = [], [], []
        for strategy in artifact.policy.strategies:
            cell = []
            for original in manifest.partition('development').examples:
                example = Example.model_validate({**original.model_dump(),
                    'validation_id': examples[original.example_id].run_id,
                    'execution_configuration_id': contract.execution_configuration_id,
                    'attempts': attempts[original.example_id]})
                outcome = replay(context, strategy, clean_action, report_attacks, contract, example)
                outcome = ReplayOutcome.model_validate({**outcome.model_dump(), 'attack_id': scenario_id, 'audit': ()})
                cell.append(outcome)
            outcomes.extend(cell)
            weighted.extend((o, probabilities[strategy.strategy_id]) for o in cell)
            per_strategy.append((strategy.strategy_id, summarize(tuple((o, 1.) for o in cell), artifact.context.loss_configuration)))
            reasons = Counter(reason for o in cell for reason in o.reasons)
            per_reasons.append((strategy.strategy_id, tuple(sorted(reasons.items()))))
        metrics = summarize(tuple(weighted), artifact.context.loss_configuration)
        n = metrics.examples
        reason_names = sorted({r for o, _ in weighted for r in o.reasons})
        summaries.append(FrozenScenarioMetrics(scenario_id=scenario_id,
            resource_manifest_id=contract.resource_manifest.manifest_id,
            request_id=bundle.request.request_id, recording_id=scientific_bundle_id(bundle), metrics=metrics,
            validation_loss=metrics.validation_loss(artifact.context.loss_configuration),
            uncertainty_rate=metrics.uncertainty_rate, configured_cost_inclusive_diagnostic=metrics.mean_loss,
            expected_failed_attempts_per_example=math.fsum(w * sum(state == 'failed' for _, state in o.execution_states) for o, w in weighted) / n,
            expected_unavailable_attempts_per_example=math.fsum(w * sum(state == 'unavailable' for _, state in o.execution_states) for o, w in weighted) / n,
            expected_unresolved_requirements_per_example=math.fsum(w * len(o.unresolved) for o, w in weighted) / n,
            expected_reason_counts=tuple((reason, math.fsum(w for o, w in weighted if reason in o.reasons)) for reason in reason_names),
            per_strategy_metrics=tuple(per_strategy),
            per_strategy_validation_loss=tuple((sid, m.validation_loss(artifact.context.loss_configuration)) for sid, m in per_strategy),
            per_strategy_reason_counts=tuple(per_reasons)))
    return tuple(summaries), tuple(outcomes)


def evaluate_frozen_upstream(inputs):
    """Exact expectation over all frozen strategies; no sampling or optimization."""
    inputs = FrozenUpstreamEvaluationInput.model_validate(inputs)
    artifact = inputs.artifact
    probabilities = dict(artifact.policy.solution.probabilities)
    base = unbound_replay_context(artifact, artifact.contract)
    manifest = export_training(inputs.clean, base)
    clean_action = enumerate_attacks(base.dependencies, inputs.report_attacks)[0]
    configurations = [('clean', inputs.clean, artifact.contract)]
    for scenario in inputs.scenarios:
        resources = scenario.intervention.altered_resources
        contract = ExecutionContract.model_validate({**artifact.contract.model_dump(),
            'resource_manifest': resources, 'execution_configuration_id': resources.manifest_id})
        configurations.append((scenario.intervention.scenario_id, scenario.bundle, contract))
    summaries, outcomes = evaluate_configurations(artifact, manifest, inputs.report_attacks, configurations)
    floor = None
    if artifact.policy.matrix.clean_coverage is not None:
        floor = artifact.policy.matrix.clean_coverage.minimum
    return FrozenUpstreamEvaluation(evaluation_input_id=inputs.evaluation_input_id,
        original_artifact_id=artifact.artifact_id, original_policy_id=artifact.policy.policy_id,
        original_compatibility_id=artifact.context.compatibility_id, original_policy_version=artifact.policy.version,
        evidence_kind=artifact.policy.provenance.evidence_kind,
        original_reputation_snapshot_id=artifact.context.reputation_snapshot_id,
        original_threshold=artifact.contract.threshold,
        original_minimum_participants=artifact.context.minimum_participant_count,
        configured_cost_units=artifact.context.cost_units,
        configured_resource_weight=artifact.context.loss_configuration.resource_weight,
        strategy_probabilities=artifact.policy.solution.probabilities,
        strategies=artifact.policy.strategies,
        original_clean_coverage_floor=floor, scenario_metrics=tuple(summaries), outcomes=tuple(outcomes))
