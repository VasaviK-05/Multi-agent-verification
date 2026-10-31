"""Opt-in, development-only upstream interventions; never report transformations.

Deployment uses the clean execution contract. Experimental resources exist only
in the separately retained experiment, whose digest binds the fitted matrix.
"""
from typing import Literal

from pydantic import Field, model_validator

from app.game.dependencies import FrozenModel, identifier
from app.game.models import PlanningContext, PayoffMatrix, canonical_json, content_id
from app.game.resource_provenance import ResourceManifest
from app.game.execution_contract import ExecutionContract
from app.game.artifacts import PolicyArtifact, artifact_version
from app.game.policy import build_policy
from app.game.strategies import enumerate_strategies
from app.game.offline.attacks import AttackSpecification, enumerate_attacks
from app.game.offline.calibration import Text
from app.game.offline.collection import RecordingBundle, RecordingRequest, completeness, export_training
from app.game.offline.evaluation import bind_evaluation, summarize
from app.game.offline.records import Example
from app.game.offline.replay import replay
from app.game.research.specification import PolicyBuildSpecification
from app.game.research.evidence_validation import EvidenceValidation


def require_execution_records(bundle):
    """A prerequisite/factory exclusion is not a fabricated verifier return."""
    import json
    for row in bundle.attempts:
        if row.executed:
            continue
        if row.attempt.state != 'unavailable':
            raise ValueError('unexecuted outcomes may only record explicit unavailability, never returned reports')
        try:
            provenance = json.loads(row.attempt.report_provenance)
        except ValueError as exc:
            raise ValueError('unexecuted unavailability requires collector provenance') from exc
        if not isinstance(provenance, dict) or not provenance.get('error_or_unavailability'):
            raise ValueError('unexecuted unavailability requires an explicit prerequisite/factory reason')


def scenario_request(clean_request, altered_setup, *, name, preparation_authorization, study_approval):
    """Prepare a new development-only request; dispatch remains in the collector.

    Approval of an old clean study is deliberately not inherited as approval of
    the new intervention. Callers explicitly supply the authority for this run.
    """
    from app.game.offline.calibration import MeasurementSetup
    identifier(name)
    clean_request = RecordingRequest.model_validate(clean_request)
    altered_setup = MeasurementSetup.model_validate(altered_setup)
    if clean_request.expected_setup is None or clean_request.expected_setup.resources == altered_setup.resources:
        raise ValueError('scenario needs known clean and distinct altered resources')
    request = clean_request.model_dump()
    request.update(expected_setup=altered_setup,
        execution_configuration_id=altered_setup.resources.manifest_id,
        preparation_authorization=preparation_authorization, study_approval=study_approval,
        examples=[{**e.model_dump(), 'run_id': content_id(['upstream_run_v1', name,
            altered_setup.resources.manifest_id, e.run_id])}
            for e in clean_request.examples if e.role == 'development'])
    return RecordingRequest.model_validate(request)


def scientific_bundle_id(bundle):
    """Exclude measured durations, retain reports and every resource observation."""
    rows = []
    for row in bundle.attempts:
        data = row.model_dump(mode='json')
        data.pop('duration_ms')
        data.pop('measurement')
        rows.append(data)
    return content_id(dict(request=bundle.request.model_dump(mode='json'),
        setup=bundle.observed_setup.model_dump(mode='json'), attempts=rows))


class EvidenceIntervention(FrozenModel):
    version: Literal['upstream_evidence_intervention_v1']
    name: Text
    affected_resource: Text
    alteration: Text
    scope: Text
    provenance: Text
    clean_resources: ResourceManifest
    altered_resources: ResourceManifest
    affected_verifiers: tuple[Text, ...] = Field(min_length=1)
    # An explicit restricted threat model. Adaptive attacks need a new contract.
    timing: Literal['committed_before_collection_and_team_sampling']
    knowledge: Literal['public_questions_references_and_clean_resources_no_labels_no_sampled_team']
    reuse_contract: Literal['complete_team_independent_within_fixed_scenario_v1']
    reuse_attestation: Text
    request_id: Text
    clean_adapter_json: str | None = None
    altered_adapter_json: str | None = None

    @model_validator(mode='after')
    def check(self):
        clean = {v.verifier_name: v for v in self.clean_resources.verifiers}
        altered = {v.verifier_name: v for v in self.altered_resources.verifiers}
        if clean.keys() != altered.keys():
            raise ValueError('intervention must retain the exact candidate resource roster')
        changed = []
        targeted = False
        configuration_changes = []
        for name in clean:
            if clean[name] == altered[name]:
                continue
            changed.append(name)
            before = {(r.kind, r.resource_id): r.sha256 for r in clean[name].resources}
            after = {(r.kind, r.resource_id): r.sha256 for r in altered[name].resources}
            if before.keys() != after.keys():
                raise ValueError('retain logical resource IDs; bind altered bytes with different digests')
            corpus_changed = any(k[0] == 'corpus' and before[k] != after[k] for k in before)
            if corpus_changed and any(k[0] == 'index' for k in before) and not any(
                    k[0] == 'index' and before[k] != after[k] for k in before):
                raise ValueError('changed corpus requires a separately rebuilt and observed index')
            for key in before:
                if before[key] != after[key]:
                    if key[0] not in {'corpus', 'index', 'configuration'}:
                        raise ValueError('isolated corpus intervention cannot change algorithms/models/services')
                    if key[0] == 'corpus' and key[1] != self.affected_resource:
                        raise ValueError('undeclared additional corpus intervention')
                    if key[0] == 'configuration':
                        configuration_changes.append((before[key], after[key]))
                    targeted |= key == ('corpus', self.affected_resource)
        if (not targeted or len(set(self.affected_verifiers)) != len(self.affected_verifiers)
                or set(changed) != set(self.affected_verifiers)):
            raise ValueError('declare the changed corpus and every actually affected verifier')
        if configuration_changes or self.clean_adapter_json is not None or self.altered_adapter_json is not None:
            from app.benchmark.project_adapter import AdapterConfiguration
            if self.clean_adapter_json is None or self.altered_adapter_json is None:
                raise ValueError('changed adapter configuration requires explicit clean/altered configuration payloads')
            before = AdapterConfiguration.model_validate_json(self.clean_adapter_json)
            after = AdapterConfiguration.model_validate_json(self.altered_adapter_json)
            paths = {'corpus_path', 'index_dir', 'index_receipt', 'service_observation'}
            if before.model_dump(exclude=paths) != after.model_dump(exclude=paths):
                raise ValueError('isolated intervention cannot change sampling/model/execution settings')
            if before.corpus_path == after.corpus_path or before.index_dir == after.index_dir:
                raise ValueError('altered corpus/index need separate experimental paths')
            excluded = {'embedding_snapshot', 'nli_snapshot', 'index_receipt', 'service_observation'}
            expected = (content_id(before.model_dump(exclude=excluded)), content_id(after.model_dump(exclude=excluded)))
            if any(pair != expected for pair in configuration_changes):
                raise ValueError('configuration fingerprints differ from supplied project adapter configurations')
            for name in clean:
                before_config = [r.sha256 for r in clean[name].resources if r.kind == 'configuration']
                after_config = [r.sha256 for r in altered[name].resources if r.kind == 'configuration']
                if before_config != [expected[0]] or after_config != [expected[1]]:
                    raise ValueError('every project adapter entry must bind its actual configuration, including shared path changes')
        return self

    @property
    def scenario_id(self):
        return content_id(self.model_dump(mode='json'))


class ScenarioRecording(FrozenModel):
    intervention: EvidenceIntervention
    bundle: RecordingBundle
    evidence_validation: EvidenceValidation | None = None

    @model_validator(mode='after')
    def check(self):
        request = self.bundle.request
        if type(request) is not RecordingRequest or request.intended_use == 'smoke':
            raise ValueError('scenario needs labelled pilot/study recordings, not diagnostic/smoke')
        if request.request_id != self.intervention.request_id:
            raise ValueError('scenario request identity mismatch')
        if request.factory in {'app.benchmark.project_adapter:create_recording_verifiers',
                               'app.game.offline.recording_adapters:project_factory'}:
            if self.intervention.clean_adapter_json is None or self.intervention.altered_adapter_json is None:
                raise ValueError('project scenario requires explicit clean/altered configurations proving separate resource paths')
        if any(e.role != 'development' for e in request.examples):
            raise ValueError('altered-resource collection is development only; no history/final-test')
        if (self.bundle.observed_setup is None
                or self.bundle.observed_setup.resources != self.intervention.altered_resources
                or request.expected_setup != self.bundle.observed_setup):
            raise ValueError('scenario must bind its exact observed altered-resource setup')
        gaps = completeness(self.bundle)
        if not gaps['complete']:
            raise ValueError('scenario recording incomplete: ' + canonical_json(gaps['gaps']))
        require_execution_records(self.bundle)
        if self.evidence_validation is not None:
            self.evidence_validation.require_resources(self.intervention.altered_resources)
        return self


def validate_scenario_links(clean, context, contract, scenarios):
    """Shared identity/resource validation, independent of any fitting objective."""
    if contract.resource_manifest is None:
        raise ValueError('upstream experiments require resource-bound execution')
    if len({s.intervention.scenario_id for s in scenarios}) != len(scenarios):
        raise ValueError('duplicate scenario')
    clean_request = clean.request
    expected = {e.example_id: e for e in clean_request.examples if e.role == 'development'}
    used_runs = {e.run_id for e in clean_request.examples}
    for scenario in scenarios:
        intervention, bundle = scenario.intervention, scenario.bundle
        request = bundle.request
        if intervention.clean_resources != contract.resource_manifest:
            raise ValueError('scenario clean resources differ from deployment resources')
        evidence_required = bool(set(context.plan.requirements.requirements) & {'direct_fact', 'evidence_retrieval'}) or any(
            c.adapter == 'evidence_v1' for c in request.candidates)
        if clean.observed_setup.evidence_kind == 'empirical' and evidence_required:
            if scenario.evidence_validation is None:
                raise ValueError('empirical scenario requires existing resource-bound EvidenceValidation probes')
            scenario.evidence_validation.require_resources(intervention.altered_resources)
        if (request.candidates != clean_request.candidates
                or request.factory != clean_request.factory
                or request.final_test_reservation != clean_request.final_test_reservation
                or request.permitted_datasets != clean_request.permitted_datasets
                or request.randomness_control != clean_request.randomness_control):
            raise ValueError('scenario roster/reservation/dataset/randomness mismatch')
        if (bundle.observed_setup.evidence_kind != clean.observed_setup.evidence_kind
                or bundle.observed_setup.code_revision != clean.observed_setup.code_revision
                or bundle.observed_setup.application_source_digest != clean.observed_setup.application_source_digest
                or bundle.observed_setup.dependency_versions != clean.observed_setup.dependency_versions
                or bundle.observed_setup.environment != clean.observed_setup.environment):
            raise ValueError('scenario environment/code differs; not an isolated resource intervention')
        if {e.example_id for e in request.examples} != set(expected):
            raise ValueError('scenario must cover exactly every clean development example')
        for example in request.examples:
            baseline = expected[example.example_id]
            left, right = example.model_dump(), baseline.model_dump()
            left.pop('run_id'); right.pop('run_id')
            if left != right:
                raise ValueError('scenario example/split/independent label differs from clean input')
            if example.run_id in used_runs:
                raise ValueError('scenario requires distinct execution IDs, not reused clean reports')
            used_runs.add(example.run_id)


class UpstreamExperiment(FrozenModel):
    version: Literal['upstream_evidence_experiment_v1']
    clean: RecordingBundle
    context: PlanningContext
    contract: ExecutionContract
    report_attacks: AttackSpecification
    scenarios: tuple[ScenarioRecording, ...] = Field(min_length=1)
    clean_build_specification: PolicyBuildSpecification | None = None

    @model_validator(mode='after')
    def check(self):
        # Existing history/split/prerequisite/coverage contracts remain authoritative.
        if any(getattr(self.context, k) is not None for k in
               ('clean_coverage_json', 'reliability_first_json', 'pooling_contract_json')):
            raise ValueError('this additive scenario path requires an unpooled base objective context')
        manifest = export_training(self.clean, self.context)
        require_execution_records(self.clean)
        clean_bound = bind_evaluation(self.context, manifest, self.contract, self.report_attacks)
        if self.contract.resource_manifest is None:
            raise ValueError('upstream experiments require resource-bound execution')
        if len({s.intervention.scenario_id for s in self.scenarios}) != len(self.scenarios):
            raise ValueError('duplicate scenario')
        spec = self.clean_build_specification
        if manifest.evidence_kind == 'empirical' and spec is None:
            raise ValueError('empirical upstream fitting requires the clean PolicyBuildSpecification and existing readiness checks')
        if spec is not None:
            if (spec.context != clean_bound or spec.manifest != manifest or spec.contract != self.contract
                    or spec.attacks != self.report_attacks):
                raise ValueError('empirical clean build specification differs from the exact clean collection/settings')
            from app.game.research.readiness import check_readiness
            readiness = check_readiness(spec, actual_code_revision=self.clean.observed_setup.code_revision)
            if not readiness.ready:
                raise ValueError('empirical clean readiness blocked: ' + '; '.join(readiness.blockers))
        validate_scenario_links(self.clean, self.context, self.contract, self.scenarios)
        return self

    @property
    def experiment_id(self):
        # Full raw timings remain in the bundle; costs come from the frozen context.
        return content_id(dict(version=self.version, clean=scientific_bundle_id(self.clean),
            context=self.context.model_dump(mode='json'), contract=self.contract.model_dump(mode='json'),
            report_attacks=self.report_attacks.model_dump(mode='json'), scenarios=[
                (s.intervention.model_dump(mode='json'), scientific_bundle_id(s.bundle),
                 None if s.evidence_validation is None else s.evidence_validation.validation_id) for s in self.scenarios],
            clean_build_specification_id=None if self.clean_build_specification is None else self.clean_build_specification.specification_id))


def prepare_experiment(experiment):
    experiment = UpstreamExperiment.model_validate(experiment)
    manifest = export_training(experiment.clean, experiment.context)
    clean = bind_evaluation(experiment.context, manifest, experiment.contract, experiment.report_attacks)
    bound = PlanningContext.model_validate({**clean.model_dump(),
        'offline_evaluation_id': content_id(['upstream_evidence_fit_v1', experiment.experiment_id]),
        'provenance': {**clean.provenance.model_dump(),
            'attack_specification': content_id(dict(version='upstream_evidence_scenario_set_v1',
                report_attacks=experiment.report_attacks.model_dump(mode='json'),
                interventions=[s.intervention.model_dump(mode='json') for s in experiment.scenarios]))}})
    return experiment, manifest, bound


def construct_upstream_payoffs(experiment):
    experiment, manifest, context = prepare_experiment(experiment)
    strategies = enumerate_strategies(context).strategies
    if not strategies:
        raise ValueError('no_feasible_strategy')
    clean_actions = enumerate_attacks(context.dependencies, experiment.report_attacks)
    replay_base = bind_evaluation(experiment.context, manifest, experiment.contract, experiment.report_attacks)
    # Report attacks are evaluated on clean resources; no implicit combination
    # with poisoning. Each resource scenario is one ex-ante column across teams.
    columns = tuple(a.attack_id for a in clean_actions) + tuple(
        s.intervention.scenario_id for s in experiment.scenarios)
    values, metrics, outcomes = [], [], []
    for strategy in strategies:
        cells = []
        for attack in clean_actions:
            cells.append(tuple(replay(replay_base, strategy, attack, experiment.report_attacks,
                experiment.contract, e) for e in manifest.partition('development').examples))
        for scenario in experiment.scenarios:
            altered_contract = ExecutionContract.model_validate({**experiment.contract.model_dump(),
                'execution_configuration_id': scenario.intervention.altered_resources.manifest_id,
                'resource_manifest': scenario.intervention.altered_resources})
            # Experimental replay binds the altered contract explicitly, including
            # v4's exact contract guard. It is never exported as a deployment context.
            replay_context = PlanningContext.model_validate({**replay_base.model_dump(),
                'execution_contract_json': canonical_json(altered_contract.model_dump(mode='json'))})
            lookup = {e.example_id: e for e in scenario.bundle.request.examples}
            attempts = {}
            for row in scenario.bundle.attempts:
                attempts.setdefault(row.example_id, []).append(row.attempt)
            cell = []
            for baseline in manifest.partition('development').examples:
                example = Example.model_validate({**baseline.model_dump(),
                    'validation_id': lookup[baseline.example_id].run_id,
                    'execution_configuration_id': altered_contract.execution_configuration_id,
                    'attempts': attempts[baseline.example_id]})
                result = replay(replay_context, strategy, clean_actions[0], experiment.report_attacks,
                                altered_contract, example)
                cell.append(result.model_copy(update={'attack_id': scenario.intervention.scenario_id, 'audit': ()}))
            cells.append(tuple(cell))
        row = []
        for column, cell in zip(columns, cells):
            summary = summarize(tuple((o, 1.) for o in cell), context.loss_configuration)
            row.append(summary.mean_loss)
            metrics.append((strategy.strategy_id, column, summary))
            outcomes.extend(cell)
        values.append(tuple(row))
    matrix = PayoffMatrix(strategy_ids=tuple(s.strategy_id for s in strategies), strategy_definitions=strategies,
        attack_ids=columns, values=tuple(values), compatibility_id=context.compatibility_id)
    return context, matrix, tuple(metrics), tuple(outcomes)


class UpstreamFit(FrozenModel):
    version: Literal['upstream_evidence_fit_v1'] = 'upstream_evidence_fit_v1'
    experiment: UpstreamExperiment
    artifact: PolicyArtifact

    @model_validator(mode='after')
    def check(self):
        context, matrix, _, _ = construct_upstream_payoffs(self.experiment)
        if (self.artifact.context != context or self.artifact.policy.matrix != matrix
                or self.artifact.contract != self.experiment.contract):
            raise ValueError('upstream export differs from the bound experiment/payoffs/clean deployment contract')
        # PolicyArtifact validation checks the existing minimax certificate too.
        return self


def fit_upstream(experiment, *, actual_code_revision=None):
    experiment = UpstreamExperiment.model_validate(experiment)
    if experiment.clean.observed_setup.evidence_kind == 'empirical':
        if actual_code_revision != experiment.clean_build_specification.code_revision:
            raise ValueError('empirical fit requires actual_code_revision matching the approved clean build specification')
    context, matrix, _, _ = construct_upstream_payoffs(experiment)
    tolerance = None if experiment.clean_build_specification is None else experiment.clean_build_specification.optimizer_tolerance
    policy = build_policy(context, matrix, tolerance=tolerance)
    return UpstreamFit(experiment=experiment, artifact=PolicyArtifact(
        version=artifact_version(context, policy), context=context, policy=policy,
        contract=experiment.contract, execution_configuration_id=experiment.contract.execution_configuration_id,
        applicable_domain=context.plan.domain))
