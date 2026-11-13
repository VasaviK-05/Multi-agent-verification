"""Five independent, metadata-only readiness stages; never replay, solve or read Final."""
import hashlib

from app.game.offline.attacks import adapter_incompatibility
from app.game.research.comparison import validate_frozen
from app.game.research.experiment1.manifest import reporting_environment
from app.game.resource_provenance import VerifierResources
from .models import Manifest, Authorizations, reviewed_record

STAGES = ('protocol_review', 'history_development_collection', 'policy_fitting',
          'final_test_authorization_review', 'final_test_scoring')
OWNERS = dict(game='Vasavi / game-research', data='Research preparation owner',
              resources='Raunak', collector='Tanmayee')


def issue(code, owner, expected, check):
    return dict(code=code, owner=OWNERS[owner], expected_artifact=expected, identity_check=check)


def _approval(auth, scope, identity):
    return any(a.scope == scope and a.subject_id == identity for a in auth.approvals)


def training_issues(c):
    problems = []
    def add(code, expected, check):
        problems.append(issue(code, 'data', expected, check))
    if c.training is None:
        add('training_missing', 'Complete labelled History/Development TrainingManifest', 'Typed role/recording and outcome-free reservation bindings')
        return problems
    if c.population is None or c.resources is None:
        return problems
    names = {x.verifier_name for x in c.candidates}
    adapters = {x.verifier_name: x.adapter for x in c.candidates}
    expected = {e.example_id: e for e in c.population.members}
    dataset_ids = dict(c.population.dataset_ids)
    for p in c.training.partitions:
        if p.dataset_id != dataset_ids[p.role] or {e.example_id for e in p.examples} != {e.example_id for e in c.population.members if e.role == p.role}:
            add('training_roster_mismatch', 'Exact approved dataset/role roster', p.role)
        for e in p.examples:
            m = expected.get(e.example_id)
            if m is None:
                continue
            reference = hashlib.sha256(e.reference.encode()).hexdigest() if e.reference else None
            if ((e.split_identity, e.question_id, e.content_identity, e.validation_id, reference, e.label_method, e.label_source) !=
                    (m.group_id, m.question_id, m.content_id, m.validation_id, m.reference_sha256, m.label.method, m.label.source)):
                add('input_or_label_provenance_mismatch', 'Exact input/reference/group/independent label ledger', e.example_id)
            if e.execution_configuration_id != c.resources.manifest_id:
                add('recording_resource_mismatch', 'Bound recording configuration', e.example_id)
            if {a.verifier_name for a in e.attempts} != names or any(a.state == 'missing' for a in e.attempts):
                add('incomplete_recordings', 'Every candidate terminal outcome, including failed/unavailable', e.example_id)
            for a in e.attempts:
                try:
                    if a.observed_resources_json is None:
                        raise ValueError('missing observation')
                    c.resources.require_observation(VerifierResources.model_validate_json(a.observed_resources_json))
                    if adapter_incompatibility(a) is not None or adapters.get(a.verifier_name) != a.adapter:
                        raise ValueError('attack adapter mismatch')
                except ValueError as exc:
                    add('report_resource_or_adapter_mismatch', 'Original per-verifier observation and report adapter', e.example_id + ':' + str(exc))
    reservation = c.training.final_test_reservation
    if reservation.dataset_id != dataset_ids['final_test']:
        add('reservation_mismatch', 'Approved outcome-free reservation', 'dataset identity')
    actual = {e.example_id: e.model_dump() for e in reservation.examples}
    wanted = {m.example_id: dict(example_id=m.example_id, split_identity=m.group_id, question_id=m.question_id,
              content_identity=m.content_id, validation_id=m.validation_id) for m in c.population.members if m.role == 'final_test'}
    if actual != wanted:
        add('reservation_mismatch', 'Approved outcome-free reservation', 'all reserved input/group/run identities')
    return problems


def frozen_issues(manifest, c, actual_commit):
    problems = []
    def add(code, check):
        problems.append(issue(code, 'game', 'Exact prospective frozen policy/comparison/specification', check))
    if c.frozen is None:
        add('frozen_comparison_missing', 'No selection or fitting is performed by readiness/reporting')
        return problems
    s, f = c.frozen.specification, c.frozen.comparison
    try:
        validate_frozen(s, f, actual_code_revision=actual_commit)
    except ValueError as exc:
        add('frozen_comparison_incompatible', str(exc))
    if s.study_id != manifest.study_id + ':' + c.name:
        add('study_lineage_mismatch', 'new prospective study/cohort identity')
    required = ('arithmetic',) if c.name == 'arithmetic' else ('direct_fact',)
    if tuple(s.context.plan.requirements.requirements) != required:
        add('task_obligations_mismatch', str(required))
    if s.code_revision != manifest.source_commit or s.context.dependencies != c.dependencies or s.attacks != c.attacks:
        add('source_dependency_or_attack_mismatch', 'protocol source, connected groups and suppression semantics')
    if s.contract.resource_manifest != c.resources:
        add('frozen_resources_mismatch', 'exact ResourceManifest')
    # The captured planner descriptors, including prerequisite exclusions, are common to every method.
    planner = {v.verifier_name: v for v in s.context.plan.candidates}
    if set(planner) != {v.verifier_name for v in c.candidates}:
        add('candidate_roster_mismatch', 'captured eligible/capability roster')
    for v in c.candidates:
        p = planner.get(v.verifier_name)
        cap = v.capabilities
        if p is None or (set(p.expected_capabilities), p.registered, p.requires_reference, p.configured_readiness, p.limitations) != (set(cap.expected_capabilities), v.registered, cap.requires_reference, cap.readiness, cap.limitations):
            add('candidate_capabilities_mismatch', v.verifier_name)
    k, x, choices = s.contract, s.context, c.choices
    minima = k.team_requirements
    if minima is None or (minima.minimum_selected, minima.minimum_informative) != (choices.minimum_selected, choices.minimum_informative):
        add('contributor_contract_mismatch', 'explicit common selected/informative requirements')
    loss = x.loss_configuration
    if (loss.false_accept, loss.false_reject, loss.uncertain, k.threshold) != (manifest.false_accept, manifest.false_reject, manifest.uncertain, manifest.threshold):
        add('loss_or_threshold_mismatch', '1/1/0.2 and threshold 0.55')
    if (x.budget, loss.resource_weight, x.cost_units, dict(x.attempt_costs), k.failure_contract, k.history_prior_alpha, k.history_prior_beta, s.optimizer_tolerance) != (choices.budget, choices.resource_coefficient, choices.cost_units, dict(choices.attempt_costs or ()), choices.failure_contract, choices.history_prior_alpha, choices.history_prior_beta, choices.optimizer_tolerance):
        add('objective_or_cost_contract_mismatch', 'frozen common budget/cost/priors/failure/tolerance')
    matrix = f.full_artifact.policy.matrix
    if matrix.clean_coverage is None or matrix.clean_coverage.minimum != choices.development_coverage_floor:
        add('development_coverage_mismatch', 'floor constrains Development, never guaranteed on held-out data')
    reliability = matrix.reliability_first
    if choices.objective == 'validation_then_attempt_cost_v1':
        if reliability is None or (reliability.epsilon, reliability.cost_tolerance) != (choices.validation_epsilon, choices.cost_tolerance):
            add('objective_mismatch', 'validation first, then declared attempt cost tie-break')
    elif reliability is not None:
        add('objective_mismatch', 'cost-inclusive objective cannot be relabelled validation-first')
    if manifest.statistics is None or (s.uncertainty.resamples, s.uncertainty.seed, s.uncertainty.confidence_level) != (manifest.statistics.resamples, manifest.statistics.seed, .95):
        add('statistical_design_mismatch', 'explicit prospective paired 95% design')
    return problems


def readiness(manifest, *, actual_commit, actual_source_fingerprint, authorizations=None):
    manifest = Manifest.model_validate(manifest)
    auth = Authorizations.model_validate(authorizations or {})
    results = []
    for c in manifest.cohorts:
        common = []
        def add(code, owner, expected, check):
            common.append(issue(code, owner, expected, check))
        if manifest.source_commit is None or manifest.source_commit != actual_commit:
            add('source_commit_mismatch', 'game', 'Reviewed exact source revision', 'expected versus actual Git commit')
        if manifest.source_fingerprint is None or manifest.source_fingerprint != actual_source_fingerprint:
            add('source_bytes_mismatch', 'game', 'Reviewed executable byte inventory', 'exact source SHA-256 including checkout line endings')
        if c.population is None:
            add('population_missing', 'data', 'Outcome-free per-role roster and preserved exclusions', 'group, question, content and execution isolation')
        else:
            if any(m.label.method == 'provisional_automated' or ('provisional' in m.label.producer_protocol.casefold() and m.label.independent_review_record is None) for m in c.population.members):
                add('independent_label_review_missing', 'data', 'Independent label provenance, not eligibility approval alone', 'provisional labels cannot be promoted to ground truth')
        required_kind = 'bounded_arithmetic' if c.name == 'arithmetic' else 'grounded_direct_fact'
        if c.population_kind != required_kind or (c.source_benchmark or '').casefold() in {'gsm8k', 'hotpotqa'}:
            add('unsupported_population', 'resources', 'Resource-bound support review of an in-scope population', 'No silent GSM8K/direct-arithmetic or HotpotQA/direct-fact reinterpretation in v1')
        if c.resources is None or not c.candidates:
            add('resources_or_roster_missing', 'resources', 'Actual ResourceManifest and captured Candidate descriptors', 'models/config/corpus/index/prompt/service identities')
        elif {v.verifier_name for v in c.resources.verifiers} != {v.verifier_name for v in c.candidates}:
            add('resource_roster_mismatch', 'resources', 'One resource entry per captured candidate', 'exact roster equality')
        if c.reference_contract is None:
            add('reference_contract_missing', 'data', 'Approved exact reference serializer or explicit no-reference contract', 'identical allowed inputs for every method; no gold/labels sent to verifiers')
        for kind, owner in [('labels', 'data'), ('task_support', 'resources'), ('eligibility', 'data'), ('reference', 'data'), ('resources', 'resources'), ('collector', 'collector')]:
            if not any(e.kind == kind and e.subject_id == manifest.collection_id(c.name) for e in c.evidence):
                add(kind + '_evidence_missing_or_stale', owner, kind + ' review with authority, record and artifact digest', 'exact collection binding ' + manifest.collection_id(c.name))
        collection = list(common)
        if not _approval(auth, 'collection', manifest.collection_id(c.name)):
            collection.append(issue('collection_authorization_missing', 'data', 'Explicit History/Development collection decision', 'exact collection binding; no inference occurs here'))
        fitting = list(collection)
        if c.choices.attempt_costs is not None and set(dict(c.choices.attempt_costs)) != {v.verifier_name for v in c.candidates}:
            fitting.append(issue('cost_roster_mismatch', 'game', 'Explicit cost for every captured candidate', 'no missing or additional cost identities'))
        if c.dependencies is not None:
            try:
                c.dependencies.groups(v.verifier_name for v in c.candidates)
            except ValueError as exc:
                fitting.append(issue('dependency_roster_mismatch', 'game', 'Declared dependency/unknown status for each candidate', str(exc)))
        if c.population is not None and len({m.reference_sha256 is not None for m in c.population.members}) > 1:
            fitting.append(issue('mixed_reference_profiles', 'game', 'One compatible frozen planning/reference context per cohort', 'split into explicitly versioned contexts rather than flatten prerequisite differences'))
        for field in type(c.choices).model_fields:
            if field in {'validation_epsilon', 'cost_tolerance'} and c.choices.objective != 'validation_then_attempt_cost_v1':
                continue
            if getattr(c.choices, field) is None:
                fitting.append(issue('unresolved_' + field, 'game', 'Approved prospective ' + field, 'no inherited historical default'))
        for code, ok, expected in [
            ('dependencies_missing', c.dependencies is not None, 'Declared shared/unknown dependency registry'),
            ('attack_definition_missing', c.attacks is not None, 'Report corruption specification with approved suppression'),
            ('statistics_missing', manifest.statistics is not None, 'Paired 95% group bootstrap seed and repetitions'),
            ('reporting_environment_mismatch', manifest.reporting_environment == reporting_environment(), 'Pinned reporting Python/NumPy/SciPy/Pydantic versions'),
            ('protocol_approval_missing', _approval(auth, 'protocol', manifest.protocol_id), 'Approved exact prospective protocol'),
            ('fitting_authorization_missing', _approval(auth, 'fitting', manifest.fitting_id(c.name)), 'Explicit fitting approval bound to this protocol, cohort, training ID and calibration'),
            ('calibration_missing_or_stale', any(e.kind == 'calibration' and e.subject_id == manifest.collection_id(c.name) for e in c.evidence), 'Authenticated compatible calibration with actual input/source/resource custody')]:
            if not ok:
                identity = manifest.fitting_id(c.name) if code == 'fitting_authorization_missing' else manifest.collection_id(c.name) if code == 'calibration_missing_or_stale' else manifest.protocol_id
                fitting.append(issue(code, 'game' if code != 'calibration_missing_or_stale' else 'resources', expected, identity))
        if c.training is not None and c.training.evidence_kind != manifest.evidence_kind:
            fitting.append(issue('evidence_kind_mismatch', 'data', 'Consistent empirical or synthetic evidence kind', 'synthetic fixtures cannot authenticate empirical studies'))
        fitting.extend(training_issues(c))
        final_review = list(fitting) + frozen_issues(manifest, c, actual_commit)
        if c.final_exposure != 'untouched_reserved':
            final_review.append(issue('final_exposure_unverified', 'data', 'Independent untouched-Final-Test exposure attestation', 'known Development overlap or unknown exposure is not a new held-out population'))
        if not any(e.kind == 'custody' and e.subject_id == manifest.collection_id(c.name) for e in c.evidence):
            final_review.append(issue('independent_final_custody_missing', 'data', 'Independent outcome-free Final Test custody/exposure attestation', 'exact population and collection binding'))
        if c.training is not None:
            try:
                reviewed_record(c.training.final_test_reservation.custody_record)
            except ValueError:
                final_review.append(issue('unresolved_custody_record', 'data', 'Actual independent custodian record', 'a pending reservation guard is not a completed Final Test seal'))
        final_score = list(final_review)
        release = next((r for r in auth.releases if r.cohort == c.name), None)
        if release is None or release.manifest_id != manifest.manifest_id or c.training is None or release.reservation_id != c.training.final_test_reservation.reservation_id:
            final_score.append(issue('final_release_missing_or_stale', 'data', 'External exact-manifest and exact-payload SHA-256 release decision', 'manifest ID + cohort + reservation ID + payload digest before loading'))
        stages = dict(protocol_review=dict(ready=True, blockers=[], unresolved_decisions=[p for p in fitting if p['code'].startswith('unresolved_')]))
        for name, problems in zip(STAGES[1:], (collection, fitting, final_review, final_score)):
            stages[name] = dict(ready=not problems, blockers=problems)
        results.append(dict(cohort=c.name, stages=stages))
    return dict(version='prospective_experiment1_readiness_v1', manifest_id=manifest.manifest_id,
        protocol_id=manifest.protocol_id, stages={stage: dict(ready=all(r['stages'][stage]['ready'] for r in results)) for stage in STAGES},
        cohorts=results, final_payloads_read=False, inference_calls=0, optimization_calls=0,
        evidence_limit='Metadata consistency and caller-trusted digest checks, not independent certification of producer assertions')
