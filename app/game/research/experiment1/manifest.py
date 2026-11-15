"""Outcome-free retrospective manifest, identities, and pure readiness gates."""
import hashlib
import importlib.metadata
import platform
from pathlib import Path
from typing import Annotated, Literal

from pydantic import Field, model_validator

from app.game.dependencies import FrozenModel
from app.game.models import PayoffMatrix, SolverResult, content_id
from app.game.offline.attacks import enumerate_attacks
from app.game.offline.compound import Training
from app.game.research.comparison import FrozenComparison, METHODS, validate_frozen
from app.game.research.component_comparison import FrozenComponentComparison
from app.game.research.specification import PolicyBuildSpecification
from app.game.research.experiment1.metrics import Statistics

COHORTS = ('arithmetic', 'factual', 'original_semantic', 'compound', 'reference')
RULES = {
    'full_minimax': 'exact_existing_frozen_probabilities_no_refit',
    'coverage_aware_greedy': 'captured_initial_selected_declared_aggregation_complete_team',
    'deterministic_minimax': 'development_coverage_eligible_minimax_validation_then_cost_then_id',
    'clean_development': 'development_coverage_eligible_clean_validation_then_cost_then_id',
    'uniform': 'exact_uniform_over_feasible_rows_report_floor_compliance',
    'fixed_reputation_weighted': 'development_restricted_game_preserve_coverage_and_objective',
    'fixed_dependency_group': 'development_restricted_game_preserve_coverage_and_objective',
}


def reporting_environment():
    return dict(python=platform.python_version(), **{name: importlib.metadata.version(name)
        for name in ('numpy', 'scipy', 'pydantic')})


def atomic_bindings(spec, comparison):
    artifact = comparison.full_artifact
    return dict(policy_id=artifact.policy.policy_id, artifact_id=artifact.artifact_id,
        comparison_id=comparison.comparison_id, specification_id=spec.specification_id,
        context_id=artifact.context.compatibility_id, contract_id=content_id(artifact.contract.model_dump(mode='json')),
        resource_id=artifact.execution_configuration_id, reputation_id=artifact.context.reputation_snapshot_id,
        training_id=spec.manifest.manifest_id, reservation_id=spec.manifest.final_test_reservation.reservation_id,
        datasets={p.role: p.dataset_id for p in (*spec.manifest.partitions, spec.manifest.final_test_reservation)},
        groups={p.role: sorted([e.example_id, e.split_identity] for e in p.examples)
                for p in (*spec.manifest.partitions, spec.manifest.final_test_reservation)},
        attack_specification_id=spec.attacks.specification_id,
        actions=[a.model_dump(mode='json') | {'attack_id': a.attack_id} for a in enumerate_attacks(spec.context.dependencies, spec.attacks)],
        strategies=[s.model_dump(mode='json') for s in artifact.policy.strategies],
        method_rules=RULES, floor_amendment=('post_development_50_percent' if
            spec.context.provenance.history_dataset == 'reference-fresh-v1-history' else None))


class AtomicEntry(FrozenModel):
    kind: Literal['atomic'] = 'atomic'
    cohort: Literal['arithmetic', 'factual', 'reference']
    specification: PolicyBuildSpecification
    comparison: FrozenComparison
    bindings: dict

    @model_validator(mode='after')
    def check(self):
        if self.bindings != atomic_bindings(self.specification, self.comparison):
            raise ValueError('atomic manifest identities or method rules differ from frozen inputs')
        if (self.comparison.full_artifact.context != self.specification.context
                or self.comparison.full_artifact.contract != self.specification.contract
                or self.comparison.manifest_id != self.specification.manifest.manifest_id
                or self.comparison.specification_id != self.specification.specification_id):
            raise ValueError('atomic specification/comparison mismatch')
        if self.specification.context.provenance.evidence_kind == 'empirical':
            expected = {'arithmetic': ('arithmetic',), 'factual': ('direct_fact',), 'reference': ('semantic_comparison',)}[self.cohort]
            if tuple(self.specification.context.plan.requirements.requirements) != expected:
                raise ValueError('empirical cohort label differs from declared task')
        return self


def component_bindings(training, comparison):
    policy = comparison.full_policy
    from app.game.component_execution import enumerate_component_strategies
    return dict(policy_id=policy.policy_id, comparison_id=comparison.comparison_id,
        contract_id=policy.contract.compatibility_id, training_id=training.binding_id,
        resource_id=training.setup.resources.manifest_id, study_id=training.study.study_id,
        datasets={role: getattr(policy.contract.obligations[0].context.provenance, role + '_dataset')
                  for role in ('history', 'development', 'final_test')},
        groups=[g.model_dump(mode='json') for g in training.study.groups],
        joint_reservation_id=policy.joint_development.final_test_reservation_id if policy.joint_development else None,
        attack_specification_id=training.study.attack_specification.specification_id,
        actions=[a.model_dump(mode='json') | {'attack_id': a.attack_id} for a in enumerate_attacks(training.study.dependencies, training.study.attack_specification)],
        strategies=[s.model_dump(mode='json') for s in enumerate_component_strategies(policy.contract)],
        method_rules=RULES, floor_amendment=policy.contract.fitting_configuration.model_dump(mode='json')
            if policy.contract.fitting_configuration else None)


class ComponentEntry(FrozenModel):
    kind: Literal['component'] = 'component'
    cohort: Literal['compound'] = 'compound'
    training: Training
    comparison: FrozenComponentComparison
    bindings: dict
    original_freeze_id: str = Field(pattern=r'^[0-9a-f]{64}$')
    resource_transfer: dict | None = None

    @model_validator(mode='after')
    def check(self):
        if self.resource_transfer is not None:
            from app.game.offline.calibration import MeasurementSetup
            transfer = self.resource_transfer
            policy = self.comparison.full_policy
            setup = MeasurementSetup.model_validate(transfer.get('scoped_setup'))
            # Contract resources, not candidate names, determine required scope.
            required = {v.verifier_name for o in policy.contract.obligations for v in o.contract.resource_manifest.verifiers}
            expected = tuple(v for v in self.training.setup.resources.verifiers if v.verifier_name in required)
            if (transfer.get('transfer_id') != content_id({k:v for k,v in transfer.items() if k != 'transfer_id'})
                    or transfer.get('version') != 'compound_required_resource_transfer_v1'
                    or transfer.get('original_policy_id') != policy.policy_id
                    or transfer.get('original_freeze_id') != self.original_freeze_id
                    or transfer.get('original_full_resource_id') != self.training.setup.resources.manifest_id
                    or transfer.get('study_id') != self.training.study.study_id
                    or setup.resources.verifiers != expected
                    or setup.evidence_kind != self.training.setup.evidence_kind
                    or transfer.get('scope') != sorted(required)
                    or transfer.get('scoped_resource_id') != setup.resources.manifest_id):
                raise ValueError('component resource transfer is not the exact frozen required-resource projection')
        if (self.training.binding_id != self.comparison.training_binding_id or
                self.bindings != component_bindings(self.training, self.comparison)):
            raise ValueError('component manifest training/identities differ from frozen inputs')
        return self


class InfeasibleEntry(FrozenModel):
    kind: Literal['infeasible'] = 'infeasible'
    cohort: Literal['original_semantic'] = 'original_semantic'
    matrix: PayoffMatrix
    solution: SolverResult
    explanation: str

    @model_validator(mode='after')
    def check(self):
        q = self.matrix.clean_coverage
        if (self.solution.status != 'infeasible' or self.solution.probabilities
                or self.solution.matrix_id != self.matrix.matrix_id or q is None or q.minimum != .9
                or max(v for _, v in q.strategy_coverage) >= q.minimum):
            raise ValueError('original Semantic requires the existing infeasible 90% game, no probabilities')
        return self


class BlockedEntry(FrozenModel):
    kind: Literal['blocked'] = 'blocked'
    cohort: Literal['arithmetic', 'factual', 'original_semantic', 'compound', 'reference']
    reason: str = Field(min_length=1)
    expected_policy_id: str | None = Field(default=None, pattern=r'^[0-9a-f]{64}$')


Entry = Annotated[AtomicEntry | ComponentEntry | InfeasibleEntry | BlockedEntry, Field(discriminator='kind')]


class ExperimentManifest(FrozenModel):
    version: Literal['retrospective_experiment1_v1'] = 'retrospective_experiment1_v1'
    experiment_id: str = Field(min_length=1)
    status: Literal['retrospective_exploratory'] = 'retrospective_exploratory'
    interpretation: Literal['previously_exposed_tests_no_new_confirmatory_claim'] = 'previously_exposed_tests_no_new_confirmatory_claim'
    source_commit: str = Field(pattern=r'^[0-9a-f]{40}$')
    source_fingerprint: str = Field(pattern=r'^[0-9a-f]{64}$')
    statistics: Statistics = Statistics()
    reporting_environment: dict[str, str] = Field(default_factory=reporting_environment)
    cohorts: tuple[Entry, ...]
    pooling: Literal['forbidden_report_each_cohort_separately'] = 'forbidden_report_each_cohort_separately'

    @model_validator(mode='after')
    def check(self):
        if len({c.cohort for c in self.cohorts}) != len(self.cohorts):
            raise ValueError('duplicate cohort')
        for entry in self.cohorts:
            if isinstance(entry, AtomicEntry) and (entry.specification.code_revision != self.source_commit
                    or entry.comparison.code_revision != self.source_commit):
                raise ValueError('atomic source revision differs from experiment source')
        return self

    @property
    def manifest_id(self):
        return content_id(self.model_dump(mode='json'))


def source_fingerprint(root):
    """Bind executable source bytes, including uncommitted Phase A/Phase 1 files."""
    root = Path(root)
    paths = sorted([*(root / 'app').rglob('*.py'), *(root / 'scripts').glob('*.py')])
    return content_id([(p.relative_to(root).as_posix(), hashlib.sha256(p.read_bytes()).hexdigest()) for p in paths])


def readiness(manifest, *, actual_commit, actual_source_fingerprint, source_root=None):
    """No replay, optimization, model/service requests, test payloads, or writes."""
    manifest = ExperimentManifest.model_validate(manifest)
    blockers, cohorts = [], []
    if manifest.reporting_environment != reporting_environment():
        blockers.append('reporting_environment_mismatch')
    if manifest.source_commit != actual_commit:
        blockers.append('source_commit_mismatch')
    if manifest.source_fingerprint != actual_source_fingerprint:
        blockers.append('source_bytes_mismatch')
    missing = sorted(set(COHORTS) - {c.cohort for c in manifest.cohorts})
    if missing:
        blockers.append('missing_cohort_dispositions:' + ','.join(missing))
    for entry in manifest.cohorts:
        issues = []
        if isinstance(entry, BlockedEntry):
            issues.append(entry.reason)
        elif isinstance(entry, AtomicEntry):
            try:
                validate_frozen(entry.specification, entry.comparison, actual_code_revision=actual_commit)
            except ValueError as exc:
                issues.append(str(exc))
        elif isinstance(entry, ComponentEntry) and entry.resource_transfer is not None:
            if source_root is None:
                issues.append('transfer_source_verification_requires_repository_root')
            else:
                root = Path(source_root).resolve()
                hashes = entry.resource_transfer.get('code_hashes', {})
                if not hashes:
                    issues.append('missing_transfer_source_hashes')
                for relative, expected in hashes.items():
                    path = (root / relative).resolve()
                    if not path.is_relative_to(root) or not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
                        issues.append('transfer_source_hash_mismatch:' + relative)
        # ComponentEntry validates Training, policy certificates, bindings and
        # resource observations on parse; it never substitutes atomic replay.
        cohorts.append(dict(cohort=entry.cohort, kind=entry.kind, ready=not issues,
            blockers=issues, unavailable_methods=[m.model_dump(mode='json') for m in
                getattr(getattr(entry, 'comparison', None), 'unavailable_methods', ())]))
        blockers.extend(entry.cohort + ':' + issue for issue in issues)
    return dict(ready=not blockers, manifest_id=manifest.manifest_id,
        status=manifest.status, cohorts=cohorts, blockers=blockers,
        statistics=manifest.statistics.model_dump(), final_payloads_read=False,
        inference_calls=0, optimization_calls=0)
